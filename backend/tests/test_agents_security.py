
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock environment variables to prevent startup errors
os.environ["GEMINI_API_KEY"] = "mock-key"
os.environ["REDIS_URL"] = "redis://localhost:6379"

# We need to mock dependencies before importing main because of startup events
with patch("app.services.gemini_live.gemini_service"), \
     patch("app.dependencies.soul_repo"), \
     patch("app.services.cache.cache"):
    from app.main import app

client = TestClient(app)

def test_create_agent_dev_mode_allowed():
    """
    In Development Mode (default, no GCP_PROJECT_ID), create_agent should be allowed without auth.
    """
    with patch("app.dependencies.settings.GCP_PROJECT_ID", ""), \
         patch("app.dependencies.settings.FIREBASE_CREDENTIALS", ""):

        # We expect 201 Created or 500 (if service fails), but NOT 401/403
        # Mocking the service to return success
        with patch("app.routers.agents.agent_service.create_agent") as mock_create:
            mock_create.return_value = {
                "id": "test-agent",
                "name": "Test Agent",
                "role": "Tester",
                "base_instruction": "Test Instruction",
                "traits": {},
                "tags": []
            }

            response = client.post("/api/agents/", json={
                "name": "Test Agent",
                "role": "Tester",
                "base_instruction": "Test"
            })

            # Should be allowed (201 or 200 depending on implementation)
            # Currently returns 200 OK because create_agent returns the new_agent
            assert response.status_code in [200, 201]

def test_create_agent_prod_mode_no_token_blocked():
    """
    In Production Mode (GCP_PROJECT_ID set), create_agent MUST be blocked without a token.
    """
    # Simulate Production Environment
    with patch("app.dependencies.settings.GCP_PROJECT_ID", "prod-project"), \
         patch("app.dependencies.settings.FIREBASE_CREDENTIALS", "cred.json"):

        # Mocking the service to return success (to simulate vulnerability if auth is missing)
        with patch("app.routers.agents.agent_service.create_agent") as mock_create:
            mock_create.return_value = {
                "id": "test-agent",
                "name": "Test Agent",
                "role": "Tester",
                "base_instruction": "Test Instruction",
                "traits": {},
                "tags": []
            }

            response = client.post("/api/agents/", json={
                "name": "Test Agent",
                "role": "Tester",
                "base_instruction": "Test"
            })

            # This is the expected behavior AFTER the fix.
            # Before fix, this will return 201 (Failure of test)
            # We assert what we WANT to see to confirm the fix works later.
            assert response.status_code in [401, 403]

# def test_create_agent_prod_mode_with_token_allowed():
#     """
#     In Production Mode, create_agent should be allowed with a valid token.
#     """
#     with patch("app.dependencies.settings.GCP_PROJECT_ID", "prod-project"), \
#          patch("app.dependencies.settings.FIREBASE_CREDENTIALS", "cred.json"), \
#          patch("app.dependencies.verify_user_logic") as mock_verify:

#         mock_verify.return_value = "authenticated_user_id"

#         with patch("app.routers.agents.agent_service.create_agent") as mock_create:
#             mock_create.return_value = {
#                 "id": "test-agent",
#                 "name": "Test Agent",
#                 "role": "Tester",
#                 "base_instruction": "Test Instruction",
#                 "traits": {},
#                 "tags": []
#             }

#             headers = {"Authorization": "Bearer valid-token"}
#             response = client.post("/api/agents/", json={
#                 "name": "Test Agent",
#                 "role": "Tester",
#                 "base_instruction": "Test"
#             }, headers=headers)

#             assert response.status_code in [200, 201]
