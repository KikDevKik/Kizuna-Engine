import asyncio
import base64
import logging
import json
import re
from fastapi import WebSocket, WebSocketDisconnect

from .auction_service import auction_service
from .agent_service import agent_service
from ..models.graph import GraphEdge
# Note: We avoid importing SoulRepository type to prevent circular imports if possible,
# but for type hinting we can use explicit string or conditional.
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from ..repositories.base import SoulRepository

# Try importing types for robust multimodal handling
try:
    from google.genai import types
except ImportError:
    types = None

# Try importing websockets exceptions if available (used by some underlying libraries)
try:
    from websockets.exceptions import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError
except ImportError:
    # If websockets is not installed, define dummy exceptions that won't match anything
    class ConnectionClosed(Exception): pass
    class ConnectionClosedOK(Exception): pass
    class ConnectionClosedError(Exception): pass

logger = logging.getLogger(__name__)

# 16000 Hz * 2 bytes = 32000 bytes/sec
# 3200 bytes = 100ms
AUDIO_BUFFER_THRESHOLD = 3200

async def send_injections_to_gemini(session, injection_queue: asyncio.Queue):
    """
    Task C: Subconscious -> Gemini
    Injects system hints (text) into the active session without ending the turn.
    """
    try:
        while True:
            # Wait for a "hint" from the subconscious
            hint_payload = await injection_queue.get()

            text = hint_payload.get("text", "")
            turn_complete = hint_payload.get("turn_complete", False)

            if not text:
                continue

            logger.info(f"🤫 Whispering to Gemini: {text}")

            # Send text with end_of_turn=False to inject context silently
            # The SDK method session.send(input=..., end_of_turn=False)
            await session.send(input=text, end_of_turn=turn_complete)

    except asyncio.CancelledError:
        logger.info("Injection loop cancelled.")
    except Exception as e:
        logger.error(f"Error injecting system hint: {e}")
        # Don't crash, just log and continue/retry?
        pass


