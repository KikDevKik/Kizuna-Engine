try:
    from google.cloud import spanner
    from google.cloud.spanner_v1.pool import FixedSizePool
except ImportError:
    spanner = None
    FixedSizePool = None

from ..repositories.base import SoulRepository
from ..models.graph import (
    UserNode, AgentNode, ResonanceEdge, MemoryEpisodeNode, FactNode,
    DreamNode, ShadowEdge, ArchetypeNode, GlobalDreamNode, EmbodiesEdge,
    SystemConfigNode, CollectiveEventNode
)
import logging
from core.config import settings
from datetime import datetime
import json
from ..services.embedding import embedding_service
from typing import Optional, List

logger = logging.getLogger(__name__)

class SpannerSoulRepository(SoulRepository):
    """
    Phase 3.2: Google Cloud Spanner (Graph).
    Implements the SoulRepository using Spanner Graph queries (GQL).
    Includes Evolution Phase 1: Ontology & Batch Optimizations.
    """

    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.instance_id = settings.SPANNER_INSTANCE_ID
        self.database_id = settings.SPANNER_DATABASE_ID
        self.instance = None
        self.database = None
        self.client = None

    async def initialize(self) -> None:
        """Connect to Cloud Spanner."""
        if spanner is None:
            logger.error("❌ google-cloud-spanner is not installed. Cannot initialize Spanner Repository.")
            raise ImportError("google-cloud-spanner library missing")

        logger.info(f"Connecting to Spanner Instance: {self.instance_id}, Database: {self.database_id}")
        try:
            self.client = spanner.Client(project=self.project_id)
            self.instance = self.client.instance(self.instance_id)
            # Use FixedSizePool for production performance
            self.database = self.instance.database(self.database_id, pool=FixedSizePool())
            logger.info("✅ Spanner Database Connected.")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Spanner: {e}")
            raise

    async def get_or_create_user(self, user_id: str, name: str = "Anonymous") -> UserNode:
        """Get User Node or Create via GQL."""
        def get_user_tx(transaction):
            query = "GRAPH FinetuningGraph MATCH (u:User {id: @id}) RETURN u.id, u.name, u.created_at"
            results = transaction.execute_sql(query, params={"id": user_id}, param_types={"id": spanner.param_types.STRING})
            row = None
            for r in results:
                row = r
                break
            return row

        def create_user_tx(transaction):
            query = """
                GRAPH FinetuningGraph
                CREATE (:User {id: @id, name: @name, created_at: @created_at})
            """
            transaction.execute_update(query, params={
                "id": user_id,
                "name": name,
                "created_at": datetime.now().isoformat()
            }, param_types={
                "id": spanner.param_types.STRING,
                "name": spanner.param_types.STRING,
                "created_at": spanner.param_types.STRING
            })

        try:
            with self.database.snapshot() as snapshot:
                row = get_user_tx(snapshot)
                if row:
                    return UserNode(id=row[0], name=row[1], created_at=row[2])

            self.database.run_in_transaction(create_user_tx)
            return UserNode(id=user_id, name=name)
        except Exception as e:
            logger.error(f"Spanner Error in get_or_create_user: {e}")
            raise

    async def get_agent(self, agent_id: str) -> AgentNode | None:
        def query_agent(snapshot):
            query = "GRAPH FinetuningGraph MATCH (a:Agent {id: @id}) RETURN a.id, a.name, a.base_instruction, a.traits"
            results = snapshot.execute_sql(query, params={"id": agent_id}, param_types={"id": spanner.param_types.STRING})
            for row in results:
                traits = json.loads(row[3]) if row[3] else {}
                return AgentNode(id=row[0], name=row[1], base_instruction=row[2], traits=traits)
            return None

        with self.database.snapshot() as snapshot:
            return query_agent(snapshot)

    async def get_resonance(self, user_id: str, agent_id: str) -> ResonanceEdge:
        def query_resonance(snapshot):
            query = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent {id: @aid})
                RETURN r.affinity_level, r.last_interaction, r.shared_memories
            """
            results = snapshot.execute_sql(query, params={"uid": user_id, "aid": agent_id},
                                           param_types={"uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING})
            for row in results:
                return ResonanceEdge(source_id=user_id, target_id=agent_id,
                                     affinity_level=float(row[0]),
                                     last_interaction=row[1],
                                     shared_memories=row[2] if row[2] else [])
            return None

        with self.database.snapshot() as snapshot:
            res = query_resonance(snapshot)
            if res:
                return res
            return ResonanceEdge(source_id=user_id, target_id=agent_id, affinity_level=50.0)

    async def update_resonance(self, user_id: str, agent_id: str, delta: float) -> ResonanceEdge:
        def merge_tx(transaction):
            initial_level = 50.0 + delta
            initial_level = max(0.0, min(100.0, initial_level))
            now_iso = datetime.now().isoformat()

            merge_query = """
                GRAPH FinetuningGraph
                MERGE (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent {id: @aid})
                ON CREATE SET r.affinity_level = @initial_level, r.last_interaction = @now
                ON MATCH SET r.affinity_level = CASE
                    WHEN r.affinity_level + @delta > 100.0 THEN 100.0
                    WHEN r.affinity_level + @delta < 0.0 THEN 0.0
                    ELSE r.affinity_level + @delta
                END, r.last_interaction = @now
            """
            transaction.execute_update(merge_query, params={
                "uid": user_id, "aid": agent_id,
                "delta": delta, "initial_level": initial_level,
                "now": now_iso
            }, param_types={
                "uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING,
                "delta": spanner.param_types.FLOAT64, "initial_level": spanner.param_types.FLOAT64,
                "now": spanner.param_types.STRING
            })

        def fallback_tx(transaction):
            now_iso = datetime.now().isoformat()
            check_query = "GRAPH FinetuningGraph MATCH (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent {id: @aid}) RETURN r.affinity_level"
            results = list(transaction.execute_sql(check_query, params={"uid": user_id, "aid": agent_id},
                                           param_types={"uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING}))

            if not results:
                initial_level = 50.0 + delta
                initial_level = max(0.0, min(100.0, initial_level))
                create_query = """
                    GRAPH FinetuningGraph
                    MATCH (u:User {id: @uid}), (a:Agent {id: @aid})
                    CREATE (u)-[:HAS_RESONANCE {affinity_level: @initial_level, last_interaction: @now}]->(a)
                """
                transaction.execute_update(create_query, params={
                    "uid": user_id, "aid": agent_id, "initial_level": initial_level, "now": now_iso
                }, param_types={
                    "uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING,
                    "initial_level": spanner.param_types.FLOAT64, "now": spanner.param_types.STRING
                })
            else:
                current_level = float(results[0][0])
                new_level = current_level + delta
                new_level = max(0.0, min(100.0, new_level))
                update_query = """
                    GRAPH FinetuningGraph
                    MATCH (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent {id: @aid})
                    SET r.affinity_level = @new_level, r.last_interaction = @now
                """
                transaction.execute_update(update_query, params={
                    "uid": user_id, "aid": agent_id, "new_level": new_level, "now": now_iso
                }, param_types={
                    "uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING,
                    "new_level": spanner.param_types.FLOAT64, "now": spanner.param_types.STRING
                })

        try:
            self.database.run_in_transaction(merge_tx)
        except Exception as e:
            logger.error(f"MERGE failed, attempting Fallback. Error: {e}")
            try:
                self.database.run_in_transaction(fallback_tx)
            except Exception as e_fallback:
                logger.error(f"Spanner Update Resonance Failed: {e_fallback}")
                raise
        return await self.get_resonance(user_id, agent_id)

    async def save_episode(self, user_id: str, agent_id: str, summary: str, valence: float) -> MemoryEpisodeNode:
        def save_tx(transaction):
             ep_id = f"ep-{datetime.now().timestamp()}"
             create_ep = """
                GRAPH FinetuningGraph
                CREATE (:Episode {id: @id, summary: @summary, valence: @valence, timestamp: @now})
             """
             transaction.execute_update(create_ep, params={
                 "id": ep_id, "summary": summary, "valence": valence, "now": datetime.now().isoformat()
             }, param_types={
                 "id": spanner.param_types.STRING, "summary": spanner.param_types.STRING,
                 "valence": spanner.param_types.FLOAT64, "now": spanner.param_types.STRING
             })

             link_ep = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: @uid}), (e:Episode {id: @eid})
                CREATE (u)-[:EXPERIENCED]->(e)
             """
             transaction.execute_update(link_ep, params={"uid": user_id, "eid": ep_id},
                                        param_types={"uid": spanner.param_types.STRING, "eid": spanner.param_types.STRING})
             return ep_id

        try:
            ep_id = self.database.run_in_transaction(save_tx)
            return MemoryEpisodeNode(id=str(ep_id), summary=summary, emotional_valence=valence)
        except Exception as e:
            logger.error(f"Spanner Save Episode Failed: {e}")
            raise

    # --- Evolution Phase 1: Ontology & Archetypes ---

    async def create_archetype(self, name: str, description: str, triggers: dict) -> ArchetypeNode:
        """Creates a new Archetype Node."""
        archetype_id = f"arc-{datetime.now().timestamp()}"

        def create_tx(transaction):
            query = """
                GRAPH FinetuningGraph
                CREATE (:Archetype {id: @id, name: @name, description: @description, triggers: @triggers})
            """
            transaction.execute_update(query, params={
                "id": archetype_id, "name": name, "description": description,
                "triggers": json.dumps(triggers)
            }, param_types={
                "id": spanner.param_types.STRING, "name": spanner.param_types.STRING,
                "description": spanner.param_types.STRING, "triggers": spanner.param_types.STRING
            })

        try:
            self.database.run_in_transaction(create_tx)
            return ArchetypeNode(id=archetype_id, name=name, description=description, triggers=triggers)
        except Exception as e:
            logger.error(f"Failed to create Archetype: {e}")
            raise

    async def get_archetype(self, name: str) -> Optional[ArchetypeNode]:
        """Fetch Archetype by Name."""
        def query_tx(snapshot):
            query = "GRAPH FinetuningGraph MATCH (a:Archetype {name: @name}) RETURN a.id, a.name, a.description, a.triggers"
            results = snapshot.execute_sql(query, params={"name": name}, param_types={"name": spanner.param_types.STRING})
            for row in results:
                triggers = json.loads(row[3]) if row[3] else {}
                return ArchetypeNode(id=row[0], name=row[1], description=row[2], triggers=triggers)
            return None

        with self.database.snapshot() as snapshot:
            return query_tx(snapshot)

    async def link_agent_archetype(self, agent_id: str, archetype_id: str, strength: float = 1.0) -> None:
        """Creates EMBODIES edge."""
        def link_tx(transaction):
            query = """
                GRAPH FinetuningGraph
                MATCH (a:Agent {id: @aid}), (arc:Archetype {id: @arcid})
                CREATE (a)-[:EMBODIES {strength: @strength}]->(arc)
            """
            transaction.execute_update(query, params={
                "aid": agent_id, "arcid": archetype_id, "strength": strength
            }, param_types={
                "aid": spanner.param_types.STRING, "arcid": spanner.param_types.STRING,
                "strength": spanner.param_types.FLOAT64
            })

        try:
            self.database.run_in_transaction(link_tx)
        except Exception as e:
            logger.error(f"Failed to link Agent to Archetype: {e}")
            raise

    async def get_agent_archetype(self, agent_id: str) -> Optional[ArchetypeNode]:
        """Get the Archetype an agent embodies."""
        def query_tx(snapshot):
            query = """
                GRAPH FinetuningGraph
                MATCH (a:Agent {id: @aid})-[:EMBODIES]->(arc:Archetype)
                RETURN arc.id, arc.name, arc.description, arc.triggers
            """
            results = snapshot.execute_sql(query, params={"aid": agent_id}, param_types={"aid": spanner.param_types.STRING})
            for row in results:
                triggers = json.loads(row[3]) if row[3] else {}
                return ArchetypeNode(id=row[0], name=row[1], description=row[2], triggers=triggers)
            return None

        with self.database.snapshot() as snapshot:
            return query_tx(snapshot)

    # --- Evolution Phase 1: Global Dream ---

    async def get_global_dream(self) -> GlobalDreamNode:
        """Fetch Singleton Global Dream."""
        def query_tx(snapshot):
            query = "GRAPH FinetuningGraph MATCH (g:GlobalDream {id: 'global-dream'}) RETURN g.themes, g.intensity, g.last_updated"
            results = snapshot.execute_sql(query)
            for row in results:
                # themes is Array<String>
                return GlobalDreamNode(themes=row[0], intensity=float(row[1]), last_updated=row[2])
            return GlobalDreamNode() # Default

        with self.database.snapshot() as snapshot:
            return query_tx(snapshot)

    async def update_global_dream(self, themes: List[str], intensity: float) -> None:
        """Update Singleton Global Dream."""
        def update_tx(transaction):
            now = datetime.now().isoformat()
            query = """
                GRAPH FinetuningGraph
                MERGE (g:GlobalDream {id: 'global-dream'})
                SET g.themes = @themes, g.intensity = @intensity, g.last_updated = @now
            """
            transaction.execute_update(query, params={
                "themes": themes, "intensity": intensity, "now": now
            }, param_types={
                "themes": spanner.param_types.Array(spanner.param_types.STRING),
                "intensity": spanner.param_types.FLOAT64,
                "now": spanner.param_types.STRING
            })

        try:
            self.database.run_in_transaction(update_tx)
        except Exception as e:
            logger.error(f"Failed to update Global Dream: {e}")

    # --- Evolution Phase 1: Batch Optimization ---

    async def consolidate_memories(self, user_id: str, dream_generator=None) -> None:
        """
        Refactored to use Batch Updates (reduce round trips).
        """
        logger.info(f"Spanner Consolidation (Batch Optimized) triggered for {user_id}.")

        # 1. Fetch Active Episodes
        active_episodes = []
        try:
            with self.database.snapshot() as snapshot:
                query = """
                    GRAPH FinetuningGraph
                    MATCH (u:User {id: @uid})-[:EXPERIENCED]->(e:Episode)
                    WHERE e.valence != 999.0
                    RETURN e.id, e.summary, e.valence
                """
                results = snapshot.execute_sql(query, params={"uid": user_id},
                                               param_types={"uid": spanner.param_types.STRING})
                for row in results:
                    active_episodes.append(MemoryEpisodeNode(id=row[0], summary=row[1], emotional_valence=row[2]))
        except Exception as e:
            logger.error(f"Failed to fetch active episodes: {e}")
            return

        if not active_episodes:
            return

        # 2. Generate Dream
        dream_node = None
        if dream_generator:
            try:
                dream_node = await dream_generator(active_episodes)
            except Exception as e:
                logger.error(f"Dream generation failed: {e}")

        if not dream_node:
             dream_node = DreamNode(theme="Void", intensity=0.0, surrealism_level=0.0)

        # 3. Calculate EMA Affinity Updates
        agent_updates = {}
        ALPHA = 0.15

        try:
            with self.database.snapshot() as snapshot:
                query = """
                    GRAPH FinetuningGraph
                    MATCH (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent)
                    RETURN a.id, r.affinity_level, r.shared_memories
                """
                results = snapshot.execute_sql(query, params={"uid": user_id},
                                               param_types={"uid": spanner.param_types.STRING})

                for row in results:
                    agent_id = row[0]
                    current_affinity = float(row[1])
                    shared_memories = row[2] if row[2] else []

                    relevant_eps = [ep for ep in active_episodes if ep.id in shared_memories]

                    if relevant_eps:
                        avg_valence = sum(ep.emotional_valence for ep in relevant_eps) / len(relevant_eps)
                        target = 50.0 + (avg_valence * 50.0)
                        new_affinity = (target * ALPHA) + (current_affinity * (1.0 - ALPHA))
                        new_affinity = max(0.0, min(100.0, new_affinity))
                        agent_updates[agent_id] = new_affinity

        except Exception as e:
            logger.error(f"Failed to calculate EMA updates: {e}")

        # 4. Write Transaction (Batched DML)
        def consolidation_tx(transaction):
            dml_statements = []

            # A. Create Dream Node
            create_dream = """
                GRAPH FinetuningGraph
                CREATE (:Dream {id: %s, theme: %s, intensity: %f, surrealism_level: %f, timestamp: %s})
            """ % (json.dumps(dream_node.id), json.dumps(dream_node.theme), float(dream_node.intensity),
                   float(dream_node.surrealism_level), json.dumps(datetime.now().isoformat()))
            dml_statements.append(create_dream)

            # B. Link User -> Dream
            link_dream = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: %s}), (d:Dream {id: %s})
                CREATE (u)-[:SHADOW {weight: 1.0}]->(d)
            """ % (json.dumps(user_id), json.dumps(dream_node.id))
            dml_statements.append(link_dream)

            # C. Update Affinities
            now_iso = datetime.now().isoformat()
            for aid, new_aff in agent_updates.items():
                update_aff = """
                    GRAPH FinetuningGraph
                    MATCH (u:User {id: %s})-[r:HAS_RESONANCE]->(a:Agent {id: %s})
                    SET r.affinity_level = %f, r.last_interaction = %s
                """ % (json.dumps(user_id), json.dumps(aid), float(new_aff), json.dumps(now_iso))
                dml_statements.append(update_aff)

            # D. Archive Episodes
            for ep in active_episodes:
                archive_ep = """
                    GRAPH FinetuningGraph
                    MATCH (e:Episode {id: %s})
                    SET e.valence = 999.0
                """ % (json.dumps(ep.id))
                dml_statements.append(archive_ep)

            # Execute Batch
            if dml_statements:
                transaction.batch_update(dml_statements)

        try:
            self.database.run_in_transaction(consolidation_tx)
            logger.info("✅ Spanner Consolidation Complete (Batched).")
        except Exception as e:
            logger.error(f"Spanner Consolidation Transaction Failed: {e}")
            raise

    async def get_relevant_facts(self, user_id: str, query: str, limit: int = 5) -> list[FactNode]:
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(query)
        if not query_embedding:
            logger.warning("Failed to generate embedding for query.")
            return []

        def query_tx(snapshot):
            gql = """
                GRAPH FinetuningGraph
                MATCH (f:Fact)
                WHERE COSINE_DISTANCE(f.embedding, @embedding) < 0.5
                RETURN f.id, f.content, f.category, f.confidence
                ORDER BY COSINE_DISTANCE(f.embedding, @embedding) ASC
                LIMIT @limit
            """
            results = snapshot.execute_sql(gql, params={
                "embedding": query_embedding,
                "limit": limit
            }, param_types={
                "embedding": spanner.param_types.Array(spanner.param_types.FLOAT64),
                "limit": spanner.param_types.INT64
            })
            facts = []
            for row in results:
                facts.append(FactNode(id=row[0], content=row[1], category=row[2], confidence=row[3]))
            return facts

        try:
            with self.database.snapshot() as snapshot:
                 return query_tx(snapshot)
        except Exception as e:
            logger.error(f"Spanner Vector Search Failed: {e}")
            return []

    async def save_fact(self, user_id: str, content: str, category: str) -> FactNode:
        """
        GQL implementation for saving a fact and linking it to a user.
        """
        embedding = await embedding_service.embed_text(content)

        def save_tx(transaction):
            fact_id = f"fact-{datetime.now().timestamp()}"
            create_fact = """
                GRAPH FinetuningGraph
                CREATE (:Fact {id: @id, content: @content, category: @category, confidence: @confidence, embedding: @embedding})
            """
            transaction.execute_update(create_fact, params={
                "id": fact_id,
                "content": content,
                "category": category,
                "confidence": 1.0,
                "embedding": embedding if embedding else None
            }, param_types={
                "id": spanner.param_types.STRING,
                "content": spanner.param_types.STRING,
                "category": spanner.param_types.STRING,
                "confidence": spanner.param_types.FLOAT64,
                "embedding": spanner.param_types.Array(spanner.param_types.FLOAT64)
            })

            link_fact = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: @uid}), (f:Fact {id: @fid})
                CREATE (u)-[:KNOWS]->(f)
            """
            transaction.execute_update(link_fact, params={
                "uid": user_id,
                "fid": fact_id
            }, param_types={
                "uid": spanner.param_types.STRING,
                "fid": spanner.param_types.STRING
            })
            return fact_id

        try:
            fact_id = self.database.run_in_transaction(save_tx)
            return FactNode(id=str(fact_id), content=content, category=category, embedding=embedding)
        except Exception as e:
            logger.error(f"Spanner Save Fact Failed: {e}")
            raise

    async def get_last_dream(self, user_id: str) -> Optional[DreamNode]:
        def query_tx(snapshot):
            query = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: @uid})-[:SHADOW]->(d:Dream)
                RETURN d.id, d.theme, d.intensity, d.surrealism_level
                ORDER BY d.timestamp DESC
                LIMIT 1
            """
            results = snapshot.execute_sql(query, params={"uid": user_id},
                                           param_types={"uid": spanner.param_types.STRING})
            for row in results:
                return DreamNode(id=row[0], theme=row[1], intensity=float(row[2]), surrealism_level=float(row[3]))
            return None

        try:
            with self.database.snapshot() as snapshot:
                return query_tx(snapshot)
        except Exception as e:
            logger.error(f"Failed to fetch last dream: {e}")
            return None

    async def get_recent_episodes(self, user_id: str, limit: int = 10) -> list[MemoryEpisodeNode]:
        def query_tx(snapshot):
            query = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: @uid})-[:EXPERIENCED]->(e:Episode)
                RETURN e.id, e.summary, e.valence
                ORDER BY e.timestamp DESC
                LIMIT @limit
            """
            results = snapshot.execute_sql(query, params={"uid": user_id, "limit": limit},
                                           param_types={"uid": spanner.param_types.STRING, "limit": spanner.param_types.INT64})
            episodes = []
            for row in results:
                episodes.append(MemoryEpisodeNode(id=row[0], summary=row[1], emotional_valence=float(row[2])))
            return episodes[::-1]

        try:
            with self.database.snapshot() as snapshot:
                return query_tx(snapshot)
        except Exception as e:
            logger.error(f"Failed to fetch recent episodes: {e}")
            return []

    async def get_relevant_episodes(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEpisodeNode]:
        """
        Placeholder for Semantic Search in Spanner (Phase 3.2).
        Requires `embedding_service` and vector index on `Episode` nodes.
        """
        # raise NotImplementedError("Spanner vector search for episodes pending")
        # Returning empty list to prevent runtime crashes during transition
        logger.warning(f"Spanner get_relevant_episodes not implemented yet for query: {query}")
        return []

    # --- Evolution Phase 2: System Config (Spanner) ---

    async def get_system_config(self) -> SystemConfigNode:
        """Fetch the System Configuration Node."""
        def query_tx(snapshot):
            query = "GRAPH FinetuningGraph MATCH (s:SystemConfig {id: 'system-config'}) RETURN s.core_directive, s.affinity_matrix, s.default_triggers, s.sentiment_resonance_matrix, s.reflection_base_chance, s.reflection_neuroticism_multiplier"
            results = snapshot.execute_sql(query)
            for row in results:
                affinity_matrix = json.loads(row[1]) if row[1] else []
                default_triggers = json.loads(row[2]) if row[2] else {}
                sentiment_matrix = json.loads(row[3]) if row[3] else {}

                return SystemConfigNode(
                    core_directive=row[0],
                    affinity_matrix=affinity_matrix,
                    default_triggers=default_triggers,
                    sentiment_resonance_matrix=sentiment_matrix,
                    reflection_base_chance=float(row[4]) if row[4] is not None else 0.2,
                    reflection_neuroticism_multiplier=float(row[5]) if row[5] is not None else 0.6
                )
            return SystemConfigNode() # Default

        try:
            with self.database.snapshot() as snapshot:
                return query_tx(snapshot)
        except Exception as e:
            logger.error(f"Failed to fetch System Config from Spanner: {e}")
            return SystemConfigNode() # Fallback to default

    async def update_system_config(self, config: SystemConfigNode) -> None:
        """Update the System Configuration Node."""
        def update_tx(transaction):
            query = """
                GRAPH FinetuningGraph
                MERGE (s:SystemConfig {id: 'system-config'})
                SET s.core_directive = @core_directive,
                    s.affinity_matrix = @affinity_matrix,
                    s.default_triggers = @default_triggers,
                    s.sentiment_resonance_matrix = @sentiment_resonance_matrix,
                    s.reflection_base_chance = @reflection_base_chance,
                    s.reflection_neuroticism_multiplier = @reflection_neuroticism_multiplier
            """
            transaction.execute_update(query, params={
                "core_directive": config.core_directive,
                "affinity_matrix": json.dumps(config.affinity_matrix),
                "default_triggers": json.dumps(config.default_triggers),
                "sentiment_resonance_matrix": json.dumps(config.sentiment_resonance_matrix),
                "reflection_base_chance": config.reflection_base_chance,
                "reflection_neuroticism_multiplier": config.reflection_neuroticism_multiplier
            }, param_types={
                "core_directive": spanner.param_types.STRING,
                "affinity_matrix": spanner.param_types.STRING,
                "default_triggers": spanner.param_types.STRING,
                "sentiment_resonance_matrix": spanner.param_types.STRING,
                "reflection_base_chance": spanner.param_types.FLOAT64,
                "reflection_neuroticism_multiplier": spanner.param_types.FLOAT64
            })

        try:
            self.database.run_in_transaction(update_tx)
        except Exception as e:
            logger.error(f"Failed to update System Config in Spanner: {e}")
            raise

    # --- Evolution Phase 3: Collective Events (Stubs for now) ---

    async def get_recent_collective_events(self, limit: int = 5) -> List[CollectiveEventNode]:
        return []

    async def get_agent_collective_events(self, agent_id: str, limit: int = 5) -> List[CollectiveEventNode]:
        return []

    async def get_relevant_collective_events(self, query: str, limit: int = 5) -> List[CollectiveEventNode]:
        return []
