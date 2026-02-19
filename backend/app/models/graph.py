from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

# --- Nodes ---

class UserNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "Anonymous"
    created_at: datetime = Field(default_factory=datetime.now)

class AgentNode(BaseModel):
    id: str
    name: str
    base_instruction: str
    traits: dict = Field(default_factory=dict)

class MemoryEpisodeNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    summary: str
    timestamp: datetime = Field(default_factory=datetime.now)
    emotional_valence: float = 0.0  # -1.0 to 1.0
    embedding: Optional[List[float]] = None # Vector embedding for RAG

class FactNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    category: str # e.g. "preference", "relationship", "biography"
    confidence: float = 1.0

# --- Edges (Relationships) ---

class ResonanceEdge(BaseModel):
    source_id: str # User ID
    target_id: str # Agent ID
    affinity_level: int = 0
    last_interaction: datetime = Field(default_factory=datetime.now)
    shared_memories: List[str] = Field(default_factory=list) # List of Episode IDs

class ExperiencedEdge(BaseModel):
    source_id: str # User ID
    target_id: str # Episode ID
    weight: float = 1.0

class KnowsEdge(BaseModel):
    source_id: str # User or Agent ID
    target_id: str # Fact ID
    context: str = ""
