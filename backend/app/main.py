from dotenv import load_dotenv
load_dotenv()

import asyncio
import base64
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.genai import types

from app.services.gemini_live import gemini_service
from core.config import settings


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

@app.get("/health")
async def health_check():
    return {"status": "Kizuna Engine Online"}

async def send_to_gemini(websocket: WebSocket, session):
    """
    Task A: Client -> Gemini
    Reads audio bytes from WebSocket and sends to Gemini session.
    """
    try:
        while True:
            # Client sends raw PCM audio bytes
            data = await websocket.receive_bytes()
            if not data:
                # Usually receive_bytes raises disconnect or returns data
                logger.warning("Received empty data from client.")
                continue

            # Send to Gemini with explicit mime_type as requested
            # sending raw PCM 16kHz audio chunks
            await session.send(input={"data": data, "mime_type": "audio/pcm;rate=16000"})

    except WebSocketDisconnect:
        logger.info("Client disconnected (send_to_gemini)")
        # Start cancellation of the other task via TaskGroup logic (raising exception)
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
                        b64_data = base64.b64encode(part.inline_data.data).decode('utf-8')
                        await websocket.send_json({
                            "type": "audio",
                            "data": b64_data
                        })

                    # Handle Text (if interleaved)
                    if part.text:
                        await websocket.send_json({
                            "type": "text",
                            "data": part.text
                        })

            # Handle turn completion
            if server_content.turn_complete:
                await websocket.send_json({"type": "turn_complete"})

    except Exception as e:
        logger.error(f"Error receiving from Gemini: {e}")
        raise

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established.")

    try:
        async with gemini_service.connect() as session:
            logger.info("Gemini session started.")

            # Manage bidirectional streams concurrently
            # If either task fails (e.g. disconnect), the TaskGroup will cancel the other.
            async with asyncio.TaskGroup() as tg:
                tg.create_task(send_to_gemini(websocket, session))
                tg.create_task(receive_from_gemini(websocket, session))

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
        logger.info("WebSocket session closed.")
