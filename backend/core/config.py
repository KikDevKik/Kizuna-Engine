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

    # Environment Toggle
    # 'development' = Force Flash for everything (save quota)
    # 'production' = Enable Pro models for Architect/Dream (high quality)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Model Configuration (The Gemini Triad)
    # User Requirement: Use Gemini 2.5+ (Flash/Pro). Avoid 1.5/2.0.

    # 1. Main Voice Thread (Low Latency Audio)
    # Using 2.5 Flash as the stable base for audio/realtime if supported, or standard Flash.
    MODEL_LIVE_VOICE: str = os.getenv("MODEL_LIVE_VOICE", "gemini-2.5-flash")

    # 2. Subconscious Worker (Fast Text Analysis - Scout)
    # Always Flash for speed and cost.
    MODEL_SUBCONSCIOUS: str = os.getenv("MODEL_SUBCONSCIOUS", "gemini-2.5-flash")

    # 3. Dream Cycle (Deep Reasoning / Consolidation - Architect)
    # In Production: Uses Pro (e.g. gemini-3.0-pro-exp) for maximum narrative quality.
    # In Development: Forces Flash to avoid 429 errors.
    _MODEL_DREAM_PROD: str = os.getenv("MODEL_DREAM", "gemini-3.0-pro-exp")

    @property
    def MODEL_DREAM(self) -> str:
        if self.ENVIRONMENT == "development":
            return self.MODEL_SUBCONSCIOUS
        return self._MODEL_DREAM_PROD

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
