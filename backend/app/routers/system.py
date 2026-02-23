from fastapi import APIRouter, HTTPException, Depends
from app.repositories.base import SoulRepository
from app.repositories.local_graph import LocalSoulRepository
from app.dependencies import get_repository
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["System Control"])

@router.delete("/purge-memories")
async def purge_memories(repo: SoulRepository = Depends(get_repository)):
    """
    SCORCHED EARTH: Wipes all episodic memory and dreams.
    This action is irreversible.
    """
    # Safety Check: Only Local Graph for now
    if not isinstance(repo, LocalSoulRepository):
        raise HTTPException(status_code=501, detail="Purge only supported for Local Graph simulation")

    try:
        await repo.purge_all_memories()
        return {"status": "success", "message": "All memories purged. The slate is clean."}
    except Exception as e:
        logger.error(f"Failed to purge memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
