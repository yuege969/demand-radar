from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.daily_report import DailyReport
from app.models.pain_point import PainPoint
from app.schemas import ApiResponse
from app.schemas.report import ReportSummary

router = APIRouter()


@router.get("/daily-report")
def get_daily_report(
    date: str | None = None,
    db: Session = Depends(get_db),
):
    from datetime import date as dt_date
    report_date = date or dt_date.today().isoformat()
    report = db.query(DailyReport).filter(DailyReport.report_date == report_date).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"No report for {report_date}")

    top_pains = []
    if report.top_pain_ids:
        try:
            ids = json.loads(report.top_pain_ids)
            points = db.query(PainPoint).filter(PainPoint.id.in_(ids)).all()
            top_pains = [{"id": p.id, "title": p.title, "pain_score": p.pain_score} for p in points]
        except (json.JSONDecodeError, TypeError):
            pass

    new_pains = []
    if report.new_pain_ids:
        try:
            ids = json.loads(report.new_pain_ids)
            points = db.query(PainPoint).filter(PainPoint.id.in_(ids)).all()
            new_pains = [{"id": p.id, "title": p.title, "pain_score": p.pain_score} for p in points]
        except (json.JSONDecodeError, TypeError):
            pass

    stats = json.loads(report.stats) if report.stats else {}

    return ApiResponse(
        data=ReportSummary(
            report_date=report.report_date,
            summary=report.summary,
            top_pains=top_pains,
            new_pains=new_pains,
            stats=stats,
        )
    )


@router.get("/trends")
def get_trends(
    days: int = Query(7, ge=1, le=90),
    category: str | None = None,
    db: Session = Depends(get_db),
):
    from datetime import date as dt_date, timedelta
    start_date = (dt_date.today() - timedelta(days=days - 1)).isoformat()

    reports = (
        db.query(DailyReport)
        .filter(DailyReport.report_date >= start_date)
        .order_by(DailyReport.report_date.asc())
        .all()
    )

    trend_data = []
    for r in reports:
        stats = json.loads(r.stats) if r.stats else {}
        trend_data.append({
            "date": r.report_date,
            "total_posts_crawled": stats.get("total_posts_crawled", 0),
            "new_pain_points": stats.get("new_pain_points", 0),
        })

    return ApiResponse(data=trend_data)
