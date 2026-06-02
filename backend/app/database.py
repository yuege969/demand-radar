from __future__ import annotations

import os
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

    import app.models.pain_point  # noqa: F401
    import app.models.pain_score  # noqa: F401

    import app.models.research_job  # noqa: F401
    import app.models.research_finding  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created from ORM models")

    _migrate_pain_points(engine)

    inspector = inspect(engine)
    logger.info("Database ready — tables: {}", inspector.get_table_names())


def _migrate_pain_points(eng) -> None:
    """Add new columns to existing pain_points table (SQLite-safe)."""
    from sqlalchemy import text

    new_columns = [
        ("snapshot_summary", "TEXT"),
        ("snapshot_opportunity", "TEXT"),
        ("snapshot_at", "TEXT"),
        ("enrichment_data", "TEXT"),
    ]
    with eng.connect() as conn:
        for col_name, col_type in new_columns:
            try:
                conn.execute(text(f"ALTER TABLE pain_points ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                logger.info("Added column pain_points.{}", col_name)
            except Exception:
                pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
