import redis.asyncio as aioredis
import redis.exceptions
import logging
import asyncio
import fnmatch
from backend.app.core.config import settings

logger = logging.getLogger("redis_manager")

class SafeRedisPubSub:
    async def subscribe(self, *args, **kwargs):
        return True

    async def unsubscribe(self, *args, **kwargs):
        return True

    async def listen(self):
        # Async generator yielding nothing
        if False:
            yield None

class SafeRedisPipeline:
    def __init__(self, pipeline, fallback_db):
        self._pipeline = pipeline
        self._fallback_db = fallback_db
        self._commands = []

    def incr(self, key):
        if self._pipeline:
            try:
                self._pipeline.incr(key)
            except Exception:
                pass
        self._commands.append(("incr", key, None))
        return self

    def expire(self, key, seconds):
        if self._pipeline:
            try:
                self._pipeline.expire(key, seconds)
            except Exception:
                pass
        self._commands.append(("expire", key, seconds))
        return self

    async def execute(self):
        if self._pipeline:
            try:
                return await self._pipeline.execute()
            except Exception as e:
                logger.warning(f"Redis pipeline execute failed: {e}. Executing on local memory fallback.")
        
        # Execute on local memory fallback
        results = []
        for cmd, key, val in self._commands:
            if cmd == "incr":
                curr = self._fallback_db.get(key, 0)
                try:
                    curr_val = int(curr)
                except Exception:
                    curr_val = 0
                new_val = curr_val + 1
                self._fallback_db[key] = str(new_val)
                results.append(new_val)
            elif cmd == "expire":
                results.append(True)
        return results

class SafeRedisClient:
    def __init__(self, client):
        self._client = client
        self._fallback_db = {}  # In-memory dictionary fallback

    async def get(self, key):
        try:
            val = await self._client.get(key)
            # If standard return is bytes, decode it
            if val is not None:
                return val.decode("utf-8") if isinstance(val, bytes) else str(val)
            return None
        except Exception as e:
            logger.warning(f"Redis get failed for {key}: {str(e)}. Using local memory fallback.")
            val = self._fallback_db.get(key)
            return val.decode("utf-8") if isinstance(val, bytes) else (str(val) if val is not None else None)

    async def set(self, key, value, *args, **kwargs):
        try:
            return await self._client.set(key, value, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Redis set failed for {key}: {str(e)}. Using local memory fallback.")
            self._fallback_db[key] = value
            return True

    async def setex(self, key, time, value):
        try:
            return await self._client.setex(key, time, value)
        except Exception as e:
            logger.warning(f"Redis setex failed for {key}: {str(e)}. Using local memory fallback.")
            self._fallback_db[key] = value
            return True

    async def exists(self, key):
        try:
            return await self._client.exists(key)
        except Exception as e:
            logger.warning(f"Redis exists failed for {key}: {str(e)}. Using local memory fallback.")
            return 1 if key in self._fallback_db else 0

    async def delete(self, key):
        try:
            return await self._client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed for {key}: {str(e)}. Using local memory fallback.")
            self._fallback_db.pop(key, None)
            return True

    async def keys(self, pattern):
        try:
            return await self._client.keys(pattern)
        except Exception as e:
            logger.warning(f"Redis keys failed for pattern {pattern}: {str(e)}. Using local memory fallback.")
            return [k for k in self._fallback_db.keys() if fnmatch.fnmatch(k, pattern)]

    async def hset(self, key, mapping=None, *args, **kwargs):
        try:
            if mapping:
                return await self._client.hset(key, mapping=mapping, *args, **kwargs)
            return await self._client.hset(key, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Redis hset failed for {key}: {str(e)}. Using local memory fallback.")
            if key not in self._fallback_db:
                self._fallback_db[key] = {}
            if isinstance(self._fallback_db[key], dict):
                if mapping:
                    self._fallback_db[key].update(mapping)
                elif len(args) >= 2:
                    self._fallback_db[key][args[0]] = args[1]
            return True

    async def hget(self, key, field):
        try:
            val = await self._client.hget(key, field)
            if val is not None:
                return val.decode("utf-8") if isinstance(val, bytes) else str(val)
            return None
        except Exception as e:
            logger.warning(f"Redis hget failed for {key}:{field}: {str(e)}. Using local memory fallback.")
            val = self._fallback_db.get(key)
            if isinstance(val, dict):
                field_val = val.get(field)
                if field_val is not None:
                    return field_val.decode("utf-8") if isinstance(field_val, bytes) else str(field_val)
            return None

    async def scard(self, key):
        try:
            return await self._client.scard(key)
        except Exception as e:
            logger.warning(f"Redis scard failed for {key}: {str(e)}. Using local memory fallback.")
            val = self._fallback_db.get(key)
            if isinstance(val, set):
                return len(val)
            return 0

    async def sadd(self, key, *values):
        try:
            return await self._client.sadd(key, *values)
        except Exception as e:
            logger.warning(f"Redis sadd failed for {key}: {str(e)}. Using local memory fallback.")
            if key not in self._fallback_db:
                self._fallback_db[key] = set()
            if isinstance(self._fallback_db[key], set):
                for v in values:
                    self._fallback_db[key].add(v)
            return len(values)

    async def srem(self, key, *values):
        try:
            return await self._client.srem(key, *values)
        except Exception as e:
            logger.warning(f"Redis srem failed for {key}: {str(e)}. Using local memory fallback.")
            val = self._fallback_db.get(key)
            if isinstance(val, set):
                count = 0
                for v in values:
                    if v in val:
                        val.remove(v)
                        count += 1
                return count
            return 0

    def pubsub(self):
        try:
            return self._client.pubsub()
        except Exception:
            return SafeRedisPubSub()

    async def ping(self):
        try:
            return await self._client.ping()
        except Exception:
            return False

    async def aclose(self):
        try:
            await self._client.aclose()
        except Exception:
            pass

    def pipeline(self):
        try:
            return SafeRedisPipeline(self._client.pipeline(), self._fallback_db)
        except Exception:
            return SafeRedisPipeline(None, self._fallback_db)

class RedisManager:
    def __init__(self):
        client = aioredis.from_url(settings.REDIS_URL, decode_responses=False) # Keep original bytes/string decoding control
        self.client = SafeRedisClient(client)

    async def ping(self) -> bool:
        return await self.client.ping()

    async def close(self):
        await self.client.aclose()

    async def blacklist_token(self, jti: str, expires_in_seconds: int):
        try:
            await self.client.setex(f"blacklist:{jti}", expires_in_seconds, "true")
        except Exception:
            pass

    async def is_token_blacklisted(self, jti: str) -> bool:
        try:
            return await self.client.exists(f"blacklist:{jti}") == 1
        except Exception:
            return False

    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        try:
            current = await self.client.get(key)
            if current is not None and int(current) >= limit:
                return False
            
            pipeline = self.client.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, window_seconds)
            await pipeline.execute()
            return True
        except Exception:
            return True

redis_manager = RedisManager()
