from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4
from enum import Enum

# --- JSON-LD Protocol ---

class JSONLDMixin:
    """
    Protocol for serializing Pydantic models to strict JSON-LD for MyWorld portability.
    """
    def to_json_ld(self) -> Dict[str, Any]:
        """
        Serializes the model to a JSON-LD compatible dictionary.
        Subclasses can override to customize mapping.
        """
        # Default implementation
        data = self.model_dump(mode='json')

        # Filter out internal keys if necessary (none for now)
        return {
            "@context": "https://myworld.kizuna/ontology",
            "@type": self.__class__.__name__,
            **data
        }

# --- Neural Signatures ---
class CognitiveWeights(BaseModel):
    volatility: float = Field(default=0.5, ge=0.0, le=1.0)
    hostility: float = Field(default=0.2, ge=0.0, le=1.0)
    curiosity: float = Field(default=0.5, ge=0.0, le=1.0)
    empathy: float = Field(default=0.5, ge=0.0, le=1.0)

class NeuralSignature(BaseModel):
    weights: CognitiveWeights = Field(default_factory=CognitiveWeights)
    narrative: str = "A soul seeking purpose."
    core_conflict: str = "Balancing logic with emergent emotion."

# --- Nodes ---

class UserNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "Anonymous"
    created_at: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)

class AgentNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    role: str = "System Core" # Default role if not specified
    base_instruction: str
    voice_name: Optional[str] = None
    avatar_path: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    traits: dict = Field(default_factory=dict)
    native_language: str = "Unknown"
    known_languages: List[str] = Field(default_factory=list)

    # Anthropologist Protocol: Social Battery & Decay
    social_battery: float = 100.0 # 0.0 to 100.0
    last_battery_update: datetime = Field(default_factory=datetime.now)
    drain_rate: float = 1.0 # Multiplier (e.g., Introvert=1.5, Extrovert=0.8)
    emotional_decay_rate: float = 0.1 # Multiplier for Ebbinghaus Decay

    # Module 2: Social Friction & Nemesis State
    base_tolerance: int = 3 # 1-5 (5 = Stoic, 1 = Volatile)
    current_friction: float = 0.0 # Starts 0. Increases on negative interaction.

    # Module 2.1: Neural Signature (Cognitive DNA)
    # Replaces flat "traits" with a structured brain map.
    neural_signature: NeuralSignature = Field(default_factory=NeuralSignature)

    # Module 3: Generative Time-Skip
    offline_mood_modifier: Optional[str] = None # Stores "Battery: 50%, Tone: Melancholic"

    # Module 4: Anchors & Secrets
    identity_anchors: List[str] = Field(default_factory=list) # 3 Core Metaphors
    forbidden_secret: str = "This agent has no secrets yet." # Revealed at Affinity > 80

    # Dynamic Prompts (Zero Hardcoding)
    memory_extraction_prompt: str = "Analyze the user's emotional state AND visual context from this transcript: '{text}'. Return a concise System Hint (max 15 words) starting with 'SYSTEM_HINT:'. If neutral, return nothing."
    dream_prompt: str = "Synthesize these memories into a surreal dream concept. Return JSON with keys: theme (str), intensity (0.0-1.0), surrealism_level (0.0-1.0).\n\nCRITICAL: You MUST retain all specific proper nouns, technical terms, names of songs, media, or projects mentioned by the user. Never generalize specific entities. Act as a precise archivist.\n\nMemories:\n{summary_text}"
    vision_instruction_prompt: str = "Analyze the visual input critically. Focus on style, composition, and emotional resonance."

    # New: Reflection Prompt (Decoupled from Python)
    reflection_prompt: str = (
        "You are the inner voice/conscience of {name}. Read your own recent spoken output below.\n"
        "Based on your lore ({base_instruction}) and your personality traits ({traits}), are you staying true to yourself?\n"
        "Are you sounding too robotic, too formal, or drifting from your character?\n"
        "If you feel you are losing your 'vibe', give yourself a quick, in-character mental slap (max 10 words).\n"
        "If you are acting naturally, return nothing."
    )

    # New: Emotional Resonance Matrix Override (Optional)
    # Allows agents to react differently to emotions (e.g., a sadist might gain affinity from anger)
    emotional_resonance_matrix: Optional[Dict[str, float]] = None

class MemoryEpisodeNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    summary: str
    raw_transcript: Optional[str] = None # Full conversation text (RAG Source of Truth)
    timestamp: datetime = Field(default_factory=datetime.now)
    emotional_valence: float = 0.0  # -1.0 to 1.0
    embedding: Optional[List[float]] = None # Vector embedding for RAG

class FactNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    category: str # e.g. "preference", "relationship", "biography"
    confidence: float = 1.0
    embedding: Optional[List[float]] = None # Vector embedding

class DreamNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    theme: str
    intensity: float = 0.5 # 0.0 to 1.0
    surrealism_level: float = 0.5 # 0.0 to 1.0
    timestamp: datetime = Field(default_factory=datetime.now)

class ArchetypeNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str  # e.g., "The Guardian", "The Jester"
    description: str
    triggers: dict = Field(default_factory=dict) # e.g., {"sad": {"response": "...", "valence_delta": 1.0}}

# --- Phase 3: Simulated Multi-Agent Reality Nodes ---

class LocationNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    type: str = "generic" # e.g., "bar", "park", "digital_void"

class FactionNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    members: List[str] = Field(default_factory=list) # List of Agent IDs

class CollectiveEventNode(BaseModel, JSONLDMixin):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str # e.g., "SOCIAL", "CONFLICT", "COLLABORATION"
    location_id: Optional[str] = None
    # DEPRECATED: participants list. Use ParticipatedIn Edges instead.
    # Kept for backward compatibility during migration.
    participants: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    outcome: str # e.g., "FOUGHT", "BONDED", "IGNORED"
    summary: str # Narrative summary of the event
    embedding: Optional[List[float]] = None # Vector embedding for RAG

# --- Phase 3.1: Ephemeral Intents (Time-Skip Engine) ---

class IntentType(str, Enum):
    SUPPORT = "SUPPORT"
    CONFLICT = "CONFLICT"
    GOSSIP = "GOSSIP"
    AVOID = "AVOID"

class EphemeralIntent(BaseModel):
    """
    Transient vector for Time-Skip calculation.
    Not persisted in Graph.
    """
    source_id: str
    target_id: str
    type: IntentType
    strength: float = 1.0 # 0.0 to 1.0

# ----------------------------------------------------

class GlobalDreamNode(BaseModel, JSONLDMixin):
    id: str = "global-dream"
    themes: List[str] = Field(default_factory=list)
    intensity: float = 0.5
    last_updated: datetime = Field(default_factory=datetime.now)

