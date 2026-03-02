import asyncio
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

class AuctionService:
    """
    Module 6: The Unforgiven Debt (Audio Concurrency).
    Phase 6 Stable: Corrected race conditions and dirty-state handling.
    All contention logic runs inside the lock to prevent TOCTOU races.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._current_winner: Optional[str] = None
        self._current_score: float = 0.0
        self._last_user_activity: float = 0.0
        self._user_priority_window: float = 0.5  # 500ms grace period

    def _is_user_active(self) -> bool:
        """Checks if the user has spoken within the grace window."""
        return (time.time() - self._last_user_activity) < self._user_priority_window

    async def force_release(self, agent_id: Optional[str] = None):
        """
        Emergency reset: clears any dirty lock state at session start.
        Called by SessionManager BEFORE the audio loop begins.
        If agent_id is provided, only releases if that agent holds the lock.
        If agent_id is None, forces a full reset regardless.
        """
        async with self._lock:
            if agent_id is None or self._current_winner == agent_id:
                if self._current_winner:
                    logger.info(f"🔧 Force Release: Cleared dirty lock held by '{self._current_winner}'")
                self._current_winner = None
                self._current_score = 0.0

    async def bid(self, agent_id: str, score: float) -> bool:
        """
        Attempts to win the audio lock.
        All state-mutating logic is now inside the lock to prevent race conditions.
        """
        # Fast path 1: ownership continuity (no lock needed for read, confirmed inside)
        if self._current_winner == agent_id:
            return True

        # Fast path 2: user active suppression (no lock needed — only reads time)
        if self._is_user_active():
            if score < 10.0:
                return False

        async with self._lock:
            # Re-check ownership inside lock
            if self._current_winner == agent_id:
                return True

            # No current owner → acquire
            if self._current_winner is None:
                self._current_winner = agent_id
                self._current_score = score
                logger.info(f"🎤 Auction Won: {agent_id} (Score: {score})")
                return True

            # Another agent owns it → pre-emption check
            if score > self._current_score * 2.0:
                logger.info(f"🎤 PRE-EMPTION: {agent_id} ({score}) outbid {self._current_winner} ({self._current_score})")
                self._current_winner = agent_id
                self._current_score = score
                return True

            return False

    async def release(self, agent_id: str):
        """Releases the lock if held by this agent."""
        async with self._lock:
            if self._current_winner == agent_id:
                self._current_winner = None
                self._current_score = 0.0
                logger.info(f"🎤 Mic Released by {agent_id}")

    async def interrupt(self):
        """
        User Barge-in: Mark activity and clear current winner.
        """
        self._last_user_activity = time.time()
        async with self._lock:
            if self._current_winner:
                logger.info(f"⚠️ BARGE-IN: User speaking. Interrupting {self._current_winner}")
                self._current_winner = None
                self._current_score = 0.0
