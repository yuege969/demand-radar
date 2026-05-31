from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PostOut(BaseModel):
    id: int
    external_id: str
    source: str
    title: str
    body: Optional[str] = None
    url: Optional[str] = None
    subreddit: str
    author: Optional[str] = None
    score: int
    num_comments: int
    signal_score: Optional[float] = None
    analysis_stage: str
    created_utc: str
    fetched_at: str
    processed: int

    model_config = {"from_attributes": True}


class PostDetail(PostOut):
    comments: list["CommentOut"] = []


class CommentOut(BaseModel):
    id: int
    external_id: str
    post_id: int
    body: str
    author: Optional[str] = None
    score: int
    created_utc: str

    model_config = {"from_attributes": True}
