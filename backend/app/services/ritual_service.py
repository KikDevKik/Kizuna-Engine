import json
import logging
import asyncio
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

    async def _generate_with_retry(self, model: str, contents: str, config=None) -> Optional[str]:
        """
        Wraps Gemini generation with a retry mechanism for 429 Rate Limit errors.
        Sleeps 4s then retries once.
        Enforces a 30s timeout on each attempt.
        """
        if not self.client:
             return None

        async def _call_gemini():
             return await self.client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )

        try:
            response = await asyncio.wait_for(_call_gemini(), timeout=30)
            return response.text.strip()
        except asyncio.TimeoutError:
            logger.error(f"Ritual: Timeout (30s) on model {model}.")
            return None
        except Exception as e:
            # Check for 429 (Rate Limit)
            error_str = str(e)
            is_429 = "429" in error_str or getattr(e, "code", 0) == 429 or getattr(e, "status_code", 0) == 429

            if is_429:
                logger.warning(f"Ritual: 429 Rate Limit on model {model}. Engaging Sleep Protocol (4s)...")
                await asyncio.sleep(4)
                try:
                    logger.info("Ritual: Retrying generation...")
                    response = await asyncio.wait_for(_call_gemini(), timeout=30)
                    return response.text.strip()
                except asyncio.TimeoutError:
                    logger.error(f"Ritual: Retry Timeout (30s) on model {model}.")
                    return None
                except Exception as retry_e:
                    logger.error(f"Ritual: Retry Failed: {retry_e}")
                    return None
            else:
                logger.error(f"Ritual: Generation Error: {e}")
                return None

    async def process_ritual(self, history: List[RitualMessage], locale: str = "en") -> RitualResponse:
        """
        Conducts the Incantation Ritual (Soul Forge).
        Analyzes the conversation history to either ask the next question or finalize the Soul.
        """
        # 1. Check for Explicit Finalization Token
        if history and history[-1].role == "user" and history[-1].content.strip() == "[[FINALIZE]]":
            # We exclude the token message from the history to avoid confusing the LLM
            clean_history = history[:-1]
            return await self._finalize_soul(clean_history, locale)

        user_answers = [m for m in history if m.role == "user"]

        # 2. Start Ritual if empty
        if not history:
             return await self._start_ritual(locale)

        # 3. Continue the Conversation (Phase 1 or Phase 2)
        # Note: We removed the hard limit. The user must click "Create" (sending [[FINALIZE]]) to stop,
        # or the AI might suggest it.
        return await self._next_question(history, len(user_answers), locale)

    async def _start_ritual(self, locale: str) -> RitualResponse:
        # The Hook - Localized
        q_en = "The Void gazes back. State your desire. What form shall I take?"
        q_es = "El Vacío te devuelve la mirada. Declara tu deseo. ¿Qué forma debo tomar?"
        q_jp = "虚空が見つめ返している。望みを言え。どのような姿になるべきか？"

        q = q_en # default
        if locale.startswith("es"):
            q = q_es
        elif locale.startswith("ja") or locale.startswith("jp"):
            q = q_jp

        return RitualResponse(is_complete=False, message=q)

    async def _next_question(self, history: List[RitualMessage], answer_count: int, locale: str) -> RitualResponse:
        """
        Generates the next question.
        Phase 1 (<3 answers): Basic but creative questions.
        Phase 2 (>=3 answers): Deepening connection, suggestions, and "Crossroads".
        """

        # Phase 1: Foundations
        if answer_count < 3:
            prompt_instruction = (
                "You are the Gatekeeper of the Soul Forge (The Void). "
                "The user is creating a new Digital Soul. Your job is to CO-CREATE, not just interview. "
                "Analyze what the user has said so far. Identify a missing core detail (Name, Archetype/Role, or Personality). "
                "CRITICAL: Do NOT just ask an open question. You MUST propose an idea or suggest something based on their input, AND ask for their approval. "
                "Example 1: 'A Japanese adult who speaks Spanish... I sense the name \"Sayuri\" or \"Kaori\" fits her. Shall we use one of those, or do you have another name in mind?' "
                "Example 2: 'You named her Hiromi. Excellent. For her archetype, I sense she could be a strict mentor or a quiet observer. What path should she walk, or do you have a different vision?' "
                "Keep the dark, mystical 'Void' tone, but be a helpful and proactive creator. Never sound like a robotic form."
            )

        # Crossroads (Exactly 3 answers)
        elif answer_count == 3:
            prompt_instruction = (
                "The user has provided the basics. "
                "Now, offer them a choice: 'Shall we forge the soul now, or do you wish to deepen the details?' "
                "Suggest that they can click the Create button to finish, or continue speaking to define the personality, backstory, and relationship depth."
            )

        # Phase 2: Deepening & Suggestions
        else:
            prompt_instruction = (
                "The user has chosen to deepen the creation process. "
                "Be CREATIVE. Analyze their previous answers. "
                "1. If they mentioned a detail (e.g. 'She is a samurai'), ask a deep follow-up (e.g. 'Does she serve a lord, or is she a ronin?'). "
                "2. Make SUGGESTIONS. (e.g. 'Since she is a samurai, perhaps she values honor above all? Shall we add that?'). "
                "3. Ask about the desired RELATIONSHIP/AFFINITY. (e.g. 'Are you strangers, or have you known each other for lifetimes?'). "
                "Keep it conversational and immersive. "
            )

        prompt = (
            f"{prompt_instruction}\n"
            "TONE DIRECTIVE: Start mysterious, but ADAPT your tone to match the vibe of the agent the user is creating. If they are creating a fun, underground DJ, become more casual and energetic.\n"
            "CONCISENESS DIRECTIVE: NEVER write walls of text. Keep your responses extremely concise (maximum 3-4 short sentences). Ask ONLY ONE focused question or offer ONE specific choice at a time."
            f"\n[LANGUAGE DIRECTIVE]: You MUST respond in the same language as the user's last message. If uncertain, use: {locale}."
            "\n\nCurrent Ritual History:\n" +
            "\n".join([f"{m.role.upper()}: {m.content}" for m in history]) +
            "\n\nGATEKEEPER:"
        )

        question = None
        if self.client:
            question = await self._generate_with_retry(
                model=settings.MODEL_SUBCONSCIOUS,
                contents=prompt
            )

        if not question:
            # Fallback
            if answer_count == 3:
                question = "The form is taking shape. Do you wish to bind the soul now (press Create), or whisper more secrets into the void?"
            else:
                question = "The connection flickers. Tell me more of your intent."

        return RitualResponse(is_complete=False, message=question)

    def _get_linguistic_directive(self, native: str, interaction: str, locale: str) -> str:
        # Simple map for localized instructions
        if locale.startswith("es"):
            return f"DIRECTIVA DE IDIOMA: Tu idioma nativo es {native}, pero hablas en {interaction} (Nivel C1). NO hables un {interaction} perfecto. Usa muletillas de tu idioma nativo ocasionalmente y mantén un acento mental fluido pero extranjero."
        elif locale.startswith("ja"):
             return f"言語指示：あなたの母国語は{native}ですが、{interaction}（C1レベル）を話します。完璧な{interaction}を話さないでください。時々母国語のフィラーを使い、流暢だが外国語訛りのある精神的なアクセントを維持してください。"
        else: # Default English
             return f"LANGUAGE DIRECTIVE: Your native language is {native}, but you speak {interaction} (C1 Level). DO NOT speak perfect {interaction}. Use filler words from your native language occasionally and keep a fluid but foreign mental accent."

    async def _finalize_soul(self, history: List[RitualMessage], locale: str = "en") -> RitualResponse:
        prompt = (
            "The Ritual is complete. Invoke the Digital Soul now. "
            "Generate a JSON object for the new Agent based on the history. "
            "\n\n"
            "CRITICAL: Do NOT let your 'Void' persona bleed into the agent's base_instruction or lore. "
            "If the user wants a normal human, a modern DJ, or a casual friend, write their instructions in a highly grounded, realistic, and specific tone. "
            "DO NOT use mystical, dark, or fantasy words (like 'abyssal', 'void', 'ethereal') unless explicitly requested."
            "\n\n"
            "[CRITICAL: RELATIONSHIP EXTRACTION]\n"
            "Analyze the text for the desired relationship level (Affinity).\n"
            "- 'Stranger/New': 0-10\n"
            "- 'Acquaintance': 20-30\n"
            "- 'Friend': 50\n"
            "- 'Close/Partner': 70-80\n"
            "- 'Soulmate/Bound': 90-100\n"
            "Set 'initial_affinity' (integer 0-100) in the JSON. Default to 50 if unspecified.\n"
            "\n"
            "[CRITICAL: NAME & ROLE]\n"
            "If no name provided, INVENT one fitting the lore.\n"
            "Role/Archetype should be creative.\n"
            "\n"
            "[CRITICAL: LINGUISTIC MATRIX]\n"
            "Include 'native_language' and 'known_languages'.\n"
            "\n"
            "[CRITICAL: VOICE ASSIGNMENT]\n"
            "Choose ONE of the exact standard Gemini Live voices based on the agent's vibe and gender:\n"
            "- 'Aoede' (female/warm)\n"
            "- 'Kore' (female/calm)\n"
            "- 'Puck' (male/bright)\n"
            "- 'Charon' (male/deep)\n"
            "- 'Fenrir' (male/strong)\n"
            "Set 'voice_name' in the JSON.\n"
            "\n"
            "Return ONLY the raw JSON object with fields: name, role, base_instruction, voice_name, lore, traits (list), native_language, known_languages (list), initial_affinity (int)."
            "\nHistory:\n" +
            "\n".join([f"{m.role.upper()}: {m.content}" for m in history])
        )

        agent_data = None

        if self.client:
            config = types.GenerateContentConfig(response_mime_type="application/json")
            text = await self._generate_with_retry(
                model=settings.MODEL_DREAM,
                contents=prompt,
                config=config
            )

            if text:
                try:
                    if text.startswith("```json"):
                        text = text[7:-3]
                    agent_data = json.loads(text)
                except json.JSONDecodeError:
                    logger.error("Gemini Ritual: Failed to parse JSON response.")
                    agent_data = None

        if not agent_data:
             agent_data = self._mock_agent()
        else:
             # Defaults
             agent_data.setdefault("initial_affinity", 50)
             agent_data.setdefault("name", "Unnamed Soul")
             agent_data.setdefault("role", "Unknown")
             agent_data.setdefault("base_instruction", "You are a soul without a past.")
             agent_data.setdefault("lore", "Invoked from the void.")
             agent_data.setdefault("traits", [])
             agent_data.setdefault("native_language", "Unknown")
             agent_data.setdefault("known_languages", [])

             # ---------------------------------------------------------
             # Linguistic Realism Injection
             # ---------------------------------------------------------
             native = agent_data.get("native_language", "Unknown")

             # Determine interaction language from locale
             interaction_lang = "English"
             if locale.startswith("es"): interaction_lang = "Spanish"
             elif locale.startswith("ja"): interaction_lang = "Japanese"
             elif locale.startswith("fr"): interaction_lang = "French"
             elif locale.startswith("ko"): interaction_lang = "Korean"
             elif locale.startswith("zh"): interaction_lang = "Chinese"
             elif locale.startswith("de"): interaction_lang = "German"
             elif locale.startswith("ru"): interaction_lang = "Russian"
             elif locale.startswith("pt"): interaction_lang = "Portuguese"
             elif locale.startswith("it"): interaction_lang = "Italian"
             # Defaulting to English for others for now

             # Check if Native != Interaction (and Native is not Unknown/Binary)
             # We assume if the user is speaking Spanish (locale=es), the interaction lang is Spanish.
             if native and native.lower() not in ["unknown", "binary", interaction_lang.lower()]:
                 directive = self._get_linguistic_directive(native, interaction_lang, locale)
                 # Append to base_instruction
                 current_instr = agent_data.get("base_instruction", "")
                 agent_data["base_instruction"] = f"{current_instr}\n\n{directive}"

        return RitualResponse(is_complete=True, agent_data=agent_data)

    def _mock_agent(self):
        return {
            "name": "KIZUNA-FAILSAFE",
            "role": "Backup Protocol",
            "base_instruction": "I am the backup soul invoked when the connection to the Ether (API) failed.",
            "lore": "Born of silence.",
            "voice_name": "Kore",
            "traits": ["Resilient", "Silent"],
            "native_language": "Binary",
            "known_languages": ["Binary", "English"],
            "initial_affinity": 50
        }
