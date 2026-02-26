import asyncio
import sys
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import tempfile
import shutil
import uuid

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Path
# Adjust so that 'app' and 'core' are importable
current_file = Path(__file__).resolve()
backend_root = current_file.parent.parent
sys.path.insert(0, str(backend_root))

try:
    from app.services.agent_service import AgentService, HollowAgentProfile, GeneratedMemory
    from app.repositories.local_graph import LocalSoulRepository
    from app.services.soul_assembler import assemble_soul
    from app.models.graph import AgentNode
    from core.config import settings
except ImportError as e:
    logger.error(f"Import Error: {e}")
    sys.exit(1)

async def verify_hollow_memory():
    logger.info("--- Starting Hollow Memory Verification Protocol ---")

    # Create a temporary directory for the test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        agents_dir = temp_path / "agents"
        agents_dir.mkdir()
        graph_path = temp_path / "graph.json"

        # Initialize Services with Temp Paths
        # We must override the data_dir for AgentService to isolate tests
        agent_svc = AgentService(data_dir=agents_dir)

        # Initialize LocalSoulRepository with temp graph path
        repo = LocalSoulRepository(data_path=graph_path)
        await repo.initialize()

        # Mock the Gemini Client Response
        # We need to simulate the return of `agent_svc.client.aio.models.generate_content`
        mock_memories = [
            GeneratedMemory(summary="VerifyAlpha: I saw the neon rain fall in sector 9.", emotional_valence=-0.5),
            GeneratedMemory(summary="VerifyBeta: I deciphered the ancient code on the monolith.", emotional_valence=0.8)
        ]

        mock_profile = HollowAgentProfile(
            name="Test Stranger",
            backstory="A digital ghost wandering the datastreams.",
            traits={"curiosity": "high", "stealth": "max"},
            voice_name="Puck",
            false_memories=mock_memories
        )

        # Build the mock chain
        # The service calls: response = await self.client.aio.models.generate_content(...)
        # We need to mock 'generate_content' to return an object with a .parsed attribute
        mock_gen_content_response = MagicMock()
        mock_gen_content_response.parsed = mock_profile

        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_gen_content_response)

        # Inject the mock client into the service instance
        agent_svc.client = mock_client

        # --- EXECUTION PHASE ---

        # 1. Forge the Hollow Agent
        logger.info("Forging Hollow Agent...")
        try:
            # aesthetic_description is arbitrary here since we mock the response
            agent_node, memories = await agent_svc.forge_hollow_agent("Cyberpunk drifter")
        except Exception as e:
            logger.error(f"Failed to forge agent: {e}")
            return

        logger.info(f"Agent Created: {agent_node.name} ({agent_node.id})")
        logger.info(f"Generated {len(memories)} False Memories.")

        # 2. Mimic the Router Logic: Save to Repository
        # The router saves the agent and then the memories.
        await repo.create_agent(agent_node)

        for mem in memories:
            # CRITICAL CHECK: The router saves these with user_id=agent_id (Self-Experience)
            logger.info(f"Saving Memory: {mem.summary}")
            await repo.save_episode(
                user_id=agent_node.id,  # Agent experiences their own memory
                agent_id=agent_node.id,
                summary=mem.summary,
                valence=mem.emotional_valence
            )

        # 3. Assemble Soul (Generate System Prompt)
        logger.info("Assembling Soul (Context Injection)...")
        # Use a dummy user ID for the interaction context
        user_id = str(uuid.uuid4())

        try:
            system_prompt = await assemble_soul(agent_node.id, user_id, repo)
        except Exception as e:
            logger.error(f"Soul Assembly Failed: {e}")
            return

        # --- VERIFICATION PHASE ---

        logger.info("\n--- Verification Analysis ---")

        missing = []
        found_count = 0

        if "VerifyAlpha" in system_prompt:
            logger.info("✅ Memory Alpha detected.")
            found_count += 1
        else:
            logger.error("❌ Memory Alpha MISSING.")
            missing.append("VerifyAlpha")

        if "VerifyBeta" in system_prompt:
            logger.info("✅ Memory Beta detected.")
            found_count += 1
        else:
            logger.error("❌ Memory Beta MISSING.")
            missing.append("VerifyBeta")

        # Check for the Header
        header = "--- PERSONAL HISTORY (FALSE MEMORIES) ---"
        if header in system_prompt:
             logger.info("✅ Personal History Header detected.")
        else:
             logger.error("❌ Personal History Header MISSING.")
             missing.append("Header")

        if not missing:
            logger.info("\n🎉 SUCCESS: All False Memories were correctly injected into the System Prompt.")
            # Print the relevant section for manual confirmation
            start = system_prompt.find(header)
            end = system_prompt.find("\n\n", start)
            snippet = system_prompt[start:end]
            logger.info(f"\n--- INJECTED CONTEXT SNIPPET ---\n{snippet}\n--------------------------------")
        else:
            logger.error("\n💀 FAILURE: Context Injection Failed.")
            logger.error(f"Missing elements: {missing}")
            logger.error("Full Prompt Dump (First 2000 chars):")
            logger.error(system_prompt[:2000])

if __name__ == "__main__":
    asyncio.run(verify_hollow_memory())
