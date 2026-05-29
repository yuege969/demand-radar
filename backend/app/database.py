from __future__ import annotations

import os
from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Base

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    if settings.DATABASE_URL.startswith("sqlite:///"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if not db_path.startswith("/"):
            db_path = os.path.join(os.getcwd(), db_path)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info("Created database directory: {}", db_dir)

    try:
        from alembic import command
        from alembic.config import Config

        backend_dir = Path(__file__).resolve().parent.parent
        alembic_ini = backend_dir / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully")
    except Exception as exc:
        logger.warning("Alembic migration failed ({}), creating tables via create_all", exc)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured via create_all")

    inspector = inspect(engine)
    logger.info("Database ready — tables: {}", inspector.get_table_names())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
