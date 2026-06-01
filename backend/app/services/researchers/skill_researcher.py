from __future__ import annotations

from loguru import logger
from openai import OpenAI

from app.config import settings
from app.schemas.research import ResearchFinding, ResearcherOutput
from app.schemas.skill import LoadedSkill
from app.services.researchers.base import BaseResearcher


class SkillResearcher(BaseResearcher):
    """Researcher backed by an external SKILL.md definition.

    Uses the skill's Markdown body as LLM methodology guidance for extraction.
    """

    platform_name: str = ""

    def __init__(self, skill: LoadedSkill):
        self._skill = skill
        self.platform_name = skill.meta.name

    async def search(self, domain: str) -> list[ResearchFinding]:
        return []

    async def extract_insights(self, findings: list[ResearchFinding]) -> ResearcherOutput:
        if not findings:
            return ResearcherOutput(
                platform=self.platform_name,
                findings_count=0,
                pain_points=[],
                feature_requests=[],
                complaints=[],
                target_users=[],
            )

        if not settings.LLM_API_KEY:
            return ResearcherOutput(
                platform=self.platform_name,
                findings_count=len(findings),
            )

        content_blocks = []
        for i, f in enumerate(findings):
            body_text = f.content_snippet[:800]
            content_blocks.append(
                f'<item id="{i}">\n'
                f"<title>{f.title}</title>\n"
                f"<body>{body_text}</body>\n"
                f"</item>"
            )

        skill_guidance = f"Use this methodology:\n\n{self._skill.body[:2000]}"

        client = OpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_API_BASE)
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract user pain points, feature requests, and complaints "
                            "from online discussion content. Return ONLY valid JSON.\n\n"
                            f"{skill_guidance}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": "<content>\n" + "\n\n".join(content_blocks) + "\n</content>",
                    },
                ],
                max_tokens=4096,
                temperature=0.3,
            )

            text = response.choices[0].message.content or ""
            text = self._strip_formatting(text)
            result = self._parse_json(text)
            if result is None:
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

            return ResearcherOutput(
                platform=self.platform_name,
                findings_count=len(findings),
                pain_points=pain_points,
                feature_requests=result.get("feature_requests", []),
                complaints=result.get("complaints", []),
                target_users=result.get("target_users", []),
            )
        except Exception as e:
            logger.error("Skill extraction failed for {}: {}", self.platform_name, e)
            return ResearcherOutput(
                platform=self.platform_name,
                findings_count=len(findings),
            )
