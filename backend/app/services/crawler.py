from __future__ import annotations

from loguru import logger

from app.config import settings
from app.services.rate_limiter import RateLimiter, create_rate_limiter


class CrawlerService:
    """Shared service for crawling web pages to extract clean markdown using Crawl4AI."""

    def __init__(self, rate_limiter: RateLimiter | None = None) -> None:
        self._rate_limiter = rate_limiter or create_rate_limiter()
        self._crawler = None

    async def _ensure_crawler(self):
        if self._crawler is None:
            from crawl4ai import AsyncWebCrawler, BrowserConfig

            browser_cfg = BrowserConfig(headless=settings.CRAWL4AI_HEADLESS, verbose=False)
            self._crawler = AsyncWebCrawler(config=browser_cfg)
            await self._crawler.__aenter__()

    async def crawl(self, url: str) -> str:
        """Crawl a single URL and return clean markdown content."""
        try:
            await self._ensure_crawler()
            await self._rate_limiter.wait()
            try:
                from crawl4ai import CrawlerRunConfig

                config = CrawlerRunConfig(
                    word_count_threshold=settings.CRAWL4AI_WORD_COUNT_THRESHOLD,
                    exclude_external_links=True,
                )
                result = await self._crawler.arun(url=url, config=config)
                return (result.markdown or "")[:3000]
            finally:
                self._rate_limiter.release()
        except Exception as e:
            logger.warning("Crawl4AI failed for {}: {}", url, e)
            return ""

    async def crawl_many(self, urls: list[str]) -> list[str]:
        """Crawl multiple URLs and return markdown for each."""
        results = []
        for url in urls:
            content = await self.crawl(url)
            if content:
                results.append(content)
        return results

    async def close(self) -> None:
        if self._crawler is not None:
            try:
                await self._crawler.__aexit__(None, None, None)
            except Exception:
                pass
            self._crawler = None
