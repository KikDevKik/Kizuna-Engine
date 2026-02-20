from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel

from ..models.graph import AgentNode
from ..services.agent_service import AgentService

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Service initialization
# In a real app we might inject this, but for now we instantiate directly or use a singleton
agent_service = AgentService()

class CreateAgentRequest(BaseModel):
    name: str
    role: str
    base_instruction: str
    traits: dict = {}
    tags: List[str] = []

@router.get("/", response_model=List[AgentNode])
async def list_agents():
    """
    List all available agents.
    """
    try:
        return agent_service.list_agents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=AgentNode, status_code=status.HTTP_201_CREATED)
async def create_agent(request: CreateAgentRequest):
    """
    Create a new agent.
    """
    try:
        new_agent = agent_service.create_agent(
            name=request.name,
            role=request.role,
            base_instruction=request.base_instruction,
            traits=request.traits,
            tags=request.tags
        )
        return new_agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
