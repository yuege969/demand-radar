from __future__ import annotations

from sqlalchemy import Column, Integer, Text, Float

from app.models import Base


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(Text, nullable=False)
    platforms = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    total_findings = Column(Integer, default=0)
    pain_points_extracted = Column(Integer, default=0)
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(Text, nullable=False)
    completed_at = Column(Text, nullable=True)
