import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AuctionService:
    """
    Module 6: The Unforgiven Debt (Audio Concurrency).
    Manages the 'Acoustic Lock' to prevent multiple agents from speaking simultaneously.
    Implements a bidding system where agents compete for the microphone.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuctionService, cls).__new__(cls)
            cls._instance._lock = asyncio.Lock()
            cls._instance._current_winner: Optional[str] = None
            cls._instance._current_score: float = 0.0
        return cls._instance

    async def bid(self, agent_id: str, score: float) -> bool:
        """
        Attempts to win the audio lock.

        Args:
            agent_id (str): The ID of the agent requesting the mic.
            score (float): The 'bid' (e.g., Anxiety or Friction level).

        Returns:
            bool: True if the agent won the lock, False otherwise.
        """
        # If I already own it, keep it.
        if self._current_winner == agent_id:
            return True

        # If locked by someone else, I lose.
        # Future: Implement pre-emption if score > _current_score * 1.5?
        if self._current_winner is not None:
            logger.debug(f"Auction Lost: {agent_id} ({score}) vs Winner {self._current_winner} ({self._current_score})")
            return False

        # Try to acquire the lock
        # We use a non-blocking check first to avoid waiting
        if self._lock.locked():
             return False

        async with self._lock:
            # Double check inside lock
            if self._current_winner is None:
                self._current_winner = agent_id
                self._current_score = score
                logger.info(f"🎤 Auction Won: {agent_id} took the mic (Score: {score})")
                return True
            else:
                return False

    async def release(self, agent_id: str):
        """
        Releases the lock if held by the specified agent.
        """
        if self._current_winner == agent_id:
            self._current_winner = None
            self._current_score = 0.0
            logger.info(f"🎤 Mic Released by {agent_id}")

    async def interrupt(self):
        """
        Forcefully releases the lock (User Barge-in).
        """
        if self._current_winner:
            logger.info(f"⚠️ BARGE-IN: Interrupting {self._current_winner}")
            self._current_winner = None
            self._current_score = 0.0

# Singleton Instance
auction_service = AuctionService()
