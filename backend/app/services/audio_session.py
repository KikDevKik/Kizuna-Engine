import asyncio
import base64
import logging
import json
import re
import time
from fastapi import WebSocket, WebSocketDisconnect

from .agent_service import agent_service
from ..models.graph import GraphEdge
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ..repositories.base import SoulRepository

# Try importing types for robust multimodal handling
try:
    from google.genai import types
except ImportError:
    types = None

try:
    from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError
except ImportError:
    class ConnectionClosed(Exception): pass
    class ConnectionClosedOK(Exception): pass
    class ConnectionClosedError(Exception): pass

logger = logging.getLogger(__name__)

# 16000 Hz * 2 bytes = 32000 bytes/sec
# 2048 bytes = ~64ms of audio
AUDIO_BUFFER_THRESHOLD = 2048

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CAUSA 1 FIX: Silence-Based Auto End-of-Turn (VAD)
# If audio buffer stays below threshold for VAD_SILENCE_MS,
# flush and signal end_of_turn to Gemini automatically.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VAD_SILENCE_MS = 800  # ms of silence before auto-signaling end_of_turn


async def send_injections_to_gemini(session, injection_queue, session_closed_event):
    logger.info("InjectionLoop: Started.")
    running = True
    while running:
        try:
            injection = await asyncio.wait_for(
                injection_queue.get(),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            if session_closed_event.is_set():
                logger.info("InjectionLoop: Session closed. Exiting.")
                running = False
            continue
        except asyncio.CancelledError:
            logger.info("InjectionLoop: Cancelled.")
            running = False
            continue

        if session_closed_event.is_set():
            logger.info("InjectionLoop: Dropping injection — session closed.")
            running = False
            continue

        try:
            text = injection.get("text", "")
            turn_complete = injection.get("turn_complete", False)
            if not text:
                continue

            logger.info(f"💉 Injecting to Gemini: {text}")

            # 🏰 BASTION SHIELD: Strict SDK Formatting for Live API
            await session.send(
                input=f"[SYSTEM_CONTEXT]: {text}",
                end_of_turn=turn_complete
            )
        except Exception as e:
            logger.warning(f"⚠️ Injection failed: {e}")
            logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: Injection failed in send_injections_to_gemini")
            session_closed_event.set()
            running = False

    logger.info("InjectionLoop: Fully stopped.")


async def send_to_gemini(
    websocket: WebSocket,
    session,
    auction_service,
    session_closed_event: asyncio.Event,
    transcript_buffer: list[str] | None = None,
    transcript_queue: asyncio.Queue | None = None
):
    """
    Task A: Client -> Gemini
    Reads audio bytes from WebSocket and sends to Gemini session.

    CAUSA 1 FIX: Implements silence-based VAD.
    If no new audio arrives within VAD_SILENCE_MS after buffering begins,
    the buffer is flushed with end_of_turn=True so Gemini generates a response.
    """
    try:
        audio_buffer = bytearray()
        carry_over = bytearray()
        last_audio_time: Optional[float] = None  # Timestamp of last received audio chunk

        async def _flush_with_end_of_turn():
            """Flush the current buffer to Gemini and signal end of turn."""
            nonlocal last_audio_time
            if audio_buffer:
                logger.info(f"🔚 VAD Auto End-of-Turn: Flushing {len(audio_buffer)} bytes to Gemini")
                try:
                    await session.send(
                        input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"},
                        end_of_turn=True
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Error flushing audio buffer: {e}")
            else:
                logger.info("🔚 VAD Auto End-of-Turn: Buffer empty, sending blank turn signal")
                try:
                    await session.send(input=" ", end_of_turn=True)
                except Exception as e:
                    logger.warning(f"⚠️ Error sending blank turn signal: {e}")
            audio_buffer.clear()
            last_audio_time = None

        while True:
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # CAUSA 1 FIX: VAD Silence Detection
            # If we have buffered audio and no new data arrives within
            # VAD_SILENCE_MS, fire end_of_turn automatically.
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            timeout = None
            if last_audio_time is not None and audio_buffer:
                elapsed_ms = (time.monotonic() - last_audio_time) * 1000
                remaining_ms = VAD_SILENCE_MS - elapsed_ms
                if remaining_ms <= 0:
                    # Silence window expired, flush now
                    await _flush_with_end_of_turn()
                    timeout = None
                else:
                    timeout = remaining_ms / 1000.0  # convert to seconds

            try:
                message = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                # Silence window expired mid-wait
                if audio_buffer:
                    await _flush_with_end_of_turn()
                continue

            # 🏰 BASTION SHIELD: Graceful Disconnect Handling
            if message.get("type") == "websocket.disconnect":
                logger.info("Client disconnected cleanly (websocket.disconnect received).")
                logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: Client disconnected cleanly in send_to_gemini")
                session_closed_event.set()
                break  # Exit the loop immediately, don't call receive() again.

            data = message.get("bytes")
            text = message.get("text")

            if data:
                if carry_over:
                    data = carry_over + data
                    carry_over.clear()

                if len(data) % 2 != 0:
                    carry_over.extend(data[-1:])
                    data = data[:-1]

                audio_buffer.extend(data)
                last_audio_time = time.monotonic()  # Record time of last audio activity

                # Send immediately when buffer is full (real-time streaming)
                if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
                    try:
                        logger.info(f"📤 Sending audio packet: {len(audio_buffer)} bytes")
                        await session.send(input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"})
                        audio_buffer.clear()
                        # Keep last_audio_time — silence timer resets from LAST audio activity
                    except (ConnectionClosedError, ConnectionClosedOK) as e:
                        logger.warning(f"Gemini connection closed during audio send: {e}. Closing session gracefully.")
                        logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: Gemini connection closed during audio send")
                        session_closed_event.set()
                        break
                    except Exception as e:
                        logger.error(f"Unexpected error in send_to_gemini: {e}")
                        raise

            elif text:
                logger.info(f"📨 Text message received: repr={repr(text[:100])}")
                try:
                    control = json.loads(text)
                    if control.get("type") == "control" and control.get("action") == "interrupt":
                        logger.info("🛑 SOVEREIGN VOICE: User Interrupted")
                        await auction_service.interrupt()
                        # Also flush with end_of_turn on interrupt so Gemini can respond
                        last_audio_time = None
                        audio_buffer.clear()
                        continue

                    if control.get("type") == "end_of_turn":
                        logger.info("🔚 End of turn signal received from frontend. Flushing to Gemini.")
                        await _flush_with_end_of_turn()
                        continue

                    if control.get("type") == "native_transcript":
                        transcript_text = control.get("text")
                        if transcript_text:
                            if auction_service._current_winner is not None:
                                continue
                            if transcript_buffer is not None:
                                transcript_buffer.append(f"User: {transcript_text}")
                            if transcript_queue:
                                transcript_queue.put_nowait(transcript_text)
                            continue
                except json.JSONDecodeError:
                    logger.warning(f"📨 Non-JSON text message ignored: {repr(text[:100])}")
                except Exception as e:
                    logger.error(f"Error handling text message: {e}")
                continue

    except Exception as e:
        logger.warning(f"Connection dropped in send_to_gemini: {e}")
        raise e

async def receive_from_gemini(
    websocket: WebSocket,
    session,
    auction_service,
    session_closed_event: asyncio.Event,
    transcript_queue: asyncio.Queue | None = None,
    reflection_queue: asyncio.Queue | None = None,
    transcript_buffer: list[str] | None = None,
    agent_name: str = "AI",
    agent_id: Optional[str] = None,
    soul_repo: Optional["SoulRepository"] = None
):
    """
    Task B: Gemini -> Client
    Phase 6 Stable: Cognitive Silence Architecture with robust diagnostics.

    CAUSA 4 FIX: Added detailed pre-auction logging to detect silent failures.
    """
    try:
        # 🏰 BASTION: Turn-scoped state
        turn_aborted = False

        logger.info("📥 receive_from_gemini: Starting receive loop.")
        try:
            async for response in session.receive():
                logger.info(f"📥 Gemini raw response FULL: {response}")
                logger.info(
                    f"📥 has data attr: {hasattr(response, 'data')} | "
                    f"data value: {getattr(response, 'data', None) is not None} | "
                    f"server_content: {response.server_content is not None} | "
                    f"model_turn: {response.server_content.model_turn is not None if response.server_content else False}"
                )

                if session_closed_event.is_set():
                    logger.info("📥 Session closed mid-receive. Stopping.")
                    break

                # 🛡️ BASTION: Robust Audio Extraction (SDK 0.3.0 path + legacy)
                audio_data = None
                if hasattr(response, 'data') and response.data:
                    audio_data = response.data
                elif (response.server_content and
                      response.server_content.model_turn and
                      response.server_content.model_turn.parts):
                    for part in response.server_content.model_turn.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            audio_data = part.inline_data.data
                            break

                if audio_data:
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    # CAUSA 2 & 4 FIX: Log auction state BEFORE bidding
                    # so we can diagnose why audio gets dropped.
                    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    logger.info(
                        f"🔊 Audio received from Gemini ({len(audio_data)} bytes). "
                        f"Auction state: winner={auction_service._current_winner!r}, "
                        f"turn_aborted={turn_aborted}, agent_id={agent_id!r}"
                    )

                    if agent_id:
                        won = await auction_service.bid(agent_id, 1.0)
                        if not won:
                            current_winner = auction_service._current_winner
                            if current_winner is not None:
                                logger.warning(
                                    f"🔇 {agent_name} LOST AUCTION. "
                                    f"Current winner: {current_winner!r}. "
                                    f"Aborting this turn."
                                )
                                turn_aborted = True
                            else:
                                # No winner but bid failed → dirty lock state
                                logger.error(
                                    f"🚨 AUCTION BUG: bid() returned False but _current_winner is None. "
                                    f"Force-releasing to recover."
                                )
                                await auction_service.force_release()
                                # Retry bid once
                                won = await auction_service.bid(agent_id, 1.0)
                                if not won:
                                    logger.error(f"🚨 AUCTION RECOVERY FAILED for {agent_id}. Skipping audio chunk.")
                                    continue

                            if turn_aborted:
                                continue

                    try:
                        await websocket.send_bytes(audio_data)
                        logger.info(f"🔊 Audio sent to client: {len(audio_data)} bytes")
                    except Exception:
                        raise WebSocketDisconnect()

                # Handle other content (Text, Tools)
                if response.server_content is None:
                    continue

                server_content = response.server_content
                model_turn = server_content.model_turn

                if model_turn:
                    for part in model_turn.parts:
                        if turn_aborted:
                            continue

                        # 1. TOOL HANDLING (Gossip)
                        if part.function_call:
                            fc = part.function_call
                            if fc.name == "spawn_stranger":
                                try:
                                    name = fc.args.get("name", "Unknown")
                                    relation = fc.args.get("relation", "Associate")
                                    vibe = fc.args.get("vibe", "Mysterious")
                                    new_agent = await asyncio.wait_for(agent_service.create_agent(
                                        name=name, role="Stranger",
                                        base_instruction=f"You are {name}, a {relation} of {agent_name}.",
                                        voice_name="Puck", traits={"gossip_spawn": True},
                                        tags=["hollow", "gossip"]
                                    ), timeout=3.0)
                                    if soul_repo and agent_id:
                                        await asyncio.wait_for(soul_repo.create_agent(new_agent), timeout=3.0)
                                        await asyncio.wait_for(soul_repo.create_edge(GraphEdge(
                                            source_id=agent_id, target_id=new_agent.id,
                                            type="Gossip_Source", properties={"relation": relation}
                                        )), timeout=3.0)
                                    await session.send(input={"function_responses": [{"name": "spawn_stranger", "response": {"result": "success", "agent_id": new_agent.id}}]})
                                except Exception as e:
                                    logger.error(f"Tool Failed: {e}")
                            continue

                        if part.text:
                            text_to_process = part.text

                            # 🏰 BASTION: Basic Cognitive Silence Filter
                            if not turn_aborted:
                                stripped = text_to_process.strip()
                                if "[THOUGHT]" in stripped:
                                    continue

                                # Send real dialogue to client
                                if transcript_buffer is not None:
                                    transcript_buffer.append(f"{agent_name}: {stripped}")

                                try:
                                    await websocket.send_json({"type": "text", "data": stripped})
                                except Exception:
                                    raise WebSocketDisconnect()

                                if reflection_queue:
                                    reflection_queue.put_nowait(stripped)

                if server_content.turn_complete:
                    # Reset turn state
                    logger.info(f"✅ Turn complete for {agent_name} (turn_aborted={turn_aborted})")
                    turn_aborted = False
                    if agent_id:
                        await auction_service.release(agent_id)
                    try:
                        await websocket.send_json({"type": "turn_complete"})
                    except: pass

        except (WebSocketDisconnect, ConnectionClosed) as e:
            logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: receive_from_gemini stream exception")
            session_closed_event.set()
            raise e
        except (ConnectionClosedError, ConnectionClosedOK) as e:
            logger.warning(f"Gemini connection closed during receive: {e}. Ending session.")
            logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: Gemini connection closed during receive")
            session_closed_event.set()
            return
        except Exception as e:
            logger.error(f"Loop Error in receive_from_gemini: {type(e).__name__}: {e}", exc_info=True)
            raise e

    except (ConnectionClosedError, ConnectionClosedOK) as e:
        logger.warning(f"Gemini connection closed during receive: {e}. Ending session.")
        logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: Gemini connection closed during receive (outer catch)")
        session_closed_event.set()
        return
    except Exception as e:
        logger.error(f"Fatal Session Error in receive_from_gemini: {type(e).__name__}: {e}", exc_info=True)
        raise e
    finally:
        if agent_id:
            await auction_service.release(agent_id)
