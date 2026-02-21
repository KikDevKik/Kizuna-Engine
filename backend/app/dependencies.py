import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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

# --- Security & Authentication ---

# Security Scheme (Optional Bearer Token)
security = HTTPBearer(auto_error=False)

def verify_user_logic(token: str | None) -> str:
    """
    Core authentication logic shared between REST and WebSocket.
    Validates token if present/required, returns user_id.
    Falls back to 'guest_user' in local/dev environments.
    """
    # Phase 3.2: Secure Identity if Configured
    if token and settings.FIREBASE_CREDENTIALS:
        try:
            from app.services.auth import FirebaseAuth
            user_id = FirebaseAuth.verify_token(token)
            logger.info(f"Authenticated User: {user_id}")
            return user_id
        except Exception as e:
            logger.warning(f"Authentication Failed: {e}")
            raise

    # Enforce Auth in Prod (GCP)
    if settings.GCP_PROJECT_ID:
        if not token:
            logger.warning("Connection rejected: No token provided in Production.")
            raise ValueError("Authentication Required in Production")

        # If we have a token but NO credentials in Prod -> CRITICAL ERROR
        if not settings.FIREBASE_CREDENTIALS:
            logger.critical("SECURITY ALERT: Production environment detected but FIREBASE_CREDENTIALS are missing. Cannot verify token.")
            raise ValueError("Server Misconfiguration: Auth credentials missing in Production.")

    # Lab Mode / Guest
    return "guest_user"

async def get_current_user(
    token_creds: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    FastAPI Dependency for REST Endpoints.
    Extracts Bearer token and validates user identity.
    """
    token = token_creds.credentials if token_creds else None
    try:
        return verify_user_logic(token)
    except ValueError as e:
        logger.warning(f"Access Denied: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Auth Error: {e}")
        # If it's not a ValueError (auth rejection), it might be an internal error
        # Re-raising HTTPException allows FastAPI to handle it
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )
