from sqlalchemy import Column, Integer, Text, Float, ForeignKey

from app.models import Base


class PainScore(Base):
    __tablename__ = "pain_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pain_point_id = Column(Integer, ForeignKey("pain_points.id"), nullable=False, unique=True)
    emotion_intensity = Column(Float, default=0.0)
    comment_volume = Column(Float, default=0.0)
    repeat_frequency = Column(Float, default=0.0)
    involves_money = Column(Float, default=0.0)
    has_paid_solution = Column(Float, default=0.0)
    automation_difficulty = Column(Float, default=0.0)
    is_long_term = Column(Float, default=0.0)
    total_score = Column(Float, default=0.0)
    calculated_at = Column(Text, nullable=False)
