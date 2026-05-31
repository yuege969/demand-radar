from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings
from app.routers import api_router
from app.scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Demand Radar backend...")

    from app.database import init_db

    await asyncio.to_thread(init_db)

    from app.services.crawler_registry import CrawlerRegistry
    from app.services.reddit_crawler import RedditCrawler
    from app.services.hn_crawler import HackerNewsCrawler

    CrawlerRegistry.seed_default_sources()

    import json
    from app.database import SessionLocal
    from app.models.data_source import DataSource

    db = SessionLocal()
    try:
        reddit_ds = db.query(DataSource).filter(DataSource.name == "reddit").first()
        hn_ds = db.query(DataSource).filter(DataSource.name == "hackernews").first()
        if reddit_ds:
            CrawlerRegistry.register(RedditCrawler(json.loads(reddit_ds.config)))
        if hn_ds:
            CrawlerRegistry.register(HackerNewsCrawler(json.loads(hn_ds.config)))
    finally:
        db.close()

    from app.services.deduplicator import preload_model

    await asyncio.to_thread(preload_model)
    start_scheduler()
    yield
    shutdown_scheduler()
    logger.info("Demand Radar backend stopped")


app = FastAPI(title="Demand Radar API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error: {}", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "data": None, "error": "Internal server error", "meta": None},
    )


@app.get("/api/v1/health")
def health_check():
    return {"success": True, "data": {"status": "healthy"}, "error": None, "meta": None}
