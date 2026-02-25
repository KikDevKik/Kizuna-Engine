import logging
import random
import math
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from ..repositories.base import SoulRepository
from ..models.graph import (
    CollectiveEventNode, LocationNode, AgentAffinityEdge, UserNode,
    IntentType, EphemeralIntent, ParticipatedIn, OccurredAt
)

logger = logging.getLogger(__name__)

class TimeSkipService:
    """
    The Offline Time-Skip Engine.
    Simulates background life using stochastic generators and probability matrices.
    Zero LLM interference. Pure Math.
    """

    def __init__(self, repository: SoulRepository):
        self.repository = repository

        # Stochastic Configuration
        self.min_delta_minutes = 10 # Minimum time away to trigger simulation
        self.max_events = 5 # Cap events to prevent flooding context

        # Anthropologist Parameters
        self.battery_recharge_per_hour = 20.0 # 20% recharge per hour of offline time

        # Hardcoded Shadow Agents (Procedural NPCs)
        self.shadow_agents = [
            "Stranger_01", "Bartender_X", "Cyber_Ronin", "Neon_Rat", "Corp_Drone",
            "The_Glitch", "Null_Entity", "System_Daemon"
        ]

        # Default Locations (if graph is empty)
        self.default_locations = [
            ("The Glitch Bar", "social", "A neon-soaked dive bar where data-runners congregate."),
            ("Sector 4 Plaza", "public", "A busy intersection under the holographic sky."),
            ("The Old Server Room", "hidden", "A quiet, humming sanctuary of ancient tech.")
        ]

        # Intent Outcome Matrix
        # Maps Intent -> List of (Probability, Outcome, ValenceDelta, SummaryTemplate)
        self.outcome_matrix = {
            IntentType.SUPPORT: [
                (0.7, "BONDED", 5.0, "{p1} and {p2} had a deep heart-to-heart at {loc}."),
                (1.0, "CHATTED", 1.0, "{p1} and {p2} shared a drink at {loc} and caught up.")
            ],
            IntentType.CONFLICT: [
                (0.4, "FOUGHT", -10.0, "{p1} and {p2} nearly came to blows at {loc} over a misunderstanding."),
                (1.0, "ARGUED", -5.0, "{p1} and {p2} got into a heated debate at {loc}.")
            ],
            IntentType.GOSSIP: [
                (0.5, "SHARED_SECRETS", 2.0, "{p1} whispered secrets to {p2} at {loc}."),
                (1.0, "RUMOR_MILL", 0.5, "{p1} and {p2} were seen gossiping at {loc}.")
            ],
            IntentType.AVOID: [
                (0.8, "IGNORED", -1.0, "{p1} saw {p2} at {loc} but deliberately looked away."),
                (1.0, "AWKWARD", -2.0, "{p1} and {p2} had an awkward run-in at {loc}.")
            ]
        }

    async def simulate_background_life(self, user: UserNode) -> List[CollectiveEventNode]:
        """
        Calculates time passed since user.last_seen and generates background events.
        Also handles Social Battery Recharge and Emotional Decay.
        """
        now = datetime.now()
        last_seen = user.last_seen

        # Safety: If last_seen is future or null (shouldn't be with new schema), handle it.
        if not last_seen:
            last_seen = now

        delta = now - last_seen
        minutes_passed = delta.total_seconds() / 60.0

        # --- Anthropologist: Battery Recharge & Emotional Decay ---
        await self._apply_anthropologist_protocols(user.id, minutes_passed)

        if minutes_passed < self.min_delta_minutes:
            logger.info(f"⏳ Time-Skip: Only {minutes_passed:.1f}m passed. No simulation needed.")
            return []

        logger.info(f"🕰️ Time-Skip: User away for {minutes_passed:.1f}m. Simulating background reality...")

        # Determine number of events (Logarithmic scale or simple caps)
        num_events = int(minutes_passed / 60)
        num_events = max(1, min(num_events, self.max_events))

        events = []
        for _ in range(num_events):
            event = await self._generate_stochastic_event(user.id)
            if event:
                events.append(event)

        return events

    async def _apply_anthropologist_protocols(self, user_id: str, minutes_passed: float):
        """
        Applies mathematical decay to emotions and recharges social batteries.
        """
        if minutes_passed <= 0:
            return

        # Fetch known agents (Simulated Reality only affects active nodes)
        # We need access to internal repo structure or add a method.
        # Assuming LocalSoulRepository has .agents
        agents = []
        if hasattr(self.repository, 'agents'):
            agents = list(self.repository.agents.values())

        for agent in agents:
            # --- Battery Recharge ---
            recharge_amount = (minutes_passed / 60.0) * self.battery_recharge_per_hour
            if agent.social_battery < 100.0:
                agent.social_battery = min(100.0, agent.social_battery + recharge_amount)
                agent.last_battery_update = datetime.now()
                # Persist Agent State
                if hasattr(self.repository, 'create_agent'):
                     # 🏰 BASTION SHIELD: Protect battery state save
                     await asyncio.shield(self.repository.create_agent(agent))

            # --- Emotional Decay (Ebbinghaus) ---
            resonance = await self.repository.get_resonance(user_id, agent.id)
            if resonance:
                await self._apply_decay_to_resonance(resonance, agent, minutes_passed)

    async def _apply_decay_to_resonance(self, resonance, agent, minutes_passed: float):
        """
        Applies Exponential Decay to affinity.
        """
        BASELINE = 50.0
        current_affinity = resonance.affinity_level

        if abs(current_affinity - BASELINE) < 0.1:
            return

        # --- Anthropologist Update: Precision Decay ---
        # Instead of just using 'minutes_passed' since user login, use the ACTUAL last interaction time
        # from the graph edges. This prevents decay from applying to active relationships.
        decay_minutes = minutes_passed # Default fallback

        if hasattr(self.repository, 'get_last_interaction'):
            last_ts = await self.repository.get_last_interaction(resonance.source_id, agent.id)
            if last_ts != datetime.min:
                delta_ts = datetime.now() - last_ts
                decay_minutes = delta_ts.total_seconds() / 60.0

        # Don't decay if interaction was very recent (< 1 hour)
        if decay_minutes < 60:
            return

        decay_rate = getattr(agent, 'emotional_decay_rate', 0.1)
        hours_passed = decay_minutes / 60.0

        difference = current_affinity - BASELINE
        decay_factor = math.exp(-decay_rate * hours_passed)
        new_difference = difference * decay_factor
        new_affinity = BASELINE + new_difference

        delta = new_affinity - current_affinity
        if abs(delta) > 0.1:
            if hasattr(self.repository, 'update_resonance'):
                # 🏰 BASTION SHIELD: Protect resonance decay update
                await asyncio.shield(self.repository.update_resonance(resonance.source_id, resonance.target_id, delta))

    async def _generate_stochastic_event(self, user_id: str) -> Optional[CollectiveEventNode]:
        """
        Generates a single event using Intent Vectors.
        """
        # 1. Identify Valid Participants
        # Filter agents by checking if user has interacted with them (Resonance Exists)
        # This keeps the world focused on the user's circle.
        valid_agents = []
        if hasattr(self.repository, 'agents') and hasattr(self.repository, 'resonances'):
            user_resonances = self.repository.resonances.get(user_id, {})
            known_agent_ids = list(user_resonances.keys())
            # Ensure they exist in agent list (sanity check)
            for aid in known_agent_ids:
                if aid in self.repository.agents:
                    valid_agents.append(self.repository.agents[aid])

        if not valid_agents:
            # Fallback if user is new: Use random agents from repo
             if hasattr(self.repository, 'agents'):
                 valid_agents = list(self.repository.agents.values())

        if not valid_agents:
            return None

        # 2. Select Participants (2-3)
        num_participants = random.randint(2, 3)
        participants = []
        real_agents = []

        # At least one real agent is required for a meaningful event
        primary_agent = random.choice(valid_agents)
        participants.append(primary_agent.id)
        real_agents.append(primary_agent)

        # Fill the rest
        for _ in range(num_participants - 1):
            if random.random() < 0.6: # 60% chance of another known agent
                other = random.choice(valid_agents)
                if other.id not in participants:
                    participants.append(other.id)
                    real_agents.append(other)
                else:
                    # Fallback to shadow
                    shadow = random.choice(self.shadow_agents)
                    if shadow not in participants:
                        participants.append(shadow)
            else:
                shadow = random.choice(self.shadow_agents)
                if shadow not in participants:
                    participants.append(shadow)

        # 3. Calculate Intent (Ephemeral)
        # We only calculate intent between the first two participants for simplicity
        # If both are real, we check their affinity.
        p1_id = participants[0]
        p2_id = participants[1]

        intent_type = IntentType.GOSSIP # Default

        if len(real_agents) >= 2 and p2_id == real_agents[1].id:
            # Real-to-Real Interaction
            intent_type = await self._calculate_intent(real_agents[0], real_agents[1])
        else:
            # Real-to-Shadow Interaction (Randomized based on Agent Traits?)
            # Simplified: Random
            intent_type = random.choice(list(IntentType))

        # 4. Resolve Outcome
        outcome_data = self._resolve_outcome(intent_type)
        if not outcome_data:
            return None

        outcome, valence_delta, summary_template = outcome_data

        # 5. Select Location
        location = await self._get_random_location()

        # 6. Format Summary
        participant_names = []
        for pid in participants:
            if hasattr(self.repository, 'agents') and pid in self.repository.agents:
                participant_names.append(self.repository.agents[pid].name)
            else:
                participant_names.append(pid) # Shadow agent name

        summary = summary_template.format(
            p1=participant_names[0],
            p2=participant_names[1] if len(participants) > 1 else "someone",
            loc=location.name
        )

        # 7. Create Event Node
        event = CollectiveEventNode(
            type=intent_type.value, # Event Type maps to Intent Type
            location_id=location.id,
            participants=[], # Explicitly empty, moving to edges
            outcome=outcome,
            summary=summary,
            timestamp=datetime.now() - timedelta(minutes=random.randint(1, 60))
        )

        # 8. Apply Consequence (Update Affinity)
        if len(real_agents) >= 2:
             await self._apply_affinity_shift(real_agents[0].id, real_agents[1].id, valence_delta)

        # 9. Persist Event
        if hasattr(self.repository, 'record_collective_event'):
            # 🏰 BASTION SHIELD: Protect event recording
            await asyncio.shield(self.repository.record_collective_event(event))

        # 10. Create Graph Edges (Pillar 1 Upgrade)
        if hasattr(self.repository, 'create_edge'):
            # ParticipatedIn Edges
            for pid in participants:
                edge = ParticipatedIn(
                    source_id=pid,
                    target_id=event.id,
                    timestamp=event.timestamp,
                    properties={"role": "participant"}
                )
                await asyncio.shield(self.repository.create_edge(edge))

            # OccurredAt Edge
            loc_edge = OccurredAt(
                source_id=event.id,
                target_id=location.id,
                timestamp=event.timestamp
            )
            await asyncio.shield(self.repository.create_edge(loc_edge))

        return event

    async def _calculate_intent(self, agent_a, agent_b) -> IntentType:
        """
        Determines the ephemeral intent based on existing affinity.
        """
        affinity_edge = await self.repository.get_agent_affinity(agent_a.id, agent_b.id)
        affinity = affinity_edge.affinity

        # Weighted Probability based on Affinity
        # Low Affinity -> High conflict chance
        # High Affinity -> High support chance

        roll = random.random()

        if affinity < 30.0:
            if roll < 0.6: return IntentType.CONFLICT
            if roll < 0.9: return IntentType.AVOID
            return IntentType.GOSSIP # Bad mouthing?
        elif affinity > 70.0:
            if roll < 0.7: return IntentType.SUPPORT
            if roll < 0.9: return IntentType.GOSSIP
            return IntentType.CONFLICT # Lovers quarrel?
        else:
            # Neutral
            if roll < 0.4: return IntentType.GOSSIP
            if roll < 0.7: return IntentType.SUPPORT
            if roll < 0.9: return IntentType.AVOID
            return IntentType.CONFLICT

    def _resolve_outcome(self, intent: IntentType):
        """Returns (Outcome, ValenceDelta, SummaryTemplate)"""
        possibilities = self.outcome_matrix.get(intent)
        if not possibilities:
            return None

        roll = random.random()
        for threshold, outcome, delta, template in possibilities:
            if roll <= threshold:
                return outcome, delta, template

        # Fallback to last
        return possibilities[-1][1:]

    async def _get_random_location(self) -> LocationNode:
        """Fetches a random location or creates one if none exist."""
        locations = []
        if hasattr(self.repository, 'get_all_locations'):
            locations = await self.repository.get_all_locations()

        if locations:
            return random.choice(locations)

        # Create default locations if empty
        name, ltype, desc = random.choice(self.default_locations)
        if hasattr(self.repository, 'get_or_create_location'):
            # 🏰 BASTION SHIELD: Protect location creation
            return await asyncio.shield(self.repository.get_or_create_location(name, ltype, desc))

        return LocationNode(name="The Void", description="Unknown space", type="void")

    async def _apply_affinity_shift(self, agent_a: str, agent_b: str, delta: float):
        """Updates Agent-to-Agent affinity."""
        if delta != 0.0:
            if hasattr(self.repository, 'update_agent_affinity'):
                # 🏰 BASTION SHIELD: Protect affinity updates (bi-directional)
                await asyncio.shield(self.repository.update_agent_affinity(agent_a, agent_b, delta))
                await asyncio.shield(self.repository.update_agent_affinity(agent_b, agent_a, delta))

# Singleton Instance (Initialized in main.py)
time_skip_service = None
