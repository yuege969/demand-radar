from __future__ import annotations

import json
from datetime import date as dt_date, datetime, timezone

from loguru import logger

from app.database import SessionLocal
from app.models.pain_point import PainPoint
from app.repositories.daily_report_repo import DailyReportRepository


def generate_daily_report() -> dict:
    """Generate daily report for today. Executed by APScheduler and after crawl trigger."""
    db = SessionLocal()
    try:
        today = dt_date.today().isoformat()
        repo = DailyReportRepository(db)

        pain_points = db.query(PainPoint).all()
        total = len(pain_points)

        today_points = [
            p for p in pain_points
            if p.created_at and p.created_at[:10] == today
        ]
        sorted_by_score = sorted(pain_points, key=lambda p: p.pain_score or 0, reverse=True)

        top_ids = [p.id for p in sorted_by_score[:10]]
        new_ids = [p.id for p in today_points[:10]]

        summary = (
            f"今日累计收录 {total} 个需求，"
            f"其中新发现 {len(today_points)} 个。"
            f"TOP 需求类别：{_top_category(sorted_by_score)}。"
        )

        stats = json.dumps({
            "total_posts_crawled": 0,
            "new_pain_points": len(today_points),
            "total_pain_points": total,
            "trending_up": 0,
            "trending_down": 0,
        })

        repo.upsert_report(
            report_date=today,
            summary=summary,
            top_pain_ids=json.dumps(top_ids),
            new_pain_ids=json.dumps(new_ids),
            stats=stats,
        )

        logger.info("Daily report generated for {}: {} pain points", today, total)
        return {"report_date": today, "total": total, "new": len(today_points)}
    finally:
        db.close()


def _top_category(points: list[PainPoint]) -> str:
    from collections import Counter
    cats = Counter(p.category for p in points if p.category)
    return cats.most_common(1)[0][0] if cats else "unknown"
