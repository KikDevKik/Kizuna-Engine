import asyncio
import logging
import json
from asyncio import Queue
from datetime import datetime

logger = logging.getLogger(__name__)

class SubconsciousMind:
    """
    Simulates the Subconscious Observer (Phase 2).
    It processes transcripts in the background and injects System Hints.
    """
    def __init__(self):
        self.buffer = []
        self.last_process_time = datetime.now()
        # Mock thresholds for demonstration (Phase 2)
        # In Phase 3+, this would call a real LLM (Gemini Flash).
        self.triggers = {
            "sad": "The user seems down. Be extra gentle and supportive.",
            "angry": "The user is frustrated. Apologize and de-escalate calmly.",
            "happy": " The user is excited! Match their energy.",
            "tired": "The user is tired. Keep responses short and soothing."
        }

    async def start(self, transcript_queue: Queue, injection_queue: Queue):
        """
        Main loop for the Subconscious Mind.
        """
        logger.info("🧠 Subconscious Mind activated.")
        try:
            while True:
                # Wait for transcript segment
                text_segment = await transcript_queue.get()

                if not text_segment:
                    continue

                self.buffer.append(text_segment)

                # Simple logic: Check buffer for keywords every time (or batch)
                # For demo purposes, we check immediately.
                full_text = " ".join(self.buffer).lower()

                # Analyze (Mock Logic)
                hint = self._analyze_sentiment(full_text)

                if hint:
                    logger.info(f"🧠 Insight detected: {hint}")
                    # Construct System Hint Payload
                    # This format matches the 'clientContent' expectation for Gemini Live
                    # We send a tuple or dict that the injection sender understands
                    payload = {
                        "text": f"SYSTEM_HINT: {hint}",
                        "turn_complete": False
                    }
                    await injection_queue.put(payload)
                    # Clear buffer after successful insight to avoid repetition
                    self.buffer = []

                # Keep buffer manageable
                if len(self.buffer) > 20:
                    self.buffer.pop(0)

        except asyncio.CancelledError:
            logger.info("🧠 Subconscious Mind deactivated.")
            raise
        except Exception as e:
            logger.error(f"🧠 Subconscious Error: {e}")
            # Don't crash the whole app, just log
            pass

    def _analyze_sentiment(self, text: str) -> str | None:
        """
        Mock implementation of sentiment analysis.
        In production, this calls Gemini 2.5 Flash.
        """
        for trigger, hint in self.triggers.items():
            if trigger in text:
                return hint
        return None

subconscious_mind = SubconsciousMind()
