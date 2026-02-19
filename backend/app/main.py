from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.services.gemini_live import gemini_service
from app.services.audio_session import send_to_gemini, receive_from_gemini, send_injections_to_gemini
from app.services.soul_assembler import assemble_soul
from app.services.subconscious import subconscious_mind
from core.config import settings

# Creamos la maldita libreta de Jules
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "Kizuna Engine Online"}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket, agent_id: str | None = None):
    # Security: Verify Origin
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.CORS_ORIGINS:
        logger.warning(f"Rejected connection from unauthorized origin: {origin}")
        await websocket.close(code=1008) # Policy Violation
        return

    # Phase 1: Dynamic Soul Assembly
    if not agent_id:
        logger.warning("Connection rejected: No agent_id provided.")
        await websocket.close(code=1008, reason="agent_id required")
        return

    try:
        # Load agent and assemble system instruction
        system_instruction = await assemble_soul(agent_id)
    except FileNotFoundError:
        logger.warning(f"Connection rejected: Agent {agent_id} not found.")
        await websocket.close(code=1008, reason="Agent not found")
        return
    except Exception as e:
        logger.error(f"Error assembling soul: {e}")
        await websocket.close(code=1011, reason="Internal Soul Error")
        return

    await websocket.accept()
    logger.info(f"WebSocket connection established from origin: {origin} for Agent: {agent_id}")

    try:
        async with gemini_service.connect(system_instruction=system_instruction) as session:
            logger.info(f"Gemini session started for {agent_id}.")

            # Phase 2: Initialize Subconscious Channels
            transcript_queue = asyncio.Queue()
            injection_queue = asyncio.Queue()

            # Manage bidirectional streams and subconscious concurrently
            # If either task fails (e.g. disconnect), the TaskGroup will cancel the others.
            async with asyncio.TaskGroup() as tg:
                # 1. Audio Upstream (Client -> Gemini)
                tg.create_task(send_to_gemini(websocket, session))

                # 2. Audio/Text Downstream (Gemini -> Client) + Transcript Feed
                tg.create_task(receive_from_gemini(websocket, session, transcript_queue))

                # 3. Subconscious Mind (Transcripts -> Analysis -> Injection Queue)
                tg.create_task(subconscious_mind.start(transcript_queue, injection_queue))

                # 4. Injection Upstream (Injection Queue -> Gemini)
                tg.create_task(send_injections_to_gemini(session, injection_queue))

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
