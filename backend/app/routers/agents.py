from fastapi import APIRouter, HTTPException, status, Response, Header
from typing import List, Optional, Any
from pydantic import BaseModel

from ..models.graph import AgentNode
from ..services.agent_service import AgentService
from ..services.ritual_service import RitualService, RitualMessage

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Service initialization
agent_service = AgentService()
ritual_service = RitualService()

class CreateAgentRequest(BaseModel):
    name: str
    role: str
    base_instruction: str
    traits: dict = {}
    tags: List[str] = []

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
        raise HTTPException(status_code=500, detail=str(e))

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
            traits=request.traits,
            tags=request.tags
        )
        return new_agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ritual", response_model=RitualFlowResponse, status_code=status.HTTP_200_OK)
async def conduct_ritual(history: List[RitualMessage], response: Response, accept_language: str = Header(default="en")):
    """
    The Incantation Ritual:
    A conversation with the Soul Forge to design a new agent.
    If 'is_complete' is true, the agent is automatically created and returned with status 201.
    If false, the next question is returned with status 200.
    """
    try:
        ritual_result = await ritual_service.process_ritual(history, locale=accept_language)

        if ritual_result.is_complete and ritual_result.agent_data:
            # Auto-save the agent
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
                traits=traits,
                tags=["ritual-born"]
            )

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
        raise HTTPException(status_code=500, detail=f"Ritual Failed: {str(e)}")
