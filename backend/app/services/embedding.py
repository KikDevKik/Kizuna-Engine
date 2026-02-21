import logging
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
        self.model = "text-embedding-004"
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
        Generates a vector embedding for the given text using text-embedding-004.
        Returns a list of floats.
        """
        if self.mock_mode:
            # Return dummy 768-dim vector (standard for text-embedding-004)
            # Just a placeholder for testing flow
            return [0.0] * 768

        if not self.client:
            logger.error("EmbeddingService: No client available (Check API Key or Install google-genai).")
            return []

        try:
            # Using async client for non-blocking IO
            result = await self.client.aio.models.embed_content(
                model=self.model,
                contents=text
            )

            # Handle response structure
            if hasattr(result, 'embedding') and result.embedding:
                 return result.embedding.values
            elif hasattr(result, 'embeddings') and result.embeddings:
                 return result.embeddings[0].values

            logger.warning(f"Unexpected embedding response format: {result}")
            return []

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []

# Singleton instance
embedding_service = EmbeddingService()
