from __future__ import annotations

import json
import re

from loguru import logger
from openai import OpenAI

from app.config import settings

SYSTEM_PROMPT = """You are a demand analysis AI. Your task is to identify user pain points, needs, and business opportunities from social media posts.

Analyze the provided content and extract:
1. Pain points: What frustrations or problems do users express?
2. Automation potential: Can this be solved with software/tools?
3. Monetary signals: Are users willing to pay for solutions?
4. Business angle: How could this be turned into a SaaS or plugin product?
5. Individual developer feasibility: Can a solo developer build and maintain this?

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
      "keywords": ["keyword1", "keyword2"],
      "source_post_indices": [0, 2],
      "is_individual_feasible": true/false,
      "individual_score": 0-10,
      "feasibility_reason": "why this is or isn't feasible for a solo developer",
      "estimated_dev_time": "1-2 weeks|1 month|2-3 months|longer",
      "tech_stack_hints": ["tech1", "tech2"],
      "market_saturation": "red|amber|green"
    }
  ]
}

## Individual Developer Feasibility Scoring

Score each pain point on 0-10 scale for individual developer feasibility:

**Technical Feasibility (30% weight):**
- 10: Single tech stack, 1-2 weeks MVP
- 7: 2 tech stacks, 1 month MVP
- 4: Multiple tech stacks, 2-3 months
- 1: Requires professional team

**Ops Feasibility (25% weight):**
- 10: Serverless, near-zero maintenance
- 7: Simple cron, <1hr/day maintenance
- 4: Regular maintenance, <4hr/day
- 1: Requires dedicated ops/support

**Acquisition Feasibility (25% weight):**
- 10: Direct via niche community
- 7: SEO/content marketing in 3-6 months
- 4: Paid acquisition with positive LTV
- 1: Requires enterprise sales

**Market Size (20% weight):**
- 10: >100K target users, ARPU>$20
- 7: 10K-100K users, ARPU $10-20
- 4: 1K-10K users, ARPU $5-10
- 1: <1K users or very low willingness to pay

**is_individual_feasible** = true if individual_score >= 5, false otherwise

## Market Saturation Guide
- "green": Few/no solutions exist, blue ocean
- "amber": Some solutions exist but underserved or differentiable
- "red": Crowded market with established players

For each pain point, set "source_post_indices" to the <post id="X"> values of the posts it was derived from. If it came from multiple posts, list all that apply. If it came from all posts, list all indices.

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


def _strip_thinking(text: str) -> str:
    """Remove `` blocks and markdown fences from model output."""
    text = text.strip()
    text = re.sub(r"</?think>", "", text)
    text = re.sub(r"</?thinking>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```(?:json)?\s*", "", text)
    return text.strip()


def _extract_json(text: str) -> dict | None:
    """Extract the outermost JSON object from text that may contain extra content."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _analyze_with_llm(posts_batch: list[dict]) -> list[dict]:
    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not configured, skipping AI analysis")
        return []

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)
    user_content = _build_batch_prompt(posts_batch)

    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"<posts>\n{user_content}\n</posts>\n\nExtract pain points from these posts."},
        ],
        max_tokens=16384,
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
    if not posts:
        return []
    pain_points = []
    batch_size = settings.MAX_POSTS_PER_BATCH
    for i in range(0, len(posts), batch_size):
        batch = posts[i : i + batch_size]
        logger.info("Analyzing batch {}/{} ({} posts)", i // batch_size + 1, (len(posts) - 1) // batch_size + 1, len(batch))
        try:
            result = _analyze_with_llm(batch)
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
            logger.error("AI analysis failed for batch {}: {}", i // batch_size, e)
    return pain_points
