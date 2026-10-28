import asyncio
import os
import sys

# Ensure current directory is on python path
sys.path.insert(0, os.path.abspath("."))

from backend.database import engine
from backend.models.schema import Base

async def init_tables():
    print("Connecting to database and creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_tables())