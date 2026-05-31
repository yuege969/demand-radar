"""Fast LLM triage that classifies posts as pain-point or not.

Uses a minimal prompt so each call returns in 2-5 seconds instead of 30-90s.
"""

from __future__ import annotations

import json
import re

from loguru import logger
from openai import OpenAI

from app.config import settings

TRIAGE_SYSTEM = (
    "Classify whether each post describes a real user frustration, pain point, "
    "or unmet need that software could address. Be strict: only flag posts where "
    "the author is clearly frustrated or asking for a better solution. "
    "Return ONLY a JSON array, no other text."
)

TRIAGE_USER_TEMPLATE = """For each post below, determine if it's a real pain point.

{posts}

Return a JSON array with one entry per post. Each entry MUST include the "index" field matching the post id:
[{{"index": 0, "is_pain_point": true, "title": "brief summary", "confidence": 8}}, ...]"""


def _build_triage_prompt(posts: list[dict]) -> str:
    parts = []
    for p in posts:
        idx = p.get("index", 0)
        body = (p.get("body") or "")[:300]
        parts.append(
            f'<post id="{idx}">\n'
            f"  <title>{p.get('title', '')}</title>\n"
            f"  <body>{body}</body>\n"
            f"</post>"
        )
    return TRIAGE_USER_TEMPLATE.format(posts="\n".join(parts))


def _call_llm(posts_batch: list[dict]) -> list[dict]:
    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not configured, skipping triage")
        return [
            {"index": p["index"], "is_pain_point": False, "title": "", "confidence": 0}
            for p in posts_batch
        ]

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)
    user_content = _build_triage_prompt(posts_batch)

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": TRIAGE_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            max_tokens=2048,
            temperature=0.2,
        )
        text = response.choices[0].message.content
    except Exception as e:
        logger.error("LLM triage call failed: {}", e)
        return [
            {"index": p["index"], "is_pain_point": False, "title": "", "confidence": 0}
            for p in posts_batch
        ]

    text = re.sub(r"```(?:json)?\s*", "", text.strip()).strip()
    parsed = None
    try:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1:
            parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        logger.error("Failed to parse triage response: {}", text[:300])

    if isinstance(parsed, list) and len(parsed) > 0:
        # Validate and fix up: ensure every item has "index"
        fixed = []
        for i, item in enumerate(parsed):
            if isinstance(item, dict):
                if "index" not in item:
                    item["index"] = i
                if "is_pain_point" not in item:
                    item["is_pain_point"] = False
                if "title" not in item:
                    item["title"] = ""
                if "confidence" not in item:
                    item["confidence"] = 0
                fixed.append(item)
        if fixed:
            return fixed

    return [
        {"index": p["index"], "is_pain_point": False, "title": "", "confidence": 0}
        for p in posts_batch
    ]


def triage_posts(posts: list[dict], batch_size: int = 15) -> list[dict]:
    """Classify posts as pain-point or not. Returns triage results with index."""
    if not posts:
        return []

    results: list[dict] = []
    for i in range(0, len(posts), batch_size):
        batch = posts[i : i + batch_size]
        logger.info(
            "Triage batch {}/{} ({} posts)",
            i // batch_size + 1,
            (len(posts) - 1) // batch_size + 1,
            len(batch),
        )
        results.extend(_call_llm(batch))

    return results
