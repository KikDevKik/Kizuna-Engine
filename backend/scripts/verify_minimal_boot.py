import sys
import os
from pathlib import Path

# Add backend to sys.path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(BACKEND_ROOT))

# Mock environment variables if missing to prevent crash on import
if not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = "dummy_key_for_verification"
    print("⚠️ Used dummy GEMINI_API_KEY for verification.")

# Mock other critical env vars
if not os.getenv("FIREBASE_CREDENTIALS"):
    os.environ["FIREBASE_CREDENTIALS"] = "dummy_creds.json"

try:
    # Attempt to import the main app
    # This triggers all startup checks (except actual @app.on_event("startup") which runs on server start)
    # But module level code runs.
    from app.main import app
    print("✅ Successfully imported app.main (Backend Boot Verified)")
    sys.exit(0)
except Exception as e:
    print(f"❌ Failed to import app.main: {e}")
    sys.exit(1)
