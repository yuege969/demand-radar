from __future__ import annotations

import numpy as np
from loguru import logger

from app.config import settings


_embedding_model = None


def _get_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Loaded embedding model: {}", settings.EMBEDDING_MODEL)
    return _embedding_model


def compute_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    a = np.array(embedding_a)
    b = np.array(embedding_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def is_duplicate(similarity: float) -> bool:
    return similarity > settings.DEDUP_THRESHOLD


def encode_texts(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return [e.tolist() for e in embeddings]


def find_most_similar(
    new_embedding: list[float],
    existing_embeddings: list[tuple[int, list[float]]],
) -> tuple[int | None, float]:
    best_id = None
    best_score = -1.0
    for pp_id, emb in existing_embeddings:
        sim = compute_similarity(new_embedding, emb)
        if sim > best_score:
            best_score = sim
            best_id = pp_id
    return best_id, best_score
