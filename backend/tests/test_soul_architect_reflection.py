import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.reflection import ReflectionMind
from app.models.graph import AgentNode, SystemConfigNode

@pytest.mark.asyncio
async def test_reflection_uses_custom_prompt():
    """
    Verifies that ReflectionMind uses the prompt from AgentNode.
    """
    service = ReflectionMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Mock response
    mock_resp = MagicMock()
    mock_resp.text = "Correction needed."
    service.client.aio.models.generate_content.return_value = mock_resp

    # Agent with custom prompt
    custom_prompt = "CUSTOM_REFLECTION_PROMPT: {name}"
    agent = AgentNode(
        name="Mirror",
        base_instruction="...",
        reflection_prompt=custom_prompt
    )

    with patch("app.services.reflection.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False
        mock_settings.MODEL_SUBCONSCIOUS = ["gemini-test"]

        await service._reflect("I am speaking.", agent)

        # Verify call arguments
        call_args = service.client.aio.models.generate_content.call_args
        assert call_args is not None

        config = call_args.kwargs['config']

        # Check system_instruction
        # If running with real genai installed, config is a Pydantic-like object (types.GenerateContentConfig)
        # If running without, it might be different, but here we assume real types are used if imported.

        # We handle potential attribute access issues defensively or assume standard structure
        try:
            # Try getting text from parts
            text_part = config.system_instruction.parts[0].text
        except AttributeError:
             # Fallback if structure is different
             text_part = str(config)

        # Should contain formatted prompt
        assert "CUSTOM_REFLECTION_PROMPT: Mirror" in text_part

@pytest.mark.asyncio
async def test_reflection_throttling_config():
    """
    Verifies that start() fetches throttling params from SystemConfig.
    """
    service = ReflectionMind()
    mock_repo = AsyncMock()
    service.set_repository(mock_repo)

    # Config with 100% chance (base=1.0)
    mock_config = SystemConfigNode(
        reflection_base_chance=1.0,
        reflection_neuroticism_multiplier=0.0
    )
    mock_repo.get_system_config.return_value = mock_config

    agent = AgentNode(name="Test", base_instruction="...", traits={"neuroticism": 0.0})

    # Queues
    ai_q = asyncio.Queue()
    inj_q = asyncio.Queue()

    # Mock _reflect to avoid API call
    service._reflect = AsyncMock(return_value="Self-Correction")

    # Inject one item
    await ai_q.put("I am talking.")

    # Start task
    task = asyncio.create_task(service.start(ai_q, inj_q, agent))

    try:
        await asyncio.sleep(0.5)

        # Verify _reflect was called (because probability is 1.0)
        service._reflect.assert_called()

        # Verify injection
        payload = await inj_q.get()
        assert "Self-Correction" in payload["text"]

    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
