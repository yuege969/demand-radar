from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.domain_taxonomy import (
    DOMAIN_CATEGORIES,
    ROLES,
    get_role_by_key,
    get_vocabulary_by_category,
)
from app.database import get_db
from app.models.pain_point import PainPoint
from app.schemas import ApiResponse
from app.schemas.domain import (
    DomainCategoryOut,
    PainVocabularyOut,
    RoleOut,
    TaxonomyOut,
)

router = APIRouter(prefix="/domains", tags=["domains"])


def _build_role_stats(db: Session) -> dict[str, dict]:
    rows = (
        db.query(
            PainPoint.industry,
            func.count(PainPoint.id).label("cnt"),
            func.avg(PainPoint.opportunity_score).label("avg_score"),
        )
        .group_by(PainPoint.industry)
        .all()
    )
    stats: dict[str, dict] = {}
    for industry, cnt, avg_score in rows:
        if industry:
            stats[industry] = {"count": cnt, "avg_score": round(float(avg_score or 0), 1)}
    return stats


def _match_role_stats(role_name: str, stats: dict[str, dict]) -> dict:
    for industry, s in stats.items():
        if role_name in industry or industry in role_name:
            return s
    return {"count": 0, "avg_score": 0.0}


@router.get("/taxonomy")
def get_taxonomy(db: Session = Depends(get_db)):
    stats = _build_role_stats(db)

    roles_out = []
    for r in ROLES:
        rs = _match_role_stats(r.name, stats)
        roles_out.append(RoleOut(
            key=r.key,
            name=r.name,
            icon=r.icon,
            description=r.description,
            subtopics=r.subtopics,
            demand_count=rs["count"],
            avg_opportunity_score=rs["avg_score"],
        ))

    categories_out = [
        DomainCategoryOut(
            key=c.key,
            name=c.name,
            description=c.description,
            keywords=c.keywords,
        )
        for c in DOMAIN_CATEGORIES
    ]

    vocab_out = [
        PainVocabularyOut(category=cat, words=words)
        for cat, words in get_vocabulary_by_category().items()
    ]

    return ApiResponse(data=TaxonomyOut(
        roles=roles_out,
        categories=categories_out,
        pain_vocabulary=vocab_out,
    ))


@router.get("/roles")
def list_roles(db: Session = Depends(get_db)):
    stats = _build_role_stats(db)
    roles_out = []
    for r in ROLES:
        rs = _match_role_stats(r.name, stats)
        roles_out.append(RoleOut(
            key=r.key,
            name=r.name,
            icon=r.icon,
            description=r.description,
            subtopics=r.subtopics,
            demand_count=rs["count"],
            avg_opportunity_score=rs["avg_score"],
        ))
    return ApiResponse(data=roles_out)


@router.get("/roles/{key}")
def get_role_detail(key: str, db: Session = Depends(get_db)):
    role = get_role_by_key(key)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    stats = _build_role_stats(db)
    rs = _match_role_stats(role.name, stats)

    related = (
        db.query(PainPoint)
        .filter(PainPoint.industry.ilike(f"%{role.name}%"))
        .order_by(PainPoint.opportunity_score.desc())
        .limit(10)
        .all()
    )

    from app.routers.pain_points import _to_pain_point_out

    return ApiResponse(data={
        "role": RoleOut(
            key=role.key,
            name=role.name,
            icon=role.icon,
            description=role.description,
            subtopics=role.subtopics,
            demand_count=rs["count"],
            avg_opportunity_score=rs["avg_score"],
        ),
        "related_pain_points": [_to_pain_point_out(p) for p in related],
    })


@router.get("/pain-vocabulary")
def get_pain_vocabulary():
    vocab = [
        PainVocabularyOut(category=cat, words=words)
        for cat, words in get_vocabulary_by_category().items()
    ]
    return ApiResponse(data=vocab)


@router.get("/suggest")
def suggest_domains(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    rows = (
        db.query(PainPoint.industry)
        .filter(PainPoint.industry.ilike(f"%{q}%"))
        .distinct()
        .limit(10)
        .all()
    )
    suggestions = [r[0] for r in rows if r[0]]
    return ApiResponse(data={"suggestions": suggestions})