async def send_to_gemini(websocket: WebSocket, session, transcript_buffer: list[str] | None = None, transcript_queue: asyncio.Queue | None = None):
    """
    Task A: Client -> Gemini
    Reads audio bytes from WebSocket and sends to Gemini session.
    Buffering logic added to prevent flooding Gemini with tiny packets.
    """
    try:
        packet_count = 0
        audio_buffer = bytearray()
        carry_over = bytearray()  # Buffer for odd bytes

        while True:
            # Handle Multimodal Input (Phase 5)
            # We must detect if the message is bytes (audio) or text/json (video/control)
            message = await websocket.receive()

            data = message.get("bytes")
            text = message.get("text")

            if data:
                # --- AUDIO FLOW ---
                # Module 6: User Barge-in -> Interrupt Agent
                await auction_service.interrupt()

                # Prepend carry_over from previous iteration
                if carry_over:
                    data = carry_over + data
                    carry_over.clear()

                # Handle odd number of bytes (alignment check)
                # In Python 3.12, extend works with bytes too.
                # data is 'bytes'. We need to be careful.
                if len(data) % 2 != 0:
                    carry_over.extend(data[-1:])
                    data = data[:-1]

                packet_count += 1
                audio_buffer.extend(data)

                # Buffer up to ~100ms (3200 bytes)
                if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
                    await session.send(input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"})
                    audio_buffer.clear()

            elif text:
                # --- VIDEO / CONTROL FLOW ---
                try:
                    payload = json.loads(text)

                    # SOVEREIGN VOICE: Explicit Interrupt
                    if payload.get("type") == "control" and payload.get("action") == "interrupt":
                        logger.info("🛑 SOVEREIGN VOICE: User Interrupted (Explicit Signal)")
                        await auction_service.interrupt()
                        # Note: We can't force the 'session.receive()' loop to stop yielding easily
                        # from here without shared state, but clearing the auction lock prevents
                        # new audio from being sent to client in 'receive_from_gemini'.
                        continue

                    # TRUE ECHO PROTOCOL: Handle Native Transcript
                    if payload.get("type") == "native_transcript":
                        transcript_text = payload.get("text")
                        if transcript_text:
                            logger.info(f"🎤 Native Transcript: {transcript_text}")

                            # a) Append to Global Transcript Buffer
                            if transcript_buffer is not None:
                                transcript_buffer.append(f"User: {transcript_text}")

                            # b) Push to Subconscious (Emotion Analysis)
                            if transcript_queue:
                                try:
                                    transcript_queue.put_nowait(transcript_text)
                                except asyncio.QueueFull:
                                    logger.warning("⚠️ Transcript Queue Full! Dropping user text for Subconscious.")
                                except Exception as e:
                                    logger.warning(f"Failed to queue native transcript: {e}")

                            # c) DO NOT forward to Gemini (Prevent Double Processing)
                            continue

                    # Capture User Text (if provided)
                    if transcript_buffer is not None:
                        # Assuming 'text' type or implicit text in payload
                        # Adjust based on actual client protocol if needed
                        user_text = payload.get("text")
                        # If the payload is just text content (e.g. {type: "text", text: "Hello"})
                        # Or if the payload itself IS the text (though it's json.loads parsed)
                        if payload.get("type") == "text" and payload.get("data"):
                             user_content = payload.get('data')
                             transcript_buffer.append(f"User: {user_content}")

                             # Feed Subconscious Mind (Direct Text Input)
                             if transcript_queue:
                                 try:
                                     transcript_queue.put_nowait(user_content)
                                 except asyncio.QueueFull:
                                     logger.warning("⚠️ Transcript Queue Full! Dropping user text.")
                                 except Exception as e:
                                     logger.warning(f"Failed to queue user text transcript: {e}")

                    if payload.get("type") == "image":
                        # Phase 5: Ojos Digitales
                        # Payload: {type: "image", data: "base64..."}
                        b64_image = payload.get("data")
                        if b64_image:
                            logger.info("📷 Sending Video Frame to Gemini...")
                            # Decode base64 to bytes in a thread pool to avoid blocking the event loop
                            image_bytes = await asyncio.to_thread(base64.b64decode, b64_image)

                            # Argus Phase 6: Use simple dict payload to avoid SDK type warnings
                            # "Unsupported input type <class 'google.genai.types.Content'>"
                            await session.send(input={"data": image_bytes, "mime_type": "image/jpeg"})

                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON text from client.")
                except Exception as e:
                    logger.error(f"Error handling text message: {e}")

    except (WebSocketDisconnect, ConnectionClosed, ConnectionClosedOK, ConnectionClosedError) as e:
        logger.info(f"Client disconnected (send_to_gemini): {e}")
        # Re-raise to trigger TaskGroup cancellation of other tasks (e.g. receive loop)
        raise e

    except Exception as e:
        # Check for specific string patterns if exception type is generic
        error_msg = str(e).lower()
        if "disconnect" in error_msg or "closed" in error_msg or "1006" in error_msg or "1011" in error_msg or "unexpected asgi message" in error_msg:
             logger.warning(f"Connection dropped in send_to_gemini: {e}")
             raise e

        logger.error(f"Error sending to Gemini: {e}")
        # 🏰 BASTION: Fail Fast. If audio upstream dies, the session is zombie. Kill it.
        raise e

async def receive_from_gemini(
    websocket: WebSocket,
    session,
    transcript_queue: asyncio.Queue | None = None,
    reflection_queue: asyncio.Queue | None = None,
    transcript_buffer: list[str] | None = None,
    agent_name: str = "AI",
    agent_id: Optional[str] = None,
    soul_repo: Optional["SoulRepository"] = None
):
    """
    Task B: Gemini -> Client + Subconscious
    Receives from Gemini and sends to WebSocket as custom JSON.
    Also sends text transcripts to the Subconscious Mind via transcript_queue.

    ARCHIVIST UPDATE (Echo Protocol):
    - Intercepts <user_log>...</user_log> to log user speech.
    - Strips internal monologue (**...**) from transcripts.
    """
    try:
        while True:
            try:
                async for response in session.receive():
                    # SOVEREIGN VOICE: Check lock status before processing chunks
                    # If lock is lost (user barged in), we should mute output.
                    is_interrupted = False
                    if agent_id:
                        # We don't bid here, just check if we still hold it if we did before.
                        # Actually, bid() handles re-acquisition or check.
                        # But interrupt() clears the winner.
                        # So if we are sending audio, we check if we are the winner.
                        pass

                    if response.server_content is None:
                        continue

                    server_content = response.server_content
                    model_turn = server_content.model_turn

                    if model_turn:
                        turn_aborted = False # Reset abort flag for the new turn
                        for part in model_turn.parts:
                            # If the turn was aborted (e.g., lost auction), ignore all subsequent parts of this turn
                            if turn_aborted:
                                continue

                            # --- MODULE 1.5: GOSSIP TOOL ---
                            if part.function_call:
                                fc = part.function_call
                                if fc.name == "spawn_stranger":
                                    logger.info(f"🛠️ Tool Use Detected: spawn_stranger args={fc.args}")
                                    try:
                                        # Extract args
                                        name = fc.args.get("name", "Unknown")
                                        relation = fc.args.get("relation", "Associate")
                                        vibe = fc.args.get("vibe", "Mysterious")

                                        # Create the Stranger Agent directly
                                        new_agent = await agent_service.create_agent(
                                            name=name,
                                            role="Stranger",
                                            base_instruction=f"You are {name}, a {relation} of {agent_name}. Aesthetic/Vibe: {vibe}.",
                                            voice_name="Puck",
                                            traits={"gossip_spawn": True, "relation": relation},
                                            tags=["hollow", "gossip", "spawned"]
                                        )

                                        # Create the Gossip Edge (Roster Agent -> Stranger)
                                        if soul_repo and agent_id:
                                            # We need to ensure new_agent is in the repo/cache
                                            if hasattr(soul_repo, 'create_agent'):
                                                await soul_repo.create_agent(new_agent)

                                            edge = GraphEdge(
                                                source_id=agent_id,
                                                target_id=new_agent.id,
                                                type="Gossip_Source",
                                                properties={"relation": relation, "context": vibe}
                                            )
                                            if hasattr(soul_repo, 'create_edge'):
                                                await soul_repo.create_edge(edge)
                                                logger.info(f"🕸️ Gossip Edge Created: {agent_name} -> {name}")

                                        # Send Tool Response to Gemini
                                        # Solution B: Use native dictionary for tool responses if supported, 
                                        # otherwise ensure type safety.
                                        tool_response = {
                                            "function_responses": [
                                                {
                                                    "name": "spawn_stranger",
                                                    "response": {"result": "success", "agent_id": new_agent.id}
                                                }
                                            ]
                                        }
                                        await session.send(input=tool_response)

                                    except Exception as e:
                                        logger.error(f"Tool Execution Failed: {e}")
                                        # Send error response
                                        # Solution B: Native dictionary for error response
                                        tool_error_response = {
                                            "function_responses": [
                                                {
                                                    "name": "spawn_stranger",
                                                    "response": {"error": str(e)}
                                                }
                                            ]
                                        }
                                        await session.send(input=tool_error_response)
                                continue

                            # --- ANTHROPOLOGIST: HANG-UP INTERCEPTOR ---
                            # Check text for [ACTION: HANGUP] before processing
                            if part.text and "[ACTION: HANGUP]" in part.text:
                                logger.warning(f"⛔ AGENT INITIATED HANG-UP: {part.text}")
                                # Send a final polite close message (optional) or just kill it.
                                # Requirement: "Physically hangs up".
                                # We can send a control message so frontend knows WHY.
                                try:
                                    await websocket.send_json({
                                        "type": "control",
                                        "action": "hangup",
                                        "reason": "Agent initiated termination."
                                    })
                                except Exception as e:
                                    logger.warning(f"Failed to send hangup control message: {e}")

                                # Force disconnect (Triggers TaskGroup cancellation)
                                raise WebSocketDisconnect(code=1000, reason="Agent Hangup")

                            # Handle Audio
                            if part.inline_data:
                                # --- MODULE 6: AUDIO CONCURRENCY LOCK ---
                                if agent_id:
                                    # Bid for the mic (Priority 1.0 default)
                                    won = await auction_service.bid(agent_id, 1.0)
                                    if not won:
                                        # 🔇 Auction Lost: Drop Audio and Abort Turn
                                        # To prevent mid-sentence cut-ins, we give up on this entire AI response turn.
                                        logger.info(f"🔇 {agent_name} lost the auction. Aborting turn to prevent cut-off phrase.")
                                        turn_aborted = True
                                        continue

                                # part.inline_data.data is bytes
                                # Optimize: Send raw binary directly to avoid Base64 overhead
                                try:
                                    await websocket.send_bytes(part.inline_data.data)
                                except (RuntimeError, WebSocketDisconnect, ConnectionClosed, ConnectionClosedOK, ConnectionClosedError) as e:
                                    # 🏰 BASTION SHIELD: Ignore write errors on closed sockets to prevent ECONNRESET
                                    logger.debug(f"Audio send suppressed: Socket already closed ({type(e).__name__})")
                                    raise WebSocketDisconnect()
                                except Exception as e:
                                    # Check for specific string patterns for low-level OS errors
                                    if "closed" in str(e).lower() or "1006" in str(e) or "reset" in str(e).lower():
                                        raise WebSocketDisconnect()
                                    raise e

                            # Handle Text (if interleaved or final transcript)
                            if part.text:
                                text_to_process = part.text

                                # --- Heuristic CoT Filter (English Monologue Detector) ---
                                # Gemini Live often ignores [THOUGHT] tags and streams raw English CoT before the Spanish audio.
                                # If the text looks like internal reasoning, drop it immediately.
                                stripped_text = text_to_process.strip()
                                # Common CoT starters observed in logs
                                cot_starters = ("Okay,", "So,", "I ", "The user", "Alright,", "Let me", "Based on", "Thinking:")
                                if stripped_text.startswith(cot_starters) or (len(stripped_text) > 20 and "user" in stripped_text.lower() and "context" in stripped_text.lower()):
                                    logger.debug(f"🛑 Dropped Potential CoT/Monologue: {stripped_text[:50]}...")
                                    continue

                                # --- Clean Internal Monologue ---
                                # Strip [THOUGHT]...[/THOUGHT] (Chain of Thought)
                                text_to_process = re.sub(r'\[THOUGHT\].*?\[/THOUGHT\]', '', text_to_process, flags=re.DOTALL)

                                # Strip <thinking>...</thinking> (Cognitive Exhaust - Legacy)
                                # Archibald's Clean-up: Prevent internal monologue from leaking to TTS/DB.
                                text_to_process = re.sub(r'<thinking>.*?</thinking>', '', text_to_process, flags=re.DOTALL)

                                # Strip **...** (Cognitive Exhaust)
                                # Note: This simple regex might fail if ** is split across chunks.
                                # But handling split tokens is complex. Best effort for now.
                                clean_text = re.sub(r'\*\*.*?\*\*', '', text_to_process, flags=re.DOTALL).strip()

                                if not clean_text:
                                    continue

                                logger.info(f"Gemini -> Client: Text: {clean_text[:50]}...")

                                # Global Transcript Buffer (AI Response)
                                if transcript_buffer is not None:
                                    transcript_buffer.append(f"{agent_name}: {clean_text}")

                                try:
                                    await websocket.send_json({
                                        "type": "text",
                                        "data": clean_text
                                    })
                                except (RuntimeError, WebSocketDisconnect, ConnectionClosed, ConnectionClosedOK, ConnectionClosedError) as e:
                                    logger.debug(f"Text send suppressed: Socket already closed ({type(e).__name__})")
                                    raise WebSocketDisconnect()
                                except Exception as e:
                                    if "closed" in str(e).lower() or "1006" in str(e) or "reset" in str(e).lower():
                                        raise WebSocketDisconnect()
                                    raise e

                                # Feed Reflection Mind (AI Output)
                                if reflection_queue:
                                    try:
                                        reflection_queue.put_nowait(clean_text)
                                    except asyncio.QueueFull:
                                        logger.debug("Reflection Queue Full. Dropping introspection.")
                                    except Exception as e:
                                        logger.warning(f"Failed to queue reflection: {e}")

                    # Handle turn completion
                    if server_content.turn_complete:
                        logger.info("Gemini -> Client: Turn complete signal.")

                        # --- MODULE 6: RELEASE LOCK ---
                        if agent_id:
                            await auction_service.release(agent_id)

                        try:
                            await websocket.send_json({"type": "turn_complete"})
                        except RuntimeError as e:
                            if "Unexpected ASGI message" in str(e) or "closed" in str(e).lower():
                                logger.debug("Socket closed before turn_complete could be sent.")
                                raise WebSocketDisconnect()
                            raise e

            except asyncio.CancelledError:
                logger.info("Receive loop cancelled (Graceful Shutdown).")
                raise

            except WebSocketDisconnect:
                # 🏰 BASTION SHIELD: Ensure disconnects propagate to cancel TaskGroup
                logger.info("WebSocket disconnected in receive loop.")
                raise

            except Exception as e:
                # 1. Check for specific GenAI disconnect messages
                error_msg = str(e)
                if "disconnect" in error_msg or "Cannot call 'receive'" in error_msg or "closed" in error_msg:
                    logger.info(f"Gemini session closed by client/network: {error_msg}")
                    raise e
                else:
                    logger.error(f"Error in receive loop: {e}")
                    # 🏰 BASTION PROTOCOL: Fail Fast.
                    # If we encounter an unknown error, we MUST NOT swallow it with break.
                    # We must raise it to trigger the TaskGroup cancellation.
                    raise e

            logger.info("Gemini session.receive() iterator exhausted. Re-entering loop to listen for next turn...")

    except (WebSocketDisconnect, ConnectionClosed, ConnectionClosedOK, ConnectionClosedError) as e:
        logger.info(f"Client disconnected (receive_from_gemini): {e}")
        # Re-raise to trigger TaskGroup cancellation of other tasks
        raise e

    except Exception as e:
        logger.error(f"Error receiving from Gemini: {e}")
        # 🏰 BASTION: Fail Fast. If audio downstream dies, the session is deaf. Kill it.
        raise e
