from fastapi import APIRouter, Header, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
from app.services.soul_assembler import assemble_soul
from app.services.cache import cache
from app.repositories.base import SoulRepository
from app.dependencies import get_repository
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/warmup", tags=["Neural Sync"])

class WarmupRequest(BaseModel):
    agent_id: str

async def perform_warmup(user_id: str, agent_id: str, repo: SoulRepository):
    """
    Background Task: Assemble Soul and Cache it.
    Uses the injected singleton repository to avoid redundant I/O.
    """
    try:
        # Heavy computation: GQL + Logic
        system_instruction = await assemble_soul(agent_id, user_id, repo)

        # Cache in Redis (TTL 60s - enough for WS handshake to follow)
        cache_key = f"soul:{user_id}:{agent_id}"
        await cache.set(cache_key, system_instruction, ttl=60)

        logger.info(f"🔥 Soul Warmed Up for {user_id} -> {agent_id}. Cached.")
    except Exception as e:
        logger.error(f"❌ Warmup Failed: {e}")

@router.post("/")
async def warmup_soul(
    request: WarmupRequest,
    background_tasks: BackgroundTasks,
    authorization: str = Header(None), # Bearer Token
    repo: SoulRepository = Depends(get_repository)
):
    """
    Pre-calculates the Agent's Soul (System Instruction) based on User History.
    Called by Frontend on page load.
    """
    # 1. Authenticate (Lazy Logic)
    user_id = "guest_user"
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if settings.FIREBASE_CREDENTIALS:
            try:
                from app.services.auth import FirebaseAuth
                user_id = FirebaseAuth.verify_token(token)
            except ImportError:
                # Should not happen if credentials exist unless lib is missing
                logger.warning("Firebase credentials present but library missing.")
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid Token")
    elif settings.GCP_PROJECT_ID:
        # Enforce strict auth in Prod
        raise HTTPException(status_code=401, detail="Authentication Required")

    # 2. Trigger Background Warm-up (Non-blocking response)
    background_tasks.add_task(perform_warmup, user_id, request.agent_id, repo)

    return {"status": "warming_up", "agent_id": request.agent_id, "user_id": user_id}
