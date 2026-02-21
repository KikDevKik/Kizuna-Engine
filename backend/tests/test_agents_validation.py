import os
import sys
from unittest.mock import patch, AsyncMock
import pytest

# Add backend to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock environment variables
os.environ["GEMINI_API_KEY"] = "mock-key"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["GCP_PROJECT_ID"] = "" # Dev mode

# Mock dependencies before importing app to avoid startup side effects
with patch("app.services.gemini_live.gemini_service"), \
     patch("app.dependencies.soul_repo"), \
     patch("app.services.cache.cache"), \
     patch("app.services.sleep_manager.SleepManager"), \
     patch("app.services.seeder.seed_data", new_callable=AsyncMock):
    from app.main import app

from fastapi.testclient import TestClient

client = TestClient(app)

def test_create_agent_huge_input():
    # Attempt to create an agent with a huge name (over 100 chars)
    huge_name = "a" * 101
    response = client.post("/api/agents/", json={
        "name": huge_name,
        "role": "Test Role",
        "base_instruction": "Test Instruction"
    })
    # If validation is missing, this will likely succeed (201)
    # We assert 422 because that's our goal
    assert response.status_code == 422

def test_create_agent_error_masking():
    # Mock the service to raise an exception with sensitive info
    with patch("app.routers.agents.agent_service.create_agent", side_effect=Exception("SecretDBPassword")):
        response = client.post("/api/agents/", json={
            "name": "Valid Name",
            "role": "Valid Role",
            "base_instruction": "Valid Instruction"
        })

        assert response.status_code == 500
        # Ensure the secret is NOT leaked
        assert "SecretDBPassword" not in response.text
        # Ensure we get a generic error
        assert "Internal Server Error" in response.text

def test_create_agent_deep_validation():
    # Test long tag
    response = client.post("/api/agents/", json={
        "name": "Valid Name",
        "role": "Valid Role",
        "base_instruction": "Valid Instruction",
        "tags": ["a" * 51]
    })
    assert response.status_code == 422
    # Pydantic's error message structure might vary, but we expect validation error

    # Test long trait key
    response = client.post("/api/agents/", json={
        "name": "Valid Name",
        "role": "Valid Role",
        "base_instruction": "Valid Instruction",
        "traits": {"a" * 51: "value"}
    })
    assert response.status_code == 422
