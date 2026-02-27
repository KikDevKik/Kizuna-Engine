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
    async def supervise(name: str, task_func: Callable[[], Coroutine]):
        """
        Runs a task in an infinite loop with error recovery.
        """
        logger.info(f"🛡️ Supervisor: Starting {name}...")
        while True:
            try:
                await task_func()
            except asyncio.CancelledError:
                logger.info(f"🛡️ Supervisor: {name} cancelled gracefully.")
                break
            except Exception as e:
                logger.error(f"❌ Supervisor: {name} CRASHED: {e}. Restarting in 5s...")
                await asyncio.sleep(5)
