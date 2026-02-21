import asyncio
import base64
import logging
import json
from fastapi import WebSocket, WebSocketDisconnect

# Try importing types for robust multimodal handling
try:
    from google.genai import types
except ImportError:
    types = None

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


async def send_to_gemini(websocket: WebSocket, session):
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

    except WebSocketDisconnect:
        logger.info("Client disconnected (send_to_gemini)")
        # Send remaining audio if any?
        # Usually if user disconnects we don't care, but for completeness:
        if len(audio_buffer) > 0:
             try:
                 await session.send(input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"})
             except Exception:
                 pass
        raise
    except Exception as e:
        logger.error(f"Error sending to Gemini: {e}")
        raise

async def receive_from_gemini(websocket: WebSocket, session, transcript_queue: asyncio.Queue | None = None):
    """
    Task B: Gemini -> Client + Subconscious
    Receives from Gemini and sends to WebSocket as custom JSON.
    Also sends text transcripts to the Subconscious Mind via transcript_queue.
    """
    try:
        while True:
            try:
                async for response in session.receive():
                    if response.server_content is None:
                        continue

                    server_content = response.server_content
                    model_turn = server_content.model_turn

                    if model_turn:
                        for part in model_turn.parts:
                            # Handle Audio
                            if part.inline_data:
                                # part.inline_data.data is bytes
                                # Optimize: Send raw binary directly to avoid Base64 overhead
                                await websocket.send_bytes(part.inline_data.data)

                            # Handle Text (if interleaved or final transcript)
                            if part.text:
                                logger.info(f"Gemini -> Client: Text: {part.text[:50]}...")
                                await websocket.send_json({
                                    "type": "text",
                                    "data": part.text
                                })

                                # Feed the Subconscious Mind
                                if transcript_queue:
                                    try:
                                        transcript_queue.put_nowait(part.text)
                                    except Exception as e:
                                        logger.warning(f"Failed to queue transcript: {e}")

                    # Handle turn completion
                    if server_content.turn_complete:
                        logger.info("Gemini -> Client: Turn complete signal.")
                        await websocket.send_json({"type": "turn_complete"})

            except asyncio.CancelledError:
                logger.info("Receive loop cancelled (Graceful Shutdown).")
                break

            except Exception as e:
                # 1. Check for specific GenAI disconnect messages
                error_msg = str(e)
                if "disconnect" in error_msg or "Cannot call 'receive'" in error_msg:
                    logger.info(f"Gemini session closed by client/network: {error_msg}")
                    break
                else:
                    logger.error(f"Error in receive loop: {e}")
                    raise

            logger.info("Gemini session.receive() iterator exhausted. Re-entering loop to listen for next turn...")

    except Exception as e:
        logger.error(f"Error receiving from Gemini: {e}")
        raise
