import pytest
from httpx import AsyncClient
from app.main import app
from app.models.graph import SystemConfigNode

@pytest.mark.asyncio
async def test_get_system_config():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/system/config")
    assert response.status_code == 200
    data = response.json()
    assert "core_directive" in data
    assert "affinity_matrix" in data

@pytest.mark.asyncio
async def test_update_system_config():
    new_directive = "TEST DIRECTIVE"
    # We need to provide a valid affinity matrix structure or rely on defaults if partial updates were supported,
    # but the model validation likely requires the full object or defaults.
    # The default affinity_matrix is a list of lists.
    payload = {
        "id": "system-config",
        "core_directive": new_directive,
        "affinity_matrix": [[0, "Cold"]] # Minimal valid matrix
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put("/api/system/config", json=payload)

    # If the response is 200, check the data.
    assert response.status_code == 200
    data = response.json()
    assert data["core_directive"] == new_directive

    # Verify persistence
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/system/config")
    assert response.status_code == 200
    data = response.json()
    assert data["core_directive"] == new_directive
