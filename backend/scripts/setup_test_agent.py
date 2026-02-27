import asyncio
import httpx
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "kizuna_graph.db"

async def setup():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Forging new agent...")
        resp = await client.post("http://localhost:8000/api/agents/forge_hollow", json={"aesthetic_description": "A test agent"})
        if resp.status_code == 201:
            data = resp.json()
            print(f"Agent forged: {data['id']}")
        else:
            print(f"Failed to forge: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    asyncio.run(setup())
