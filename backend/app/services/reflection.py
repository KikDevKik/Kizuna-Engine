import asyncio
import logging
import random
import httpx
from asyncio import Queue
from datetime import datetime
from core.config import settings
from ..models.graph import AgentNode
from ..repositories.base import SoulRepository

# Try import genai
try:
    from google import genai
    from google.genai import types
    from google.genai import errors as genai_errors
except ImportError:
    genai = None
    genai_errors = None

logger = logging.getLogger(__name__)

class ReflectionMind:
    """
    The Inner Critic (Self-Reflection Module).
    Analyzes the AI's own output to ensure persona consistency and quality.
    Operates as the Agent's internal monologue/conscience.
    """
    def __init__(self):
        self.repository: SoulRepository | None = None
        self.client = None
        if genai and settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def set_repository(self, repo: SoulRepository):
        self.repository = repo

    async def start(self, ai_transcript_queue: Queue, injection_queue: Queue, agent: AgentNode):
        """
        Main loop for the Reflection Mind.
        """
        logger.info(f"🪞 Reflection Mind activated for Agent: {agent.name}")

        # Fetch Throttling Config (Once per session startup to avoid IO in loop)
        base_chance = 0.2
        multiplier = 0.6
        if self.repository:
            try:
                config = await self.repository.get_system_config()
                base_chance = config.reflection_base_chance
                multiplier = config.reflection_neuroticism_multiplier
            except Exception as e:
                logger.warning(f"Failed to fetch SystemConfig for ReflectionMind: {e}")

        try:
            while True:
                try:
                    # Wait for AI's spoken text
                    text_segment = await ai_transcript_queue.get()

                    if not text_segment:
                        continue

                    # Throttling Logic (Trait-Based & Configurable)
                    # "neuroticism" (0.0 - 1.0): High = more reflection. Low = less.
                    # Default to 0.5 (Moderate) if missing.
                    neuroticism = agent.traits.get("neuroticism", 0.5)

                    reflection_chance = base_chance + (multiplier * neuroticism)

                    if random.random() > reflection_chance:
                        # Skip reflection this turn to save latency/tokens and avoid overthinking
                        continue

                    # Analyze (Real or Mock)
                    correction = await self._reflect(text_segment, agent)

                    if correction:
                        logger.info(f"🪞 Inner Voice: {correction}")

                        # Inject Correction
                        payload = {
                            "text": f"[{agent.name} Inner Voice]: {correction}",
                            "turn_complete": False
                        }
                        try:
                            injection_queue.put_nowait(payload)
                        except asyncio.QueueFull:
                            logger.warning("⚠️ Injection Queue Full! Dropping Reflection.")

                except Exception:
                    logger.exception("🪞 Reflection Mind iteration error. Recovering...")
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("🪞 Reflection Mind deactivated.")
            pass

    async def _reflect(self, text: str, agent: AgentNode) -> str | None:
        """
        Analyzes the text for persona drift using Gemini.
        """
        mock_mode = settings.MOCK_GEMINI

        if self.client and not mock_mode:
            try:
                # Dynamic Prompt Loading (Zero Hardcoding)
                prompt_template = agent.reflection_prompt
                # Fallback safety (should be covered by Pydantic default)
                if not prompt_template:
                     prompt_template = (
                        "You are the inner voice/conscience of {name}. Read your own recent spoken output below.\n"
                        "Based on your lore ({base_instruction}) and your personality traits ({traits}), are you staying true to yourself?\n"
                        "If you feel you are losing your 'vibe', give yourself a quick, in-character mental slap (max 10 words).\n"
                        "If you are acting naturally, return nothing."
                     )

                system_instruction = prompt_template.format(
                    name=agent.name,
                    base_instruction=agent.base_instruction,
                    traits=str(agent.traits)
                )

                # Waterfall Logic (Reuse Subconscious Model or dedicated one?)
                # User suggested gemini-3.0-flash or 2.5 fallback.
                # We'll use MODEL_SUBCONSCIOUS for now as it fits the "background thought" tier.
                models = settings.MODEL_SUBCONSCIOUS
                if isinstance(models, str):
                    models = [models]

                response = None

                for model in models:
                    try:
                        # 🏰 BASTION: Timeout Enforcement & Native Dict Config
                        response = await asyncio.wait_for(
                            self.client.aio.models.generate_content(
                                model=model,
                                contents=text,
                                config={
                                    "system_instruction": system_instruction
                                }
                            ),
                            timeout=10.0 # Reflection should be fast
                        )
                        break
                    except asyncio.TimeoutError:
                        logger.warning(f"Reflection inference timed out on {model}.")
                        continue
                    except (httpx.RemoteProtocolError, httpx.ConnectError) as e:
                        logger.debug(f"Reflection inference network error on {model}: {e}")
                        continue
                    except Exception as e:
                        if genai_errors and isinstance(e, genai_errors.ClientError) and e.code == 429:
                            continue
                        logger.warning(f"Reflection inference failed on {model}: {e}")
                        continue

                if response and response.text:
                    result = response.text.strip()
                    # Filter out empty or "Nothing" responses
                    if not result or result.lower() in ["nothing", "none", "no correction"]:
                        return None
                    return result

            except Exception as e:
                logger.warning("Reflection inference failed (Global).", exc_info=True)

        return None

reflection_mind = ReflectionMind()
