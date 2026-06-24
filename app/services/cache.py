from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    # В файле app/services/cache.py метод init_redis должен быть таким:
    def init_redis(self):
        self.redis = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
            encoding="utf-8",
            decode_responses=True
        )

    async def set_cache(self, key: str, value: str, expire_seconds: int = 300):
        """Записать данные в кэш с временем жизни (по умолчанию 5 минут)."""
        if self.redis:
            await self.redis.set(key, value, ex=expire_seconds)

    async def get_cache(self, key: str) -> Optional[str]:
        """Получить данные из кэша."""
        if self.redis:
            return await self.redis.get(key)
        return None

    async def delete_cache(self, key: str):
        """Удалить ключ из кэша."""
        if self.redis:
            await self.redis.delete(key)

cache_service = CacheService()