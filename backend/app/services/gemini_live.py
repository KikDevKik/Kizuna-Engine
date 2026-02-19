import os
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# 1. Buscamos el archivo .env a la fuerza
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 2. Extraemos la llave de forma manual
api_key = os.getenv("GEMINI_API_KEY")

# 3. Si no la encuentra, explota
if not api_key:
    raise ValueError(f"🚨 ERROR CRÍTICO: No se encontró la llave GEMINI_API_KEY en {env_path} 🚨")

# 4. Inicializamos el cliente
client = genai.Client(api_key=api_key)

class GeminiLiveService:
    """
    Service to handle Gemini Live API connections.
    """

    @staticmethod
    @asynccontextmanager
    async def connect() -> AsyncGenerator[genai.live.AsyncSession, None]:
        """
        Establishes an asynchronous connection to the Gemini Live API.

        Yields:
            genai.live.AsyncSession: The active session for sending and receiving messages.
        """
        # Configure the session
        # We start with a simple system instruction as requested.
        # Response modalities is set to AUDIO to ensure we get audio back.
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[types.Part(text="Eres Kizuna, un asistente reactivo")]
            ),
        )

        logger.info(f"Connecting to Gemini Live API with model: {"gemini-2.5-flash-native-audio-preview-12-2025"}")

        try:
            async with client.aio.live.connect(
                model="gemini-2.5-flash-native-audio-preview-12-2025",
                config=config
            ) as session:
                logger.info("Connected to Gemini Live API session.")
                yield session
        except Exception as e:
            logger.error(f"Error connecting to Gemini Live API: {e}")
            raise

gemini_service = GeminiLiveService()
