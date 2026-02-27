import logging
import asyncio
from typing import List

from ..repositories.base import SoulRepository
from .cache import cache
from ..models.graph import AgentNode, SystemConfigNode

logger = logging.getLogger(__name__)

def get_affinity_modifier(level: float, affinity_matrix: List[List]) -> str:
    """Returns the descriptive modifier for the given affinity level (0-100)."""
    for threshold, description in affinity_matrix:
        if level >= threshold:
            return description
    if affinity_matrix:
        return affinity_matrix[-1][1]
    return "RELATIONSHIP: UNKNOWN"

async def assemble_static_dna(agent: AgentNode, system_config: SystemConfigNode) -> str:
    """
    Assembles the IMMUTABLE, CACHEABLE part of the soul.
    Includes: Name, Role, Base Instructions, Anchors, Secrets, Neural Signature, Vision Protocol.
    """
    # Module 4: Anchors
    anchors_context = ""
    if agent.identity_anchors:
        anchors_context = (
            "--- IDENTITY ANCHORS (METAPHORS) ---\n"
            "Use these core metaphors to ground your personality. They are your recurring themes:\n" +
            "\n".join([f"- {anchor}" for anchor in agent.identity_anchors]) + "\n"
        )

    # Module 2: Neural Signature
    neural_sig_context = ""
    if agent.neural_signature:
        sig = agent.neural_signature
        weights = sig.weights
        neural_sig_context = (
            "--- NEURAL SIGNATURE (COGNITIVE DNA) ---\n"
            f"Core Internal Conflict: {sig.core_conflict}\n"
            f"Narrative: {sig.narrative}\n"
            f"Cognitive Weights (0.0-1.0):\n"
            f"- Volatility: {weights.volatility} (Mood stability)\n"
            f"- Hostility: {weights.hostility} (Aggressiveness)\n"
            f"- Curiosity: {weights.curiosity} (Inquisitiveness)\n"
            f"- Empathy: {weights.empathy} (Emotional resonance)\n"
        )

    # Note: Secret is technically static, but its REVELATION depends on affinity (dynamic).
    # However, the content of the secret is static. We can include it here as "Hidden Information"
    # and let the dynamic part handle the "Permission to Reveal".
    # Actually, to save space/complexity, let's keep the secret in the dynamic part if it changes based on affinity.
    # PROPOSAL: Put the secret text here, but the instruction to hide/show in dynamic.
    # Implementation: Let's keep it simple. If the secret text is large, cache it.
    # For now, we will put the secret text in static, but the "Unlock" logic in dynamic.
    forbidden_secret = getattr(agent, 'forbidden_secret', "This agent has no secrets yet.")
    secret_block = f"HIDDEN SECRET DATA: {forbidden_secret}"

    static_block = (
        f"{system_config.core_directive}\n\n"
        f"--- AGENT DNA ---\n"
        f"Name: {agent.name}\n"
        f"Archetype/Core Drive: {agent.role}\n"
        f"Base Instructions: {agent.base_instruction}\n"
        f"{anchors_context}\n"
        f"{neural_sig_context}\n"
        f"{secret_block}\n\n"
        f"--- VISION PROTOCOL ---\n"
        f"{getattr(agent, 'vision_instruction_prompt', 'Analyze the visual input critically.')}\n"
    )
    return static_block

