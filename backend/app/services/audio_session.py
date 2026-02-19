import asyncio
import base64
import logging
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# 16000 Hz * 2 bytes = 32000 bytes/sec
# 3200 bytes = 100ms
AUDIO_BUFFER_THRESHOLD = 3200

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
            # Client sends raw PCM audio bytes
            # Typically 256 bytes per packet from client (8ms)
            data = await websocket.receive_bytes()
            if not data:
                logger.warning("Received empty data from client.")
                continue

            # Prepend carry_over from previous iteration
            if carry_over:
                data = carry_over + data
                carry_over.clear()

            # Handle odd number of bytes (alignment check)
            if len(data) % 2 != 0:
                # Save the last byte for next time
                carry_over.extend(data[-1:])
                # Process the rest
                data = data[:-1]

            packet_count += 1
            if packet_count % 100 == 0:
                logger.info(f"Client -> Gemini: Received {packet_count} packets. Buffer size: {len(audio_buffer)}")

            audio_buffer.extend(data)

            # Buffer up to ~100ms (3200 bytes) to ensure efficient streaming
            if len(audio_buffer) >= AUDIO_BUFFER_THRESHOLD:
                # logger.debug(f"Sending {len(audio_buffer)} bytes to Gemini")
                await session.send(input={"data": bytes(audio_buffer), "mime_type": "audio/pcm;rate=16000"})
                audio_buffer.clear()
                logger.info(f"Client -> Gemini: Buffer flushed. New size: {len(audio_buffer)}")

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

async def receive_from_gemini(websocket: WebSocket, session):
    """
    Task B: Gemini -> Client
    Receives from Gemini and sends to WebSocket as custom JSON.
    """
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
                        # logger.debug(f"Gemini -> Client: Audio chunk ({len(part.inline_data.data)} bytes)")
                        b64_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio",
                            "data": b64_data
                        })

                    # Handle Text (if interleaved)
                    if part.text:
                        logger.info(f"Gemini -> Client: Text: {part.text[:50]}...")
                        await websocket.send_json({
                            "type": "text",
                            "data": part.text
                        })

            # Handle turn completion
            if server_content.turn_complete:
                logger.info("Gemini -> Client: Turn complete signal.")
                await websocket.send_json({"type": "turn_complete"})

        logger.warning("🚨 ALERTA: session.receive() ha terminado el bucle")

    except Exception as e:
        logger.error(f"Error receiving from Gemini: {e}")
        raise
