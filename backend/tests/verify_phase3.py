import asyncio
import logging
import sys
import os
from pathlib import Path
from asyncio import Queue
from unittest.mock import AsyncMock

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.repositories.local_graph import LocalSoulRepository
from app.models.graph import AgentNode, UserNode
from app.services.subconscious import SubconsciousMind

# Use a test DB file
TEST_DB_PATH = Path("test_graph.json")

async def test_phase3_graph_integration():
    print("🕸️  Starting Phase 3.1 Graph Simulation Test...")

    # 1. Initialize Repository
    repo = LocalSoulRepository(data_path=TEST_DB_PATH)
    await repo.initialize()
    print("✅ Repository Initialized.")

    # 2. Seed Data
    agent = AgentNode(id="test_kizuna", name="TestKizuna", base_instruction="You are a test.")
    await repo.create_agent(agent)

    user = await repo.get_or_create_user("test_user_001")
    print(f"✅ User Created: {user.name}")

    # 3. Verify Resonance Initialization
    res = await repo.get_resonance("test_user_001", "test_kizuna")
    print(f"✅ Initial Resonance: {res.affinity_level}")
    assert res.affinity_level == 0

    # 4. Test Subconscious Persistence
    # Simulate the subconscious detecting "happy" and updating the graph
    print("\n🧠 Testing Subconscious Memory Persistence...")

    mind = SubconsciousMind()
    mind.set_repository(repo)

    transcript_queue = Queue()
    injection_queue = Queue()

    # Start Mind Task
    mind_task = asyncio.create_task(mind.start(transcript_queue, injection_queue, "test_user_001", "test_kizuna"))

    # Feed "happy" trigger
    # Sending it in small chunks to ensure it's not discarded by logic
    await transcript_queue.put("I am so ")
    await transcript_queue.put("happy and excited today!")

    # Wait for processing (increased for CI/CD environments)
    await asyncio.sleep(2.0)

    # 5. Verify Graph Updates
    # Resonance should have increased
    res_updated = await repo.get_resonance("test_user_001", "test_kizuna")
    print(f"✅ Updated Resonance: {res_updated.affinity_level}")

    if res_updated.affinity_level > 0:
        print("🎉 SUCCESS: Resonance increased based on emotional trigger!")
    else:
        print("❌ FAILURE: Resonance did not increase.")
        sys.exit(1)

    # Check Episodes
    # We can't easily query episodes by user in the simple repo yet (need to check 'experienced' dict)
    user_episodes = repo.experienced.get("test_user_001", [])
    print(f"✅ Memory Episodes Count: {len(user_episodes)}")

    if len(user_episodes) > 0:
        episode_id = user_episodes[0]
        episode = repo.episodes.get(episode_id)
        print(f"   Episode Content: {episode.summary}")
    else:
         print("❌ FAILURE: No episode saved.")
         sys.exit(1)

    # Cleanup
    mind_task.cancel()
    try:
        await mind_task
    except asyncio.CancelledError:
        pass

    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    if TEST_DB_PATH.with_suffix(".tmp").exists():
        TEST_DB_PATH.with_suffix(".tmp").unlink()

    print("\n🏁 Phase 3.1 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_phase3_graph_integration())
