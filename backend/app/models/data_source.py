from sqlalchemy import Column, Integer, Text, Float

from app.models import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    display_name = Column(Text, nullable=False)
    source_type = Column(Text, nullable=False)
    config = Column(Text, nullable=False, default="{}")
    enabled = Column(Integer, default=1)
    crawl_interval_minutes = Column(Integer, default=60)
    last_crawl_at = Column(Text, nullable=True)
    last_crawl_status = Column(Text, nullable=True)
    last_crawl_posts_fetched = Column(Integer, default=0)
    last_crawl_error = Column(Text, nullable=True)
    signal_yield_rate = Column(Float, default=0.0)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
