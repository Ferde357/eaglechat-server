"""
Core Services Module for EagleChat
Contains shared utilities and services
"""

from .config import settings
from .logger import logger, context_logger
from .validators import (
    TenantRegistrationRequest, 
    TenantRegistrationResponse,
    TenantValidationRequest,
    ChatRequest,
    ChatResponse,
    AIConfig,
    ErrorResponse,
    generate_tenant_id,
    generate_secure_api_key
)
from .key_manager import key_manager
from .conversation_manager import conversation_manager
from .api_key_validator import api_key_validator
from .wordpress_client import wp_client

__all__ = [
    "settings", 
    "logger", 
    "context_logger",
    "TenantRegistrationRequest", 
    "TenantRegistrationResponse",
    "TenantValidationRequest",
    "ChatRequest",
    "ChatResponse", 
    "AIConfig",
    "ErrorResponse",
    "generate_tenant_id",
    "generate_secure_api_key"
]