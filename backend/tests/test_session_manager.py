import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import WebSocket

from app.services.session_manager import SessionManager
from app.services.sleep_manager import SleepManager
from app.repositories.base import SoulRepository


@pytest.mark.asyncio
async def test_session_manager_reject_origin():
    repo_mock = Mock(spec=SoulRepository)
    sleep_mock = Mock(spec=SleepManager)
    manager = SessionManager(repo_mock, sleep_mock)

    websocket = AsyncMock(spec=WebSocket)
    websocket.headers = {"origin": "http://evil.com"}

    # Mock settings to only allow localhost
    with patch("app.services.session_manager.settings") as settings_mock:
        settings_mock.CORS_ORIGINS = ["http://localhost:5173"]

        await manager.handle_session(websocket, "agent1", None)

        websocket.close.assert_called_with(code=1008)


@pytest.mark.asyncio
async def test_session_manager_reject_no_agent():
    repo_mock = Mock(spec=SoulRepository)
    sleep_mock = Mock(spec=SleepManager)
    manager = SessionManager(repo_mock, sleep_mock)

    websocket = AsyncMock(spec=WebSocket)
    websocket.headers = {"origin": "http://localhost:5173"}

    with patch("app.services.session_manager.settings") as settings_mock:
        settings_mock.CORS_ORIGINS = ["http://localhost:5173"]

        await manager.handle_session(websocket, None, None)

        websocket.close.assert_called_with(code=1008, reason="agent_id required")


@pytest.mark.asyncio
async def test_session_manager_success_flow():
    repo_mock = Mock(spec=SoulRepository)
    repo_mock.get_or_create_user = AsyncMock(return_value=Mock(id="user1"))
    repo_mock.get_agent = AsyncMock(return_value=Mock(voice_name="Puck"))

    sleep_mock = Mock(spec=SleepManager)
    sleep_mock.cancel_sleep = AsyncMock()
    sleep_mock.schedule_sleep = AsyncMock()

    manager = SessionManager(repo_mock, sleep_mock)

    websocket = AsyncMock(spec=WebSocket)
    websocket.headers = {"origin": "http://localhost:5173"}
    websocket.accept = AsyncMock()

    # Mock Gemini Service Context Manager
    mock_session = AsyncMock()

    # Let's mock the internal tasks so we don't need deep mocking of gemini
    with patch("app.services.session_manager.settings") as settings_mock, patch(
        "app.services.session_manager.verify_user_logic"
    ) as verify_mock, patch(
        "app.services.session_manager.cache"
    ) as cache_mock, patch(
        "app.services.session_manager.gemini_service"
    ) as gemini_mock, patch(
        "app.services.session_manager.send_to_gemini", new_callable=AsyncMock
    ) as send_mock, patch(
        "app.services.session_manager.receive_from_gemini", new_callable=AsyncMock
    ) as receive_mock, patch(
        "app.services.session_manager.send_injections_to_gemini",
        new_callable=AsyncMock,
    ), patch(
        "app.services.session_manager.subconscious_mind"
    ):

        settings_mock.CORS_ORIGINS = ["http://localhost:5173"]
        settings_mock.FIREBASE_CREDENTIALS = None
        verify_mock.return_value = "user1"
        cache_mock.get = AsyncMock(return_value="System Prompt")

        # Mock gemini context manager
        gemini_mock.connect.return_value.__aenter__.return_value = mock_session
        gemini_mock.connect.return_value.__aexit__.return_value = None

        # Run session
        await manager.handle_session(websocket, "agent1", "token")

        # Verify flow
        repo_mock.get_or_create_user.assert_called_with("user1")
        sleep_mock.cancel_sleep.assert_called_with("user1")
        websocket.accept.assert_called()
        gemini_mock.connect.assert_called()

        # Verify tasks were started (mocked functions called)
        send_mock.assert_called()
        receive_mock.assert_called()

        # Verify cleanup
        websocket.close.assert_called()
        sleep_mock.schedule_sleep.assert_called_with(
            user_id="user1", agent_id="agent1", raw_transcript=None
        )
