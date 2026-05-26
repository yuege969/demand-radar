from sqlalchemy import Column, Integer, Text, ForeignKey

from app.models import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reddit_comment_id = Column(Text, nullable=False, unique=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    body = Column(Text, nullable=False)
    author = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    created_utc = Column(Text, nullable=False)
    fetched_at = Column(Text, nullable=False)
