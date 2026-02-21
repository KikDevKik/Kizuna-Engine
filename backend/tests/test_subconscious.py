
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.subconscious import SubconsciousMind
from app.models.graph import AgentNode, DreamNode, MemoryEpisodeNode

# ---------------------------------------------------------
# TESTS PARA: _analyze_sentiment
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_sentiment_mock_mode_fallback():
    """
    Verifies that when MOCK_GEMINI is True, the system falls back to keyword matching
    regardless of whether a client is present.
    """
    service = SubconsciousMind()
    # Ensure client is "present" to prove we skip it due to mock_mode
    service.client = MagicMock()

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = True

        # Text containing a default trigger "sad" -> "The user seems down..."
        text = "I am feeling very sad today."

        hint = await service._analyze_sentiment(text)

        # Should return the default trigger hint for "sad"
        assert hint == "The user seems down. Be extra gentle and supportive."

        # Verify that client was NOT called
        service.client.aio.models.generate_content.assert_not_called()

@pytest.mark.asyncio
async def test_analyze_sentiment_gemini_success():
    """
    Verifies that when MOCK_GEMINI is False and Gemini returns a valid hint,
    it is returned correctly.
    """
    service = SubconsciousMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Mock successful response
    mock_response = MagicMock()
    mock_response.text = "SYSTEM_HINT: User is happy."
    service.client.aio.models.generate_content.return_value = mock_response

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False
        mock_settings.MODEL_SUBCONSCIOUS = "gemini-test"

        text = "I am so happy!"
        hint = await service._analyze_sentiment(text)

        assert hint == "User is happy."
        service.client.aio.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_sentiment_gemini_exception_fallback():
    """
    Verifies that when Gemini raises an exception,
    the system falls back to keyword matching.
    """
    service = SubconsciousMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Mock Exception
    service.client.aio.models.generate_content.side_effect = Exception("API connection failed")

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False
        mock_settings.MODEL_SUBCONSCIOUS = "gemini-test"

        # Text with a keyword trigger "angry"
        text = "I am so angry right now!"

        hint = await service._analyze_sentiment(text)

        # Should fall back to "angry" trigger
        assert hint == "The user is frustrated. Apologize and de-escalate calmly."

@pytest.mark.asyncio
async def test_analyze_sentiment_gemini_no_hint_returns_none():
    """
    Verifies that when Gemini returns a response without the hint prefix,
    it returns None (trusting Gemini's judgement) rather than falling back.
    """
    service = SubconsciousMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Mock response without "SYSTEM_HINT:"
    mock_response = MagicMock()
    mock_response.text = "Just a neutral observation."
    service.client.aio.models.generate_content.return_value = mock_response

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False
        mock_settings.MODEL_SUBCONSCIOUS = "gemini-test"

        # Text with a keyword trigger "sad"
        text = "I am feeling very sad today."

        hint = await service._analyze_sentiment(text)

        # Should NOT fallback, because Gemini didn't fail, it just didn't see a hint.
        assert hint is None

@pytest.mark.asyncio
async def test_analyze_sentiment_custom_agent_prompt():
    """
    Verifies that if an agent is provided with a custom prompt,
    it is used in the Gemini call.
    """
    service = SubconsciousMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()
    mock_response = MagicMock()
    mock_response.text = "SYSTEM_HINT: Custom."
    service.client.aio.models.generate_content.return_value = mock_response

    # Mock Repository and Agent
    mock_repo = AsyncMock()
    service.set_repository(mock_repo)

    custom_agent = AgentNode(
        name="TestAgent",
        base_instruction="Test",
        memory_extraction_prompt="CUSTOM_PROMPT: {text}"
    )
    mock_repo.get_agent.return_value = custom_agent

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False
        mock_settings.MODEL_SUBCONSCIOUS = "gemini-test"

        await service._analyze_sentiment("hello", agent_id="agent-123")

        # Verify the prompt sent contained the custom prompt text
        call_args = service.client.aio.models.generate_content.call_args
        assert call_args is not None

        # Check system_instruction in config
        config = call_args.kwargs['config']
        system_instruction_part = config.system_instruction.parts[0].text
        # The code replaces {text} with [TRANSCRIPT] in the system instruction
        # prompt_template = "CUSTOM_PROMPT: {text}" -> "CUSTOM_PROMPT: [TRANSCRIPT]"
        assert "CUSTOM_PROMPT: [TRANSCRIPT]" in system_instruction_part

@pytest.mark.asyncio
async def test_analyze_sentiment_network_error():
    """
    Verifies that network errors (httpx) are caught gracefully and return None.
    """
    service = SubconsciousMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Simulate Network Error
    import httpx
    service.client.aio.models.generate_content.side_effect = httpx.ConnectError("Connection failed")

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False

        result = await service._analyze_sentiment("hello")

        assert result is None
        # Ensure it didn't crash

