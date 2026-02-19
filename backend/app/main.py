from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.services.gemini_live import gemini_service
from app.services.audio_session import send_to_gemini, receive_from_gemini
from core.config import settings

# Creamos la maldita libreta de Jules
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

@app.get("/health")
async def health_check():
    return {"status": "Kizuna Engine Online"}


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
