from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from ..models.graph import (
    UserNode, AgentNode, ResonanceEdge, MemoryEpisodeNode, FactNode,
    DreamNode, ArchetypeNode, GlobalDreamNode, CollectiveEventNode,
    GraphEdge
)

class SoulRepository(ABC):
    """
    Abstract interface for the Soul Evolution system's memory layer.
    This will be implemented by:
    1. LocalSoulRepository (Phase 3.1 - JSON/SQLite)
    2. SpannerSoulRepository (Phase 3.2 - Google Cloud Spanner)
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository (e.g. connect to DB, load JSON)."""
        pass

    @abstractmethod
    async def get_or_create_user(self, user_id: str, name: str = "Anonymous") -> UserNode:
        """Retrieve a user or create a new one."""
        pass

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Optional[AgentNode]:
        """Retrieve an agent by ID."""
        pass

    @abstractmethod
    async def get_resonance(self, user_id: str, agent_id: str) -> ResonanceEdge:
        """Retrieve the resonance (relationship) between a user and an agent."""
        pass

    @abstractmethod
    async def update_resonance(self, user_id: str, agent_id: str, delta: float) -> ResonanceEdge:
        """Update the affinity level of a resonance edge."""
        pass

    @abstractmethod
    async def save_episode(self, user_id: str, agent_id: str, summary: str, valence: float) -> MemoryEpisodeNode:
        """Save a new memory episode and link it to the user."""
        pass

    @abstractmethod
    async def get_relevant_facts(self, user_id: str, query: str, limit: int = 5) -> List[FactNode]:
        """Retrieve relevant facts for a user (RAG)."""
        pass

    @abstractmethod
    async def save_fact(self, user_id: str, content: str, category: str) -> FactNode:
        """Save a new fact about the user."""
        pass

    @abstractmethod
    async def consolidate_memories(self, user_id: str, dream_generator=None) -> None:
        """
        Consolidate memories for the user (Event-Driven Debounce).
        Compresses recent episodes and updates long-term resonance.
        """
        pass

    @abstractmethod
    async def get_last_dream(self, user_id: str) -> Optional[DreamNode]:
        """Retrieve the most recent dream (long-term memory consolidation) for the user."""
        pass

    @abstractmethod
    async def get_recent_episodes(self, user_id: str, limit: int = 10) -> List[MemoryEpisodeNode]:
        """Retrieve the most recent short-term memory episodes."""
        pass

    @abstractmethod
    async def get_relevant_episodes(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEpisodeNode]:
        """Retrieve relevant episodes for a user based on semantic similarity."""
        pass

    @abstractmethod
    async def get_recent_collective_events(self, limit: int = 5) -> List[CollectiveEventNode]:
        """Retrieve the most recent collective events (world history)."""
        pass

    @abstractmethod
    async def get_agent_collective_events(self, agent_id: str, limit: int = 5) -> List[CollectiveEventNode]:
        """
        Retrieve collective events where the specific agent was a participant.
        Strictly filtered for narrative injection.
        """
        pass

    @abstractmethod
    async def get_relevant_collective_events(self, query: str, limit: int = 5) -> List[CollectiveEventNode]:
        """Retrieve relevant collective events based on semantic similarity (RAG)."""
        pass

    # --- Evolution Phase 1: Ontology & Archetypes ---

    @abstractmethod
    async def create_archetype(self, name: str, description: str, triggers: Dict) -> ArchetypeNode:
        """Creates a new Archetype Node."""
        pass

    @abstractmethod
    async def get_archetype(self, name: str) -> Optional[ArchetypeNode]:
        """Fetch Archetype by Name."""
        pass

    @abstractmethod
    async def link_agent_archetype(self, agent_id: str, archetype_id: str, strength: float = 1.0) -> None:
        """Creates EMBODIES edge."""
        pass

    @abstractmethod
    async def get_agent_archetype(self, agent_id: str) -> Optional[ArchetypeNode]:
        """Get the Archetype an agent embodies."""
        pass

    # --- Evolution Phase 1: Global Dream ---

    @abstractmethod
    async def get_global_dream(self) -> GlobalDreamNode:
        """Fetch Singleton Global Dream."""
        pass

    @abstractmethod
    async def update_global_dream(self, themes: List[str], intensity: float) -> None:
        """Update Singleton Global Dream."""
        pass

    # --- Evolution Phase 2: System Config (Ontological Decoupling) ---

    @abstractmethod
    async def get_system_config(self) -> 'SystemConfigNode':
        """Fetch the System Configuration Node."""
        pass

    @abstractmethod
    async def update_system_config(self, config: 'SystemConfigNode') -> None:
        """Update the System Configuration Node."""
        pass

    # --- Evolution Phase 3: Explicit Graph Edges ---

    @abstractmethod
    async def create_edge(self, edge: GraphEdge) -> None:
        """
        Creates an explicit edge in the graph (e.g., ParticipatedIn, OccurredAt).
        """
        pass

    @abstractmethod
    async def get_edges(self, source_id: str = None, target_id: str = None, type: str = None) -> List[GraphEdge]:
        """
        Retrieves edges based on source, target, or type.
        """
        pass
