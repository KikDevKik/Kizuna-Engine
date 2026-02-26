import json
import logging
import asyncio
import aiofiles
import os
import shutil
import time
import math
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

from .base import SoulRepository
from ..services.embedding import embedding_service
from ..models.graph import (
    UserNode, AgentNode, ResonanceEdge, MemoryEpisodeNode, FactNode,
    DreamNode, ShadowEdge, ArchetypeNode, GlobalDreamNode, EmbodiesEdge,
    SystemConfigNode,
    LocationNode, FactionNode, CollectiveEventNode, AgentAffinityEdge,
    GraphEdge, ParticipatedIn, OccurredAt, InteractedWith,
    ExperiencedEdge, KnowsEdge
)

logger = logging.getLogger(__name__)

# Path to local JSON simulation
GRAPH_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "graph.json"

class LegacyJsonSoulRepository(SoulRepository):
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
        self.dreams: Dict[str, DreamNode] = {}
        self.resonances: Dict[str, Dict[str, ResonanceEdge]] = {} # {user_id: {agent_id: Resonance}}
        self.experienced: Dict[str, List[str]] = {} # {user_id: [episode_ids]}
        self.knows: Dict[str, List[str]] = {} # {user_id: [fact_ids]}
        self.shadows: Dict[str, List[ShadowEdge]] = {} # {user_id: [ShadowEdge]}

        # Evolution Phase 1
        self.archetypes: Dict[str, ArchetypeNode] = {}
        self.embodies: Dict[str, List[EmbodiesEdge]] = {} # {agent_id: [EmbodiesEdge]}
        self.global_dream: GlobalDreamNode = GlobalDreamNode()

        # Evolution Phase 2: System Config
        self.system_config: SystemConfigNode = SystemConfigNode()

        # Evolution Phase 3: Multi-Agent Reality
        self.locations: Dict[str, LocationNode] = {}
        self.factions: Dict[str, FactionNode] = {}
        self.collective_events: Dict[str, CollectiveEventNode] = {}
        # {source_id: {target_id: AgentAffinityEdge}}
        self.agent_affinities: Dict[str, Dict[str, AgentAffinityEdge]] = {}

        # Explicit Graph Edges (Pillar 1 Redesign)
        self.graph_edges: List[GraphEdge] = []

    async def initialize(self) -> None:
        """Load the graph from JSON."""
        # Use asyncio.Lock() to ensure exclusive access
        async with self.lock:
            await self.load()

    @staticmethod
    def _sync_load_worker(path: Path) -> dict:
        """
        Worker for file I/O and JSON parsing to be run in a separate thread.
        This isolates CPU-bound JSON serialization and blocking I/O.
        Returns a dict of hydrated objects.
        """
        loaded_state = {
            "users": {},
            "episodes": {},
            "facts": {},
            "dreams": {},
            "resonances": {},
            "experienced": {},
            "knows": {},
            "shadows": {},
            "archetypes": {},
            "embodies": {},
            "locations": {},
            "factions": {},
            "collective_events": {},
            "agent_affinities": {},
            "graph_edges": [],
            "global_dream": GlobalDreamNode(),
            "system_config": SystemConfigNode()
        }

        if not path.exists():
            return loaded_state

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Hydrate models
            for u in data.get("users", []):
                node = UserNode(**u)
                loaded_state["users"][node.id] = node

            for e in data.get("episodes", []):
                node = MemoryEpisodeNode(**e)
                loaded_state["episodes"][node.id] = node

            for f in data.get("facts", []):
                node = FactNode(**f)
                loaded_state["facts"][node.id] = node

            for d in data.get("dreams", []):
                node = DreamNode(**d)
                loaded_state["dreams"][node.id] = node

            # Hydrate Edges
            for r in data.get("resonances", []):
                edge = ResonanceEdge(**r)
                if edge.source_id not in loaded_state["resonances"]:
                    loaded_state["resonances"][edge.source_id] = {}
                loaded_state["resonances"][edge.source_id][edge.target_id] = edge

            loaded_state["experienced"] = data.get("experienced", {})
            loaded_state["knows"] = data.get("knows", {})

            # Hydrate Shadows
            for uid, edges in data.get("shadows", {}).items():
                loaded_state["shadows"][uid] = [ShadowEdge(**e) for e in edges]

            # Hydrate Archetypes (Phase 1)
            for a in data.get("archetypes", []):
                node = ArchetypeNode(**a)
                loaded_state["archetypes"][node.id] = node

            if "global_dream" in data:
                loaded_state["global_dream"] = GlobalDreamNode(**data["global_dream"])

            # Hydrate System Config (Phase 2)
            if "system_config" in data:
                loaded_state["system_config"] = SystemConfigNode(**data["system_config"])

            # Hydrate Embodies
            for aid, edges in data.get("embodies", {}).items():
                loaded_state["embodies"][aid] = [EmbodiesEdge(**e) for e in edges]

            # Hydrate Locations (Phase 3)
            for l in data.get("locations", []):
                node = LocationNode(**l)
                loaded_state["locations"][node.id] = node

            # Hydrate Factions (Phase 3)
            for fc in data.get("factions", []):
                node = FactionNode(**fc)
                loaded_state["factions"][node.id] = node

            # Hydrate Collective Events (Phase 3)
            for ce in data.get("collective_events", []):
                node = CollectiveEventNode(**ce)
                loaded_state["collective_events"][node.id] = node

            # Hydrate Agent Affinities (Phase 3)
            for af in data.get("agent_affinities", []):
                edge = AgentAffinityEdge(**af)
                if edge.source_agent_id not in loaded_state["agent_affinities"]:
                    loaded_state["agent_affinities"][edge.source_agent_id] = {}
                loaded_state["agent_affinities"][edge.source_agent_id][edge.target_agent_id] = edge

            # Hydrate Explicit Graph Edges (Pillar 1)
            for ge in data.get("graph_edges", []):
                edge_type = ge.get("type")
                if edge_type == "participatedIn":
                    loaded_state["graph_edges"].append(ParticipatedIn(**ge))
                elif edge_type == "occurredAt":
                    loaded_state["graph_edges"].append(OccurredAt(**ge))
                elif edge_type == "interactedWith":
                    loaded_state["graph_edges"].append(InteractedWith(**ge))
                else:
                    # Fallback generic
                    loaded_state["graph_edges"].append(GraphEdge(**ge))

            return loaded_state

        except Exception as e:
            logger.error(f"Failed to load graph database in worker: {e}")
            raise e

    def _migrate_legacy_data(self):
        """
        Graceful Migration Protocol:
        Converts legacy 'flat lists' (e.g., event.participants) into Explicit Graph Edges.
        Called after load() but before usage.
        """
        migration_count = 0

        # 1. Migrate CollectiveEventNode.participants -> ParticipatedIn Edges
        for event in self.collective_events.values():
            if event.participants:
                for participant_id in event.participants:
                    # Check if edge already exists to avoid duplicates
                    exists = any(
                        e.source_id == participant_id and
                        e.target_id == event.id and
                        e.type == "participatedIn"
                        for e in self.graph_edges
                    )

                    if not exists:
                        edge = ParticipatedIn(
                            source_id=participant_id,
                            target_id=event.id,
                            timestamp=event.timestamp
                        )
                        self.graph_edges.append(edge)
                        migration_count += 1

                # Clear legacy list to enforce new ontology
                # We can keep it if we want backward compat, but plan says "Mark for migration"
                # Clearing it confirms migration is done.
                event.participants = []

        if migration_count > 0:
            logger.info(f"🏗️ MIGRATION: Converted {migration_count} legacy event participants to Graph Edges.")

    async def load(self):
        """Helper to actually load data (called manually or lazily)."""

        # 1. Load Graph Data (Threaded)
        try:
             # Offload heavy JSON parsing to thread
             loaded_state = await asyncio.to_thread(self._sync_load_worker, self.data_path)

             self.users = loaded_state["users"]
             self.episodes = loaded_state["episodes"]
             self.facts = loaded_state["facts"]
             self.dreams = loaded_state["dreams"]
             self.resonances = loaded_state["resonances"]
             self.experienced = loaded_state["experienced"]
             self.knows = loaded_state["knows"]
             self.shadows = loaded_state["shadows"]
             self.archetypes = loaded_state["archetypes"]
             self.embodies = loaded_state["embodies"]
             self.global_dream = loaded_state["global_dream"]
             self.system_config = loaded_state["system_config"]
             self.locations = loaded_state["locations"]
             self.factions = loaded_state["factions"]
             self.collective_events = loaded_state["collective_events"]
             self.agent_affinities = loaded_state["agent_affinities"]
             self.graph_edges = loaded_state["graph_edges"]

             # 2. Trigger Migration
             self._migrate_legacy_data()

             logger.info(f"Graph Database loaded: {len(self.users)} Users, {len(self.graph_edges)} Edges.")

        except Exception as e:
            logger.error(f"Failed to load graph database: {e}")

        # ---------------------------------------------------------
        # Sync with Agents Directory (Source of Truth for Agents)
        # ---------------------------------------------------------
        self.agents = {}
        agents_dir = self.data_path.parent / "agents"

        def _sync_agents_worker(dir_path: Path) -> Dict[str, AgentNode]:
             agents_map = {}
             if dir_path.exists():
                 for agent_file in dir_path.glob("*.json"):
                    try:
                        with open(agent_file, "r", encoding="utf-8") as af:
                            agent_data = json.load(af)
                            agent_node = AgentNode(**agent_data)
                            agents_map[agent_node.id] = agent_node
                    except Exception as ae:
                        logger.error(f"Failed to sync agent from {agent_file}: {ae}")
             return agents_map

        try:
            self.agents = await asyncio.to_thread(_sync_agents_worker, agents_dir)
            logger.info(f"Synced {len(self.agents)} agents from filesystem.")
        except Exception as e:
            logger.error(f"Failed to sync agents: {e}")

        if not self.data_path.exists():
            await self._save()

    async def _save(self):
        """Async save using aiofiles."""
        await self._write_to_disk()

    @staticmethod
    def _sync_save_worker(path: Path, data: dict):
        """
        Synchronous worker for file I/O to be run in a separate thread.
        This isolates CPU-bound JSON serialization and blocking I/O.
        """
        temp_path = path.with_suffix(".tmp")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(temp_path, path)
        except Exception as e:
            logger.error(f"Failed to save graph database to {path}: {e}")
            if temp_path.exists():
                try:
                    os.unlink(temp_path)
                except:
                    pass

    async def _write_to_disk(self):
        # Helper to dump pydantic models to dict
        def to_dict_list(models):
             return [m.model_dump(mode='json') for m in models]

        # 1. Prepare Data
        data = {
            "users": to_dict_list(self.users.values()),
            "agents": to_dict_list(self.agents.values()),
            "episodes": to_dict_list(self.episodes.values()),
            "facts": to_dict_list(self.facts.values()),
            "dreams": to_dict_list(self.dreams.values()),
            "resonances": [
                r.model_dump(mode='json')
                for u_dict in self.resonances.values()
                for r in u_dict.values()
            ],
            "experienced": self.experienced,
            "knows": self.knows,
            "shadows": {
                uid: [e.model_dump(mode='json') for e in edges]
                for uid, edges in self.shadows.items()
            },
            "archetypes": to_dict_list(self.archetypes.values()),
            "global_dream": self.global_dream.model_dump(mode='json'),
            "system_config": self.system_config.model_dump(mode='json'),
            "embodies": {
                aid: [e.model_dump(mode='json') for e in edges]
                for aid, edges in self.embodies.items()
            },
            "locations": to_dict_list(self.locations.values()),
            "factions": to_dict_list(self.factions.values()),
            "collective_events": to_dict_list(self.collective_events.values()),
            "agent_affinities": [
                edge.model_dump(mode='json')
                for s_dict in self.agent_affinities.values()
                for edge in s_dict.values()
            ],
            # Explicit Graph Edges
            "graph_edges": [e.model_dump(mode='json') for e in self.graph_edges]
        }

        # 2. Offload Serialization & I/O to Thread Pool
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._sync_save_worker, self.data_path, data)
        except Exception as e:
            logger.error(f"Async save failed: {e}")

    # ... existing methods (get_or_create_user, update_user_last_seen, etc.) ...

    async def get_or_create_user(self, user_id: str, name: str = "Anonymous") -> UserNode:
        async with self.lock:
            if user_id in self.users:
                return self.users[user_id]
            new_user = UserNode(id=user_id, name=name)
            self.users[user_id] = new_user
            await self._save()
            return new_user

    async def update_user_last_seen(self, user_id: str):
        async with self.lock:
            if user_id in self.users:
                self.users[user_id].last_seen = datetime.now()
                await self._save()

    async def get_agent(self, agent_id: str) -> Optional[AgentNode]:
        return self.agents.get(agent_id)

    async def create_agent(self, agent: AgentNode):
        async with self.lock:
            self.agents[agent.id] = agent
            await self._save()

    def _get_resonance_unsafe(self, user_id: str, agent_id: str) -> ResonanceEdge:
        user_resonances = self.resonances.get(user_id, {})
        if agent_id in user_resonances:
            return user_resonances[agent_id]
        new_resonance = ResonanceEdge(source_id=user_id, target_id=agent_id, affinity_level=10.0)
        if user_id not in self.resonances:
            self.resonances[user_id] = {}
        self.resonances[user_id][agent_id] = new_resonance
        return new_resonance

    async def get_resonance(self, user_id: str, agent_id: str) -> ResonanceEdge:
        async with self.lock:
            resonance = self._get_resonance_unsafe(user_id, agent_id)
            await self._save()
            return resonance

    async def update_resonance(self, user_id: str, agent_id: str, delta: float) -> ResonanceEdge:
        async with self.lock:
            resonance = self._get_resonance_unsafe(user_id, agent_id)
            new_affinity = max(0.0, min(100.0, resonance.affinity_level + delta))
            resonance.affinity_level = new_affinity
            resonance.last_interaction = datetime.now()
            await self._save()
            return resonance

    @staticmethod
    def _vector_search(query_vector: List[float], candidates: List[Any], limit: int) -> List[Any]:
        if not candidates or not query_vector:
            return []
        valid_candidates = [c for c in candidates if c.embedding and len(c.embedding) == len(query_vector)]
        if not valid_candidates:
            return []
        try:
            embeddings = [c.embedding for c in valid_candidates]
            matrix = np.array(embeddings, dtype=np.float32)
            query = np.array(query_vector, dtype=np.float32)
            norm_matrix = np.linalg.norm(matrix, axis=1, keepdims=True)
            norm_matrix[norm_matrix == 0] = 1e-10
            normalized_matrix = matrix / norm_matrix
            norm_query = np.linalg.norm(query)
            if norm_query == 0:
                return []
            normalized_query = query / norm_query
            scores = np.dot(normalized_matrix, normalized_query)
            top_k_indices = np.argsort(scores)[-limit:][::-1]
            return [valid_candidates[i] for i in top_k_indices]
        except Exception as e:
            logger.error(f"Vector math error in _vector_search: {e}")
            return []

    async def save_episode(self, user_id: str, agent_id: str, summary: str, valence: float, raw_transcript: Optional[str] = None) -> MemoryEpisodeNode:
        embedding = await embedding_service.embed_text(summary)
        async with self.lock:
            episode = MemoryEpisodeNode(
                summary=summary,
                emotional_valence=valence,
                raw_transcript=raw_transcript,
                embedding=embedding
            )
            self.episodes[episode.id] = episode
            if user_id not in self.experienced:
                self.experienced[user_id] = []
            self.experienced[user_id].append(episode.id)
            user_resonances = self.resonances.get(user_id, {})
            if agent_id in user_resonances:
                resonance = user_resonances[agent_id]
            else:
                resonance = ResonanceEdge(source_id=user_id, target_id=agent_id, affinity_level=10.0)
                if user_id not in self.resonances:
                    self.resonances[user_id] = {}
                self.resonances[user_id][agent_id] = resonance
            resonance.shared_memories.append(episode.id)
            await self._save()
            return episode

    async def get_relevant_facts(self, user_id: str, query: str, limit: int = 5) -> List[FactNode]:
        if user_id not in self.knows:
            return []
        query_vector = await embedding_service.embed_text(query)
        if not query_vector:
            return []
        user_fact_ids = self.knows[user_id]
        candidates = [self.facts[fid] for fid in user_fact_ids if fid in self.facts]
        return await asyncio.to_thread(self._vector_search, query_vector, candidates, limit)

    async def save_fact(self, user_id: str, content: str, category: str) -> FactNode:
        embedding = await embedding_service.embed_text(content)
        async with self.lock:
            fact = FactNode(content=content, category=category, embedding=embedding)
            self.facts[fact.id] = fact
            if user_id not in self.knows:
                self.knows[user_id] = []
            self.knows[user_id].append(fact.id)
            await self._save()
            return fact

    async def save_dream(self, user_id: str, dream: DreamNode) -> DreamNode:
        async with self.lock:
            self.dreams[dream.id] = dream
            edge = ShadowEdge(source_id=user_id, target_id=dream.id)
            if user_id not in self.shadows:
                self.shadows[user_id] = []
            self.shadows[user_id].append(edge)
            await self._save()
            return dream

    async def consolidate_memories(self, user_id: str, dream_generator=None) -> None:
        raw_episodes = []
        async with self.lock:
            ep_ids = self.experienced.get(user_id, [])
            if not ep_ids:
                return
            for eid in ep_ids:
                ep = self.episodes.get(eid)
                if ep and abs(ep.emotional_valence) <= 1.0:
                    raw_episodes.append(ep)
            if not raw_episodes:
                return

        logger.info(f"Compressing {len(raw_episodes)} raw episodes into Long-Term Memory...")
        dream_node = None
        fallback_mode = False
        if dream_generator:
            try:
                dream_node = await dream_generator(raw_episodes)
            except Exception as e:
                logger.error(f"Failed to generate dream: {e}")
        else:
            fallback_mode = True

        async with self.lock:
            valid_episodes = [
                ep for ep in raw_episodes
                if ep.id in self.episodes and abs(ep.emotional_valence) <= 1.0
            ]
            if not valid_episodes:
                return
            if dream_node:
                self.dreams[dream_node.id] = dream_node
                edge = ShadowEdge(source_id=user_id, target_id=dream_node.id)
                if user_id not in self.shadows:
                    self.shadows[user_id] = []
                self.shadows[user_id].append(edge)
            elif fallback_mode:
                summary_text = f"User interaction summary: {len(valid_episodes)} events consolidated."
                summary_node = MemoryEpisodeNode(summary=summary_text, emotional_valence=1.0)
                self.episodes[summary_node.id] = summary_node
                self.experienced[user_id].append(summary_node.id)

            # Affinity EMA
            avg_valence = sum(ep.emotional_valence for ep in valid_episodes) / len(valid_episodes)
            agent_episode_map = {}
            user_resonances = self.resonances.get(user_id, {})
            for agent_id, resonance in user_resonances.items():
                agent_eps = [ep for ep in valid_episodes if ep.id in resonance.shared_memories]
                if agent_eps:
                    agent_episode_map[agent_id] = agent_eps

            ALPHA = 0.15
            for agent_id, eps in agent_episode_map.items():
                local_avg_valence = sum(e.emotional_valence for e in eps) / len(eps)
                local_target = 50.0 + (local_avg_valence * 50.0)
                resonance = user_resonances[agent_id]
                old_affinity = float(resonance.affinity_level)
                new_affinity = (local_target * ALPHA) + (old_affinity * (1.0 - ALPHA))
                new_affinity = max(0.0, min(100.0, new_affinity))
                resonance.affinity_level = new_affinity

            for ep in valid_episodes:
                ep.emotional_valence = 999.0

            await asyncio.shield(self._save())

    async def get_last_dream(self, user_id: str) -> Optional[DreamNode]:
        async with self.lock:
            shadow_edges = self.shadows.get(user_id, [])
            if not shadow_edges:
                return None
            last_edge = shadow_edges[-1]
            return self.dreams.get(last_edge.target_id)

    async def purge_all_memories(self) -> None:
        async with self.lock:
            self.episodes.clear()
            self.experienced.clear()
            self.dreams.clear()
            self.shadows.clear()
            for user_res in self.resonances.values():
                for resonance in user_res.values():
                    resonance.shared_memories.clear()
            await self._save()

    async def get_recent_episodes(self, user_id: str, limit: int = 10) -> List[MemoryEpisodeNode]:
        async with self.lock:
            episode_ids = self.experienced.get(user_id, [])
            if not episode_ids:
                return []
            collected_raw = []
            collected_summaries = []
            LOOKBACK_LIMIT = 50
            scanned = 0
            for eid in reversed(episode_ids):
                ep = self.episodes.get(eid)
                if not ep: continue
                if ep.raw_transcript and len(ep.raw_transcript.strip()) > 0:
                    collected_raw.append(ep)
                else:
                    collected_summaries.append(ep)
                if len(collected_raw) >= limit: break
                scanned += 1
                if scanned >= LOOKBACK_LIMIT: break
            result = collected_raw
            if len(result) < limit:
                needed = limit - len(result)
                result.extend(collected_summaries[:needed])
            result.sort(key=lambda x: x.timestamp)
            return result

    async def get_relevant_episodes(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEpisodeNode]:
        if user_id not in self.experienced:
            return []
        query_vector = await embedding_service.embed_text(query)
        if not query_vector:
            return []
        user_episode_ids = self.experienced[user_id]
        candidates = [self.episodes[eid] for eid in user_episode_ids if eid in self.episodes]
        return await asyncio.to_thread(self._vector_search, query_vector, candidates, limit)

    async def create_archetype(self, name: str, description: str, triggers: Dict) -> ArchetypeNode:
        async with self.lock:
            arc = ArchetypeNode(name=name, description=description, triggers=triggers)
            self.archetypes[arc.id] = arc
            await self._save()
            return arc

    async def get_archetype(self, name: str) -> Optional[ArchetypeNode]:
        async with self.lock:
            for arc in self.archetypes.values():
                if arc.name == name:
                    return arc
            return None

    async def link_agent_archetype(self, agent_id: str, archetype_id: str, strength: float = 1.0) -> None:
        async with self.lock:
            edge = EmbodiesEdge(source_id=agent_id, target_id=archetype_id, strength=strength)
            if agent_id not in self.embodies:
                self.embodies[agent_id] = []
            self.embodies[agent_id].append(edge)
            await self._save()

    async def get_agent_archetype(self, agent_id: str) -> Optional[ArchetypeNode]:
        async with self.lock:
            edges = self.embodies.get(agent_id, [])
            if not edges:
                return None
            edge = edges[0]
            return self.archetypes.get(edge.target_id)

    async def get_global_dream(self) -> GlobalDreamNode:
        return self.global_dream

    async def update_global_dream(self, themes: List[str], intensity: float) -> None:
        async with self.lock:
            self.global_dream.themes = themes
            self.global_dream.intensity = intensity
            self.global_dream.last_updated = datetime.now()
            await self._save()

    async def get_system_config(self) -> SystemConfigNode:
        async with self.lock:
            return self.system_config

    async def update_system_config(self, config: SystemConfigNode) -> None:
        async with self.lock:
            self.system_config = config
            await self._save()

    async def get_or_create_location(self, name: str, type: str, description: str) -> LocationNode:
        async with self.lock:
            for loc in self.locations.values():
                if loc.name == name:
                    return loc
            loc = LocationNode(name=name, type=type, description=description)
            self.locations[loc.id] = loc
            await self._save()
            return loc

    async def record_collective_event(self, event: CollectiveEventNode):
        embedding = await embedding_service.embed_text(event.summary)
        event.embedding = embedding
        async with self.lock:
            self.collective_events[event.id] = event
            await self._save()

    def _get_agent_affinity_unsafe(self, source_id: str, target_id: str) -> AgentAffinityEdge:
        source_map = self.agent_affinities.get(source_id, {})
        if target_id in source_map:
            return source_map[target_id]
        new_edge = AgentAffinityEdge(source_agent_id=source_id, target_agent_id=target_id)
        if source_id not in self.agent_affinities:
            self.agent_affinities[source_id] = {}
        self.agent_affinities[source_id][target_id] = new_edge
        return new_edge

    async def get_agent_affinity(self, source_id: str, target_id: str) -> AgentAffinityEdge:
        async with self.lock:
            edge = self._get_agent_affinity_unsafe(source_id, target_id)
            await self._save()
            return edge

    async def update_agent_affinity(self, source_id: str, target_id: str, delta: float) -> AgentAffinityEdge:
        async with self.lock:
            edge = self._get_agent_affinity_unsafe(source_id, target_id)
            new_val = max(0.0, min(100.0, edge.affinity + delta))
            edge.affinity = new_val
            edge.last_interaction = datetime.now()
            await self._save()
            return edge

    async def get_recent_collective_events(self, limit: int = 5) -> List[CollectiveEventNode]:
        async with self.lock:
            events = list(self.collective_events.values())
            events.sort(key=lambda x: x.timestamp, reverse=True)
            return events[:limit]

    async def get_agent_collective_events(self, agent_id: str, limit: int = 5) -> List[CollectiveEventNode]:
        async with self.lock:
            # Revised: Use Graph Edges to find participation
            event_ids = {
                edge.target_id for edge in self.graph_edges
                if edge.source_id == agent_id and edge.type == "participatedIn"
            }

            # Filter from main collection
            relevant_events = [
                self.collective_events[eid] for eid in event_ids
                if eid in self.collective_events
            ]

            relevant_events.sort(key=lambda x: x.timestamp, reverse=True)
            return relevant_events[:limit]

    async def get_relevant_collective_events(self, query: str, limit: int = 5) -> List[CollectiveEventNode]:
        query_vector = await embedding_service.embed_text(query)
        if not query_vector:
            return []
        async with self.lock:
            candidates = list(self.collective_events.values())
        return await asyncio.to_thread(self._vector_search, query_vector, candidates, limit)

    async def get_all_locations(self) -> List[LocationNode]:
        async with self.lock:
            return list(self.locations.values())

    # --- New Methods for Explicit Graph Edges ---

    async def create_edge(self, edge: GraphEdge) -> None:
        async with self.lock:
            self.graph_edges.append(edge)
            await self._save()

    async def get_edges(self, source_id: str = None, target_id: str = None, type: str = None) -> List[GraphEdge]:
        async with self.lock:
            results = []
            for edge in self.graph_edges:
                if source_id and edge.source_id != source_id:
                    continue
                if target_id and edge.target_id != target_id:
                    continue
                if type and edge.type != type:
                    continue
                results.append(edge)
            return results

    async def record_interaction(self, user_id: str, agent_id: str) -> None:
        """
        Records a discrete interaction (e.g., Session Start) between User and Agent.
        Creates or updates the 'InteractedWith' edge.
        This edge serves as the 'First Contact' bridge for the Roster.
        """
        async with self.lock:
            found_edge = None
            for edge in self.graph_edges:
                if edge.type == "interactedWith" and edge.source_id == user_id and edge.target_id == agent_id:
                    found_edge = edge
                    break

            if found_edge:
                # Update existing edge
                found_edge.timestamp = datetime.now()
                current_count = found_edge.properties.get("interaction_count", 0)
                found_edge.properties["interaction_count"] = current_count + 1
            else:
                # Create new edge (First Contact)
                new_edge = InteractedWith(
                    source_id=user_id,
                    target_id=agent_id,
                    timestamp=datetime.now(),
                    properties={"interaction_count": 1}
                )
                self.graph_edges.append(new_edge)

            await self._save()

    async def get_active_peers(self, user_id: str, time_window_minutes: int = 15) -> List[AgentNode]:
        """
        Finds agents who have interacted with the user or participated in events with the user
        within the given time window.
        """
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        active_agent_ids = set()

        async with self.lock:
            # 1. Check direct interactions (InteractedWith)
            for edge in self.graph_edges:
                if edge.type == "interactedWith" and edge.timestamp >= cutoff_time:
                    if edge.source_id == user_id:
                        active_agent_ids.add(edge.target_id)
                    elif edge.target_id == user_id:
                        active_agent_ids.add(edge.source_id)

            # 2. Check shared events (ParticipatedIn)
            # First find events the user participated in recently
            user_event_ids = set()
            for edge in self.graph_edges:
                if edge.type == "participatedIn" and edge.source_id == user_id and edge.timestamp >= cutoff_time:
                    user_event_ids.add(edge.target_id)

            # Then find other agents in those events
            if user_event_ids:
                for edge in self.graph_edges:
                    if edge.type == "participatedIn" and edge.target_id in user_event_ids:
                        if edge.source_id != user_id:
                            active_agent_ids.add(edge.source_id)

            # Retrieve Agent Nodes
            results = []
            for agent_id in active_agent_ids:
                if agent_id in self.agents:
                    results.append(self.agents[agent_id])
            return results

    async def get_last_interaction(self, user_id: str, agent_id: str) -> datetime:
        """
        Finds the timestamp of the last meaningful interaction (direct or shared event)
        between a user and an agent.
        """
        last_time = datetime.min

        async with self.lock:
            # 1. Direct Interactions
            for edge in self.graph_edges:
                if edge.type == "interactedWith":
                    # Check both directions
                    is_relevant = (edge.source_id == user_id and edge.target_id == agent_id) or \
                                  (edge.source_id == agent_id and edge.target_id == user_id)

                    if is_relevant and edge.timestamp > last_time:
                        last_time = edge.timestamp

            # 2. Shared Events
            # Find events for both
            user_events = {} # event_id -> timestamp
            agent_events = {} # event_id -> timestamp

            for edge in self.graph_edges:
                if edge.type == "participatedIn":
                    if edge.source_id == user_id:
                        user_events[edge.target_id] = edge.timestamp
                    elif edge.source_id == agent_id:
                        agent_events[edge.target_id] = edge.timestamp

            # Find intersection
            shared_event_ids = set(user_events.keys()) & set(agent_events.keys())
            for eid in shared_event_ids:
                # Use the later of the two timestamps (interaction completed)
                ts = max(user_events[eid], agent_events[eid])
                if ts > last_time:
                    last_time = ts

        return last_time

    async def export_to_json_ld(self) -> Dict[str, Any]:
        """
        Exports the entire graph state to a standard JSON-LD flattened format.
        Schema compliant with MyWorld / Kizuna Ontology.
        """
        async with self.lock:
            graph_objects = []

            # 1. Nodes
            graph_objects.extend([n.to_json_ld() for n in self.users.values()])
            graph_objects.extend([n.to_json_ld() for n in self.agents.values()])
            graph_objects.extend([n.to_json_ld() for n in self.episodes.values()])
            graph_objects.extend([n.to_json_ld() for n in self.facts.values()])
            graph_objects.extend([n.to_json_ld() for n in self.dreams.values()])
            graph_objects.extend([n.to_json_ld() for n in self.archetypes.values()])
            graph_objects.extend([n.to_json_ld() for n in self.locations.values()])
            graph_objects.extend([n.to_json_ld() for n in self.factions.values()])
            graph_objects.extend([n.to_json_ld() for n in self.collective_events.values()])

            # Singletons
            graph_objects.append(self.global_dream.to_json_ld())
            graph_objects.append(self.system_config.to_json_ld())

            # 2. Edges
            # Resonances
            for u_dict in self.resonances.values():
                for r in u_dict.values():
                    graph_objects.append(r.to_json_ld())

            # Shadows
            for edges in self.shadows.values():
                for s in edges:
                    graph_objects.append(s.to_json_ld())

            # Embodies
            for edges in self.embodies.values():
                for e in edges:
                    graph_objects.append(e.to_json_ld())

            # Agent Affinities
            for s_dict in self.agent_affinities.values():
                for a in s_dict.values():
                    graph_objects.append(a.to_json_ld())

            # Explicit Graph Edges
            for edge in self.graph_edges:
                graph_objects.append(edge.to_json_ld())

            # Experienced (Derived to Explicit)
            for uid, eps in self.experienced.items():
                for eid in eps:
                    edge = ExperiencedEdge(source_id=uid, target_id=eid)
                    graph_objects.append(edge.to_json_ld())

            # Knows (Derived to Explicit)
            for uid, facts in self.knows.items():
                for fid in facts:
                    edge = KnowsEdge(source_id=uid, target_id=fid)
                    graph_objects.append(edge.to_json_ld())

            return {
                "@context": "https://myworld.kizuna/ontology",
                "@graph": graph_objects
            }

    async def import_from_json_ld(self, data: Dict[str, Any]) -> None:
        """
        Imports a JSON-LD graph, replacing the current state.
        Performs a safety backup before overwriting.
        Transactional: Validates entire dataset before applying changes.
        """
        if "@graph" not in data or not isinstance(data["@graph"], list):
            raise ValueError("Invalid JSON-LD: Missing '@graph' array.")

        # 1. Prepare Temporary State (Transactional Staging)
        staging = {
            "users": {},
            "agents": {},
            "episodes": {},
            "facts": {},
            "dreams": {},
            "resonances": {},
            "experienced": {},
            "knows": {},
            "shadows": {},
            "archetypes": {},
            "embodies": {},
            "locations": {},
            "factions": {},
            "collective_events": {},
            "agent_affinities": {},
            "graph_edges": [],
            "global_dream": GlobalDreamNode(),
            "system_config": SystemConfigNode()
        }

        count = 0
        try:
            for item in data["@graph"]:
                obj_type = item.get("@type")
                if not obj_type:
                    continue

                if obj_type == "UserNode":
                    node = UserNode(**item)
                    staging["users"][node.id] = node
                elif obj_type == "AgentNode":
                    node = AgentNode(**item)
                    staging["agents"][node.id] = node
                elif obj_type == "MemoryEpisodeNode":
                    node = MemoryEpisodeNode(**item)
                    staging["episodes"][node.id] = node
                elif obj_type == "FactNode":
                    node = FactNode(**item)
                    staging["facts"][node.id] = node
                elif obj_type == "DreamNode":
                    node = DreamNode(**item)
                    staging["dreams"][node.id] = node
                elif obj_type == "ArchetypeNode":
                    node = ArchetypeNode(**item)
                    staging["archetypes"][node.id] = node
                elif obj_type == "LocationNode":
                    node = LocationNode(**item)
                    staging["locations"][node.id] = node
                elif obj_type == "FactionNode":
                    node = FactionNode(**item)
                    staging["factions"][node.id] = node
                elif obj_type == "CollectiveEventNode":
                    node = CollectiveEventNode(**item)
                    staging["collective_events"][node.id] = node
                elif obj_type == "GlobalDreamNode":
                    staging["global_dream"] = GlobalDreamNode(**item)
                elif obj_type == "SystemConfigNode":
                    staging["system_config"] = SystemConfigNode(**item)

                # Edges
                elif obj_type == "ResonanceEdge":
                    edge = ResonanceEdge(**item)
                    if edge.source_id not in staging["resonances"]:
                        staging["resonances"][edge.source_id] = {}
                    staging["resonances"][edge.source_id][edge.target_id] = edge

                elif obj_type == "ShadowEdge":
                    edge = ShadowEdge(**item)
                    if edge.source_id not in staging["shadows"]:
                        staging["shadows"][edge.source_id] = []
                    staging["shadows"][edge.source_id].append(edge)

                elif obj_type == "EmbodiesEdge":
                    edge = EmbodiesEdge(**item)
                    if edge.source_id not in staging["embodies"]:
                        staging["embodies"][edge.source_id] = []
                    staging["embodies"][edge.source_id].append(edge)

                elif obj_type == "AgentAffinityEdge":
                    edge = AgentAffinityEdge(**item)
                    if edge.source_agent_id not in staging["agent_affinities"]:
                        staging["agent_affinities"][edge.source_agent_id] = {}
                    staging["agent_affinities"][edge.source_agent_id][edge.target_agent_id] = edge

                elif obj_type == "ExperiencedEdge":
                    edge = ExperiencedEdge(**item)
                    if edge.source_id not in staging["experienced"]:
                        staging["experienced"][edge.source_id] = []
                    # Ensure no duplicates
                    if edge.target_id not in staging["experienced"][edge.source_id]:
                            staging["experienced"][edge.source_id].append(edge.target_id)

                elif obj_type == "KnowsEdge":
                    edge = KnowsEdge(**item)
                    if edge.source_id not in staging["knows"]:
                        staging["knows"][edge.source_id] = []
                    if edge.target_id not in staging["knows"][edge.source_id]:
                        staging["knows"][edge.source_id].append(edge.target_id)

                elif obj_type in ["ParticipatedIn", "OccurredAt", "InteractedWith", "GraphEdge"]:
                    if obj_type == "ParticipatedIn":
                        staging["graph_edges"].append(ParticipatedIn(**item))
                    elif obj_type == "OccurredAt":
                        staging["graph_edges"].append(OccurredAt(**item))
                    elif obj_type == "InteractedWith":
                        staging["graph_edges"].append(InteractedWith(**item))
                    else:
                        staging["graph_edges"].append(GraphEdge(**item))

                count += 1

        except Exception as e:
             logger.error(f"Import validation failed at item {count}: {e}")
             raise ValueError(f"Import failed: Invalid data at item {count}. {str(e)}")

        # 2. Safety Backup (Only if validation passed)
        if self.data_path.exists():
            timestamp = int(time.time())
            backup_path = self.data_path.with_name(f"graph_backup_{timestamp}.json")
            try:
                shutil.copy2(self.data_path, backup_path)
                logger.info(f"🛡️ Backup created at {backup_path}")
            except Exception as e:
                logger.error(f"Failed to create backup: {e}")
                raise RuntimeError("Backup failed. Aborting import to protect data.")

        async with self.lock:
            # 3. Atomic Swap
            self.users = staging["users"]
            self.agents = staging["agents"]
            self.episodes = staging["episodes"]
            self.facts = staging["facts"]
            self.dreams = staging["dreams"]
            self.resonances = staging["resonances"]
            self.experienced = staging["experienced"]
            self.knows = staging["knows"]
            self.shadows = staging["shadows"]
            self.archetypes = staging["archetypes"]
            self.embodies = staging["embodies"]
            self.locations = staging["locations"]
            self.factions = staging["factions"]
            self.collective_events = staging["collective_events"]
            self.agent_affinities = staging["agent_affinities"]
            self.graph_edges = staging["graph_edges"]

            self.global_dream = staging["global_dream"]
            self.system_config = staging["system_config"]

            # 4. Persist
            await self._save()
            logger.info(f"Import complete. Restored {count} nodes/edges.")

    # --- Phase 6.5 Legacy Stubs (to satisfy interface) ---
    async def get_gossip_candidates(self, exclude_ids: List[str], limit: int = 3) -> List[AgentNode]:
        return []

    async def get_nemesis_agents(self, user_id: str) -> List[AgentNode]:
        return []

    async def update_agent_friction(self, agent_id: str, delta: float) -> float:
        return 0.0
