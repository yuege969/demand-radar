from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ReportSummary(BaseModel):
    report_date: str
    summary: str
    top_pains: list[dict[str, Any]] = []
    new_pains: list[dict[str, Any]] = []
    stats: dict[str, Any] = {}

    model_config = {"from_attributes": True}


class CrawlStatus(BaseModel):
    is_running: bool = False
    last_run_at: Optional[str] = None
    last_result: Optional[str] = None
