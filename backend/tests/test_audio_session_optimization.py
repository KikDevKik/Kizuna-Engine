
import sys
import asyncio
import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Mock dependencies that might be missing in the environment
mock_fastapi = MagicMock()
sys.modules["fastapi"] = mock_fastapi

# Now import the function to test
# We need to set PYTHONPATH=backend so it finds 'app'
try:
    from app.services.audio_session import send_to_gemini
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

import pytest

@pytest.mark.asyncio
async def test_send_to_gemini_image_offloading():
    # Mock WebSocket
    mock_websocket = AsyncMock()

    # Simulate an image message
    test_image_data = b"fake-image-data-to-decode"
    b64_image = base64.b64encode(test_image_data).decode('ascii')
    payload = {
        "type": "image",
        "data": b64_image
    }

    # We need to simulate WebSocketDisconnect.
    class FakeDisconnect(Exception):
        pass

    with patch("app.services.audio_session.WebSocketDisconnect", FakeDisconnect):
        # WebSocket.receive should return our payload and then raise FakeDisconnect to stop the loop
        mock_websocket.receive.side_effect = [
            {"text": json.dumps(payload)},
            FakeDisconnect()
        ]

        # Mock Session
        mock_session = AsyncMock()

        # Run the function. It should eventually raise FakeDisconnect.
        try:
            await send_to_gemini(mock_websocket, mock_session)
        except FakeDisconnect:
            pass
        except Exception as e:
            print(f"Caught unexpected exception: {type(e).__name__}: {e}")
            raise

        # Verify session.send was called with decoded bytes
        # Since we upgraded to use google.genai.types.Content, we need to check flexibly
        call_args = mock_session.send.call_args
        if call_args:
            input_arg = call_args.kwargs.get('input')
            if isinstance(input_arg, dict):
                 assert input_arg == {"data": test_image_data, "mime_type": "image/jpeg"}
            else:
                 # Assume it's a Content object (we can't easily import types here without potentially failing if not installed)
                 # Check if the blob data inside matches
                 # Content -> parts[0] -> inline_data -> data
                 assert input_arg.parts[0].inline_data.data == test_image_data
                 assert input_arg.parts[0].inline_data.mime_type == "image/jpeg"
        else:
             raise AssertionError("session.send was not called")

        print("✅ Verification test passed: Image sent successfully (Typed or Dict).")

if __name__ == "__main__":
    asyncio.run(test_send_to_gemini_image_offloading())
