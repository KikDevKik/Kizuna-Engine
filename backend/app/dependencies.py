import logging
from app.repositories.base import SoulRepository
from app.repositories.local_graph import LocalSoulRepository
from core.config import settings

logger = logging.getLogger(__name__)

# Lazy Factory for Repository
def create_soul_repository() -> SoulRepository:
    """
    Creates the appropriate SoulRepository instance based on environment configuration.
    Returns a Singleton instance to be shared across the application.
    """
    # Phase 3.2: Check if Spanner Config is present
    if settings.GCP_PROJECT_ID and settings.SPANNER_INSTANCE_ID:
        try:
            # Lazy import to prevent crash in Local Mode if deps are missing
            from app.repositories.spanner_graph import SpannerSoulRepository
            logger.info("🌐 Using Spanner Soul Repository (Production Mode)")
            return SpannerSoulRepository()
        except ImportError as e:
            logger.warning(f"⚠️ Failed to import Spanner Repository: {e}. Falling back to Local.")
            return LocalSoulRepository()
    else:
        logger.info("🏠 Using Local Soul Repository (Development Mode)")
        return LocalSoulRepository()

# Singleton Instance (initialized at module import)
soul_repo = create_soul_repository()

# Dependency for FastAPI
def get_repository() -> SoulRepository:
    """
    Dependency to get the global SoulRepository singleton.
    """
    return soul_repo
