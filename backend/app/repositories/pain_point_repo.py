from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models.pain_point import PainPoint


class PainPointRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[PainPoint]:
        return self.db.query(PainPoint).filter(PainPoint.id == id).first()

    def create(self, pp: PainPoint) -> PainPoint:
        self.db.add(pp)
        self.db.commit()
        self.db.refresh(pp)
        return pp

    def find_similar(self, title: str, summary: str) -> list[PainPoint]:
        return self.db.query(PainPoint).all()

    def get_all_ids(self) -> list[int]:
        return [r[0] for r in self.db.query(PainPoint.id).all()]

    def merge_sources(self, pp_id: int, new_sources: list) -> None:
        pp = self.get_by_id(pp_id)
        if not pp:
            return
        existing = json.loads(pp.source_urls or "[]")
        merged = existing + [s for s in new_sources if s not in existing]
        pp.source_urls = json.dumps(merged)
        pp.updated_at = __import__("datetime").datetime.utcnow().isoformat() + "Z"
        self.db.commit()

    def count_all(self) -> int:
        return self.db.query(PainPoint).count()
