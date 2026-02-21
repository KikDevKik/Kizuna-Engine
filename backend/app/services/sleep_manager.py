import asyncio
import logging
from typing import Dict
from datetime import datetime
from ..repositories.base import SoulRepository
from .subconscious import subconscious_mind
from .cache import cache

logger = logging.getLogger(__name__)

class SleepManager:
    """
    Manages the REM Sleep Cycle (Consolidation) using an Event-Driven Debounce Pattern.
    Persists state to Redis (Neural Sync) to survive restarts.
    """
    def __init__(self, repository: SoulRepository):
        self.repository = repository
        # Map user_id -> asyncio.TimerHandle (or Task)
        self.active_timers: Dict[str, asyncio.Task] = {}
        # Default grace period in seconds (e.g., 300s = 5 mins)
        self.grace_period = 300
        self._is_shutting_down = False

    async def restore_state(self):
        """
        On Startup: Scan Redis for pending sleep intents and restore timers.
        """
        logger.info("💤 Restoring Sleep State from Neural Sync...")
        keys = await cache.scan_match("sleep_intent:*")
        restored_count = 0

        for key in keys:
            user_id = key.split(":")[1]
            val = await cache.get(key)
            if not val:
                continue

            try:
                target_ts = float(val)
                now = datetime.now().timestamp()
                remaining = target_ts - now

                if remaining > 0:
                    logger.info(f"Rescheduling sleep for {user_id} (in {remaining:.1f}s)")
                    task = asyncio.create_task(self._sleep_timer(user_id, remaining))
                    self.active_timers[user_id] = task
                    restored_count += 1
                else:
                    logger.info(f"Sleep overdue for {user_id}. Triggering immediately.")
                    # We trigger in background to not block startup
                    asyncio.create_task(self._trigger_consolidation(user_id))
                    await cache.delete(key)

            except ValueError:
                logger.warning(f"Invalid sleep intent value for {key}")

        logger.info(f"💤 Restored {restored_count} pending sleep cycles.")

    async def schedule_sleep(self, user_id: str, delay: int = None):
        """
        Schedule consolidation after a grace period.
        Called on WebSocket Disconnect.
        """
        if self._is_shutting_down:
            logger.info(f"🛑 Shutdown in progress. Skipping sleep schedule for {user_id}.")
            return

        if delay is None:
            delay = self.grace_period

        # Persist Intent (Neural Sync)
        target_ts = datetime.now().timestamp() + delay
        # TTL slightly longer than delay to ensure it exists until trigger
        await cache.set(f"sleep_intent:{user_id}", str(target_ts), ttl=int(delay + 60))

        # Cancel any existing timer just in case
        await self.cancel_sleep(user_id, remove_intent=False)

        logger.info(f"💤 User {user_id} disconnected. Scheduling REM Sleep in {delay}s...")

        # Create a background task that sleeps then triggers
        task = asyncio.create_task(self._sleep_timer(user_id, delay))
        self.active_timers[user_id] = task

    async def cancel_sleep(self, user_id: str, remove_intent: bool = True):
        """
        Cancel pending consolidation.
        Called on WebSocket Connect (Reconnection).
        """
        if remove_intent:
            await cache.delete(f"sleep_intent:{user_id}")

        if user_id in self.active_timers:
            task = self.active_timers.pop(user_id)
            if not task.done():
                task.cancel()
                logger.info(f"🌅 User {user_id} reconnected! REM Sleep cancelled. Session continues.")
            else:
                pass

    async def _sleep_timer(self, user_id: str, delay: int):
        """
        Internal coroutine to wait and trigger.
        """
        try:
            await asyncio.sleep(delay)
            # If we get here without cancellation, trigger consolidation
            await self._trigger_consolidation(user_id)
            # Cleanup Redis
            await cache.delete(f"sleep_intent:{user_id}")
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
            # Use Subconscious Mind to generate dreams during consolidation
            await self.repository.consolidate_memories(
                user_id,
                dream_generator=subconscious_mind.generate_dream
            )
            logger.info(f"✨ Consolidation Complete for {user_id}.")
        except Exception as e:
            logger.error(f"❌ Consolidation Failed for {user_id}: {e}")

    async def shutdown(self):
        """
        Gracefully shutdown all pending sleep/consolidation tasks.
        """
        self._is_shutting_down = True
        logger.info("🛑 SleepManager shutting down...")

        if not self.active_timers:
            return

        tasks = list(self.active_timers.values())
        for task in tasks:
            if not task.done():
                task.cancel()

        # Await clean cancellation
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.active_timers.clear()
        logger.info("🛑 SleepManager shutdown complete.")
