import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.subconscious import SubconsciousMind
from app.models.graph import AgentNode, SystemConfigNode

@pytest.mark.asyncio
async def test_resonance_update_system_default():
    """
    Verifies that resonance is updated based on SystemConfig matrix when Agent has no override.
    """
    service = SubconsciousMind()
    mock_repo = AsyncMock()
    service.set_repository(mock_repo)

    # Mock System Config
    mock_config = SystemConfigNode(
        sentiment_resonance_matrix={"joy": 5.0, "sadness": 2.0}
    )
    mock_repo.get_system_config.return_value = mock_config

    # Mock Agent (No override)
    mock_agent = AgentNode(name="TestAgent", base_instruction="...")
    mock_repo.get_agent.return_value = mock_agent

    # Mock _analyze_sentiment to return "joy"
    # We patch the method on the instance to avoid complex Gemini mocking
    service._analyze_sentiment = AsyncMock(return_value="User is feeling joy.")

    # Mock get_relevant_episodes to return empty
    mock_repo.get_relevant_episodes.return_value = []

    # Queues
    t_queue = asyncio.Queue()
    i_queue = asyncio.Queue()

    # Put data
    await t_queue.put("I am so happy.")

    # Run start loop for a brief moment
    task = asyncio.create_task(service.start(t_queue, i_queue, "user1", "agent1"))

    try:
        # Wait for processing
        await asyncio.sleep(0.5)

        # Verify update_resonance called with 5.0 (joy)
        # hint was "User is feeling joy." -> contains "joy"
        mock_repo.update_resonance.assert_called_with("user1", "agent1", 5.0)

    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

@pytest.mark.asyncio
async def test_resonance_update_agent_override():
    """
    Verifies that Agent override matrix takes precedence.
    """
    service = SubconsciousMind()
    mock_repo = AsyncMock()
    service.set_repository(mock_repo)

    # Mock System Config (Default)
    mock_config = SystemConfigNode(
        sentiment_resonance_matrix={"anger": 0.0}
    )
    mock_repo.get_system_config.return_value = mock_config

    # Mock Agent (With Override: Masochist/Sadist?)
    # Anger gives positive resonance
    mock_agent = AgentNode(
        name="DarkSoul",
        base_instruction="...",
        emotional_resonance_matrix={"anger": 3.0}
    )
    mock_repo.get_agent.return_value = mock_agent

    # Mock _analyze_sentiment
    service._analyze_sentiment = AsyncMock(return_value="User is expressing anger.")
    mock_repo.get_relevant_episodes.return_value = []

    t_queue = asyncio.Queue()
    i_queue = asyncio.Queue()
    await t_queue.put("I hate this!")

    task = asyncio.create_task(service.start(t_queue, i_queue, "user1", "agent1"))

    try:
        await asyncio.sleep(0.5)
        # Verify 3.0 instead of 0.0
        mock_repo.update_resonance.assert_called_with("user1", "agent1", 3.0)
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
