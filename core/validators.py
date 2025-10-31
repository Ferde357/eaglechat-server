import re
import secrets
from uuid import UUID, uuid4
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, EmailStr


class TenantRegistrationRequest(BaseModel):
    site_url: str = Field(..., description="WordPress site URL")
    admin_email: EmailStr = Field(..., description="Admin email address")
    callback_token: str = Field(..., description="Temporary token for WordPress callback verification")
    
    @validator('callback_token')
    def validate_callback_token(cls, v):
        """Validate callback token is not empty and reasonable length"""
        if not v or len(v.strip()) == 0:
            raise ValueError("callback_token cannot be empty")
        
        # Check if development mode is enabled
        from .config import settings
        if settings.api.development_mode:
            # In development mode, allow shorter tokens for easier testing
            if len(v) < 4:
                raise ValueError("callback_token must be at least 4 characters in development mode")
        else:
            # Production mode - require full security
            if len(v) < 16:
                raise ValueError("callback_token must be at least 16 characters")
        
        if len(v) > 256:
            raise ValueError("callback_token must not exceed 256 characters")
        return v
    
    @validator('site_url')
    def validate_site_url(cls, v):
        """Validate site URL format with security restrictions"""
        from .config import settings
        
        # In development mode, allow localhost and private IPs
        if settings.api.development_mode:
            # Basic URL validation for development - allow localhost
            dev_url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:'
                r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'  # IP address
                r')'
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE
            )
            
            if not dev_url_pattern.match(v):
                raise ValueError("Invalid URL format. Development mode allows localhost and IP addresses.")
            
            return v
        
        # Production mode - strict validation
        # Basic URL validation - restrict to public domains only
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?)'  # domain only (no localhost/IPs)
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format. Only public domain names are allowed.")
        
        # Additional security checks for private networks
        from urllib.parse import urlparse
        parsed = urlparse(v)
        hostname = parsed.hostname
        
        # Block private IP ranges and localhost
        if hostname:
            import ipaddress
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    raise ValueError("Private IP addresses and localhost are not allowed")
            except ipaddress.AddressValueError:
                # Not an IP address, continue with domain validation
                pass
        
        # Block localhost and private domain patterns
        blocked_patterns = ['localhost', '127.', '192.168.', '10.', '172.']
        if any(pattern in v.lower() for pattern in blocked_patterns):
            raise ValueError("Private networks and localhost are not allowed")
        
        # Normalize URL - remove trailing slash
        if v.endswith('/'):
            v = v[:-1]
        
        return v


class TenantRegistrationResponse(BaseModel):
    success: bool
    tenant_id: Optional[str] = None
    api_key: Optional[str] = None
    message: str
    

class TenantValidationRequest(BaseModel):
    tenant_id: str = Field(..., description="UUID for the tenant")
    api_key: str = Field(..., description="API key for authentication")
    
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        """Validate tenant_id is a valid UUID"""
        try:
            UUID(v)
        except ValueError:
            raise ValueError("tenant_id must be a valid UUID")
        return v


def generate_tenant_id() -> str:
    """Generate a new UUID for tenant"""
    return str(uuid4())


def generate_secure_api_key(prefix: str = "eck", length: int = 48) -> str:
    """
    Generate a secure API key with prefix
    Format: prefix_randomstring (e.g., eck_a1b2c3d4...)
    """
    # Generate random bytes and convert to URL-safe string
    random_part = secrets.token_urlsafe(length)
    # Remove any characters that might cause issues (keep alphanumeric, dash, underscore)
    random_part = re.sub(r'[^a-zA-Z0-9_-]', '', random_part)[:length-len(prefix)-1]
    
    return f"{prefix}_{random_part}"


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID"""
    try:
        UUID(value)
        return True
    except ValueError:
        return False


class AIConfig(BaseModel):
    """AI configuration for chat requests"""
    model: str = Field(..., description="AI model to use")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="AI temperature setting")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=100000, description="Maximum tokens for response")
    conversation_memory: str = Field(default="medium", description="Conversation memory setting")
    
    @validator('model')
    def validate_model(cls, v):
        """Validate AI model selection"""
        valid_models = ['claude-sonnet', 'claude-haiku', 'claude-opus', 'openai-gpt5', 'openai-gpt-mini', 'openai-gpt-nano']
        if v not in valid_models:
            raise ValueError(f"Invalid model: {v}. Must be one of {valid_models}")
        return v
    
    @validator('conversation_memory')
    def validate_memory(cls, v):
        """Validate conversation memory setting"""
        valid_memory = ['short', 'medium', 'long']
        if v not in valid_memory:
            raise ValueError(f"Invalid conversation_memory: {v}. Must be one of {valid_memory}")
        return v


class ChatRequest(BaseModel):
    """Chat request from WordPress"""
    tenant_id: str = Field(..., description="Tenant UUID")
    api_key: str = Field(..., description="Tenant API key")
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    session_id: str = Field(..., description="Chat session ID")
    ai_config: AIConfig = Field(..., description="AI configuration settings")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional conversation history from WordPress")
    
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        """Validate tenant_id is a valid UUID"""
        if not is_valid_uuid(v):
            raise ValueError("tenant_id must be a valid UUID")
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session_id format"""
        if not re.match(r'^[a-zA-Z0-9]{32,64}$', v):
            raise ValueError("Invalid session_id format")
        return v


class ChatResponse(BaseModel):
    """Chat response to WordPress"""
    response: str = Field(..., description="AI generated response")
    input_tokens: int = Field(..., ge=0, description="Tokens used for input")
    output_tokens: int = Field(..., ge=0, description="Tokens used for output")
    total_tokens: int = Field(..., ge=0, description="Total tokens used")
    model_used: str = Field(..., description="AI model that generated the response")
    finish_reason: str = Field(default="stop", description="Why the response ended")
    session_id: str = Field(..., description="Chat session ID")




class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for categorization")
    details: Optional[str] = Field(default=None, description="Additional error details")