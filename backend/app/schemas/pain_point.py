from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PainPointOut(BaseModel):
    id: int
    title: str
    summary: str
    category: Optional[str] = None
    industry: Optional[str] = None
    pain_score: float
    keywords: Optional[str] = None
    source_post_ids: Optional[str] = None
    is_saas_idea: bool = False
    is_plugin_idea: bool = False
    business_angle: Optional[str] = None
    source_count: int = 0
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class PainScoreBreakdown(BaseModel):
    emotion_intensity: float
    comment_volume: float
    repeat_frequency: float
    involves_money: float
    has_paid_solution: float
    automation_difficulty: float
    is_long_term: float
    total_score: float

    model_config = {"from_attributes": True}


class PainPointDetail(PainPointOut):
    score_breakdown: Optional[PainScoreBreakdown] = None
    source_posts: list["PostOut"] = []
    related: list["PainPointOut"] = []
