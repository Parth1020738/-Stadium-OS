import hashlib
import json
import os
from typing import Optional
from backend.app.core.redis import redis_manager

class CacheService:
    def __init__(self):
        self.default_ttl = int(os.getenv("AI_CACHE_TTL", "3600"))
        self.enabled = os.getenv("ENABLE_AI_CACHE", "true").lower() == "true"

    def _generate_key(self, prompt: str, context: str, operator: str, model: str) -> str:
        """Create a unique cache key based on prompt, context hash, operator, and model."""
        context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return f"ai_cache:{model}:{operator}:{prompt_hash}:{context_hash}"

    async def get_response(self, prompt: str, context: str, operator: str, model: str) -> Optional[str]:
        """Fetch cached response if cache is enabled."""
        if not self.enabled:
            return None
        
        key = self._generate_key(prompt, context, operator, model)
        try:
            val = await redis_manager.client.get(key)
            if val:
                return val.decode("utf-8") if isinstance(val, bytes) else str(val)
        except Exception:
            pass
        return None

    async def cache_response(self, prompt: str, context: str, operator: str, model: str, response: str, ttl: Optional[int] = None):
        """Cache the AI response."""
        if not self.enabled:
            return
        
        key = self._generate_key(prompt, context, operator, model)
        expire = ttl if ttl is not None else self.default_ttl
        try:
            # We can use setex for TTL or set + expire
            await redis_manager.client.setex(key, expire, response)
        except Exception:
            pass
