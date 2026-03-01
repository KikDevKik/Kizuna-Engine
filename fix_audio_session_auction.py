with open('backend/app/services/audio_session.py', 'r') as f:
    content = f.read()

# 1. Update send_to_gemini signature
content = content.replace("async def send_to_gemini(websocket: WebSocket, session, transcript_buffer: list[str] | None = None, transcript_queue: asyncio.Queue | None = None):", "async def send_to_gemini(websocket: WebSocket, session, auction_service, transcript_buffer: list[str] | None = None, transcript_queue: asyncio.Queue | None = None):")

# 2. Update receive_from_gemini signature
content = content.replace("async def receive_from_gemini(\n    websocket: WebSocket,\n    session,", "async def receive_from_gemini(\n    websocket: WebSocket,\n    session,\n    auction_service,")

# 3. Remove global auction_service import from audio_session.py
import re
content = re.sub(r"from \.auction_service import auction_service\n", "", content)

with open('backend/app/services/audio_session.py', 'w') as f:
    f.write(content)
