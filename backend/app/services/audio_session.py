import asyncio
import re
import base64
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

# SDK v1.65.0: use send_realtime_input(audio=Blob) / audio_stream_end=True
# 16000 Hz * 2 bytes/sample = 32000 bytes/sec; 2048 bytes ~= 64ms
AUDIO_BUFFER_THRESHOLD = 2048
VAD_SILENCE_MS = 1500  # ms

# Requires explicit platform name alongside action verb — prevents false triggers in normal conversation
ACTION_PATTERNS = [
    # "busca X en YouTube", "search X on Spotify", "find X on Google"
    r'\b(busca|b\u00fascalo|b\u00fascala|buscar|search|find|abre|open)\b.{1,60}\b(youtube|spotify|google|web)\b',
    # "en YouTube busca X", "Spotify pon X"
    r'\b(youtube|spotify|google)\b.{0,40}\b(busca|b\u00fascalo|search|find|pon|play|reproduce)\b',
    # "pon X en Spotify", "play X on YouTube"
    r'\b(pon|play|reproduce)\b.{1,60}\b(youtube|spotify)\b',
]

ALLOWED_ACTION_URLS = (
    "https://www.google.com/search",
    "https://open.spotify.com/search",
    "https://www.youtube.com/results",
    "https://www.youtube.com/watch",
    "https://music.youtube.com",
    "https://www.google.com/maps/search",
)


async def _detect_and_execute_action(transcript: str, websocket: WebSocket):
    """
    Computer Use — Intent Detection Channel.
    Fires when a user transcript contains action keywords.
    Uses a lightweight Gemini Flash text call to resolve the
    intent into a concrete URL, then relays it to the frontend.
    Never blocks the audio pipeline (called via asyncio.create_task).
    """
    import os
    from google import genai as _genai

    prompt = f"""The user said: "{transcript}"

Extract ONLY the search term they want to find, removing any command words like "busca", "search", "find", "abre", "pon", "Kizuna", "reproduce", "open", "play", etc.

Then respond with ONLY one of these formats:
OPEN_URL:https://www.youtube.com/results?search_query=SEARCH_TERM_HERE
OPEN_URL:https://www.google.com/search?q=SEARCH_TERM_HERE
OPEN_URL:https://open.spotify.com/search/SEARCH_TERM_HERE
OPEN_URL:https://www.google.com/maps/search/PLACE_HERE

Choose YouTube if they mention YouTube or videos, Spotify if they mention Spotify, music or songs, Google otherwise.
URL-encode the search term (spaces as +, special chars encoded).

If they are NOT asking to search anything, respond with: NO_ACTION

Respond with ONLY the URL line or NO_ACTION. Nothing else."""

    try:
        client = _genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        result = response.text.strip() if response.text else "NO_ACTION"
        logger.debug(f"🔍 Intent detection result: {result!r}")

        if result.startswith("OPEN_URL:"):
            url = result[9:].strip()
            if url.startswith(ALLOWED_ACTION_URLS):
                await websocket.send_json({
                    "type": "action",
                    "action": "open_url",
                    "url": url
                })
                logger.info(f"🖥️ Computer Use [intent]: {url}")
            else:
                logger.warning(f"Computer Use [intent]: BLOCKED — not in whitelist: {url}")
    except Exception as e:
        logger.warning(f"Computer Use intent detection failed: {e}")


async def send_injections_to_gemini(session, injection_queue, session_closed_event, eot_reset_event=None):
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

        # ── INJECTION DISABLED FOR NATIVE AUDIO MODEL ────────────────────
        # Injecting text into a native audio session corrupts conversation
        # history — the model stops responding to audio after seeing text.
        text = injection.get("text", "")
        if text:
            logger.info(f"💉 Injection SKIPPED (native audio mode): {text[:60]}")
        continue

    logger.info("InjectionLoop: Fully stopped.")


