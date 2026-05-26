from sqlalchemy import Column, Integer, Text

from app.models import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reddit_id = Column(Text, nullable=False, unique=True)
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    subreddit = Column(Text, nullable=False)
    author = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    created_utc = Column(Text, nullable=False)
    fetched_at = Column(Text, nullable=False)
    processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
