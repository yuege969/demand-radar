from __future__ import annotations

from fastapi import APIRouter

from app.routers import posts, pain_points, reports, crawl

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(pain_points.router, prefix="/pain-points", tags=["pain-points"])
api_router.include_router(reports.router, prefix="", tags=["reports"])
api_router.include_router(crawl.router, prefix="/crawl", tags=["crawl"])
