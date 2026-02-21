from fastapi import APIRouter, HTTPException, status, Response, Header, Depends
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import logging

from ..models.graph import AgentNode
from ..repositories.base import SoulRepository
from ..services.agent_service import AgentService
from ..services.ritual_service import RitualService, RitualMessage
from ..dependencies import get_current_user, get_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"], dependencies=[Depends(get_current_user)])

# Service initialization
agent_service = AgentService()
ritual_service = RitualService()

class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name of the agent (1-100 chars)")
    role: str = Field(..., min_length=1, max_length=100, description="Role of the agent (1-100 chars)")
    base_instruction: str = Field(..., min_length=1, max_length=5000, description="System prompt for the agent (1-5000 chars)")
    voice_name: Optional[str] = Field(default=None, description="Voice name for Gemini Live (e.g. Aoede, Kore, Puck, Charon, Fenrir)")
    traits: dict = Field(default_factory=dict, description="Key-value traits")
    tags: List[str] = Field(default_factory=list, max_length=20, description="List of tags (max 20)")
    native_language: str = Field(default="Unknown", description="Native language of the agent")
    known_languages: List[str] = Field(default_factory=list, description="List of languages the agent knows")

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag must be less than 50 characters')
        return v

    @field_validator('traits')
    @classmethod
    def validate_traits(cls, v):
        if len(v) > 20:
             raise ValueError('Too many traits (max 20)')
        for key, value in v.items():
            if len(str(key)) > 50:
                raise ValueError('Trait key must be less than 50 characters')
            if len(str(value)) > 200:
                raise ValueError('Trait value must be less than 200 characters')
        return v

class RitualFlowResponse(BaseModel):
    is_complete: bool
    message: Optional[str] = None
    agent: Optional[AgentNode] = None

@router.get("/", response_model=List[AgentNode])
async def list_agents():
    """
    List all available agents.
    """
    try:
        return await agent_service.list_agents()
    except Exception as e:
        logger.exception("Error listing agents")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/", response_model=AgentNode, status_code=status.HTTP_201_CREATED)
async def create_agent(request: CreateAgentRequest):
    """
    Create a new agent.
    """
    try:
        new_agent = await agent_service.create_agent(
            name=request.name,
            role=request.role,
            base_instruction=request.base_instruction,
            voice_name=request.voice_name,
            traits=request.traits,
            tags=request.tags,
            native_language=request.native_language,
            known_languages=request.known_languages
        )
        return new_agent
    except Exception as e:
        logger.exception(f"Error creating agent '{request.name}'")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str):
    """
    Delete an agent by ID.
    """
    try:
        success = await agent_service.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
         logger.exception(f"Error deleting agent '{agent_id}'")
         raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/ritual", response_model=RitualFlowResponse, status_code=status.HTTP_200_OK)
async def conduct_ritual(
    history: List[RitualMessage],
    response: Response,
    accept_language: str = Header(default="en"),
    user_id: str = Depends(get_current_user),
    repository: SoulRepository = Depends(get_repository)
):
    """
    The Incantation Ritual:
    A conversation with the Soul Forge to design a new agent.
    If 'is_complete' is true, the agent is automatically created and returned with status 201.
    If false, the next question is returned with status 200.
    """
    try:
        ritual_result = await ritual_service.process_ritual(history, locale=accept_language)

        if ritual_result.is_complete and ritual_result.agent_data:
            # Auto-save the agent (Filesystem)
            data = ritual_result.agent_data

            # Extract traits which might be list or dict
            raw_traits = data.get("traits", [])
            traits = {}
            if isinstance(raw_traits, list):
                traits = {t: True for t in raw_traits}
            elif isinstance(raw_traits, dict):
                traits = raw_traits

            # Combine traits and lore
            if "lore" in data:
                traits["lore"] = data["lore"]

            new_agent = await agent_service.create_agent(
                name=data.get("name", "Unnamed"),
                role=data.get("role", "Unknown"),
                base_instruction=data.get("base_instruction", ""),
                voice_name=data.get("voice_name"),
                traits=traits,
                tags=["ritual-born"],
                native_language=data.get("native_language", "Unknown"),
                known_languages=data.get("known_languages", [])
            )

            # Sync with SoulRepository (In-Memory/DB) to prevent "Agent not found"
            # This is critical for the subsequent resonance update
            try:
                # We assume the repository can handle 'create_agent' to update its internal cache
                # For LocalSoulRepository, this updates self.agents
                if hasattr(repository, 'create_agent'):
                    await repository.create_agent(new_agent)
            except Exception as e:
                logger.warning(f"Failed to sync new agent to SoulRepository: {e}")

            # Initial Affinity Injection
            initial_affinity = data.get("initial_affinity", 50)
            if initial_affinity is not None:
                try:
                    # Calculate delta dynamically to reach target (Robust to default changes)
                    # We first fetch the resonance (which creates it if missing)
                    resonance = await repository.get_resonance(user_id, new_agent.id)
                    current_affinity = resonance.affinity_level
                    target_affinity = float(initial_affinity)

                    # Only update if there is a significant difference
                    if abs(target_affinity - current_affinity) > 0.1:
                        delta = target_affinity - current_affinity
                        await repository.update_resonance(user_id, new_agent.id, delta)
                        logger.info(f"Initialized affinity for {new_agent.name} to {initial_affinity} (Delta: {delta})")
                except Exception as e:
                    logger.error(f"Failed to set initial affinity: {e}")

            response.status_code = status.HTTP_201_CREATED
            return RitualFlowResponse(
                is_complete=True,
                agent=new_agent
            )
        else:
            return RitualFlowResponse(
                is_complete=False,
                message=ritual_result.message
            )

    except Exception as e:
        logger.exception("Error in ritual process")
        raise HTTPException(status_code=500, detail="Internal Ritual Error")
