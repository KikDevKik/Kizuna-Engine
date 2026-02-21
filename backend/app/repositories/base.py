from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..models.graph import UserNode, AgentNode, ResonanceEdge, MemoryEpisodeNode, FactNode, DreamNode

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
