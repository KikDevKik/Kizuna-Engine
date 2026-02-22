import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, AsyncMock, ANY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.sleep_manager import SleepManager
from app.repositories.local_graph import LocalSoulRepository

async def test_rem_sleep_debounce():
    print("🌙 Testing REM Sleep Debounce Logic...")

    # 1. Setup Repo and Manager
    repo = LocalSoulRepository()
    # Mock consolidate_memories to track calls
    repo.consolidate_memories = AsyncMock()

    manager = SleepManager(repo)
    # Set short grace period for test
    manager.grace_period = 2

    user_id = "dreamer_001"

    # 2. Case A: Disconnect -> Reconnect (Cancel Sleep)
    print("\n[Case A] User disconnects and reconnects quickly...")
    await manager.schedule_sleep(user_id)
    print("   User disconnected. Timer started.")

    await asyncio.sleep(0.5) # Wait less than grace period

    print("   User reconnecting...")
    await manager.cancel_sleep(user_id)

    # Wait to ensure timer would have fired if not cancelled
    await asyncio.sleep(2.0)

    if repo.consolidate_memories.call_count == 0:
        print("✅ SUCCESS: Consolidation cancelled correctly.")
    else:
        print("❌ FAILURE: Consolidation triggered unexpectedly.")
        sys.exit(1)

    # 3. Case B: Disconnect -> Timeout (Trigger Sleep)
    print("\n[Case B] User disconnects and stays offline...")
    await manager.schedule_sleep(user_id)
    print(f"   User disconnected. Waiting {manager.grace_period}s...")

    await asyncio.sleep(2.5) # Wait longer than grace period

    if repo.consolidate_memories.call_count == 1:
        print("✅ SUCCESS: Consolidation triggered after grace period.")
        # Verify call args
        repo.consolidate_memories.assert_called_with(user_id, dream_generator=ANY)
    else:
        print(f"❌ FAILURE: Consolidation call count: {repo.consolidate_memories.call_count}")
        sys.exit(1)

    print("\n🏁 Phase 4 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_rem_sleep_debounce())
