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
from app.services.pain_scorer import calculate_pain_score


def process_pending_posts() -> dict:
    """Main pipeline: fetch pending posts, run AI analysis, dedup, and save pain points."""
    from app.models.post import Post

    db = SessionLocal()
    try:
        pending = db.query(Post).filter(Post.processed == 0).limit(settings.MAX_POSTS_PER_BATCH).all()
        if not pending:
            logger.info("No pending posts to process")
            return {"processed": 0, "new_pain_points": 0}

        logger.info("Processing {} pending posts", len(pending))

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
            return {"processed": len(pending), "new_pain_points": 0}

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

        new_count = 0
        for i, pp_data in enumerate(extracted):
            best_id, best_score = find_most_similar(new_embeddings[i], existing_embeddings) if existing_embeddings else (None, -1.0)

            if best_id and is_duplicate(best_score):
                _merge_pain_point(db, best_id, pending, pp_data)
                logger.debug("Merged duplicate pain point: '{}' (score={:.3f})", pp_data["title"], best_score)
            else:
                _create_pain_point(db, pp_data, [p.id for p in pending])
                new_count += 1

        for p in pending:
            p.processed = 1

        db.commit()
        logger.info("Pipeline complete: {} posts processed, {} new pain points", len(pending), new_count)
        return {"processed": len(pending), "new_pain_points": new_count}
    except Exception as e:
        db.rollback()
        logger.error("Pipeline failed: {}", e)
        for p in db.query(Post).filter(Post.processed == 0).limit(settings.MAX_POSTS_PER_BATCH).all():
            p.processed = 2
            p.error_message = str(e)[:500]
        db.commit()
        raise
    finally:
        db.close()


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


def _merge_pain_point(db, pp_id: int, posts: list, pp_data: dict) -> None:
    from app.models.pain_point import PainPoint
    pp = db.query(PainPoint).filter(PainPoint.id == pp_id).first()
    if not pp:
        return
    existing_posts = json.loads(pp.source_post_ids or "[]")
    new_posts = [p.id for p in posts]
    pp.source_post_ids = json.dumps(list(set(existing_posts + new_posts)))
    pp.updated_at = datetime.now(timezone.utc).isoformat()
