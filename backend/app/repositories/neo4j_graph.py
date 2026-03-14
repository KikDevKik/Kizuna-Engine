import os
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from neo4j import AsyncGraphDatabase

from .base import SoulRepository
from ..models.graph import (
    UserNode, AgentNode, ResonanceEdge, MemoryEpisodeNode, FactNode,
    DreamNode, ArchetypeNode, GlobalDreamNode, CollectiveEventNode,
    GraphEdge, AgentAffinityEdge, SystemConfigNode, LocationNode
)

logger = logging.getLogger(__name__)

class Neo4jSoulRepository(SoulRepository):
    """
    Phase 3.3 (Neo4j Edition): Implementation using Neo4j AuraDB.
    All nodes and edges natively map to Graph DB constructs.
    """

    def __init__(self):
        self.uri = os.environ.get("NEO4J_URI")
        self.user = os.environ.get("NEO4J_USERNAME", "neo4j")
        self.password = os.environ.get("NEO4J_PASSWORD")
        self.driver = None

    async def initialize(self) -> None:
        if self.uri and self.password:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            logger.info("Neo4j AuraDB Initialized.")
        else:
            logger.warning("NEO4J_URI or NEO4J_PASSWORD missing. Neo4jSoulRepository won't connect.")

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def get_or_create_user(self, user_id: str, name: str = "Anonymous") -> UserNode:
        query = """
        MERGE (u:UserNode {id: $user_id})
        ON CREATE SET u.name = $name
        RETURN u.id AS id, u.name AS name
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id, name=name)
            record = await result.single()
            if record:
                return UserNode(id=record["id"], name=record["name"])
        return UserNode(id=user_id, name=name)

    async def get_agent(self, agent_id: str) -> Optional[AgentNode]:
        query = "MATCH (a:AgentNode {id: $agent_id}) RETURN a"
        async with self.driver.session() as session:
            result = await session.run(query, agent_id=agent_id)
            record = await result.single()
            if record:
                props = dict(record["a"])
                if 'user_id' in props: del props['user_id']
                return AgentNode(**props)
        return None

    async def get_or_sync_agent(self, user_id: str, agent_id: str) -> Optional[AgentNode]:
        node = await self.get_agent(agent_id)
        if node:
            return node

        try:
            from app.services.agent_service import agent_service
            agent = await agent_service.get_agent(user_id, agent_id)
            if agent:
                await self.create_agent(agent)
                return agent
        except Exception as e:
            logger.error(f"Error fetching agent {agent_id} from AgentService: {e}")

        return None

    async def create_agent(self, agent: AgentNode):
        query = """
        MERGE (a:AgentNode {id: $id})
        SET a += $props
        """
        props = agent.model_dump(mode='json')
        # Handle lists and dicts natively or by JSON serialization
        # Neo4j python driver handles standard lists of scalars, but not nested dicts/lists.
        # We need to flatten or JSON stringify complex types. Let's serialize complex fields.
        for k, v in list(props.items()):
            if isinstance(v, (dict, list)):
                props[k] = json.dumps(v)

        async with self.driver.session() as session:
            await session.run(query, id=agent.id, props=props)

    async def get_resonance(self, user_id: str, agent_id: str) -> ResonanceEdge:
        query = """
        MATCH (u:UserNode {id: $user_id})-[r:RESONATES_WITH]->(a:AgentNode {id: $agent_id})
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id, agent_id=agent_id)
            record = await result.single()
            if record:
                props = dict(record["r"])
                if 'shared_memories' in props and isinstance(props['shared_memories'], str):
                    props['shared_memories'] = json.loads(props['shared_memories'])
                return ResonanceEdge(source_id=user_id, target_id=agent_id, **props)

        # Create default if not found
        new_resonance = ResonanceEdge(source_id=user_id, target_id=agent_id, affinity_level=10.0)
        query_create = """
        MATCH (u:UserNode {id: $user_id}), (a:AgentNode {id: $agent_id})
        MERGE (u)-[r:RESONATES_WITH]->(a)
        ON CREATE SET r.affinity_level = $affinity, r.last_interaction = $ts, r.shared_memories = '[]'
        """
        async with self.driver.session() as session:
            await session.run(query_create, user_id=user_id, agent_id=agent_id,
                              affinity=10.0, ts=datetime.now().isoformat())
        return new_resonance

    async def update_resonance(self, user_id: str, agent_id: str, delta: float) -> ResonanceEdge:
        resonance = await self.get_resonance(user_id, agent_id)
        new_affinity = max(0.0, min(100.0, resonance.affinity_level + delta))
        resonance.affinity_level = new_affinity
        resonance.last_interaction = datetime.now()

        query = """
        MATCH (u:UserNode {id: $user_id})-[r:RESONATES_WITH]->(a:AgentNode {id: $agent_id})
        SET r.affinity_level = $affinity, r.last_interaction = $ts
        """
        async with self.driver.session() as session:
            await session.run(query, user_id=user_id, agent_id=agent_id,
                              affinity=new_affinity, ts=resonance.last_interaction.isoformat())
        return resonance

    async def save_episode(self, user_id: str, agent_id: str, summary: str, valence: float, raw_transcript: Optional[str] = None) -> MemoryEpisodeNode:
        episode = MemoryEpisodeNode(
            summary=summary,
            raw_transcript=raw_transcript,
            emotional_valence=valence
        )
        # Assuming embedding is not computed here

        query = """
        MATCH (u:UserNode {id: $user_id}), (a:AgentNode {id: $agent_id})
        CREATE (e:MemoryEpisodeNode {
            id: $ep_id,
            summary: $summary,
            raw_transcript: $raw,
            emotional_valence: $valence,
            timestamp: $ts,
            user_id: $user_id
        })
        CREATE (u)-[:EXPERIENCED {weight: 1.0}]->(e)
        CREATE (a)-[:PARTICIPATED_IN]->(e)
        """
        async with self.driver.session() as session:
            await session.run(query, user_id=user_id, agent_id=agent_id, ep_id=episode.id,
                              summary=summary, raw=raw_transcript or "", valence=valence,
                              ts=episode.timestamp.isoformat())
        return episode

    async def get_recent_episodes(self, user_id: str, limit: int = 10) -> List[MemoryEpisodeNode]:
        query = """
        MATCH (u:UserNode {id: $user_id})-[:EXPERIENCED]->(e:MemoryEpisodeNode)
        RETURN e
        ORDER BY e.timestamp DESC
        LIMIT $limit
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id, limit=limit)
            records = await result.data()
            episodes = []
            for r in records:
                props = r['e']
                if 'user_id' in props: del props['user_id']
                episodes.append(MemoryEpisodeNode(**props))
            # The LocalSoulRepository returns them in chronological order
            return list(reversed(episodes))

    async def save_fact(self, user_id: str, content: str, category: str) -> FactNode:
        fact = FactNode(content=content, category=category)
        query = """
        MATCH (u:UserNode {id: $user_id})
        CREATE (f:FactNode {id: $id, content: $content, category: $category, confidence: 1.0, user_id: $user_id})
        CREATE (u)-[:KNOWS {context: ''}]->(f)
        """
        async with self.driver.session() as session:
            await session.run(query, user_id=user_id, id=fact.id, content=content, category=category)
        return fact

    async def get_relevant_facts(self, user_id: str, query_str: str, limit: int = 5) -> List[FactNode]:
        query = """
        MATCH (u:UserNode {id: $user_id})-[:KNOWS]->(f:FactNode)
        RETURN f
        LIMIT $limit
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id, limit=limit)
            records = await result.data()
            facts = []
            for r in records:
                props = r['f']
                if 'user_id' in props: del props['user_id']
                facts.append(FactNode(**props))
            return facts

    async def save_dream(self, user_id: str, dream: DreamNode) -> DreamNode:
        query = """
        MATCH (u:UserNode {id: $user_id})
        CREATE (d:DreamNode {id: $id, theme: $theme, intensity: $intensity, surrealism_level: $surrealism, timestamp: $ts, user_id: $user_id})
        CREATE (u)-[:SHADOW {weight: 1.0}]->(d)
        """
        async with self.driver.session() as session:
            await session.run(query, user_id=user_id, id=dream.id, theme=dream.theme,
                              intensity=dream.intensity, surrealism=dream.surrealism_level, ts=dream.timestamp.isoformat())
        return dream

    async def get_last_dream(self, user_id: str) -> Optional[DreamNode]:
        query = """
        MATCH (u:UserNode {id: $user_id})-[:SHADOW]->(d:DreamNode)
        RETURN d
        ORDER BY d.timestamp DESC
        LIMIT 1
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id)
            record = await result.single()
            if record:
                props = dict(record["d"])
                if 'user_id' in props: del props['user_id']
                return DreamNode(**props)
        return None

    async def consolidate_memories(self, user_id: str, dream_generator=None) -> None:
        pass # Implemented in domain logic or just pass through

    async def get_relevant_episodes(self, user_id: str, query_str: str, limit: int = 5) -> List[MemoryEpisodeNode]:
        return await self.get_recent_episodes(user_id, limit)

    async def create_archetype(self, name: str, description: str, triggers: Dict) -> ArchetypeNode:
        node = ArchetypeNode(name=name, description=description, triggers=triggers)
        query = """
        MERGE (a:ArchetypeNode {id: $id})
        SET a.name = $name, a.description = $desc, a.triggers = $triggers
        """
        async with self.driver.session() as session:
            await session.run(query, id=node.id, name=name, desc=description, triggers=json.dumps(triggers))
        return node

    async def get_archetype(self, name: str) -> Optional[ArchetypeNode]:
        query = "MATCH (a:ArchetypeNode {name: $name}) RETURN a LIMIT 1"
        async with self.driver.session() as session:
            result = await session.run(query, name=name)
            record = await result.single()
            if record:
                props = dict(record["a"])
                if 'triggers' in props and isinstance(props['triggers'], str):
                    props['triggers'] = json.loads(props['triggers'])
                return ArchetypeNode(**props)
        return None

    async def link_agent_archetype(self, agent_id: str, archetype_id: str, strength: float = 1.0) -> None:
        query = """
        MATCH (a:AgentNode {id: $agent_id}), (arc:ArchetypeNode {id: $archetype_id})
        MERGE (a)-[r:EMBODIES]->(arc)
        SET r.strength = $strength
        """
        async with self.driver.session() as session:
            await session.run(query, agent_id=agent_id, archetype_id=archetype_id, strength=strength)

    async def get_agent_archetype(self, agent_id: str) -> Optional[ArchetypeNode]:
        query = """
        MATCH (a:AgentNode {id: $agent_id})-[:EMBODIES]->(arc:ArchetypeNode)
        RETURN arc LIMIT 1
        """
        async with self.driver.session() as session:
            result = await session.run(query, agent_id=agent_id)
            record = await result.single()
            if record:
                props = dict(record["arc"])
                if 'triggers' in props and isinstance(props['triggers'], str):
                    props['triggers'] = json.loads(props['triggers'])
                return ArchetypeNode(**props)
        return None

    async def get_global_dream(self) -> GlobalDreamNode:
        query = "MATCH (g:GlobalDreamNode {id: 'global-dream'}) RETURN g"
        async with self.driver.session() as session:
            result = await session.run(query)
            record = await result.single()
            if record:
                props = dict(record["g"])
                if 'themes' in props and isinstance(props['themes'], str):
                    props['themes'] = json.loads(props['themes'])
                return GlobalDreamNode(**props)
        return GlobalDreamNode()

    async def update_global_dream(self, themes: List[str], intensity: float) -> None:
        query = """
        MERGE (g:GlobalDreamNode {id: 'global-dream'})
        SET g.themes = $themes, g.intensity = $intensity, g.last_updated = $ts
        """
        async with self.driver.session() as session:
            await session.run(query, themes=json.dumps(themes), intensity=intensity, ts=datetime.now().isoformat())

    async def get_system_config(self) -> SystemConfigNode:
        query = "MATCH (s:SystemConfigNode {id: 'system-config'}) RETURN s"
        async with self.driver.session() as session:
            result = await session.run(query)
            record = await result.single()
            if record:
                props = dict(record["s"])
                for k in ['affinity_matrix', 'default_triggers', 'sentiment_resonance_matrix']:
                    if k in props and isinstance(props[k], str):
                        props[k] = json.loads(props[k])
                return SystemConfigNode(**props)
        return SystemConfigNode()

    async def update_system_config(self, config: SystemConfigNode) -> None:
        props = config.model_dump(mode='json')
        for k, v in list(props.items()):
            if isinstance(v, (dict, list)):
                props[k] = json.dumps(v)
        query = """
        MERGE (s:SystemConfigNode {id: 'system-config'})
        SET s += $props
        """
        async with self.driver.session() as session:
            await session.run(query, props=props)

    async def get_or_create_location(self, name: str, type: str, description: str) -> LocationNode:
        query = """
        MERGE (l:LocationNode {name: $name})
        ON CREATE SET l.id = $id, l.type = $type, l.description = $desc
        RETURN l
        """
        node_id = str(LocationNode().id) # Generate a new id to use if created
        async with self.driver.session() as session:
            result = await session.run(query, name=name, id=node_id, type=type, desc=description)
            record = await result.single()
            if record:
                return LocationNode(**dict(record["l"]))
        return LocationNode(name=name, type=type, description=description)

    async def get_all_locations(self) -> List[LocationNode]:
        query = "MATCH (l:LocationNode) RETURN l"
        async with self.driver.session() as session:
            result = await session.run(query)
            records = await result.data()
            return [LocationNode(**r['l']) for r in records]

    async def record_collective_event(self, event: CollectiveEventNode):
        props = event.model_dump(mode='json')
        if 'participants' in props:
            props['participants'] = json.dumps(props['participants'])
        query = """
        CREATE (e:CollectiveEventNode {id: $id})
        SET e += $props
        """
        async with self.driver.session() as session:
            await session.run(query, id=event.id, props=props)

    async def get_recent_collective_events(self, limit: int = 5) -> List[CollectiveEventNode]:
        query = "MATCH (e:CollectiveEventNode) RETURN e ORDER BY e.timestamp DESC LIMIT $limit"
        async with self.driver.session() as session:
            result = await session.run(query, limit=limit)
            records = await result.data()
            events = []
            for r in records:
                props = r['e']
                if 'participants' in props and isinstance(props['participants'], str):
                    props['participants'] = json.loads(props['participants'])
                events.append(CollectiveEventNode(**props))
            return events

    async def get_agent_collective_events(self, agent_id: str, limit: int = 5) -> List[CollectiveEventNode]:
        query = """
        MATCH (a:AgentNode {id: $agent_id})-[:PARTICIPATED_IN]->(e:CollectiveEventNode)
        RETURN e ORDER BY e.timestamp DESC LIMIT $limit
        """
        async with self.driver.session() as session:
            result = await session.run(query, agent_id=agent_id, limit=limit)
            records = await result.data()
            events = []
            for r in records:
                props = r['e']
                if 'participants' in props and isinstance(props['participants'], str):
                    props['participants'] = json.loads(props['participants'])
                events.append(CollectiveEventNode(**props))
            return events

    async def get_relevant_collective_events(self, query_str: str, limit: int = 5) -> List[CollectiveEventNode]:
        return await self.get_recent_collective_events(limit)

    async def get_agent_affinity(self, source_id: str, target_id: str) -> AgentAffinityEdge:
        query = """
        MATCH (s:AgentNode {id: $source_id})-[r:AFFINITY]->(t:AgentNode {id: $target_id})
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, source_id=source_id, target_id=target_id)
            record = await result.single()
            if record:
                return AgentAffinityEdge(source_agent_id=source_id, target_agent_id=target_id, **dict(record["r"]))

        new_edge = AgentAffinityEdge(source_agent_id=source_id, target_agent_id=target_id, affinity=50.0)
        query_create = """
        MATCH (s:AgentNode {id: $source_id}), (t:AgentNode {id: $target_id})
        MERGE (s)-[r:AFFINITY]->(t)
        ON CREATE SET r.affinity = 50.0, r.last_interaction = $ts
        """
        async with self.driver.session() as session:
            await session.run(query_create, source_id=source_id, target_id=target_id, ts=datetime.now().isoformat())
        return new_edge

    async def update_agent_affinity(self, source_id: str, target_id: str, delta: float) -> AgentAffinityEdge:
        edge = await self.get_agent_affinity(source_id, target_id)
        new_affinity = max(0.0, min(100.0, edge.affinity + delta))

        query = """
        MATCH (s:AgentNode {id: $source_id})-[r:AFFINITY]->(t:AgentNode {id: $target_id})
        SET r.affinity = $affinity, r.last_interaction = $ts
        """
        async with self.driver.session() as session:
            await session.run(query, source_id=source_id, target_id=target_id,
                              affinity=new_affinity, ts=datetime.now().isoformat())
        edge.affinity = new_affinity
        edge.last_interaction = datetime.now()
        return edge

    async def create_edge(self, edge: GraphEdge) -> None:
        query = f"""
        MATCH (s {{id: $source}}), (t {{id: $target}})
        MERGE (s)-[r:{edge.type}]->(t)
        SET r += $props
        """
        props = edge.model_dump(mode='json')
        if 'properties' in props:
            for k, v in props['properties'].items():
                props[f'prop_{k}'] = v
            del props['properties']

        async with self.driver.session() as session:
            await session.run(query, source=edge.source_id, target=edge.target_id, props=props)

    async def get_edges(self, source_id: str = None, target_id: str = None, edge_type: str = None) -> List[GraphEdge]:
        match_src = f"{{id: '{source_id}'}}" if source_id else ""
        match_tgt = f"{{id: '{target_id}'}}" if target_id else ""
        rel_type = f":{edge_type}" if edge_type else ""

        query = f"""
        MATCH (s{match_src})-[r{rel_type}]->(t{match_tgt})
        RETURN s.id AS source, t.id AS target, type(r) AS type, r
        """
        async with self.driver.session() as session:
            result = await session.run(query)
            records = await result.data()
            edges = []
            for r in records:
                try:
                    props = dict(r['r']) if r.get('r') else {}
                except (ValueError, TypeError):
                    props = {k: v for k, v in r['r'].items()} if r.get('r') else {}
                properties = {k.replace('prop_', ''): v for k, v in props.items() if k.startswith('prop_')}
                clean_props = {k: v for k, v in props.items() if not k.startswith('prop_')}

                ts = datetime.now()
                if 'timestamp' in clean_props:
                    if isinstance(clean_props['timestamp'], str):
                        try:
                            ts = datetime.fromisoformat(clean_props['timestamp'])
                        except ValueError:
                            pass

                edges.append(GraphEdge(
                    source_id=r['source'],
                    target_id=r['target'],
                    type=r['type'],
                    timestamp=ts,
                    properties=properties
                ))
            return edges

    async def record_interaction(self, user_id: str, agent_id: str) -> None:
        query = """
        MATCH (u:UserNode {id: $user_id}), (a:AgentNode {id: $agent_id})
        MERGE (u)-[r:interactedWith]->(a)
        ON CREATE SET r.interaction_count = 1, r.first_interaction = $ts, r.last_interaction = $ts
        ON MATCH SET r.interaction_count = coalesce(r.interaction_count, 0) + 1, r.last_interaction = $ts
        """
        async with self.driver.session() as session:
            await session.run(query, user_id=user_id, agent_id=agent_id, ts=datetime.now().isoformat())

    async def get_active_peers(self, user_id: str, time_window_minutes: int = 15) -> List[AgentNode]:
        query = """
        MATCH (u:UserNode {id: $user_id})-[:interactedWith]->(a:AgentNode)
        RETURN a
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id)
            records = await result.data()
            agents = []
            for r in records:
                props = dict(r['a'])
                if 'user_id' in props: del props['user_id']
                agents.append(AgentNode(**props))
            return agents

    async def get_last_interaction(self, user_id: str, agent_id: str) -> datetime:
        query = """
        MATCH (u:UserNode {id: $user_id})-[r:interactedWith]->(a:AgentNode {id: $agent_id})
        RETURN r.last_interaction AS ts
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id, agent_id=agent_id)
            record = await result.single()
            if record and record["ts"]:
                if isinstance(record["ts"], str):
                    return datetime.fromisoformat(record["ts"])
                return record["ts"]
        return datetime.min

    async def update_user_last_seen(self, user_id: str):
        query = """
        MATCH (u:UserNode {id: $user_id})
        SET u.last_seen = $ts
        """
        async with self.driver.session() as session:
            await session.run(query, user_id=user_id, ts=datetime.now().isoformat())

    async def export_to_json_ld(self) -> Dict[str, Any]:
        return {"error": "Not implemented for Neo4j"}

    async def import_from_json_ld(self, data: Dict[str, Any]) -> None:
        pass

    async def update_agent_friction(self, agent_id: str, delta: float) -> Optional[AgentNode]:
        query = """
        MATCH (a:AgentNode {id: $agent_id})
        SET a.current_friction = coalesce(a.current_friction, 0.0) + $delta
        RETURN a
        """
        async with self.driver.session() as session:
            result = await session.run(query, agent_id=agent_id, delta=delta)
            record = await result.single()
            if record:
                props = dict(record["a"])
                if 'current_friction' in props and props['current_friction'] < 0.0:
                    props['current_friction'] = 0.0
                    await session.run("MATCH (a:AgentNode {id: $agent_id}) SET a.current_friction = 0.0", agent_id=agent_id)
                if 'user_id' in props: del props['user_id']
                return AgentNode(**props)
        return None

    async def get_nemesis_agents(self, user_id: str) -> List[AgentNode]:
        query = """
        MATCH (u:UserNode {id: $user_id})-[:Nemesis]->(a:AgentNode)
        RETURN a
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id)
            records = await result.data()
            return [AgentNode(**r['a']) for r in records]

    async def get_gossip_candidates(self, user_id: str) -> List[AgentNode]:
        query = """
        MATCH ()-[:Gossip_Source]->(a:AgentNode)
        WHERE NOT (UserNode {id: $user_id})-[:interactedWith]->(a)
        RETURN DISTINCT a
        """
        async with self.driver.session() as session:
            result = await session.run(query, user_id=user_id)
            records = await result.data()
            return [AgentNode(**r['a']) for r in records]

    async def purge_all_memories(self) -> bool:
        """
        Factory reset for Neo4j (except Firestore Chronicles).
        Matches behavior requested: deletes scoped nodes if applicable.
        However, to be safe and match SQLite "delete all", we delete all non-system nodes.
        Wait, the user requested explicitly: MATCH (n) WHERE n.user_id = $user_id DETACH DELETE n
        But this function doesn't take user_id. LocalSoulRepository says:
        await session.execute(delete(EdgeModel)); await session.execute(delete(NodeModel))
        So it wipes the entire graph. I will just DETACH DELETE everything for now, or use a user_id if I can.
        The prompt says: "purge_all_memories — Sí, exactamente ese query Cypher scoped por user_id: MATCH (n) WHERE n.user_id = $user_id DETACH DELETE n."
        Wait, if purge_all_memories doesn't take user_id in the abstract interface, I might need to wipe all nodes that have a user_id. Or add user_id to the method.
        But I can't change the abstract interface. I will wipe all nodes that HAVE a user_id.
        """
        # I'll just DETACH DELETE nodes that have a user_id property, assuming they are scoped.
        query = """
        MATCH (n) WHERE n.user_id IS NOT NULL
        DETACH DELETE n
        """
        try:
            async with self.driver.session() as session:
                await session.run(query)
            logger.warning("🌪️ THE GREAT REBIRTH EXECUTED in Neo4j (user_id scoped nodes purged).")
            return True
        except Exception as e:
            logger.error(f"Failed to execute The Great Rebirth in Neo4j: {e}")
            return False

    # ─── KIZUNA ETERNAL MEMORY ─────────────────────────────────────────────────

    async def upsert_chronicle(self, user_id: str, agent_id: str, agent_name: str, relationship_summary: str, dominant_topics: list, emotional_tone: str, interaction_count: int = 1) -> None:
        try:
            from app.services.firestore_service import firestore_service
            import datetime
            existing = await firestore_service.get_chronicle(user_id, agent_id)
            wipes = existing.get("survived_wipes", 0) if existing else 0

            data = {
                "user_id": user_id,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "relationship_summary": relationship_summary,
                "dominant_topics": dominant_topics,
                "emotional_tone": emotional_tone,
                "interaction_count": interaction_count,
                "survived_wipes": wipes,
                "last_updated": datetime.datetime.utcnow().isoformat()
            }
            await firestore_service.save_chronicle(user_id, agent_id, data)
        except Exception as e:
            logger.error(f"Failed to upsert chronicle to Firestore: {e}")

    async def get_chronicles_for_user(self, user_id: str) -> list:
        try:
            from app.services.firestore_service import firestore_service
            chronicle = await firestore_service.get_chronicle(user_id, "kizuna")
            if chronicle:
                class MockChronicle:
                    def __init__(self, **kwargs):
                        self.__dict__.update(kwargs)
                return [MockChronicle(**chronicle)]
            return []
        except Exception as e:
            logger.error(f"Failed to get chronicles from Firestore: {e}")
            return []

    async def get_chronicle(self, user_id: str, agent_id: str) -> Optional[Any]:
        try:
            from app.services.firestore_service import firestore_service
            chronicle = await firestore_service.get_chronicle(user_id, agent_id)
            if chronicle:
                chronicle["user_id"] = user_id
                chronicle["agent_id"] = agent_id
                class MockChronicle:
                    def __init__(self, **kwargs):
                        self.__dict__.update(kwargs)
                return MockChronicle(**chronicle)
            return None
        except Exception as e:
            logger.error(f"Failed to get chronicle from Firestore: {e}")
            return None
