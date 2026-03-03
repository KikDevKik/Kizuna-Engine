import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["MOCK_GEMINI"] = "true"

from core.config import settings
from app.repositories.local_graph import LocalSoulRepository
from app.services.seeder import seed_data
from app.services.agent_service import AgentService

async def verify():
    print("Initializing test DB")
    settings.SQLITE_DB_PATH = "sqlite+aiosqlite:///test_seeder.db"

    repo = LocalSoulRepository()
    await repo.initialize()
    await repo.purge_all_memories()

    print("Running seed_data")
    await seed_data(repo)

    agent_service = AgentService()

    # Verify Locations
    locations = await repo.get_locations()
    print("\n--- LOCATIONS GENERATED ---")
    for loc in locations:
        print(f"Location: {loc.name} | Type: {loc.type}")

    print("\n--- STRANGERS GENERATED ---")
    strangers = await repo.get_agents()
    count = 0
    for s in strangers:
        if s.role.lower() == "stranger" or (hasattr(s, "tags") and "stranger" in s.tags):
            print(f"Stranger: {s.name} | is_revealed: {s.is_revealed}")
            print(f"  Instruction: {s.base_instruction[:100]}")
            count += 1

    print(f"\nStrangers count: {count}")
    print(f"Locations count: {len(locations)}")

if __name__ == "__main__":
    asyncio.run(verify())
