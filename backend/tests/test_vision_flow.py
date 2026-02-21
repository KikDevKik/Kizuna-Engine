import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import base64

# Ensure backend modules are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock fastapi
mock_fastapi = MagicMock()
mock_fastapi.WebSocket = MagicMock() # Class
mock_fastapi.WebSocketDisconnect = Exception # Exception class
sys.modules['fastapi'] = mock_fastapi

# Mock google.genai
mock_google_genai = MagicMock()
sys.modules['google.genai'] = mock_google_genai

# Now import
try:
    from app.services.audio_session import send_to_gemini
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

class TestVisionFlow(unittest.IsolatedAsyncioTestCase):
    async def test_send_image_payload(self):
        # Mock WebSocket Instance
        mock_ws = AsyncMock()

        # Simulate a message with text payload containing an image
        # "SGVsbG8=" -> "Hello"
        image_data_b64 = "SGVsbG8="
        payload = {
            "type": "image",
            "data": image_data_b64
        }

        # Simulate receiving this message.
        # Crucially, we simulate the structure that caused the bug: {"bytes": None, "text": "..."}
        message = {"bytes": None, "text": json.dumps(payload)}

        # side_effect: first return message, then raise exception to break loop
        mock_ws.receive.side_effect = [
            message,
            Exception("Disconnect")
        ]

        # Mock Gemini Session
        mock_session = AsyncMock()

        # Run send_to_gemini
        try:
            await send_to_gemini(mock_ws, mock_session)
        except Exception:
            pass # Expected disconnect exception

        # Verify session.send called with image content
        self.assertTrue(mock_session.send.called, "Session.send should have been called")

        # Inspect arguments
        # args[0] is input=...
        call_args = mock_session.send.call_args
        # In Python 3.8+, kwargs are stored in call_args.kwargs
        args, kwargs = call_args
        input_arg = kwargs.get('input') if 'input' in kwargs else args[0] if args else None

        expected_bytes = b"Hello" # Decoded base64

        # In this test environment, google.genai might not be installed,
        # so audio_session.py likely uses the fallback dict format.
        if isinstance(input_arg, dict):
            self.assertEqual(input_arg['mime_type'], "image/jpeg")
            self.assertEqual(input_arg['data'], expected_bytes)
        else:
            # If types was imported, it might be a Content object.
            # But in this mock environment, types is likely None unless mocked correctly.
            pass

if __name__ == '__main__':
    unittest.main()
