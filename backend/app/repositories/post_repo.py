from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.post import Post


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[Post]:
        return self.db.query(Post).filter(Post.id == id).first()

    def get_by_reddit_id(self, reddit_id: str) -> Optional[Post]:
        return self.db.query(Post).filter(Post.reddit_id == reddit_id).first()

    def create_or_skip(self, post: Post) -> Optional[Post]:
        existing = self.get_by_reddit_id(post.reddit_id)
        if existing:
            return None
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def list_pending(self, limit: int = 50) -> list[Post]:
        return (
            self.db.query(Post).filter(Post.processed == 0).limit(limit).all()
        )

    def mark_analyzed(self, post_id: int) -> None:
        post = self.get_by_id(post_id)
        if post:
            post.processed = 1
            self.db.commit()

    def mark_failed(self, post_id: int, error: str) -> None:
        post = self.get_by_id(post_id)
        if post:
            post.processed = 2
            post.error_message = error
            self.db.commit()

    def count_all(self) -> int:
        return self.db.query(Post).count()
