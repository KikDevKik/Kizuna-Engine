import json
import logging
import asyncio
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

from .base import SoulRepository
from ..models.graph import UserNode, AgentNode, ResonanceEdge, MemoryEpisodeNode, FactNode

logger = logging.getLogger(__name__)

# Path to local JSON simulation
GRAPH_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "graph.json"

class LocalSoulRepository(SoulRepository):
    """
    Phase 3.1: Local Simulation of Google Cloud Spanner using JSON.
    This simulates the "Graph" structure in memory and persists to disk.
    """

    def __init__(self, data_path: Path = GRAPH_DATA_PATH):
        self.data_path = data_path
        self.lock = asyncio.Lock()

        # In-memory graph representation
        self.users: Dict[str, UserNode] = {}
        self.agents: Dict[str, AgentNode] = {}
        self.episodes: Dict[str, MemoryEpisodeNode] = {}
        self.facts: Dict[str, FactNode] = {}
        self.resonances: Dict[str, Dict[str, ResonanceEdge]] = {} # {user_id: {agent_id: Resonance}}
        self.experienced: Dict[str, List[str]] = {} # {user_id: [episode_ids]}
        self.knows: Dict[str, List[str]] = {} # {user_id: [fact_ids]}

    async def initialize(self) -> None:
        """Load the graph from JSON."""
        # Use asyncio.Lock() to ensure exclusive access
        async with self.lock:
            await self.load()

    async def load(self):
        """Helper to actually load data (called manually or lazily)."""
        # 1. Load Graph Data (if exists)
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Hydrate models
                for u in data.get("users", []):
                    node = UserNode(**u)
                    self.users[node.id] = node

                for a in data.get("agents", []):
                    node = AgentNode(**a)
                    self.agents[node.id] = node

                for e in data.get("episodes", []):
                    node = MemoryEpisodeNode(**e)
                    self.episodes[node.id] = node

                for f in data.get("facts", []):
                    node = FactNode(**f)
                    self.facts[node.id] = node

                # Hydrate Edges
                for r in data.get("resonances", []):
                    edge = ResonanceEdge(**r)
                    if edge.source_id not in self.resonances:
                        self.resonances[edge.source_id] = {}
                    self.resonances[edge.source_id][edge.target_id] = edge

                self.experienced = data.get("experienced", {})
                self.knows = data.get("knows", {})

                logger.info(f"Graph Database loaded: {len(self.users)} Users, {len(self.agents)} Agents.")

            except Exception as e:
                logger.error(f"Failed to load graph database: {e}")
                # We proceed to sync agents anyway, effectively starting with partial data if graph is corrupt
        else:
            logger.info("No graph.json found. Starting with empty graph.")

        # ---------------------------------------------------------
        # Sync with Agents Directory (Source of Truth for Agents)
        # ---------------------------------------------------------
        # This must happen regardless of graph.json state
        agents_dir = self.data_path.parent / "agents"
        if agents_dir.exists():
            loaded_count = 0
            for agent_file in agents_dir.glob("*.json"):
                try:
                    with open(agent_file, "r", encoding="utf-8") as af:
                        agent_data = json.load(af)
                        agent_node = AgentNode(**agent_data)
                        # Upsert: Filesystem overrides graph.json cache
                        self.agents[agent_node.id] = agent_node
                        loaded_count += 1
                except Exception as ae:
                    logger.error(f"Failed to sync agent from {agent_file}: {ae}")
            logger.info(f"Synced {loaded_count} agents from filesystem.")

        # Ensure graph.json is initialized if it didn't exist
        if not self.data_path.exists():
            self._save_sync()

    def _save_sync(self):
        """Synchronous save for initialization."""
        self._write_to_disk()

    async def _save(self):
        """Async wrapper for save."""
        # In a real scenario with aiofiles, we'd await here.
        # For simplicity with JSON dumps, we'll keep it sync-wrapped or just call it.
        # Since this is a local simulation, a small blocking write is acceptable for Phase 3.1
        self._write_to_disk()

    def _write_to_disk(self):
        # Helper to dump pydantic models to dict
        def to_dict_list(models):
             return [m.model_dump(mode='json') for m in models]

        data = {
            "users": to_dict_list(self.users.values()),
            "agents": to_dict_list(self.agents.values()),
            "episodes": to_dict_list(self.episodes.values()),
            "facts": to_dict_list(self.facts.values()),
            "resonances": [
                r.model_dump(mode='json')
                for u_dict in self.resonances.values()
                for r in u_dict.values()
            ],
            "experienced": self.experienced,
            "knows": self.knows
        }

        # Ensure directory exists
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = self.data_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            temp_path.replace(self.data_path)
        except Exception as e:
            logger.error(f"Failed to save graph database: {e}")
            if temp_path.exists():
                temp_path.unlink()

    async def get_or_create_user(self, user_id: str, name: str = "Anonymous") -> UserNode:
        async with self.lock:
            if user_id in self.users:
                return self.users[user_id]

            new_user = UserNode(id=user_id, name=name)
            self.users[user_id] = new_user
            await self._save()
            return new_user

    async def get_agent(self, agent_id: str) -> Optional[AgentNode]:
        # Agents are usually pre-seeded, but let's check
        return self.agents.get(agent_id)

    async def create_agent(self, agent: AgentNode):
        """Helper to seed agents."""
        async with self.lock:
            self.agents[agent.id] = agent
            await self._save()

    async def get_resonance(self, user_id: str, agent_id: str) -> ResonanceEdge:
        async with self.lock:
            user_resonances = self.resonances.get(user_id, {})
            if agent_id in user_resonances:
                return user_resonances[agent_id]

            # Default Resonance (Starts at 0)
            new_resonance = ResonanceEdge(source_id=user_id, target_id=agent_id, affinity_level=0)
            if user_id not in self.resonances:
                self.resonances[user_id] = {}
            self.resonances[user_id][agent_id] = new_resonance
            await self._save()
            return new_resonance

    async def update_resonance(self, user_id: str, agent_id: str, delta: int) -> ResonanceEdge:
        async with self.lock:
            resonance = await self.get_resonance(user_id, agent_id)
            # Apply delta
            new_affinity = resonance.affinity_level + delta
            # Clamp logic could go here (e.g. max 100)
            resonance.affinity_level = new_affinity
            resonance.last_interaction = datetime.now()

            # Save logic handled by reference update in dict, but need to persist to disk
            await self._save()
            logger.info(f"Resonance updated for User {user_id} -> Agent {agent_id}: {new_affinity}")
            return resonance

    async def save_episode(self, user_id: str, agent_id: str, summary: str, valence: float) -> MemoryEpisodeNode:
        async with self.lock:
            episode = MemoryEpisodeNode(summary=summary, emotional_valence=valence)
            self.episodes[episode.id] = episode

            # Link to User
            if user_id not in self.experienced:
                self.experienced[user_id] = []
            self.experienced[user_id].append(episode.id)

            # Update Resonance with this shared memory
            resonance = await self.get_resonance(user_id, agent_id)
            resonance.shared_memories.append(episode.id)

            await self._save()
            return episode

    async def get_relevant_facts(self, user_id: str, query: str, limit: int = 5) -> List[FactNode]:
        """
        Mock Vector Search.
        In Phase 3.2 (Spanner), this will use vector embeddings.
        Here, we do a simple keyword match.
        """
        if user_id not in self.knows:
            return []

        user_fact_ids = self.knows[user_id]
        relevant = []

        query_terms = set(query.lower().split())

        for fact_id in user_fact_ids:
            fact = self.facts.get(fact_id)
            if not fact:
                continue

            # Basic keyword matching
            content_terms = set(fact.content.lower().split())
            if query_terms.intersection(content_terms):
                relevant.append(fact)

            if len(relevant) >= limit:
                break

        return relevant

    async def save_fact(self, user_id: str, content: str, category: str) -> FactNode:
        async with self.lock:
            fact = FactNode(content=content, category=category)
            self.facts[fact.id] = fact

            if user_id not in self.knows:
                self.knows[user_id] = []
            self.knows[user_id].append(fact.id)

            await self._save()
            return fact

    async def consolidate_memories(self, user_id: str) -> None:
        """
        Consolidate memories for the user (Event-Driven Debounce).
        Simulates compressing recent episodes.
        """
        async with self.lock:
            ep_ids = self.experienced.get(user_id, [])
            if not ep_ids:
                logger.info(f"No memories to consolidate for {user_id}.")
                return

            # Simulate LLM Clustering & Compression (Mock)
            # Find all unprocessed episodes (valence=0.5 was our trigger)
            raw_episodes = []
            for eid in ep_ids:
                ep = self.episodes.get(eid)
                if ep and ep.emotional_valence == 0.5: # Mock 'raw' flag
                    raw_episodes.append(ep)

            if not raw_episodes:
                logger.info("No RAW episodes to consolidate.")
                return

            logger.info(f"Compressing {len(raw_episodes)} raw episodes into Long-Term Memory...")

            # 1. Create Summary Episode (The "Dream")
            summary_text = f"User interaction summary: {len(raw_episodes)} events consolidated."
            summary_node = MemoryEpisodeNode(
                summary=summary_text,
                emotional_valence=1.0 # Consolidated/Refined
            )
            self.episodes[summary_node.id] = summary_node

            # 2. Link Summary to User
            self.experienced[user_id].append(summary_node.id)

            # 3. Mark Raw Episodes as archived (or delete them to save space)
            # For demo, we just update valence to indicate processed
            for ep in raw_episodes:
                ep.emotional_valence = 0.0 # Archived state

            # 4. Trigger Affinity Decay/Growth (Mathematical recalibration)
            # Stub: Just +1 for a good consolidation
            # In Phase 4, this would be the exponential moving average.

            await self._save()
