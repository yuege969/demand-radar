from __future__ import annotations

from loguru import logger

from app.schemas.research import ResearchFinding
from app.services.rate_limiter import RateLimiter, create_rate_limiter
from app.services.researchers.base import BaseResearcher

HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"

QUERY_TEMPLATES = [
    "{domain} pain point",
    "{domain} frustrated",
    "{domain} tool wishlist",
    "{domain} hard to",
    "{domain} alternative",
]

RESULTS_PER_QUERY = 10
MAX_TOTAL_RESULTS = 40


class HNResearcher(BaseResearcher):
    platform_name = "hackernews"

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

        logger.info("HN found {} results for '{}'", len(findings), domain)
        return findings

    async def _search_query(self, query: str) -> list[ResearchFinding]:
        try:
            await self._rate_limiter.wait()
            try:
                async with self._build_http_client() as client:
                    params = {
                        "query": query,
                        "tags": "story",
                        "hitsPerPage": RESULTS_PER_QUERY,
                    }
                    resp = await client.get(HN_ALGOLIA_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()
            finally:
                self._rate_limiter.release()

            items = data.get("hits", [])
            results = []
            for item in items:
                title = item.get("title", "") or ""
                url = item.get("url", "") or f"https://news.ycombinator.com/item?id={item.get('objectID', '')}"
                snippet = (item.get("story_text") or item.get("comment_text") or "")[:2000]
                if not snippet:
                    snippet = f"points: {item.get('points', 0)}, comments: {item.get('num_comments', 0)}"
                results.append(
                    ResearchFinding(
                        title=title,
                        content_snippet=snippet,
                        url=url,
                        platform=self.platform_name,
                        author=item.get("author"),
                        published_at=item.get("created_at"),
                        engagement={"points": item.get("points", 0), "num_comments": item.get("num_comments", 0)},
                    )
                )
            return results

        except Exception as e:
            logger.warning("HN search failed for '{}': {}", query, e)
            return []
