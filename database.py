"""
Database Connection and Session Management
Async PostgreSQL with connection pooling
Fixed for Render deployment with automatic URL conversion
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
from sqlalchemy import text
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================
# DATABASE URL CONVERSION (FIX FOR RENDER)
# ============================================

def get_database_url() -> str:
    """
    Get database URL and convert to async format
    
    Handles:
    - Render's postgres:// format → postgresql+asyncpg://
    - Standard postgresql:// format → postgresql+asyncpg://
    - Local development URLs
    
    Returns:
        str: Properly formatted async database URL
    """
    # Get DATABASE_URL from environment
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:110305@localhost:5432/campusvoice"
    )
    
    logger.info(f"🔗 Raw DATABASE_URL: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
    
    # ✅ FIX 1: Convert Render's postgres:// to postgresql+asyncpg://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
        logger.info("🔄 Converted postgres:// → postgresql+asyncpg://")
    
    # ✅ FIX 2: Convert standard postgresql:// to postgresql+asyncpg://
    elif db_url.startswith("postgresql://") and "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        logger.info("🔄 Converted postgresql:// → postgresql+asyncpg://")
    
    # ✅ FIX 3: Already has asyncpg - no conversion needed
    elif "asyncpg" in db_url:
        logger.info("✅ Database URL already has async driver")
    
    # Validate URL format
    if not db_url.startswith("postgresql+asyncpg://"):
        raise ValueError(f"Invalid database URL format: {db_url[:30]}...")
    
    logger.info(f"✅ Final DATABASE_URL format: postgresql+asyncpg://...")
    return db_url

# Get the properly formatted database URL
DATABASE_URL = get_database_url()

# ============================================
# DATABASE CONFIGURATION
# ============================================

DB_ECHO = os.getenv("DEBUG", "False").lower() == "true"
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))  # Reduced for free tier
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

# ============================================
# ASYNC ENGINE CREATION
# ============================================

def create_engine_instance() -> AsyncEngine:
    """
    Create async database engine with connection pooling
    
    Returns:
        AsyncEngine: Configured async engine
    """
    logger.info("🔧 Creating async database engine...")
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=DB_ECHO,  # Log SQL queries (only in DEBUG mode)
        future=True,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=DB_POOL_SIZE,  # Max connections in pool
        max_overflow=DB_MAX_OVERFLOW,  # Extra connections when pool full
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "server_settings": {
                "application_name": "CampusVoice_Backend"
            },
            "command_timeout": 60,  # Query timeout in seconds
            "timeout": 10,  # Connection timeout
        },
    )
    
    logger.info("✅ Database engine created successfully!")
    return engine

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

logger.info("✅ Session factory created!")

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
            logger.error(f"❌ Database session error: {e}")
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
    try:
        logger.info("📊 Initializing database tables...")
        
        # ✅ CORRECT: Import models with DB suffix
        from models_db import Base, StudentDB, ComplaintDB, VoteDB, StatusUpdateDB, MetaDB
        
        async with engine.begin() as conn:
            # Create all tables defined in Base.metadata
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

async def drop_all_tables():
    """
    Drop all tables (USE WITH CAUTION!)
    
    Only use in development for resetting database
    """
    try:
        from models_db import Base
        
        logger.warning("⚠️  Dropping all database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.warning("⚠️  All tables dropped!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        raise

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
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection: OK")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
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
    try:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
        }
    except Exception as e:
        logger.error(f"❌ Error getting pool status: {e}")
        return {"error": str(e)}

# ============================================
# CLEANUP
# ============================================

async def close_db():
    """
    Close database connections
    
    Call this on application shutdown
    """
    try:
        logger.info("🔌 Closing database connections...")
        await engine.dispose()
        logger.info("✅ Database connections closed successfully!")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")
        raise

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
                logger.error(f"❌ All retry attempts failed: {e}")
                raise e
            logger.warning(f"⚠️  Retry attempt {attempt + 1}/{max_retries}")
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
    logger.info("\n" + "="*50)
    logger.info("DATABASE CONNECTION TEST")
    logger.info("="*50)
    
    # Test connection
    is_connected = await check_db_connection()
    
    if is_connected:
        # Show pool stats
        stats = get_pool_status()
        if "error" not in stats:
            logger.info(f"\n📊 Connection Pool Stats:")
            logger.info(f"   Pool Size: {stats['pool_size']}")
            logger.info(f"   Checked In: {stats['checked_in']}")
            logger.info(f"   Checked Out: {stats['checked_out']}")
            logger.info(f"   Overflow: {stats['overflow']}")
            logger.info(f"   Total: {stats['total_connections']}")
        
        # Test query
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"\n🐘 PostgreSQL Version:")
                logger.info(f"   {version}")
        except Exception as e:
            logger.error(f"❌ Error getting PostgreSQL version: {e}")
    
    logger.info("="*50 + "\n")
    
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
    "execute_with_retry",
]
