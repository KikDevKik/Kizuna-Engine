from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import logging
from app.services.auth_service import _firebase_initialized
from firebase_admin import auth

logger = logging.getLogger(__name__)

def get_user_id(request: Request) -> str:
    """
    Extracts user_id for rate limiting.
    First tries to get it from the Authorization header.
    If no token or invalid token, falls back to IP address.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if _firebase_initialized:
            try:
                decoded_token = auth.verify_id_token(token)
                user_id = decoded_token.get("uid")
                if user_id:
                    return user_id
            except Exception as e:
                logger.debug(f"RateLimiter: Auth failed, falling back to IP. Error: {e}")
                pass
        else:
            return "guest_user"

    # Fallback to IP address
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_id)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for RateLimitExceeded.
    Returns JSON with {"error": "rate_limit_exceeded", "retry_after": N}
    """
    # Expose the wait time if available, otherwise default to 60.
    # In slowapi, 'exc.detail' usually contains a string like "60 per 1 minute"
    # To be perfectly correct with retry_after, we'd need to calculate it,
    # but 60 is a safe fallback for our 60/minute limit.
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "retry_after": 60}
    )
