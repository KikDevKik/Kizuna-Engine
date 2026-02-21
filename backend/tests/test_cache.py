import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.cache import RedisCache
from collections import OrderedDict

@pytest.fixture
def cache_instance():
    # Create a fresh instance for each test to avoid singleton side effects
    return RedisCache()

@pytest.mark.asyncio
async def test_initialize_redis_success(cache_instance):
    with patch("app.services.cache.redis") as mock_redis:
        mock_client = AsyncMock()
        mock_redis.Redis.return_value = mock_client
        mock_client.ping.return_value = True

        await cache_instance.initialize()

        assert cache_instance.connected is True
        assert cache_instance.client == mock_client
        mock_client.ping.assert_called_once()

@pytest.mark.asyncio
async def test_initialize_redis_failure(cache_instance):
    with patch("app.services.cache.redis") as mock_redis:
        mock_client = AsyncMock()
        mock_redis.Redis.return_value = mock_client
        # ping fails
        mock_client.ping.side_effect = Exception("Connection refused")

        await cache_instance.initialize()

        assert cache_instance.connected is False
        assert cache_instance.client is None
        assert isinstance(cache_instance.local_cache, OrderedDict)

@pytest.mark.asyncio
async def test_local_cache_operations(cache_instance):
    # Ensure we are in fallback mode
    cache_instance.connected = False

    await cache_instance.set("test_key", "test_value")
    val = await cache_instance.get("test_key")

    assert val == "test_value"
    assert cache_instance.local_cache["test_key"] == "test_value"

@pytest.mark.asyncio
async def test_local_cache_lru_eviction(cache_instance):
    cache_instance.connected = False
    # Set a small MAX_LOCAL_CACHE_SIZE for testing
    cache_instance.MAX_LOCAL_CACHE_SIZE = 2

    await cache_instance.set("k1", "v1")
    await cache_instance.set("k2", "v2")
    await cache_instance.set("k3", "v3") # Should evict k1

    assert await cache_instance.get("k1") is None
    assert await cache_instance.get("k2") == "v2"
    assert await cache_instance.get("k3") == "v3"

    # Test LRU update on get
    await cache_instance.get("k2") # k2 is now most recent
    await cache_instance.set("k4", "v4") # Should evict k3

    assert await cache_instance.get("k3") is None
    assert await cache_instance.get("k2") == "v2"
    assert await cache_instance.get("k4") == "v4"

@pytest.mark.asyncio
async def test_redis_cache_operations(cache_instance):
    mock_client = AsyncMock()
    cache_instance.client = mock_client
    cache_instance.connected = True

    # Test set
    await cache_instance.set("rkey", "rval", ttl=30)
    mock_client.set.assert_called_once_with("rkey", "rval", ex=30)

    # Test get
    mock_client.get.return_value = "rval"
    val = await cache_instance.get("rkey")
    assert val == "rval"
    mock_client.get.assert_called_once_with("rkey")

@pytest.mark.asyncio
async def test_initialize_redis_missing_library(cache_instance):
    with patch("app.services.cache.redis", None):
        await cache_instance.initialize()
        assert cache_instance.connected is False
        assert cache_instance.client is None
