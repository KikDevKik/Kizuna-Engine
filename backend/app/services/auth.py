try:
    import firebase_admin
    from firebase_admin import auth, credentials
except ImportError:
    firebase_admin = None
    auth = None
    credentials = None

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

        if firebase_admin is None:
            logger.error("❌ firebase_admin is not installed. Auth will fail unless in Mock mode.")
            return

        try:
            cred_path = settings.FIREBASE_CREDENTIALS
            if not cred_path:
                logger.warning("⚠️ No FIREBASE_CREDENTIALS provided.")
                return

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

    @staticmethod
    def verify_token(token: str) -> str:
        """
        Verifies a Firebase ID Token.
        Returns the User UID if valid.
        Raises ValueError if invalid.
        """
        # 1. Fallback for Missing Libs
        if firebase_admin is None:
             if os.getenv("MOCK_AUTH", "false").lower() == "true" or not settings.FIREBASE_CREDENTIALS:
                 logger.warning("⚠️ Auth Library Missing. Returning Mock User.")
                 return "mock_user_no_lib"
             raise RuntimeError("firebase_admin library missing.")

        # 2. Check Initialization
        if not FirebaseAuth._initialized:
             # Try lazy init
             FirebaseAuth.initialize()
             if not FirebaseAuth._initialized:
                 # If still not init, allow mock if no creds
                 if not settings.FIREBASE_CREDENTIALS or os.getenv("MOCK_AUTH", "false").lower() == "true":
                     logger.warning("⚠️ Firebase not initialized. Accepting dummy token.")
                     return "mock_user_no_init"
                 raise RuntimeError("Firebase not initialized and credentials present.")

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
