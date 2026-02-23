import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from app.services.gemini_live import gemini_service
from app.services.audio_session import (
    send_to_gemini,
    receive_from_gemini,
    send_injections_to_gemini,
)
from app.services.soul_assembler import assemble_soul
from app.services.subconscious import subconscious_mind
from app.services.reflection import reflection_mind
from app.services.sleep_manager import SleepManager
from app.services.cache import cache
from app.repositories.base import SoulRepository
from app.dependencies import verify_user_logic
from core.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages the lifecycle of a WebSocket session with the Kizuna Engine.
    Encapsulates authentication, agent retrieval, Gemini connection, and cleanup.
    """

    def __init__(self, soul_repo: SoulRepository, sleep_manager: SleepManager):
        self.soul_repo = soul_repo
        self.sleep_manager = sleep_manager

    async def handle_session(
        self, websocket: WebSocket, agent_id: str | None, token: str | None
    ):
        """
        Main entry point for WebSocket connection handling.
        """
        # Security: Verify Origin
        origin = websocket.headers.get("origin")
        if "*" not in settings.CORS_ORIGINS and origin not in settings.CORS_ORIGINS:
            logger.warning(f"Rejected connection from unauthorized origin: {origin}")
            await websocket.close(code=1008)  # Policy Violation
            return

        # Validations
        if not agent_id:
            logger.warning("Connection rejected: No agent_id provided.")
            await websocket.close(code=1008, reason="agent_id required")
            return

        # Phase 3.2: Secure Identity (Lazy)
        try:
            user_id = verify_user_logic(token)
        except Exception as e:
            await websocket.close(code=1008, reason=str(e))
            return

        # Ensure user exists in Graph
        await self.soul_repo.get_or_create_user(user_id)

        # Phase 4: Waking Up
        await self.sleep_manager.cancel_sleep(user_id)

        # Agent Voice Configuration
        voice_name = None
        agent_name = "AI"

        try:
            # Fetch Agent to get Voice Config
            agent = await self.soul_repo.get_agent(agent_id)
            if agent:
                voice_name = agent.voice_name
                agent_name = agent.name

            # Phase 5: Neural Sync (Redis Check)
            cache_key = f"soul:{user_id}:{agent_id}"
            system_instruction = await cache.get(cache_key)

            if system_instruction:
                logger.info("⚡ Using Warmed-up Soul from Cache (Zero Latency).")
            else:
                logger.info("❄️ Cold Start: Assembling Soul from Graph...")
                system_instruction = await assemble_soul(
                    agent_id, user_id, self.soul_repo
                )

        except ValueError as e:
            logger.warning(f"Connection rejected: {e}")
            await websocket.close(code=1008, reason="Agent not found")
            return
        except Exception as e:
            logger.error(f"Error assembling soul: {e}")
            await websocket.close(code=1011, reason="Internal Soul Error")
            return

        await websocket.accept()
        logger.info(
            f"WebSocket connection established from origin: {origin} for Agent: {agent_id}"
        )

        # Master Session Logger: Global Transcript Accumulation
        session_transcript_buffer: list[str] = []

        try:
            async with gemini_service.connect(
                system_instruction=system_instruction, voice_name=voice_name
            ) as session:
                logger.info(f"Gemini session started for {agent_id}.")

                # Phase 2: Initialize Subconscious Channels
                transcript_queue = asyncio.Queue()
                reflection_queue = asyncio.Queue()
                injection_queue = asyncio.Queue()

                # Manage bidirectional streams and subconscious concurrently
                # If either task fails (e.g. disconnect), the TaskGroup will cancel the others.

                # Phase 3: Inject Repository into Subconscious
                subconscious_mind.set_repository(self.soul_repo)
                reflection_mind.set_repository(self.soul_repo)

                try:
                    async with asyncio.TaskGroup() as tg:
                        # 1. Audio Upstream (Client -> Gemini)
                        tg.create_task(
                            send_to_gemini(
                                websocket, session, session_transcript_buffer, transcript_queue
                            )
                        )

                        # 2. Audio/Text Downstream (Gemini -> Client) + Transcript Feed
                        tg.create_task(
                            receive_from_gemini(
                                websocket,
                                session,
                                transcript_queue,
                                reflection_queue,
                                session_transcript_buffer,
                                agent_name=agent_name,
                            )
                        )

                        # 3. Subconscious Mind (Transcripts -> Analysis -> Injection Queue -> Persistence)
                        tg.create_task(
                            subconscious_mind.start(
                                transcript_queue, injection_queue, user_id, agent_id
                            )
                        )

                        # 4. Injection Upstream (Injection Queue -> Gemini)
                        tg.create_task(
                            send_injections_to_gemini(session, injection_queue)
                        )

                        # 5. Reflection Mind (AI Output -> Self-Critique -> Injection Queue)
                        if agent:
                            tg.create_task(
                                reflection_mind.start(
                                    reflection_queue, injection_queue, agent
                                )
                            )

                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected by client.")
                except Exception as e:
                    logger.error(f"Error in WebSocket session: {e}")
                    # Try to close the websocket if it's still open and we had an internal error
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                finally:
                    # CRITICAL: Async Shutdown
                    # Close the websocket IMMEDIATELY to free the frontend proxy,
                    # while the Gemini session cleans up in the background (context exit).
                    try:
                        await websocket.close()
                    except Exception:
                        # Ignore if already closed
                        pass

        except Exception as e:
            logger.error(f"Unexpected error managing Gemini Session: {e}")
        finally:
            logger.info("WebSocket session closed.")

            # Full Session Persistence (Master Session Logger)
            # Decoupled to SleepManager to avoid ASGI Deadlock
            full_transcript = None
            if session_transcript_buffer:
                full_transcript = "\n".join(session_transcript_buffer)
                logger.info(
                    f"Buffering Full Session Transcript ({len(full_transcript)} chars) for {user_id}"
                )

            # Phase 4: Entering REM Sleep (Debounced Consolidation)
            # Schedule consolidation after grace period.
            asyncio.create_task(
                self.sleep_manager.schedule_sleep(
                    user_id=user_id,
                    agent_id=agent_id,
                    raw_transcript=full_transcript,
                )
            )
