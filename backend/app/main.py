from __future__ import annotations

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
    start_scheduler()
    yield
    shutdown_scheduler()
    logger.info("Demand Radar backend stopped")


app = FastAPI(title="Demand Radar API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET"],
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
