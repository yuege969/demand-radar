from __future__ import annotations

from loguru import logger

from app.config import settings
from app.schemas.research import ResearchFinding
from app.services.rate_limiter import RateLimiter, create_rate_limiter
from app.services.researchers.base import BaseResearcher

GITHUB_SEARCH_URL = "https://api.github.com/search/issues"

QUERY_TEMPLATES = [
    '"{domain}" pain point',
    '"{domain}" frustrated wish',
    '"{domain}" need tool',
    '"{domain}" hard to find',
]

RESULTS_PER_QUERY = 10
MAX_TOTAL_RESULTS = 40


class GitHubResearcher(BaseResearcher):
    platform_name = "github"

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

        logger.info("GitHub found {} results for '{}'", len(findings), domain)
        return findings

    async def _search_query(self, query: str) -> list[ResearchFinding]:
        try:
            await self._rate_limiter.wait()
            try:
                headers = {"Accept": "application/vnd.github.v3+json"}
                if settings.GITHUB_TOKEN:
                    headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

                params = {
                    "q": f"{query} type:issue",
                    "sort": "comments",
                    "order": "desc",
                    "per_page": RESULTS_PER_QUERY,
                }

                client = self._build_http_client()
                resp = await client.get(GITHUB_SEARCH_URL, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            finally:
                self._rate_limiter.release()

            items = data.get("items", [])
            results = []
            for item in items:
                title = item.get("title", "")
                url = item.get("html_url", "")
                body = (item.get("body") or "")[:2000]
                labels = [lb.get("name", "") for lb in item.get("labels", [])]

                results.append(
                    ResearchFinding(
                        title=title,
                        content_snippet=body,
                        url=url,
                        platform=self.platform_name,
                        author=item.get("user", {}).get("login"),
                        published_at=item.get("created_at"),
                        engagement={
                            "comments": item.get("comments", 0),
                            "reactions": item.get("reactions", {}).get("total_count", 0),
                            "labels": labels,
                        },
                    )
                )
            return results

        except Exception as e:
            logger.warning("GitHub search failed for '{}': {}", query, e)
            return []
