"""
API v1 Endpoints
"""

from fastapi import APIRouter
from .health import router as health_router
from .tenant import router as tenant_router
from .chat import router as chat_router
from .keys import router as keys_router

# Create main v1 router
v1_router = APIRouter(prefix="/api/v1")

# Include endpoint routers (health will be added at root level)
v1_router.include_router(tenant_router, tags=["tenant"])
v1_router.include_router(chat_router, tags=["chat"])
v1_router.include_router(keys_router, tags=["api-keys"])

__all__ = ["v1_router"]