from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.daily_report import DailyReport


class DailyReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_date(self, date_str: str) -> Optional[DailyReport]:
        return self.db.query(DailyReport).filter(DailyReport.report_date == date_str).first()

    def upsert_report(self, report_date: str, summary: str, top_pain_ids: str, new_pain_ids: str, stats: str) -> DailyReport:
        existing = self.get_by_date(report_date)
        if existing:
            existing.summary = summary
            existing.top_pain_ids = top_pain_ids
            existing.new_pain_ids = new_pain_ids
            existing.stats = stats
            existing.created_at = datetime.utcnow().isoformat() + "Z"
        else:
            existing = DailyReport(
                report_date=report_date,
                summary=summary,
                top_pain_ids=top_pain_ids,
                new_pain_ids=new_pain_ids,
                stats=stats,
                created_at=datetime.utcnow().isoformat() + "Z",
            )
            self.db.add(existing)
        self.db.commit()
        self.db.refresh(existing)
        return existing
