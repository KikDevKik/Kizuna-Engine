import json
import logging
import asyncio
import aiofiles
import os
import math
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

from .base import SoulRepository
from ..services.embedding import embedding_service
from ..models.graph import (
    UserNode, AgentNode, ResonanceEdge, MemoryEpisodeNode, FactNode,
    DreamNode, ShadowEdge, ArchetypeNode, GlobalDreamNode, EmbodiesEdge,
    SystemConfigNode
)

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

                # NOTE: We intentionally DO NOT load agents from graph.json.
                # The 'agents' directory is the single source of truth.
                # This prevents "ghost agents" (deleted from disk but remaining in graph.json) from persisting.
                # self.agents will be populated strictly from the filesystem below.

                for e in data.get("episodes", []):
                    node = MemoryEpisodeNode(**e)
                    self.episodes[node.id] = node

                for f in data.get("facts", []):
                    node = FactNode(**f)
                    self.facts[node.id] = node

                for d in data.get("dreams", []):
                    node = DreamNode(**d)
                    self.dreams[node.id] = node

                # Hydrate Edges
                for r in data.get("resonances", []):
                    edge = ResonanceEdge(**r)
                    if edge.source_id not in self.resonances:
                        self.resonances[edge.source_id] = {}
                    self.resonances[edge.source_id][edge.target_id] = edge

                self.experienced = data.get("experienced", {})
                self.knows = data.get("knows", {})

                # Hydrate Shadows
                self.shadows = {}
                for uid, edges in data.get("shadows", {}).items():
                    self.shadows[uid] = [ShadowEdge(**e) for e in edges]

                # Hydrate Archetypes (Phase 1)
                for a in data.get("archetypes", []):
                    node = ArchetypeNode(**a)
                    self.archetypes[node.id] = node

                if "global_dream" in data:
                    self.global_dream = GlobalDreamNode(**data["global_dream"])

                # Hydrate System Config (Phase 2)
                if "system_config" in data:
                    self.system_config = SystemConfigNode(**data["system_config"])
                else:
                    # Default values (matches previous hardcoded constants)
                    self.system_config = SystemConfigNode()

                # Hydrate Embodies
                self.embodies = {}
                for aid, edges in data.get("embodies", {}).items():
                    self.embodies[aid] = [EmbodiesEdge(**e) for e in edges]

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

        # Clear in-memory agents to ensure we strictly mirror the filesystem.
        # This removes "ghost agents" that were deleted from disk.
        self.agents = {}

        agents_dir = self.data_path.parent / "agents"
        if agents_dir.exists():
            loaded_count = 0
            for agent_file in agents_dir.glob("*.json"):
                try:
                    with open(agent_file, "r", encoding="utf-8") as af:
                        agent_data = json.load(af)
                        agent_node = AgentNode(**agent_data)
                        # Source of Truth: Filesystem
                        self.agents[agent_node.id] = agent_node
                        loaded_count += 1
                except Exception as ae:
                    logger.error(f"Failed to sync agent from {agent_file}: {ae}")
            logger.info(f"Synced {loaded_count} agents from filesystem.")

        # Ensure graph.json is initialized if it didn't exist
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
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # CPU-bound serialization + Blocking I/O
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)

            # Atomic replacement (Blocking)
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
        # 1. Prepare Data (Fast in-memory construction)
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
            }
        }

        # 2. Offload Serialization & I/O to Thread Pool
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._sync_save_worker, self.data_path, data)
        except Exception as e:
            logger.error(f"Async save failed: {e}")

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

            # Default Resonance (Starts at 10.0 - Stranger/Warm)
            # Was 50.0 (Friend/Neutral), but we want procedural growth starting from stranger.
            new_resonance = ResonanceEdge(source_id=user_id, target_id=agent_id, affinity_level=10.0)
            if user_id not in self.resonances:
                self.resonances[user_id] = {}
            self.resonances[user_id][agent_id] = new_resonance
            await self._save()
            return new_resonance

    async def update_resonance(self, user_id: str, agent_id: str, delta: float) -> ResonanceEdge:
        async with self.lock:
            resonance = await self.get_resonance(user_id, agent_id)
            # Apply delta
            new_affinity = resonance.affinity_level + delta

            # Clamp between 0.0 and 100.0
            new_affinity = max(0.0, min(100.0, new_affinity))

            resonance.affinity_level = new_affinity
            resonance.last_interaction = datetime.now()

            # Save logic handled by reference update in dict, but need to persist to disk
            await self._save()
            logger.info(f"Resonance updated for User {user_id} -> Agent {agent_id}: {new_affinity}")
            return resonance

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        Calculates the Cosine Similarity between two vectors.
        Range: -1.0 to 1.0 (where 1.0 is identical).
        """
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude_v1 = math.sqrt(sum(a * a for a in v1))
        magnitude_v2 = math.sqrt(sum(b * b for b in v2))

        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0

        return dot_product / (magnitude_v1 * magnitude_v2)

    async def save_episode(self, user_id: str, agent_id: str, summary: str, valence: float, raw_transcript: Optional[str] = None) -> MemoryEpisodeNode:
        # Generate embedding asynchronously (outside lock to avoid blocking)
        embedding = await embedding_service.embed_text(summary)

        async with self.lock:
            episode = MemoryEpisodeNode(
                summary=summary,
                emotional_valence=valence,
                raw_transcript=raw_transcript,
                embedding=embedding
            )
            self.episodes[episode.id] = episode

            # Link to User
            if user_id not in self.experienced:
                self.experienced[user_id] = []
            self.experienced[user_id].append(episode.id)

            # Update Resonance with this shared memory
            # Access self.resonances directly since we already hold self.lock
            user_resonances = self.resonances.get(user_id, {})
            if agent_id in user_resonances:
                resonance = user_resonances[agent_id]
            else:
                # Default Resonance (Starts at 10.0 - Stranger/Warm)
                resonance = ResonanceEdge(source_id=user_id, target_id=agent_id, affinity_level=10.0)
                if user_id not in self.resonances:
                    self.resonances[user_id] = {}
                self.resonances[user_id][agent_id] = resonance

            resonance.shared_memories.append(episode.id)

            await self._save()
            return episode

    async def get_relevant_facts(self, user_id: str, query: str, limit: int = 5) -> List[FactNode]:
        """
        Semantic Search using Cosine Similarity.
        Replaces basic keyword matching with local vector search.
        """
        if user_id not in self.knows:
            return []

        # 1. Generate Query Vector
        query_vector = await embedding_service.embed_text(query)
        if not query_vector:
            logger.warning("Failed to generate embedding for query in local RAG.")
            return []

        user_fact_ids = self.knows[user_id]
        scored_facts = []

        # 2. Iterate and Rank
        for fact_id in user_fact_ids:
            fact = self.facts.get(fact_id)
            if not fact or not fact.embedding:
                # Skip facts without embeddings (pre-vector era)
                continue

            similarity = self._cosine_similarity(query_vector, fact.embedding)
            scored_facts.append((similarity, fact))

        # 3. Sort by Similarity (Descending)
        scored_facts.sort(key=lambda x: x[0], reverse=True)

        # 4. Return Top K
        return [item[1] for item in scored_facts[:limit]]

    async def save_fact(self, user_id: str, content: str, category: str) -> FactNode:
        # Generate embedding asynchronously
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

            # Create Shadow Edge
            edge = ShadowEdge(source_id=user_id, target_id=dream.id)
            if user_id not in self.shadows:
                self.shadows[user_id] = []
            self.shadows[user_id].append(edge)

            await self._save()
            return dream

    async def consolidate_memories(self, user_id: str, dream_generator=None) -> None:
        """
        Consolidate memories for the user (Event-Driven Debounce).
        Simulates compressing recent episodes.
        """
        # PHASE 1: Identification (Lock held)
        raw_episodes = []
        async with self.lock:
            ep_ids = self.experienced.get(user_id, [])
            if not ep_ids:
                logger.info(f"No memories to consolidate for {user_id}.")
                return

            # Simulate LLM Clustering & Compression (Mock)
            # Find all unprocessed episodes (valence != 999.0)
            # We use 999.0 to mark 'Archived' since 0.0 is valid Neutral valence.
            for eid in ep_ids:
                ep = self.episodes.get(eid)
                if ep and abs(ep.emotional_valence) <= 1.0: # Valid range -1.0 to 1.0
                    raw_episodes.append(ep)

            if not raw_episodes:
                logger.info("No RAW episodes to consolidate.")
                return

            # NOTE: We hold references to `raw_episodes`. If another thread modifies them,
            # we see the changes. We release the lock now to allow other operations.

        logger.info(f"Compressing {len(raw_episodes)} raw episodes into Long-Term Memory...")

        # PHASE 2: Generation (Lock released - Async IO)
        dream_node = None
        fallback_mode = False

        if dream_generator:
            # Lucid Dreaming Protocol
            try:
                # 🏰 BASTION SHIELD: Execute slow network call OUTSIDE the lock to prevent deadlock
                dream_node = await dream_generator(raw_episodes)
            except Exception as e:
                logger.error(f"Failed to generate dream: {e}")
        else:
            fallback_mode = True

        # PHASE 3: Commit (Lock re-acquired)
        async with self.lock:
            # Re-verify existence (Race Condition with Purge)
            # Only process episodes that still exist AND are not already archived (Race Condition: Double Process)
            valid_episodes = [
                ep for ep in raw_episodes
                if ep.id in self.episodes and abs(ep.emotional_valence) <= 1.0
            ]

            if not valid_episodes:
                logger.warning(f"Consolidation aborted for {user_id}: Episodes no longer valid (Purged/Archived?).")
                return

            if dream_node:
                self.dreams[dream_node.id] = dream_node

                # Link Shadow Edge
                edge = ShadowEdge(source_id=user_id, target_id=dream_node.id)
                if user_id not in self.shadows:
                    self.shadows[user_id] = []
                self.shadows[user_id].append(edge)
                logger.info(f"✨ Generated Dream: {dream_node.theme} (Intensity: {dream_node.intensity})")

            elif fallback_mode:
                # Fallback: Create Summary Episode (The "Dream")
                summary_text = f"User interaction summary: {len(valid_episodes)} events consolidated."
                summary_node = MemoryEpisodeNode(
                    summary=summary_text,
                    emotional_valence=1.0 # Consolidated/Refined
                )
                self.episodes[summary_node.id] = summary_node

                # 2. Link Summary to User
                self.experienced[user_id].append(summary_node.id)

            # 4. Trigger Affinity Decay/Growth (Mathematical recalibration)
            # Exponential Moving Average (EMA)
            # NOTE: Must be done BEFORE archiving episodes so we have the correct valence.

            # Calculate Average Valence (-1.0 to 1.0)
            avg_valence = sum(ep.emotional_valence for ep in valid_episodes) / len(valid_episodes)

            # FIX: We need to know the agent.
            # `save_episode` links User->Episode.
            # `ResonanceEdge` has `shared_memories` (list of Episode IDs).
            # We can reverse lookup: For each episode, find which agent lists it in `shared_memories`.

            agent_episode_map = {} # {agent_id: [episodes]}

            # This is expensive in a big graph but fine for local.
            # Iterate all agents -> resonances for this user -> check shared_memories.
            user_resonances = self.resonances.get(user_id, {})

            for agent_id, resonance in user_resonances.items():
                agent_eps = []
                for ep in valid_episodes:
                    if ep.id in resonance.shared_memories:
                        agent_eps.append(ep)
                if agent_eps:
                    agent_episode_map[agent_id] = agent_eps

            # Now calculate EMA per agent
            ALPHA = 0.15

            for agent_id, eps in agent_episode_map.items():
                if not eps: continue

                # Avg valence for this agent's episodes
                local_avg_valence = sum(e.emotional_valence for e in eps) / len(eps)

                # Map Valence to Target Signal (0-100)
                # -1.0 -> 0.0
                #  0.0 -> 50.0
                #  1.0 -> 100.0
                local_target = 50.0 + (local_avg_valence * 50.0)

                # Get current affinity
                resonance = user_resonances[agent_id]
                old_affinity = float(resonance.affinity_level)

                # EMA Formula
                new_affinity = (local_target * ALPHA) + (old_affinity * (1.0 - ALPHA))

                # Clamp
                new_affinity = max(0.0, min(100.0, new_affinity))

                resonance.affinity_level = new_affinity
                logger.info(f"📉 Affinity EMA Updated for {agent_id}: {old_affinity:.2f} -> {new_affinity:.2f} (Target: {local_target:.2f})")

            # 3. Mark Raw Episodes as archived (or delete them to save space)
            # We use 999.0 to indicate processed/archived state
            for ep in valid_episodes:
                ep.emotional_valence = 999.0 # Archived state

            # Shield the save operation as it's critical state persistence
            await asyncio.shield(self._save())

    async def get_last_dream(self, user_id: str) -> Optional[DreamNode]:
        """Retrieve the last dream generated for this user."""
        async with self.lock:
            shadow_edges = self.shadows.get(user_id, [])
            if not shadow_edges:
                return None

            # The edges are appended chronologically, so the last one is the most recent
            last_edge = shadow_edges[-1]
            return self.dreams.get(last_edge.target_id)

    async def purge_all_memories(self) -> None:
        """
        SCORCHED EARTH PROTOCOL: Wipes all episodic memory and dreams.
        Preserves Identity (Users/Agents) and Facts (Knowledge).
        """
        async with self.lock:
            logger.warning("☢️ SCORCHED EARTH: Purging all memories...")

            # Clear Episodic Memory
            self.episodes.clear()
            self.experienced.clear()

            # Clear Dreams & Shadows
            self.dreams.clear()
            self.shadows.clear()

            # Clear Shared Memories in Resonances (Keep Affinities)
            for user_res in self.resonances.values():
                for resonance in user_res.values():
                    resonance.shared_memories.clear()

            await self._save()
            logger.info("☢️ Memory Purge Complete.")

    async def get_recent_episodes(self, user_id: str, limit: int = 10) -> List[MemoryEpisodeNode]:
        """
        Retrieve recent episodes (short-term memory).
        Archivist Patch: Implements 'Verbatim Priority' to ensure raw transcripts are not
        displaced by consolidation summaries.
        """
        async with self.lock:
            episode_ids = self.experienced.get(user_id, [])
            if not episode_ids:
                return []

            # Scan backwards to find relevant episodes with Verbatim Priority
            collected_raw = []
            collected_summaries = []

            # We want to fill 'limit' slots.
            # We scan deeper than 'limit' to skip over potential summaries if needed.
            # Arbitrary lookback limit to prevent infinite scan on huge history
            LOOKBACK_LIMIT = 50
            scanned = 0

            for eid in reversed(episode_ids):
                ep = self.episodes.get(eid)
                if not ep:
                    continue

                if ep.raw_transcript and len(ep.raw_transcript.strip()) > 0:
                    collected_raw.append(ep)
                else:
                    collected_summaries.append(ep)

                # If we have filled the quota with raw transcripts, we are done.
                if len(collected_raw) >= limit:
                    break

                scanned += 1
                if scanned >= LOOKBACK_LIMIT:
                    break

            # Construct result: Prioritize raw, backfill with summaries
            result = collected_raw

            if len(result) < limit:
                needed = limit - len(result)
                # Take the most recent summaries available
                result.extend(collected_summaries[:needed])

            # Restore chronological order (since we collected backwards)
            # Sorting by timestamp ensures correct flow regardless of mix
            result.sort(key=lambda x: x.timestamp)

            return result

    async def get_relevant_episodes(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEpisodeNode]:
        """
        Semantic Search for Long-Term Memory (Episodes).
        Uses local cosine similarity.
        """
        if user_id not in self.experienced:
            return []

        # 1. Generate Query Vector
        query_vector = await embedding_service.embed_text(query)
        if not query_vector:
            logger.warning("Failed to generate embedding for query in local Episode RAG.")
            return []

        user_episode_ids = self.experienced[user_id]
        scored_episodes = []

        # 2. Iterate and Rank
        for eid in user_episode_ids:
            ep = self.episodes.get(eid)
            # We filter out archived episodes (valence=999.0) if we only want active memory,
            # but usually RAG should search ALL history including archived ones.
            # However, for now, let's search everything that has an embedding.
            if not ep or not ep.embedding:
                continue

            similarity = self._cosine_similarity(query_vector, ep.embedding)
            scored_episodes.append((similarity, ep))

        # 3. Sort by Similarity (Descending)
        scored_episodes.sort(key=lambda x: x[0], reverse=True)

        return [item[1] for item in scored_episodes[:limit]]

    # --- Evolution Phase 1: Ontology & Archetypes (Mock for Local) ---

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
            # Return first one
            edge = edges[0]
            return self.archetypes.get(edge.target_id)

    # --- Evolution Phase 1: Global Dream (Mock for Local) ---

    async def get_global_dream(self) -> GlobalDreamNode:
        return self.global_dream

    async def update_global_dream(self, themes: List[str], intensity: float) -> None:
        async with self.lock:
            self.global_dream.themes = themes
            self.global_dream.intensity = intensity
            self.global_dream.last_updated = datetime.now()
            await self._save()

    # --- Evolution Phase 2: System Config (Local) ---

    async def get_system_config(self) -> SystemConfigNode:
        """Fetch the System Configuration (Singleton)."""
        async with self.lock:
            # Already initialized in __init__ or load()
            return self.system_config

    async def update_system_config(self, config: SystemConfigNode) -> None:
        """Update the System Configuration."""
        async with self.lock:
            self.system_config = config
            await self._save()
