from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from time import time

from loguru import logger
from openai import OpenAI

from app.config import settings
from app.http_client import build_http_client
from app.schemas.research import ResearchFinding, ResearcherOutput

EXTRACTION_PROMPT = """你是一个 JSON API。你的整个响应必须是一个单一的 JSON 对象。不要在 JSON 前后写任何文字，不要使用 markdown 代码块。

从提供的内容中提取用户痛点、功能需求和抱怨。所有输出的文字内容（title, summary, description, target_user）必须使用中文。

输出以下结构：
{
  "pain_points": [
    {
      "title": "简短的中文描述性标题",
      "summary": "1-2 句中文描述",
      "category": "automation|saas|tooling|mobile|content|other",
      "target_user": "谁会经历这个痛点（中文描述）",
      "frequency": "high|medium|low",
      "willingness_to_pay": "high|medium|low|none",
      "source_indices": [0, 1]
    }
  ],
  "feature_requests": [
    {"description": "功能需求描述（中文）", "target_user": "目标用户（中文）", "source_indices": [0]}
  ],
  "complaints": [
    {"description": "抱怨内容描述（中文）", "target_user": "目标用户（中文）", "source_indices": [0]}
  ],
  "target_users": ["自由职业者", "小企业主"]
}

如果没有找到有意义的内容，返回 {"pain_points": [], "feature_requests": [], "complaints": [], "target_users": []}"""


class BaseResearcher(ABC):
    platform_name: str = ""

    @abstractmethod
    async def search(self, domain: str) -> list[ResearchFinding]:
        """Search the platform for content related to the domain."""

    async def extract_insights(self, findings: list[ResearchFinding]) -> ResearcherOutput:
        """Use LLM to extract structured pain points from findings."""
        if not findings:
            logger.info("[{}] 提取: 无数据，跳过", self.platform_name)
            return ResearcherOutput(
                platform=self.platform_name,
                findings_count=0,
                pain_points=[],
                feature_requests=[],
                complaints=[],
                target_users=[],
            )

        logger.info("[{}] 提取: {} 条发现 → LLM ({}) ...", self.platform_name, len(findings), settings.LLM_MODEL)
        t0 = time()

        content_blocks = []
        for i, f in enumerate(findings):
            body = f.content_snippet[:800]
            content_blocks.append(
                f'<item id="{i}">\n'
                f"<title>{f.title}</title>\n"
                f"<body>{body}</body>\n"
                f"</item>"
            )

        batch_prompt = "\n\n".join(content_blocks)

        if not settings.LLM_API_KEY:
            logger.warning("LLM_API_KEY not configured, returning empty insights")
            return ResearcherOutput(
                platform=self.platform_name,
                findings_count=len(findings),
                pain_points=[],
                feature_requests=[],
                complaints=[],
                target_users=[],
            )

        client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": f"<content>\n{batch_prompt}\n</content>\n\nExtract pain points and insights."},
                ],
                max_tokens=4096,
                temperature=0.3,
            )

            text = response.choices[0].message.content or ""
            usage = response.usage
            if usage:
                logger.debug("[{}] LLM tokens: in={} out={} total={}",
                           self.platform_name, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens)

            text = self._strip_formatting(text)
            result = self._parse_json(text)
            if result is None:
                logger.error("[{}] 提取: JSON 解析失败: {}", self.platform_name, text[:500])
                return ResearcherOutput(
                    platform=self.platform_name,
                    findings_count=len(findings),
                )

            pain_points = result.get("pain_points", [])
            for pp in pain_points:
                raw = pp.pop("source_indices", [])
                if isinstance(raw, list):
                    pp["source_indices"] = [
                        idx for idx in raw if isinstance(idx, int) and 0 <= idx < len(findings)
                    ]

            elapsed = (time() - t0) * 1000
            logger.info("[{}] 提取完成 | {:.0f}ms | pain={} req={} comp={} users={}",
                       self.platform_name, elapsed,
                       len(pain_points),
                       len(result.get("feature_requests", [])),
                       len(result.get("complaints", [])),
                       len(result.get("target_users", [])))

            return ResearcherOutput(
                platform=self.platform_name,
                findings_count=len(findings),
                pain_points=pain_points,
                feature_requests=result.get("feature_requests", []),
                complaints=result.get("complaints", []),
                target_users=result.get("target_users", []),
            )
        except Exception as e:
            logger.error("[{}] 提取 LLM 失败: {}", self.platform_name, e)
            return ResearcherOutput(
                platform=self.platform_name,
                findings_count=len(findings),
            )

    async def research(self, domain: str) -> ResearcherOutput:
        findings = await self.search(domain)
        return await self.extract_insights(findings)

    @staticmethod
    def _build_http_client():
        return build_http_client(timeout=30.0, follow_redirects=True)

    @staticmethod
    def _strip_formatting(text: str) -> str:
        text = text.strip()
        text = re.sub(r"</?think>", "", text)
        text = re.sub(r"</?thinking>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```(?:json)?\s*", "", text)
        return text.strip()

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or start >= end:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
