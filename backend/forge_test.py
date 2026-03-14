"""Run from: cd C:\Users\User\kizuna-engine\backend && python forge_test.py"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.agent_service import AgentService
from pathlib import Path

async def main():
    service = AgentService()
    try:
        agent, memories = await service.forge_hollow_agent(
            "A silent archivist who collects dying languages in a flooded library."
        )
        print(f"SUCCESS: {agent.name} ({agent.id})")
    except Exception as e:
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"EXCEPTION MESSAGE: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(main())
