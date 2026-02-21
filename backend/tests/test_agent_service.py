import pytest
import pytest_asyncio
import shutil
import asyncio
from pathlib import Path
from app.services.agent_service import AgentService
from app.models.graph import AgentNode

# Use a temporary directory for tests
TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "agents"

@pytest_asyncio.fixture(scope="function")
async def agent_service():
    # Setup
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

    service = AgentService(data_dir=TEST_DATA_DIR)
    yield service

    # Teardown
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR.parent)

@pytest.mark.asyncio
async def test_create_and_get_agent(agent_service):
    # Create
    agent = await agent_service.create_agent(
        name="Test Agent",
        role="Tester",
        base_instruction="You are a test agent.",
        traits={"test": True},
        tags=["test"]
    )
    assert agent.name == "Test Agent"
    assert agent.id is not None

    # Get
    fetched_agent = await agent_service.get_agent(agent.id)
    assert fetched_agent is not None
    assert fetched_agent.id == agent.id
    assert fetched_agent.name == "Test Agent"

@pytest.mark.asyncio
async def test_list_agents(agent_service):
    await agent_service.create_agent("Agent 1", "Role 1", "Inst 1")
    await agent_service.create_agent("Agent 2", "Role 2", "Inst 2")

    agents = await agent_service.list_agents()
    assert len(agents) == 2

@pytest.mark.asyncio
async def test_delete_agent(agent_service):
    agent = await agent_service.create_agent("Delete Me", "Role", "Inst")

    # Verify exists
    assert (TEST_DATA_DIR / f"{agent.id}.json").exists()

    # Delete
    result = await agent_service.delete_agent(agent.id)
    assert result is True

    # Verify gone
    assert not (TEST_DATA_DIR / f"{agent.id}.json").exists()

    # Verify get returns None
    fetched = await agent_service.get_agent(agent.id)
    assert fetched is None

@pytest.mark.asyncio
async def test_path_traversal_prevention(agent_service):
    # Create a file outside the data directory
    sensitive_file = TEST_DATA_DIR.parent / "sensitive.json"
    sensitive_file.write_text('{"sensitive": "data"}', encoding='utf-8')

    try:
        # Try to access it via path traversal
        # Path: ../sensitive
        agent_id = "../sensitive"

        # Test get_agent
        result = await agent_service.get_agent(agent_id)
        assert result is None

        # Test delete_agent
        result = await agent_service.delete_agent(agent_id)
        assert result is False

        # Verify file still exists
        assert sensitive_file.exists()

    finally:
        if sensitive_file.exists():
            sensitive_file.unlink()

@pytest.mark.asyncio
async def test_absolute_path_prevention(agent_service):
    # Create a temporary file somewhere else
    # e.g. /tmp/test_agent_vuln.json
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False) as tmp:
        tmp.write('{"test": "data"}')
        tmp_path = Path(tmp.name)

    try:
        # Try to access using absolute path
        # If we strip extension, we get just path without .json
        # But create_agent appends .json
        # get_agent appends .json
        # so we need to pass path without .json
        agent_id = str(tmp_path.with_suffix(''))

        # However, if tmp_path is /tmp/foo.json, agent_id is /tmp/foo
        # agent_service constructs /tmp/foo.json

        # Test get_agent
        result = await agent_service.get_agent(agent_id)
        assert result is None

        # Test delete_agent
        result = await agent_service.delete_agent(agent_id)
        assert result is False

        # Verify file still exists
        assert tmp_path.exists()

    finally:
        if tmp_path.exists():
            tmp_path.unlink()
