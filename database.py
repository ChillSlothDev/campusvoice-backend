"""
Database Connection and Session Management
Async PostgreSQL with connection pooling
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from dotenv import load_dotenv
from models_db import Base

# Load environment variables
load_dotenv()

# ============================================
# DATABASE CONFIGURATION
# ============================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:110305@localhost:5432/campusvoice"
)

DB_ECHO = os.getenv("DEBUG", "False").lower() == "true"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

print(f"🔗 Database URL: {DATABASE_URL.split('@')[1]}")  # Hide password in logs


# ============================================
# ASYNC ENGINE CREATION
# ============================================

def create_engine_instance() -> AsyncEngine:
    """
    Create async database engine with connection pooling
    
    Returns:
        AsyncEngine: Configured async engine
    """
    return create_async_engine(
        DATABASE_URL,
        echo=DB_ECHO,  # Log SQL queries (only in DEBUG mode)
        future=True,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=DB_POOL_SIZE,  # Max connections in pool
        max_overflow=DB_MAX_OVERFLOW,  # Extra connections when pool full
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "server_settings": {
                "jit": "off",  # Disable JIT for faster simple queries
                "application_name": "CampusVoice_Backend"
            },
            "command_timeout": 60,  # Query timeout in seconds
            "timeout": 10,  # Connection timeout
        },
        # Note: poolclass is not needed for async engines
        # AsyncAdaptedQueuePool is used by default
    )


# Create global engine instance
engine = create_engine_instance()


# ============================================
# SESSION FACTORY
# ============================================

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,  # Manual flush control
    autocommit=False,  # Manual commit control
)


# ============================================
# SESSION DEPENDENCY (for FastAPI)
# ============================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get database session
    
    Usage in FastAPI:
        @app.get("/complaints")
        async def get_complaints(db: AsyncSession = Depends(get_db)):
            # Use db here
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except Exception as e:
            await session.rollback()  # Rollback on error
            raise e
        finally:
            await session.close()


# ============================================
# DATABASE INITIALIZATION
# ============================================

async def init_db():
    """
    Initialize database - Create all tables
    
    Call this on application startup
    """
    async with engine.begin() as conn:
        # Create all tables defined in Base.metadata
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully!")


async def drop_all_tables():
    """
    Drop all tables (USE WITH CAUTION!)
    
    Only use in development for resetting database
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    print("⚠️  All tables dropped!")


# ============================================
# DATABASE HEALTH CHECK
# ============================================

async def check_db_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        print("✅ Database connection: OK")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# ============================================
# CONNECTION POOL STATS
# ============================================

def get_pool_status() -> dict:
    """
    Get current connection pool statistics
    
    Returns:
        dict: Pool status information
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }


# ============================================
# CLEANUP
# ============================================

async def close_db():
    """
    Close database connections
    
    Call this on application shutdown
    """
    await engine.dispose()
    print("✅ Database connections closed")


# ============================================
# TRANSACTION HELPER
# ============================================

async def execute_with_retry(func, max_retries: int = 3):
    """
    Execute database function with retry logic
    
    Args:
        func: Async function to execute
        max_retries: Maximum retry attempts
    
    Returns:
        Result of the function
    """
    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                result = await func(session)
                await session.commit()
                return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"⚠️  Retry attempt {attempt + 1}/{max_retries}")
            await session.rollback()


# ============================================
# CONTEXT MANAGER FOR MANUAL SESSIONS
# ============================================

class DatabaseSession:
    """
    Context manager for manual database sessions
    
    Usage:
        async with DatabaseSession() as db:
            result = await db.execute(query)
    """
    
    def __init__(self):
        self.session: AsyncSession = None
    
    async def __aenter__(self) -> AsyncSession:
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()


# ============================================
# TESTING UTILITIES
# ============================================

async def test_connection():
    """
    Test database connection and print info
    """
    print("\n" + "="*50)
    print("DATABASE CONNECTION TEST")
    print("="*50)
    
    # Test connection
    is_connected = await check_db_connection()
    
    if is_connected:
        # Show pool stats
        stats = get_pool_status()
        print(f"\n📊 Connection Pool Stats:")
        print(f"   Pool Size: {stats['pool_size']}")
        print(f"   Checked In: {stats['checked_in']}")
        print(f"   Checked Out: {stats['checked_out']}")
        print(f"   Overflow: {stats['overflow']}")
        print(f"   Total: {stats['total_connections']}")
        
        # Test query
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"\n🐘 PostgreSQL Version:")
            print(f"   {version}")
    
    print("="*50 + "\n")
    
    return is_connected


# ============================================
# EXPORT
# ============================================

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "drop_all_tables",
    "check_db_connection",
    "get_pool_status",
    "close_db",
    "DatabaseSession",
    "test_connection",
]
