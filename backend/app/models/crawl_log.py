from sqlalchemy import Column, Integer, Text

from app.models import Base


class CrawlLog(Base):
    __tablename__ = "crawl_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(Text, nullable=False, index=True)
    started_at = Column(Text, nullable=False)
    completed_at = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default="running")
    posts_fetched = Column(Integer, default=0)
    comments_fetched = Column(Integer, default=0)
    posts_after_filter = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
