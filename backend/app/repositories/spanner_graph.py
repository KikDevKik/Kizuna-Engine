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
from ..services.embedding import embedding_service

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
        # Generate query embedding
        query_embedding = await embedding_service.embed_text(query)
        if not query_embedding:
            logger.warning("Failed to generate embedding for query.")
            return []

        def query_tx(snapshot):
            # GQL with Vector Search
            # Uses COSINE_DISTANCE to find semantically similar facts
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
        # Generate embedding before transaction
        embedding = await embedding_service.embed_text(content)

        def save_tx(transaction):
            # 1. Create Fact Node
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
            return FactNode(id=str(fact_id), content=content, category=category, embedding=embedding)
        except Exception as e:
            logger.error(f"Spanner Save Fact Failed: {e}")
            raise

    async def consolidate_memories(self, user_id: str, dream_generator=None) -> None:
        """
        GQL implementation for memory consolidation.
        """
        # Stub for now.
        # In Production Spanner, this would involve complex GQL:
        # 1. MATCH (u:User {id: @uid})-[:EXPERIENCED]->(e:Episode) WHERE e.valence = 0.5
        # 2. Extract texts -> Send to Gemini -> Get Summary
        # 3. CREATE (new_e:Episode)
        # 4. DELETE old edges or mark e.valence = 0.0
        logger.info(f"Spanner Consolidation triggered for {user_id} (Stub).")
        return
