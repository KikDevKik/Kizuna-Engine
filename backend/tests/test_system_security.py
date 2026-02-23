import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock environment variables to prevent startup errors
os.environ["GEMINI_API_KEY"] = "mock-key"
os.environ["REDIS_URL"] = "redis://localhost:6379"

# We need to mock dependencies before importing main because of startup events
with patch("app.services.gemini_live.gemini_service"), \
     patch("app.dependencies.soul_repo"), \
     patch("app.services.cache.cache"), \
     patch("app.services.agent_service.agent_service"):
    from app.main import app

client = TestClient(app)

def test_system_config_secure_in_prod():
    """
    Simulate Production Mode (GCP_PROJECT_ID set).
    Attempt to access /api/system/config without a token.
    Now asserts 401 Unauthorized (SECURE).
    """
    # Set GCP_PROJECT_ID to simulate Production
    with patch("app.dependencies.settings.GCP_PROJECT_ID", "prod-project"), \
         patch("app.dependencies.settings.FIREBASE_CREDENTIALS", "cred.json"):

        # Mock the repository call to return dummy data so we don't hit the DB
        with patch("app.routers.system.get_repository") as mock_repo_dep:
            mock_repo = MagicMock()
            mock_repo.get_system_config = AsyncMock(return_value={
                "id": "system-config",
                "core_directive": "Test Directive",
                "affinity_matrix": []
            })

            from app.dependencies import get_repository
            app.dependency_overrides[get_repository] = lambda: mock_repo

            try:
                response = client.get("/api/system/config")

                # SECURE: Expecting 401 because auth is missing
                assert response.status_code == 401
                print("\n[SECURITY CONFIRMED] /api/system/config is protected in Production!")

            finally:
                app.dependency_overrides = {}

def test_purge_memories_secure_in_prod():
    """
    Simulate Production Mode.
    Attempt to access /api/system/purge-memories without a token.
    Now asserts 401 Unauthorized (SECURE).
    """
    with patch("app.dependencies.settings.GCP_PROJECT_ID", "prod-project"), \
         patch("app.dependencies.settings.FIREBASE_CREDENTIALS", "cred.json"):

        from app.dependencies import get_repository
        from app.repositories.local_graph import LocalSoulRepository

        mock_repo = MagicMock(spec=LocalSoulRepository)
        mock_repo.purge_all_memories = AsyncMock(return_value=None)

        app.dependency_overrides[get_repository] = lambda: mock_repo

        try:
            response = client.delete("/api/system/purge-memories")

            # SECURE: Expecting 401 because auth is missing
            assert response.status_code == 401
            print("\n[SECURITY CONFIRMED] /api/system/purge-memories is protected in Production!")

        finally:
            app.dependency_overrides = {}

def test_dev_access_allowed():
    """
    Simulate Development Mode (no GCP_PROJECT_ID).
    Access should be allowed without a token (defaults to guest_user).
    """
    with patch("app.dependencies.settings.GCP_PROJECT_ID", ""), \
         patch("app.dependencies.settings.FIREBASE_CREDENTIALS", ""):

        # Mock the repository call
        with patch("app.routers.system.get_repository") as mock_repo_dep:
            mock_repo = MagicMock()
            mock_repo.get_system_config = AsyncMock(return_value={
                "id": "system-config",
                "core_directive": "Dev Directive",
                "affinity_matrix": []
            })

            from app.dependencies import get_repository
            app.dependency_overrides[get_repository] = lambda: mock_repo

            try:
                response = client.get("/api/system/config")

                # ALLOWED: Expecting 200 in Dev Mode
                assert response.status_code == 200
                print("\n[DEV ACCESS CONFIRMED] /api/system/config is accessible in Dev Mode.")

            finally:
                app.dependency_overrides = {}
