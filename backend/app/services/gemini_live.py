import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from core.config import settings

# Use try-except for google.genai imports in case it's not installed or not needed for mock
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


logger = logging.getLogger(__name__)

# Check for Mock Mode
MOCK_MODE = settings.MOCK_GEMINI

if MOCK_MODE:
    logger.warning("⚠️ MOCK_GEMINI is enabled. Using MockGeminiService.")
    # Import Mock Service
    try:
        from app.services.mock_gemini import MockGeminiService
        gemini_service = MockGeminiService()
    except ImportError as e:
        logger.error(f"Failed to import MockGeminiService: {e}")
        raise
else:
    # 2. Extraemos la llave de forma manual
    api_key = settings.GEMINI_API_KEY

    # 3. Si no la encuentra, explota
    if not api_key:
        raise ValueError("🚨 ERROR CRÍTICO: GEMINI_API_KEY environment variable is not set. 🚨")

    # 4. Inicializamos el cliente
    client = genai.Client(api_key=api_key)

    class GeminiLiveService:
        """
        Service to handle Gemini Live API connections.
        """

        @staticmethod
        @asynccontextmanager
        async def connect(system_instruction: str, voice_name: Optional[str] = None) -> AsyncGenerator['genai.live.AsyncSession', None]:
            """
            Establishes an asynchronous connection to the Gemini Live API.

            Args:
                system_instruction (str): The system prompt for the AI agent.
                voice_name (str, optional): The name of the voice to use (e.g. "Aoede", "Puck").

            Yields:
                genai.live.AsyncSession: The active session for sending and receiving messages.
            """
            # Configure the session
            speech_config = None
            if voice_name:
                speech_config = types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name
                        )
                    )
                )

            # Response modalities is set to AUDIO to ensure we get audio back.
            config = types.LiveConnectConfig(
                response_modalities=[types.Modality.AUDIO],
                speech_config=speech_config,
                system_instruction=types.Content(
                    parts=[types.Part(text=system_instruction)]
                ),
            )

            model_id = settings.MODEL_LIVE_VOICE
            logger.info(f"Connecting to Gemini Live API with model: {model_id}")

            try:
                async with client.aio.live.connect(
                    model=model_id,
                    config=config
                ) as session:
                    logger.info("Connected to Gemini Live API session.")
                    yield session
            except Exception as e:
                logger.error(f"Error connecting to Gemini Live API: {e}")
                raise

    gemini_service = GeminiLiveService()
