from __future__ import annotations


def calculate_pain_score(dimensions: dict) -> float:
    """Calculate weighted pain score from 7 dimensions.

    Formula:
      emotion_intensity  * 0.20
    + comment_volume     * 0.15
    + repeat_frequency   * 0.20
    + involves_money     * 0.20
    + has_paid_solution  * 0.10
    + (10 - automation_difficulty) * 0.10   # lower difficulty = higher score
    + is_long_term       * 0.05

    Returns a float in [0, 10].
    """
    total = (
        dimensions.get("emotion_intensity", 0) * 0.20
        + dimensions.get("comment_volume", 0) * 0.15
        + dimensions.get("repeat_frequency", 0) * 0.20
        + dimensions.get("involves_money", 0) * 0.20
        + dimensions.get("has_paid_solution", 0) * 0.10
        + (10 - dimensions.get("automation_difficulty", 0)) * 0.10
        + dimensions.get("is_long_term", 0) * 0.05
    )
    return round(total, 2)


def calculate_opportunity_score(pain_score: float, individual_score: float) -> float:
    """Combine pain_score (0-10) + individual_score (0-1) into a 0-100 opportunity score."""
    scaled_individual = individual_score * 10
    raw = pain_score * 0.40 + scaled_individual * 0.60
    return round(raw * 10, 1)
