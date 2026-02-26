import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.agent_service import AgentService, HollowAgentProfile, GeneratedMemory
from app.models.graph import AgentNode, MemoryEpisodeNode

@pytest.mark.asyncio
async def test_forge_hollow_agent():
    # Mock the Gemini Client and response
    mock_client = MagicMock()
    mock_response = MagicMock()

    # Mock the parsed response (HollowAgentProfile)
    mock_profile = HollowAgentProfile(
        name="Test Stranger",
        backstory="A test backstory.",
        traits={"brave": "true"},
        voice_name="Aoede",
        false_memories=[
            GeneratedMemory(summary="Memory 1", emotional_valence=-0.5),
            GeneratedMemory(summary="Memory 2", emotional_valence=0.8)
        ]
    )
    mock_response.parsed = mock_profile

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
    assert memories[0].emotional_valence == -0.5

    # Verify Gemini call
    mock_client.aio.models.generate_content.assert_called_once()
    args, kwargs = mock_client.aio.models.generate_content.call_args
    # Check if passed as arg or kwarg
    prompt_content = kwargs.get('contents')
    if not prompt_content and args:
        # Check args if kwargs failed
        # Arg 0 is model, Arg 1 is contents
        if len(args) > 1:
            prompt_content = args[1]

    assert prompt_content is not None
    assert "Cyberpunk ninja" in prompt_content
