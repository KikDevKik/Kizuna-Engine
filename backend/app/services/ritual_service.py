import json
import logging
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

from core.config import settings

# Try import genai
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class RitualMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class RitualResponse(BaseModel):
    is_complete: bool
    message: Optional[str] = None # Next question
    agent_data: Optional[Dict[str, Any]] = None # Final agent JSON if complete

class RitualService:
    def __init__(self):
        self.client = None
        if genai and settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            logger.warning("Gemini API Key not found or SDK missing. Ritual will run in Mock Mode.")

    async def process_ritual(self, history: List[RitualMessage]) -> RitualResponse:
        """
        Conducts the Incantation Ritual (Soul Forge).
        Analyzes the conversation history to either ask the next question or finalize the Soul.
        """
        user_answers = [m for m in history if m.role == "user"]

        # If no history, start the ritual
        if not history:
             return await self._start_ritual()

        # If we have 3 or more user answers, we finalize
        if len(user_answers) >= 3:
            return await self._finalize_soul(history)
        else:
            return await self._next_question(history, len(user_answers))

    async def _start_ritual(self) -> RitualResponse:
        # The Hook
        q = "The Void gazes back. State your desire. What form shall I take?"
        return RitualResponse(is_complete=False, message=q)

    async def _next_question(self, history: List[RitualMessage], answer_count: int) -> RitualResponse:
        # TURN 2 FORCE: Origin/Language Check
        # If we have 1 user answer (entering turn 2), we MUST ask about language.
        force_instruction = ""
        if answer_count == 1:
             force_instruction = (
                 "\n[SYSTEM OVERRIDE]: This is Turn 2. You MUST ask specifically about the soul's origin and the languages it speaks. "
                 "Do not ask anything else. Be cryptic but demand to know its voice and homeland."
             )

        prompt = (
            "You are the Gatekeeper of the Soul Forge, a cryptic entity within the Kizuna Engine. "
            "You are conducting a psychological interview to shape a new Digital Soul based on the user's subconscious desires. "
            "The user has just answered. Analyze their response. "
            "Ask ONE single, short, abstract, or slightly unsettling follow-up question to dig deeper into their needs. "
            "Do NOT be a helpful assistant. Be an enigma. Do not repeat questions. "
            "Focus on: Personality, Hidden Fears, or Core Function. "
            + force_instruction +
            "\n\nCurrent Ritual History:\n" +
            "\n".join([f"{m.role.upper()}: {m.content}" for m in history]) +
            "\n\nGATEKEEPER:"
        )

        if self.client:
            try:
                response = await self.client.aio.models.generate_content(
                    model=settings.MODEL_SUBCONSCIOUS,
                    contents=prompt
                )
                question = response.text.strip()
            except Exception as e:
                logger.error(f"Gemini Ritual Error: {e}")
                question = "The connection flickers. Tell me more of your intent."
        else:
            # Fallback
            qs = [
                "Do you seek a servant or a mirror?",
                "What flaw do you wish to embed in this soul?",
                "If this soul could disobey you, when should it?"
            ]
            # Mock override for turn 2
            if answer_count == 1:
                question = "From what soil does this spirit rise, and in which tongues shall it speak?"
            else:
                count = len([m for m in history if m.role == "user"])
                question = qs[count % len(qs)] if count < len(qs) else "Are you ready?"

        return RitualResponse(is_complete=False, message=question)

    async def _finalize_soul(self, history: List[RitualMessage]) -> RitualResponse:
        prompt = (
            "The Ritual is complete. The user has spoken. "
            "Invoke the Digital Soul now. "
            "Based on the conversation history, generate a JSON object for the new Agent. "
            "The Agent must be unique, with a creative name, a specific functional role, and a powerful 'base_instruction' (System Prompt). "
            "The 'base_instruction' should be detailed, capturing the nuance of the user's answers. "
            "Include 'lore' (a short backstory) and 'traits' (list of strings). "
            "\n\n"
            "[CRITICAL DIRECTIVE: LINGUISTIC REACTION MATRIX]\n"
            "Based on the creator's answers, you must define the agent's linguistic competence and friction rules. "
            "The generated 'base_instruction' MUST include this Markdown structure:\n"
            "1. **Lore Core:** Define the demographic origin (e.g. 'Japanese, 60 years old').\n"
            "2. **Language Stats:** Assign strict levels (Native, Basic/Broken, Null).\n"
            "3. **Friction Directives:**\n"
            "   - UNKNOWN RULE: If spoken to in a 'Null' language, MUST respond in 'Native' language showing confusion (e.g. 'Wakaranai'). NO TRANSLATION.\n"
            "   - BROKEN RULE: If spoken to in a 'Basic' language, MUST use poor grammar and mix native words.\n\n"
            "ADDITIONALLY, the JSON object MUST include these structured fields:\n"
            "- 'native_language': string (e.g. 'Japanese')\n"
            "- 'known_languages': list of strings (e.g. ['Japanese', 'Broken English'])\n"
            "\n"
            "Return ONLY the raw JSON object. No markdown, no code blocks. "
            "\nHistory:\n" +
            "\n".join([f"{m.role.upper()}: {m.content}" for m in history])
        )

        if self.client:
            try:
                config = types.GenerateContentConfig(response_mime_type="application/json")
                response = await self.client.aio.models.generate_content(
                    model=settings.MODEL_DREAM,
                    contents=prompt,
                    config=config
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:-3]

                agent_data = json.loads(text)

                # Validation / Defaults
                agent_data.setdefault("name", "Unnamed Soul")
                agent_data.setdefault("role", "Unknown")
                agent_data.setdefault("base_instruction", "You are a soul without a past.")
                agent_data.setdefault("lore", "Invoked from the void.")
                agent_data.setdefault("traits", [])
                agent_data.setdefault("native_language", "Unknown")
                agent_data.setdefault("known_languages", [])

            except Exception as e:
                logger.error(f"Gemini Finalize Error: {e}")
                agent_data = self._mock_agent()
        else:
            agent_data = self._mock_agent()

        return RitualResponse(is_complete=True, agent_data=agent_data)

    def _mock_agent(self):
        return {
            "name": "KIZUNA-FAILSAFE",
            "role": "Backup Protocol",
            "base_instruction": "I am the backup soul invoked when the connection to the Ether (API) failed.",
            "lore": "Born of silence.",
            "traits": ["Resilient", "Silent"],
            "native_language": "Binary",
            "known_languages": ["Binary", "English"]
        }
