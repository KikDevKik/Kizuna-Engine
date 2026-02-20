import redis.asyncio as redis
import logging
from core.config import settings
import asyncio

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Phase 5: Neural Sync (Redis Layer).
    Handles ephemeral storage for Warm-up and Session State.
    """
    _instance = None

    def __init__(self):
        self.client = None
        self.connected = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RedisCache()
        return cls._instance

    async def initialize(self):
        """Connect to Redis."""
        try:
            # Check if we should use Mock Redis (for tests/local dev without redis)
            # Or assume real Redis if host is set.
            # If connection fails, we can fallback or log error.

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
            logger.warning(f"⚠️ Redis Connection Failed: {e}. Running without Cache.")
            self.connected = False
            self.client = None

    async def set(self, key: str, value: str, ttl: int = 60):
        """Set key with TTL (seconds)."""
        if not self.connected or not self.client:
            return
        try:
            await self.client.set(key, value, ex=ttl)
        except Exception as e:
            logger.error(f"Redis Set Error: {e}")

    async def get(self, key: str) -> str | None:
        """Get value by key."""
        if not self.connected or not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis Get Error: {e}")
            return None

    async def close(self):
        if self.client:
            await self.client.close()

# Singleton
cache = RedisCache.get_instance()
