from __future__ import annotations

import pytest
from app.services.pain_scorer import calculate_pain_score


def test_all_zero_returns_zero():
    dims = {
        "emotion_intensity": 0, "comment_volume": 0, "repeat_frequency": 0,
        "involves_money": 0, "has_paid_solution": 0,
        "automation_difficulty": 0, "is_long_term": 0,
    }
    assert calculate_pain_score(dims) == 10 * 0.10  # (10-0)*0.10 = 1.0


def test_all_ten_returns_ten():
    dims = {
        "emotion_intensity": 10, "comment_volume": 10, "repeat_frequency": 10,
        "involves_money": 10, "has_paid_solution": 10,
        "automation_difficulty": 0, "is_long_term": 10,
    }
    expected = 10 * 0.20 + 10 * 0.15 + 10 * 0.20 + 10 * 0.20 + 10 * 0.10 + 10 * 0.10 + 10 * 0.05
    assert calculate_pain_score(dims) == round(expected, 2)


def test_difficulty_inverse():
    low_diff = calculate_pain_score({
        "emotion_intensity": 5, "comment_volume": 5, "repeat_frequency": 5,
        "involves_money": 5, "has_paid_solution": 5,
        "automation_difficulty": 2, "is_long_term": 5,
    })
    high_diff = calculate_pain_score({
        "emotion_intensity": 5, "comment_volume": 5, "repeat_frequency": 5,
        "involves_money": 5, "has_paid_solution": 5,
        "automation_difficulty": 8, "is_long_term": 5,
    })
    assert low_diff > high_diff


def test_missing_keys_default_to_zero():
    assert calculate_pain_score({}) == (10 - 0) * 0.10  # only difficulty inverse applies
