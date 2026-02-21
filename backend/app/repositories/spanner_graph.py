try:
    from google.cloud import spanner
    from google.cloud.spanner_v1.pool import FixedSizePool
except ImportError:
    spanner = None
    FixedSizePool = None

from ..repositories.base import SoulRepository
from ..models.graph import UserNode, AgentNode, ResonanceEdge, MemoryEpisodeNode, FactNode, DreamNode, ShadowEdge
import logging
from core.config import settings
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class SpannerSoulRepository(SoulRepository):
    """
    Phase 3.2: Google Cloud Spanner (Graph).
    Implements the SoulRepository using Spanner Graph queries (GQL).
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
                    return UserNode(id=row[0], name=row[1], created_at=row[2]) # Assuming row order matches query

            # If not found, create in read-write transaction
            self.database.run_in_transaction(create_user_tx)
            return UserNode(id=user_id, name=name)
        except Exception as e:
            logger.error(f"Spanner Error in get_or_create_user: {e}")
            # Fallback or re-raise
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
                # row[2] (shared_memories) might be ARRAY<STRING>
                return ResonanceEdge(source_id=user_id, target_id=agent_id,
                                     affinity_level=float(row[0]), # Ensure float
                                     last_interaction=row[1],
                                     shared_memories=row[2] if row[2] else [])
            return None

        with self.database.snapshot() as snapshot:
            res = query_resonance(snapshot)
            if res:
                return res

            # Default empty resonance (not persisted until update)
            return ResonanceEdge(source_id=user_id, target_id=agent_id, affinity_level=50.0)

    async def update_resonance(self, user_id: str, agent_id: str, delta: float) -> ResonanceEdge:
        def update_tx(transaction):
            # Upsert edge logic in GQL? Or MERGE logic.
            # Assuming basic CREATE if not exists, SET if exists.
            query = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent {id: @aid})
                SET r.affinity_level = r.affinity_level + @delta, r.last_interaction = @now
            """
            # This fails if edge doesn't exist. We need MERGE (or equivalent in Spanner GQL).
            # If Spanner GQL doesn't support MERGE yet, we check existence first (in transaction) and create.

            check_query = "GRAPH FinetuningGraph MATCH (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent {id: @aid}) RETURN r"
            exists = list(transaction.execute_sql(check_query, params={"uid": user_id, "aid": agent_id},
                                           param_types={"uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING}))

            if not exists:
                # Start at 50.0 (neutral) + delta
                initial_level = 50.0 + delta
                initial_level = max(0.0, min(100.0, initial_level))

                create_query = """
                    GRAPH FinetuningGraph
                    MATCH (u:User {id: @uid}), (a:Agent {id: @aid})
                    CREATE (u)-[:HAS_RESONANCE {affinity_level: @initial_level, last_interaction: @now}]->(a)
                """
                transaction.execute_update(create_query, params={
                    "uid": user_id, "aid": agent_id, "initial_level": initial_level, "now": datetime.now().isoformat()
                }, param_types={
                    "uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING,
                    "initial_level": spanner.param_types.FLOAT64, "now": spanner.param_types.STRING
                })
            else:
                transaction.execute_update(query, params={
                    "uid": user_id, "aid": agent_id, "delta": delta, "now": datetime.now().isoformat()
                }, param_types={
                    "uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING,
                    "delta": spanner.param_types.FLOAT64, "now": spanner.param_types.STRING
                })

        try:
            self.database.run_in_transaction(update_tx)
            # Return updated object (re-fetch)
            return await self.get_resonance(user_id, agent_id)
        except Exception as e:
            logger.error(f"Spanner Update Resonance Failed: {e}")
            raise

    async def save_episode(self, user_id: str, agent_id: str, summary: str, valence: float) -> MemoryEpisodeNode:
        def save_tx(transaction):
             # 1. Create Episode Node
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

             # 2. Link User -> Episode (EXPERIENCED)
             link_ep = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: @uid}), (e:Episode {id: @eid})
                CREATE (u)-[:EXPERIENCED]->(e)
             """
             transaction.execute_update(link_ep, params={"uid": user_id, "eid": ep_id},
                                        param_types={"uid": spanner.param_types.STRING, "eid": spanner.param_types.STRING})

             return ep_id

        try:
            # We can't return complex objects easily from run_in_transaction unless we refetch
            ep_id = self.database.run_in_transaction(save_tx)
            return MemoryEpisodeNode(id=str(ep_id), summary=summary, emotional_valence=valence)
        except Exception as e:
            logger.error(f"Spanner Save Episode Failed: {e}")
            raise

    async def get_relevant_facts(self, user_id: str, query: str, limit: int = 5) -> list[FactNode]:
        # Implementation depends on Vector Search in Spanner (using cosine distance)
        # Assuming table Facts has 'embedding' column
        # SELECT * FROM Facts WHERE COSINE_DISTANCE(embedding, @query_embedding) < 0.5 ...
        return [] # Stub for now as we don't have embedding service set up yet

    async def save_fact(self, user_id: str, content: str, category: str) -> FactNode:
        """
        GQL implementation for saving a fact and linking it to a user.
        """
        def save_tx(transaction):
            # 1. Create Fact Node
            fact_id = f"fact-{datetime.now().timestamp()}"
            create_fact = """
                GRAPH FinetuningGraph
                CREATE (:Fact {id: @id, content: @content, category: @category, confidence: @confidence})
            """
            transaction.execute_update(create_fact, params={
                "id": fact_id,
                "content": content,
                "category": category,
                "confidence": 1.0
            }, param_types={
                "id": spanner.param_types.STRING,
                "content": spanner.param_types.STRING,
                "category": spanner.param_types.STRING,
                "confidence": spanner.param_types.FLOAT64
            })

            # 2. Link User -> Fact (KNOWS)
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
            return FactNode(id=str(fact_id), content=content, category=category)
        except Exception as e:
            logger.error(f"Spanner Save Fact Failed: {e}")
            raise

    async def consolidate_memories(self, user_id: str, dream_generator=None) -> None:
        """
        Phase 3.2 Spanner Implementation: Lucid Dreaming Protocol.
        1. Fetch all active episodes (valence != 999.0).
        2. Generate DreamNode via Gemini (dream_generator).
        3. Calculate EMA affinity updates for agents involved in those episodes.
        4. Run Transaction: Create Dream, Link Shadow, Update Affinities, Archive Episodes.
        """
        logger.info(f"Spanner Consolidation triggered for {user_id}.")

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
            logger.info("No active episodes to consolidate.")
            return

        logger.info(f"Consolidating {len(active_episodes)} episodes...")

        # 2. Generate Dream (External API Call - outside transaction)
        dream_node = None
        if dream_generator:
            try:
                dream_node = await dream_generator(active_episodes)
            except Exception as e:
                logger.error(f"Dream generation failed: {e}")

        # Fallback Dream if generator fails or not provided (though local logic implies generator always there)
        if not dream_node:
             dream_node = DreamNode(theme="Void", intensity=0.0, surrealism_level=0.0)

        # 3. Calculate EMA Affinity Updates
        # We need to know which agents share these episodes.
        # Fetch User's Resonances
        agent_updates = {} # {agent_id: new_affinity}
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
                    shared_memories = row[2] if row[2] else [] # List[str]

                    # Filter episodes relevant to this agent
                    relevant_eps = [ep for ep in active_episodes if ep.id in shared_memories]

                    if relevant_eps:
                        # Calculate Average Valence (-1.0 to 1.0)
                        avg_valence = sum(ep.emotional_valence for ep in relevant_eps) / len(relevant_eps)

                        # Map to Target Signal (0-100)
                        target = 50.0 + (avg_valence * 50.0)

                        # EMA Update
                        new_affinity = (target * ALPHA) + (current_affinity * (1.0 - ALPHA))
                        new_affinity = max(0.0, min(100.0, new_affinity))

                        agent_updates[agent_id] = new_affinity
                        logger.info(f"Calculated Affinity Update for {agent_id}: {current_affinity:.2f} -> {new_affinity:.2f}")

        except Exception as e:
            logger.error(f"Failed to calculate EMA updates: {e}")
            # Continue without updating affinity is risky, but better than crashing?
            # We'll log and proceed with just dream consolidation.

        # 4. Write Transaction
        def consolidation_tx(transaction):
            # A. Create Dream Node
            create_dream = """
                GRAPH FinetuningGraph
                CREATE (:Dream {id: @did, theme: @theme, intensity: @intensity, surrealism_level: @surrealism, timestamp: @now})
            """
            transaction.execute_update(create_dream, params={
                "did": dream_node.id,
                "theme": dream_node.theme,
                "intensity": float(dream_node.intensity),
                "surrealism": float(dream_node.surrealism_level),
                "now": datetime.now().isoformat()
            }, param_types={
                "did": spanner.param_types.STRING, "theme": spanner.param_types.STRING,
                "intensity": spanner.param_types.FLOAT64, "surrealism": spanner.param_types.FLOAT64,
                "now": spanner.param_types.STRING
            })

            # B. Link User -> Dream (SHADOW)
            link_dream = """
                GRAPH FinetuningGraph
                MATCH (u:User {id: @uid}), (d:Dream {id: @did})
                CREATE (u)-[:SHADOW {weight: 1.0}]->(d)
            """
            transaction.execute_update(link_dream, params={"uid": user_id, "did": dream_node.id},
                                       param_types={"uid": spanner.param_types.STRING, "did": spanner.param_types.STRING})

            # C. Update Affinities
            for aid, new_aff in agent_updates.items():
                update_aff = """
                    GRAPH FinetuningGraph
                    MATCH (u:User {id: @uid})-[r:HAS_RESONANCE]->(a:Agent {id: @aid})
                    SET r.affinity_level = @new_aff, r.last_interaction = @now
                """
                transaction.execute_update(update_aff, params={
                    "uid": user_id, "aid": aid, "new_aff": float(new_aff), "now": datetime.now().isoformat()
                }, param_types={
                    "uid": spanner.param_types.STRING, "aid": spanner.param_types.STRING,
                    "new_aff": spanner.param_types.FLOAT64, "now": spanner.param_types.STRING
                })

            # D. Archive Episodes
            # We must iterate or use IN clause. Spanner Graph GQL support for IN with nodes might be tricky in Update.
            # Iterating is safer for now given uncertain GQL `IN` support for node filtering in update.
            for ep in active_episodes:
                archive_ep = """
                    GRAPH FinetuningGraph
                    MATCH (e:Episode {id: @eid})
                    SET e.valence = 999.0
                """
                transaction.execute_update(archive_ep, params={"eid": ep.id},
                                           param_types={"eid": spanner.param_types.STRING})

        try:
            self.database.run_in_transaction(consolidation_tx)
            logger.info("✅ Spanner Consolidation Complete.")
        except Exception as e:
            logger.error(f"Spanner Consolidation Transaction Failed: {e}")
            raise
