from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./demand_radar.db"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    MAX_POSTS_PER_BATCH: int = 50
    ADMIN_API_TOKEN: str = ""

    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "demand-radar/1.0"

    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    HTTP_PROXY: str = ""

    REPORT_GENERATION_HOUR: int = 8

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEDUP_THRESHOLD: float = 0.85

    CRAWL_INTERVAL_MINUTES: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
