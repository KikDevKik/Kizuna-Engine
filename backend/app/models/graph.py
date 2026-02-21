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
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    role: str = "System Core" # Default role if not specified
    base_instruction: str
    avatar_path: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    traits: dict = Field(default_factory=dict)
    native_language: str = "Unknown"
    known_languages: List[str] = Field(default_factory=list)

    # Dynamic Prompts (Zero Hardcoding)
    memory_extraction_prompt: str = "Analyze the user's emotional state AND visual context from this transcript: '{text}'. Return a concise System Hint (max 15 words) starting with 'SYSTEM_HINT:'. If neutral, return nothing."
    dream_prompt: str = "Synthesize these memories into a surreal dream concept. Return JSON with keys: theme (str), intensity (0.0-1.0), surrealism_level (0.0-1.0).\n\nMemories:\n{summary_text}"
    vision_instruction_prompt: str = "Analyze the visual input critically. Focus on style, composition, and emotional resonance."

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
    embedding: Optional[List[float]] = None # Vector embedding

class DreamNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    theme: str
    intensity: float = 0.5 # 0.0 to 1.0
    surrealism_level: float = 0.5 # 0.0 to 1.0
    timestamp: datetime = Field(default_factory=datetime.now)

# --- Edges (Relationships) ---

class ResonanceEdge(BaseModel):
    source_id: str # User ID
    target_id: str # Agent ID
    affinity_level: float = 50.0 # 0.0 to 100.0 (50.0 = Neutral)
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

class ShadowEdge(BaseModel):
    source_id: str # User ID
    target_id: str # Dream ID
    weight: float = 1.0
