from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.core.config import settings
import logging

# Configure logging
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
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message: {data}")
            # Echo the message back
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")
        await websocket.close()
