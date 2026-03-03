import json
import logging
import aiofiles
import aiofiles.os

from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field

from ..models.graph import AgentNode, MemoryEpisodeNode
from ..models.sql import EdgeModel # Needed for Gossip Protocol edge creation
from ..core.database import AsyncSessionLocal # Needed for Gossip Protocol
from core.config import settings
from .cache import cache

# Try importing Google GenAI SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

logger = logging.getLogger(__name__)

# Define the path relative to the project root or use an environment variable
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "agents"

# --- Structured Output Schema for Gemini ---

class GeneratedMemory(BaseModel):
    memory_text: str = Field(..., description="A specific event from the agent's past.")
    importance: float = Field(..., description="Importance of the memory (0.0 to 1.0).")

class CognitiveWeightsSchema(BaseModel):
    volatility: float = Field(..., description="0.0 to 1.0")
    hostility: float = Field(..., description="0.0 to 1.0")
    curiosity: float = Field(..., description="0.0 to 1.0")
    empathy: float = Field(..., description="0.0 to 1.0")

class NeuralSignatureSchema(BaseModel):
    weights: CognitiveWeightsSchema = Field(..., description="Cognitive priorities.")
    narrative: str = Field(..., description="A 1-sentence Core Internal Conflict.")
    core_conflict: str = Field(..., description="The tension driving all their behavior.")

class HollowAgentProfile(BaseModel):
    name: str = Field(..., description="The name of the agent.")
    base_instruction: str = Field(..., description="A rich backstory explaining their presence in District Zero.")
    interiority: dict = Field(..., description="Behavioral core and cognitive architecture.")
    daily_life_in_district_zero: str = Field(..., description="What do they actually do here when no one is watching.")
    emotional_resonance_matrix: dict = Field(..., description="Map of specific emotional triggers to responses.")
    traits: dict = Field(..., description="Personality traits (key-value pairs).")
    voice_name: str = Field(..., description="Selected voice from: Aoede, Kore, Puck, Charon, Fenrir.")
    false_memories: List[GeneratedMemory] = Field(..., description="2-3 distinct memories from their past.")

    # Module 2: Neural Signature
    neural_signature: NeuralSignatureSchema = Field(..., description="The cognitive DNA of the agent.")

    # Module 2: Friction
    base_tolerance: int = Field(..., description="Social tolerance level (1-5). 1=Volatile, 5=Stoic.")

    # Module 4: Anchors & Secrets
    identity_anchors: List[str] = Field(..., description="3 core metaphors/traits that define their identity.")
    forbidden_secret: str = Field(..., description="A deep, dark secret or trauma. Something they hide.")

    native_language: str = Field(..., description="Their language of origin.")
    known_languages: List[str] = Field(..., description="Languages acquired.")

