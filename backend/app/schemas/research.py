from __future__ import annotations

from pydantic import BaseModel


class ResearchFinding(BaseModel):
    title: str
    content_snippet: str
    url: str
    platform: str = "web"
    author: str | None = None
    published_at: str | None = None
    engagement: dict | None = None


class ExtractedPainPoint(BaseModel):
    title: str
    summary: str
    category: str
    target_user: str
    frequency: str
    willingness_to_pay: str
    source_indices: list[int] = []


class ResearcherOutput(BaseModel):
    platform: str
    findings_count: int
    pain_points: list[dict] = []
    feature_requests: list[dict] = []
    complaints: list[dict] = []
    target_users: list[str] = []
