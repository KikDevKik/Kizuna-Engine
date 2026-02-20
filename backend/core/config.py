import os
import json
from dotenv import load_dotenv
load_dotenv()

# Load environment variables from .env file
# This ensures .env is loaded from the backend root directory regardless of where the app is started
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "Kizuna Engine"
    VERSION: str = "1.0.0"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Model Configuration (The Gemini Triad)
    # 1. Main Voice Thread (Low Latency Audio)
    MODEL_LIVE_VOICE: str = os.getenv("MODEL_LIVE_VOICE", "gemini-3-flash-preview")
    # Note: "gemini-2.5-flash-native-audio-preview-12-2025" was specific, defaulting to 2.0 Flash Exp for broader availability if needed.

    # 2. Subconscious Worker (Fast Text Analysis)
    MODEL_SUBCONSCIOUS: str = os.getenv("MODEL_SUBCONSCIOUS", "gemini-3-flash-preview")

    # 3. Dream Cycle (Deep Reasoning / Consolidation)
    MODEL_DREAM: str = os.getenv("MODEL_DREAM", "gemini-3.1-pro-preview")

    CORS_ORIGINS: list[str] = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000"]'))

    # GCP Configuration (Phase 3.2)
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    SPANNER_INSTANCE_ID: str = os.getenv("SPANNER_INSTANCE_ID", "")
    SPANNER_DATABASE_ID: str = os.getenv("SPANNER_DATABASE_ID", "")
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "") # Path to JSON or JSON content

    # Redis Configuration (Phase 5)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

settings = Settings()
