import asyncio
import logging
import json
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# VAD: Silence-based Auto End-of-Turn
# After VAD_SILENCE_MS of no new audio, flush buffer + fire turn_complete.
# Uses a SEPARATE asyncio Task so websocket.receive() is never cancelled.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VAD_SILENCE_MS = 900  # ms


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
    transcript_queue: asyncio.Queue | None = None,
    eot_reset_event: asyncio.Event | None = None,
):
    """
    Task A: Client -> Gemini
    Reads audio bytes from WebSocket and forwards to Gemini.

    VAD FIX: Uses a separate asyncio.Task for silence detection so that
    websocket.receive() is NEVER wrapped in asyncio.wait_for — avoiding
    Starlette WebSocket internal state corruption on cancellation.

    SDK FIX: The google-genai SDK silently ignores end_of_turn=True when the
    input is an audio blob (it routes audio as realtime_input, which has no
    turn_complete field). A separate text message with end_of_turn=True is
    always sent after audio flushes to correctly signal turn completion.

    DUPLICATE EOT FIX: _eot_fired flag ensures only one turn_complete is sent
    per turn. Resets via eot_reset_event when Gemini signals turn_complete.
    """
    audio_buffer = bytearray()
    carry_over = bytearray()
    silence_timer_task: Optional[asyncio.Task] = None
    eot_lock = asyncio.Lock()  # Prevents overlapping end_of_turn sends
    _eot_fired = False          # Guard: block duplicate EOTs within one turn

    async def _send_end_of_turn_signal():
        """
        Flush the audio buffer and send an EXPLICIT turn_complete text message.

        This is the critical fix: the SDK ignores end_of_turn=True on audio blob
        sends (realtime_input path). We must always follow up with a text-based
        session.send(input=" ", end_of_turn=True) to fire turn_complete correctly.
        """
        nonlocal _eot_fired
        async with eot_lock:
            if session_closed_event.is_set():
                return
            # ── DUPLICATE EOT GUARD ──────────────────────────────────
            # Only the first caller wins. VAD and frontend both call
            # this; without the guard Gemini receives two turn_complete
            # signals per turn, which silences the second response.
            if _eot_fired:
                logger.info("🔚 EOT: Already fired this turn — skipping duplicate.")
                return
            _eot_fired = True
            # Clear any queued reset so we wait for the real turn_complete
            if eot_reset_event:
                eot_reset_event.clear()
            # ─────────────────────────────────────────────────────────
            try:
                if audio_buffer:
                    logger.info(f"🔚 EOT: Flushing {len(audio_buffer)} audio bytes to Gemini")
                    await session.send(
                        input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"}
                    )
                    audio_buffer.clear()

                # SDK FIX: Always send explicit turn_complete via separate text message.
                # Audio realtime_input does NOT carry turn_complete in the protocol.
                logger.info("🔚 EOT: Sending explicit turn_complete signal to Gemini")
                await session.send(input=" ", end_of_turn=True)
                logger.info("✅ EOT: turn_complete sent. Awaiting Gemini response...")

            except Exception as e:
                _eot_fired = False  # Allow retry on send failure
                if not session_closed_event.is_set():
                    logger.warning(f"⚠️ EOT send error: {e}")

    def _reset_vad_timer():
        """
        Resets the VAD silence watchdog.
        Cancels any existing timer and starts a fresh one.
        Uses a separate asyncio Task — websocket.receive() is NEVER touched.
        """
        nonlocal silence_timer_task
        if silence_timer_task and not silence_timer_task.done():
            silence_timer_task.cancel()

        async def _vad_watchdog():
            """Fires end_of_turn after VAD_SILENCE_MS of audio inactivity."""
            try:
                await asyncio.sleep(VAD_SILENCE_MS / 1000.0)
                # Only fire if there's audio and EOT hasn't already been fired
                if audio_buffer and not session_closed_event.is_set() and not _eot_fired:
                    logger.info(f"🎙️ VAD: {VAD_SILENCE_MS}ms silence detected. Auto-firing EOT.")
                    await _send_end_of_turn_signal()
            except asyncio.CancelledError:
                pass  # Timer was reset by new audio — this is normal

        silence_timer_task = asyncio.create_task(_vad_watchdog())

    try:
        while True:
            # Clean receive — no asyncio.wait_for wrapper.
            # The VAD watchdog Task handles silence detection independently.
            message = await websocket.receive()

            # 🏰 BASTION SHIELD: Graceful Disconnect Handling
            if message.get("type") == "websocket.disconnect":
                logger.info("Client disconnected cleanly (websocket.disconnect received).")
                logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: Client disconnected in send_to_gemini")
                session_closed_event.set()
                break

            data = message.get("bytes")
            text = message.get("text")

            if data:
                if carry_over:
                    data = carry_over + data
                    carry_over.clear()

                if len(data) % 2 != 0:
                    carry_over.extend(data[-1:])
                    data = data[:-1]

                # ── POST-EOT AUDIO GUARD ─────────────────────────────
                # After EOT is fired, reset the flag only when Gemini has
                # acknowledged the turn (via eot_reset_event). Until then,
                # buffer incoming audio but do NOT flush it to Gemini.
                if _eot_fired:
                    if eot_reset_event and eot_reset_event.is_set():
                        _eot_fired = False
                        logger.info("🔄 EOT reset: ready for next turn.")
                    else:
                        # Gemini hasn't finished yet — keep buffering silently
                        audio_buffer.extend(data)
                        continue
                # ─────────────────────────────────────────────────────

                audio_buffer.extend(data)
                _reset_vad_timer()  # Always reset on new audio

                if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
                    try:
                        logger.info(f"📤 Sending audio packet: {len(audio_buffer)} bytes")
                        await session.send(
                            input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"}
                        )
                        audio_buffer.clear()
                        # VAD timer keeps running — resets on next audio chunk
                    except (ConnectionClosedError, ConnectionClosedOK) as e:
                        logger.warning(f"Gemini connection closed during audio send: {e}.")
                        logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: Gemini closed during audio send")
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
                        # Cancel VAD and clear buffer on barge-in
                        if silence_timer_task and not silence_timer_task.done():
                            silence_timer_task.cancel()
                        audio_buffer.clear()
                        await auction_service.interrupt()
                        continue

                    if control.get("type") == "end_of_turn":
                        logger.info("🔚 End of turn signal received from frontend.")
                        if silence_timer_task and not silence_timer_task.done():
                            silence_timer_task.cancel()
                        # _send_end_of_turn_signal is idempotent: guard inside will
                        # skip if VAD already fired EOT this turn.
                        await _send_end_of_turn_signal()
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
    finally:
        # Cancel VAD watchdog on exit
        if silence_timer_task and not silence_timer_task.done():
            silence_timer_task.cancel()


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
    soul_repo: Optional["SoulRepository"] = None,
    eot_reset_event: asyncio.Event | None = None,
):
    """
    Task B: Gemini -> Client
    Phase 6 Stable: Cognitive Silence Architecture with robust diagnostics.
    """
    try:
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
                                    f"Aborting turn."
                                )
                                turn_aborted = True
                            else:
                                logger.error(
                                    f"🚨 AUCTION BUG: bid() returned False but _current_winner is None. "
                                    f"Force-releasing to recover."
                                )
                                await auction_service.force_release()
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

                        if part.function_call:
                            fc = part.function_call
                            if fc.name == "spawn_stranger":
                                try:
                                    name = fc.args.get("name", "Unknown")
                                    relation = fc.args.get("relation", "Associate")
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
                            if not turn_aborted:
                                stripped = text_to_process.strip()
                                if "[THOUGHT]" in stripped:
                                    continue

                                if transcript_buffer is not None:
                                    transcript_buffer.append(f"{agent_name}: {stripped}")

                                try:
                                    await websocket.send_json({"type": "text", "data": stripped})
                                except Exception:
                                    raise WebSocketDisconnect()

                                if reflection_queue:
                                    reflection_queue.put_nowait(stripped)

                if server_content.turn_complete:
                    logger.info(f"✅ Turn complete for {agent_name} (turn_aborted={turn_aborted})")
                    turn_aborted = False
                    if agent_id:
                        await auction_service.release(agent_id)
                    # Signal send_to_gemini that it's safe to start the next turn
                    if eot_reset_event:
                        eot_reset_event.set()
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
        logger.warning(f"🔴 session_closed_event SET at: {__name__} — reason: Gemini connection closed (outer catch)")
        session_closed_event.set()
        return
    except Exception as e:
        logger.error(f"Fatal Session Error in receive_from_gemini: {type(e).__name__}: {e}", exc_info=True)
        raise e
    finally:
        if agent_id:
            await auction_service.release(agent_id)
