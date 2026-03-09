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
from app.services.parallel_brain import parallel_brain
from app.services.reflection import reflection_mind
from app.services.sleep_manager import SleepManager
from app.services.time_skip import TimeSkipService
from app.services.cache import cache
from app.services.auction_service import AuctionService
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
        logger.info(f"👉 Received WebSocket connection request for {agent_id}")
        
        # Security: Verify Origin
        origin = websocket.headers.get("origin")
        
        # In Development (or when using non-browser clients), Origin might be None or localhost.
        # We allow None for native clients, and bypass strict origin checks if "*" is present.
        if origin is not None and "*" not in settings.CORS_ORIGINS:
            # Allow basic dev localhost origins automatically if CORS_ORIGINS isn't explicitly dropping them.
            is_localhost = "localhost" in origin or "127.0.0.1" in origin
            
            if not is_localhost and origin not in settings.CORS_ORIGINS:
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

        logger.info(f"Attempting to accept websocket connection for {agent_id}...")
        try:
            await websocket.accept()
            logger.info(f"WebSocket connection accepted from origin: {origin} for Agent: {agent_id}")
        except Exception as ws_err:
            logger.error(f"Failed to accept websocket: {ws_err}")
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
            else:
                # soul_repo no tiene el agente — buscar en agent_service (JSON)
                from app.services.agent_service import get_agent as agent_service_get_agent
                agent_from_file = await agent_service_get_agent(agent_id)
                if agent_from_file:
                    voice_name = agent_from_file.voice_name
                    agent_name = agent_from_file.name

                    try:
                        # ARCH-01: Ensure agent exists in SQLite graph
                        existing = await self.soul_repo._get_node(agent_from_file.id, "AgentNode")
                        if not existing:
                            await self.soul_repo._save_node(agent_from_file.id, "AgentNode", agent_from_file.model_dump(mode='json'))
                            logger.info(f"🔧 ARCH-01: Registered agent '{agent_from_file.name}' in SQLite at session start")
                    except Exception as e:
                        logger.warning(f"ARCH-01: Failed to register agent in SQLite: {e}")

            # Phase 5: Neural Sync (Modular Caching)
            # assemble_soul internally fetches the static DNA from cache (Zero Latency)
            # and appends the fresh volatile state (Battery, Memories, Friction).
            logger.info("⚡ Assembling Soul (Neural Sync)...")
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

        # WebSocket was accepted earlier to prevent frontend timeouts.
        

        # Phase 3.3: First Contact Protocol (Roster Update)
        try:
            if hasattr(self.soul_repo, "record_interaction"):
                await self.soul_repo.record_interaction(user_id, agent_id)
        except Exception as e:
            logger.error(f"Failed to record interaction edge: {e}")

        # Phase 2.1: Isolate Session Auction
        auction_service = AuctionService()

        # CAUSA 2 FIX: Force-release any dirty state from a previous session
        # (e.g. server survived an abrupt disconnect and lock was never released)
        await auction_service.force_release()
        logger.info("🔧 AuctionService: Clean state guaranteed for new session.")

        # Master Session Logger: Global Transcript Accumulation
        session_transcript_buffer: list[str] = []

        # MODULE 1: NERVOUS SYSTEM DECOUPLING
        # We decouple the 'Cognitive' tasks (Subconscious, Reflection, Injection) from the 'Motor' tasks (Audio I/O).
        # We declare the list here so it is accessible in the outer finally block for cleanup.
        cognitive_tasks = []

        try:
            # Contexto dinámico — se actualiza con cada búsqueda del Canal 2
            dynamic_context: str = ""
            should_reconnect = asyncio.Event()
            reconnect_context: list[str] = [""]  # lista mutable para pasar por referencia

            async def trigger_reconnect(new_context: str):
                """Callback llamado por _monitor_reconnect cuando hay contexto nuevo."""
                reconnect_context[0] = new_context
                should_reconnect.set()

            # Loop de reconexión — se repite si el Canal 2 pide un nuevo contexto
            while True:
                # Construir system_instruction con contexto acumulado
                full_instruction = system_instruction
                if dynamic_context:
                    full_instruction = f"{system_instruction}\n\n[CONTEXTO ACTUALIZADO POR BÚSQUEDA RECIENTE]:\n{dynamic_context}"

                try:
                    async with gemini_service.connect(
                        system_instruction=full_instruction,
                        voice_name=voice_name
                    ) as session:
                        logger.info(f"Gemini session started for {agent_id}. Context length: {len(full_instruction)}")

                        # Ready signal
                        try:
                            import json
                            ready_signal = json.dumps({"type": "session_ready", "agent_id": agent_id})
                            await websocket.send_text(ready_signal)
                            logger.info(f"✅ Ready signal sent to client for {agent_name}")
                        except Exception as e:
                            logger.warning(f"Failed to send ready signal: {e}")

                        # Queues
                        transcript_queue = asyncio.Queue(maxsize=50)
                        reflection_queue = asyncio.Queue(maxsize=20)
                        injection_queue = asyncio.Queue(maxsize=20)
                        session_closed_event = asyncio.Event()
                        eot_reset_event = asyncio.Event()
                        should_reconnect.clear()

                        subconscious_mind.set_repository(self.soul_repo)
                        reflection_mind.set_repository(self.soul_repo)

                        try:
                            cognitive_tasks = []

                            cognitive_tasks.append(asyncio.create_task(
                                CognitiveSupervisor.supervise("Subconscious", lambda: subconscious_mind.start(
                                    transcript_queue, injection_queue, user_id, agent_id
                                ), session_closed_event)
                            ))
                            cognitive_tasks.append(asyncio.create_task(
                                CognitiveSupervisor.supervise("InjectionLoop", lambda: send_injections_to_gemini(
                                    session, injection_queue, session_closed_event, eot_reset_event
                                ), session_closed_event)
                            ))
                            if agent:
                                cognitive_tasks.append(asyncio.create_task(
                                    CognitiveSupervisor.supervise("ReflectionMind", lambda: reflection_mind.start(
                                        reflection_queue, injection_queue, agent
                                    ), session_closed_event)
                                ))

                            parallel_transcript_queue = asyncio.Queue(maxsize=50)
                            reconnect_queue = asyncio.Queue(maxsize=1)

                            cognitive_tasks.append(asyncio.create_task(
                                CognitiveSupervisor.supervise(
                                    "ParallelBrain",
                                    lambda: parallel_brain.start(
                                        parallel_transcript_queue,
                                        reconnect_queue,
                                        user_id,
                                        agent_id,
                                        session_closed_event,
                                    ),
                                    session_closed_event,
                                )
                            ))

                            async with asyncio.TaskGroup() as tg:
                                tg.create_task(
                                    send_to_gemini(
                                        websocket, session, auction_service,
                                        session_closed_event, session_transcript_buffer,
                                        transcript_queue,
                                        eot_reset_event=eot_reset_event,
                                        parallel_transcript_queue=parallel_transcript_queue,
                                    )
                                )
                                tg.create_task(
                                    receive_from_gemini(
                                        websocket, session, auction_service,
                                        session_closed_event, transcript_queue,
                                        reflection_queue, session_transcript_buffer,
                                        agent_name=agent_name, agent_id=agent_id,
                                        soul_repo=self.soul_repo,
                                        eot_reset_event=eot_reset_event,
                                    )
                                )
                                tg.create_task(
                                    _monitor_reconnect(
                                        reconnect_queue,
                                        websocket,
                                        session_closed_event,
                                        trigger_reconnect,
                                    )
                                )

                        except WebSocketDisconnect:
                            logger.info("WebSocket disconnected by client.")
                            break  # Salir del loop de reconexión
                        except Exception as e:
                            import traceback
                            logger.error(f"❌ CRITICAL ERROR in WebSocket session: {e}")
                            if isinstance(e, BaseExceptionGroup):
                                for i, ex in enumerate(e.exceptions):
                                    logger.error(f"  Sub-exception {i}: {ex}")
                            logger.error(traceback.format_exc())
                            try:
                                await websocket.close()
                            except Exception:
                                pass
                            break
                        finally:
                            if cognitive_tasks:
                                logger.info(f"Terminating {len(cognitive_tasks)} background cognitive tasks...")
                                for task in cognitive_tasks:
                                    task.cancel()
                                await asyncio.gather(*cognitive_tasks, return_exceptions=True)

                except Exception as e:
                    logger.error(f"Unexpected error managing Gemini Session: {e}")
                    break

                # ¿Reconectar con nuevo contexto?
                if should_reconnect.is_set() and reconnect_context[0]:
                    dynamic_context = reconnect_context[0]
                    logger.info(f"🔄 Micro-Reconexión ejecutada. Nuevo contexto: {dynamic_context[:80]}...")
                    reconnect_context[0] = ""
                    # Pequeña pausa antes de reconectar
                    await asyncio.sleep(0.5)
                    continue  # Volver al inicio del while True con nuevo contexto
                else:
                    break  # Sesión terminó normalmente — no reconectar
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
            subconscious_mind.cleanup(user_id)

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


                        # KIZUNA ETERNAL MEMORY: Chronicle Update
            if subconscious_mind and session_transcript_buffer and agent_id != "kizuna":
                asyncio.create_task(
                    subconscious_mind._update_kizuna_chronicle(
                        user_id=user_id,
                        agent_id=agent_id,
                        agent_name=agent_name,
                        transcript_buffer=session_transcript_buffer,
                    )
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


async def _monitor_reconnect(
    reconnect_queue: asyncio.Queue,
    websocket,
    session_closed_event: asyncio.Event,
    reconnect_callback,
):
    """
    Monitorea la cola del Canal 2.
    Cuando llega un resultado de búsqueda, ejecuta la Micro-Reconexión
    Sincronizada: notifica al frontend, espera silencio de audio,
    y llama al callback de reconexión con el nuevo contexto.
    """
    logger = logging.getLogger(__name__)

    try:
        while not session_closed_event.is_set():
            try:
                result = await asyncio.wait_for(
                    reconnect_queue.get(), timeout=2.0
                )
            except asyncio.TimeoutError:
                continue

            if not result:
                continue

            logger.info(f"🔄 Micro-Reconexión: Resultado recibido del Canal 2.")

            # 1. Notificar al frontend — reproducir filler
            try:
                await websocket.send_json({
                    "type": "CONTROL",
                    "action": "AGENT_THINKING",
                    "message": "Un momento..."
                })
            except Exception:
                pass

            # 2. Pequeña pausa para dejar que el audio actual termine
            await asyncio.sleep(0.3)

            # 3. Señalizar reconexión al SessionManager
            await reconnect_callback(result)

    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"_monitor_reconnect error: {e}")
