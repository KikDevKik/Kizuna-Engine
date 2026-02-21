try:
    import redis.asyncio as redis
except ImportError:
    redis = None

import logging
from core.config import settings
import asyncio
from collections import OrderedDict

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Phase 5: Neural Sync (Redis Layer).
    Handles ephemeral storage for Warm-up and Session State.
    """
    _instance = None
    MAX_LOCAL_CACHE_SIZE = 1000

    def __init__(self):
        self.client = None
        self.connected = False
        self.local_cache = OrderedDict() # Fallback for Local Mode

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RedisCache()
        return cls._instance

    async def initialize(self):
        """Connect to Redis."""
        if redis is None:
            logger.warning("⚠️ redis library missing. Using Local Memory Cache.")
            self.connected = False
            self.client = None
            self.local_cache = OrderedDict()
            return

        try:
            logger.info(f"Connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            await self.client.ping()
            self.connected = True
            logger.info("✅ Redis Connected.")
        except Exception as e:
            logger.warning(f"⚠️ Redis Connection Failed: {e}. Switching to Local Memory Cache (Fallback Mode).")
            self.connected = False
            self.client = None
            self.local_cache = OrderedDict()

    async def set(self, key: str, value: str, ttl: int = 60):
        """Set key with TTL (seconds)."""
        if not self.connected or not self.client:
            # Fallback
            if key in self.local_cache:
                self.local_cache.move_to_end(key)
            self.local_cache[key] = value
            if len(self.local_cache) > self.MAX_LOCAL_CACHE_SIZE:
                self.local_cache.popitem(last=False)
            return

        try:
            await self.client.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Redis Set Error: {e}")

    async def get(self, key: str) -> str | None:
        """Get value by key."""
        if not self.connected or not self.client:
            # Fallback
            val = self.local_cache.get(key)
            if val:
                self.local_cache.move_to_end(key)
                logger.info(f"⚡ Local Cache Hit: {key}")
            return val

        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis Get Error: {e}")
            return None

    async def delete(self, key: str):
        """Delete key."""
        if not self.connected or not self.client:
            if key in self.local_cache:
                del self.local_cache[key]
            return

        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis Delete Error: {e}")

    async def scan_match(self, pattern: str) -> list[str]:
        """Scan keys matching pattern."""
        if not self.connected or not self.client:
            # Simple list comp for local cache
            # pattern usually ends with *
            prefix = pattern.replace("*", "")
            return [k for k in self.local_cache.keys() if k.startswith(prefix)]

        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            return keys
        except Exception as e:
            logger.error(f"Redis Scan Error: {e}")
            return []

    async def close(self):
        if self.client:
            await self.client.close()

# Singleton
cache = RedisCache.get_instance()
