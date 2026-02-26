from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from pathlib import Path
import os

# Ensure the database file is stored in the backend root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR}/kizuna_graph.db"

# 3. SQLITE ARMOR (WAL Mode)
# Target: The Chief Architect
# Update the SQLAlchemy create_async_engine connection string or engine arguments.
# You MUST pass connect_args={"check_same_thread": False}.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

# You MUST execute the PRAGMA PRAGMA journal_mode=WAL; (Write-Ahead Logging) and PRAGMA synchronous=NORMAL; upon engine initialization.
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    """Initializes the database schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
