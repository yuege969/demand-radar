from __future__ import annotations

import json
from typing import Optional

from anthropic import Anthropic
from loguru import logger

from app.config import settings

SYSTEM_PROMPT = """You are a demand analysis AI. Your task is to identify user pain points, needs, and business opportunities from social media posts.

Analyze the provided content and extract:
1. Pain points: What frustrations or problems do users express?
2. Automation potential: Can this be solved with software/tools?
3. Monetary signals: Are users willing to pay for solutions?
4. Business angle: How could this be turned into a SaaS or plugin product?

Output ONLY valid JSON (no markdown, no backticks) in this exact structure:
{
  "pain_points": [
    {
      "title": "short descriptive title",
      "summary": "concise 1-2 sentence summary of the need",
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
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}

If no pain points are found, return {"pain_points": []}."""


def _build_batch_prompt(posts: list[dict]) -> str:
    parts = []
    for i, post in enumerate(posts):
        parts.append(
            f"<post id=\"{i}\">\n"
            f"<title>{post['title']}</title>\n"
            f"<body>{post.get('body', '') or ''}</body>\n"
            f"<subreddit>r/{post.get('subreddit', '')}</subreddit>\n"
            f"<score>{post.get('score', 0)}</score>\n"
            f"<num_comments>{post.get('num_comments', 0)}</num_comments>\n"
            f"</post>"
        )
    return "\n\n".join(parts)


def _analyze_with_claude(posts_batch: list[dict]) -> list[dict]:
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not configured, skipping AI analysis")
        return []

    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    user_content = _build_batch_prompt(posts_batch)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"<posts>\n{user_content}\n</posts>\n\nExtract pain points from these posts."},
    ]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        temperature=0.3,
        messages=messages,
    )

    text = response.content[0].text if isinstance(response.content, list) else response.content
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("\n```", 1)[0]

    try:
        result = json.loads(text)
        return result.get("pain_points", [])
    except json.JSONDecodeError:
        logger.error("Failed to parse Claude response as JSON: {}", text[:500])
        return []


def analyze_posts(posts: list[dict]) -> list[dict]:
    if not posts:
        return []
    pain_points = []
    batch_size = settings.MAX_POSTS_PER_BATCH
    for i in range(0, len(posts), batch_size):
        batch = posts[i : i + batch_size]
        logger.info("Analyzing batch {}/{} ({} posts)", i // batch_size + 1, (len(posts) - 1) // batch_size + 1, len(batch))
        try:
            result = _analyze_with_claude(batch)
            for r in result:
                r["source_indices"] = list(range(i, i + len(batch)))
            pain_points.extend(result)
        except Exception as e:
            logger.error("AI analysis failed for batch {}: {}", i // batch_size, e)
    return pain_points
