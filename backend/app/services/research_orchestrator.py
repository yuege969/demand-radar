from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from time import time

from loguru import logger

from app.config import settings
from app.database import SessionLocal
from app.models.pain_point import PainPoint
from app.models.pain_score import PainScore
from app.models.research_job import ResearchJob
from app.schemas.research import ResearcherOutput
from app.services.deduplicator import encode_texts, find_most_similar, is_duplicate
from app.services.pain_point_enricher import enrich_pain_point, enrich_snapshot
from app.services.pain_scorer import calculate_pain_score, calculate_opportunity_score
from app.services.rate_limiter import create_rate_limiter
from app.services.researchers.ddg_search import DDGSearchResearcher
from app.services.researchers.github_search import GitHubResearcher
from app.services.researchers.hn_search import HNResearcher
from app.services.researchers.reddit_search import RedditResearcher
from app.services.researchers.rss_search import RSSResearcher
from app.services.skill_loader import SkillLoader

BUILTIN_RESEARCHER_MAP = {
    "web": DDGSearchResearcher,
    "hackernews": HNResearcher,
    "github": GitHubResearcher,
    "reddit": RedditResearcher,
    "rss": RSSResearcher,
}

_skill_loader: SkillLoader | None = None


def _get_skill_loader() -> SkillLoader:
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader(
            search_paths=settings.skill_search_paths,
            allowlist=settings.skill_allowlist,
        )
    return _skill_loader


def list_available_platforms() -> list[str]:
    platforms = list(BUILTIN_RESEARCHER_MAP.keys())
    try:
        loader = _get_skill_loader()
        for meta in loader.list_skills():
            if meta.name not in platforms:
                platforms.append(meta.name)
    except Exception:
        pass
    return platforms


def _resolve_researcher(name: str, rate_limiter=None):
    if name in BUILTIN_RESEARCHER_MAP:
        researcher_cls = BUILTIN_RESEARCHER_MAP[name]
        return researcher_cls(rate_limiter=rate_limiter)

    skill = _get_skill_loader().load_skill(name)
    if skill is not None:
        from app.services.researchers.skill_researcher import SkillResearcher

        return SkillResearcher(skill)

    return None

FREQUENCY_MAP = {"high": 10, "medium": 6, "low": 3}
WTP_MAP = {"high": 10, "medium": 6, "low": 3, "none": 0}


def _map_dimensions(pp: dict) -> dict:
    freq = FREQUENCY_MAP.get(pp.get("frequency", "low"), 3)
    wtp = WTP_MAP.get(pp.get("willingness_to_pay", "none"), 0)
    return {
        "emotion_intensity": 5,
        "repeat_frequency": freq,
        "involves_money": wtp,
        "has_paid_solution": 5,
        "automation_difficulty": 5,
        "is_long_term": 7 if freq >= 6 else 4,
    }


async def run_research(domain: str, platforms: list[str], job_id: int | None = None) -> dict:
    if job_id is None:
        job = _create_job(domain, platforms)
        job_id = job.id

    logger.info("=" * 60)
    logger.info("[JOB {}] 研究开始 | domain='{}' | platforms={}", job_id, domain, platforms)

    try:
        logger.info("[JOB {}] 阶段1/4: 启动多源搜索...", job_id)
        t0 = time()
        results = await _run_researchers(domain, platforms)
        elapsed = (time() - t0) * 1000
        logger.info("[JOB {}] 阶段1/4 完成 | {:.0f}ms | {} 个数据源返回结果",
                    job_id, elapsed, len(results))

        all_findings_count = sum(r.findings_count for r in results)
        all_pain_points = []
        for r in results:
            for pp in r.pain_points:
                pp["_platform"] = r.platform
                all_pain_points.append(pp)

        logger.info("[JOB {}] 汇总: {} 条原始发现 → {} 个候选痛点",
                    job_id, all_findings_count, len(all_pain_points))

        logger.info("[JOB {}] 阶段2/4: 语义去重 + 入库...", job_id)
        t0 = time()
        new_count = 0
        if all_pain_points:
            new_count = _store_pain_points(all_pain_points, job_id, domain)
        elapsed = (time() - t0) * 1000
        logger.info("[JOB {}] 阶段2/4 完成 | {:.0f}ms | 新增 {} 个 / 合并 {} 个",
                    job_id, elapsed, new_count, len(all_pain_points) - new_count)

        logger.info("[JOB {}] 阶段3/4: 快照富化 (snapshot)...", job_id)
        t0 = time()
        if new_count > 0:
            await _snapshot_pain_points(job_id)
        elapsed = (time() - t0) * 1000
        logger.info("[JOB {}] 阶段3/4 完成 | {:.0f}ms", job_id, elapsed)

        logger.info("[JOB {}] 阶段4/4: 持久化完成标记...", job_id)
        _complete_job(job_id, all_findings_count, new_count)

        logger.info("[JOB {}] 研究完成 | findings={} | pain_points={} | new={}",
                    job_id, all_findings_count, len(all_pain_points), new_count)
        logger.info("=" * 60)

        return {
            "job_id": job_id,
            "domain": domain,
            "platforms": platforms,
            "total_findings": all_findings_count,
            "pain_points_extracted": new_count,
        }

    except Exception as e:
        logger.error("[JOB {}] 研究失败: {}", job_id, e)
        _fail_job(job_id, str(e))
        raise


