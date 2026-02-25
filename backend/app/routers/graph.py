from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.repositories.base import SoulRepository
from app.repositories.local_graph import LocalSoulRepository
from app.dependencies import get_repository, get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["Graph Interop"])

@router.get("/export")
async def export_graph(
    repo: SoulRepository = Depends(get_repository),
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Export the current Knowledge Graph as standard JSON-LD.
    Compatible with MyWorld and other semantic engines.
    """
    if not isinstance(repo, LocalSoulRepository):
         raise HTTPException(status_code=501, detail="Export only supported for Local Graph simulation")

    try:
        return await repo.export_to_json_ld()
    except Exception as e:
        logger.error(f"Graph Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_graph(
    data: Dict[str, Any],
    repo: SoulRepository = Depends(get_repository),
    current_user: str = Depends(get_current_user)
):
    """
    Import a JSON-LD graph state.
    WARNING: This performs a full wipe and replace of the local graph.
    A backup is automatically created before overwriting.
    """
    if not isinstance(repo, LocalSoulRepository):
         raise HTTPException(status_code=501, detail="Import only supported for Local Graph simulation")

    try:
        await repo.import_from_json_ld(data)
        return {"status": "success", "message": "Graph imported successfully. Reality has been rewritten."}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        # Backup failure or critical error
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        logger.error(f"Graph Import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
