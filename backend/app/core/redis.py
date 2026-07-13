import redis.asyncio as aioredis
import redis.exceptions
from backend.app.core.config import settings

class RedisManager:
    def __init__(self):
        # Decode Redis URL from configuration
        self.client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def ping(self) -> bool:
        try:
            return await self.client.ping()
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()

    async def blacklist_token(self, jti: str, expires_in_seconds: int):
        try:
            await self.client.setex(f"blacklist:{jti}", expires_in_seconds, "true")
        except redis.exceptions.ConnectionError:
            pass

    async def is_token_blacklisted(self, jti: str) -> bool:
        try:
            return await self.client.exists(f"blacklist:{jti}") == 1
        except redis.exceptions.ConnectionError:
            return False

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        """
        Simple rate limiting check utilizing a sliding counter window
        """
        try:
            current = await self.client.get(key)
            if current is not None and int(current) >= limit:
                return False
            
            pipeline = self.client.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, window_seconds)
            await pipeline.execute()
            return True
        except redis.exceptions.ConnectionError:
            return True

redis_manager = RedisManager()
