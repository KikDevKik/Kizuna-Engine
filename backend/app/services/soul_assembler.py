import logging
from ..repositories.base import SoulRepository

logger = logging.getLogger(__name__)

async def assemble_soul(agent_id: str, user_id: str, repository: SoulRepository) -> str:
    """
    Assembles the system instruction using the SoulRepository.
    Applies psychological modifiers based on the specific affinity between User and Agent.

    Args:
        agent_id (str): The ID of the agent.
        user_id (str): The ID of the user.
        repository (SoulRepository): The data access layer.

    Returns:
        str: The fully assembled system instruction.

    Raises:
        ValueError: If the agent is not found.
    """
    # 1. Fetch Agent (Static DNA)
    agent = await repository.get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found in repository.")

    # 2. Fetch Resonance (Dynamic Relationship)
    resonance = await repository.get_resonance(user_id, agent_id)
    affinity_level = resonance.affinity_level

    # 3. Dynamic Modifiers based on Affinity (Phase 3 Logic)
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
    full_instruction = (
        f"{agent.base_instruction}\n\n"
        f"--- DYNAMIC SOUL STATE ---\n"
        f"Agent Name: {agent.name}\n"
        f"User ID: {user_id}\n"
        f"Affinity Level: {affinity_level}\n"
        f"Directives:\n" + "\n".join(modifiers)
    )

    logger.info(f"Soul assembled for {agent.name} (ID: {agent_id}) with affinity {affinity_level}.")
    return full_instruction
