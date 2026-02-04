
import asyncio
import os
import sys
from sqlalchemy import text
from app.db_models.base import engine

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def inspect():
    async with engine.connect() as conn:
        print(f"Connected to: {engine.url}")
        
        # Check columns
        try:
            result = await conn.execute(text("DESCRIBE users"))
            print("\nColumns in 'users' table:")
            columns = result.fetchall()
            for col in columns:
                print(f" - {col[0]} ({col[1]})")
                
            # Check row count
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"\nTotal rows in 'users': {count}")
            
        except Exception as e:
            print(f"Error inspecting table: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
