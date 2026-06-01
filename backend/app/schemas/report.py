from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class StepStatus(BaseModel):
    step: str
    label: str
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class CrawlStatus(BaseModel):
    is_running: bool = False
    last_run_at: Optional[str] = None
    last_result: Optional[str] = None
    steps: list[StepStatus] = []
    model_ready: bool = False
