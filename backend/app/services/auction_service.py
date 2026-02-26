import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class AuctionService:
    """
    Module 6: The Unforgiven Debt (Audio Concurrency).
    Updated with Solution B: Priority Thresholding & Silence Watchdog.
    Prevents deadlocks where agents never speak due to VAD jitter.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuctionService, cls).__new__(cls)
            cls._instance._lock = asyncio.Lock()
            cls._instance._current_winner: Optional[str] = None
            cls._instance._current_score: float = 0.0
            cls._instance._last_user_activity: float = 0.0
            cls._instance._user_priority_window: float = 0.5  # 500ms grace period
        return cls._instance

    def _is_user_active(self) -> bool:
        """Checks if the user has spoken within the grace window."""
        return (time.time() - self._last_user_activity) < self._user_priority_window

    async def bid(self, agent_id: str, score: float) -> bool:
        """
        Attempts to win the audio lock with priority thresholding.
        """
        # 1. User Priority Check (Solution B Watchdog)
        if self._is_user_active():
            # If user is active, only a massive score (e.g. 10.0+) can break through.
            # Default bids (1.0) are suppressed during user speech.
            if score < 10.0:
                return False

        # 2. Ownership Continuity
        if self._current_winner == agent_id:
            return True

        # 3. Competition & Pre-emption
        # If someone else is speaking, can I outbid them?
        # Requirement: Score must be significantly higher to interrupt another agent.
        if self._current_winner is not None:
            if score > self._current_score * 2.0:
                logger.info(f"🎤 PRE-EMPTION: {agent_id} ({score}) outbid {self._current_winner} ({self._current_score})")
                self._current_winner = agent_id
                self._current_score = score
                return True
            return False

        # 4. Acquisition
        async with self._lock:
            # Final check inside lock
            if self._current_winner is None:
                self._current_winner = agent_id
                self._current_score = score
                logger.info(f"🎤 Auction Won: {agent_id} (Score: {score})")
                return True
            return False

    async def release(self, agent_id: str):
        """Releases the lock."""
        if self._current_winner == agent_id:
            self._current_winner = None
            self._current_score = 0.0
            logger.info(f"🎤 Mic Released by {agent_id}")

    async def interrupt(self):
        """
        User Barge-in: Mark activity and clear current winner.
        """
        self._last_user_activity = time.time()
        if self._current_winner:
            logger.info(f"⚠️ BARGE-IN: User speaking. Interrupting {self._current_winner}")
            self._current_winner = None
            self._current_score = 0.0

# Singleton Instance
auction_service = AuctionService()
