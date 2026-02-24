from dotenv import load_dotenv

load_dotenv()

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.services.session_manager import SessionManager
from app.repositories.local_graph import LocalSoulRepository
from app.models.graph import AgentNode
from app.services.sleep_manager import SleepManager
from app.services.time_skip import TimeSkipService
from app.services.cache import cache
from app.services.agent_service import agent_service
from app.services.seeder import seed_data
from app.routers import warmup, agents, bio, system
from app.dependencies import soul_repo
from core.config import settings

# Creamos la maldita libreta de Jules
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sleep Manager (Phase 4)
sleep_manager = SleepManager(soul_repo)

# Initialize Time Skip Service (The Architect's Temporal Engine)
time_skip_service = TimeSkipService(soul_repo)

# Initialize Session Manager (The Architect's Modularization)
session_manager = SessionManager(soul_repo, sleep_manager, time_skip_service)


# Lifecycle Event to load Graph
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Cache...")
    await cache.initialize()

    # Neural Sync: Warm up agents
    await agent_service.warm_up_agents()

    # Neural Sync: Restore pending sleep cycles
    await sleep_manager.restore_state()

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
    if isinstance(soul_repo, LocalSoulRepository) and not await soul_repo.get_agent(
        "kizuna"
    ):
        kizuna = AgentNode(
            id="kizuna",
            name="Kizuna",
            base_instruction="You are Kizuna, a digital partner projected in the user's space. You are NOT a generic AI assistant. You have a chaotic but supportive personality. Treat the user as an equal, use humor, be direct, and avoid excessive formality or robotic apologies. Respond conversationally, concisely, and naturally, as if in the same room.",
            traits={"warmth": 0.5, "chaos": 0.8},
        )
        await soul_repo.create_agent(kizuna)
        logger.info("Seeded Kizuna Agent into Graph.")

    yield

    # Shutdown
    await sleep_manager.shutdown()


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

# Register Routers (Phase 5)
app.include_router(warmup.router)
app.include_router(agents.router)
app.include_router(bio.router)
app.include_router(system.router)

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
async def websocket_endpoint(
    websocket: WebSocket, agent_id: str | None = None, token: str | None = None
):
    # Delegate to Session Manager
    await session_manager.handle_session(websocket, agent_id, token)
