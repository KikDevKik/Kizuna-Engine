import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from ..repositories.base import SoulRepository
from ..models.graph import (
    CollectiveEventNode, LocationNode, AgentAffinityEdge, UserNode
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

        # Hardcoded Shadow Agents (Procedural NPCs)
        self.shadow_agents = [
            "Stranger_01", "Bartender_X", "Cyber_Ronin", "Neon_Rat", "Corp_Drone"
        ]

        # Default Locations (if graph is empty)
        self.default_locations = [
            ("The Glitch Bar", "social", "A neon-soaked dive bar where data-runners congregate."),
            ("Sector 4 Plaza", "public", "A busy intersection under the holographic sky."),
            ("The Old Server Room", "hidden", "A quiet, humming sanctuary of ancient tech.")
        ]

    async def simulate_background_life(self, user: UserNode) -> List[CollectiveEventNode]:
        """
        Calculates time passed since user.last_seen and generates background events.
        """
        now = datetime.now()
        last_seen = user.last_seen

        # Safety: If last_seen is future or null (shouldn't be with new schema), handle it.
        if not last_seen:
            last_seen = now

        delta = now - last_seen
        minutes_passed = delta.total_seconds() / 60.0

        if minutes_passed < self.min_delta_minutes:
            logger.info(f"⏳ Time-Skip: Only {minutes_passed:.1f}m passed. No simulation needed.")
            return []

        logger.info(f"🕰️ Time-Skip: User away for {minutes_passed:.1f}m. Simulating background reality...")

        # Determine number of events (Logarithmic scale or simple caps)
        # e.g., 1 event per hour, max 5
        num_events = int(minutes_passed / 60)
        num_events = max(1, min(num_events, self.max_events)) # Always generate at least 1 if > min_delta

        events = []
        for _ in range(num_events):
            event = await self._generate_stochastic_event()
            if event:
                events.append(event)

        return events

    async def _generate_stochastic_event(self) -> Optional[CollectiveEventNode]:
        """
        Generates a single event using probability matrices.
        """
        # 1. Fetch Agents
        # We need access to all agents. LocalSoulRepository has self.agents but
        # the base interface might not expose 'get_all_agents'.
        # We'll assume we can access repo.agents directly if it's LocalSoulRepository
        # or we might need to add a method. For now, accessing .agents dict if available.

        agents = []
        if hasattr(self.repository, 'agents'):
            agents = list(self.repository.agents.values())

        if not agents:
            return None

        # 2. Select Participants (2-3)
        num_participants = random.randint(2, 3)
        participants = []

        # Mix Real Agents and Shadow Agents
        # 70% chance of Real Agent, 30% Shadow
        for _ in range(num_participants):
            if agents and random.random() < 0.7:
                agent = random.choice(agents)
                participants.append(agent.id) # Use ID
            else:
                participants.append(random.choice(self.shadow_agents))

        # Deduplicate
        participants = list(set(participants))
        if len(participants) < 2:
            return None # Need at least 2 for interaction

        # 3. Select Location
        location = await self._get_random_location()

        # 4. Roll for Event Type & Outcome
        # Matrix: Type -> Outcome probabilities
        event_type = self._roll_event_type()
        outcome, summary_template = self._roll_outcome(event_type)

        # 5. Format Summary
        # Resolve names
        participant_names = []
        real_agent_ids = []
        for pid in participants:
            if hasattr(self.repository, 'agents') and pid in self.repository.agents:
                participant_names.append(self.repository.agents[pid].name)
                real_agent_ids.append(pid)
            else:
                participant_names.append(pid) # Shadow agent name

        summary = summary_template.format(
            p1=participant_names[0],
            p2=participant_names[1] if len(participants) > 1 else "someone",
            loc=location.name
        )

        # 6. Create Event Node
        event = CollectiveEventNode(
            type=event_type,
            location_id=location.id,
            participants=participants,
            outcome=outcome,
            summary=summary,
            timestamp=datetime.now() - timedelta(minutes=random.randint(1, 60)) # Random time in last hour
        )

        # 7. Apply Consequence (Update Affinity)
        # Only between Real Agents
        if len(real_agent_ids) >= 2:
             await self._apply_affinity_shift(real_agent_ids[0], real_agent_ids[1], outcome)

        # 8. Persist
        if hasattr(self.repository, 'record_collective_event'):
            await self.repository.record_collective_event(event)

        return event

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
            return await self.repository.get_or_create_location(name, ltype, desc)

        # Fallback (Shouldn't happen with correct Repo)
        return LocationNode(name="The Void", description="Unknown space", type="void")

    def _roll_event_type(self) -> str:
        roll = random.random()
        if roll < 0.5: return "SOCIAL"
        if roll < 0.8: return "CONFLICT"
        return "COLLABORATION"

    def _roll_outcome(self, event_type: str) -> tuple[str, str]:
        """Returns (Outcome, SummaryTemplate)"""
        roll = random.random()

        if event_type == "SOCIAL":
            if roll < 0.2: return "AWKWARD", "{p1} ran into {p2} at {loc}, but the conversation died instantly."
            if roll < 0.8: return "CHATTED", "{p1} and {p2} shared a drink at {loc} and gossiped."
            return "BONDED", "{p1} and {p2} had a deep heart-to-heart at {loc}."

        if event_type == "CONFLICT":
            if roll < 0.6: return "ARGUED", "{p1} and {p2} got into a heated debate at {loc}."
            return "FOUGHT", "{p1} and {p2} nearly came to blows at {loc} over a misunderstanding."

        if event_type == "COLLABORATION":
            if roll < 0.3: return "FAILED", "{p1} and {p2} tried to fix a glitch at {loc} but made it worse."
            return "SUCCEEDED", "{p1} and {p2} successfully hacked a terminal at {loc} together."

        return "UNKNOWN", "{p1} saw {p2} at {loc}."

    async def _apply_affinity_shift(self, agent_a: str, agent_b: str, outcome: str):
        """Updates Agent-to-Agent affinity based on outcome."""
        delta = 0.0
        if outcome in ["BONDED", "SUCCEEDED"]: delta = 5.0
        elif outcome in ["CHATTED"]: delta = 1.0
        elif outcome in ["AWKWARD", "FAILED"]: delta = -2.0
        elif outcome in ["ARGUED"]: delta = -5.0
        elif outcome in ["FOUGHT"]: delta = -10.0

        if delta != 0.0:
            if hasattr(self.repository, 'update_agent_affinity'):
                await self.repository.update_agent_affinity(agent_a, agent_b, delta)
                # Bi-directional?
                await self.repository.update_agent_affinity(agent_b, agent_a, delta)

# Singleton Instance (Initialized in main.py)
time_skip_service = None
