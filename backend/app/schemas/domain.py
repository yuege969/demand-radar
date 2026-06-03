from __future__ import annotations

from pydantic import BaseModel


class RoleOut(BaseModel):
    key: str
    name: str
    icon: str
    description: str
    subtopics: list[str]
    demand_count: int = 0
    avg_opportunity_score: float = 0.0

    model_config = {"from_attributes": False}


class DomainCategoryOut(BaseModel):
    key: str
    name: str
    description: str
    keywords: list[str]

    model_config = {"from_attributes": False}


class PainVocabularyOut(BaseModel):
    category: str
    words: list[str]


class TaxonomyOut(BaseModel):
    roles: list[RoleOut]
    categories: list[DomainCategoryOut]
    pain_vocabulary: list[PainVocabularyOut]
