import json
import logging
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4
from pydantic import BaseModel, Field

from ..models.graph import AgentNode, MemoryEpisodeNode
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
    summary: str = Field(..., description="A specific event from the agent's past.")
    emotional_valence: float = Field(..., description="Emotional impact (-1.0 to 1.0).")

class HollowAgentProfile(BaseModel):
    name: str = Field(..., description="The name of the agent.")
    backstory: str = Field(..., description="A rich backstory explaining their presence in District Zero.")
    traits: dict = Field(..., description="Personality traits (key-value pairs).")
    voice_name: str = Field(..., description="Selected voice from: Aoede, Kore, Puck, Charon, Fenrir.")
    false_memories: List[GeneratedMemory] = Field(..., description="2-3 distinct memories from their past.")

class AgentService:
    def __init__(self, data_dir: Path = AGENTS_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Gemini Client if key exists
        self.client = None
        if genai and settings.GEMINI_API_KEY:
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

    async def create_agent(self, name: str, role: str, base_instruction: str, voice_name: Optional[str] = None, traits: dict = None, tags: list = None, native_language: str = "Unknown", known_languages: list = None) -> AgentNode:
        """
        Creates a new agent file and updates cache.
        """
        agent_id = str(uuid4())

        agent = AgentNode(
            id=agent_id,
            name=name,
            role=role,
            base_instruction=base_instruction,
            voice_name=voice_name,
            traits=traits or {},
            tags=tags or [],
            native_language=native_language,
            known_languages=known_languages or []
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

        prompt = (
            f"You are the Soul Forge. Your task is to create a procedural 'Stranger' agent for the Kizuna Engine simulation.\n"
            f"The user has provided this aesthetic description: '{aesthetic_description}'\n\n"
            f"Generate a full psychological profile, including:\n"
            f"1. A fitting Name.\n"
            f"2. A Semantic Backstory (Base Instruction) that explains why they are in District Zero. They must be a STRANGER to the user.\n"
            f"3. Personality Traits (key-value).\n"
            f"4. Voice Selection: Choose the best voice from [Aoede, Kore, Puck, Charon, Fenrir] based on the vibe.\n"
            f"5. False Memories: Create 2-3 specific, vivid memories from their past (NOT involving the user). "
            f"These give them depth (e.g., 'Escaped a corp raid', 'Lost a bet').\n\n"
            f"Output must be valid JSON matching the schema."
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=settings.MODEL_FORGE,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=HollowAgentProfile
                )
            )

            if not response.parsed:
                raise ValueError("Failed to parse structured output from Soul Forge.")

            profile: HollowAgentProfile = response.parsed

            # Create AgentNode
            # We treat 'backstory' as 'base_instruction'
            new_agent = AgentNode(
                name=profile.name,
                role="Stranger", # Default role for forged hollows
                base_instruction=profile.backstory,
                voice_name=profile.voice_name,
                traits=profile.traits,
                tags=["hollow-forged", "stranger"],
                native_language="Unknown", # Can be inferred later or added to schema if needed
                known_languages=[]
            )

            # Create MemoryEpisodeNodes
            memories = []
            for mem in profile.false_memories:
                episode = MemoryEpisodeNode(
                    summary=mem.summary,
                    emotional_valence=mem.emotional_valence,
                    raw_transcript=None # No transcript for false memories
                )
                memories.append(episode)

            return new_agent, memories

        except Exception as e:
            logger.error(f"Soul Forge failed: {e}")
            raise

# Singleton instance
agent_service = AgentService()