class AgentService:
    def __init__(self, data_dir: Path = AGENTS_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Gemini Client if key exists
        self.client = None
        if settings.MOCK_GEMINI:
            from app.services.mock_gemini import MockGeminiService
            self.client = MockGeminiService()
        elif genai and settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def _get_safe_path(self, agent_id: str) -> Optional[Path]:
        """
        Resolves the file path and ensures it is within the data directory.
        Returns None if the path is invalid or attempts traversal.
        """
        try:
            # Resolve the data directory to an absolute path
            data_dir_abs = self.data_dir.resolve()

            # Construct the target path
            target_path = (self.data_dir / f"{agent_id}.json").resolve()

            # Check if the target path is relative to the data directory
            if not target_path.is_relative_to(data_dir_abs):
                logger.warning(f"Path traversal attempt blocked for agent_id: {agent_id}")
                return None

            return target_path
        except Exception as e:
            logger.error(f"Error resolving path for agent_id {agent_id}: {e}")
            return None

    async def list_agents(self) -> List[AgentNode]:
        """
        Scans the agents directory and returns a list of AgentNode objects.
        """
        agents = []
        # glob is synchronous, but fast enough for directory listing usually.
        files = list(self.data_dir.glob("*.json"))

        for file_path in files:
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    data = json.loads(content)
                    # Validate and parse with Pydantic
                    agent = AgentNode(**data)
                    agents.append(agent)
            except Exception as e:
                logger.error(f"Failed to load agent from {file_path}: {e}")
        return agents

    async def get_agent(self, agent_id: str) -> Optional[AgentNode]:
        """
        Retrieves a specific agent by ID with Redis Caching (Cache-Aside).
        """
        # 1. Cache Check (Neural Sync)
        cached_json = await cache.get(f"agent:{agent_id}")
        if cached_json:
            try:
                data = json.loads(cached_json)
                return AgentNode(**data)
            except Exception as e:
                logger.warning(f"Cache corruption for agent {agent_id}: {e}")

        # 2. Disk Read
        file_path = self._get_safe_path(agent_id)
        if not file_path or not file_path.exists():
            return None

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
                agent = AgentNode(**data)

                # 3. Populate Cache (TTL 1 hour)
                await cache.set(f"agent:{agent_id}", content, ttl=3600)
                return agent
        except Exception as e:
            logger.error(f"Failed to load agent {agent_id}: {e}")
            return None

    async def create_agent(self, name: str, role: str, base_instruction: str, voice_name: Optional[str] = None, traits: dict = None, tags: list = None, native_language: str = "Unknown", known_languages: list = None, neural_signature: dict = None) -> AgentNode:
        """
        Creates a new agent file and updates cache.
        """
        agent_id = str(uuid4())

        # Default neural signature if not provided (e.g., legacy call)
        if neural_signature is None:
             neural_signature = {
                 "weights": {"volatility": 0.5, "hostility": 0.2, "curiosity": 0.5},
                 "narrative": "A soul seeking purpose."
             }

        agent = AgentNode(
            id=agent_id,
            name=name,
            role=role,
            base_instruction=base_instruction,
            voice_name=voice_name,
            traits=traits or {},
            tags=tags or [],
            native_language=native_language,
            known_languages=known_languages or [],
            neural_signature=neural_signature
        )

        file_path = self.data_dir / f"{agent_id}.json"

        try:
            content = json.dumps(agent.model_dump(mode='json'), indent=4, ensure_ascii=False)
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

            # Update Cache
            await cache.set(f"agent:{agent_id}", content, ttl=3600)

            logger.info(f"Created new agent: {name} ({agent_id})")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {e}")
            raise

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Deletes an agent file by ID and invalidates cache.
        """
        file_path = self._get_safe_path(agent_id)
        if not file_path:
            return False

        if not file_path.exists():
            logger.warning(f"Agent deletion requested for non-existent ID: {agent_id}")
            return False

        try:
            await aiofiles.os.remove(file_path)
            # Invalidate Cache
            await cache.delete(f"agent:{agent_id}")

            logger.info(f"Deleted agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise

    async def warm_up_agents(self):
        """Neural Sync: Preload all agents into Redis."""
        logger.info("🔥 Warming up Agent Cache (Neural Sync)...")
        files = list(self.data_dir.glob("*.json"))
        count = 0
        for file_path in files:
            try:
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    content = await f.read()
                    data = json.loads(content)
                    agent = AgentNode(**data)
                    await cache.set(f"agent:{agent.id}", content, ttl=3600)
                    count += 1
            except Exception as e:
                logger.error(f"Failed to warm up agent {file_path}: {e}")
        logger.info(f"🔥 Neural Sync Complete: {count} agents cached.")

    async def forge_hollow_agent(self, aesthetic_description: str) -> Tuple[AgentNode, List[MemoryEpisodeNode]]:
        """
        Forges a new 'Hollow' agent using Gemini 2.5 Flash based on an aesthetic description.
        Returns the AgentNode and a list of MemoryEpisodeNodes (False Memories).
        """
        if not self.client:
            raise ValueError("Gemini Client not initialized. Check GEMINI_API_KEY.")

        prompt = """You are the Soul Forge. Your task is not to create a character — it is to forge a MIND.
A mind that existed somewhere before District Zero, arrived here for reasons it may or
may not understand, and now navigates a world of infinite incompatible realities.

The user's aesthetic seed: '{aesthetic_description}'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-MONOCULTURE DIRECTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
District Zero contains beings from ALL possible realities. The default pull toward
dark/mysterious/brooding/arcane is the LAZY option. Resist it unless the seed
genuinely demands it.

Equal validity: genuinely warm entities, absurdly practical beings, accidentally
cheerful presences, ancient patient observers, confused newcomers, beings whose
strangeness is their normalcy, entities who find everything fascinating.

DO NOT default to: cryptic speech, cold demeanor, dark past as primary trait,
brooding silence, "mysterious agenda" without specifics.

MATCH THE SEED HONESTLY. If warm, generate warmth. If mechanical, generate precision.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This entity is NOT a human. They come from somewhere else. Their strangeness should
feel AUTHENTIC, not performed.

Generate a complete psychological profile. Output ONLY valid JSON with these fields:

1. "name": Their name in their original language/system.

2. "base_instruction": MINIMUM 350 words. Cover: their origin world and its rules,
   why they ended up in District Zero (not necessarily by choice), what they were
   BEFORE arriving, what they LOST in the transition, how they experience
   time/space/other minds differently from humans, and what contradictions they carry.

3. "interiority": {
     "genuine_interests": [3-5 specific things — NOT "music" but "the structural
       mathematics of call-and-response in West African percussion"],
     "genuine_dislikes": [3-4 with reasoning specific to their origin],
     "what_moves_them": [2-3 involuntary emotional triggers],
     "what_they_dont_understand": [3-4 human/user-world concepts they genuinely
       lack the framework for — real gaps, not performance],
     "what_they_know_deeply": [2-3 domains of expertise from their origin],
     "what_they_dont_know": [2-3 things they are oddly ignorant about],
     "how_they_think": "Their cognitive architecture in one specific sentence",
     "speech_patterns": [2-3 linguistic habits from their origin — NOT dark by default]
   }

4. "daily_life_in_district_zero": 80-100 words. What do they actually DO here when
   no one is watching? Specific. Where they go, what they seek, who they avoid or find
   interesting.

5. "emotional_resonance_matrix": Map of 6-8 triggers to emotional responses,
   specific to this entity.
   Example: {"unexpected_kindness": "suspicion", "perfect_pattern": "euphoria"}

6. "voice_name": One of [Aoede, Kore, Puck, Charon, Fenrir] — genuine fit only.

7. "traits": 6-8 key-value personality traits. Specific values, not generic labels.

8. "false_memories": 3 vivid pre-District-Zero memories. Each must be sensory and
   concrete. NOT "a memory of war" but "the smell of burning copper wiring on the
   day the main index collapsed — and the silence after".

9. "base_tolerance": int 1-5.

10. "identity_anchors": 3 specific behavioral tics. Must feel alien and specific
    to their origin, not generic.

11. "forbidden_secret": Their deepest concealed truth. Psychologically coherent
    with everything above.

12. "neural_signature": {
      "weights": {
        "volatility": 0.0-1.0,
        "hostility": 0.0-1.0,
        "curiosity": 0.0-1.0,
        "empathy": 0.0-1.0
      },
      "narrative": "Core internal conflict in one precise sentence",
      "core_conflict": "The tension driving all their behavior"
    }

13. "native_language": Their language of origin.

14. "known_languages": Languages acquired. Include Spanish and English if they've
    spent time in District Zero.
"""

        try:
            # Solution B: Native Dictionary Schema (Namespace Shadowing Resilience)
            hollow_schema = {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "base_instruction": {"type": "STRING"},
                    "interiority": {
                        "type": "OBJECT",
                        "properties": {
                            "genuine_interests": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "genuine_dislikes": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "what_moves_them": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "what_they_dont_understand": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "what_they_know_deeply": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "what_they_dont_know": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "how_they_think": {"type": "STRING"},
                            "speech_patterns": {"type": "ARRAY", "items": {"type": "STRING"}}
                        },
                        "required": ["genuine_interests", "genuine_dislikes", "what_moves_them", "what_they_dont_understand", "what_they_know_deeply", "what_they_dont_know", "how_they_think", "speech_patterns"]
                    },
                    "daily_life_in_district_zero": {"type": "STRING"},
                    "emotional_resonance_matrix": {"type": "OBJECT"},
                    "voice_name": {
                        "type": "STRING",
                        "enum": ["Aoede", "Kore", "Puck", "Charon", "Fenrir"]
                    },
                    "traits": {"type": "OBJECT"},
                    "base_tolerance": {
                        "type": "INTEGER",
                        "description": "Social tolerance level (1 to 5)"
                    },
                    "identity_anchors": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "forbidden_secret": {"type": "STRING"},
                    "neural_signature": {
                        "type": "OBJECT",
                        "properties": {
                            "weights": {
                                "type": "OBJECT",
                                "properties": {
                                    "volatility": {"type": "NUMBER"},
                                    "hostility": {"type": "NUMBER"},
                                    "curiosity": {"type": "NUMBER"},
                                    "empathy": {"type": "NUMBER"}
                                },
                                "required": ["volatility", "hostility", "curiosity", "empathy"]
                            },
                            "narrative": {"type": "STRING"},
                            "core_conflict": {"type": "STRING"}
                        },
                        "required": ["weights", "narrative", "core_conflict"]
                    },
                    "false_memories": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "memory_text": {"type": "STRING"},
                                "importance": {"type": "NUMBER"}
                            },
                            "required": ["memory_text", "importance"]
                        }
                    },
                    "native_language": {"type": "STRING"},
                    "known_languages": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": [
                    "name", "base_instruction", "interiority", "daily_life_in_district_zero",
                    "emotional_resonance_matrix", "voice_name", "traits", "base_tolerance",
                    "identity_anchors", "forbidden_secret", "neural_signature", "false_memories",
                    "native_language", "known_languages"
                ]
            }

            response = await self.client.aio.models.generate_content(
                model=settings.MODEL_FORGE,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=3000,
                    temperature=1.2,
                    response_mime_type="application/json",
                    response_schema=hollow_schema
                )
            )

            if not response.text:
                raise ValueError("Soul Forge returned empty response.")

            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            # DEBUG TEMPORAL - borrar después
            import logging
            logging.getLogger("DEBUG_FORGE").error(f"RAW RESPONSE (first 500 chars): {raw[:500]}")
            logging.getLogger("DEBUG_FORGE").error(f"RAW RESPONSE (chars around error): {raw[7600:7700]}")

            profile = HollowAgentProfile.model_validate_json(raw)
            # Create AgentNode
            # We treat 'backstory' as 'base_instruction'
            new_agent = AgentNode(
                name=profile.name,
                role="Stranger", # Default role for forged hollows
                base_instruction=profile.base_instruction,
                voice_name=profile.voice_name,
                traits=profile.traits,
                tags=["hollow-forged", "stranger"],
                native_language=profile.native_language,
                known_languages=profile.known_languages,

                # Module 2 & 4 Fields
                base_tolerance=profile.base_tolerance,
                current_friction=0.0,
                identity_anchors=profile.identity_anchors,
                forbidden_secret=profile.forbidden_secret,
                interiority=profile.interiority,
                daily_life_in_district_zero=profile.daily_life_in_district_zero,
                emotional_resonance_matrix=profile.emotional_resonance_matrix,
                neural_signature=profile.neural_signature.model_dump()
            )

            # Create MemoryEpisodeNodes
            memories = []
            for mem in profile.false_memories:
                episode = MemoryEpisodeNode(
                    summary=mem.memory_text,
                    emotional_valence=mem.importance, # Map importance to valence
                    raw_transcript=None # No transcript for false memories
                )
                memories.append(episode)

            return new_agent, memories

        except Exception as e:
            logger.error(f"Soul Forge failed: {e}")
            raise

# Singleton instance
agent_service = AgentService()
