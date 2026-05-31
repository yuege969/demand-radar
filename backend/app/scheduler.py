from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from app.config import settings
from app.database import SessionLocal

scheduler = BackgroundScheduler()


def _scheduled_crawl() -> None:
    from app.services.crawler_registry import CrawlerRegistry
    from app.services.pipeline import process_pending_posts
    from app.services.report_generator import generate_daily_report

    logger.info("Scheduled crawl job starting")
    db = SessionLocal()
    try:
        total_new = 0
        for crawler in CrawlerRegistry.get_enabled():
            try:
                result = crawler.crawl(db)
                db.commit()
                total_new += result.posts_fetched
                logger.info("{} crawl: {} posts", crawler.source_name, result.posts_fetched)
            except Exception as e:
                db.rollback()
                logger.error("{} crawl failed: {}", crawler.source_name, e)

        if total_new > 0:
            pipeline_result = process_pending_posts()
            logger.info("Pipeline result: {}", pipeline_result)

        generate_daily_report()
    except Exception as e:
        logger.error("Scheduled crawl job failed: {}", e)
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(
        _scheduled_crawl,
        "interval",
        minutes=settings.CRAWL_INTERVAL_MINUTES,
        id="crawl",
    )
    scheduler.add_job(
        lambda: __import__("app.services.report_generator", fromlist=["generate_daily_report"]).generate_daily_report(),
        "cron",
        hour=settings.REPORT_GENERATION_HOUR,
        minute=7,
        id="daily_report",
    )
    scheduler.start()
    logger.info(
        "Scheduler started: crawl every {}min, daily report at {:02d}:07",
        settings.CRAWL_INTERVAL_MINUTES,
        settings.REPORT_GENERATION_HOUR,
    )


def shutdown_scheduler() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler shut down")
