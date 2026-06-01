from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillMeta:
    name: str
    description: str = ""
    origin: str = ""
    allowed_tools: str = ""
    argument_hint: str = ""
    disable_model_invocation: bool = False


@dataclass
class LoadedSkill:
    meta: SkillMeta
    body: str
    source_path: str = ""


@dataclass
class MCPServerConfig:
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    timeout: float = 60.0


@dataclass
class ToolInfo:
    name: str
    description: str = ""
    server_name: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearcherCapability:
    """A resolved research capability combining a skill + MCP tools."""

    name: str
    skill: LoadedSkill | None = None
    tools: list[ToolInfo] = field(default_factory=list)
    legacy_class: type | None = None
