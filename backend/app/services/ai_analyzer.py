from __future__ import annotations

import json
import re

from loguru import logger
from openai import OpenAI

from app.config import settings

SYSTEM_PROMPT = """Extract pain points and business opportunities from these social media posts.

Return ONLY valid JSON (no markdown, no backticks):
{
  "pain_points": [
    {
      "title": "short descriptive title",
      "summary": "1-2 sentence summary of the need",
      "category": "automation|saas|tooling|mobile|content",
      "industry": "dev-tools|productivity|e-commerce|health|edu",
      "emotion_intensity": 0-10,
      "repeat_frequency": 0-10,
      "involves_money": 0-10,
      "has_paid_solution": 0-10,
      "automation_difficulty": 0-10,
      "is_long_term": 0-10,
      "is_saas_idea": true/false,
      "is_plugin_idea": true/false,
      "business_angle": "brief monetization angle",
      "keywords": ["keyword1", "keyword2"],
      "source_post_indices": [0, 2],
      "is_individual_feasible": true/false,
      "individual_score": 0-10,
      "feasibility_reason": "why feasible or not for a solo developer",
      "estimated_dev_time": "1-2 weeks|1 month|2-3 months|longer",
      "tech_stack_hints": ["tech1", "tech2"],
      "market_saturation": "red|amber|green"
    }
  ]
}

Scoring guides:
- emotion_intensity: how frustrated/upset the user sounds
- repeat_frequency: how commonly this problem appears across posts
- involves_money: willingness to pay or current spending on the problem
- has_paid_solution: existing paid tools addressing this (higher = more validated market)
- automation_difficulty: technical complexity (lower = easier to build)
- is_long_term: ongoing need vs one-time fix
- individual_score: 0-10 for solo-developer viability (tech complexity, maintenance burden, go-to-market ease)
- market_saturation: "green"=blue ocean, "amber"=underserved, "red"=crowded
- is_individual_feasible: true if individual_score >= 5

Set source_post_indices to the <post id="X"> values the pain point was derived from.
If no pain points found, return {"pain_points": []}."""


def _build_batch_prompt(posts: list[dict]) -> str:
    parts = []
    for i, post in enumerate(posts):
        body = (post.get("body") or "")[:500]
        parts.append(
            f'<post id="{i}">\n'
            f"<title>{post['title']}</title>\n"
            f"<body>{body}</body>\n"
            f"<subreddit>r/{post.get('subreddit', '')}</subreddit>\n"
            f"<score>{post.get('score', 0)}</score>\n"
            f"<num_comments>{post.get('num_comments', 0)}</num_comments>\n"
            f"</post>"
        )
    return "\n\n".join(parts)


def _strip_thinking(text: str) -> str:
    text = text.strip()
    text = re.sub(r"</?think>", "", text)
    text = re.sub(r"</?thinking>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```(?:json)?\s*", "", text)
    return text.strip()


def _extract_json(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _analyze_batch_with_llm(posts_batch: list[dict]) -> list[dict]:
    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not configured, skipping analysis")
        return []

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)
    user_content = _build_batch_prompt(posts_batch)

    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"<posts>\n{user_content}\n</posts>\n\nExtract pain points."},
        ],
        max_tokens=8192,
        temperature=0.3,
    )

    text = response.choices[0].message.content
    text = _strip_thinking(text)
    result = _extract_json(text)
    if result is None:
        logger.error("Failed to parse LLM response as JSON: {}", text[:500])
        return []
    return result.get("pain_points", [])


def analyze_posts(posts: list[dict]) -> list[dict]:
    """Extract pain points from posts via LLM. Posts are already filtered to likely pain points."""
    if not posts:
        return []

    pain_points = []
    batch_size = min(settings.MAX_POSTS_PER_BATCH, 20)

    for i in range(0, len(posts), batch_size):
        batch = posts[i : i + batch_size]
        logger.info(
            "Deep analysis batch {}/{} ({} posts)",
            i // batch_size + 1,
            (len(posts) - 1) // batch_size + 1,
            len(batch),
        )
        try:
            result = _analyze_batch_with_llm(batch)
            for r in result:
                raw_indices = r.pop("source_post_indices", None)
                if not isinstance(raw_indices, list):
                    raw_indices = []
                valid_local = [
                    idx for idx in raw_indices
                    if isinstance(idx, int) and 0 <= idx < len(batch)
                ]
                if not valid_local:
                    valid_local = list(range(len(batch)))
                r["source_indices"] = [idx + i for idx in valid_local]
            pain_points.extend(result)
        except Exception as e:
            logger.error("Deep analysis failed for batch {}: {}", i // batch_size, e)

    return pain_points
