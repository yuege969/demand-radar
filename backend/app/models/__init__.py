from __future__ import annotations

from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.post import Post  # noqa: E402, F401
from app.models.comment import Comment  # noqa: E402, F401
from app.models.pain_point import PainPoint  # noqa: E402, F401
from app.models.pain_score import PainScore  # noqa: E402, F401

from app.models.research_job import ResearchJob  # noqa: E402, F401
from app.models.research_finding import ResearchFinding  # noqa: E402, F401
