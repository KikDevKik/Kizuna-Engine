import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from app.services.sleep_manager import SleepManager

@pytest.mark.asyncio
async def test_shutdown_prevents_scheduling():
    # Mock dependencies
    repo_mock = Mock()
    sleep_manager = SleepManager(repo_mock)

    # Initial state
    assert sleep_manager._is_shutting_down is False
    assert len(sleep_manager.active_timers) == 0

    # 1. Schedule sleep normally
    await sleep_manager.schedule_sleep("user_1")
    assert "user_1" in sleep_manager.active_timers
    assert len(sleep_manager.active_timers) == 1

    # Verify task is running (or at least created)
    task = sleep_manager.active_timers["user_1"]
    assert not task.done()

    # 2. Shutdown the manager
    await sleep_manager.shutdown()

    # Verify state after shutdown
    assert sleep_manager._is_shutting_down is True
    assert len(sleep_manager.active_timers) == 0  # Tasks should be cleared

    # 3. Try to schedule sleep AFTER shutdown
    await sleep_manager.schedule_sleep("user_2")

    # Verify NO new task was created
    assert "user_2" not in sleep_manager.active_timers
    assert len(sleep_manager.active_timers) == 0

@pytest.mark.asyncio
async def test_shutdown_cancels_existing_tasks():
    # Mock dependencies
    repo_mock = Mock()
    sleep_manager = SleepManager(repo_mock)

    # Schedule a task
    await sleep_manager.schedule_sleep("user_3", delay=10) # 10s delay
    task = sleep_manager.active_timers["user_3"]

    assert not task.done()

    # Shutdown
    await sleep_manager.shutdown()

    # Task should be cancelled and removed
    assert task.cancelled() or task.done()
    assert "user_3" not in sleep_manager.active_timers

if __name__ == "__main__":
    asyncio.run(test_shutdown_prevents_scheduling())
    asyncio.run(test_shutdown_cancels_existing_tasks())
