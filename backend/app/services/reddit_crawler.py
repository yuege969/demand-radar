from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import praw
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.post import Post
from app.models.comment import Comment

DEFAULT_SUBREDDITS = [
    "SaaS", "automation", "smallbusiness", "entrepreneur",
    "sideproject", "devops", "webdev", "productivity",
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


def _build_reddit_client() -> praw.Reddit:
    if not settings.REDDIT_CLIENT_ID:
        raise RuntimeError("REDDIT_CLIENT_ID not configured")
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
    )


def _crawl_subreddit(
    reddit: praw.Reddit,
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


def crawl_subreddits(subreddits: Optional[list[str]] = None) -> dict:
    target = subreddits or DEFAULT_SUBREDDITS
    keywords = _load_keywords()
    db = SessionLocal()
    total_posts = 0
    total_comments = 0
    errors = 0

    try:
        reddit = _build_reddit_client()
    except RuntimeError as e:
        logger.warning("Reddit client not configured: {}", e)
        return {"posts_fetched": 0, "comments_fetched": 0, "errors": 1, "message": str(e)}

    for sr_name in target:
        try:
            p, c = _crawl_subreddit(reddit, sr_name, db, keywords)
            total_posts += p
            total_comments += c
            logger.info("r/{}: {} new posts, {} new comments", sr_name, p, c)
        except Exception as e:
            errors += 1
            logger.error("Failed to crawl r/{}: {}", sr_name, e)

    db.commit()
    db.close()
    result = {"posts_fetched": total_posts, "comments_fetched": total_comments, "errors": errors}
    logger.info("Crawl complete: {}", result)
    return result


def crawl_job() -> None:
    """Hourly crawl job executed by APScheduler."""
    logger.info("Scheduled crawl job starting")
    try:
        crawl_subreddits()
    except Exception as e:
        logger.error("Scheduled crawl job failed: {}", e)
