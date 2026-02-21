import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ritual_service import RitualService, RitualMessage, RitualResponse

@pytest.mark.asyncio
async def test_process_ritual_start():
    """Verifies localized greeting when history is empty."""
    service = RitualService()

    # Test English
    resp = await service.process_ritual([], locale="en")
    assert resp.is_complete is False
    assert "The Void gazes back" in resp.message

    # Test Spanish
    resp = await service.process_ritual([], locale="es")
    assert "El Vacío te devuelve la mirada" in resp.message

    # Test Japanese
    resp = await service.process_ritual([], locale="ja")
    assert "虚空が見つめ返している" in resp.message

@pytest.mark.asyncio
async def test_process_ritual_next_question_mock():
    """Verifies fallback sequential questions when Gemini client is absent."""
    service = RitualService()
    service.client = None

    # One user answer
    history = [RitualMessage(role="user", content="I want to create a protector")]
    resp = await service.process_ritual(history)
    assert resp.is_complete is False
    assert resp.message == "What is its primary function or role?" # index 1 % 3

    # Two user answers
    history.append(RitualMessage(role="assistant", content=resp.message))
    history.append(RitualMessage(role="user", content="To guard the gates"))
    resp = await service.process_ritual(history)
    assert resp.is_complete is False
    assert resp.message == "What languages does its mind command?" # index 2 % 3

@pytest.mark.asyncio
async def test_process_ritual_next_question_gemini_success():
    """Verifies that Gemini is called and its response is used for the next question."""
    service = RitualService()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    mock_response = MagicMock()
    mock_response.text = "What is your name, traveler?"
    service.client.aio.models.generate_content.return_value = mock_response

    history = [RitualMessage(role="user", content="Hello")]
    resp = await service.process_ritual(history)

    assert resp.is_complete is False
    assert resp.message == "What is your name, traveler?"
    service.client.aio.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_process_ritual_next_question_gemini_failure():
    """Verifies fallback message when Gemini generation fails."""
    service = RitualService()
    service.client = MagicMock()

    with patch.object(RitualService, '_generate_with_retry', return_value=None):
        history = [RitualMessage(role="user", content="Hello")]
        resp = await service.process_ritual(history)

        assert resp.is_complete is False
        assert resp.message == "The connection flickers. Tell me more of your intent."

@pytest.mark.asyncio
async def test_process_ritual_finalize_mock():
    """Verifies that the failsafe agent is returned when no Gemini client is available at finalization."""
    service = RitualService()
    service.client = None

    history = [
        RitualMessage(role="user", content="Ares"),
        RitualMessage(role="user", content="Warrior"),
        RitualMessage(role="user", content="Greek")
    ]

    resp = await service.process_ritual(history)
    assert resp.is_complete is True
    assert resp.agent_data["name"] == "KIZUNA-FAILSAFE"

@pytest.mark.asyncio
async def test_process_ritual_finalize_gemini_success():
    """Verifies that Gemini generates the agent JSON and it is correctly parsed with defaults."""
    service = RitualService()
    service.client = MagicMock()

    generated_json = {
        "name": "Custom Soul",
        "role": "Guardian",
        "base_instruction": "You protect.",
        "lore": "From the mountains.",
        "traits": ["Strong"],
        "native_language": "Common",
        "known_languages": ["Common"]
    }

    # Test handling of markdown code blocks
    mock_text = f"```json\n{json.dumps(generated_json)}\n```"

    with patch.object(RitualService, '_generate_with_retry', return_value=mock_text):
        history = [
            RitualMessage(role="user", content="A"),
            RitualMessage(role="user", content="B"),
            RitualMessage(role="user", content="C")
        ]
        resp = await service.process_ritual(history)

        assert resp.is_complete is True
        assert resp.agent_data["name"] == "Custom Soul"
        assert resp.agent_data["role"] == "Guardian"

@pytest.mark.asyncio
async def test_generate_with_retry_429():
    """Verifies the retry mechanism specifically for 429 Rate Limit errors."""
    service = RitualService()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # First call raises 429 error
    error_429 = Exception("Resource has been exhausted (e.g. check quota). 429 Rate Limit")

    mock_response = MagicMock()
    mock_response.text = "Success after retry"

    service.client.aio.models.generate_content.side_effect = [error_429, mock_response]

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        result = await service._generate_with_retry("model", "contents")

        assert result == "Success after retry"
        assert service.client.aio.models.generate_content.call_count == 2
        mock_sleep.assert_called_once_with(4)

@pytest.mark.asyncio
async def test_generate_with_retry_failure():
    """Verifies that if the retry also fails (e.g., second 429), it returns None."""
    service = RitualService()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Both calls raise 429 error
    error_429 = Exception("Resource has been exhausted (e.g. check quota). 429 Rate Limit")
    service.client.aio.models.generate_content.side_effect = [error_429, error_429]

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        result = await service._generate_with_retry("model", "contents")

        assert result is None
        assert service.client.aio.models.generate_content.call_count == 2
        mock_sleep.assert_called_once_with(4)

@pytest.mark.asyncio
async def test_generate_with_retry_non_429():
    """Verifies that a non-429 error (e.g., 500) returns None immediately without sleeping/retrying."""
    service = RitualService()
    service.client = MagicMock()
    service.client.aio.models.generate_content = AsyncMock()

    # Call raises 500 error
    error_500 = Exception("Internal Server Error")
    service.client.aio.models.generate_content.side_effect = error_500

    with patch("asyncio.sleep", AsyncMock()) as mock_sleep:
        result = await service._generate_with_retry("model", "contents")

        assert result is None
        assert service.client.aio.models.generate_content.call_count == 1
        mock_sleep.assert_not_called()

@pytest.mark.asyncio
async def test_generate_with_retry_no_client():
    """Verifies that if self.client is None, it returns None."""
    service = RitualService()
    service.client = None

    result = await service._generate_with_retry("model", "contents")
    assert result is None
