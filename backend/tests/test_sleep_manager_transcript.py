import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.sleep_manager import SleepManager
from app.repositories.base import SoulRepository

# Configure logging to see output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_sleep_manager_lifecycle():
    logger.info("--- Starting Test ---")

    # Mock Repository
    repo_mock = AsyncMock(spec=SoulRepository)
    # Ensure methods are async mocks
    repo_mock.save_episode = AsyncMock()
    repo_mock.consolidate_memories = AsyncMock()

    # Initialize SleepManager
    sleep_manager = SleepManager(repo_mock)
    # Shorten grace period for test
    sleep_manager.grace_period = 0.5

    user_id = "test_user"
    agent_id = "test_agent"
    transcript = "User: Hello\nAgent: Hi there!"

    # 1. Test Schedule Sleep with Transcript
    logger.info("1. Scheduling Sleep with Transcript...")
    await sleep_manager.schedule_sleep(
        user_id=user_id,
        agent_id=agent_id,
        raw_transcript=transcript
    )

    # Verify transcript is pending
    assert user_id in sleep_manager.pending_transcripts
    assert sleep_manager.pending_transcripts[user_id]["transcript"] == transcript
    logger.info("✅ Transcript is pending.")

    # 2. Wait for Grace Period to Expire (Normal Execution)
    logger.info("2. Waiting for grace period...")
    await asyncio.sleep(0.7) # Wait slightly longer than 0.5s

    # Verify save_episode was called
    repo_mock.save_episode.assert_called_with(
        user_id=user_id,
        agent_id=agent_id,
        summary="Full Session Transcript",
        valence=0.0,
        raw_transcript=transcript
    )
    logger.info("✅ save_episode called correctly after timer.")

    # Verify pending transcript is removed
    assert user_id not in sleep_manager.pending_transcripts
    logger.info("✅ Pending transcript removed.")

    # Verify consolidation triggered
    # We can just check called because matching the bound method is tricky without importing the exact instance
    assert repo_mock.consolidate_memories.called
    logger.info("✅ Consolidation triggered.")


    # Reset mocks for Shutdown Test
    repo_mock.reset_mock()
    sleep_manager.active_timers.clear()
    sleep_manager.pending_transcripts.clear()
    sleep_manager._is_shutting_down = False # Reset shutdown state if needed

    # 3. Test Shutdown Rescue
    logger.info("3. Testing Shutdown Rescue...")

    # Schedule again
    await sleep_manager.schedule_sleep(
        user_id=user_id,
        agent_id=agent_id,
        raw_transcript=transcript
    )

    # Verify pending
    assert user_id in sleep_manager.pending_transcripts

    # Trigger Shutdown immediately (before grace period)
    logger.info("Calling shutdown...")
    await sleep_manager.shutdown()

    # Verify save_episode was called explicitly by shutdown
    repo_mock.save_episode.assert_called_with(
        user_id=user_id,
        agent_id=agent_id,
        summary="Full Session Transcript",
        valence=0.0,
        raw_transcript=transcript
    )
    logger.info("✅ save_episode called during shutdown.")

    # Verify consolidation was forced
    assert repo_mock.consolidate_memories.called
    logger.info("✅ Consolidation forced during shutdown.")

    # 4. Test Cancel Sleep (Reconnection) - Ensure Clean up
    repo_mock.reset_mock()
    sleep_manager._is_shutting_down = False

    logger.info("4. Testing Reconnection Cleanup...")
    await sleep_manager.schedule_sleep(
        user_id=user_id,
        agent_id=agent_id,
        raw_transcript=transcript
    )
    assert user_id in sleep_manager.pending_transcripts

    # Simulate Reconnection
    await sleep_manager.cancel_sleep(user_id)

    # Verify transcript removed
    assert user_id not in sleep_manager.pending_transcripts
    logger.info("✅ Pending transcript removed on reconnection.")

    # Verify save_episode NOT called
    assert not repo_mock.save_episode.called
    logger.info("✅ save_episode NOT called on reconnection.")

    logger.info("🎉 All Tests Passed!")
