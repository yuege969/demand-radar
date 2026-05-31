"""Reddit crawler using PRAW (OAuth) or public JSON API with browser-like session."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from app.config import settings
from app.models.comment import Comment
from app.models.post import Post
from app.services.base_crawler import BaseCrawler, CrawlResult

REDDIT_SOURCE = "reddit"

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


def _build_public_session() -> httpx.Client:
    proxy = None
    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        if val := os.environ.get(key):
            proxy = val
            break
    if not proxy:
        proxy = settings.HTTP_PROXY or None

    client = httpx.Client(
        proxy=proxy,
        trust_env=False,
        timeout=30.0,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
    )
    try:
        client.get("https://old.reddit.com/", timeout=10.0)
    except Exception:
        pass
    return client


class RedditCrawler(BaseCrawler):
    source_name = "reddit"
    display_name = "Reddit"

    def crawl(self, db: Session) -> CrawlResult:
        keywords = _load_keywords()
        subreddits = self.config.get("subreddits", [])
        post_limit = self.config.get("post_limit", 25)
        comment_limit = self.config.get("comment_limit", 10)

        if not subreddits:
            return CrawlResult(source_name=self.source_name, errors=1, message="No subreddits configured")

        use_praw = bool(settings.REDDIT_CLIENT_ID)
        reddit = None
        public_session = None

        if use_praw:
            try:
                import praw
                reddit = praw.Reddit(
                    client_id=settings.REDDIT_CLIENT_ID,
                    client_secret=settings.REDDIT_CLIENT_SECRET,
                    user_agent=settings.REDDIT_USER_AGENT,
                )
            except Exception as e:
                logger.warning("PRAW init failed, falling back to public session: {}", e)
                use_praw = False

        if not use_praw:
            public_session = _build_public_session()

        result = CrawlResult(source_name=self.source_name)

        try:
            for sr_name in subreddits:
                try:
                    if reddit:
                        p, c = self._crawl_subreddit_praw(reddit, sr_name, db, keywords, post_limit, comment_limit)
                    else:
                        p, c = self._crawl_subreddit_public(sr_name, db, keywords, public_session, post_limit, comment_limit)
                    result.posts_fetched += p
                    result.comments_fetched += c
                    if p > 0:
                        logger.info("r/{}: {} new posts, {} new comments", sr_name, p, c)
                except Exception as e:
                    result.errors += 1
                    logger.error("Failed to crawl r/{}: {}", sr_name, e)
        finally:
            if public_session:
                public_session.close()

        result.posts_after_filter = result.posts_fetched
        self._log_crawl(db, result)
        self._update_source_status(db, result)
        return result

    def _crawl_subreddit_praw(self, reddit, subreddit_name: str, db: Session, keywords: dict, post_limit: int, comment_limit: int) -> tuple[int, int]:
        posts_fetched = 0
        comments_fetched = 0
        subreddit = reddit.subreddit(subreddit_name)
        now = datetime.now(timezone.utc).isoformat()

        for submission in subreddit.hot(limit=post_limit):
            external_id = f"t3_{submission.id}"
            if db.query(Post).filter(Post.external_id == external_id).first():
                continue

            title = submission.title or ""
            body = submission.selftext or ""
            if not _matches_keyword(f"{title} {body}", keywords):
                continue

            post = Post(
                external_id=external_id,
                source=REDDIT_SOURCE,
                title=title,
                body=body or None,
                url=f"https://reddit.com{submission.permalink}",
                subreddit=subreddit_name,
                author=str(submission.author) if submission.author else None,
                score=submission.score,
                num_comments=submission.num_comments,
                created_utc=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat(),
                fetched_at=now,
                analysis_stage="pending",
                processed=0,
            )
            db.add(post)
            db.flush()
            posts_fetched += 1

            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list()[:comment_limit]:
                cid = f"t1_{comment.id}"
                if db.query(Comment).filter(Comment.external_id == cid).first():
                    continue
                db.add(Comment(
                    external_id=cid,
                    post_id=post.id,
                    body=comment.body or "",
                    author=str(comment.author) if comment.author else None,
                    score=comment.score,
                    created_utc=datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).isoformat(),
                    fetched_at=now,
                ))
                comments_fetched += 1

        return posts_fetched, comments_fetched

    def _crawl_subreddit_public(self, subreddit_name: str, db: Session, keywords: dict, client: httpx.Client, post_limit: int, comment_limit: int) -> tuple[int, int]:
        posts_fetched = 0
        comments_fetched = 0
        now = datetime.now(timezone.utc).isoformat()

        resp = client.get(
            f"https://old.reddit.com/r/{subreddit_name}/hot.json",
            params={"limit": post_limit},
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])

        for child in children:
            pd = child.get("data", {})
            post_id = pd.get("id", "")
            if not post_id:
                continue
            external_id = f"t3_{post_id}"
            if db.query(Post).filter(Post.external_id == external_id).first():
                continue

            title = pd.get("title", "") or ""
            body = pd.get("selftext", "") or ""
            if not _matches_keyword(f"{title} {body}", keywords):
                continue

            created = pd.get("created_utc") or 0
            post = Post(
                external_id=external_id,
                source=REDDIT_SOURCE,
                title=title,
                body=body or None,
                url=f"https://reddit.com{pd.get('permalink', '')}",
                subreddit=subreddit_name,
                author=pd.get("author"),
                score=pd.get("score", 0) or 0,
                num_comments=pd.get("num_comments", 0) or 0,
                created_utc=datetime.fromtimestamp(created, tz=timezone.utc).isoformat(),
                fetched_at=now,
                analysis_stage="pending",
                processed=0,
            )
            db.add(post)
            db.flush()
            posts_fetched += 1

            time.sleep(1.0)
            try:
                cr = client.get(
                    f"https://old.reddit.com/r/{subreddit_name}/comments/{post_id}.json",
                    params={"limit": comment_limit, "depth": 1},
                    headers={"Accept": "application/json"},
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
                        if db.query(Comment).filter(Comment.external_id == cid).first():
                            continue
                        cmt_created = cd.get("created_utc") or 0
                        db.add(Comment(
                            external_id=cid,
                            post_id=post.id,
                            body=cmt_body,
                            author=cd.get("author"),
                            score=cd.get("score", 0) or 0,
                            created_utc=datetime.fromtimestamp(cmt_created, tz=timezone.utc).isoformat(),
                            fetched_at=now,
                        ))
                        comments_fetched += 1
            except Exception as e:
                logger.warning("Failed to fetch public comments for {}: {}", external_id, e)

        return posts_fetched, comments_fetched