async def _run_researchers(domain: str, platforms: list[str]) -> list[ResearcherOutput]:
    rate_limiter = create_rate_limiter()
    tasks = []
    for name in platforms:
        researcher = _resolve_researcher(name, rate_limiter=rate_limiter)
        if researcher is None:
            logger.warning("[JOB] 跳过未知数据源: {}", name)
            continue
        logger.info("[JOB] 启动数据源: {} ({})", name, researcher.__class__.__name__)
        tasks.append(researcher.research(domain))

    if not tasks:
        logger.warning("[JOB] 没有可用的数据源")
        return []

    results = await asyncio.gather(*tasks, return_exceptions=True)
    outputs = []
    for i, r in enumerate(results):
        name = platforms[i] if i < len(platforms) else "?"
        if isinstance(r, Exception):
            logger.error("[JOB] 数据源 {} 异常: {}", name, r)
        else:
            logger.info("[JOB] 数据源 {} 完成 | findings={} | pain_points={}",
                       name, r.findings_count, len(r.pain_points))
            outputs.append(r)
    return outputs


def _store_pain_points(pain_points: list[dict], job_id: int, domain: str) -> int:
    db = SessionLocal()
    try:
        logger.info("[JOB {}] 去重: 加载 {} 个已有痛点 embeddings...", job_id,
                    db.query(PainPoint).count())
        existing_pps = db.query(PainPoint).all()
        existing_embeddings: list[tuple[int, list[float]]] = []
        if existing_pps:
            summaries = [pp.summary for pp in existing_pps]
            encodings = encode_texts(summaries)
            for pp, emb in zip(existing_pps, encodings):
                existing_embeddings.append((pp.id, emb))
            logger.info("[JOB {}] 去重: 已编码 {} 个已有痛点", job_id, len(existing_embeddings))

        summaries_to_encode = [pp.get("summary", pp.get("title", "")) for pp in pain_points]
        new_embeddings = (
            encode_texts(summaries_to_encode)
            if existing_embeddings
            else [[] for _ in pain_points]
        )

        new_count = 0
        merged_count = 0
        for i, pp_data in enumerate(pain_points):
            best_id, best_score = find_most_similar(
                new_embeddings[i], existing_embeddings
            ) if existing_embeddings else (None, -1.0)

            if best_id and is_duplicate(best_score):
                _merge_pain_point(db, best_id, pp_data)
                merged_count += 1
                logger.debug("[JOB {}] 去重: 合并 '{}' → PP#{} (相似度 {:.3f})",
                           job_id, pp_data.get("title", "")[:40], best_id, best_score)
            else:
                _create_pain_point(db, pp_data, job_id, domain)
                new_count += 1
                logger.info("[JOB {}] 去重: 新增 '{}' [{}/{}]",
                           job_id, pp_data.get("title", "")[:40], i + 1, len(pain_points))

        db.commit()
        logger.info("[JOB {}] 去重结果: 新增 {} / 合并 {} / 总计 {}", job_id, new_count, merged_count, len(pain_points))
        return new_count
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def _create_pain_point(db, pp_data: dict, job_id: int, domain: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    dims = _map_dimensions(pp_data)
    total = calculate_pain_score(dims)
    opp_score = calculate_opportunity_score(total, 0.5)

    source_info = json.dumps([
        {
            "platform": pp_data.get("_platform", "unknown"),
            "title": pp_data.get("title", ""),
            "snippet": (pp_data.get("summary", "") or "")[:500],
        }
    ])

    pp = PainPoint(
        research_job_id=job_id,
        title=pp_data.get("title", ""),
        summary=pp_data.get("summary", ""),
        category=pp_data.get("category"),
        industry=domain,
        pain_score=total,
        keywords=json.dumps([pp_data.get("category", ""), pp_data.get("target_user", ""), domain]),
        source_urls=source_info,
        business_angle=pp_data.get("target_user", ""),
        created_at=now,
        updated_at=now,
        individual_score=5.0,
        opportunity_score=opp_score,
        market_saturation="amber",
    )
    db.add(pp)
    db.flush()

    ps = PainScore(
        pain_point_id=pp.id,
        emotion_intensity=dims["emotion_intensity"],
        repeat_frequency=dims["repeat_frequency"],
        involves_money=dims["involves_money"],
        has_paid_solution=dims["has_paid_solution"],
        automation_difficulty=dims["automation_difficulty"],
        is_long_term=dims["is_long_term"],
        total_score=total,
        calculated_at=now,
    )
    db.add(ps)


def _merge_pain_point(db, pp_id: int, pp_data: dict) -> None:
    pp = db.query(PainPoint).filter(PainPoint.id == pp_id).first()
    if not pp:
        return
    existing = json.loads(pp.source_urls or "[]")
    existing.append({
        "platform": pp_data.get("_platform", "unknown"),
        "title": pp_data.get("title", ""),
    })
    pp.source_urls = json.dumps(existing)
    pp.updated_at = datetime.now(timezone.utc).isoformat()


def _create_job(domain: str, platforms: list[str]) -> ResearchJob:
    db = SessionLocal()
    try:
        job = ResearchJob(
            domain=domain,
            platforms=json.dumps(platforms),
            status="running",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    finally:
        db.close()


def _complete_job(job_id: int, total_findings: int, pain_points_count: int) -> None:
    db = SessionLocal()
    try:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if job:
            job.status = "completed"
            job.total_findings = total_findings
            job.pain_points_extracted = pain_points_count
            job.completed_at = datetime.now(timezone.utc).isoformat()
            db.commit()
    finally:
        db.close()


def _fail_job(job_id: int, error: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = error
            job.completed_at = datetime.now(timezone.utc).isoformat()
            db.commit()
    finally:
        db.close()


async def _snapshot_pain_points(job_id: int) -> int:
    """Run lightweight snapshot enrichment for all pain points in a job."""
    db = SessionLocal()
    try:
        points = (
            db.query(PainPoint)
            .filter(PainPoint.research_job_id == job_id, PainPoint.snapshot_at.is_(None))
            .all()
        )
        if not points:
            logger.info("[JOB {}] 快照: 无需富化 (已全部完成)", job_id)
            return 0

        logger.info("[JOB {}] 快照: 开始富化 {} 个痛点...", job_id, len(points))
        enriched = 0
        for i, pp in enumerate(points):
            snippets = _extract_snippets(pp)
            result = await enrich_snapshot(
                title=pp.title,
                summary=pp.summary,
                category=pp.category,
                industry=pp.industry,
                source_snippets=snippets or None,
            )
            if result is None:
                logger.warning("[JOB {}] 快照: '{}' LLM 返回为空", job_id, pp.title[:30])
                continue

            pp.snapshot_summary = result.get("summary") or pp.snapshot_summary
            pp.snapshot_opportunity = result.get("opportunity") or pp.snapshot_opportunity
            pp.snapshot_at = datetime.now(timezone.utc).isoformat()
            enriched += 1
            logger.info("[JOB {}] 快照: '{:.30s}' → '{}' [{}/{}]",
                       job_id, pp.title, pp.snapshot_summary or "-", i + 1, len(points))

        db.commit()
        logger.info("[JOB {}] 快照完成: {}/{}", job_id, enriched, len(points))
        return enriched
    except Exception as e:
        db.rollback()
        logger.error("[JOB {}] 快照失败: {}", job_id, e)
        return 0
    finally:
        db.close()


def _extract_snippets(pp: PainPoint) -> str:
    try:
        sources = json.loads(pp.source_urls or "[]")
        parts = []
        for s in sources:
            if isinstance(s, dict) and s.get("snippet"):
                parts.append(f"- {s.get('title', '')}: {s['snippet'][:300]}")
        return "\n".join(parts) if parts else ""
    except (json.JSONDecodeError, TypeError):
        return ""


async def _enrich_pain_points(job_id: int) -> int:
    db = SessionLocal()
    try:
        points = (
            db.query(PainPoint)
            .filter(PainPoint.research_job_id == job_id, PainPoint.enriched_at.is_(None))
            .all()
        )
        if not points:
            return 0

        enriched = 0
        for pp in points:
            snippets = _extract_snippets(pp)

            result = await enrich_pain_point(
                title=pp.title,
                summary=pp.summary,
                category=pp.category,
                industry=pp.industry,
                source_snippets=snippets or None,
            )
            if result is None:
                continue

            if result.get("demand_validation"):
                pp.demand_validation = json.dumps(result["demand_validation"], ensure_ascii=False)
            if result.get("market_value_analysis"):
                pp.market_value_analysis = json.dumps(result["market_value_analysis"], ensure_ascii=False)
            if result.get("implementation_plan"):
                pp.implementation_plan = json.dumps(result["implementation_plan"], ensure_ascii=False)
            if result.get("solo_feasibility"):
                pp.solo_feasibility = json.dumps(result["solo_feasibility"], ensure_ascii=False)

            scores = result.get("dimension_scores")
            if scores and isinstance(scores, dict):
                pp.market_saturation = scores.get("market_saturation") or pp.market_saturation
                pp.individual_score = float(scores.get("individual_score", pp.individual_score))

                pp.is_individual_feasible = 1 if pp.individual_score >= 6.0 else 0

                ps = db.query(PainScore).filter(PainScore.pain_point_id == pp.id).first()
                if ps:
                    ps.emotion_intensity = float(scores.get("emotion_intensity", ps.emotion_intensity))
                    # discussion_volume removed — not meaningful from web search data
                    ps.repeat_frequency = float(scores.get("repeat_frequency", ps.repeat_frequency))
                    ps.involves_money = float(scores.get("involves_money", ps.involves_money))
                    ps.has_paid_solution = float(scores.get("has_paid_solution", ps.has_paid_solution))
                    ps.automation_difficulty = float(scores.get("automation_difficulty", ps.automation_difficulty))
                    ps.is_long_term = float(scores.get("is_long_term", ps.is_long_term))

                    dims = {
                        "emotion_intensity": ps.emotion_intensity,
                        "repeat_frequency": ps.repeat_frequency,
                        "involves_money": ps.involves_money,
                        "has_paid_solution": ps.has_paid_solution,
                        "automation_difficulty": ps.automation_difficulty,
                        "is_long_term": ps.is_long_term,
                    }
                    ps.total_score = calculate_pain_score(dims)
                    pp.pain_score = ps.total_score
                    pp.opportunity_score = calculate_opportunity_score(
                        ps.total_score, pp.individual_score / 10.0
                    )

            sf = result.get("solo_feasibility")
            if sf and isinstance(sf, dict):
                if not pp.feasibility_reason and sf.get("how_to_overcome"):
                    pp.feasibility_reason = sf["how_to_overcome"]
                if not pp.estimated_dev_time and sf.get("realistic_dev_time"):
                    raw_time = sf["realistic_dev_time"]
                    colon = raw_time.find("：") if "：" in raw_time else raw_time.find(":")
                    pp.estimated_dev_time = raw_time[:colon] if colon > 0 else raw_time[:30]

            ip = result.get("implementation_plan")
            if ip and isinstance(ip, dict):
                if not pp.tech_stack_hints and ip.get("recommended_tech_stack"):
                    pp.tech_stack_hints = json.dumps(ip["recommended_tech_stack"], ensure_ascii=False)

            mva = result.get("market_value_analysis")
            if mva and isinstance(mva, dict):
                target = mva.get("target_audience", "")
                business = pp.business_angle or ""
                pp.is_saas_idea = 1 if ("saas" in (pp.category or "").lower() or "subscription" in (business + target).lower()) else pp.is_saas_idea
                pp.is_plugin_idea = 1 if ("plugin" in (pp.category or "").lower() or "插件" in (business + target)) else pp.is_plugin_idea

            pp.enriched_at = datetime.now(timezone.utc).isoformat()
            enriched += 1

        db.commit()
        logger.info("Enriched {} pain points for job {}", enriched, job_id)
        return enriched
    except Exception as e:
        db.rollback()
        logger.error("Enrichment failed for job {}: {}", job_id, e)
        return 0
    finally:
        db.close()
