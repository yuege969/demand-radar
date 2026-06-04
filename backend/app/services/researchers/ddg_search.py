from __future__ import annotations

from loguru import logger

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


class DDGSearchResearcher(BaseResearcher):
    platform_name = "web"

    def __init__(self, rate_limiter: RateLimiter | None = None) -> None:
        super().__init__()
        self._rate_limiter = rate_limiter or create_rate_limiter()

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

        logger.info("DDG found {} results for '{}'", len(findings), domain)
        return findings

    async def _search_query(self, query: str) -> list[ResearchFinding]:
        try:
            await self._rate_limiter.wait()
            try:
                from ddgs import DDGS

                results = []
                with DDGS(timeout=30) as ddgs:
                    for r in ddgs.text(query, max_results=RESULTS_PER_QUERY):
                        title = r.get("title", "") or ""
                        url = r.get("href", "") or ""
                        snippet = (r.get("body", "") or "")[:2000]
                        results.append(
                            ResearchFinding(
                                title=title,
                                content_snippet=snippet,
                                url=url,
                                platform=self.platform_name,
                            )
                        )
            finally:
                self._rate_limiter.release()
            return results

        except ImportError:
            logger.warning("ddgs not installed, DDG search disabled")
            return []
        except Exception as e:
            logger.warning("DDG search failed for '{}': {}", query, e)
            return []
