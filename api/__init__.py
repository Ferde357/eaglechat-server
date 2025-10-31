"""
API Module for EagleChat
Handles all REST API endpoints
"""

from .v1 import v1_router
from .v1.health import router as health_router
from .middleware import rate_limit_middleware, add_cors_middleware

__all__ = ["v1_router", "health_router", "rate_limit_middleware", "add_cors_middleware"]