import os
import sys

# 1. Set Mock Mode BEFORE any imports from app to ensure GeminLiveService initializes in Mock Mode
os.environ["MOCK_GEMINI"] = "true"

# 2. Add backend to sys.path
# backend/tests/verify_soul.py -> backend/
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(backend_path)

try:
    from fastapi.testclient import TestClient
    from app.main import app
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running from the backend root or have dependencies installed.")
    sys.exit(1)

def test_kizuna_connection():
    print("Starting Soul Verification Tests...")

    with TestClient(app) as client:
        # Test 1: No Agent ID -> Should Fail
        print("\n[Test 1] Connecting without agent_id...")
        try:
            with client.websocket_connect("/ws/live") as websocket:
                print("❌ Failed: Connection accepted without agent_id")
                sys.exit(1)
        except Exception:
            # TestClient raises generic exception or WebSocketDisconnect on rejection during handshake
            print("✅ Correctly rejected without agent_id")

        # Test 2: Invalid Agent ID
        print("\n[Test 2] Connecting with invalid agent_id 'ghost'...")
        try:
            with client.websocket_connect("/ws/live?agent_id=ghost") as websocket:
                print("❌ Failed: Connection accepted for invalid agent")
                sys.exit(1)
        except Exception:
             print("✅ Correctly rejected invalid agent")

        # Test 3: Valid Agent (Kizuna)
        print("\n[Test 3] Connecting with valid agent_id 'kizuna'...")
        try:
            with client.websocket_connect("/ws/live?agent_id=kizuna", headers={"Origin": "http://localhost:5173"}) as websocket:
                print("✅ Connection established for Kizuna")
                # Check if we can receive the 'Gemini session started' log indirectly or just hold connection
                pass
        except Exception as e:
            print(f"❌ Failed to connect with Kizuna: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print("\n🎉 All Soul Verification Tests Passed!")

if __name__ == "__main__":
    test_kizuna_connection()
