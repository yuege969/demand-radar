"""Abstract base class for all data source crawlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session


@dataclass
class CrawlResult:
    source_name: str = ""
    posts_fetched: int = 0
    comments_fetched: int = 0
    posts_after_filter: int = 0
    errors: int = 0
    message: str = ""


class BaseCrawler(ABC):
    """Abstract crawler that every data source must implement."""

    def __init__(self, config: dict) -> None:
        self.config = config

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique source identifier: 'reddit', 'hackernews', etc."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name: 'Reddit', 'HackerNews', etc."""
        ...

    @abstractmethod
    def crawl(self, db: Session) -> CrawlResult:
        """Execute crawl and persist new posts/comments to the database."""
        ...

    def _log_crawl(self, db: Session, result: CrawlResult) -> None:
        from app.models.crawl_log import CrawlLog

        now = datetime.now(timezone.utc).isoformat()
        log = CrawlLog(
            source_name=self.source_name,
            started_at=now,
            completed_at=now,
            status="success" if result.errors == 0 else "partial",
            posts_fetched=result.posts_fetched,
            comments_fetched=result.comments_fetched,
            posts_after_filter=result.posts_after_filter,
            error_message=result.message if result.errors > 0 else None,
        )
        db.add(log)

    def _update_source_status(self, db: Session, result: CrawlResult) -> None:
        from app.models.data_source import DataSource

        now = datetime.now(timezone.utc).isoformat()
        ds = db.query(DataSource).filter(DataSource.name == self.source_name).first()
        if ds:
            ds.last_crawl_at = now
            ds.last_crawl_status = "success" if result.errors == 0 else "partial"
            ds.last_crawl_posts_fetched = result.posts_fetched
            ds.last_crawl_error = result.message if result.errors > 0 else None
