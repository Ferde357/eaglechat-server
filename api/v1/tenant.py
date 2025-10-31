"""
Tenant Management Endpoints
"""

from fastapi import APIRouter, HTTPException
from core.validators import (
    TenantRegistrationRequest, 
    TenantRegistrationResponse,
    TenantValidationRequest,
    generate_tenant_id,
    generate_secure_api_key
)
from database import db
from core.wordpress_client import wp_client
from core.logger import logger

router = APIRouter()


@router.post("/register", response_model=TenantRegistrationResponse)
async def register_tenant(request: TenantRegistrationRequest):
    """Register a new WordPress tenant with callback verification"""
    try:
        logger.info(f"Registration request received for site: {request.site_url}")
        
        # Check if site already exists
        site_exists = await db.check_existing_site(request.site_url)
        if site_exists:
            logger.warning(f"Registration failed: Site already exists - {request.site_url}")
            raise HTTPException(
                status_code=400,
                detail="Site URL already registered"
            )
        
        # Check if email already has a tenant
        existing_tenant = await db.get_tenant_by_email(request.admin_email)
        if existing_tenant:
            logger.warning(f"Registration failed: Email already registered - {request.admin_email}")
            raise HTTPException(
                status_code=400,
                detail="Admin email already associated with another tenant"
            )
        
        # Verify callback token with WordPress
        logger.info(f"Verifying callback token with WordPress site: {request.site_url}")
        token_valid = await wp_client.verify_callback_token(
            request.site_url, 
            request.callback_token
        )
        
        if not token_valid:
            logger.error(f"Callback token verification failed for site: {request.site_url}")
            raise HTTPException(
                status_code=400,
                detail="Failed to verify callback token with WordPress site"
            )
        
        # Generate credentials after successful verification
        tenant_id = generate_tenant_id()
        api_key = generate_secure_api_key()
        
        # Register in database
        result = await db.register_tenant(
            tenant_id=tenant_id,
            api_key=api_key,
            site_url=request.site_url,
            admin_email=request.admin_email
        )
        
        if result.get('success'):
            logger.info(f"Successfully registered tenant: {tenant_id} for site: {request.site_url}")
            return TenantRegistrationResponse(
                success=True,
                tenant_id=tenant_id,
                api_key=api_key,
                message="Tenant registered successfully"
            )
        else:
            error = result.get('error', 'Unknown error occurred')
            logger.error(f"Registration failed: {error}")
            raise HTTPException(status_code=400, detail=error)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during registration"
        )


@router.post("/validate")
async def validate_tenant(request: TenantValidationRequest):
    """Validate tenant credentials"""
    try:
        logger.info(f"Validation request for tenant: {request.tenant_id}")
        
        is_valid = await db.validate_tenant(request.tenant_id, request.api_key)
        
        if is_valid:
            logger.info(f"Tenant validated successfully: {request.tenant_id}")
            return {
                "valid": True,
                "message": "Credentials are valid"
            }
        else:
            logger.warning(f"Invalid credentials for tenant: {request.tenant_id}")
            raise HTTPException(
                status_code=401,
                detail="Invalid tenant credentials"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during validation"
        )