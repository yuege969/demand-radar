from sqlalchemy import Column, Integer, Text

from app.models import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Text, nullable=False, unique=True)
    summary = Column(Text, nullable=False)
    top_pain_ids = Column(Text, nullable=True)
    new_pain_ids = Column(Text, nullable=True)
    stats = Column(Text, nullable=True)
    created_at = Column(Text, nullable=False)
