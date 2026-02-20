import json
import logging
from pathlib import Path
from app.models.graph import AgentNode

logger = logging.getLogger(__name__)

# Resolve paths relative to this file
# backend/app/services/seeder.py -> backend/data/agents
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "agents"
GRAPH_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "graph.json"

async def seed_data():
    """
    Ensures that the application has the necessary initial data to run.
    """
    logger.info("🌱 Seeding: Checking data integrity...")

    # 1. Seed Agents
    if not AGENTS_DIR.exists():
        AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Check if empty (ignore .gitignore or other dotfiles)
    existing_agents = list(AGENTS_DIR.glob("*.json"))

    if not existing_agents:
        logger.info("⚠️ No agents found. Creating default 'Kizuna' agent.")

        kizuna = AgentNode(
            id="kizuna",
            name="Kizuna",
            role="CORE SYSTEM",
            base_instruction="You are Kizuna, a digital partner projected in the user's space. You are NOT a generic AI assistant. You have a chaotic but supportive personality. Treat the user as an equal, use humor, be direct, and avoid excessive formality or robotic apologies. Respond conversationally, concisely, and naturally, as if in the same room.",
            avatar_path=None,
            tags=["core", "system"],
            traits={"warmth": 0.5, "chaos": 0.8}
        )

        # Save to file
        kizuna_path = AGENTS_DIR / "kizuna.json"
        try:
            with open(kizuna_path, "w", encoding="utf-8") as f:
                json.dump(kizuna.model_dump(mode='json'), f, indent=4, ensure_ascii=False)
            logger.info(f"✅ Created {kizuna_path}")
        except Exception as e:
            logger.error(f"❌ Failed to create Kizuna agent: {e}")

    # 2. Seed Graph (Users/Memory)
    # We ensure the file exists so LocalSoulRepository doesn't complain or can load empty.
    if not GRAPH_FILE.exists():
        logger.info("⚠️ Graph file missing. Initializing empty graph structure.")
        GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)

        default_graph = {
            "users": [],
            "agents": [], # Graph agents are distinct from file agents in this new architecture (references)
            "episodes": [],
            "facts": [],
            "resonances": [],
            "experienced": {},
            "knows": {}
        }

        try:
            with open(GRAPH_FILE, "w", encoding="utf-8") as f:
                json.dump(default_graph, f, indent=2)
            logger.info(f"✅ Created {GRAPH_FILE}")
        except Exception as e:
            logger.error(f"❌ Failed to create graph file: {e}")

    logger.info("✅ Seeding complete.")
