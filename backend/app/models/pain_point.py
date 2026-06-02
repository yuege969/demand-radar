from sqlalchemy import Column, Integer, Text, Float, ForeignKey

from app.models import Base


class PainPoint(Base):
    __tablename__ = "pain_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    research_job_id = Column(Integer, ForeignKey("research_jobs.id"), nullable=True)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    category = Column(Text, nullable=True)
    industry = Column(Text, nullable=True)
    pain_score = Column(Float, default=0.0)
    keywords = Column(Text, nullable=True)
    source_urls = Column("source_post_ids", Text, nullable=True)
    is_saas_idea = Column(Integer, default=0)
    is_plugin_idea = Column(Integer, default=0)
    business_angle = Column(Text, nullable=True)
    created_at = Column(Text, nullable=False)
    updated_at = Column(Text, nullable=False)

    # Individual developer feasibility fields (Phase 1)
    is_individual_feasible = Column(Integer, default=0)
    feasibility_reason = Column(Text, nullable=True)
    estimated_dev_time = Column(Text, nullable=True)
    tech_stack_hints = Column(Text, nullable=True)
    market_saturation = Column(Text, nullable=True)
    individual_score = Column(Float, default=0.0)
    opportunity_score = Column(Float, default=0.0)

    # Snapshot enrichment (lightweight, auto-generated after research)
    snapshot_summary = Column(Text, nullable=True)
    snapshot_opportunity = Column(Text, nullable=True)
    snapshot_at = Column(Text, nullable=True)

    # On-demand modular deep analysis results (JSON)
    enrichment_data = Column(Text, nullable=True)

    # Legacy deep analysis fields — kept for backward compatibility
    demand_validation = Column(Text, nullable=True)
    market_value_analysis = Column(Text, nullable=True)
    implementation_plan = Column(Text, nullable=True)
    solo_feasibility = Column(Text, nullable=True)
    enriched_at = Column(Text, nullable=True)

