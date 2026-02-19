import asyncio
import logging
import base64
import json
from unittest.mock import AsyncMock, MagicMock
from asyncio import Queue

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import classes to test (simulate importing from app)
# Note: This requires the backend code to be importable
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.subconscious import SubconsciousMind
from app.services.audio_session import send_injections_to_gemini

async def test_subconscious_flow():
    print("🧠 Starting Subconscious Integration Test...")

    # 1. Setup Queues
    transcript_queue = Queue()
    injection_queue = Queue()

    # 2. Setup Mock Session
    mock_session = AsyncMock()
    mock_session.send = AsyncMock()

    # 3. Setup Subconscious Mind
    mind = SubconsciousMind()

    # 4. Create Tasks
    # Task A: Subconscious Mind
    mind_task = asyncio.create_task(mind.start(transcript_queue, injection_queue))

    # Task B: Injection Sender
    injection_task = asyncio.create_task(send_injections_to_gemini(mock_session, injection_queue))

    # 5. Simulate Gemini Input (Transcripts)
    print("🗣️  Simulating user speech...")
    # "I am so sad" triggers the "sad" logic in SubconsciousMind
    await transcript_queue.put("I am feeling really")
    await asyncio.sleep(0.1)
    await transcript_queue.put(" sad today.")

    # Give it a moment to process
    print("⏳ Waiting for processing...")
    await asyncio.sleep(0.5)

    # 6. Verify Injection
    # Check if mock_session.send was called with the expected hint
    try:
        # We expect a call to session.send(input="...", end_of_turn=False)
        # The exact text depends on the SubconsciousMind logic
        expected_hint = "SYSTEM_HINT: The user seems down. Be extra gentle and supportive."

        # Get all calls to send
        calls = mock_session.send.call_args_list
        found = False
        for call in calls:
            args, kwargs = call
            input_text = kwargs.get('input', '')
            end_of_turn = kwargs.get('end_of_turn', True)

            print(f"🔍 Call detected: input='{input_text}', end_of_turn={end_of_turn}")

            if expected_hint in input_text and end_of_turn is False:
                found = True
                break

        if found:
            print("✅ SUCCESS: Subconscious hint injected correctly!")
        else:
            print("❌ FAILURE: Expected hint not found in session calls.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        mind_task.cancel()
        injection_task.cancel()
        try:
            await mind_task
            await injection_task
        except asyncio.CancelledError:
            pass
        print("🏁 Test Complete.")

if __name__ == "__main__":
    asyncio.run(test_subconscious_flow())
