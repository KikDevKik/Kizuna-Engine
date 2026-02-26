import sys
import os
import asyncio
import logging
from pathlib import Path

# Add backend to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.repositories.legacy_json_graph import LegacyJsonSoulRepository
from app.repositories.local_graph import LocalSoulRepository
from app.models.sql import NodeModel, EdgeModel
from app.core.database import AsyncSessionLocal, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate():
    logger.info("🚀 Starting Migration to SQLite...")

    # 1. Load Legacy
    legacy_repo = LegacyJsonSoulRepository()
    await legacy_repo.initialize()
    logger.info(f"Loaded Legacy Data: {len(legacy_repo.users)} Users, {len(legacy_repo.agents)} Agents")

    # 2. Init SQLite
    new_repo = LocalSoulRepository()
    await new_repo.initialize()

    # 3. Migrate Nodes
    async def save_node(node, label):
        if not node: return
        await new_repo._save_node(node.id, label, node.model_dump(mode='json'), vector_id=None)

    logger.info("Migrating Users...")
    for user in legacy_repo.users.values():
        await save_node(user, "UserNode")

    logger.info("Migrating Agents...")
    for agent in legacy_repo.agents.values():
        await save_node(agent, "AgentNode")

    logger.info(f"Migrating {len(legacy_repo.episodes)} Episodes...")
    for ep in legacy_repo.episodes.values():
        await save_node(ep, "MemoryEpisodeNode")

    logger.info("Migrating Facts...")
    for fact in legacy_repo.facts.values():
        await save_node(fact, "FactNode")

    logger.info("Migrating Dreams...")
    for dream in legacy_repo.dreams.values():
        await save_node(dream, "DreamNode")

    logger.info("Migrating Archetypes...")
    for arc in legacy_repo.archetypes.values():
        await save_node(arc, "ArchetypeNode")

    logger.info("Migrating Locations...")
    for loc in legacy_repo.locations.values():
        await save_node(loc, "LocationNode")

    logger.info("Migrating Factions...")
    for fac in legacy_repo.factions.values():
        await save_node(fac, "FactionNode")

    logger.info("Migrating Collective Events...")
    for evt in legacy_repo.collective_events.values():
        await save_node(evt, "CollectiveEventNode")

    logger.info("Migrating Singletons...")
    if legacy_repo.global_dream:
        await save_node(legacy_repo.global_dream, "GlobalDreamNode")
    if legacy_repo.system_config:
        await save_node(legacy_repo.system_config, "SystemConfigNode")

    # 4. Migrate Edges
    logger.info("Migrating Edges...")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Experienced
            for uid, ep_ids in legacy_repo.experienced.items():
                for eid in ep_ids:
                    session.add(EdgeModel(source_id=uid, target_id=eid, type="ExperiencedEdge"))

            # Knows
            for uid, fact_ids in legacy_repo.knows.items():
                for fid in fact_ids:
                    session.add(EdgeModel(source_id=uid, target_id=fid, type="KnowsEdge"))

            # Shadows
            for uid, shadows in legacy_repo.shadows.items():
                for s in shadows:
                    session.add(EdgeModel(source_id=uid, target_id=s.target_id, type="ShadowEdge", properties=s.model_dump(mode='json')))

            # Embodies
            for aid, embodies in legacy_repo.embodies.items():
                for e in embodies:
                    session.add(EdgeModel(source_id=aid, target_id=e.target_id, type="EmbodiesEdge", properties=e.model_dump(mode='json')))

            # Resonances
            for u_res in legacy_repo.resonances.values():
                for r in u_res.values():
                    session.add(EdgeModel(source_id=r.source_id, target_id=r.target_id, type="ResonanceEdge", properties=r.model_dump(mode='json')))

            # Agent Affinities
            for a_aff in legacy_repo.agent_affinities.values():
                for a in a_aff.values():
                    session.add(EdgeModel(source_id=a.source_agent_id, target_id=a.target_agent_id, type="AgentAffinityEdge", properties=a.model_dump(mode='json')))

            # Explicit Graph Edges
            for ge in legacy_repo.graph_edges:
                session.add(EdgeModel(source_id=ge.source_id, target_id=ge.target_id, type=ge.type, properties=ge.model_dump(mode='json')))

    logger.info("✅ Migration Complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
