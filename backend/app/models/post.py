from sqlalchemy import Column, Integer, Text, Float

from app.models import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(Text, nullable=False, unique=True)
    source = Column(Text, nullable=False, default="")
    title = Column(Text, nullable=False)
    body = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    subreddit = Column(Text, nullable=False)
    author = Column(Text, nullable=True)
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    created_utc = Column(Text, nullable=False)
    fetched_at = Column(Text, nullable=False)
    signal_score = Column(Float, nullable=True)
    analysis_stage = Column(Text, nullable=False, default="pending")
    triage_result = Column(Text, nullable=True)
    processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
