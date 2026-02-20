import asyncio
import logging
import sys
import os
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set Env Vars
os.environ["REDIS_HOST"] = "mock-redis"

from app.services.cache import RedisCache
from app.routers.warmup import perform_warmup
from app.services.audio_session import send_to_gemini

async def test_redis_warmup():
    print("⚡ Testing Redis Warm-up Logic (Mock)...")

    # 1. Mock Redis
    with patch("redis.asyncio.Redis") as MockRedis:
        mock_client = AsyncMock()
        MockRedis.return_value = mock_client

        # Initialize Cache
        cache = RedisCache.get_instance()
        await cache.initialize()

        # Test Set
        await cache.set("test_key", "test_value", ttl=10)
        mock_client.set.assert_called_with("test_key", "test_value", ex=10)
        print("✅ Redis Set called correctly.")

        # Test Get
        mock_client.get.return_value = "cached_soul"
        val = await cache.get("test_key")
        assert val == "cached_soul"
        print("✅ Redis Get retrieved correct value.")

async def test_multimodal_flow():
    print("\n📷 Testing Multimodal (Video) Flow...")

    # Mock WebSocket & Session
    mock_ws = AsyncMock()
    mock_session = AsyncMock()

    # 1. Simulate Image Message
    image_payload = {
        "type": "image",
        "data": "SGVsbG8gV29ybGQ=" # "Hello World" in base64
    }

    # WS receive returns: 1. Image JSON, 2. Cancel/Empty to stop loop
    mock_ws.receive.side_effect = [
        {"text": json.dumps(image_payload)},
        asyncio.CancelledError() # Stop loop
    ]

    try:
        await send_to_gemini(mock_ws, mock_session)
    except asyncio.CancelledError:
        pass

    # Verify Session Send
    # Expect: input={"data": b"Hello World", "mime_type": "image/jpeg"}
    mock_session.send.assert_called()
    call_args = mock_session.send.call_args
    input_arg = call_args.kwargs.get("input")

    assert input_arg["mime_type"] == "image/jpeg"
    assert input_arg["data"] == b"Hello World"
    print("✅ Video Frame forwarded to Gemini correctly.")

if __name__ == "__main__":
    asyncio.run(test_redis_warmup())
    asyncio.run(test_multimodal_flow())
