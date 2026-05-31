"""HackerNews crawler using the Algolia HN Search API."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.http_client import build_http_client
from app.models.comment import Comment
from app.models.post import Post
from app.services.base_crawler import BaseCrawler, CrawlResult

HN_SOURCE = "hackernews"
_HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
_HN_ITEM_URL = "https://hn.algolia.com/api/v1/items/{story_id}"

_keywords_cache: dict[str, list[str]] | None = None


def _load_keywords() -> dict[str, list[str]]:
    global _keywords_cache
    if _keywords_cache is None:
        path = Path(__file__).parent.parent / "keywords.json"
        with open(path) as f:
            _keywords_cache = json.load(f)
    return _keywords_cache


def _matches_keyword(text: str, keywords: dict[str, list[str]]) -> bool:
    text_lower = text.lower()
    for kw_list in keywords.values():
        for kw in kw_list:
            if kw.lower() in text_lower:
                return True
    return False


def _parse_hn_datetime(value: str | None) -> str:
    if not value:
        return datetime.now(timezone.utc).isoformat()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return datetime.now(timezone.utc).isoformat()


class HackerNewsCrawler(BaseCrawler):
    source_name = "hackernews"
    display_name = "HackerNews"

    def crawl(self, db: Session) -> CrawlResult:
        keywords = _load_keywords()
        queries = self.config.get("queries", [])
        hits_per_page = self.config.get("hits_per_page", 30)
        comment_limit = self.config.get("comment_limit", 5)

        if not queries:
            return CrawlResult(source_name=self.source_name, errors=1, message="No queries configured")

        result = CrawlResult(source_name=self.source_name)
        seen_ids: set[str] = set()

        with build_http_client(timeout=30.0) as client:
            for query in queries:
                try:
                    resp = client.get(
                        _HN_SEARCH_URL,
                        params={
                            "query": query,
                            "tags": "(ask_hn,show_hn,story)",
                            "hitsPerPage": hits_per_page,
                        },
                    )
                    resp.raise_for_status()
                    hits = resp.json().get("hits", [])
                except Exception as e:
                    logger.warning("HN search failed for query '{}': {}", query, e)
                    time.sleep(0.5)
                    continue

                for hit in hits:
                    story_id = str(hit.get("objectID", ""))
                    if not story_id:
                        continue
                    source_id = f"hn_{story_id}"
                    if source_id in seen_ids:
                        continue
                    seen_ids.add(source_id)

                    if db.query(Post).filter(Post.external_id == source_id).first():
                        continue

                    title = (hit.get("title") or "").strip()
                    body = (hit.get("story_text") or "").strip()
                    if not _matches_keyword(f"{title} {body}", keywords):
                        continue

                    now = datetime.now(timezone.utc).isoformat()
                    post = Post(
                        external_id=source_id,
                        source=HN_SOURCE,
                        title=title,
                        body=body or None,
                        url=hit.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                        subreddit="HackerNews",
                        author=hit.get("author"),
                        score=hit.get("points") or 0,
                        num_comments=hit.get("num_comments") or 0,
                        created_utc=_parse_hn_datetime(hit.get("created_at")),
                        fetched_at=now,
                        analysis_stage="pending",
                        processed=0,
                    )
                    db.add(post)
                    db.flush()
                    result.posts_fetched += 1

                    if comment_limit > 0:
                        time.sleep(0.3)
                        result.comments_fetched += self._fetch_comments(client, story_id, post.id, db, comment_limit)

                time.sleep(0.3)

        result.posts_after_filter = result.posts_fetched
        self._log_crawl(db, result)
        self._update_source_status(db, result)
        return result

    @staticmethod
    def _fetch_comments(client: httpx.Client, story_id: str, post_id: int, db: Session, limit: int) -> int:
        fetched = 0
        try:
            resp = client.get(_HN_ITEM_URL.format(story_id=story_id), timeout=20.0)
            resp.raise_for_status()
            item = resp.json()
        except Exception as e:
            logger.warning("HN: failed to fetch comments for story {}: {}", story_id, e)
            return 0

        now = datetime.now(timezone.utc).isoformat()
        for child in (item.get("children") or [])[:limit]:
            cmt_id_raw = child.get("id")
            cmt_text = (child.get("text") or "").strip()
            if not cmt_id_raw or not cmt_text:
                continue
            cid = f"hn_c_{cmt_id_raw}"
            if db.query(Comment).filter(Comment.external_id == cid).first():
                continue
            created_ts = child.get("created_at_i") or 0
            db.add(Comment(
                external_id=cid,
                post_id=post_id,
                body=cmt_text,
                author=child.get("author"),
                score=child.get("points") or 0,
                created_utc=datetime.fromtimestamp(created_ts, tz=timezone.utc).isoformat(),
                fetched_at=now,
            ))
            fetched += 1
        return fetched
