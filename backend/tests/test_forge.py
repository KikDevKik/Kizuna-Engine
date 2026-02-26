import pytest
from unittest.mock import AsyncMock, MagicMock
import json
import sys
import os

# Ensure backend is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.agent_service import AgentService, HollowAgentProfile, GeneratedMemory
from app.models.graph import AgentNode, MemoryEpisodeNode

@pytest.mark.asyncio
async def test_forge_hollow_agent():
    # Mock the Gemini Client and response
    mock_client = MagicMock()
    mock_response = MagicMock()

    # Create profile data matching new schema
    profile_data = {
        "name": "Test Stranger",
        "backstory": "A test backstory.",
        "traits": {"brave": "true"},
        "voice_name": "Aoede",
        "false_memories": [
            {"memory_text": "Memory 1", "importance": 0.5},
            {"memory_text": "Memory 2", "importance": 0.8}
        ]
    }

    mock_response.text = json.dumps(profile_data)

    # Setup async generate_content
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    # Initialize service with mock client
    service = AgentService()
    service.client = mock_client

    # Execute
    agent, memories = await service.forge_hollow_agent("Cyberpunk ninja")

    # Verify
    assert agent.name == "Test Stranger"
    assert agent.role == "Stranger"
    assert agent.base_instruction == "A test backstory."
    assert agent.voice_name == "Aoede"
    assert len(memories) == 2
    assert memories[0].summary == "Memory 1"
    assert memories[0].emotional_valence == 0.5

    # Verify Gemini call
    mock_client.aio.models.generate_content.assert_called_once()
    args, kwargs = mock_client.aio.models.generate_content.call_args

    contents = kwargs.get('contents')
    # If not in kwargs, might be in args.
    # generate_content(model, contents, config=...)
    if not contents and len(args) > 1:
        contents = args[1]

    assert contents is not None
    assert "Cyberpunk ninja" in str(contents)
