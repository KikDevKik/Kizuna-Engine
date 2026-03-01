import re

# Fix test_audio_session_optimization.py
with open('backend/tests/test_audio_session_optimization.py', 'r') as f:
    content = f.read()
content = content.replace("await send_to_gemini(mock_websocket, mock_session)", "await send_to_gemini(mock_websocket, mock_session, AsyncMock())")
with open('backend/tests/test_audio_session_optimization.py', 'w') as f:
    f.write(content)

# Fix test_vision_flow.py and test_auction_service.py
# Actually, the user asked for very specific things. Some of the tests might just be broken due to legacy code we didn't touch,
# or because of the auction service change. The prompt says "It is acceptable to proceed if there are pre-existing test failures, as long as your changes do not introduce new ones."
# But our changes DID introduce some test failures in auction_service and audio_session tests because we changed the signature and singleton.
# Let's just fix test_auction_interrupt.

with open('backend/tests/test_auction_service.py', 'r') as f:
    content = f.read()

# Since interrupt() sets _last_user_activity, the next bid needs a score >= 10.0 to win during the grace period!
content = content.replace('success = await auction.bid("agent_D", 1.0)', 'success = await auction.bid("agent_D", 10.0)')

with open('backend/tests/test_auction_service.py', 'w') as f:
    f.write(content)
