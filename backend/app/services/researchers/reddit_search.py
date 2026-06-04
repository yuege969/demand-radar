from __future__ import annotations

from loguru import logger

from app.schemas.research import ResearchFinding
from app.services.rate_limiter import RateLimiter, create_rate_limiter
from app.services.researchers.base import BaseResearcher

REDDIT_SEARCH_URL = "https://www.reddit.com/r/{subreddit}/search.json"

SUBREDDITS = [
    "SaaS",
    "startups",
    "SideProject",
    "alphaandbetausers",
    "selfhosted",
    "smallbusiness",
    "entrepreneur",
    "productivity",
]

QUERY_TEMPLATES = [
    "pain point {domain}",
    "looking for {domain} tool",
    "{domain} alternative",
    "frustrated with {domain}",
]

USER_AGENT = "demand-radar/0.1.0 (personal research tool)"

RESULTS_PER_QUERY = 10
MAX_TOTAL_RESULTS = 40


class RedditResearcher(BaseResearcher):
    platform_name = "reddit"

    def __init__(self, rate_limiter: RateLimiter | None = None) -> None:
        super().__init__()
        self._rate_limiter = rate_limiter or create_rate_limiter()

    async def search(self, domain: str) -> list[ResearchFinding]:
        findings: list[ResearchFinding] = []
        seen_urls: set[str] = set()

        for template in QUERY_TEMPLATES:
            query = template.format(domain=domain)
            for subreddit in SUBREDDITS:
                if len(findings) >= MAX_TOTAL_RESULTS:
                    break
                results = await self._search_subreddit(subreddit, query)
                for r in results:
                    if r.url not in seen_urls:
                        seen_urls.add(r.url)
                        findings.append(r)

            if len(findings) >= MAX_TOTAL_RESULTS:
                break

        logger.info("Reddit found {} results for '{}'", len(findings), domain)
        return findings

    async def _search_subreddit(self, subreddit: str, query: str) -> list[ResearchFinding]:
        try:
            await self._rate_limiter.wait()
            try:
                headers = {"User-Agent": USER_AGENT}
                params = {
                    "q": query,
                    "restrict_sr": "on",
                    "sort": "relevance",
                    "limit": RESULTS_PER_QUERY,
                }
                url = REDDIT_SEARCH_URL.format(subreddit=subreddit)
                client = self._build_http_client()
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            finally:
                self._rate_limiter.release()

            posts = data.get("data", {}).get("children", [])
            results = []
            for post in posts:
                pdata = post.get("data", {})
                title = pdata.get("title", "")
                permalink = pdata.get("permalink", "")
                url = f"https://www.reddit.com{permalink}" if permalink else ""
                selftext = (pdata.get("selftext") or "")[:2000]

                results.append(
                    ResearchFinding(
                        title=title,
                        content_snippet=selftext,
                        url=url,
                        platform=self.platform_name,
                        author=pdata.get("author"),
                        published_at=self._ts_to_iso(pdata.get("created_utc")),
                        engagement={
                            "score": pdata.get("score", 0),
                            "num_comments": pdata.get("num_comments", 0),
                            "subreddit": pdata.get("subreddit", ""),
                        },
                    )
                )
            return results

        except Exception as e:
            logger.warning("Reddit search failed for r/{} '{}': {}", subreddit, query, e)
            return []

    @staticmethod
    def _ts_to_iso(ts: float | None) -> str | None:
        if ts is None:
            return None
        from datetime import datetime, timezone

        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
