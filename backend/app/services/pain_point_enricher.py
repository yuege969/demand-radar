from __future__ import annotations

import json
import re

from loguru import logger
from openai import OpenAI

from app.config import settings

SNAPSHOT_PROMPT = """你是一个市场需求分析专家。请用简洁的语言提炼下面这个用户痛点，并给出个人开发者的产品机会。

重要：你的整个回复必须是纯 JSON 对象，不要有任何 markdown 标记或代码块。

{
  "summary": "痛点一句话概述（30字以内），提炼核心问题",
  "opportunity": "个人开发者可以做什么产品来解决这个痛点（50-80字），给出1-2个具体的产品方向"
}

要求：
- summary 要精炼，让人一眼看懂这个需求是什么
- opportunity 要具体可执行，不是泛泛而谈，要给出明确的产品形态建议"""

ENRICHMENT_PROMPT = """你是一个市场需求分析专家。请分析下面这个用户痛点，输出完整的结构化分析报告。

重要：你的整个回复必须是纯 JSON 对象，不要有任何解释、思考过程、markdown 标记或代码块。直接输出 JSON。

{{
  "demand_validation": {{
    "is_genuine_demand": true或false,
    "validation_reasoning": "判断这是否为真实需求的详细理由（150-300字），说明判断依据",
    "evidence_from_sources": "从来源内容中提取的具体证据，引用原文关键词句",
    "frequency_analysis": "该需求出现的频率判断：是偶发吐槽还是普遍存在的痛点，出现场景有哪些",
    "user_sentiment_intensity": "用户表达该需求时的情绪分析：紧迫程度、沮丧程度、期望值"
  }},
  "market_value_analysis": {{
    "market_size_estimate": "潜在市场规模估算：目标用户量级、市场空间大小",
    "target_audience": "目标用户群体详细描述：谁最需要、使用场景、决策链",
    "willingness_to_pay_evidence": "付费意愿证据：是否已有付费方案、用户是否表达过付费意向",
    "competition_landscape": "竞争格局：现有解决方案及其优缺点，市场空白在哪里",
    "monetization_potential": "变现潜力：可行的收费模式、预期客单价范围"
  }},
  "implementation_plan": {{
    "mvp_scope": "MVP最小可行产品范围：第一阶段必须包含的核心功能列表",
    "technical_approach": "技术实现思路：整体架构、关键模块、技术难点",
    "recommended_tech_stack": ["推荐技术1", "推荐技术2"],
    "tech_stack_rationale": "选择这些技术的原因",
    "go_to_market_strategy": "市场推广策略：冷启动方式、获客渠道、传播路径",
    "monetization_model": "盈利模式建议：订阅制/买断制/按量付费/广告等"
  }},
  "solo_feasibility": {{
    "specific_barriers": "个人开发者面临的具体障碍：技术复杂度、资源限制、时间投入、运营难度",
    "how_to_overcome": "克服障碍的具体方法：如何用有限资源达成目标、可以借助的工具和平台",
    "realistic_dev_time": "合理的开发周期估算（含具体周数或月数）",
    "dev_time_reasoning": "时间估算的依据：各阶段所需时间分解"
  }},
  "dimension_scores": {{
    "emotion_intensity": 0到10的整数,
    "repeat_frequency": 0到10的整数,
    "involves_money": 0到10的整数,
    "has_paid_solution": 0到10的整数,
    "automation_difficulty": 0到10的整数,
    "is_long_term": 0到10的整数,
    "individual_score": 0到10的整数,
    "market_saturation": "red"或"amber"或"green"
  }}
}}

评分指南：
- emotion_intensity: 用户情绪的强烈程度，越愤怒/焦虑越高
- repeat_frequency: 该需求在不同来源中重复出现的频率
- involves_money: 用户是否涉及金钱/付费意愿
- has_paid_solution: 市场上已有付费方案的程度
- automation_difficulty: 技术实现难度，越难分越高
- is_long_term: 是否为长期持续的需求
- individual_score: 个人开发者独立完成的可行性，越容易分越高
- market_saturation: green=蓝海市场, amber=有竞争但仍有空间, red=红海竞争激烈

如果缺少足够信息做出判断，请在分析文本中诚实指出不确定性，但不要留空字段。
如果完全无法分析，请返回：{{"demand_validation": null, "market_value_analysis": null, "implementation_plan": null, "solo_feasibility": null, "dimension_scores": null}}"""


def _build_enrichment_user_prompt(
    title: str,
    summary: str,
    category: str | None = None,
    industry: str | None = None,
    source_snippets: str | None = None,
) -> str:
    parts = [
        "请分析以下用户痛点：",
        "",
        f"标题：{title}",
        f"摘要：{summary}",
    ]
    if category:
        parts.append(f"分类：{category}")
    if industry:
        parts.append(f"行业：{industry}")
    if source_snippets:
        parts.append("")
        parts.append("相关来源内容：")
        parts.append(source_snippets)
    return "\n".join(parts)


