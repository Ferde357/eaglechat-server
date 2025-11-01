from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from core.config import settings
from core.logger import logger
from api import v1_router, health_router, rate_limit_middleware, add_cors_middleware, hmac_middleware


# Setup logger for FastAPI
logging.getLogger("uvicorn.access").handlers = logger.handlers
logging.getLogger("uvicorn.error").handlers = logger.handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting Eagle Chat Server...")
    
    # Log development mode status
    if settings.api.development_mode:
        logger.warning("🚨 DEVELOPMENT MODE ENABLED - Relaxed security for testing only!")
        logger.warning("   - Allows localhost and private IP registration")
        logger.warning("   - Shorter callback tokens permitted")
        logger.warning("   - NOT FOR PRODUCTION USE")
    else:
        logger.info("✅ Production mode - Full security validation enabled")
    
    yield
    logger.info("Shutting down Eagle Chat Server...")


# Create FastAPI app
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    lifespan=lifespan
)

# Add HMAC authentication middleware (before rate limiting)
app.middleware("http")(hmac_middleware)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Configure CORS
add_cors_middleware(app)

# Include API routes
app.include_router(health_router)  # Health check at root
app.include_router(v1_router)      # All v1 endpoints