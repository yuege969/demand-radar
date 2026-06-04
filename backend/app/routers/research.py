from __future__ import annotations

import asyncio
import json
import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import verify_admin_token
from app.database import get_db
from app.models.pain_point import PainPoint
from app.models.research_job import ResearchJob
from app.schemas import ApiResponse, PaginationMeta

router = APIRouter()

_DOMAIN_PATTERN = re.compile(r"^[\w一-鿿\s\-.,&+()]+$")
_DOMAIN_MAX_LENGTH = 100
_enriching_jobs: set[int] = set()


def _sanitize_domain(raw: str) -> str:
    cleaned = raw.strip()
    if len(cleaned) > _DOMAIN_MAX_LENGTH:
        cleaned = cleaned[:_DOMAIN_MAX_LENGTH]
    if not cleaned or not _DOMAIN_PATTERN.match(cleaned):
        raise HTTPException(status_code=400, detail="Domain contains invalid characters")
    return cleaned


class ResearchRequest(BaseModel):
    domain: str
    platforms: list[str] = ["web", "hackernews", "github", "rss"]


def _create_job(domain: str, platforms: list[str]) -> ResearchJob:
    from datetime import datetime, timezone

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        job = ResearchJob(
            domain=domain,
            platforms=json.dumps(platforms),
            status="running",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    finally:
        db.close()


def _run_research_sync(job_id: int, domain: str, platforms: list[str]):
    try:
        from app.services.research_orchestrator import run_research

        asyncio.run(run_research(domain, platforms, job_id=job_id))
    except Exception as e:
        logger.error("Research job {} failed: {}", job_id, e)


def _job_to_dict(job: ResearchJob) -> dict:
    return {
        "id": job.id,
        "domain": job.domain,
        "platforms": json.loads(job.platforms) if job.platforms else [],
        "status": job.status,
        "total_findings": job.total_findings or 0,
        "pain_points_extracted": job.pain_points_extracted or 0,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "is_enriching": job.id in _enriching_jobs,
    }


@router.post("")
def create_research(
    body: ResearchRequest,
    background_tasks: BackgroundTasks,
    _token: str = Depends(verify_admin_token),
):
    domain = _sanitize_domain(body.domain)
    job = _create_job(domain, body.platforms)
    background_tasks.add_task(_run_research_sync, job.id, domain, body.platforms)
    return ApiResponse(data={"job_id": job.id, "message": "Research started", "domain": domain})


@router.get("")
def list_research(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    total = db.query(ResearchJob).count()
    jobs = (
        db.query(ResearchJob)
        .order_by(ResearchJob.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return ApiResponse(
        data=[_job_to_dict(j) for j in jobs],
        meta=PaginationMeta(page=page, per_page=per_page, total=total).model_dump(),
    )


@router.get("/{job_id}")
def get_research(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")
    return ApiResponse(data=_job_to_dict(job))


@router.get("/{job_id}/pain-points")
def get_research_pain_points(
    job_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")

    query = db.query(PainPoint).filter(PainPoint.research_job_id == job_id)
    total = query.count()
    points = (
        query.order_by(PainPoint.opportunity_score.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    from app.routers.pain_points import _to_pain_point_out

    return ApiResponse(
        data=[_to_pain_point_out(p) for p in points],
        meta=PaginationMeta(page=page, per_page=per_page, total=total).model_dump(),
    )


def _run_enrich_sync(job_id: int):
    _enriching_jobs.add(job_id)
    try:
        from app.services.research_orchestrator import _enrich_pain_points

        asyncio.run(_enrich_pain_points(job_id))
    except Exception as e:
        logger.error("Re-enrich job {} failed: {}", job_id, e)
    finally:
        _enriching_jobs.discard(job_id)


@router.post("/{job_id}/re-enrich")
def re_enrich_job(job_id: int, background_tasks: BackgroundTasks):
    if job_id in _enriching_jobs:
        raise HTTPException(status_code=409, detail="Re-enrich already in progress for this job")

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        count = (
            db.query(PainPoint)
            .filter(PainPoint.research_job_id == job_id, PainPoint.enriched_at.is_(None))
            .count()
        )
    finally:
        db.close()

    if count == 0:
        return ApiResponse(data={"message": "No unenriched pain points", "enriched": 0})

    background_tasks.add_task(_run_enrich_sync, job_id)
    return ApiResponse(data={"message": f"Re-enrich started ({count} pain points queued)", "enriched": 0})
