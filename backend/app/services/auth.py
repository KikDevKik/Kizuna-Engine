import firebase_admin
from firebase_admin import auth, credentials
import logging
from core.config import settings
import os
import json

logger = logging.getLogger(__name__)

class FirebaseAuth:
    """
    Handles Firebase Authentication and Token Verification.
    Phase 3.2: Secure Identity.
    """
    _initialized = False

    @classmethod
    def initialize(cls):
        """
        Initializes the Firebase Admin SDK.
        """
        if cls._initialized:
            return

        try:
            cred_path = settings.FIREBASE_CREDENTIALS

            # Check if it's a path or raw JSON
            cred = None
            if cred_path.endswith(".json") and os.path.exists(cred_path):
                logger.info(f"Loading Firebase credentials from file: {cred_path}")
                cred = credentials.Certificate(cred_path)
            elif cred_path.startswith("{"):
                logger.info("Loading Firebase credentials from JSON string.")
                cred_dict = json.loads(cred_path)
                cred = credentials.Certificate(cred_dict)
            else:
                # Default Application Default Credentials (ADC) if on GCP
                logger.info("Using Google Application Default Credentials for Firebase.")
                cred = credentials.ApplicationDefault()

            firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("Firebase Admin SDK initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")
            # Do not raise here, allow app to start in case of local dev fallback
            # But verify_token will fail.

    @staticmethod
    def verify_token(token: str) -> str:
        """
        Verifies a Firebase ID Token.
        Returns the User UID if valid.
        Raises ValueError if invalid.
        """
        if not FirebaseAuth._initialized:
             # Try lazy init
             FirebaseAuth.initialize()
             if not FirebaseAuth._initialized:
                 # If still not init, maybe we are in mock/local mode without creds?
                 if os.getenv("MOCK_AUTH", "false").lower() == "true":
                     logger.warning("⚠️ MOCK_AUTH enabled. Accepting dummy token.")
                     return "mock_user_123"
                 raise RuntimeError("Firebase not initialized.")

        try:
            # Verify the token
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            return uid
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            raise ValueError("Invalid Authentication Token") from e

# Auto-initialize on import if possible/safe?
# Better to do it in startup event.
