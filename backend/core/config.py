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

    # MOCK_GEMINI (Code Health)
    MOCK_GEMINI: bool = os.getenv("MOCK_GEMINI", "false").lower() == "true"

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Model Configuration (The Gemini Triad)
    # User Requirement: Use Gemini 2.5+ (Flash/Pro). Avoid 1.5/2.0.

    # 1. Main Voice Thread (Low Latency Audio)
    # Original model that was connecting successfully. The v1beta API does not support
    # gemini-2.0-flash-live-001 — that endpoint does not exist. Override via env var.
    MODEL_LIVE_VOICE: str = os.getenv("MODEL_LIVE_VOICE", "gemini-2.5-flash-native-audio-preview-12-2025")

    # 2. Subconscious Worker (Fast Text Analysis - Scout)
    # 🏰 BASTION: Swapped order. Use stable 2.5 first. 3.0 previews have very low rate limits.
    MODEL_SUBCONSCIOUS: list[str] = json.loads(os.getenv("MODEL_SUBCONSCIOUS", '["gemini-2.5-flash", "gemini-3-flash-preview"]'))

    # 3. Dream Cycle (Deep Reasoning / Consolidation - Architect)
    # In Production: Uses Pro (e.g. gemini-3.0-pro-exp) for maximum narrative quality.
    # In Development: Forces Flash to avoid 429 errors.
    _MODEL_DREAM_PROD: list[str] = json.loads(os.getenv("MODEL_DREAM", '["gemini-3.0-pro-exp", "gemini-3-flash-preview", "gemini-2.5-flash"]'))

    # 4. Soul Forge (Hollow Forging - Agent Generation)
    # Always Flash 2.5 for low latency and structured output reliability.
    MODEL_FORGE: str = os.getenv("MODEL_FORGE", "gemini-2.5-flash")
    # 5. Time-Skip Narrator (Background Event Generation - Ultra Fast)
    MODEL_FLASH_LITE: str = os.getenv("MODEL_FLASH_LITE", "gemini-2.5-flash-lite")

    @property
    def MODEL_DREAM(self) -> list[str]:
        if self.ENVIRONMENT == "development":
            return self.MODEL_SUBCONSCIOUS
        return self._MODEL_DREAM_PROD

    CORS_ORIGINS: list[str] = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000", "tauri://localhost", "http://tauri.localhost", "https://tauri.localhost"]'))

    # GCP Configuration (Phase 3.2)
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    SPANNER_INSTANCE_ID: str = os.getenv("SPANNER_INSTANCE_ID", "")
    SPANNER_DATABASE_ID: str = os.getenv("SPANNER_DATABASE_ID", "")
    FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "") # Path to JSON or JSON content

    # Neo4j Graph Database Configuration
    NEO4J_URI: str | None = os.getenv("NEO4J_URI", None)
    NEO4J_USERNAME: str | None = os.getenv("NEO4J_USERNAME", None)
    NEO4J_PASSWORD: str | None = os.getenv("NEO4J_PASSWORD", None)

    # Google Cloud Application Credentials (for Firestore)
    GOOGLE_APPLICATION_CREDENTIALS: str | None = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", None)


    # Redis Configuration (Phase 5)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # Sleep Manager Configuration
    SLEEP_GRACE_PERIOD: int = int(os.getenv("SLEEP_GRACE_PERIOD", "5"))

settings = Settings()
