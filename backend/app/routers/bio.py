from fastapi import APIRouter, Request
from app.core.rate_limiter import limiter
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from ..services.subconscious import subconscious_mind
from ..dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/bio",
    tags=["bio-signals"],
    dependencies=[Depends(get_current_user)]
)

class BioSignalRequest(BaseModel):
    bpm: float
    # Future: eda, hrv, etc.

@limiter.limit("60/minute")
@router.post("/submit")
async def submit_bio_signal(request: Request, signal: BioSignalRequest, user_id: str = Depends(get_current_user)):
    """
    Ingest Bio-Signals (Heart Rate, etc.) to influence the Subconscious Mind.
    """
    await subconscious_mind.process_bio_signal(user_id, signal.model_dump())
    return {"status": "received", "signal": signal}
