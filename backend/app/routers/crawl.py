from __future__ import annotations

import threading
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from loguru import logger
from pydantic import BaseModel

from app.auth import verify_admin_token
from app.schemas import ApiResponse
from app.schemas.report import CrawlStatus

router = APIRouter()

STEPS = [
    {"step": "crawl_reddit", "label": "Reddit 抓取"},
    {"step": "crawl_hn", "label": "HN 抓取"},
    {"step": "analyze", "label": "AI 分析"},
    {"step": "report", "label": "日报生成"},
]

_crawl_state: dict = {
    "is_running": False,
    "last_run_at": None,
    "last_result": None,
    "steps": [],
}
_lock = threading.Lock()


def _init_steps():
    _crawl_state["steps"] = [
        {
            "step": s["step"],
            "label": s["label"],
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
            "message": None,
        }
        for s in STEPS
    ]


def _step_index(step_name: str) -> int:
    for i, s in enumerate(STEPS):
        if s["step"] == step_name:
            return i
    return 0


def _update_step(i: int, **kwargs):
    with _lock:
        _crawl_state["steps"][i].update(kwargs)


def _run_pipeline(start_step: str):
    start_idx = _step_index(start_step)

    with _lock:
        _init_steps()
        _crawl_state["last_run_at"] = datetime.now(timezone.utc).isoformat()

    for i in range(len(STEPS)):
        if i < start_idx:
            _update_step(i, status="skipped")
            continue

        _update_step(i, status="running", started_at=datetime.now(timezone.utc).isoformat(), message="正在执行...")

        try:
            if STEPS[i]["step"] == "crawl_reddit":
                from app.services.reddit_crawler import crawl_subreddits
                result = crawl_subreddits()
            elif STEPS[i]["step"] == "crawl_hn":
                from app.services.hn_crawler import crawl_hn
                result = crawl_hn()
            elif STEPS[i]["step"] == "analyze":
                from app.services.deduplicator import is_model_ready

                if not is_model_ready():
                    raise RuntimeError("Embedding 模型未加载，请等待服务初始化完成")
                _update_step(i, message="正在调用 AI 分析...")
                from app.services.pipeline import process_pending_posts
                result = process_pending_posts()
            elif STEPS[i]["step"] == "report":
                from app.services.report_generator import generate_daily_report
                result = generate_daily_report()
            else:
                result = {}

            _update_step(
                i,
                status="completed",
                completed_at=datetime.now(timezone.utc).isoformat(),
                result=result,
                message=None,
            )
            logger.info("Step {} completed: {}", STEPS[i]["step"], result)
        except Exception as e:
            _update_step(
                i,
                status="failed",
                completed_at=datetime.now(timezone.utc).isoformat(),
                error=str(e),
                message=None,
            )
            logger.error("Step {} failed: {}", STEPS[i]["step"], e)
            with _lock:
                _crawl_state["last_result"] = f"failed at step {STEPS[i]['step']}: {e}"
                _crawl_state["is_running"] = False
            return

    with _lock:
        _crawl_state["last_result"] = "all steps completed"
        _crawl_state["is_running"] = False


class CrawlTriggerRequest(BaseModel):
    start_step: str = "crawl_reddit"


@router.post("/trigger")
def trigger_crawl(
    body: CrawlTriggerRequest | None = None,
    _token: str = Depends(verify_admin_token),
):
    with _lock:
        if _crawl_state["is_running"]:
            return ApiResponse(data={"message": "Crawl already in progress"})
        _crawl_state["is_running"] = True

    start_step = body.start_step if body else "crawl_reddit"
    thread = threading.Thread(target=_run_pipeline, args=(start_step,), daemon=True)
    thread.start()

    return ApiResponse(data={"message": "Pipeline started", "start_step": start_step})


@router.get("/status")
def crawl_status():
    from app.services.deduplicator import is_model_ready

    with _lock:
        state_copy = {
            "is_running": _crawl_state["is_running"],
            "last_run_at": _crawl_state["last_run_at"],
            "last_result": _crawl_state["last_result"],
            "steps": [dict(s) for s in _crawl_state["steps"]],
            "model_ready": is_model_ready(),
        }
    return ApiResponse(data=CrawlStatus(**state_copy))
