from fastapi import APIRouter, HTTPException, Depends
from app.repositories.base import SoulRepository
from app.repositories.local_graph import LocalSoulRepository
from app.dependencies import get_repository, get_current_user
from app.models.graph import SystemConfigNode
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system", tags=["System Control"])

@router.get("/config", response_model=SystemConfigNode)
async def get_system_config(
    repo: SoulRepository = Depends(get_repository),
    current_user: str = Depends(get_current_user)
):
    """
    Returns the current System Configuration (Core Directive & Affinity Matrix).
    """
    try:
        return await repo.get_system_config()
    except Exception as e:
        logger.error(f"Failed to fetch system config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config", response_model=SystemConfigNode)
async def update_system_config(
    config: SystemConfigNode,
    repo: SoulRepository = Depends(get_repository),
    current_user: str = Depends(get_current_user)
):
    """
    Updates the System Configuration.
    """
    try:
        await repo.update_system_config(config)
        return config
    except Exception as e:
        logger.error(f"Failed to update system config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/purge-memories")
async def purge_memories(
    repo: SoulRepository = Depends(get_repository),
    current_user: str = Depends(get_current_user)
):
    """
    THE GREAT REBIRTH: Factory Reset.
    Wipes all nodes and edges.
    """
    # Safety Check: Only Local Graph for now
    if not isinstance(repo, LocalSoulRepository):
        raise HTTPException(status_code=501, detail="Purge only supported for Local Graph simulation")

    try:
        await repo.purge_all_memories()
        return {"status": "success", "message": "The Great Rebirth Complete. Reality has been reset."}
    except Exception as e:
        logger.error(f"Failed to purge memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
