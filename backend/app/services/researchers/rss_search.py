from __future__ import annotations

import re

from loguru import logger

from app.config import settings
from app.schemas.research import ResearchFinding
from app.services.rate_limiter import RateLimiter, create_rate_limiter
from app.services.researchers.base import BaseResearcher

DEFAULT_RSS_FEEDS = [
    "https://www.ruanyifeng.com/blog/atom.xml",
    "https://www.v2ex.com/index.xml",
    "https://36kr.com/feed",
    "https://sspai.com/feed",
    "https://www.zhihu.com/rss",
]

MAX_RESULTS = 30


class RSSResearcher(BaseResearcher):
    platform_name = "rss"

    def __init__(self, rate_limiter: RateLimiter | None = None) -> None:
        super().__init__()
        self._rate_limiter = rate_limiter or create_rate_limiter()

    async def search(self, domain: str) -> list[ResearchFinding]:
        feeds = self._get_feed_urls()
        if not feeds:
            logger.warning("No RSS feeds configured")
            return []

        keywords = self._extract_keywords(domain)
        findings: list[ResearchFinding] = []
        seen_urls: set[str] = set()

        for feed_url in feeds:
            entries = await self._fetch_feed(feed_url)
            for entry in entries:
                if len(findings) >= MAX_RESULTS:
                    break
                combined = f"{entry.get('title', '')} {entry.get('summary', '')}"
                if not self._matches_keywords(combined, keywords):
                    continue
                url = entry.get("link", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                content = entry.get("summary", "")[:2000]
                if not content.strip() and url:
                    try:
                        from app.services.crawler import CrawlerService

                        crawler = CrawlerService(rate_limiter=self._rate_limiter)
                        content = await crawler.crawl(url)
                        await crawler.close()
                    except Exception:
                        pass

                findings.append(
                    ResearchFinding(
                        title=entry.get("title", ""),
                        content_snippet=content[:2000] if content else f"RSS entry about {domain}",
                        url=url,
                        platform=self.platform_name,
                        author=entry.get("author"),
                        published_at=entry.get("published"),
                    )
                )

        logger.info("RSS found {} results for '{}'", len(findings), domain)
        return findings

    async def _fetch_feed(self, url: str) -> list[dict]:
        try:
            await self._rate_limiter.wait()
            try:
                import feedparser

                client = self._build_http_client()
                resp = await client.get(url)
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)
            finally:
                self._rate_limiter.release()

            entries = []
            for entry in feed.entries[:20]:
                entries.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "author": entry.get("author"),
                    "published": entry.get("published"),
                })
            return entries
        except Exception as e:
            logger.warning("RSS fetch failed for {}: {}", url, e)
            return []

    @staticmethod
    def _extract_keywords(domain: str) -> list[str]:
        parts = re.split(r"[\s,，、]+", domain)
        return [p.strip().lower() for p in parts if len(p.strip()) >= 2]

    @staticmethod
    def _matches_keywords(text: str, keywords: list[str]) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)

    @staticmethod
    def _get_feed_urls() -> list[str]:
        custom = settings.RSS_FEEDS.strip()
        if custom:
            return [u.strip() for u in custom.split(",") if u.strip()]
        return DEFAULT_RSS_FEEDS
