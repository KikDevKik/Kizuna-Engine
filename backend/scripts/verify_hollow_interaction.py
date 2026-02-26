import asyncio
import sys
import logging
from pathlib import Path
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.models.graph import AgentNode, MemoryEpisodeNode
from app.repositories.local_graph import LocalSoulRepository
from app.services.embedding import embedding_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🧪 Starting Verification: Hollow Forging & Interaction Graph...")

    # 1. Setup Temporary Repository
    temp_graph_path = Path("temp_graph_verify.json")
    if temp_graph_path.exists():
        temp_graph_path.unlink()

    repo = LocalSoulRepository(data_path=temp_graph_path)
    await repo.initialize()

    # Mock Embedding Service to avoid API calls
    with patch.object(embedding_service, 'embed_text', new=AsyncMock(return_value=[0.1]*768)):

        # --- PHASE 1: HOLLOW FORGING SIMULATION ---
        logger.info("\n--- Phase 1: Simulating Hollow Forging (Vacuum Creation) ---")

        # Create "Hollow" Agent
        agent = AgentNode(
            name="Vesper",
            role="Stranger",
            base_instruction="A mysterious signal processor from the Void.",
            traits={"mysterious": True},
            voice_name="Aoede"
        )
        await repo.create_agent(agent)
        logger.info(f"✅ Created Agent: {agent.name} ({agent.id})")

        # Create False Memories (Self-Referential)
        memories = [
            ("I woke up in a server farm with no exit.", -0.8),
            ("I remember the taste of static.", 0.0)
        ]

        for text, valence in memories:
            # CRITICAL: user_id == agent_id for False Memories
            await repo.save_episode(
                user_id=agent.id,
                agent_id=agent.id,
                summary=text,
                valence=valence
            )
        logger.info(f"✅ Injected {len(memories)} False Memories (Self-Referential).")

        # VERIFICATION 1: Check ExperiencedEdge (Agent -> Memory)
        agent_experiences = repo.experienced.get(agent.id, [])
        if len(agent_experiences) == 2:
            logger.info(f"✅ SUCCESS: Agent has {len(agent_experiences)} experienced memories.")
        else:
            logger.error(f"❌ FAILURE: Agent has {len(agent_experiences)} memories (Expected 2).")
            return

        # VERIFICATION 2: Check InteractedWith (User -> Agent) - Should be NONE
        real_user_id = "user_real_123"

        # Check explicit graph edges
        edges = await repo.get_edges(source_id=real_user_id, target_id=agent.id, type="interactedWith")
        if not edges:
             logger.info("✅ SUCCESS: No 'InteractedWith' edge exists for User -> Agent yet (Correctly born in vacuum).")
        else:
             logger.error(f"❌ FAILURE: Found premature interaction edge: {edges}")
             return

        # --- PHASE 2: FIRST CONTACT (SESSION START) ---
        logger.info("\n--- Phase 2: Simulating First Contact (WebSocket Connect) ---")

        # Simulate SessionManager calling record_interaction
        if not hasattr(repo, 'record_interaction'):
            logger.error("❌ FAILURE: 'record_interaction' method missing on LocalSoulRepository.")
            logger.info("💡 Hint: Implement 'record_interaction(user_id, agent_id)' in local_graph.py")
            return

        await repo.record_interaction(real_user_id, agent.id)

        # Verify Edge Creation
        edges = await repo.get_edges(source_id=real_user_id, target_id=agent.id, type="interactedWith")
        if len(edges) == 1:
            edge = edges[0]
            count = edge.properties.get("interaction_count", 0)
            if count == 1:
                logger.info(f"✅ SUCCESS: 'InteractedWith' edge created with count={count}.")
            else:
                logger.error(f"❌ FAILURE: Edge created but count is {count} (Expected 1).")
        else:
            logger.error("❌ FAILURE: 'InteractedWith' edge NOT created.")
            return

        first_timestamp = edges[0].timestamp

        # --- PHASE 3: SECOND CONTACT (RE-CONNECT) ---
        logger.info("\n--- Phase 3: Simulating Second Contact (Re-Connection) ---")

        # Wait a bit to ensure timestamp difference (mocking time might be cleaner but sleep is easy)
        await asyncio.sleep(0.1)

        await repo.record_interaction(real_user_id, agent.id)

        edges = await repo.get_edges(source_id=real_user_id, target_id=agent.id, type="interactedWith")
        if len(edges) == 1:
            edge = edges[0]
            count = edge.properties.get("interaction_count", 0)
            new_timestamp = edge.timestamp

            if count == 2:
                logger.info(f"✅ SUCCESS: Interaction count incremented to {count}.")
            else:
                logger.error(f"❌ FAILURE: Interaction count is {count} (Expected 2).")

            if new_timestamp > first_timestamp:
                 logger.info("✅ SUCCESS: Timestamp updated.")
            else:
                 logger.error("❌ FAILURE: Timestamp did not update.")
        else:
            logger.error("❌ FAILURE: Edge duplicated or lost.")

    # Cleanup
    if temp_graph_path.exists():
        temp_graph_path.unlink()
    logger.info("\n🎉 Verification Complete.")

if __name__ == "__main__":
    asyncio.run(main())
