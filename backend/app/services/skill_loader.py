from __future__ import annotations

from pathlib import Path

import yaml
from loguru import logger

from app.schemas.skill import LoadedSkill, SkillMeta


class SkillLoader:
    """Loads and parses SKILL.md files from configured search paths.

    Supports Claude Code's skill format: YAML frontmatter + Markdown body.
    When an allowlist is provided, only skills whose names appear in it are loaded.
    """

    def __init__(
        self,
        search_paths: list[str] | None = None,
        allowlist: list[str] | None = None,
    ):
        self._search_paths = [Path(p).expanduser() for p in (search_paths or [])]
        self._allowlist: set[str] | None = set(allowlist) if allowlist else None
        self._cache: dict[str, LoadedSkill] = {}

    def add_search_path(self, path: str) -> None:
        p = Path(path).expanduser()
        if p not in self._search_paths:
            self._search_paths.append(p)

    def _is_allowed(self, name: str) -> bool:
        return self._allowlist is None or name in self._allowlist

    def list_skills(self) -> list[SkillMeta]:
        metas: list[SkillMeta] = []
        seen: set[str] = set()

        for base_path in self._search_paths:
            if not base_path.exists():
                continue
            for skill_file in base_path.rglob("SKILL.md"):
                try:
                    skill = self._parse_skill_file(skill_file)
                    name = skill.meta.name
                    if name in seen or not self._is_allowed(name):
                        continue
                    metas.append(skill.meta)
                    seen.add(name)
                    self._cache[name] = skill
                except Exception:
                    logger.warning("Failed to parse skill file: {}", skill_file)

        return metas

    def load_skill(self, name: str) -> LoadedSkill | None:
        if not self._is_allowed(name):
            return None

        if name in self._cache:
            return self._cache[name]

        for base_path in self._search_paths:
            if not base_path.exists():
                continue
            for skill_file in base_path.rglob("SKILL.md"):
                try:
                    skill = self._parse_skill_file(skill_file)
                    if skill.meta.name == name and self._is_allowed(skill.meta.name):
                        self._cache[name] = skill
                        return skill
                except Exception:
                    continue

        return None

    def _parse_skill_file(self, filepath: Path) -> LoadedSkill:
        text = filepath.read_text(encoding="utf-8")
        meta = SkillMeta(name=filepath.stem)
        body = text

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                meta = SkillMeta(
                    name=frontmatter.get("name", filepath.stem),
                    description=frontmatter.get("description", ""),
                    origin=frontmatter.get("origin", ""),
                    allowed_tools=frontmatter.get("allowed-tools", ""),
                    argument_hint=frontmatter.get("argument-hint", ""),
                    disable_model_invocation=frontmatter.get(
                        "disable-model-invocation", False
                    ),
                )
                body = parts[2].strip()

        return LoadedSkill(meta=meta, body=body, source_path=str(filepath))