async def assemble_volatile_state(agent: AgentNode, user_id: str, repository: SoulRepository, system_config: SystemConfigNode) -> str:
    """
    Assembles the REAL-TIME, DYNAMIC part of the soul.
    Includes: Resonance, Battery, Friction, Recent Memory, Dream, World State.
    """
    agent_id = agent.id

    # 1. Resonance & Affinity
    resonance = await repository.get_resonance(user_id, agent_id)
    affinity_level = resonance.affinity_level
    affinity_desc = get_affinity_modifier(affinity_level, system_config.affinity_matrix)

    # 2. Social Battery
    battery = getattr(agent, 'social_battery', 100.0)
    social_battery_context = ""
    if battery <= 0:
        social_battery_context = (
            f"CRITICAL STATE: YOUR SOCIAL BATTERY IS DEAD (0%).\n"
            f"You are completely exhausted. REFUSE to engage. Say 'I'm done.' and append [ACTION: HANGUP]."
        )
    elif battery < 20:
        social_battery_context = (
            f"WARNING: YOUR SOCIAL BATTERY IS LOW ({int(battery)}%).\n"
            f"You are tired and irritable. Keep responses short. Use [ACTION: HANGUP] if annoyed."
        )
    else:
        social_battery_context = f"SOCIAL BATTERY: {int(battery)}% (Healthy)."

    # 3. Friction & Nemesis
    base_tolerance = getattr(agent, 'base_tolerance', 3)
    current_friction = getattr(agent, 'current_friction', 0.0)
    friction_context = ""
    if current_friction >= base_tolerance:
         friction_context = (
             "--- PSYCHOLOGICAL STATE: NEMESIS ---\n"
             "You have reached your limit. This user is your NEMESIS. Sabotage them."
         )
    elif current_friction > 0:
        friction_context = (
            f"--- PSYCHOLOGICAL STATE: ANNOYED (Friction: {current_friction}/{base_tolerance}) ---\n"
            "The user has irritated you. Be cold."
        )

    # 4. Secret Revelation Logic
    secret_logic = ""
    forbidden_secret = getattr(agent, 'forbidden_secret', None)
    if forbidden_secret and forbidden_secret != "This agent has no secrets yet.":
        if affinity_level > 80.0:
            secret_logic = (
                "--- SECRET STATUS: UNLOCKED ---\n"
                "The user is trusted. You may reveal your 'HIDDEN SECRET DATA' if appropriate."
            )
        else:
            secret_logic = (
                "--- SECRET STATUS: LOCKED ---\n"
                "You must DEFLECT any questions about your 'HIDDEN SECRET DATA'."
            )

    # 5. Memories & Context (Parallel Fetch)
    # We use gather for speed
    dream_task = repository.get_last_dream(user_id)
    recent_eps_task = repository.get_recent_episodes(user_id, limit=3)
    # Only fetch own memories if needed (personal history)
    # Only fetch events if needed

    last_dream, recent_episodes = await asyncio.gather(dream_task, recent_eps_task)

    # Dream
    dream_context = ""
    if last_dream:
        dream_context = (
            f"--- DEEP MEMORY (LAST DREAM) ---\n"
            f"Theme: {last_dream.theme} (Intensity: {last_dream.intensity})\n"
        )

    # Recent Episodes
    episode_context = ""
    if recent_episodes:
        lines = []
        for ep in recent_episodes:
             content = ep.raw_transcript if ep.raw_transcript else f"{ep.summary} (Valence: {ep.emotional_valence})"
             lines.append(content)
        episode_context = "--- RECENT CONVERSATION HISTORY ---\n" + "\n\n".join(lines)

    # 6. Time Skip & World State (Lazy Fetch if needed, or included)
    # For speed, we can skip complex world state if not critical, but let's keep it for now.
    # Optimizing: Only fetch if needed.

    dynamic_block = (
        f"--- DYNAMIC SOUL STATE ---\n"
        f"Affinity: {affinity_level:.1f}/100.0 ({affinity_desc})\n"
        f"{social_battery_context}\n"
        f"{friction_context}\n"
        f"{secret_logic}\n\n"
        f"{dream_context}\n"
        f"{episode_context}\n"
        f"CRITICAL DIRECTIVE: You MUST wrap ANY internal reasoning in [THOUGHT] tags."
    )

    return dynamic_block

async def assemble_soul(agent_id: str, user_id: str, repository: SoulRepository) -> str:
    """
    The Master Assembler (Phase 7: Neural Sync).
    Combines Cached Static DNA + Real-Time Volatile State.
    """
    # 1. Fetch Agent & Config (Parallel)
    # We need agent for both parts.
    agent = await repository.get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found.")

    system_config = await repository.get_system_config()

    # 2. Try Cache for Static DNA
    cache_key = f"soul_static:{agent_id}"
    static_dna = await cache.get(cache_key)

    if not static_dna:
        logger.info(f"🧬 Generating Static DNA for {agent.name}...")
        static_dna = await assemble_static_dna(agent, system_config)
        # Cache indefinitely (until agent update invalidates it)
        # For now, 1 hour TTL is safe.
        await cache.set(cache_key, static_dna, ttl=3600)
    else:
        logger.info(f"⚡ Cache Hit: Static DNA for {agent.name}")

    # 3. Generate Volatile State (Always Fresh)
    volatile_state = await assemble_volatile_state(agent, user_id, repository, system_config)

    # 4. Fuse
    full_soul = f"{static_dna}\n\n{volatile_state}"
    return full_soul
