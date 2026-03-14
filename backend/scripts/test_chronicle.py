import asyncio
import os
import sys

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import init_db
from app.models.sql import KizunaChronicleModel

async def test_db():
    print("Testing KizunaChronicleModel initialization...")
    try:
        await init_db()
        print("✅ init_db ran successfully. KizunaChronicleModel must be valid.")
    except Exception as e:
        print(f"❌ Error running init_db: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
