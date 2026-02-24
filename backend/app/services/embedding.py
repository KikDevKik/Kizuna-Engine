import logging
import asyncio
from typing import List, Optional
from core.config import settings

try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.mock_mode = settings.MOCK_GEMINI

        # Priority list of models to try
        self.models = [
            "models/text-embedding-004",
            "text-embedding-004",
            "models/gemini-embedding-001",
            "gemini-embedding-001"
        ]
        self.client = None

        if self.mock_mode:
            logger.info("⚠️ MOCK_GEMINI is enabled. Using Mock Embedding Service.")
        elif not self.api_key:
            logger.error("🚨 GEMINI_API_KEY is missing. Embedding Service will fail unless mocked.")
        elif genai:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
        else:
             logger.error("❌ google-genai library not found.")

    async def embed_text(self, text: str) -> List[float]:
        """
        Generates a vector embedding for the given text.
        Iterates through known model names to find a working one.
        Returns a list of floats, or empty list on failure.
        """
        if self.mock_mode:
            # Return dummy 768-dim vector (standard for text-embedding-004)
            return [0.0] * 768

        if not self.client:
            logger.error("EmbeddingService: No client available (Check API Key or Install google-genai).")
            return []

        for model in self.models:
            try:
                # Using async client for non-blocking IO with timeout
                result = await asyncio.wait_for(
                    self.client.aio.models.embed_content(
                        model=model,
                        contents=text
                    ),
                    timeout=10.0 # Prevent indefinite hanging
                )

                # Handle response structure
                if hasattr(result, 'embedding') and result.embedding:
                     return result.embedding.values
                elif hasattr(result, 'embeddings') and result.embeddings:
                     return result.embeddings[0].values

                logger.warning(f"Unexpected embedding response format from {model}: {result}")
                # If format is wrong, maybe try next model? Or just return empty?
                # Usually format is consistent across models if library is same.
                return []

            except asyncio.TimeoutError:
                logger.warning(f"Timeout while generating embedding with model {model}.")
                continue # Try next model
            except Exception as e:
                logger.warning(f"Failed to generate embedding with {model}: {e}")
                continue # Try next model

        logger.error("All embedding models failed.")
        return []

# Singleton instance
embedding_service = EmbeddingService()
