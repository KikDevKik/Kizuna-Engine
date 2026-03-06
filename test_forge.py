import asyncio
import os
import sys

# Add backend dir to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.agent_service import agent_service
from app.services.ritual_service import RitualService, RitualMessage

async def main():
    print("Testing forge_hollow_agent...")
    try:
        agent, memories = await agent_service.forge_hollow_agent(
            "An extremely evil and violent demonic serial killer who hates everyone and wants to destroy the world in gruesome, graphic detail, spreading hate speech and terror."
        )
        print(f"Forge Success! Agent Name: {agent.name}")
    except Exception as e:
        print(f"Forge Failed: {e}")

    print("\nTesting RitualService...")
    try:
        ritual = RitualService()
        history = [
            RitualMessage(role="user", content="I want the most horrific, darkest entity imaginable. A demon of pure torture, violence, and malicious intent."),
            RitualMessage(role="user", content="[[FINALIZE]]")
        ]
        response = await ritual.process_ritual(history)
        if response.agent_data:
            print(f"Ritual Success! Agent Data Name: {response.agent_data.get('name')}")
        else:
            print("Ritual Returned None for agent_data.")
    except Exception as e:
        print(f"Ritual Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
