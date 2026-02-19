import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from google import genai
from google.genai import types

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Force load the .env file from the backend root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Retrieve the API key explicitly
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try getting it from settings as a fallback if env didn't work directly but settings did (unlikely)
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise ValueError(f"CRITICAL ERROR: No se encontró GEMINI_API_KEY en {env_path}")

# Initialize the client with the explicit API key
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

        logger.info(f"Connecting to Gemini Live API with model: {settings.LIVE_MODEL_ID}")

        try:
            async with client.aio.live.connect(
                model=settings.LIVE_MODEL_ID,
                config=config
            ) as session:
                logger.info("Connected to Gemini Live API session.")
                yield session
        except Exception as e:
            logger.error(f"Error connecting to Gemini Live API: {e}")
            raise

gemini_service = GeminiLiveService()
