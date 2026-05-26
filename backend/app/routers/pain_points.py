from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pain_point import PainPoint
from app.models.pain_score import PainScore
from app.models.post import Post
from app.schemas import ApiResponse, PaginationMeta
from app.schemas.pain_point import PainPointOut, PainPointDetail, PainScoreBreakdown

router = APIRouter()


def _to_pain_point_out(pp: PainPoint) -> PainPointOut:
    source_count = 0
    if pp.source_post_ids:
        try:
            source_count = len(json.loads(pp.source_post_ids))
        except (json.JSONDecodeError, TypeError):
            pass
    return PainPointOut(
        id=pp.id,
        title=pp.title,
        summary=pp.summary,
        category=pp.category,
        industry=pp.industry,
        pain_score=pp.pain_score or 0.0,
        keywords=pp.keywords,
        source_post_ids=pp.source_post_ids,
        is_saas_idea=bool(pp.is_saas_idea),
        is_plugin_idea=bool(pp.is_plugin_idea),
        business_angle=pp.business_angle,
        source_count=source_count,
        created_at=pp.created_at,
        updated_at=pp.updated_at,
    )


@router.get("")
def list_pain_points(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = None,
    industry: str | None = None,
    sort_by: str = Query("pain_score", pattern="^(pain_score|created_at|updated_at)$"),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(PainPoint)
    if category:
        query = query.filter(PainPoint.category == category)
    if industry:
        query = query.filter(PainPoint.industry == industry)
    if search:
        query = query.filter(
            PainPoint.title.ilike(f"%{search}%") | PainPoint.summary.ilike(f"%{search}%")
        )
    total = query.count()
    order_col = getattr(PainPoint, sort_by)
    points = query.order_by(order_col.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return ApiResponse(
        data=[_to_pain_point_out(p) for p in points],
        meta=PaginationMeta(page=page, per_page=per_page, total=total).model_dump(),
    )


@router.get("/{pain_point_id}")
def get_pain_point(pain_point_id: int, db: Session = Depends(get_db)):
    pp = db.query(PainPoint).filter(PainPoint.id == pain_point_id).first()
    if not pp:
        raise HTTPException(status_code=404, detail="Pain point not found")

    score = db.query(PainScore).filter(PainScore.pain_point_id == pain_point_id).first()
    breakdown = PainScoreBreakdown.model_validate(score) if score else None

    source_posts = []
    if pp.source_post_ids:
        try:
            ids = json.loads(pp.source_post_ids)
            source_posts = db.query(Post).filter(Post.id.in_(ids)).all()
        except (json.JSONDecodeError, TypeError):
            pass

    related = (
        db.query(PainPoint)
        .filter(
            PainPoint.id != pain_point_id,
            PainPoint.category == pp.category,
        )
        .order_by(PainPoint.pain_score.desc())
        .limit(5)
        .all()
    )

    from app.schemas.post import PostOut

    return ApiResponse(
        data=PainPointDetail(
            **_to_pain_point_out(pp).model_dump(),
            score_breakdown=breakdown,
            source_posts=[PostOut.model_validate(p) for p in source_posts],
            related=[_to_pain_point_out(r) for r in related],
        )
    )


@router.get("/categories/list")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(PainPoint.category).distinct().all()
    inds = db.query(PainPoint.industry).distinct().all()
    return ApiResponse(
        data={
            "categories": sorted(c[0] for c in cats if c[0]),
            "industries": sorted(i[0] for i in inds if i[0]),
        }
    )


@router.get("/search/all")
def search_all(
    q: str = Query(..., min_length=1),
    type: str = Query("all", pattern="^(all|posts|pain_points)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = []
    total = 0
    if type in ("all", "pain_points"):
        query = db.query(PainPoint).filter(
            PainPoint.title.ilike(f"%{q}%") | PainPoint.summary.ilike(f"%{q}%")
        )
        total = query.count()
        results = [
            {"type": "pain_point", **PainPointOut.model_validate(p).model_dump()}
            for p in query.limit(per_page).offset((page - 1) * per_page).all()
        ]
    return ApiResponse(
        data=results,
        meta=PaginationMeta(page=page, per_page=per_page, total=total).model_dump(),
    )
