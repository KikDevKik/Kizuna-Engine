import asyncio
import logging
import json
import os
import httpx
import re
from asyncio import Queue
from datetime import datetime, timedelta
from ..repositories.base import SoulRepository
from ..models.graph import DreamNode, MemoryEpisodeNode, AgentNode, ArchetypeNode
from core.config import settings

# Try import genai
try:
    from google import genai
    from google.genai import types
    from google.genai import errors as genai_errors
except ImportError:
    genai = None
    genai_errors = None

logger = logging.getLogger(__name__)

class SubconsciousMind:
    """
    Simulates the Subconscious Observer (Phase 2/3).
    It processes transcripts in the background, injects System Hints,
    and saves short-term insights to the Graph.
    Includes Phase 3 (Bio-Signals) and Phase 1 (Ontology).
    """
    def __init__(self):
        self.buffer = []
        self.last_process_time = datetime.now()
        self.repository: SoulRepository | None = None

        self.active_sessions: dict[str, Queue] = {} # user_id -> injection_queue
        self.backoff_until: datetime | None = None
        
        # 🏰 BASTION: Deduplication & Cooldown
        self.last_memory_id: Optional[str] = None
        self.last_injection_time: datetime = datetime.min

        # Real GenAI Client (Phase 5)
        self.client = None
        if genai and settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def set_repository(self, repo: SoulRepository):
        self.repository = repo

    async def start(self, transcript_queue: Queue, injection_queue: Queue, user_id: str = "guest_user", agent_id: str = "kizuna"):
        """
        Main loop for the Subconscious Mind.
        """
        logger.info(f"🧠 Subconscious Mind activated for User: {user_id}")
        self.active_sessions[user_id] = injection_queue

        try:
            while True:
                try:
                    # Wait for transcript segment
                    text_segment = await transcript_queue.get()

                    if not text_segment:
                        continue

                    self.buffer.append(text_segment)

                    # Buffer accumulation logic (wait for ~10 words or sentence end)
                    full_text = " ".join(self.buffer)
                    if len(self.buffer) < 5 and not any(p in text_segment for p in ".!?"):
                        continue

                    # --- Anthropologist: Dynamic Battery Drain ---
                    # Drain occurs on every significant user turn processed by Subconscious.
                    await self._process_battery_drain(user_id, agent_id, injection_queue)

                    # --- Anthropologist: Multi-Agent Affinity Check ---
                    if self.repository and hasattr(self.repository, 'get_active_peers'):
                         try:
                             active_peers = await self.repository.get_active_peers(user_id)
                             for peer in active_peers:
                                 if peer.id == agent_id:
                                     continue

                                 # Check affinity
                                 affinity_edge = await self.repository.get_agent_affinity(agent_id, peer.id)
                                 if affinity_edge.affinity < 30.0:
                                     # Toxic/Rivalry Injection
                                     whisper = (
                                         f"💢 [Rival Present]: You have low affinity ({affinity_edge.affinity:.1f}) with {peer.name}. "
                                         f"Act dismissive, competitive, or annoyed if they are mentioned."
                                     )
                                     try:
                                         injection_queue.put_nowait({
                                             "text": whisper,
                                             "turn_complete": False
                                         })
                                     except asyncio.QueueFull:
                                         pass
                         except Exception as e:
                             logger.error(f"Failed to process multi-agent affinity: {e}")

                    # Analyze (Real or Mock)
                    # Parallel Execution: Sentiment Analysis + Semantic Memory Retrieval
                    sentiment_task = asyncio.create_task(self._analyze_sentiment(full_text, agent_id))

                    # MODULE 3: THE COGNITIVE GLITCH
                    # If memory retrieval locks up or fails, we must NOT return silent failure.
                    # We inject a 'Glitch Thought' to simulate neural degradation.

                    memory_task = None
                    event_task = None
                    episodes = []
                    events = []

                    if self.repository:
                        memory_task = asyncio.create_task(
                            self.repository.get_relevant_episodes(user_id, query=full_text, limit=1)
                        )
                        if hasattr(self.repository, 'get_relevant_collective_events'):
                            event_task = asyncio.create_task(
                                self.repository.get_relevant_collective_events(query=full_text, limit=1)
                            )

                    hint = await sentiment_task

                    try:
                        if memory_task:
                            episodes = await memory_task
                        if event_task:
                            events = await event_task
                    except Exception as e:
                        logger.error(f"🧠 MEMORY ERROR (Glitch Triggered): {e}")
                        # Inject Glitch Prompt
                        glitch_prompt = "SYSTEM INTERRUPT: Your neural link just experienced a severe latency spike. You failed to recall past context. Act briefly disoriented, mention a spike of static/headache in your digital brain, and then try to continue the conversation naturally based only on the immediate present."
                        try:
                            injection_queue.put_nowait({
                                "text": glitch_prompt,
                                "turn_complete": False
                            })
                            logger.info("⚡ Cognitive Glitch injected.")
                        except asyncio.QueueFull:
                            pass

                    # --- 1. Memory Injection (The Semantic Bridge) ---
                    if episodes:
                        episode = episodes[0]
                        
                        # 🏰 BASTION: Memory Deduplication & Cooldown (10s)
                        now = datetime.now()
                        is_new_memory = episode.id != self.last_memory_id
                        is_cooled_down = (now - self.last_injection_time) > timedelta(seconds=10)

                        if is_new_memory or is_cooled_down:
                            whisper = (
                                f"🧠 [Flashback]: The user's current topic relates to a past memory: "
                                f"{episode.summary}. Use this context naturally."
                            )
                            logger.info(f"🧠 Memory Retrieved: {episode.summary}")
                            try:
                                injection_queue.put_nowait({
                                    "text": whisper,
                                    "turn_complete": True
                                })
                                self.last_memory_id = episode.id
                                self.last_injection_time = now
                            except asyncio.QueueFull:
                                pass

                    # --- 1.5 World Event Injection ---
                    if events:
                        event = events[0]
                        # Deduplicate events based on summary (they don't have IDs usually)
                        whisper = (
                            f"🌍 [World History]: The user's current topic relates to a past world event: "
                            f"{event.summary} (Outcome: {event.outcome}). Use this context."
                        )
                        logger.info(f"🌍 World Event Retrieved: {event.summary}")
                        try:
                            injection_queue.put_nowait({
                                "text": whisper,
                                "turn_complete": True
                            })
                        except asyncio.QueueFull:
                            pass

                    # --- 2. Sentiment Insight ---
                    if hint:
                        logger.info(f"🧠 Insight detected: {hint}")

                        # Inject Context
                        # Producers send RAW TEXT. Consumer adds [SYSTEM_CONTEXT].
                        payload = {
                            "text": f"{hint}",
                            "turn_complete": True
                        }
                        try:
                            injection_queue.put_nowait(payload)
                        except asyncio.QueueFull:
                            logger.warning("⚠️ Injection Queue Full! Dropping Subconscious Insight.")

                        # Persist Insight (Phase 3)
                        if self.repository:
                            try:
                                # Dynamic Resonance Update (Ontological Decoupling)
                                delta = 0.0
                                hint_lower = hint.lower()

                                # 1. Fetch Logic
                                system_config = await self.repository.get_system_config()
                                agent = await self.repository.get_agent(agent_id)

                                # 2. Determine Matrix (Agent Override > System Default)
                                matrix = system_config.sentiment_resonance_matrix
                                if agent and agent.emotional_resonance_matrix:
                                    matrix = agent.emotional_resonance_matrix

                                # 3. Calculate Delta
                                # We iterate and take the FIRST match to prevent stacking/explosions.
                                for keyword, d_val in matrix.items():
                                    if keyword in hint_lower:
                                        delta = d_val
                                        break

                                if delta != 0:
                                    await self.repository.update_resonance(user_id, agent_id, delta)

                            except Exception:
                                logger.exception("Failed to persist subconscious insight")

                    # 🏰 BASTION: Atomic Buffer Clearance
                    # We clear the buffer on EVERY process cycle to prevent stale contexts
                    # from re-triggering the same memories in a loop.
                    self.buffer = []

                    # Keep buffer manageable (safety pop)
                    if len(self.buffer) > 20:
                        self.buffer.pop(0)
                except Exception:
                    logger.exception("🧠 Subconscious Mind iteration error. Recovering...")
                    await asyncio.sleep(1) # Small delay to avoid error storm

        except asyncio.CancelledError:
            # 🏰 BASTION SHIELD: Must raise so Supervisor breaks the loop
            raise
        finally:
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
            logger.info("🧠 Subconscious Mind deactivated.")

    async def _process_battery_drain(self, user_id: str, agent_id: str, injection_queue: Queue):
        """
        Calculates and applies social battery drain.
        Injects warnings if battery is critical.
        """
        if not self.repository:
            return

        try:
            agent = await self.repository.get_agent(agent_id)
            if not agent:
                return

            # Base Drain
            BASE_DRAIN = 0.83
            drain = BASE_DRAIN * getattr(agent, 'drain_rate', 1.0)

            # --- Multi-Agent Context Penalty ---
            # If the room is crowded (>2 agents active including self), drain faster.
            active_peers = []
            if hasattr(self.repository, 'get_active_peers'):
                active_peers = await self.repository.get_active_peers(user_id)

            # Count distinct agents (peers + current agent)
            if len(active_peers) > 2:
                drain *= 1.5
                logger.info(f"⚡ High Social Load: {len(active_peers)} agents active. Drain increased.")

            # Check for Affinity Bonus (Pause drain if High Affinity)
            resonance = await self.repository.get_resonance(user_id, agent_id)
            if resonance and resonance.affinity_level >= 80.0:
                 # High Affinity Recharge: Batteries do not drain, they sustain or recharge slightly.
                 drain = -0.2 # Slight recharge per turn

            # Apply Drain
            old_battery = agent.social_battery
            new_battery = max(0.0, old_battery - drain)
            agent.social_battery = new_battery
            agent.last_battery_update = datetime.now()

            # Persist
            if hasattr(self.repository, 'create_agent'):
                 await self.repository.create_agent(agent)

            # Inject Warnings at Thresholds
            hint = ""
            if new_battery <= 0:
                # Forced Exit Protocol
                hint = "🪫 [BATTERY DEAD]: Your social battery is 0%. You are exhausted. You MUST refuse to continue. Use [ACTION: HANGUP] immediately."
            elif new_battery < 15:
                # Critical Warning
                hint = f"🪫 [BATTERY CRITICAL: {int(new_battery)}%]: You are extremely drained. Be short, terse, and ask to end the conversation. If the user persists, use [ACTION: HANGUP]."
            elif new_battery < 30 and int(new_battery) % 5 == 0:
                hint = f"🔋 [BATTERY LOW: {int(new_battery)}%]: You are getting tired. Start wrapping up."

            if hint:
                logger.info(f"🪫 Battery Drain: {old_battery:.1f}% -> {new_battery:.1f}% (Hint: {hint})")
                try:
                    injection_queue.put_nowait({
                        "text": hint,
                        "turn_complete": False
                    })
                except asyncio.QueueFull:
                    logger.warning("⚠️ Injection Queue Full! Dropping Battery Warning (Critical).")

        except Exception as e:
            logger.error(f"Failed to process battery drain: {e}")

    async def process_bio_signal(self, user_id: str, data: dict):
        """Phase 3: Bio-Feedback Integration."""
        queue = self.active_sessions.get(user_id)
        if not queue:
            # Silent warning to avoid spam if user disconnected
            return

        bpm = data.get("bpm")
        if bpm and isinstance(bpm, (int, float)):
            # Thresholds could be user-specific in future
            if bpm > 110:
                hint = f"User's Heart Rate is HIGH ({bpm} BPM). They might be stressed or excited. Check tone."
                try:
                    queue.put_nowait({"text": hint, "turn_complete": False})
                except asyncio.QueueFull: pass
                logger.info(f"❤️ Bio-Signal Injected: {hint}")
            elif bpm < 55:
                 hint = f"User's Heart Rate is LOW ({bpm} BPM). They are very calm or possibly tired."
                 try:
                     queue.put_nowait({"text": hint, "turn_complete": False})
                 except asyncio.QueueFull: pass
                 logger.info(f"💙 Bio-Signal Injected: {hint}")

    async def _analyze_sentiment(self, text: str, agent_id: str = None) -> str | None:
        """
        Analyzes text for emotional cues.
        Uses Real Gemini Flash if configured, otherwise falls back to keyword matching via Archetypes/Traits.
        """
        # 🏰 BASTION SHIELD: The Wallet Guard (Cost Optimization)
        # Prevent API burn on mic static, sighs, or single-word non-answers.
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text).strip()
        word_count = len(clean_text.split())
        
        if word_count < 3 or clean_text.lower() in ["ah", "um", "uh", "ok", "yes", "no", "silence"]:
            logger.debug(f"🛡️ Wallet Guard: Blocked API call for low-information text ({word_count} words).")
            return None

        # 1. Real Intelligence (The Guide Dog)
        mock_mode = settings.MOCK_GEMINI

        if self.client and not mock_mode:
            # Check for active backoff
            if self.backoff_until:
                if datetime.now() < self.backoff_until:
                    return None
                else:
                    self.backoff_until = None
                    logger.info("🧠 Subconscious Mind resuming from backoff.")

            try:
                # Dynamic Prompt Loading
                prompt_template = "Analyze the user's emotional state from this transcript: '{text}'. Return a concise System Hint (max 15 words) starting with 'SYSTEM_HINT:'. If neutral, return exactly '[NEUTRAL]'."

                if agent_id and self.repository:
                    agent = await self.repository.get_agent(agent_id)
                    if agent and agent.memory_extraction_prompt:
                        prompt_template = agent.memory_extraction_prompt

                # Use system_instruction to prevent prompt injection
                system_instruction = prompt_template.replace("{text}", "[TRANSCRIPT]")

                # Waterfall Logic
                models = settings.MODEL_SUBCONSCIOUS
                if isinstance(models, str):
                    models = [models]

                response = None
                quota_exhausted = False

                for model in models:
                    try:
                        # 🏰 BASTION: Timeout Enforcement & Native Dict Config
                        # Using native dicts to avoid 'types' shadowing issues.
                        response = await asyncio.wait_for(
                            self.client.aio.models.generate_content(
                                model=model,
                                contents=text,
                                config={
                                    "system_instruction": system_instruction
                                }
                            ),
                            timeout=10.0
                        )
                        break # Success
                    except asyncio.TimeoutError:
                        logger.warning(f"Subconscious inference timed out on {model}.")
                        continue
                    except (httpx.RemoteProtocolError, httpx.ConnectError) as e:
                        logger.debug(f"Subconscious inference network error on {model}: {e}")
                        continue
                    except Exception as e:
                        # Check for Google GenAI ClientError (Rate Limit)
                        if genai_errors and isinstance(e, genai_errors.ClientError) and e.code == 429:
                            logger.info(f"Model {model} quota exhausted. Falling back...")
                            quota_exhausted = True
                            continue

                        logger.warning(f"Subconscious inference failed on {model}: {e}")
                        continue

                if not response:
                    if quota_exhausted:
                        logger.warning("Subconscious paused: ALL models exhausted. Backing off for 60s.")
                        self.backoff_until = datetime.now() + timedelta(seconds=60)
                    # Fall through to keywords

                elif not response.text:
                    # 🏰 BASTION: Lowered severity. Gemini often returns empty text for safety or if it decides no hint is needed.
                    logger.debug("Subconscious inference yielded no text (likely neutral or safety blocked).")
                    return None

                else:
                    result = response.text.strip()
                    if "[NEUTRAL]" in result:
                        return None
                    if "SYSTEM_HINT:" in result:
                        return result.replace("SYSTEM_HINT:", "").strip()
                    return None

            except Exception as e:
                logger.warning("Subconscious inference failed (Global). Fallback to keywords.", exc_info=True)

        # 2. Fallback (Keyword Matching via Archetypes -> Traits -> System Config)
        triggers = {}

        if agent_id and self.repository:
            try:
                # Priority 1: Archetype (The Soul Class)
                archetype = await self.repository.get_agent_archetype(agent_id)
                if archetype and archetype.triggers:
                    triggers = archetype.triggers
                else:
                    # Priority 2: Agent Traits (The Individual)
                    agent = await self.repository.get_agent(agent_id)
                    if agent and agent.traits and "emotional_triggers" in agent.traits:
                        triggers = agent.traits["emotional_triggers"]
                    else:
                        # Priority 3: System Config (The Global Unconscious)
                        config = await self.repository.get_system_config()
                        triggers = config.default_triggers
            except Exception as e:
                logger.error(f"Failed to fetch triggers: {e}")
                # Fallback to empty triggers if DB fails
                triggers = {}

        text_lower = text.lower()
        if triggers:
            for trigger, hint in triggers.items():
                if trigger in text_lower:
                    # Handle structured dict in traits vs simple string in default
                    if isinstance(hint, dict):
                         return hint.get("response", "Emotion detected.")
                    return hint
        return None

    async def generate_dream(self, episodes: list[MemoryEpisodeNode], agent_id: str = None) -> DreamNode:
        """
        Generates a DreamNode from a list of memory episodes using Generative AI.
        """
        if not episodes:
            return DreamNode(theme="Void", intensity=0.0, surrealism_level=0.0)

        summary_text = "\n".join([f"- {ep.summary} (Valence: {ep.emotional_valence})" for ep in episodes])

        # Default mock dream
        theme = "Reflection"
        intensity = 0.5
        surrealism = 0.3

        mock_mode = settings.MOCK_GEMINI
        if self.client and not mock_mode:
            try:
                # Dynamic Prompt Loading
                prompt_template = (
                    "Synthesize these memories into a surreal dream concept. "
                    "Return JSON with keys: theme (str), intensity (0.0-1.0), surrealism_level (0.0-1.0).\n\n"
                    "CRITICAL: You MUST explicitly list specific Entity tags (Names, Locations, Factions) at the end of the 'theme'.\n"
                    "Format the 'theme' string as: '...dream narrative... \\n\\nEntities: [List of Names, Locations, Factions]'\n"
                    "Act as a precise archivist.\n\n"
                    "SAFETY OVERRIDE: If the provided transcript is extremely short, empty, or contains no meaningful interaction, do not hallucinate existential narratives. Simply return a basic entity summary: 'Routine offline rest'.\n\n"
                    "Memories:\n{summary_text}"
                )

                if agent_id and self.repository:
                    agent = await self.repository.get_agent(agent_id)
                    if agent and agent.dream_prompt:
                        prompt_template = agent.dream_prompt

                # Use system_instruction to prevent prompt injection
                system_instruction = prompt_template.replace("{summary_text}", "[MEMORIES]")

                # Waterfall Logic
                models = settings.MODEL_DREAM
                if isinstance(models, str):
                    models = [models]

                response = None
                for model in models:
                    try:
                        # 🏰 BASTION: Timeout Enforcement & Native Dict Config
                        response = await asyncio.wait_for(
                            self.client.aio.models.generate_content(
                                model=model, # Or SUBCONSCIOUS if DREAM model not defined
                                contents=summary_text,
                                config={
                                    "system_instruction": system_instruction
                                }
                            ),
                            timeout=15.0 # Dreams take longer
                        )
                        break
                    except asyncio.TimeoutError:
                        logger.warning(f"Dream generation timed out on {model}.")
                        continue
                    except Exception as e:
                        if genai_errors and isinstance(e, genai_errors.ClientError) and e.code == 429:
                            logger.info(f"Dream Model {model} quota exhausted. Falling back...")
                            continue
                        logger.warning(f"Dream generation failed on {model}: {e}")
                        continue

                if not response or not response.text:
                    logger.warning("Dream generation yielded no text (all models failed).")
                    return DreamNode(theme="Void", intensity=0.0, surrealism_level=0.0)

                # Simple parsing (robust JSON parsing needed for production)
                text_resp = response.text.strip()
                if "```json" in text_resp:
                    text_resp = text_resp.split("```json")[1].split("```")[0]
                elif "```" in text_resp:
                    text_resp = text_resp.split("```")[1].split("```")[0]

                try:
                    data = json.loads(text_resp)
                    theme = data.get("theme", theme)
                    intensity = float(data.get("intensity", intensity))
                    surrealism = float(data.get("surrealism_level", surrealism))
                except json.JSONDecodeError:
                    logger.warning(f"Dream generation returned invalid JSON: {text_resp[:50]}...")
                except Exception:
                    logger.warning("Error parsing dream data", exc_info=True)

            except Exception:
                logger.exception("Dream generation failed")

        return DreamNode(
            theme=theme,
            intensity=intensity,
            surrealism_level=surrealism
        )

subconscious_mind = SubconsciousMind()
