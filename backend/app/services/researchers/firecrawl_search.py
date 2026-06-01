from __future__ import annotations

from firecrawl import AsyncFirecrawl
from firecrawl.v2.types import ScrapeOptions
from loguru import logger

from app.config import settings
from app.schemas.research import ResearchFinding
from app.services.rate_limiter import RateLimiter, create_rate_limiter
from app.services.researchers.base import BaseResearcher

QUERY_TEMPLATES = [
    "{domain} 痛点",
    "{domain} 吐槽",
    "{domain} 需求 工具 推荐",
    "{domain} 不好用 问题",
    "{domain} 希望 改进",
]

RESULTS_PER_QUERY = 10
MAX_TOTAL_RESULTS = 40


class FirecrawlResearcher(BaseResearcher):
    platform_name = "web"

    def __init__(self, rate_limiter: RateLimiter | None = None) -> None:
        super().__init__()
        self._rate_limiter = rate_limiter or create_rate_limiter()
        api_key = settings.FIRECRAWL_API_KEY
        api_url = settings.FIRECRAWL_API_BASE or "https://api.firecrawl.dev"
        self._app = AsyncFirecrawl(api_key=api_key, api_url=api_url)

    async def search(self, domain: str) -> list[ResearchFinding]:
        findings: list[ResearchFinding] = []
        seen_urls: set[str] = set()

        for template in QUERY_TEMPLATES:
            query = template.format(domain=domain)
            results = await self._search_query(query)
            for r in results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    findings.append(r)

            if len(findings) >= MAX_TOTAL_RESULTS:
                break

        logger.info("Firecrawl found {} results for '{}'", len(findings), domain)
        return findings

    async def _search_query(self, query: str) -> list[ResearchFinding]:
        try:
            await self._rate_limiter.wait()
            try:
                result = await self._app.search(
                    query=query,
                    limit=RESULTS_PER_QUERY,
                    scrape_options=ScrapeOptions(formats=["markdown"]),
                )
            finally:
                self._rate_limiter.release()

            items = list(result.web or [])

            findings = []
            for item in items:
                md = getattr(item, "metadata", None)
                if md is not None:
                    title = md.title or ""
                    url = md.url or ""
                else:
                    title = getattr(item, "title", None) or ""
                    url = getattr(item, "url", None) or ""
                markdown = getattr(item, "markdown", None) or getattr(item, "description", None) or ""
                findings.append(
                    ResearchFinding(
                        title=title,
                        content_snippet=markdown[:2000],
                        url=url,
                    )
                )
            return findings

        except Exception as e:
            logger.warning("Firecrawl search failed for '{}': {}", query, e)
            return []
