import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.subconscious import SubconsciousMind
from app.models.graph import DreamNode, MemoryEpisodeNode

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
