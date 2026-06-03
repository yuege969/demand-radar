from __future__ import annotations

from fastapi import APIRouter

from app.routers import domains, pain_points, research

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(pain_points.router, prefix="/pain-points", tags=["pain-points"])
api_router.include_router(research.router, prefix="/research", tags=["research"])
api_router.include_router(domains.router, tags=["domains"])
