import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, AsyncMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force Environment to "Laboratory Mode" (No Cloud Vars)
os.environ.pop("GCP_PROJECT_ID", None)
os.environ.pop("SPANNER_INSTANCE_ID", None)
os.environ.pop("REDIS_HOST", None)
os.environ["MOCK_GEMINI"] = "true" # Keep mock for Gemini to avoid API calls

# Re-import modules to ensure config is re-evaluated or handled
# Note: Modules are cached in sys.modules, so this only tests runtime logic if we call methods.
# For config, we'd need reload, but since we modify behavior at call time, it's fine.

from app.services.cache import RedisCache, cache
from app.services.subconscious import SubconsciousMind
from app.repositories.local_graph import LocalSoulRepository

async def test_lab_mode():
    print("🧪 Testing Laboratory Mode (Fallback Resilience)...")

    # 1. Test Redis Fallback
    print("\n[Test 1] Cache Fallback (No Redis)")
    # Reset singleton state for test
    cache.client = None
    cache.connected = False

    # Try to initialize (Should fail but not crash, enabling local cache)
    await cache.initialize()

    if cache.connected:
        print("❌ Failed: Should not be connected to Real Redis without host.")
    else:
        print("✅ Redis Connection correctly failed/skipped.")

    # Test Set/Get in Fallback
    await cache.set("lab_key", "lab_value")
    val = await cache.get("lab_key")

    if val == "lab_value":
        print("✅ Local Cache Fallback working (Set/Get).")
    else:
        print(f"❌ Local Cache failed. Got: {val}")
        sys.exit(1)

    # 2. Test Repository Selection
    # Since we unset GCP vars, main.py logic (simulated here) should pick Local
    print("\n[Test 2] Repository Selection")
    from core.config import settings

    if settings.GCP_PROJECT_ID:
        print(f"⚠️ Warning: GCP_PROJECT_ID is still set to {settings.GCP_PROJECT_ID}. Test might be invalid.")

    repo = LocalSoulRepository() # Explicitly testing Local behavior
    await repo.initialize()
    user = await repo.get_or_create_user("lab_rat_001")
    print(f"✅ Local Repo working. Created User: {user.name}")

    # 3. Test Subconscious Fallback (Keyword)
    print("\n[Test 3] Subconscious Fallback (Keywords)")
    mind = SubconsciousMind()
    # Mock client to None to force fallback path even if API key exists
    mind.client = None

    res = await mind._analyze_sentiment("I am very sad and lonely.")
    if "gentle and supportive" in str(res):
        print("✅ Keyword Fallback working.")
    else:
        print(f"❌ Keyword Fallback failed. Got: {res}")
        sys.exit(1)

    print("\n🏁 Laboratory Mode Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_lab_mode())
