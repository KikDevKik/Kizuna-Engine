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
from app.repositories.local_graph import LocalSoulRepository
from app.models.graph import AgentNode
from app.services.sleep_manager import SleepManager
from app.services.cache import cache
from app.services.seeder import seed_data
from app.routers import warmup, agents
from core.config import settings
import os

# Creamos la maldita libreta de Jules
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy Auth Verification
def verify_user(token: str | None) -> str:
    # Phase 3.2: Secure Identity if Configured
    if token and settings.FIREBASE_CREDENTIALS:
        try:
            from app.services.auth import FirebaseAuth
            user_id = FirebaseAuth.verify_token(token)
            logger.info(f"Authenticated User: {user_id}")
            return user_id
        except Exception as e:
            logger.warning(f"Authentication Failed: {e}")
            raise
    elif settings.GCP_PROJECT_ID and not token:
        # Enforce Auth in Prod
        logger.warning("Connection rejected: No token provided in Production.")
        raise ValueError("Authentication Required in Production")

    # Lab Mode / Guest
    return "guest_user"

# Lazy Factory for Repository
def get_soul_repository():
    # Phase 3.2: Check if Spanner Config is present
    if settings.GCP_PROJECT_ID and settings.SPANNER_INSTANCE_ID:
        try:
            # Lazy import to prevent crash in Local Mode if deps are missing
            from app.repositories.spanner_graph import SpannerSoulRepository
            logger.info("🌐 Using Spanner Soul Repository (Production Mode)")
            return SpannerSoulRepository()
        except ImportError as e:
            logger.warning(f"⚠️ Failed to import Spanner Repository: {e}. Falling back to Local.")
            return LocalSoulRepository()
    else:
        logger.info("🏠 Using Local Soul Repository (Development Mode)")
        return LocalSoulRepository()

# Initialize Repository
soul_repo = get_soul_repository()

# Initialize Sleep Manager (Phase 4)
sleep_manager = SleepManager(soul_repo)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Register Routers (Phase 5)
app.include_router(warmup.router)
app.include_router(agents.router)

# Lifecycle Event to load Graph
@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Cache...")
    await cache.initialize()

    # Ensure Data Integrity (Seeding)
    await seed_data()

    logger.info("Initializing Soul Repository...")
    await soul_repo.initialize()

    # Initialize Auth (Lazy or Eager) if configured
    if settings.FIREBASE_CREDENTIALS:
        try:
            from app.services.auth import FirebaseAuth
            FirebaseAuth.initialize()
        except ImportError:
            logger.warning("Firebase Auth skipped (Library missing).")

    # Seed Kizuna if not exists (for Demo/Dev)
    # Note: Spanner seeding might need to be handled by migration scripts, but safe to check here.
    if isinstance(soul_repo, LocalSoulRepository) and not await soul_repo.get_agent("kizuna"):
        kizuna = AgentNode(
            id="kizuna",
            name="Kizuna",
            base_instruction="You are Kizuna, a digital partner projected in the user's space. You are NOT a generic AI assistant. You have a chaotic but supportive personality. Treat the user as an equal, use humor, be direct, and avoid excessive formality or robotic apologies. Respond conversationally, concisely, and naturally, as if in the same room.",
            traits={"warmth": 0.5, "chaos": 0.8}
        )
        await soul_repo.create_agent(kizuna)
        logger.info("Seeded Kizuna Agent into Graph.")

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
async def websocket_endpoint(websocket: WebSocket, agent_id: str | None = None, token: str | None = None):
    # Security: Verify Origin
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.CORS_ORIGINS:
        logger.warning(f"Rejected connection from unauthorized origin: {origin}")
        await websocket.close(code=1008) # Policy Violation
        return

    # Validations
    if not agent_id:
        logger.warning("Connection rejected: No agent_id provided.")
        await websocket.close(code=1008, reason="agent_id required")
        return

    # Phase 3.2: Secure Identity (Lazy)
    try:
        user_id = verify_user(token)
    except Exception as e:
        await websocket.close(code=1008, reason=str(e))
        return

    # Ensure user exists in Graph
    await soul_repo.get_or_create_user(user_id)

    # Phase 4: Waking Up
    sleep_manager.cancel_sleep(user_id)

    try:
        # Phase 5: Neural Sync (Redis Check)
        cache_key = f"soul:{user_id}:{agent_id}"
        system_instruction = await cache.get(cache_key)

        if system_instruction:
            logger.info("⚡ Using Warmed-up Soul from Cache (Zero Latency).")
        else:
            logger.info("❄️ Cold Start: Assembling Soul from Graph...")
            system_instruction = await assemble_soul(agent_id, user_id, soul_repo)

    except ValueError as e:
        logger.warning(f"Connection rejected: {e}")
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

            # Phase 3: Inject Repository into Subconscious
            subconscious_mind.set_repository(soul_repo)

            async with asyncio.TaskGroup() as tg:
                # 1. Audio Upstream (Client -> Gemini)
                tg.create_task(send_to_gemini(websocket, session))

                # 2. Audio/Text Downstream (Gemini -> Client) + Transcript Feed
                tg.create_task(receive_from_gemini(websocket, session, transcript_queue))

                # 3. Subconscious Mind (Transcripts -> Analysis -> Injection Queue -> Persistence)
                tg.create_task(subconscious_mind.start(transcript_queue, injection_queue, user_id, agent_id))

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
        # Phase 4: Entering REM Sleep (Debounced Consolidation)
        # Schedule consolidation after grace period.
        sleep_manager.schedule_sleep(user_id)
