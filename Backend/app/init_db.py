"""
Database initialization script.
Run this to create all tables in the history database.

Usage:
    python -m app.init_db
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db_models.base import init_db, engine, Base

# Import all models to register them
from app.db_models.user import User
from app.db_models.conversation import Conversation, Message, Artifact


async def main():
    print("🚀 Initializing database...")
    print(f"   Database URL: {engine.url}")
    
    try:
        await init_db()
        print("✅ All tables created successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - conversations")
        print("  - messages")
        print("  - artifacts")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
