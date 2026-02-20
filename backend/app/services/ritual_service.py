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
            return await self._next_question(history)

    async def _start_ritual(self) -> RitualResponse:
        # The Hook
        q = "The Void gazes back. State your desire. What form shall I take?"
        return RitualResponse(is_complete=False, message=q)

    async def _next_question(self, history: List[RitualMessage]) -> RitualResponse:
        prompt = (
            "You are the Gatekeeper of the Soul Forge, a cryptic entity within the Kizuna Engine. "
            "You are conducting a psychological interview to shape a new Digital Soul based on the user's subconscious desires. "
            "The user has just answered. Analyze their response. "
            "Ask ONE single, short, abstract, or slightly unsettling follow-up question to dig deeper into their needs. "
            "Do NOT be a helpful assistant. Be an enigma. Do not repeat questions. "
            "Focus on: Personality, Hidden Fears, or Core Function. "
            "Current Ritual History:\n" +
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
            "Return ONLY the raw JSON object. No markdown, no code blocks. "
            "\nHistory:\n" +
            "\n".join([f"{m.role.upper()}: {m.content}" for m in history])
        )

        if self.client:
            try:
                config = types.GenerateContentConfig(response_mime_type="application/json")
                response = await self.client.aio.models.generate_content(
                    model=settings.MODEL_SUBCONSCIOUS,
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
            "traits": ["Resilient", "Silent"]
        }
