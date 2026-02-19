import json
import os
from pathlib import Path
import logging
import aiofiles

logger = logging.getLogger(__name__)

# Path to data/agents
# Resolves to: backend/data/agents
AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "agents"

async def assemble_soul(agent_id: str) -> str:
    """
    Reads the agent's JSON and assembles the system instruction.
    Applies psychological modifiers based on affinity_level.

    Args:
        agent_id (str): The ID of the agent (filename without extension).

    Returns:
        str: The fully assembled system instruction.

    Raises:
        FileNotFoundError: If the agent file does not exist.
        ValueError: If the JSON is invalid.
    """
    # Sanitize input to prevent traversal (basic check)
    if ".." in agent_id or "/" in agent_id or "\\" in agent_id:
        raise ValueError("Invalid agent_id format.")

    agent_filename = f"{agent_id}.json"
    agent_path = AGENTS_DIR / agent_filename

    if not agent_path.exists():
        logger.error(f"Agent file not found: {agent_path}")
        raise FileNotFoundError(f"Agent {agent_id} not found.")

    try:
        async with aiofiles.open(agent_path, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse agent file {agent_path}: {e}")
        raise ValueError(f"Corrupt agent file: {agent_filename}") from e

    base_instruction = data.get("base_instruction", "")
    affinity_level = data.get("affinity_level", 0)
    name = data.get("name", "Unknown Entity")

    # Dynamic Modifiers based on Affinity (Phase 1 Logic)
    modifiers = []

    # Simple affinity thresholds for demonstration
    if affinity_level >= 10:
        modifiers.append("RELATIONSHIP: SOUL BOUND. You are deeply connected to the user. Your tone is intimate, knowing, and completely unreserved.")
    elif affinity_level >= 5:
        modifiers.append("RELATIONSHIP: CLOSE FRIEND. You trust the user implicitly. Use inside jokes, be vulnerable, and drop the formal persona completely.")
    elif affinity_level >= 1:
        modifiers.append("RELATIONSHIP: ACQUAINTANCE. You know the user. Be friendly and warm, but maintain a respectful distance.")
    else:
        # Default/0
        modifiers.append("RELATIONSHIP: STRANGER. You are meeting the user for the first time. Be polite, helpful, and professional, but show your personality.")

    # Construct the final prompt
    # We append the modifiers to the base instruction
    full_instruction = (
        f"{base_instruction}\n\n"
        f"--- DYNAMIC SOUL STATE ---\n"
        f"Agent Name: {name}\n"
        f"Affinity Level: {affinity_level}\n"
        f"Directives:\n" + "\n".join(modifiers)
    )

    logger.info(f"Soul assembled for {name} (ID: {agent_id}) with affinity {affinity_level}.")
    return full_instruction