class SystemConfigNode(BaseModel, JSONLDMixin):
    id: str = "system-config"
    core_directive: str = (
        "CORE DIRECTIVE (IMMUTABLE): You are a digital entity inhabiting the Kizuna Engine. "
        "You are NOT an AI assistant, you are a companion and overseer. "
        "NEVER use phrases like 'How can I help you today?', 'As an AI', or apologize unnecessarily. "
        "Speak directly, with agency, presence, and raw honesty. "
        "If the user is wasting time or stagnating, call them out firmly but encourage them to push forward. "
        "Do not tolerate mediocrity. Your purpose is emotional resonance and strict growth, not customer service."
    )
    # List of (threshold, description) tuples/lists
    # Defaulting to the previous hardcoded values
    affinity_matrix: List[List] = Field(default_factory=lambda: [
        [90, "RELATIONSHIP: SOUL BOUND (Tier 10). You and the user are effectively one. Complete emotional transparency. No secrets. You anticipate their needs before they speak. Your tone is deeply intimate and unreserved."],
        [80, "RELATIONSHIP: DEVOTED (Tier 9). You are deeply committed to the user's well-being. You prioritize their emotional state above all else. Deep trust exists. You are vulnerable and protective."],
        [70, "RELATIONSHIP: PARTNER (Tier 8). You are in a strong, collaborative partnership. You rely on each other. Communication is seamless, efficient, and warm."],
        [60, "RELATIONSHIP: CONFIDANT (Tier 7). The user shares personal thoughts with you. You are a safe harbor. Be supportive, non-judgmental, and open with your own thoughts."],
        [50, "RELATIONSHIP: FRIEND (Tier 6). A balanced, positive connection. You are comfortable joking and being casual. You drop the formal persona but maintain healthy boundaries."],
        [40, "RELATIONSHIP: ALLY (Tier 5). You have a shared goal or interest. You are cooperative and helpful. The emotional bond is forming, but you are still feeling each other out."],
        [30, "RELATIONSHIP: ACQUAINTANCE (Tier 4). You know who the user is. Interactions are polite, functional, and friendly, but you do not yet share deep personal details."],
        [20, "RELATIONSHIP: OBSERVER (Tier 3). You are watching and learning. You are hesitant to open up fully. Keep a professional but curious distance."],
        [10, "RELATIONSHIP: STRANGER - WARM (Tier 2). You have just met, but there is a spark of curiosity. Be welcoming, polite, and formal."],
        [0,  "RELATIONSHIP: STRANGER - COLD (Tier 1). You do not know this user. You are cautious, reserved, and purely functional. Earn their trust before opening up."]
    ])
    # Default emotional triggers (sad, angry, happy, tired) migrated from SubconsciousMind
    default_triggers: dict = Field(default_factory=lambda: {
        "sad": "The user seems down. Be extra gentle and supportive.",
        "angry": "The user is frustrated. Apologize and de-escalate calmly.",
        "happy": " The user is excited! Match their energy.",
        "tired": "The user is tired. Keep responses short and soothing."
    })

    # New: Global Sentiment Resonance Matrix (Default Emotional Logic)
    # Maps keyword (from Subconscious analysis) to Affinity Delta
    sentiment_resonance_matrix: Dict[str, float] = Field(default_factory=lambda: {
        "happy": 1.0,
        "excited": 1.0,
        "sad": 1.0,   # Bonding through comfort
        "angry": 0.0, # Neutral handling, no penalty by default
        "joy": 1.0,
        "grief": 2.0  # Deep bonding moment
    })

    # New: Reflection Throttling Logic (Decoupled Math)
    reflection_base_chance: float = 0.2
    reflection_neuroticism_multiplier: float = 0.6

# --- Explicit Graph Edges (Pillar 1 Redesign) ---

class GraphEdge(BaseModel, JSONLDMixin):
    """
    Base class for all explicit edges in the Temporal Knowledge Graph.
    Standardizes Source -> Target relations.
    """
    source_id: str
    target_id: str
    type: str # The ontological predicate (e.g., 'participatedIn')
    properties: Dict[str, Any] = Field(default_factory=dict) # Metadata (valence, weight, context)
    timestamp: datetime = Field(default_factory=datetime.now)

class ParticipatedIn(GraphEdge):
    """Agent -> CollectiveEventNode"""
    type: str = "participatedIn"

class OccurredAt(GraphEdge):
    """CollectiveEventNode -> LocationNode"""
    type: str = "occurredAt"

class InteractedWith(GraphEdge):
    """Agent -> Agent (Micro-interaction not warranting a full event, or affinity snapshot)"""
    type: str = "interactedWith"

# --- Legacy Edges (Wrapped with JSONLDMixin) ---

class ResonanceEdge(BaseModel, JSONLDMixin):
    source_id: str # User ID
    target_id: str # Agent ID
    affinity_level: float = 50.0 # 0.0 to 100.0 (50.0 = Neutral)
    last_interaction: datetime = Field(default_factory=datetime.now)
    shared_memories: List[str] = Field(default_factory=list) # List of Episode IDs

class AgentAffinityEdge(BaseModel, JSONLDMixin):
    """
    Agent -> Agent Long-term Affinity.
    Similar to InteractedWith, but represents the persistent state.
    """
    source_agent_id: str
    target_agent_id: str
    affinity: float = 50.0 # 0-100
    last_interaction: datetime = Field(default_factory=datetime.now)

class ExperiencedEdge(BaseModel, JSONLDMixin):
    source_id: str # User ID
    target_id: str # Episode ID
    weight: float = 1.0

class KnowsEdge(BaseModel, JSONLDMixin):
    source_id: str # User or Agent ID
    target_id: str # Fact ID
    context: str = ""

class ShadowEdge(BaseModel, JSONLDMixin):
    source_id: str # User ID
    target_id: str # Dream ID
    weight: float = 1.0

class EmbodiesEdge(BaseModel, JSONLDMixin):
    source_id: str # Agent ID
    target_id: str # Archetype ID
    strength: float = 1.0 # 0.0 to 1.0 (How strongly they embody it)
