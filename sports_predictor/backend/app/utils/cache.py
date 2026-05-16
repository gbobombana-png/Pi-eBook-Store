import json
import redis.asyncio as redis
from typing import Any, Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
_redis: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        value = await r.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        logger.warning(f"Cache GET error [{key}]: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL) -> bool:
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning(f"Cache SET error [{key}]: {e}")
        return False


async def cache_delete(key: str) -> bool:
    try:
        r = await get_redis()
        await r.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Cache DELETE error [{key}]: {e}")
        return False


def cache_key(*parts: str) -> str:
    return ":".join(["sp", *parts])
