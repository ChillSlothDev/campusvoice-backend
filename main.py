"""
CampusVoice Backend - Main Application
FastAPI server with PostgreSQL, WebSocket, and LLM integration
"""

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging
from dotenv import load_dotenv

# Import local modules
from database import init_db, close_db, check_db_connection, engine
from api.routes import router
from websocket_handler import manager, periodic_cleanup_task

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "campusvoice.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================
# LIFESPAN EVENT HANDLER
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for startup and shutdown
    
    Startup:
    - Check database connection
    - Initialize database tables
    - Start background tasks
    
    Shutdown:
    - Close database connections
    - Disconnect all WebSocket clients
    - Cleanup resources
    """
    # ========== STARTUP ==========
    logger.info("=" * 60)
    logger.info("🚀 CAMPUSVOICE BACKEND STARTING UP")
    logger.info("=" * 60)
    
    # Check environment
    environment = os.getenv("ENVIRONMENT", "development")
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    logger.info(f"📋 Environment: {environment}")
    logger.info(f"🐛 Debug Mode: {debug_mode}")
    
    # Check database connection
    logger.info("🔍 Checking database connection...")
    db_connected = await check_db_connection()
    
    if not db_connected:
        logger.error("❌ Database connection failed!")
        logger.error("⚠️  Backend starting anyway, but database operations will fail")
    else:
        logger.info("✅ Database connection successful")
    
    # Initialize database tables
    if db_connected:
        logger.info("📊 Initializing database tables...")
        try:
            await init_db()
            logger.info("✅ Database tables initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
    
    # Start background tasks
    logger.info("🔄 Starting background tasks...")
    cleanup_task = asyncio.create_task(periodic_cleanup_task())
    logger.info("✅ Background tasks started")
    
    # Check LLM service
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        logger.info("✅ Groq API key configured")
    else:
        logger.warning("⚠️  Groq API key not found - LLM features disabled")
    
    # Startup complete
    logger.info("=" * 60)
    logger.info("✅ CAMPUSVOICE BACKEND READY!")
    logger.info(f"📡 API Docs: http://localhost:{os.getenv('API_PORT', '8000')}/docs")
    logger.info(f"🔌 WebSocket: ws://localhost:{os.getenv('API_PORT', '8000')}/api/ws/votes/{{complaint_id}}")
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # ========== SHUTDOWN ==========
    logger.info("=" * 60)
    logger.info("🛑 CAMPUSVOICE BACKEND SHUTTING DOWN")
    logger.info("=" * 60)
    
    # Cancel background tasks
    logger.info("⏹️  Stopping background tasks...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        logger.info("✅ Background tasks stopped")
    
    # Disconnect all WebSocket clients
    logger.info("🔌 Disconnecting WebSocket clients...")
    await manager.disconnect_all()
    logger.info("✅ All WebSocket clients disconnected")
    
    # Close database connections
    logger.info("🗄️  Closing database connections...")
    await close_db()
    logger.info("✅ Database connections closed")
    
    logger.info("=" * 60)
    logger.info("✅ SHUTDOWN COMPLETE")
    logger.info("=" * 60)


# ============================================
# CREATE FASTAPI APPLICATION
# ============================================

app = FastAPI(
    title=os.getenv("API_TITLE", "CampusVoice Backend"),
    description="""
    # CampusVoice Backend API
    
    Real-time complaint management system for campus issues.
    
    ## Features
    - 🎯 Submit and manage complaints
    - 🗳️ Vote on complaints (duplicate prevention)
    - 📊 Real-time vote updates via WebSocket
    - 🤖 AI-powered complaint analysis (Groq LLM)
    - 🏢 Automatic authority routing
    - 📈 Statistics and analytics
    
    ## Key Endpoints
    - **POST /api/complaints** - Submit complaint
    - **GET /api/complaints/my** - Your complaints
    - **GET /api/complaints/public** - Public feed
    - **POST /api/vote** - Vote on complaint
    - **WebSocket /api/ws/votes/{id}** - Real-time updates
    
    ## Database
    - PostgreSQL with async support
    - UNIQUE constraint prevents duplicate votes
    - Connection pooling for performance
    
    ## Authentication
    - Roll number-based identification
    - No JWT required for MVP
    """,
    version=os.getenv("API_VERSION", "2.0.0"),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ============================================
# MIDDLEWARE CONFIGURATION
# ============================================

# CORS Middleware
allowed_origins = os.getenv("CORS_ORIGINS", '["*"]')
try:
    import json
    origins = json.loads(allowed_origins)
except:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"🌐 CORS enabled for origins: {origins}")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"📥 {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Log response
    logger.info(f"📤 {request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")
    
    return response


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"⚠️  Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "details": exc.errors(),
            "message": "Please check your request data"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc) if os.getenv("DEBUG") == "True" else None
        }
    )


# ============================================
# INCLUDE ROUTERS
# ============================================

app.include_router(router)

logger.info("✅ API routes registered")


# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information
    """
    return {
        "service": "CampusVoice Backend",
        "version": os.getenv("API_VERSION", "2.0.0"),
        "status": "operational",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "endpoints": {
            "api_docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/api/health",
            "submit_complaint": "/api/complaints",
            "my_complaints": "/api/complaints/my",
            "public_feed": "/api/complaints/public",
            "vote": "/api/vote",
            "websocket": "/api/ws/votes/{complaint_id}"
        },
        "features": [
            "Real-time voting",
            "LLM-powered analysis",
            "Duplicate vote prevention",
            "Automatic authority routing",
            "WebSocket support"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# ADDITIONAL HEALTH ENDPOINTS
# ============================================

@app.get("/health/database", tags=["Health"])
async def database_health():
    """Check database health"""
    try:
        is_healthy = await check_db_connection()
        
        # Get pool stats
        pool = engine.pool
        pool_stats = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow()
        }
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "connection": "active" if is_healthy else "failed",
            "pool": pool_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connection": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/health/websocket", tags=["Health"])
async def websocket_health():
    """Check WebSocket health"""
    stats = manager.get_stats()
    return {
        "status": "healthy",
        "websocket": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# RUN APPLICATION
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))  # Change to 1 for WebSocket testing
    reload = False  # ← CHANGE THIS TO False for WebSocket testing
    
    # Run server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        workers=1,  # Must be 1 for WebSocket
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=True,
        use_colors=True
    )