@pytest.mark.asyncio
async def test_analyze_sentiment_agent_traits_fallback():
    """
    Verifies that fallback logic uses agent traits if provided.
    """
    service = SubconsciousMind()
    service.client = MagicMock()
    # Force fallback by making Gemini return None/Exception or just not match prefix
    service.client.aio.models.generate_content = AsyncMock(side_effect=Exception("API Error"))

    mock_repo = AsyncMock()
    service.set_repository(mock_repo)

    custom_traits = {
        "emotional_triggers": {
            "joy": "Agent is jumping with joy.",
            "glum": "Agent offers chocolate."
        }
    }

    custom_agent = AgentNode(
        name="TestAgent",
        base_instruction="Test",
        traits=custom_traits
    )
    mock_repo.get_agent.return_value = custom_agent

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False

        # Text containing "joy"
        text = "I feel such joy!"

        hint = await service._analyze_sentiment(text, agent_id="agent-123")

        assert hint == "Agent is jumping with joy."


# ---------------------------------------------------------
# TESTS PARA: generate_dream
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_dream_no_episodes():
    """Verifies that generate_dream returns a Void dream when no episodes are provided."""
    service = SubconsciousMind()
    dream = await service.generate_dream([])

    assert dream.theme == "Void"
    assert dream.intensity == 0.0
    assert dream.surrealism_level == 0.0

@pytest.mark.asyncio
async def test_generate_dream_happy_path():
    """Verifies that generate_dream correctly parses a valid JSON response from GenAI."""
    service = SubconsciousMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Mock valid JSON response
    mock_data = {
        "theme": "Flying over mountains",
        "intensity": 0.8,
        "surrealism_level": 0.9
    }
    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(mock_data)}\n```"
    service.client.aio.models.generate_content.return_value = mock_response

    episodes = [
        MemoryEpisodeNode(summary="Walked in the park", emotional_valence=0.5),
        MemoryEpisodeNode(summary="Saw a bird", emotional_valence=0.7)
    ]

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False
        mock_settings.MODEL_DREAM = "gemini-2.0-flash-exp" # Ensure model is set

        dream = await service.generate_dream(episodes)

        assert dream.theme == "Flying over mountains"
        assert dream.intensity == 0.8
        assert dream.surrealism_level == 0.9
        service.client.aio.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_generate_dream_malformed_json():
    """Verifies fallback to default dream values when JSON parsing fails."""
    service = SubconsciousMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Mock invalid JSON response
    mock_response = MagicMock()
    mock_response.text = "This is not JSON, it is just text."
    service.client.aio.models.generate_content.return_value = mock_response

    episodes = [
        MemoryEpisodeNode(summary="A stressful day", emotional_valence=-0.2)
    ]

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False
        mock_settings.MODEL_DREAM = "gemini-2.0-flash-exp"

        dream = await service.generate_dream(episodes)

# Should fall back to defaults defined in the method
        assert dream.theme == "Reflection"
        assert dream.intensity == 0.5
        assert dream.surrealism_level == 0.3

@pytest.mark.asyncio
async def test_generate_dream_empty_response():
    """Verifies that an empty or None response results in a Void dream."""
    service = SubconsciousMind()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Mock empty response
    mock_response = MagicMock()
    mock_response.text = None
    service.client.aio.models.generate_content.return_value = mock_response

    episodes = [
        MemoryEpisodeNode(summary="Coding late at night", emotional_valence=0.1)
    ]

    with patch("app.services.subconscious.settings") as mock_settings:
        mock_settings.MOCK_GEMINI = False
        mock_settings.MODEL_DREAM = "gemini-2.0-flash-exp"

        dream = await service.generate_dream(episodes)

        assert dream.theme == "Void"
        assert dream.intensity == 0.0
        assert dream.surrealism_level == 0.0

@pytest.mark.asyncio
async def test_subconscious_start_resilience():
    """Verifies that the start loop recovers from an unexpected error in one iteration."""
    service = SubconsciousMind()
    transcript_queue = asyncio.Queue()
    injection_queue = asyncio.Queue()

    # Mock _analyze_sentiment to raise an exception on the first call, then succeed
    with patch.object(service, "_analyze_sentiment", side_effect=[Exception("Boom!"), "Happy Hint"]):
        # Start the loop in a task
        task = asyncio.create_task(service.start(transcript_queue, injection_queue, "test_user", "test_agent"))

        # We need to trigger the logic.
        await transcript_queue.put("segment 1.") # triggers 1st call -> Exception

        # We need to wait a bit for the 1s sleep in the error handler
        await asyncio.sleep(1.1)

        await transcript_queue.put("segment 2.") # triggers 2nd call -> "Happy Hint"

        try:
            # Wait for the injection queue to get the "Happy Hint"
            hint_payload = await asyncio.wait_for(injection_queue.get(), timeout=2.0)
            assert hint_payload["text"] == "SYSTEM_HINT: Happy Hint"
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass