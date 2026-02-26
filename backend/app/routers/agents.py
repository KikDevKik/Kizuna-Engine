from fastapi import APIRouter, HTTPException, status, Response, Header, Depends
from typing import List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import logging

from ..models.graph import AgentNode, GraphEdge
from ..repositories.base import SoulRepository
from ..services.agent_service import AgentService
from ..services.ritual_service import RitualService, RitualMessage
from ..dependencies import get_current_user, get_repository
import random

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

class HollowForgeRequest(BaseModel):
    aesthetic_description: str = Field(..., min_length=10, max_length=1000, description="A description of the agent's vibe, appearance, or theme.")

class StrangerNode(BaseModel):
    id: str
    description: str
    tempAlias: str
    visualHint: str
    is_nemesis: bool = False
    is_gossip: bool = False

class RitualFlowResponse(BaseModel):
    is_complete: bool
    message: Optional[str] = None
    agent: Optional[AgentNode] = None

@router.get("/", response_model=List[AgentNode])
async def list_agents(
    user_id: str = Depends(get_current_user),
    repository: SoulRepository = Depends(get_repository)
):
    """
    List "My Agents" - only those the current user has interacted with (InteractedWith Edge).
    """
    try:
        # 1. Fetch all agents from filesystem
        all_agents = await agent_service.list_agents()

        # 2. Fetch interaction edges for the current user
        # We need to find agents where an 'InteractedWith' edge exists with the user.
        # Since LocalSoulRepository.record_interaction creates (User -> Agent),
        # we look for edges where source_id == user_id.

        # Use get_edges if available (LocalSoulRepository)
        if hasattr(repository, 'get_edges'):
            edges = await repository.get_edges(source_id=user_id, type="interactedWith")
            interacted_agent_ids = {edge.target_id for edge in edges}
        else:
            # Fallback for other repositories (should not happen in this phase)
            # Just return all agents if we can't filter
            logger.warning("Repository does not support get_edges filtering. Returning all agents.")
            return all_agents

        # 3. Filter the list (InteractedWith)
        my_agents = [
            agent for agent in all_agents
            if agent.id in interacted_agent_ids
        ]

        # 4. Roster Eviction: Remove Nemesis (Module 1.5)
        nemesis_agents = await repository.get_nemesis_agents(user_id)
        nemesis_ids = {a.id for a in nemesis_agents}

        my_agents = [a for a in my_agents if a.id not in nemesis_ids]

        return my_agents

    except Exception as e:
        logger.exception("Error listing agents")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/strangers", response_model=List[StrangerNode])
async def list_strangers(
    user_id: str = Depends(get_current_user),
    repository: SoulRepository = Depends(get_repository)
):
    """
    List "Stranger" candidates for District Zero.
    Includes Nemesis agents (hidden threats) and Gossiped agents (spawned by others).
    """
    try:
        results = []

        # 1. Fetch Nemesis Agents
        nemesis_agents = await repository.get_nemesis_agents(user_id)
        for agent in nemesis_agents:
            results.append(StrangerNode(
                id=agent.id,
                description=agent.base_instruction[:150] + "...", # Snippet
                tempAlias=f"{agent.name} (Hostil)",
                visualHint="bg-alert-red/10", # Signal Red
                is_nemesis=True,
                is_gossip=False
            ))

        # 2. Fetch Gossip Candidates
        gossip_agents = await repository.get_gossip_candidates(user_id)
        for agent in gossip_agents:
            # Try to get context from traits if available
            vibe = agent.base_instruction
            if "Aesthetic/Vibe:" in vibe:
                vibe = vibe.split("Aesthetic/Vibe:")[-1].strip()

            results.append(StrangerNode(
                id=agent.id,
                description=vibe,
                tempAlias=f"Unknown_0x{agent.id[:4].upper()}",
                visualHint="bg-purple-500/10",
                is_nemesis=False,
                is_gossip=True
            ))

        # Note: We return ONLY backend-managed strangers.
        # The frontend will merge these with static Enigma Shells if needed,
        # or use these primarily.

        return results

    except Exception as e:
        logger.exception("Error listing strangers")
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

@router.post("/forge_hollow", response_model=AgentNode, status_code=status.HTTP_201_CREATED)
async def forge_hollow_agent(
    request: HollowForgeRequest,
    repository: SoulRepository = Depends(get_repository)
):
    """
    Forges a procedural 'Stranger' agent using Gemini (Hollow Forging Protocol).
    Generates a full profile, voice, and false memories based on an aesthetic description.
    """
    try:
        # 1. Forge the Soul (Generate Content)
        agent_node, memories = await agent_service.forge_hollow_agent(request.aesthetic_description)

        # 2. Bind the Soul to Matter (Save File)
        saved_agent = await agent_service.create_agent(
            name=agent_node.name,
            role=agent_node.role,
            base_instruction=agent_node.base_instruction,
            voice_name=agent_node.voice_name,
            traits=agent_node.traits,
            tags=agent_node.tags,
            native_language=agent_node.native_language,
            known_languages=agent_node.known_languages
        )

        # 3. Sync with Graph Database (In-Memory)
        if hasattr(repository, 'create_agent'):
            await repository.create_agent(saved_agent)

        # 4. Inject False Memories (The Past)
        for mem in memories:
            # We use saved_agent.id as both user and agent to denote "Self-Memory"
            # This creates an 'ExperiencedEdge' from Agent -> Episode
            await repository.save_episode(
                user_id=saved_agent.id,
                agent_id=saved_agent.id,
                summary=mem.summary,
                valence=mem.emotional_valence
            )

        # 5. Module 5: The Gossip Protocol (Web Forging)
        try:
            # Query for existing agents (candidates)
            # list_agents returns ALL agents.
            all_agents = await agent_service.list_agents()
            candidates = [a for a in all_agents if a.id != saved_agent.id]

            if candidates:
                # Pick ONE victim
                target = random.choice(candidates)

                # Pick ONE relation
                relations = ["Knows", "OwesDebtTo", "FormerAlly", "Distrusts", "SecretlyAdmires"]
                rel_type = random.choice(relations)

                # Create the edge
                # We use a generic GraphEdge with 'type' set to the relation
                # Note: GraphEdge requires lowerCamelCase usually for ontological purity, but we use PascalCase for these display types
                # Let's map to standardized predicates if strictness matters, but "Knows" is fine.
                edge = GraphEdge(
                    source_id=saved_agent.id,
                    target_id=target.id,
                    type="gossip_connection", # Use a specific type for query/filtering if needed, or generic 'relatedTo'
                    properties={
                        "relation": rel_type,
                        "context": f"Procedurally generated connection: {saved_agent.name} {rel_type} {target.name}"
                    }
                )

                if hasattr(repository, 'create_edge'):
                    await repository.create_edge(edge)
                    logger.info(f"🕸️ Gossip Protocol: Linked {saved_agent.name} -> {rel_type} -> {target.name}")
        except Exception as e:
            logger.error(f"Gossip Protocol failed: {e}")

        logger.info(f"Hollow Forging Complete: {saved_agent.name} ({saved_agent.id}) with {len(memories)} memories.")
        return saved_agent

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception(f"Error forging hollow agent")
        raise HTTPException(status_code=500, detail="Soul Forge Malfunction")

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    repository: SoulRepository = Depends(get_repository)
):
    """
    Delete an agent by ID.
    HOLLOW PRESERVATION RULE: Cannot delete agents with 'Gossip_Source' edges or 'gossip' tag.
    """
    try:
        # 1. Fetch Agent (Cache/File)
        agent = await agent_service.get_agent(agent_id)
        if not agent:
             raise HTTPException(status_code=404, detail="Agent not found")

        # 2. Check for Hollow Preservation (Tags)
        if "hollow" in agent.tags or "gossip" in agent.tags:
             logger.warning(f"🛡️ Hollow Preservation: Blocked deletion of {agent.name} (Tags: {agent.tags})")
             raise HTTPException(status_code=403, detail="Hollow Preservation: This agent is protected by the Gossip Protocol.")

        # 3. Check for Hollow Preservation (Graph Edges)
        if hasattr(repository, 'get_edges'):
            # Check if this agent is the TARGET of a Gossip_Source edge (meaning it was spawned by gossip)
            # OR if it is the SOURCE (meaning it spawned someone, less critical but potentially important)
            # The rule is: "Any Agent node with a Gossip_Source edge... is strictly EXEMPT"

            # Check Incoming Gossip (Spawned by someone)
            incoming = await repository.get_edges(target_id=agent_id, type="Gossip_Source")
            if incoming:
                logger.warning(f"🛡️ Hollow Preservation: Blocked deletion of {agent.name} (Incoming Gossip Edge)")
                raise HTTPException(status_code=403, detail="Hollow Preservation: This agent is a node in a Gossip Chain.")

            # Check Outgoing Gossip (Spawned someone)
            outgoing = await repository.get_edges(source_id=agent_id, type="Gossip_Source")
            if outgoing:
                 logger.warning(f"🛡️ Hollow Preservation: Blocked deletion of {agent.name} (Outgoing Gossip Edge)")
                 raise HTTPException(status_code=403, detail="Hollow Preservation: This agent is a source of active rumors.")

        # 4. Proceed with Deletion
        success = await agent_service.delete_agent(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found during deletion")
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
    archetype: Optional[str] = None,
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

            # Ontology Phase 1: Link Archetype
            if archetype:
                try:
                    # Check if archetype exists (or create stub)
                    arc = await repository.get_archetype(archetype)
                    if not arc:
                        arc = await repository.create_archetype(
                            name=archetype,
                            description=f"Archetype: {archetype}",
                            triggers={}
                        )
                    await repository.link_agent_archetype(new_agent.id, arc.id)
                    logger.info(f"Linked Agent {new_agent.name} to Archetype {archetype}")
                except Exception as e:
                    logger.error(f"Failed to link archetype: {e}")

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
