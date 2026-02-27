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
from app.services.time_skip import TimeSkipService
from app.services.cache import cache
from app.services.supervisor import CognitiveSupervisor
from app.repositories.base import SoulRepository
from app.dependencies import verify_user_logic
from core.config import settings

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages the lifecycle of a WebSocket session with the Kizuna Engine.
    Encapsulates authentication, agent retrieval, Gemini connection, and cleanup.
    """

    def __init__(self, soul_repo: SoulRepository, sleep_manager: SleepManager, time_skip_service: TimeSkipService):
        self.soul_repo = soul_repo
        self.sleep_manager = sleep_manager
        self.time_skip_service = time_skip_service

    async def handle_session(
        self, websocket: WebSocket, agent_id: str | None, token: str | None, lang: str | None = "en"
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
        user = await self.soul_repo.get_or_create_user(user_id)

        # 🕰️ Temporal Engine: Simulate Offline Reality (Phase 3)
        try:
             await self.time_skip_service.simulate_background_life(user)
        except Exception as e:
             logger.error(f"Time-Skip Simulation Failed: {e}")

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

            # Phase 5: Neural Sync (Modular Caching)
            # assemble_soul internally fetches the static DNA from cache (Zero Latency)
            # and appends the fresh volatile state (Battery, Memories, Friction).
            logger.info("⚡ Assembling Soul (Neural Sync)...")
            system_instruction = await assemble_soul(
                agent_id, user_id, self.soul_repo
            )

            # 🏰 BASTION: The Babel Protocol (Phase 7.5)
            # Inject the user's browser language directly into the active prompt.
            system_instruction += f"\n\n[CRITICAL DIRECTIVE]: The user's system language is {lang}. You MUST ALWAYS speak and respond fluently in {lang}, maintaining your established personality."

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

        # Phase 3.3: First Contact Protocol (Roster Update)
        try:
            if hasattr(self.soul_repo, "record_interaction"):
                await self.soul_repo.record_interaction(user_id, agent_id)
        except Exception as e:
            logger.error(f"Failed to record interaction edge: {e}")

        # Master Session Logger: Global Transcript Accumulation
        session_transcript_buffer: list[str] = []

        # MODULE 1: NERVOUS SYSTEM DECOUPLING
        # We decouple the 'Cognitive' tasks (Subconscious, Reflection, Injection) from the 'Motor' tasks (Audio I/O).
        # We declare the list here so it is accessible in the outer finally block for cleanup.
        cognitive_tasks = []

        try:
            async with gemini_service.connect(
                system_instruction=system_instruction, voice_name=voice_name
            ) as session:
                logger.info(f"Gemini session started for {agent_id}.")

                # Phase 2: Initialize Subconscious Channels
                # 🏰 BASTION: Set maxsize to prevent memory leaks if consumers stall
                transcript_queue = asyncio.Queue(maxsize=50)
                reflection_queue = asyncio.Queue(maxsize=20)
                injection_queue = asyncio.Queue(maxsize=20)

                # Manage bidirectional streams and subconscious concurrently
                # If either task fails (e.g. disconnect), the TaskGroup will cancel the others.

                # Phase 3: Inject Repository into Subconscious
                subconscious_mind.set_repository(self.soul_repo)
                reflection_mind.set_repository(self.soul_repo)

                try:
                    # A. Launch Cognitive Tasks (Background - Fire & Forget-ish)
                    # We store them to cancel them gracefully later.
                    # Module 4: The Cognitive Supervisor (Resilience)

                    # 3. Subconscious Mind (Transcripts -> Analysis -> Injection Queue -> Persistence)
                    cognitive_tasks.append(asyncio.create_task(
                        CognitiveSupervisor.supervise("Subconscious", lambda: subconscious_mind.start(
                            transcript_queue, injection_queue, user_id, agent_id
                        ))
                    ))

                    # 4. Injection Upstream (Injection Queue -> Gemini)
                    cognitive_tasks.append(asyncio.create_task(
                        CognitiveSupervisor.supervise("InjectionLoop", lambda: send_injections_to_gemini(session, injection_queue))
                    ))

                    # 5. Reflection Mind (AI Output -> Self-Critique -> Injection Queue)
                    if agent:
                        cognitive_tasks.append(asyncio.create_task(
                            CognitiveSupervisor.supervise("ReflectionMind", lambda: reflection_mind.start(
                                reflection_queue, injection_queue, agent
                            ))
                        ))

                    # B. Critical Motor Loop (The TaskGroup that MUST NOT DIE from cognitive errors)
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
                                agent_id=agent_id, # Module 6: Audio Concurrency ID
                                soul_repo=self.soul_repo # Module 1.5: Gossip Protocol
                            )
                        )

                except WebSocketDisconnect:
                    logger.info("WebSocket disconnected by client.")
                except Exception as e:
                    import traceback
                    logger.error(f"❌ CRITICAL ERROR in WebSocket session: {e}")
                    # If it's an ExceptionGroup (Python 3.11+), log all sub-exceptions
                    if isinstance(e, BaseExceptionGroup):
                        for i, ex in enumerate(e.exceptions):
                            logger.error(f"  Sub-exception {i}: {ex}")
                            logger.error(traceback.format_exc())
                    else:
                        logger.error(traceback.format_exc())
                    
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
            # MODULE 1: CLEANUP COGNITIVE TASKS
            # Ensure background tasks are killed when the session ends.
            # This MUST be in the outer finally block to catch CancelledError from parent.
            if cognitive_tasks:
                logger.info(f"Terminating {len(cognitive_tasks)} background cognitive tasks...")
                for task in cognitive_tasks:
                    task.cancel()

                # Wait for them to cancel to ensure clean resource release
                await asyncio.gather(*cognitive_tasks, return_exceptions=True)

            logger.info("WebSocket session closed.")

            # Update Last Seen (Phase 3)
            if hasattr(self.soul_repo, 'update_user_last_seen'):
                try:
                    # 🏰 BASTION SHIELD: Prevent hanging DB write from blocking socket release
                    await asyncio.wait_for(
                        self.soul_repo.update_user_last_seen(user_id),
                        timeout=2.0
                    )
                except Exception as e:
                    logger.warning(f"Failed to update last_seen for {user_id}: {e}")

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
