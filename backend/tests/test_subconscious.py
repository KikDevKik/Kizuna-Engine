import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.subconscious import SubconsciousMind
from app.models.graph import AgentNode

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
        sent_contents = call_args.kwargs['contents']
        assert "CUSTOM_PROMPT: hello" in sent_contents

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
