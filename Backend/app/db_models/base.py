"""
Base database configuration for conversation history.
Uses async SQLAlchemy for non-blocking I/O.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from dotenv import load_dotenv

load_dotenv()

# Convention for constraint naming
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

class Base(DeclarativeBase):
    """Base class for all models"""
    metadata = metadata


# Async database URL for history storage
# Falls back to SQLite for development if MySQL not available
HISTORY_DB_URL = os.getenv(
    "MYSQL_HISTORY_URL", 
    "sqlite+aiosqlite:///./Backend/data/conversations.db"
)

# Create async engine
# For MySQL: mysql+aiomysql://user:pass@host:port/db
# For SQLite: sqlite+aiosqlite:///path/to/db.db
engine = create_async_engine(
    HISTORY_DB_URL,
    echo=os.getenv("DEBUG", "false").lower() == "true",
    pool_pre_ping=True,  # Check connection health
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")


async def close_db():
    """Close database connections"""
    await engine.dispose()
