from __future__ import annotations

import json
from datetime import datetime, timezone

from loguru import logger

from app.config import settings
from app.database import SessionLocal
from app.models.pain_point import PainPoint
from app.models.pain_score import PainScore
from app.services.ai_analyzer import analyze_posts
from app.services.deduplicator import encode_texts, find_most_similar, is_duplicate
from app.services.pain_scorer import calculate_pain_score, calculate_opportunity_score


def process_pending_posts() -> dict:
    """Process ALL pending posts in batches, looping until none remain."""
    from app.models.post import Post

    total_processed = 0
    total_new_pain_points = 0

    while True:
        db = SessionLocal()
        try:
            pending = db.query(Post).filter(Post.processed == 0).limit(settings.MAX_POSTS_PER_BATCH).all()
            if not pending:
                if total_processed == 0:
                    logger.info("No pending posts to process")
                break

            logger.info("Processing batch: {} posts", len(pending))

            posts_data = [
                {
                    "id": p.id,
                    "title": p.title,
                    "body": p.body or "",
                    "subreddit": p.subreddit,
                    "score": p.score or 0,
                    "num_comments": p.num_comments or 0,
                }
                for p in pending
            ]

            extracted = analyze_posts(posts_data)
            if not extracted:
                for p in pending:
                    p.processed = 1
                db.commit()
                total_processed += len(pending)
                continue

            existing_pps = db.query(PainPoint).all()
            existing_embeddings: list[tuple[int, list[float]]] = []
            if existing_pps:
                summaries = [pp.summary for pp in existing_pps]
                encodings = encode_texts(summaries)
                for pp, emb in zip(existing_pps, encodings):
                    existing_embeddings.append((pp.id, emb))

            if existing_embeddings:
                new_embeddings = encode_texts([e.get("summary", "") for e in extracted])
            else:
                new_embeddings = [[] for _ in extracted]

            batch_new_pps = 0
            for i, pp_data in enumerate(extracted):
                src_indices = pp_data.get("source_indices", [])
                if src_indices and isinstance(src_indices, list):
                    post_ids_for_pp = list({
                        posts_data[idx]["id"]
                        for idx in src_indices
                        if 0 <= idx < len(posts_data)
                    })
                else:
                    post_ids_for_pp = [p.id for p in pending]

                if not post_ids_for_pp:
                    post_ids_for_pp = [p.id for p in pending]

                best_id, best_score = find_most_similar(
                    new_embeddings[i], existing_embeddings
                ) if existing_embeddings else (None, -1.0)

                if best_id and is_duplicate(best_score):
                    _merge_pain_point(db, best_id, pp_data, post_ids_for_pp)
                else:
                    _create_pain_point(db, pp_data, post_ids_for_pp)
                    batch_new_pps += 1

            for p in pending:
                p.processed = 1

            db.commit()
            total_processed += len(pending)
            total_new_pain_points += batch_new_pps

            logger.info("Batch complete: {} processed, {} new pain points",
                        len(pending), batch_new_pps)
        except Exception as e:
            db.rollback()
            logger.error("Pipeline batch failed: {}", e)
            for p in db.query(Post).filter(Post.processed == 0).limit(
                settings.MAX_POSTS_PER_BATCH
            ).all():
                p.processed = 2
                p.error_message = str(e)[:500]
            db.commit()
            raise
        finally:
            db.close()

    logger.info("Pipeline complete: {} posts processed, {} new pain points",
                total_processed, total_new_pain_points)
    return {"processed": total_processed, "new_pain_points": total_new_pain_points}


def _create_pain_point(db, pp_data: dict, post_ids: list[int]) -> PainPoint:
    now = datetime.now(timezone.utc).isoformat()
    score_dims = {
        "emotion_intensity": pp_data.get("emotion_intensity", 0),
        "comment_volume": pp_data.get("comment_volume", 0),
        "repeat_frequency": pp_data.get("repeat_frequency", 0),
        "involves_money": pp_data.get("involves_money", 0),
        "has_paid_solution": pp_data.get("has_paid_solution", 0),
        "automation_difficulty": pp_data.get("automation_difficulty", 0),
        "is_long_term": pp_data.get("is_long_term", 0),
    }
    total = calculate_pain_score(score_dims)
    # AI returns individual_score on 0-10 scale; convert to 0-1 for weighted calculation
    ai_individual_raw = pp_data.get("individual_score", 0)
    individual_score_val = ai_individual_raw / 10.0
    opp_score = calculate_opportunity_score(total, individual_score_val)

    pp = PainPoint(
        title=pp_data.get("title", ""),
        summary=pp_data.get("summary", ""),
        category=pp_data.get("category"),
        industry=pp_data.get("industry"),
        pain_score=total,
        keywords=json.dumps(pp_data.get("keywords", [])),
        source_post_ids=json.dumps(post_ids),
        source_comment_ids=json.dumps([]),
        is_saas_idea=1 if pp_data.get("is_saas_idea") else 0,
        is_plugin_idea=1 if pp_data.get("is_plugin_idea") else 0,
        business_angle=pp_data.get("business_angle"),
        created_at=now,
        updated_at=now,
        is_individual_feasible=1 if pp_data.get("is_individual_feasible") else 0,
        feasibility_reason=pp_data.get("feasibility_reason"),
        estimated_dev_time=pp_data.get("estimated_dev_time"),
        tech_stack_hints=json.dumps(pp_data.get("tech_stack_hints", [])),
        market_saturation=pp_data.get("market_saturation"),
        individual_score=pp_data.get("individual_score", 0.0),
        opportunity_score=opp_score,
    )
    db.add(pp)
    db.flush()

    ps = PainScore(
        pain_point_id=pp.id,
        emotion_intensity=score_dims["emotion_intensity"],
        comment_volume=score_dims["comment_volume"],
        repeat_frequency=score_dims["repeat_frequency"],
        involves_money=score_dims["involves_money"],
        has_paid_solution=score_dims["has_paid_solution"],
        automation_difficulty=score_dims["automation_difficulty"],
        is_long_term=score_dims["is_long_term"],
        total_score=total,
        calculated_at=now,
    )
    db.add(ps)
    return pp


def _merge_pain_point(db, pp_id: int, pp_data: dict, new_post_ids: list[int]) -> None:
    pp = db.query(PainPoint).filter(PainPoint.id == pp_id).first()
    if not pp:
        return
    existing_posts = json.loads(pp.source_post_ids or "[]")
    pp.source_post_ids = json.dumps(list(set(existing_posts + new_post_ids)))
    pp.updated_at = datetime.now(timezone.utc).isoformat()

    # Propagate feasibility fields from new analysis when present
    if pp_data.get("is_individual_feasible") is not None:
        pp.is_individual_feasible = 1 if pp_data["is_individual_feasible"] else 0
    if pp_data.get("individual_score") is not None:
        pp.individual_score = pp_data["individual_score"]
    if pp_data.get("feasibility_reason"):
        pp.feasibility_reason = pp_data["feasibility_reason"]
    if pp_data.get("estimated_dev_time"):
        pp.estimated_dev_time = pp_data["estimated_dev_time"]
    if pp_data.get("tech_stack_hints"):
        pp.tech_stack_hints = json.dumps(pp_data["tech_stack_hints"])
    if pp_data.get("market_saturation"):
        pp.market_saturation = pp_data["market_saturation"]
    # Recalculate opportunity score if we have both scores available
    if pp_data.get("individual_score") is not None:
        ai_raw = pp_data["individual_score"]
        pp.opportunity_score = calculate_opportunity_score(pp.pain_score, ai_raw / 10.0)
