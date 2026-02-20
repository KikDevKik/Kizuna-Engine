import json
import logging
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from ..models.graph import AgentNode

logger = logging.getLogger(__name__)

# Define the path relative to the project root or use an environment variable
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "agents"

class AgentService:
    def __init__(self, data_dir: Path = AGENTS_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

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
        Retrieves a specific agent by ID.
        Since filename is [ID].json, we can look it up directly.
        """
        file_path = self.data_dir / f"{agent_id}.json"
        if not file_path.exists():
            return None

        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
                return AgentNode(**data)
        except Exception as e:
            logger.error(f"Failed to load agent {agent_id}: {e}")
            return None

    async def create_agent(self, name: str, role: str, base_instruction: str, traits: dict = None, tags: list = None) -> AgentNode:
        """
        Creates a new agent file.
        Generates a UUID for the ID and filename.
        """
        agent_id = str(uuid4())

        agent = AgentNode(
            id=agent_id,
            name=name,
            role=role,
            base_instruction=base_instruction,
            traits=traits or {},
            tags=tags or []
        )

        file_path = self.data_dir / f"{agent_id}.json"

        try:
            content = json.dumps(agent.model_dump(mode='json'), indent=4, ensure_ascii=False)
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)
            logger.info(f"Created new agent: {name} ({agent_id})")
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent {name}: {e}")
            raise

    async def delete_agent(self, agent_id: str) -> bool:
        """
        Deletes an agent file by ID.
        """
        file_path = self.data_dir / f"{agent_id}.json"
        if not file_path.exists():
            logger.warning(f"Agent deletion requested for non-existent ID: {agent_id}")
            return False

        try:
            await aiofiles.os.remove(file_path)
            logger.info(f"Deleted agent: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            raise

# Singleton instance
agent_service = AgentService()
