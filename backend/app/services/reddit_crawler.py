from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.http_client import build_http_client
from app.models.post import Post
from app.models.comment import Comment

DEFAULT_SUBREDDITS = [
    "SaaS", "automation", "smallbusiness", "entrepreneur",
    "sideproject", "devops", "webdev", "productivity",
]

# Public Reddit API requires a descriptive User-Agent (not a browser default)
_PUBLIC_HEADERS = {"User-Agent": settings.REDDIT_USER_AGENT}

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


def _build_reddit_client():  # type: ignore[return]
    try:
        import praw  # type: ignore[import-untyped]
    except ImportError:
        raise RuntimeError("praw not installed")
    if not settings.REDDIT_CLIENT_ID:
        raise RuntimeError("REDDIT_CLIENT_ID not configured")
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
    )


def _crawl_subreddit(
    reddit,  # praw.Reddit
    subreddit_name: str,
    db: Session,
    keywords: dict[str, list[str]],
    post_limit: int = 25,
    comment_limit: int = 10,
) -> tuple[int, int]:
    posts_fetched = 0
    comments_fetched = 0
    subreddit = reddit.subreddit(subreddit_name)

    for submission in subreddit.hot(limit=post_limit):
        reddit_id = f"t3_{submission.id}"
        existing = db.query(Post).filter(Post.reddit_id == reddit_id).first()
        if existing:
            continue

        title = submission.title or ""
        body = submission.selftext or ""
        text = f"{title} {body}"

        if not _matches_keyword(text, keywords):
            continue

        post = Post(
            reddit_id=reddit_id,
            title=title,
            body=body or None,
            url=f"https://reddit.com{submission.permalink}",
            subreddit=subreddit_name,
            author=str(submission.author) if submission.author else None,
            score=submission.score,
            num_comments=submission.num_comments,
            created_utc=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat(),
            fetched_at=datetime.now(timezone.utc).isoformat(),
            processed=0,
        )
        db.add(post)
        db.flush()
        posts_fetched += 1

        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list()[:comment_limit]:
            cid = f"t1_{comment.id}"
            existing_comment = db.query(Comment).filter(Comment.reddit_comment_id == cid).first()
            if existing_comment:
                continue
            cmt = Comment(
                reddit_comment_id=cid,
                post_id=post.id,
                body=comment.body or "",
                author=str(comment.author) if comment.author else None,
                score=comment.score,
                created_utc=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).isoformat(),
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
            db.add(cmt)
            comments_fetched += 1

    return posts_fetched, comments_fetched


def _crawl_subreddit_public(
    subreddit_name: str,
    db: Session,
    keywords: dict[str, list[str]],
    post_limit: int = 25,
    comment_limit: int = 10,
) -> tuple[int, int]:
    """Crawl a subreddit using Reddit's public JSON API — no OAuth required."""
    posts_fetched = 0
    comments_fetched = 0

    with build_http_client(headers=_PUBLIC_HEADERS, timeout=30.0) as client:
        resp = client.get(
            f"https://www.reddit.com/r/{subreddit_name}/hot.json",
            params={"limit": post_limit},
        )
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])

    for child in children:
        pd = child.get("data", {})
        post_id = pd.get("id", "")
        if not post_id:
            continue
        reddit_id = f"t3_{post_id}"
        if db.query(Post).filter(Post.reddit_id == reddit_id).first():
            continue

        title = pd.get("title", "") or ""
        body = pd.get("selftext", "") or ""
        if not _matches_keyword(f"{title} {body}", keywords):
            continue

        created = pd.get("created_utc") or 0
        post = Post(
            reddit_id=reddit_id,
            title=title,
            body=body or None,
            url=f"https://reddit.com{pd.get('permalink', '')}",
            subreddit=subreddit_name,
            author=pd.get("author"),
            score=pd.get("score", 0) or 0,
            num_comments=pd.get("num_comments", 0) or 0,
            created_utc=datetime.fromtimestamp(created, tz=timezone.utc).isoformat(),
            fetched_at=datetime.now(timezone.utc).isoformat(),
            processed=0,
        )
        db.add(post)
        db.flush()
        posts_fetched += 1

        # Fetch comments (polite rate-limit: 1 req/s recommended by Reddit)
        time.sleep(1.0)
        try:
            with build_http_client(headers=_PUBLIC_HEADERS, timeout=30.0) as client:
                cr = client.get(
                    f"https://www.reddit.com/r/{subreddit_name}/comments/{post_id}.json",
                    params={"limit": comment_limit, "depth": 1},
                )
                cr.raise_for_status()
                comment_listing_data = cr.json()
            if len(comment_listing_data) > 1:
                for c in comment_listing_data[1].get("data", {}).get("children", [])[:comment_limit]:
                    cd = c.get("data", {})
                    cmt_id = cd.get("id", "")
                    cmt_body = cd.get("body", "") or ""
                    if not cmt_id or cmt_body in ("", "[deleted]", "[removed]"):
                        continue
                    cid = f"t1_{cmt_id}"
                    if db.query(Comment).filter(Comment.reddit_comment_id == cid).first():
                        continue
                    cmt_created = cd.get("created_utc") or 0
                    db.add(Comment(
                        reddit_comment_id=cid,
                        post_id=post.id,
                        body=cmt_body,
                        author=cd.get("author"),
                        score=cd.get("score", 0) or 0,
                        created_utc=datetime.fromtimestamp(cmt_created, tz=timezone.utc).isoformat(),
                        fetched_at=datetime.now(timezone.utc).isoformat(),
                    ))
                    comments_fetched += 1
        except Exception as e:
            logger.warning("Failed to fetch public comments for {}: {}", reddit_id, e)

    return posts_fetched, comments_fetched


def crawl_subreddits(subreddits: Optional[list[str]] = None) -> dict:
    target = subreddits or DEFAULT_SUBREDDITS
    keywords = _load_keywords()
    db = SessionLocal()
    total_posts = 0
    total_comments = 0
    errors = 0

    # Use PRAW (OAuth) when credentials are available; fall back to public JSON API otherwise
    use_praw = bool(settings.REDDIT_CLIENT_ID)
    reddit = None
    if use_praw:
        try:
            reddit = _build_reddit_client()
        except RuntimeError as e:
            logger.warning("PRAW init failed, falling back to public JSON API: {}", e)
            use_praw = False
    else:
        logger.info("REDDIT_CLIENT_ID not set — using Reddit public JSON API (no auth required)")

    for sr_name in target:
        try:
            if use_praw and reddit:
                p, c = _crawl_subreddit(reddit, sr_name, db, keywords)
            else:
                p, c = _crawl_subreddit_public(sr_name, db, keywords)
            total_posts += p
            total_comments += c
            logger.info("r/{}: {} new posts, {} new comments", sr_name, p, c)
        except Exception as e:
            errors += 1
            logger.error("Failed to crawl r/{}: {}", sr_name, e)

    try:
        db.commit()
        result = {"posts_fetched": total_posts, "comments_fetched": total_comments, "errors": errors}
        logger.info("Reddit crawl complete: {}", result)
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def crawl_job() -> None:
    """Hourly crawl job executed by APScheduler."""
    logger.info("Scheduled crawl job starting")
    try:
        crawl_subreddits()
    except Exception as e:
        logger.error("Scheduled crawl job failed: {}", e)
