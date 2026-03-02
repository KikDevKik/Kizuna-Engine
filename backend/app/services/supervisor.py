import asyncio
import logging
from typing import Callable, Coroutine

logger = logging.getLogger(__name__)

class CognitiveSupervisor:
    """
    Manages background cognitive tasks (Subconscious, Reflection, Injection)
    with a 'Let It Crash' (Erlang-style) supervision strategy.

    If a cognitive task crashes (e.g., API 500 error), it restarts after a backoff,
    without bringing down the critical Audio I/O loop.
    """

    @staticmethod
    async def supervise(name: str, task_func: Callable[[], Coroutine], session_closed_event: asyncio.Event = None):
        """
        Runs a task in an infinite loop with error recovery.
        Stops if session_closed_event is set.
        """
        logger.info(f"🛡️ Supervisor: Starting {name}...")
        while True:
            if session_closed_event and session_closed_event.is_set():
                logger.info(f"🛡️ Supervisor: {name} stopping — session closed.")
                break

            try:
                await task_func()
                # If task_func returns normally, it means it finished its job.
                # For some tasks, we might want to exit, for others (like Subconscious)
                # it might mean it's waiting for more data.
                # However, if it's a loop that should always run, and it exits,
                # we only restart if the session is still alive.
                if session_closed_event and session_closed_event.is_set():
                    break
                
                logger.warning(f"🛡️ Supervisor: {name} finished unexpectedly. Restarting in 5s...")
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                logger.info(f"🛡️ Supervisor: {name} cancelled gracefully.")
                break
            except Exception as e:
                if session_closed_event and session_closed_event.is_set():
                    logger.info(f"🛡️ Supervisor: {name} crashed during shutdown ({e}).")
                    break
                logger.error(f"❌ Supervisor: {name} CRASHED: {e}. Restarting in 5s...")
                await asyncio.sleep(5)
