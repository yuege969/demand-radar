from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.post import Post
from app.models.comment import Comment
from app.schemas import ApiResponse, PaginationMeta
from app.schemas.post import PostOut, PostDetail, CommentOut

router = APIRouter()


@router.get("")
def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    subreddit: str | None = None,
    sort: str = Query("created_utc", pattern="^(created_utc|score|num_comments)$"),
    db: Session = Depends(get_db),
):
    query = db.query(Post)
    if subreddit:
        query = query.filter(Post.subreddit == subreddit)
    total = query.count()
    order_col = getattr(Post, sort)
    posts = query.order_by(order_col.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return ApiResponse(
        data=[PostOut.model_validate(p) for p in posts],
        meta=PaginationMeta(page=page, per_page=per_page, total=total).model_dump(),
    )


@router.get("/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    detail = PostDetail(
        **PostOut.model_validate(post).model_dump(),
        comments=[CommentOut.model_validate(c) for c in comments],
    )
    return ApiResponse(data=detail)
