from __future__ import annotations

import json

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./demand_radar.db"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    MAX_POSTS_PER_BATCH: int = 50
    ADMIN_API_TOKEN: str = ""

    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    FIRECRAWL_API_KEY: str = ""
    FIRECRAWL_API_BASE: str = ""

    HTTP_PROXY: str = ""

    # Crawl anti-detection: jittered delay between requests (seconds)
    CRAWL_MIN_DELAY: float = 1.0
    CRAWL_MAX_DELAY: float = 3.0
    CRAWL_MAX_RETRIES: int = 3
    CRAWL_BACKOFF_BASE: float = 2.0
    CRAWL_RATE_LIMIT_CONCURRENT: int = 2

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEDUP_THRESHOLD: float = 0.85

    # Skill/plugin ecosystem — only load skills relevant to demand research
    SKILL_SEARCH_PATHS: str = "~/.claude/plugins/marketplaces/ecc/skills"
    SKILL_ALLOWLIST: str = (
        "market-research,deep-research,research-ops,lead-intelligence,"
        "data-scraper-agent,exa-search,search-first,literature-review,"
        "social-graph-ranker"
    )
    MCP_SERVERS_CONFIG: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def skill_search_paths(self) -> list[str]:
        return [p.strip() for p in self.SKILL_SEARCH_PATHS.split(",") if p.strip()]

    @property
    def skill_allowlist(self) -> list[str]:
        return [s.strip() for s in self.SKILL_ALLOWLIST.split(",") if s.strip()]

    @property
    def mcp_servers(self) -> dict:
        if not self.MCP_SERVERS_CONFIG:
            return {}
        try:
            return json.loads(self.MCP_SERVERS_CONFIG)
        except json.JSONDecodeError:
            return {}


settings = Settings()
