import re
import secrets
from uuid import UUID, uuid4
from typing import Optional
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
        if len(v) < 16:
            raise ValueError("callback_token must be at least 16 characters")
        if len(v) > 256:
            raise ValueError("callback_token must not exceed 256 characters")
        return v
    
    @validator('site_url')
    def validate_site_url(cls, v):
        """Validate site URL format"""
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(v):
            raise ValueError("Invalid URL format")
        
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