"""Registry that discovers and manages crawler implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from app.services.base_crawler import BaseCrawler


class CrawlerRegistry:
    """Holds all registered crawler instances, keyed by source name."""

    _crawlers: dict[str, BaseCrawler] = {}

    @classmethod
    def register(cls, crawler: BaseCrawler) -> None:
        cls._crawlers[crawler.source_name] = crawler
        logger.info("Registered crawler: {}", crawler.source_name)

    @classmethod
    def get(cls, name: str) -> BaseCrawler | None:
        return cls._crawlers.get(name)

    @classmethod
    def get_enabled(cls) -> list[BaseCrawler]:
        """Return crawlers whose DataSource is enabled in the database."""
        from app.database import SessionLocal
        from app.models.data_source import DataSource

        db = SessionLocal()
        try:
            enabled_names = {
                row.name
                for row in db.query(DataSource.name).filter(DataSource.enabled == 1).all()
            }
        finally:
            db.close()

        return [c for name, c in cls._crawlers.items() if name in enabled_names]

    @classmethod
    def list_all(cls) -> list[BaseCrawler]:
        return list(cls._crawlers.values())

    @classmethod
    def seed_default_sources(cls) -> None:
        """Insert default data sources if the table is empty."""
        from datetime import datetime, timezone

        from app.database import SessionLocal
        from app.models.data_source import DataSource

        now = datetime.now(timezone.utc).isoformat()
        defaults = [
            {
                "name": "reddit",
                "display_name": "Reddit",
                "source_type": "reddit",
                "config": '{"subreddits":["SaaS","automation","smallbusiness","entrepreneur","sideproject","devops","webdev","productivity"],"post_limit":25,"comment_limit":10}',
                "enabled": 1,
                "crawl_interval_minutes": 60,
                "created_at": now,
                "updated_at": now,
            },
            {
                "name": "hackernews",
                "display_name": "HackerNews",
                "source_type": "hackernews",
                "config": '{"queries":["I wish there was a tool","anyone else struggling with","looking for an alternative to","frustrating workflow","automate repetitive","pain point productivity","need a better way","tedious manual process","bottleneck in our workflow","Ask HN: tool recommendation"],"hits_per_page":30,"comment_limit":5}',
                "enabled": 1,
                "crawl_interval_minutes": 60,
                "created_at": now,
                "updated_at": now,
            },
        ]

        db = SessionLocal()
        try:
            existing = db.query(DataSource).first()
            if existing:
                return
            for ds_data in defaults:
                db.add(DataSource(**ds_data))
            db.commit()
            logger.info("Seeded {} default data sources", len(defaults))
        finally:
            db.close()
