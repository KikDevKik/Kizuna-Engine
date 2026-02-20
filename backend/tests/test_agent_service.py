import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.services.agent_service import AgentService
from app.models.graph import AgentNode

def test_agent_service():
    print("Testing AgentService...")
    service = AgentService()

    # 1. List Agents
    agents = service.list_agents()
    print(f"Found {len(agents)} agents.")
    for agent in agents:
        print(f" - {agent.name} ({agent.role})")
        assert isinstance(agent, AgentNode)

    # 2. Create Agent
    new_agent_name = "TestAgent"
    new_agent = service.create_agent(
        name=new_agent_name,
        role="TEST ROLE",
        base_instruction="You are a test agent.",
        tags=["test"]
    )
    print(f"Created agent: {new_agent.name} ({new_agent.id})")
    assert new_agent.name == new_agent_name

    # 3. Get Agent
    fetched_agent = service.get_agent(new_agent.id)
    assert fetched_agent is not None
    assert fetched_agent.id == new_agent.id
    print(f"Fetched agent: {fetched_agent.name}")

    # Clean up
    file_path = service.data_dir / f"{new_agent.id}.json"
    if file_path.exists():
        file_path.unlink()
        print("Cleaned up test agent file.")

if __name__ == "__main__":
    test_agent_service()
