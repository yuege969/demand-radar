from sqlalchemy import Column, Integer, Text, Float

from app.models import Base


class PainPoint(Base):
    __tablename__ = "pain_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(Text, nullable=True)
    industry = Column(Text, nullable=True)
    pain_score = Column(Float, default=0.0)
    keywords = Column(Text, nullable=True)
    source_post_ids = Column(Text, nullable=True)
    source_comment_ids = Column(Text, nullable=True)
    is_saas_idea = Column(Integer, default=0)
    is_plugin_idea = Column(Integer, default=0)
    business_angle = Column(Text, nullable=True)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)
