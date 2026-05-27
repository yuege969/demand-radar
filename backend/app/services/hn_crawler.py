"""HackerNews crawler using the Algolia HN Search API.

No authentication required. API docs: https://hn.algolia.com/api
Rate limits: generous; keep requests polite (≥200ms between calls).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.http_client import build_http_client
from app.models.comment import Comment
from app.models.post import Post

_HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
_HN_ITEM_URL = "https://hn.algolia.com/api/v1/items/{story_id}"

# Source label stored in the subreddit column to distinguish from Reddit posts
HN_SOURCE = "HackerNews"

# High-signal search queries targeting SaaS / developer pain points on HN
_HN_QUERIES = [
    "I wish there was a tool",
    "anyone else struggling with",
    "looking for an alternative to",
    "frustrating workflow",
    "automate repetitive",
    "pain point productivity",
    "need a better way",
    "tedious manual process",
    "bottleneck in our workflow",
    "Ask HN: tool recommendation",
]

_keywords: Optional[dict[str, list[str]]] = None


def _load_keywords() -> dict[str, list[str]]:
    global _keywords
    if _keywords is None:
        path = Path(__file__).parent.parent / "keywords.json"
        with open(path) as f:
            _keywords = json.load(f)
    return _keywords


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


def _fetch_comments(client: httpx.Client, story_id: str, post_id: int, db: Session, limit: int) -> int:
    """Fetch top-level comments for a story via the items endpoint."""
    fetched = 0
    try:
        resp = client.get(_HN_ITEM_URL.format(story_id=story_id), timeout=20.0)
        resp.raise_for_status()
        item = resp.json()
    except Exception as e:
        logger.warning("HN: failed to fetch comments for story {}: {}", story_id, e)
        return 0

    for child in (item.get("children") or [])[:limit]:
        cmt_id_raw = child.get("id")
        cmt_text = (child.get("text") or "").strip()
        if not cmt_id_raw or not cmt_text:
            continue
        cid = f"hn_c_{cmt_id_raw}"
        if db.query(Comment).filter(Comment.reddit_comment_id == cid).first():
            continue
        created_ts = child.get("created_at_i") or 0
        db.add(Comment(
            reddit_comment_id=cid,
            post_id=post_id,
            body=cmt_text,
            author=child.get("author"),
            score=child.get("points") or 0,
            created_utc=datetime.fromtimestamp(created_ts, tz=timezone.utc).isoformat(),
            fetched_at=datetime.now(timezone.utc).isoformat(),
        ))
        fetched += 1
    return fetched


def _crawl_hn(
    db: Session,
    keywords: dict[str, list[str]],
    hits_per_page: int = 30,
    comment_limit: int = 5,
) -> tuple[int, int]:
    posts_fetched = 0
    comments_fetched = 0
    seen_ids: set[str] = set()

    with build_http_client(timeout=30.0) as client:
        for query in _HN_QUERIES:
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

                if db.query(Post).filter(Post.reddit_id == source_id).first():
                    continue

                title = (hit.get("title") or "").strip()
                body = (hit.get("story_text") or "").strip()
                if not _matches_keyword(f"{title} {body}", keywords):
                    continue

                post = Post(
                    reddit_id=source_id,
                    title=title,
                    body=body or None,
                    url=hit.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                    subreddit=HN_SOURCE,
                    author=hit.get("author"),
                    score=hit.get("points") or 0,
                    num_comments=hit.get("num_comments") or 0,
                    created_utc=_parse_hn_datetime(hit.get("created_at")),
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                    processed=0,
                )
                db.add(post)
                db.flush()
                posts_fetched += 1

                if comment_limit > 0:
                    time.sleep(0.3)
                    comments_fetched += _fetch_comments(client, story_id, post.id, db, comment_limit)

            time.sleep(0.3)  # polite pause between queries

    return posts_fetched, comments_fetched


def crawl_hn() -> dict:
    """Crawl HackerNews via Algolia API. Returns crawl summary dict."""
    keywords = _load_keywords()
    db = SessionLocal()
    try:
        p, c = _crawl_hn(db, keywords)
        db.commit()
        result = {"posts_fetched": p, "comments_fetched": c, "errors": 0, "source": HN_SOURCE}
        logger.info("HN crawl complete: {}", result)
        return result
    except Exception as e:
        logger.error("HN crawl failed: {}", e)
        db.rollback()
        return {"posts_fetched": 0, "comments_fetched": 0, "errors": 1, "source": HN_SOURCE, "message": str(e)}
    finally:
        db.close()
