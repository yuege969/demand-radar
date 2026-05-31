from __future__ import annotations

from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.post import Post  # noqa: E402, F401
from app.models.comment import Comment  # noqa: E402, F401
from app.models.pain_point import PainPoint  # noqa: E402, F401
from app.models.pain_score import PainScore  # noqa: E402, F401
from app.models.daily_report import DailyReport  # noqa: E402, F401
from app.models.data_source import DataSource  # noqa: E402, F401
from app.models.crawl_log import CrawlLog  # noqa: E402, F401