def _strip_formatting(text: str) -> str:
    """Extract the actual answer from a DeepSeek R1-style response.

    DeepSeek R1 wraps reasoning in ``<think>...</think>`` and places the real
    answer after the closing tag.  Keep only what comes after the last ``</think>``.
    Also strips markdown code fences.
    """
    last_close = text.rfind("</think>")
    if last_close != -1:
        text = text[last_close + len("</think>"):]
    text = re.sub(r"</?thinking>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```(?:json)?\s*", "", text)
    return text.strip()


def _find_balanced_json(text: str) -> str | None:
    """Find the outermost balanced JSON object in text that may contain non-JSON prefix/suffix."""
    best = None
    i = 0
    while i < len(text):
        pos = text.find("{", i)
        if pos == -1:
            break
        depth = 0
        in_string = False
        escape = False
        for j in range(pos, len(text)):
            ch = text[j]
            if escape:
                escape = False
                continue
            if in_string:
                if ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[pos : j + 1]
                    if best is None or len(candidate) > len(best):
                        best = candidate
                    break
        i = pos + 1
    return best


def _parse_json(text: str) -> dict | None:
    candidate = _find_balanced_json(text)
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


async def enrich_pain_point(
    title: str,
    summary: str,
    category: str | None = None,
    industry: str | None = None,
    source_snippets: str | None = None,
) -> dict | None:
    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not configured, skipping enrichment")
        return None

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)
    user_content = _build_enrichment_user_prompt(
        title=title,
        summary=summary,
        category=category,
        industry=industry,
        source_snippets=source_snippets,
    )

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": ENRICHMENT_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=8192,
            temperature=0.3,
        )

        finish = response.choices[0].finish_reason
        if finish == "length":
            logger.warning("Enrichment response truncated (finish_reason=length), consider increasing max_tokens")

        text = response.choices[0].message.content or ""
        text = _strip_formatting(text)
        result = _parse_json(text)

        if result is None:
            logger.error(
                "Failed to parse enrichment JSON (finish_reason={}): {}",
                finish,
                text[:500],
            )
            return None

        return result

    except Exception as e:
        logger.error("Enrichment LLM call failed: {}", e)
        return None


async def _call_llm(system_prompt: str, user_content: str, max_tokens: int = 4096) -> dict | None:
    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not configured")
        return None

    client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )

            finish = response.choices[0].finish_reason
            if finish == "length":
                logger.warning("LLM response truncated (finish_reason=length)")

            text = response.choices[0].message.content or ""
            text = _strip_formatting(text)
            result = _parse_json(text)

            if result is not None:
                return result

            # On first failure, check if response looks truncated and retry with more tokens
            if attempt == 0 and not text.rstrip().endswith("}"):
                logger.warning(
                    "LLM JSON appears truncated (finish_reason={}), retrying with {} tokens",
                    finish, max_tokens * 2,
                )
                max_tokens *= 2
                continue

            logger.error("Failed to parse LLM JSON (finish_reason={}): {}", finish, text[:500])
            return None

        except Exception as e:
            if attempt == 0:
                logger.warning("LLM call failed, retrying: {}", e)
                continue
            logger.error("LLM call failed after retry: {}", e)
            return None

    return None


def _build_user_prompt(
    title: str,
    summary: str,
    category: str | None = None,
    industry: str | None = None,
    source_snippets: str | None = None,
) -> str:
    parts = [
        "请分析以下用户痛点：",
        "",
        f"标题：{title}",
        f"摘要：{summary}",
    ]
    if category:
        parts.append(f"分类：{category}")
    if industry:
        parts.append(f"行业：{industry}")
    if source_snippets:
        parts.append("")
        parts.append("相关来源内容：")
        parts.append(source_snippets)
    return "\n".join(parts)


async def enrich_snapshot(
    title: str,
    summary: str,
    category: str | None = None,
    industry: str | None = None,
    source_snippets: str | None = None,
) -> dict | None:
    user_content = _build_user_prompt(title, summary, category, industry, source_snippets)
    return await _call_llm(SNAPSHOT_PROMPT, user_content, max_tokens=1024)


async def enrich_module(
    module_key: str,
    title: str,
    summary: str,
    category: str | None = None,
    industry: str | None = None,
    source_snippets: str | None = None,
) -> dict | None:
    from app.services.enrichment_modules import get_module

    module = get_module(module_key)
    if module is None:
        logger.error("Unknown enrichment module: {}", module_key)
        return None

    user_content = _build_user_prompt(title, summary, category, industry, source_snippets)
    return await _call_llm(module.system_prompt, user_content, max_tokens=8192)
