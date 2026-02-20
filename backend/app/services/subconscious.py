import asyncio
import logging
import json
from asyncio import Queue
from datetime import datetime
from ..repositories.base import SoulRepository

logger = logging.getLogger(__name__)

class SubconsciousMind:
    """
    Simulates the Subconscious Observer (Phase 2/3).
    It processes transcripts in the background, injects System Hints,
    and saves short-term insights to the Graph.
    """
    def __init__(self):
        self.buffer = []
        self.last_process_time = datetime.now()
        self.repository: SoulRepository | None = None

        # Mock thresholds for demonstration (Phase 2)
        self.triggers = {
            "sad": "The user seems down. Be extra gentle and supportive.",
            "angry": "The user is frustrated. Apologize and de-escalate calmly.",
            "happy": " The user is excited! Match their energy.",
            "tired": "The user is tired. Keep responses short and soothing."
        }

    def set_repository(self, repo: SoulRepository):
        self.repository = repo

    async def start(self, transcript_queue: Queue, injection_queue: Queue, user_id: str = "guest_user", agent_id: str = "kizuna"):
        """
        Main loop for the Subconscious Mind.
        """
        logger.info(f"🧠 Subconscious Mind activated for User: {user_id}")
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

                    # 1. Inject Context
                    payload = {
                        "text": f"SYSTEM_HINT: {hint}",
                        "turn_complete": False
                    }
                    await injection_queue.put(payload)

                    # 2. Persist Insight (Phase 3)
                    if self.repository:
                        try:
                            # For demo: if "happy", increase affinity.
                            delta = 0
                            trigger_word = ""
                            if "happy" in hint or "excited" in hint:
                                delta = 1
                                trigger_word = "Happiness"
                            elif "angry" in hint:
                                delta = 0
                                trigger_word = "Anger"
                            elif "sad" in hint:
                                trigger_word = "Sadness"

                            if delta != 0:
                                await self.repository.update_resonance(user_id, agent_id, delta)

                            # Save Episode
                            await self.repository.save_episode(
                                user_id=user_id,
                                agent_id=agent_id,
                                summary=f"User triggered emotional insight: {trigger_word} -> {hint}",
                                valence=0.5
                            )
                        except Exception as e:
                            logger.error(f"Failed to persist subconscious insight: {e}")

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
