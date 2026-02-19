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
    LIVE_MODEL_ID: str = "gemini-2.5-flash-native-audio-preview-12-2025"
    CORS_ORIGINS: list[str] = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://localhost:3000"]'))

settings = Settings()
