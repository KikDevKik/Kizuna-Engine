import asyncio
import logging
import json
import os
from asyncio import Queue
from datetime import datetime
from ..repositories.base import SoulRepository
from ..models.graph import DreamNode, MemoryEpisodeNode, AgentNode
from core.config import settings

# Try import genai
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class SubconsciousMind:
    """
    Simulates the Subconscious Observer (Phase 2/3).
    It processes transcripts in the background, injects System Hints,
    and saves short-term insights to the Graph.
    """
    def __init__(self):
        self.buffer = []
        self.last_process_time = datetime.now()
        self.repository: SoulRepository | None = None

        # Default fallback if agent traits are missing
        self.default_triggers = {
            "sad": "The user seems down. Be extra gentle and supportive.",
            "angry": "The user is frustrated. Apologize and de-escalate calmly.",
            "happy": " The user is excited! Match their energy.",
            "tired": "The user is tired. Keep responses short and soothing."
        }

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
        try:
            while True:
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
                hint = await self._analyze_sentiment(full_text, agent_id)

                if hint:
                    logger.info(f"🧠 Insight detected: {hint}")

                    # 1. Inject Context
                    payload = {
                        "text": f"SYSTEM_HINT: {hint}",
                        "turn_complete": False
                    }
                    await injection_queue.put(payload)

                    # 2. Persist Insight (Phase 3)
                    if self.repository:
                        try:
                            # Dynamic Resonance Update
                            delta = 0
                            trigger_word = "Emotion"

                            # Simple heuristic for now, but could be trait-driven later
                            hint_lower = hint.lower()
                            if "happy" in hint_lower or "excited" in hint_lower:
                                delta = 1
                                trigger_word = "Positivity"
                            elif "angry" in hint_lower:
                                delta = 0 # No penalty, just neutral/handling
                                trigger_word = "Conflict"
                            elif "sad" in hint_lower:
                                delta = 1 # Comforting is bonding
                                trigger_word = "Vulnerability"

                            if delta != 0:
                                await self.repository.update_resonance(user_id, agent_id, delta)

                            # Save Episode
                            await self.repository.save_episode(
                                user_id=user_id,
                                agent_id=agent_id,
                                summary=f"User triggered insight: {trigger_word} -> {hint}",
                                valence=0.5
                            )
                        except Exception as e:
                            logger.error(f"Failed to persist subconscious insight: {e}")

                    # Clear buffer after successful insight to avoid repetition
                    self.buffer = []

                # Keep buffer manageable
                if len(self.buffer) > 20:
                    self.buffer.pop(0)

        except asyncio.CancelledError:
            logger.info("🧠 Subconscious Mind deactivated.")
            raise
        except Exception as e:
            logger.error(f"🧠 Subconscious Error: {e}")
            # Don't crash the whole app, just log
            pass

    async def _analyze_sentiment(self, text: str, agent_id: str = None) -> str | None:
        """
        Analyzes text for emotional cues.
        Uses Real Gemini Flash if configured, otherwise falls back to keyword matching.
        """
        # 1. Real Intelligence (The Guide Dog)
        mock_mode = os.getenv("MOCK_GEMINI", "false").lower() == "true"

        if self.client and not mock_mode:
            try:
                # Run in executor to avoid blocking loop if sync
                # SDK 0.x is sync, 1.x has aio? client.aio.models...
                # Assuming unified SDK supports async or we wrap it.
                # For safety, let's wrap the generate call.

                # Dynamic Prompt Loading
                prompt_template = "Analyze the user's emotional state from this transcript: '{text}'. Return a concise System Hint (max 15 words) starting with 'SYSTEM_HINT:'. If neutral, return nothing."

                if agent_id and self.repository:
                    agent = await self.repository.get_agent(agent_id)
                    if agent and agent.memory_extraction_prompt:
                        prompt_template = agent.memory_extraction_prompt

                prompt = prompt_template.replace("{text}", text)

                # Using 2.0 Flash Exp or configured model
                response = await self.client.aio.models.generate_content(
                    model=settings.MODEL_SUBCONSCIOUS,
                    contents=prompt
                )

                if not response.text:
                    logger.warning("Subconscious inference yielded no text/invalid response")
                    return None

                result = response.text.strip()
                if "SYSTEM_HINT:" in result:
                    return result.replace("SYSTEM_HINT:", "").strip()
                return None

            except Exception as e:
                logger.warning(f"Subconscious inference failed: {e}. Fallback to keywords.")

        # 2. Fallback (Keyword Matching via Traits)
        triggers = self.default_triggers
        if agent_id and self.repository:
            agent = await self.repository.get_agent(agent_id)
            if agent and agent.traits and "emotional_triggers" in agent.traits:
                triggers = agent.traits["emotional_triggers"]

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

        mock_mode = os.getenv("MOCK_GEMINI", "false").lower() == "true"
        if self.client and not mock_mode:
            try:
                # Dynamic Prompt Loading
                prompt_template = (
                    "Synthesize these memories into a surreal dream concept. "
                    "Return JSON with keys: theme (str), intensity (0.0-1.0), surrealism_level (0.0-1.0).\n\n"
                    "Memories:\n{summary_text}"
                )

                if agent_id and self.repository:
                    agent = await self.repository.get_agent(agent_id)
                    if agent and agent.dream_prompt:
                        prompt_template = agent.dream_prompt

                prompt = prompt_template.replace("{summary_text}", summary_text)

                response = await self.client.aio.models.generate_content(
                    model=settings.MODEL_DREAM, # Or SUBCONSCIOUS if DREAM model not defined
                    contents=prompt
                )

                if not response.text:
                    logger.warning("Dream generation yielded no text.")
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
                except Exception as e:
                    logger.warning(f"Error parsing dream data: {e}")

            except Exception as e:
                logger.error(f"Dream generation failed: {e}")

        return DreamNode(
            theme=theme,
            intensity=intensity,
            surrealism_level=surrealism
        )

subconscious_mind = SubconsciousMind()
