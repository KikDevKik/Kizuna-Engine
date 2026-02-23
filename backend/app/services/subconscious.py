import asyncio
import logging
import json
import os
import httpx
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

                    # Analyze (Real or Mock)
                    # Parallel Execution: Sentiment Analysis + Semantic Memory Retrieval
                    sentiment_task = asyncio.create_task(self._analyze_sentiment(full_text, agent_id))
                    memory_task = None
                    if self.repository:
                        memory_task = asyncio.create_task(
                            self.repository.get_relevant_episodes(user_id, query=full_text, limit=1)
                        )

                    hint = await sentiment_task
                    episodes = []
                    try:
                        if memory_task:
                            episodes = await memory_task
                    except Exception as e:
                        logger.error(f"Memory retrieval failed: {e}")

                    # --- 1. Memory Injection (The Semantic Bridge) ---
                    if episodes:
                        # We found a relevant memory from the past
                        episode = episodes[0]
                        whisper = (
                            f"SYSTEM_HINT: 🧠 [Flashback]: The user's current topic relates to a past memory: "
                            f"{episode.summary}. Use this context naturally."
                        )
                        logger.info(f"🧠 Memory Retrieved: {episode.summary}")
                        await injection_queue.put({
                            "text": whisper,
                            "turn_complete": False
                        })

                    # --- 2. Sentiment Insight ---
                    if hint:
                        logger.info(f"🧠 Insight detected: {hint}")

                        # Inject Context
                        payload = {
                            "text": f"SYSTEM_HINT: {hint}",
                            "turn_complete": False
                        }
                        await injection_queue.put(payload)

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

                    # Clear buffer if ANY insight was found to avoid repetition
                    if hint or episodes:
                        self.buffer = []

                    # Keep buffer manageable
                    if len(self.buffer) > 20:
                        self.buffer.pop(0)
                except Exception:
                    logger.exception("🧠 Subconscious Mind iteration error. Recovering...")
                    await asyncio.sleep(1) # Small delay to avoid error storm

        except asyncio.CancelledError:
            pass
        finally:
            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
            logger.info("🧠 Subconscious Mind deactivated.")

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
                hint = f"SYSTEM_HINT: User's Heart Rate is HIGH ({bpm} BPM). They might be stressed or excited. Check tone."
                await queue.put({"text": hint, "turn_complete": False})
                logger.info(f"❤️ Bio-Signal Injected: {hint}")
            elif bpm < 55:
                 hint = f"SYSTEM_HINT: User's Heart Rate is LOW ({bpm} BPM). They are very calm or possibly tired."
                 await queue.put({"text": hint, "turn_complete": False})
                 logger.info(f"💙 Bio-Signal Injected: {hint}")

    async def _analyze_sentiment(self, text: str, agent_id: str = None) -> str | None:
        """
        Analyzes text for emotional cues.
        Uses Real Gemini Flash if configured, otherwise falls back to keyword matching via Archetypes/Traits.
        """
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
                prompt_template = "Analyze the user's emotional state from this transcript: '{text}'. Return a concise System Hint (max 15 words) starting with 'SYSTEM_HINT:'. If neutral, return nothing."

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
                        response = await self.client.aio.models.generate_content(
                            model=model,
                            contents=text,
                            config=types.GenerateContentConfig(
                                system_instruction=types.Content(
                                    parts=[types.Part(text=system_instruction)]
                                )
                            )
                        )
                        break # Success
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
                    logger.warning("Subconscious inference yielded no text/invalid response")
                    return None

                else:
                    result = response.text.strip()
                    if "SYSTEM_HINT:" in result:
                        return result.replace("SYSTEM_HINT:", "").strip()
                    return None

            except Exception as e:
                logger.warning("Subconscious inference failed (Global). Fallback to keywords.", exc_info=True)

        # 2. Fallback (Keyword Matching via Archetypes -> Traits -> System Config)
        triggers = {}

        if agent_id and self.repository:
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

        text_lower = text.lower()
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
                    "CRITICAL: You MUST retain all specific proper nouns, technical terms, names of songs, media, or projects mentioned by the user. Never generalize specific entities. Act as a precise archivist.\n\n"
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
                        response = await self.client.aio.models.generate_content(
                            model=model, # Or SUBCONSCIOUS if DREAM model not defined
                            contents=summary_text,
                            config=types.GenerateContentConfig(
                                system_instruction=types.Content(
                                    parts=[types.Part(text=system_instruction)]
                                )
                            )
                        )
                        break
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