async def send_to_gemini(
    websocket: WebSocket,
    session,
    auction_service,
    session_closed_event: asyncio.Event,
    transcript_buffer: list[str] | None = None,
    transcript_queue: asyncio.Queue | None = None,
    eot_reset_event: asyncio.Event | None = None,
    parallel_transcript_queue: asyncio.Queue | None = None,
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
        Collect all buffered audio and send as client_content audio turn.

        ROOT CAUSE FIX: Mixing realtime_input + client_content (text ' ') in the
        same session corrupts native audio model history. After 2 turns with text
        entries ('\u0020', '[SYSTEM_CONTEXT]...'), Gemini stops responding entirely.

        FIX: Buffer ALL audio (threshold=10MB, never flushes mid-turn) and send
        on EOT as types.LiveClientContent(turns=[audio Part], turn_complete=True).
        History becomes: [audio] → [assistant audio] → [audio] → ... (no text ever)
        """
        nonlocal _eot_fired
        async with eot_lock:
            if session_closed_event.is_set():
                return
            if _eot_fired:
                logger.info("🔚 EOT: Already fired this turn — skipping duplicate.")
                return
            _eot_fired = True
            if eot_reset_event:
                eot_reset_event.clear()
            try:
                # Flush any remaining buffered audio first
                if audio_buffer:
                    logger.info(f"🔚 EOT: Flushing {len(audio_buffer)} remaining bytes")
                    await session.send_realtime_input(
                        audio=types.Blob(data=bytes(audio_buffer), mime_type="audio/pcm;rate=16000")
                    )
                    audio_buffer.clear()

                # Signal end of audio stream — server-VAD triggers Gemini response
                logger.info("🔚 EOT: Sending audio_stream_end to Gemini")
                await session.send_realtime_input(audio_stream_end=True)
                logger.info("✅ EOT: audio_stream_end sent. Awaiting Gemini response...")

                async def _eot_recovery_watchdog():
                    nonlocal _eot_fired
                    try:
                        await asyncio.sleep(12.0)
                        if _eot_fired and not session_closed_event.is_set():
                            logger.warning("⏰ EOT watchdog: No response in 12s — unlocking.")
                            _eot_fired = False
                            audio_buffer.clear()
                            if eot_reset_event:
                                eot_reset_event.set()
                    except asyncio.CancelledError:
                        pass

                asyncio.create_task(_eot_recovery_watchdog())

            except Exception as e:
                _eot_fired = False
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
                # Block audio while _eot_fired=True (Gemini is generating).
                # Audio flowing during generation sends stale silence that
                # confuses the model on subsequent turns.
                # Reset flag when Gemini sends turn_complete (eot_reset_event).
                if _eot_fired:
                    if eot_reset_event and eot_reset_event.is_set():
                        _eot_fired = False
                        logger.info("\U0001f504 EOT reset: ready for next turn.")
                    else:
                        # Still waiting for Gemini — discard this audio chunk
                        continue
                # ─────────────────────────────────────────────────────

                audio_buffer.extend(data)
                _reset_vad_timer()  # Always reset on new audio

                if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
                    try:
                        logger.debug(f"📤 Sending audio packet: {len(audio_buffer)} bytes")
                        await session.send_realtime_input(
                            audio=types.Blob(
                                data=bytes(audio_buffer),
                                mime_type="audio/pcm;rate=16000"
                            )
                        )
                        audio_buffer.clear()
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

                            # Reenviar al Canal 2 si está activo
                            if parallel_transcript_queue is not None:
                                try:
                                    parallel_transcript_queue.put_nowait(transcript_text)
                                except asyncio.QueueFull:
                                    pass

                            # Computer Use — Intent Detection
                            # Requires explicit platform mention to avoid triggering on normal conversation.
                            if any(re.search(p, transcript_text.lower()) for p in ACTION_PATTERNS):
                                logger.info(f"🎯 Computer Use pattern matched — launching intent detection")
                                asyncio.create_task(
                                    _detect_and_execute_action(transcript_text, websocket)
                                )
                        continue

                    if control.get("type") == "image":
                        try:
                            image_b64 = control.get("data", "")
                            if not image_b64:
                                continue
                            if types is None:
                                logger.warning("Vision frame dropped: google.genai.types not available — SDK import failed")
                                continue

                            if image_b64.startswith("data:"):
                                image_b64 = image_b64.split(",")[1]

                            image_bytes = base64.b64decode(image_b64)
                            await session.send_realtime_input(
                                video=types.Blob(
                                    data=image_bytes,
                                    mime_type="image/jpeg"
                                )
                            )
                            logger.debug(f"🎥 Vision frame relayed to Gemini ({len(image_bytes)} bytes)")
                        except Exception as img_err:
                            logger.warning(f"Vision frame relay failed: {img_err}")
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
        turn_text_buffer: list[str] = []  # Accumulates ALL text parts across the entire turn

        logger.info("📥 receive_from_gemini: Starting receive loop.")
        try:
            # ── CRITICAL: The SDK's session.receive() is a SINGLE-TURN
            # generator — it breaks internally after turn_complete. We must
            # re-call it in an outer while loop to stay alive across turns.
            while not session_closed_event.is_set():
              async for response in session.receive():
                logger.debug(f"📥 Gemini raw response FULL: {response}")
                logger.debug(
                    f"📥 has data attr: {hasattr(response, 'data')} | "
                    f"data value: {getattr(response, 'data', None) is not None} | "
                    f"server_content: {response.server_content is not None} | "
                    f"model_turn: {response.server_content.model_turn is not None if response.server_content else False}"
                )

                if session_closed_event.is_set():
                    logger.info("📥 Session closed mid-receive. Stopping.")
                    break

                # BARGE-IN: Detectar interrupción inmediatamente
                if hasattr(response, 'server_content') and response.server_content:
                    if getattr(response.server_content, 'interrupted', False):
                        logger.info("🤚 Barge-in detected — user interrupted agent. Flushing audio.")
                        await websocket.send_json({
                            "type": "CONTROL",
                            "action": "FLUSH_AUDIO"
                        })
                        continue  # NO esperar transcripción — saltar inmediatamente

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
                    logger.debug(
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
                        logger.debug(f"🔊 Audio sent to client: {len(audio_data)} bytes")
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

                                # ── COMPUTER USE: Immediate scan on each part ────────────
                                # Native audio model may emit ACTION tags in any text part
                                # across multiple response packets. Scan immediately AND
                                # accumulate for the turn-end scan.
                                turn_text_buffer.append(stripped)

                                ALLOWED_URL_PREFIXES = (
                                    "https://www.google.com/search",
                                    "https://open.spotify.com/search",
                                    "https://www.youtube.com/results",
                                    "https://www.youtube.com/watch",
                                    "https://music.youtube.com",
                                    "https://www.google.com/maps/search",
                                )

                                url_match = re.search(r'\[ACTION: OPEN_URL:([^\]]+)\]', stripped)
                                if url_match:
                                    action_url = url_match.group(1).strip()
                                    if action_url.startswith(ALLOWED_URL_PREFIXES):
                                        try:
                                            await websocket.send_json({
                                                "type": "action",
                                                "action": "open_url",
                                                "url": action_url
                                            })
                                            logger.info(f"🖥️ Computer Use [part]: relayed open_url → {action_url}")
                                        except Exception as cu_err:
                                            logger.warning(f"Computer Use: failed to relay: {cu_err}")
                                    else:
                                        logger.warning(f"Computer Use: BLOCKED — not in whitelist: {action_url}")

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

                    # ── COMPUTER USE: Turn-end cumulative scan ──────────────
                    # Catch ACTION tags that arrived across multiple packets
                    # (native audio model may interleave text + audio parts)
                    if turn_text_buffer and not turn_aborted:
                        full_turn_text = " ".join(turn_text_buffer)
                        ALLOWED_URL_PREFIXES = (
                            "https://www.google.com/search",
                            "https://open.spotify.com/search",
                            "https://www.youtube.com/results",
                            "https://www.youtube.com/watch",
                            "https://music.youtube.com",
                            "https://www.google.com/maps/search",
                        )
                        for url_match in re.finditer(r'\[ACTION: OPEN_URL:([^\]]+)\]', full_turn_text):
                            action_url = url_match.group(1).strip()
                            if action_url.startswith(ALLOWED_URL_PREFIXES):
                                try:
                                    await websocket.send_json({
                                        "type": "action",
                                        "action": "open_url",
                                        "url": action_url
                                    })
                                    logger.info(f"🖥️ Computer Use [turn-end]: relayed open_url → {action_url}")
                                except Exception as cu_err:
                                    logger.warning(f"Computer Use [turn-end]: failed to relay: {cu_err}")
                            else:
                                logger.warning(f"Computer Use [turn-end]: BLOCKED — not in whitelist: {action_url}")
                    turn_text_buffer.clear()
                    # ───────────────────────────────────────────────────────

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
