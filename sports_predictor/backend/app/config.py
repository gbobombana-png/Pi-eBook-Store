from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "SportPredictor Pro"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/sportpredictor"

    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600

    API_FOOTBALL_KEY: Optional[str] = None
    API_FOOTBALL_HOST: str = "api-football-v1.p.rapidapi.com"

    ODDS_API_KEY: Optional[str] = None
    ODDS_API_BASE: str = "https://api.the-odds-api.com/v4"

    DAILY_GENERATION_HOUR: int = 7
    DAILY_GENERATION_MINUTE: int = 0
    TICKETS_PER_DAY: int = 5
    TARGET_ODDS: float = 5.0

    MODEL_PATH: str = "ml/models/predictor.pkl"
    MIN_CONFIDENCE: int = 60

    @model_validator(mode="after")
    def fix_database_url(self) -> "Settings":
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            self.DATABASE_URL = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            self.DATABASE_URL = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self

    model_config = {"env_file": ".env", "case_sensitive": True}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
