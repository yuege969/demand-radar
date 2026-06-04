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
    source_urls: Optional[str] = None
    is_saas_idea: bool = False
    is_plugin_idea: bool = False
    business_angle: Optional[str] = None
    source_count: int = 0
    created_at: str
    updated_at: str
    # Individual developer feasibility fields
    is_individual_feasible: bool = False
    feasibility_reason: Optional[str] = None
    estimated_dev_time: Optional[str] = None
    tech_stack_hints: Optional[list[str]] = None
    market_saturation: Optional[str] = None
    individual_score: float = 0.0
    opportunity_score: float = 0.0
    # Snapshot enrichment (lightweight, auto-generated)
    snapshot_summary: Optional[str] = None
    snapshot_opportunity: Optional[str] = None
    snapshot_at: Optional[str] = None
    # On-demand modular deep analysis (JSON)
    enrichment_data: Optional[str] = None
    # Legacy deep analysis fields (kept for backward compatibility)
    demand_validation: Optional[str] = None
    market_value_analysis: Optional[str] = None
    implementation_plan: Optional[str] = None
    solo_feasibility: Optional[str] = None
    enriched_at: Optional[str] = None

    model_config = {"from_attributes": True}


class PainScoreBreakdown(BaseModel):
    emotion_intensity: float
    repeat_frequency: float
    involves_money: float
    has_paid_solution: float
    automation_difficulty: float
    is_long_term: float
    total_score: float

    model_config = {"from_attributes": True}


class PainPointDetail(PainPointOut):
    score_breakdown: Optional[PainScoreBreakdown] = None
    source_findings: list = []
    related: list["PainPointOut"] = []
    is_enriching: bool = False
