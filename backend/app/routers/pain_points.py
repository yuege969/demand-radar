from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pain_point import PainPoint
from app.models.pain_score import PainScore
from app.schemas import ApiResponse, PaginationMeta
from app.schemas.pain_point import PainPointOut, PainPointDetail, PainScoreBreakdown
from app.services.research_orchestrator import _enrich_pain_points

router = APIRouter()


def _parse_json_list(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _to_pain_point_out(pp: PainPoint) -> PainPointOut:
    source_count = 0
    if pp.source_urls:
        try:
            source_count = len(json.loads(pp.source_urls))
        except (json.JSONDecodeError, TypeError):
            pass
    return PainPointOut(
        id=pp.id,
        title=pp.title,
        summary=pp.summary,
        category=pp.category,
        industry=pp.industry,
        pain_score=pp.pain_score or 0.0,
        keywords=pp.keywords,
        source_urls=pp.source_urls,
        is_saas_idea=bool(pp.is_saas_idea),
        is_plugin_idea=bool(pp.is_plugin_idea),
        business_angle=pp.business_angle,
        source_count=source_count,
        created_at=pp.created_at,
        updated_at=pp.updated_at,
        is_individual_feasible=bool(pp.is_individual_feasible),
        feasibility_reason=pp.feasibility_reason,
        estimated_dev_time=pp.estimated_dev_time,
        tech_stack_hints=_parse_json_list(pp.tech_stack_hints),
        market_saturation=pp.market_saturation,
        individual_score=pp.individual_score or 0.0,
        opportunity_score=pp.opportunity_score or 0.0,
        snapshot_summary=pp.snapshot_summary,
        snapshot_opportunity=pp.snapshot_opportunity,
        snapshot_at=pp.snapshot_at,
        enrichment_data=pp.enrichment_data,
        demand_validation=pp.demand_validation,
        market_value_analysis=pp.market_value_analysis,
        implementation_plan=pp.implementation_plan,
        solo_feasibility=pp.solo_feasibility,
        enriched_at=pp.enriched_at,
    )


@router.get("")
def list_pain_points(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=1000),
    category: str | None = None,
    industry: str | None = None,
    sort_by: str = Query("pain_score", pattern="^(pain_score|opportunity_score|created_at|updated_at)$"),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(PainPoint)
    if category:
        query = query.filter(PainPoint.category == category)
    if industry:
        query = query.filter(PainPoint.industry == industry)
    if search:
        query = query.filter(
            PainPoint.title.ilike(f"%{search}%") | PainPoint.summary.ilike(f"%{search}%")
        )
    total = query.count()
    order_col = getattr(PainPoint, sort_by)
    points = query.order_by(order_col.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return ApiResponse(
        data=[_to_pain_point_out(p) for p in points],
        meta=PaginationMeta(page=page, per_page=per_page, total=total).model_dump(),
    )


@router.get("/density-stats")
def get_density_stats(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(PainPoint).count()
    points = (
        db.query(PainPoint)
        .order_by(PainPoint.opportunity_score.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    result = []
    for pp in points:
        source_count = 0
        if pp.source_urls:
            try:
                source_count = len(json.loads(pp.source_urls))
            except (json.JSONDecodeError, TypeError):
                pass
        competition_count = _extract_competition_count(pp)
        density = _calc_density_score(source_count, pp.opportunity_score or 0, competition_count)
        stars = _density_to_stars(density)
        result.append({
            "id": pp.id,
            "title": pp.title,
            "source_count": source_count,
            "opportunity_score": pp.opportunity_score or 0,
            "competition_count": competition_count,
            "density_score": round(density, 1),
            "density_stars": stars,
        })

    return ApiResponse(
        data=result,
        meta=PaginationMeta(page=page, per_page=per_page, total=total).model_dump(),
    )


@router.get("/{pain_point_id}")
def get_pain_point(pain_point_id: int, db: Session = Depends(get_db)):
    pp = db.query(PainPoint).filter(PainPoint.id == pain_point_id).first()
    if not pp:
        raise HTTPException(status_code=404, detail="Pain point not found")

    score = db.query(PainScore).filter(PainScore.pain_point_id == pain_point_id).first()
    breakdown = PainScoreBreakdown.model_validate(score) if score else None

    source_findings: list = []
    if pp.source_urls:
        try:
            source_findings = json.loads(pp.source_urls)
        except (json.JSONDecodeError, TypeError):
            pass

    related = (
        db.query(PainPoint)
        .filter(
            PainPoint.id != pain_point_id,
            PainPoint.category == pp.category,
        )
        .order_by(PainPoint.pain_score.desc())
        .limit(5)
        .all()
    )

    return ApiResponse(
        data=PainPointDetail(
            **_to_pain_point_out(pp).model_dump(),
            score_breakdown=breakdown,
            source_findings=source_findings,
            related=[_to_pain_point_out(r) for r in related],
        )
    )


@router.get("/categories/list")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(PainPoint.category).distinct().all()
    inds = db.query(PainPoint.industry).distinct().all()
    return ApiResponse(
        data={
            "categories": sorted(c[0] for c in cats if c[0]),
            "industries": sorted(i[0] for i in inds if i[0]),
        }
    )


@router.get("/search/all")
def search_all(
    q: str = Query(..., min_length=1),
    type: str = Query("all", pattern="^(all|posts|pain_points)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    results = []
    total = 0
    if type in ("all", "pain_points"):
        query = db.query(PainPoint).filter(
            PainPoint.title.ilike(f"%{q}%") | PainPoint.summary.ilike(f"%{q}%")
        )
        total = query.count()
        results = [
            {"type": "pain_point", **PainPointOut.model_validate(p).model_dump()}
            for p in query.limit(per_page).offset((page - 1) * per_page).all()
        ]
    return ApiResponse(
        data=results,
        meta=PaginationMeta(page=page, per_page=per_page, total=total).model_dump(),
    )


def _extract_competition_count(pp: PainPoint) -> int | None:
    if not pp.enrichment_data:
        return None
    try:
        data = json.loads(pp.enrichment_data)
        for key in ("competitor_scan", "competitor_compare"):
            if key in data:
                stored = data[key].get("result", {})
                direct = stored.get("direct_competitors", [])
                if isinstance(direct, list):
                    return len(direct)
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _calc_density_score(source_count: int, opportunity_score: float,
                         competition_count: int | None) -> float:
    freq_factor = min(source_count / 10.0, 1.0)
    opp_factor = opportunity_score / 100.0

    if competition_count is not None and competition_count > 0:
        comp_factor = max(0.0, 1.0 - competition_count / 10.0)
    else:
        comp_factor = 1.0

    return (freq_factor * 0.3 + opp_factor * 0.4 + comp_factor * 0.3) * 100


def _density_to_stars(score: float) -> int:
    if score >= 70:
        return 5
    if score >= 55:
        return 4
    if score >= 40:
        return 3
    if score >= 25:
        return 2
    return 1


@router.post("/re-enrich")
async def re_enrich_pain_points(db: Session = Depends(get_db)):
    """Re-run enrichment for all unenriched pain points."""
    unenriched_count = db.query(PainPoint).filter(PainPoint.enriched_at.is_(None)).count()
    if unenriched_count == 0:
        return ApiResponse(data={"message": "All pain points are already enriched", "enriched": 0})

    job_ids = [
        row[0] for row in
        db.query(PainPoint.research_job_id)
        .filter(PainPoint.enriched_at.is_(None), PainPoint.research_job_id.isnot(None))
        .distinct()
        .all()
    ]

    enriched = 0
    for job_id in job_ids:
        result = await _enrich_pain_points(job_id)
        enriched += result

    return ApiResponse(data={"message": f"Enriched {enriched} pain points", "enriched": enriched})


class EnrichRequest(BaseModel):
    modules: list[str]


_enriching_points: set[int] = set()


@router.get("/{pain_point_id}/enrich/modules")
def get_enrich_modules(pain_point_id: int, db: Session = Depends(get_db)):
    pp = db.query(PainPoint).filter(PainPoint.id == pain_point_id).first()
    if not pp:
        raise HTTPException(status_code=404, detail="Pain point not found")

    from app.services.enrichment_modules import get_pillars

    pillars = get_pillars()
    enrichment = {}
    if pp.enrichment_data:
        try:
            enrichment = json.loads(pp.enrichment_data)
        except (json.JSONDecodeError, TypeError):
            pass

    result = []
    for pillar in pillars:
        pillar_modules = []
        for m in pillar["modules"]:
            completed = m.key in enrichment
            pillar_modules.append({
                "key": m.key,
                "display_name": m.display_name,
                "description": m.description,
                "completed": completed,
                "output_fields": m.output_fields,
            })
        result.append({
            "key": pillar["key"],
            "display_name": pillar["display_name"],
            "description": pillar["description"],
            "modules": pillar_modules,
        })

    return ApiResponse(data=result)


def _run_module_enrich_sync(pain_point_id: int, module_keys: list[str]):
    from app.database import SessionLocal
    from app.services.pain_point_enricher import enrich_module

    db = SessionLocal()
    try:
        pp = db.query(PainPoint).filter(PainPoint.id == pain_point_id).first()
        if not pp:
            return

        enrichment = {}
        if pp.enrichment_data:
            try:
                enrichment = json.loads(pp.enrichment_data)
            except (json.JSONDecodeError, TypeError):
                pass

        now = datetime.now(timezone.utc).isoformat()
        for module_key in module_keys:
            if module_key in enrichment:
                continue

            try:
                result = asyncio.run(enrich_module(
                    module_key=module_key,
                    title=pp.title,
                    summary=pp.summary,
                    category=pp.category,
                    industry=pp.industry,
                    source_snippets=_extract_snippets_inline(pp),
                ))
            except Exception as e:
                logger.error("Module {} enrichment failed for pp {}: {}", module_key, pain_point_id, e)
                continue

            if result is not None:
                enrichment[module_key] = {"completed_at": now, "result": result}

        pp.enrichment_data = json.dumps(enrichment, ensure_ascii=False)
        pp.updated_at = now
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Enrichment sync failed for pp {}: {}", pain_point_id, e)
    finally:
        db.close()
        _enriching_points.discard(pain_point_id)


def _extract_snippets_inline(pp: PainPoint) -> str:
    try:
        sources = json.loads(pp.source_urls or "[]")
        parts = []
        for s in sources:
            if isinstance(s, dict) and s.get("snippet"):
                parts.append(f"- {s.get('title', '')}: {s['snippet'][:300]}")
        return "\n".join(parts) if parts else ""
    except (json.JSONDecodeError, TypeError):
        return ""


@router.post("/{pain_point_id}/enrich")
def trigger_enrich(
    pain_point_id: int,
    body: EnrichRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    pp = db.query(PainPoint).filter(PainPoint.id == pain_point_id).first()
    if not pp:
        raise HTTPException(status_code=404, detail="Pain point not found")

    if pain_point_id in _enriching_points:
        raise HTTPException(status_code=409, detail="Enrichment already in progress for this pain point")

    from app.services.enrichment_modules import get_module_map

    valid_keys = set(get_module_map().keys())
    selected = [k for k in body.modules if k in valid_keys]
    if not selected:
        raise HTTPException(status_code=400, detail="No valid modules selected")

    # Skip already-completed modules
    enrichment = {}
    if pp.enrichment_data:
        try:
            enrichment = json.loads(pp.enrichment_data)
        except (json.JSONDecodeError, TypeError):
            pass
    pending = [k for k in selected if k not in enrichment]
    if not pending:
        return ApiResponse(data={"message": "All selected modules already completed", "enriched": 0, "pending": []})

    _enriching_points.add(pain_point_id)
    background_tasks.add_task(_run_module_enrich_sync, pain_point_id, pending)
    return ApiResponse(data={"message": f"Enrichment started for {len(pending)} modules", "pending": pending})
