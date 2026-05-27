from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import verify_admin_token
from app.schemas import ApiResponse
from app.schemas.report import CrawlStatus

router = APIRouter()

_crawl_state: dict = {
    "is_running": False,
    "last_run_at": None,
    "last_result": None,
}


class CrawlTriggerRequest(BaseModel):
    subreddits: Optional[list[str]] = None


@router.post("/trigger")
def trigger_crawl(
    body: CrawlTriggerRequest | None = None,
    _token: str = Depends(verify_admin_token),
):
    if _crawl_state["is_running"]:
        return ApiResponse(data={"message": "Crawl already in progress"})

    _crawl_state["is_running"] = True
    try:
        from app.services.reddit_crawler import crawl_subreddits
        from app.services.hn_crawler import crawl_hn
        from app.services.pipeline import process_pending_posts
        from app.services.report_generator import generate_daily_report

        subreddits = body.subreddits if body else None
        reddit_result = crawl_subreddits(subreddits)
        hn_result = crawl_hn()
        total_new = reddit_result["posts_fetched"] + hn_result["posts_fetched"]

        pipeline_result = process_pending_posts() if total_new > 0 else {"new_pain_points": 0}

        report_result = generate_daily_report()

        now = datetime.now(timezone.utc).isoformat()
        _crawl_state["last_run_at"] = now
        full_result = {
            "crawl": {"reddit": reddit_result, "hacker_news": hn_result, "total_posts": total_new},
            "pipeline": pipeline_result,
            "report": report_result,
        }
        _crawl_state["last_result"] = str(full_result)
        return ApiResponse(data=full_result)
    except Exception as e:
        _crawl_state["last_result"] = f"error: {e}"
        return ApiResponse(success=False, error=str(e))
    finally:
        _crawl_state["is_running"] = False


@router.get("/status")
def crawl_status():
    return ApiResponse(data=CrawlStatus(**_crawl_state))
