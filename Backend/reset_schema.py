
import asyncio
import os
import sys
from sqlalchemy import text
from app.db_models.base import engine, init_db

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def reset():
    async with engine.begin() as conn:
        print(f"Connected to: {engine.url}")
        
        # Disable FK checks to allow dropping tables easily
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        tables = ["artifacts", "messages", "conversations", "users"]
        for table in tables:
            print(f"Dropping table {table}...")
            await conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        print("\nExisting tables dropped.")

    print("\nRe-initializing database schema...")
    await init_db()
    print("Database reset complete!")
    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(reset())
    except Exception as e:
        print(f"Error: {e}")
