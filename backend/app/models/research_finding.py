from __future__ import annotations

from sqlalchemy import Column, Integer, Text, Float, ForeignKey

from app.models import Base


class ResearchFinding(Base):
    __tablename__ = "research_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    research_job_id = Column(Integer, ForeignKey("research_jobs.id"), nullable=False)
    platform = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    content_snippet = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    author = Column(Text, nullable=True)
    published_at = Column(Text, nullable=True)
    engagement_score = Column(Float, default=0.0)
    extracted_pain_points = Column(Text, nullable=True)
