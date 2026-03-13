import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase Admin
_firebase_initialized = False

def initialize_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return

    # Check for credentials path or content from environment/settings
    cred_data = settings.FIREBASE_CREDENTIALS
    if cred_data:
        try:
            if cred_data.startswith("{"):
                # It's a JSON string
                import json
                cred_dict = json.loads(cred_data)
                cred = credentials.Certificate(cred_dict)
            else:
                # It's a file path
                cred = credentials.Certificate(cred_data)
                
            firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            logger.info("Firebase Admin initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")
    else:
        if cred_path:
            logger.warning(f"FIREBASE_CREDENTIALS_PATH set to {cred_path} but file not found. Falling back to guest_user.")
        else:
            logger.info("FIREBASE_CREDENTIALS_PATH not set. Operating in fallback mode (guest_user).")


initialize_firebase()


async def verify_token(token: str) -> str:
    """
    Verifies a Firebase ID token.
    Returns the user_id if valid.
    Raises HTTPException 401 if invalid.
    """
    if not _firebase_initialized:
        logger.warning("Firebase not initialized. Cannot verify token. Falling back to guest_user.")
        return "guest_user"

    try:
        # verify_id_token is synchronous, but we use it in async context. For simple verification, it's fast enough.
        # Alternatively, we could run it in a thread pool.
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get("uid")
        if not user_id:
            raise ValueError("Token does not contain a UID.")
        return user_id
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token.")
