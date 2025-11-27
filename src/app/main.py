"""
FastAPI application entry point.

Initializes the FastAPI app with middleware, routes, and startup/shutdown events.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.app.api.v1 import router as v1_router
from src.app.core.config import settings
from src.app.core.exceptions import setup_exception_handlers
from src.app.db.session import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting up FastAPI application...")
    
    # Try to initialize database, but don't fail startup if it's not available
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Application will start without database initialization")
        logger.info("You can start the database later and restart the application")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    
    # Gracefully close database connections if they exist
    try:
        from src.app.db.session import close_db
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="AI Backend Service",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Add middleware (disable TrustedHostMiddleware for development)
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(v1_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint."""
        return {"status": "ok", "service": settings.APP_NAME}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=8111,
        reload=settings.DEBUG,
        log_level="info",
    )
