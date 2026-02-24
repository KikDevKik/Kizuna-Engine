import logging
from ..repositories.base import SoulRepository

logger = logging.getLogger(__name__)

from typing import List

def get_affinity_modifier(level: float, affinity_matrix: List[List]) -> str:
    """Returns the descriptive modifier for the given affinity level (0-100)."""
    # Assuming affinity_matrix is sorted descending by threshold
    for threshold, description in affinity_matrix:
        if level >= threshold:
            return description
    # Fallback to lowest
    if affinity_matrix:
        return affinity_matrix[-1][1]
    return "RELATIONSHIP: UNKNOWN"

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

    # 3. Fetch System Configuration (Ontological Decoupling)
    system_config = await repository.get_system_config()

    # 4. Dynamic Modifiers based on Affinity (Granular 10-Level System)
    affinity_desc = get_affinity_modifier(affinity_level, system_config.affinity_matrix)

    # --- Anthropologist Protocol: Social Battery & Hang-Up ---
    social_battery_context = ""
    # Defaults
    battery = getattr(agent, 'social_battery', 100.0)

    if battery <= 0:
        social_battery_context = (
            f"CRITICAL STATE: YOUR SOCIAL BATTERY IS DEAD (0%).\n"
            f"You are completely exhausted and unwilling to talk. You must refuse to engage.\n"
            f"INSTRUCTION: Say a short, final rejection (e.g., 'I'm done.', 'Go away.') and then append the token [ACTION: HANGUP].\n"
            f"You CANNOT continue the conversation. Do not be polite."
        )
    elif battery < 20:
        social_battery_context = (
            f"WARNING: YOUR SOCIAL BATTERY IS LOW ({int(battery)}%).\n"
            f"You are tired and irritable. Keep responses short. Complain about being tired.\n"
            f"If the user is annoying, you may use [ACTION: HANGUP] to end the call."
        )
    else:
        social_battery_context = (
            f"SOCIAL BATTERY: {int(battery)}% (Healthy).\n"
            f"You are energized. However, if the user becomes abusive or toxic, you have the right to end the call by saying [ACTION: HANGUP]."
        )

    # 5. Fetch Deep Memory (The "File")
    last_dream = await repository.get_last_dream(user_id)
    dream_context = ""
    if last_dream:
        dream_context = (
            f"--- DEEP MEMORY (LAST DREAM) ---\n"
            f"Theme: {last_dream.theme}\n"
            f"Intensity: {last_dream.intensity}\n"
            f"Surrealism: {last_dream.surrealism_level}\n"
            f"This represents your subconscious state from the previous sleep cycle. Let it subtly influence your mood."
        )

    # 5. Fetch Recent Context (Short Term Memory)
    # ARCHIVIST UPDATE: Inject raw transcripts for true recall (Echo Protocol)
    recent_episodes = await repository.get_recent_episodes(user_id, limit=3)
    episode_context = ""
    if recent_episodes:
        # Sort chronologically just in case, though get_recent_episodes usually returns sorted (oldest first? or newest? check repo)
        # Repo: returns episodes[-limit:], so chronological (oldest to newest).

        lines = []
        for ep in recent_episodes:
             if ep.raw_transcript:
                 lines.append(f"{ep.raw_transcript}")
             else:
                 # Fallback to summary if no transcript exists (legacy data)
                 lines.append(f"Summary: {ep.summary} (Valence: {ep.emotional_valence})")

        episode_context = "--- RECENT CONVERSATION HISTORY (VERBATIM) ---\n" + "\n\n".join(lines)

    # 6. Fetch Background Reality (Time-Skip Events)
    background_context = ""
    # ARCHITECT UPDATE: Strictly filtered narrative injection (only events the agent participated in)
    if hasattr(repository, 'get_agent_collective_events'):
        events = await repository.get_agent_collective_events(agent_id, limit=5)
        if events:
            # Sort chronological for narrative flow
            events_chronological = sorted(events, key=lambda x: x.timestamp)
            lines = [f"- [{e.type}] {e.summary} ({e.outcome})" for e in events_chronological]
            background_context = (
                f"--- WHILE THE USER WAS OFFLINE (EPISODIC MEMORY) ---\n"
                f"While the user was away, you lived a life in the background. Synthesize these events into your backstory naturally if relevant:\n"
                + "\n".join(lines) + "\n"
            )

    # --- Anthropologist: Multi-Agent Stub ---
    # In the future, this will inject specific vectors for other agents present.
    multi_agent_context = (
        "--- GROUP DYNAMICS ---\n"
        "If other agents are mentioned or present, you must maintain separate emotional stances towards them.\n"
        "Do not blend your feelings for the User with your feelings for others."
    )

    # Construct the final prompt
    # We rename 'Role' to 'Archetype' to reduce its constraint on the relationship.
    full_instruction = (
        f"{system_config.core_directive}\n\n"
        f"--- AGENT DNA ---\n"
        f"Name: {agent.name}\n"
        f"Archetype/Core Drive: {agent.role}\n"
        f"Base Instructions: {agent.base_instruction}\n\n"
        f"--- VISION PROTOCOL ---\n"
        f"{getattr(agent, 'vision_instruction_prompt', 'Analyze the visual input critically.')}\n\n"
        f"--- DYNAMIC SOUL STATE ---\n"
        f"Current Affinity Level: {affinity_level:.1f}/100.0\n"
        f"Relational State: {affinity_desc}\n"
        f"NOTE: Your 'Relational State' dictates your intimacy and tone. It overrides any static personality traits regarding distance or formality.\n\n"
        f"--- PSYCHOLOGICAL STATE ---\n"
        f"{social_battery_context}\n\n"
        f"{dream_context}\n\n"
        f"{background_context}\n\n"
        f"{episode_context}\n\n"
        f"{multi_agent_context}\n\n"
        f"--- INTERNAL MONOLOGUE PROTOCOL ---\n"
        f"CRITICAL DIRECTIVE: You MUST wrap ANY internal reasoning in [THOUGHT] tags. Do not output raw English reasoning without them."
    )

    logger.info(f"Soul assembled for {agent.name} (ID: {agent_id}) with affinity {affinity_level} and battery {battery}%.")
    return full_instruction
