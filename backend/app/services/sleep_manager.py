import asyncio
import logging
from typing import Dict
from ..repositories.base import SoulRepository

logger = logging.getLogger(__name__)

class SleepManager:
    """
    Manages the REM Sleep Cycle (Consolidation) using an Event-Driven Debounce Pattern.
    When a user disconnects, a timer starts (Grace Period).
    If the user reconnects within the Grace Period, the timer is CANCELLED (session continues).
    If the timer expires, the consolidation process (Worker) is triggered.
    """
    def __init__(self, repository: SoulRepository):
        self.repository = repository
        # Map user_id -> asyncio.TimerHandle (or Task)
        self.active_timers: Dict[str, asyncio.Task] = {}
        # Default grace period in seconds (e.g., 300s = 5 mins)
        # For demo purposes, we might use a shorter duration.
        self.grace_period = 300

    def schedule_sleep(self, user_id: str, delay: int = None):
        """
        Schedule consolidation after a grace period.
        Called on WebSocket Disconnect.
        """
        if delay is None:
            delay = self.grace_period

        # Cancel any existing timer just in case
        self.cancel_sleep(user_id)

        logger.info(f"💤 User {user_id} disconnected. Scheduling REM Sleep in {delay}s...")

        # Create a background task that sleeps then triggers
        task = asyncio.create_task(self._sleep_timer(user_id, delay))
        self.active_timers[user_id] = task

    def cancel_sleep(self, user_id: str):
        """
        Cancel pending consolidation.
        Called on WebSocket Connect (Reconnection).
        """
        if user_id in self.active_timers:
            task = self.active_timers.pop(user_id)
            if not task.done():
                task.cancel()
                logger.info(f"🌅 User {user_id} reconnected! REM Sleep cancelled. Session continues.")
            else:
                # Task already finished naturally
                pass

    async def _sleep_timer(self, user_id: str, delay: int):
        """
        Internal coroutine to wait and trigger.
        """
        try:
            await asyncio.sleep(delay)
            # If we get here without cancellation, trigger consolidation
            await self._trigger_consolidation(user_id)
        except asyncio.CancelledError:
            # Task was cancelled, do nothing
            pass
        finally:
            # Cleanup map
            if user_id in self.active_timers and self.active_timers[user_id] == asyncio.current_task():
                del self.active_timers[user_id]

    async def _trigger_consolidation(self, user_id: str):
        """
        Execute the consolidation logic.
        This represents the "Worker" taking over.
        """
        logger.info(f"🌙 Grace Period expired for {user_id}. Entering REM Sleep (Consolidation)...")
        try:
            await self.repository.consolidate_memories(user_id)
            logger.info(f"✨ Consolidation Complete for {user_id}.")
        except Exception as e:
            logger.error(f"❌ Consolidation Failed for {user_id}: {e}")
