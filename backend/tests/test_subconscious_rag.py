import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.subconscious import SubconsciousMind
from app.models.graph import CollectiveEventNode

@pytest.mark.asyncio
async def test_subconscious_event_rag_injection():
    """
    Verifies that if a relevant collective event is found, it is injected into the queue.
    """
    service = SubconsciousMind()
    mock_repo = AsyncMock()
    service.set_repository(mock_repo)

    # Mock analyze_sentiment to return None (no emotion hint)
    service._analyze_sentiment = AsyncMock(return_value=None)
    service._process_battery_drain = AsyncMock()

    # Mock get_relevant_episodes to return empty
    mock_repo.get_relevant_episodes.return_value = []

    # Mock get_relevant_collective_events to return a mock event
    mock_event = CollectiveEventNode(
        type="CONFLICT",
        summary="Great War of Data",
        outcome="FOUGHT"
    )
    # Ensure the method exists on the mock
    mock_repo.get_relevant_collective_events = AsyncMock(return_value=[mock_event])

    # We need to ensure hasattr(mock_repo, 'get_relevant_collective_events') is True
    # MagicMock usually handles this, but AsyncMock might be tricky.
    # By assigning it, hasattr should work.

    transcript_queue = asyncio.Queue()
    injection_queue = asyncio.Queue()

    # Start loop
    task = asyncio.create_task(service.start(transcript_queue, injection_queue, "user", "agent"))

    # Feed input
    await transcript_queue.put("Tell me about the war.")

    try:
        # Expect injection
        payload = await asyncio.wait_for(injection_queue.get(), timeout=5.0)
        text = payload["text"]
        assert "SYSTEM_HINT: 🌍 [World History]" in text
        assert "Great War of Data" in text
        assert "FOUGHT" in text

    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
