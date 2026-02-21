import json
import logging
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from ..models.graph import AgentNode
from .cache import cache

logger = logging.getLogger(__name__)

# Define the path relative to the project root or use an environment variable
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "agents"

class AgentService:
    def __init__(self, data_dir: Path = AGENTS_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

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

# Singleton instance
agent_service = AgentService()
