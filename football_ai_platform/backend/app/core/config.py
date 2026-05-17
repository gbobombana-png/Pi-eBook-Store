from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Football AI Platform"
    version: str = "1.0.0"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/football_ai"
    redis_url: str = "redis://localhost:6379"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ML
    model_cache_ttl: int = 3600       # 1h cache pour les prédictions
    live_update_interval: int = 60    # secondes entre recalculs live

    # Suspicion thresholds
    suspicion_high_threshold: float = 70.0
    suspicion_medium_threshold: float = 40.0
    odds_sharp_move_pct: float = 0.08   # 8% mouvement = sharp bet
    volume_anomaly_multiplier: float = 3.0  # 3x volume normal = anomalie

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
