"""
API Key Management Endpoints
"""

import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import db
from core.key_manager import key_manager
from core.api_key_validator import api_key_validator
from core.logger import logger

router = APIRouter()


class APIKeyConfigRequest(BaseModel):
    tenant_id: str
    api_key: str
    anthropic_api_key: str = ""
    openai_api_key: str = ""


class APIKeyVerifyRequest(BaseModel):
    tenant_id: str
    api_key: str
    provider: str  # "anthropic" or "openai"


class APIKeyStatusRequest(BaseModel):
    tenant_id: str
    api_key: str


class APIKeyRemoveRequest(BaseModel):
    tenant_id: str
    api_key: str
    provider: str  # "anthropic" or "openai"


@router.post("/configure-keys")
async def configure_api_keys(request: APIKeyConfigRequest):
    """Configure AI API keys for a tenant"""
    try:
        logger.info(f"API key configuration request for tenant: {request.tenant_id}")
        
        # Validate tenant credentials
        is_valid = await db.validate_tenant(request.tenant_id, request.api_key)
        if not is_valid:
            logger.warning(f"Invalid credentials for API key configuration: {request.tenant_id}")
            raise HTTPException(
                status_code=401,
                detail="Invalid tenant credentials"
            )
        
        # Validate API keys with actual providers before storing
        validation_results = await api_key_validator.validate_api_keys(
            anthropic_key=request.anthropic_api_key,
            openai_key=request.openai_api_key
        )
        
        # Check if at least one key is valid
        if not validation_results['any_valid']:
            errors = []
            if request.anthropic_api_key and not validation_results['anthropic']['valid']:
                errors.append(f"Anthropic: {validation_results['anthropic']['error']}")
            if request.openai_api_key and not validation_results['openai']['valid']:
                errors.append(f"OpenAI: {validation_results['openai']['error']}")
            
            logger.warning(f"API key validation failed for tenant {request.tenant_id}: {'; '.join(errors)}")
            raise HTTPException(
                status_code=400,
                detail=f"API key validation failed: {'; '.join(errors)}"
            )
        
        # Only store keys that passed validation
        anthropic_key_to_store = request.anthropic_api_key if validation_results['anthropic']['valid'] else ""
        openai_key_to_store = request.openai_api_key if validation_results['openai']['valid'] else ""
        
        # Store validated keys securely per tenant
        success = await key_manager.store_tenant_keys(
            tenant_id=request.tenant_id,
            anthropic_key=anthropic_key_to_store,
            openai_key=openai_key_to_store
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to store API keys securely"
            )
        
        logger.info(f"API keys configured successfully for tenant: {request.tenant_id}")
        stats = await key_manager.get_tenant_stats(request.tenant_id)
        
        # Build response with validation details
        response_data = {
            "success": True,
            "message": "API keys processed successfully",
            "anthropic_configured": stats['anthropic_configured'],
            "openai_configured": stats['openai_configured'],
            "validation_results": {}
        }
        
        # Add validation details for each provider
        if request.anthropic_api_key:
            response_data["validation_results"]["anthropic"] = {
                "valid": validation_results['anthropic']['valid'],
                "stored": validation_results['anthropic']['valid'],
                "error": validation_results['anthropic']['error']
            }
        
        if request.openai_api_key:
            response_data["validation_results"]["openai"] = {
                "valid": validation_results['openai']['valid'],
                "stored": validation_results['openai']['valid'],
                "error": validation_results['openai']['error']
            }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during API key configuration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during API key configuration"
        )


@router.post("/verify-key")
async def verify_api_key(request: APIKeyVerifyRequest):
    """Verify that a stored API key is still valid"""
    try:
        logger.info(f"API key verification request for tenant: {request.tenant_id}, provider: {request.provider}")
        
        # Validate tenant credentials
        is_valid = await db.validate_tenant(request.tenant_id, request.api_key)
        if not is_valid:
            logger.warning(f"Invalid credentials for API key verification: {request.tenant_id}")
            raise HTTPException(
                status_code=401,
                detail="Invalid tenant credentials"
            )
        
        # Get the stored API key for this provider
        tenant_key = await key_manager.get_tenant_key(request.tenant_id, request.provider)
        if not tenant_key:
            raise HTTPException(
                status_code=404,
                detail=f"No {request.provider} API key configured for this tenant"
            )
        
        # Verify the key with the provider
        if request.provider == "anthropic":
            is_valid, error = await api_key_validator.validate_anthropic_key(tenant_key)
        elif request.provider == "openai":
            is_valid, error = await api_key_validator.validate_openai_key(tenant_key)
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid provider. Must be 'anthropic' or 'openai'"
            )
        
        response_data = {
            "provider": request.provider,
            "valid": is_valid,
            "error": error,
            "verified_at": time.time()
        }
        
        if not is_valid:
            logger.warning(f"Stored {request.provider} API key invalid for tenant {request.tenant_id}: {error}")
        else:
            logger.info(f"Stored {request.provider} API key verified for tenant {request.tenant_id}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during API key verification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during API key verification"
        )


@router.post("/get-key-status")
async def get_api_key_status(request: APIKeyStatusRequest):
    """Get masked API key status for WordPress admin display"""
    try:
        logger.info(f"API key status request for tenant: {request.tenant_id}")
        
        # Validate tenant credentials
        is_valid = await db.validate_tenant(request.tenant_id, request.api_key)
        if not is_valid:
            logger.warning(f"Invalid credentials for API key status: {request.tenant_id}")
            raise HTTPException(
                status_code=401,
                detail="Invalid tenant credentials"
            )
        
        # Get tenant stats (which provider keys are configured)
        stats = await key_manager.get_tenant_stats(request.tenant_id)
        
        # Get masked keys for display
        masked_keys = {}
        
        if stats['anthropic_configured']:
            # Get the key to create a mask
            anthropic_key = await key_manager.get_tenant_key(request.tenant_id, 'anthropic')
            if anthropic_key:
                # Create masked version (first 8 + last 4 characters)
                if len(anthropic_key) > 12:
                    masked_keys['anthropic'] = anthropic_key[:8] + '*' * (len(anthropic_key) - 12) + anthropic_key[-4:]
                else:
                    masked_keys['anthropic'] = '*' * len(anthropic_key)
        
        if stats['openai_configured']:
            # Get the key to create a mask  
            openai_key = await key_manager.get_tenant_key(request.tenant_id, 'openai')
            if openai_key:
                # Create masked version (first 8 + last 4 characters)
                if len(openai_key) > 12:
                    masked_keys['openai'] = openai_key[:8] + '*' * (len(openai_key) - 12) + openai_key[-4:]
                else:
                    masked_keys['openai'] = '*' * len(openai_key)
        
        return {
            "success": True,
            "anthropic_configured": stats['anthropic_configured'],
            "openai_configured": stats['openai_configured'], 
            "total_providers": stats['total_providers'],
            "masked_keys": masked_keys
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during API key status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during API key status"
        )


@router.post("/remove-key")
async def remove_api_key(request: APIKeyRemoveRequest):
    """Remove a specific API key for a tenant"""
    try:
        logger.info(f"API key removal request for tenant: {request.tenant_id}, provider: {request.provider}")
        
        # Validate tenant credentials
        is_valid = await db.validate_tenant(request.tenant_id, request.api_key)
        if not is_valid:
            logger.warning(f"Invalid credentials for API key removal: {request.tenant_id}")
            raise HTTPException(
                status_code=401,
                detail="Invalid tenant credentials"
            )
        
        # Validate provider
        if request.provider not in ['anthropic', 'openai']:
            raise HTTPException(
                status_code=400,
                detail="Invalid provider. Must be 'anthropic' or 'openai'"
            )
        
        # Remove the specific API key from Supabase
        result = await db.remove_tenant_api_key(
            tenant_id=request.tenant_id,
            provider=request.provider
        )
        
        success = result.get('success', False) if result else False
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to remove API key from storage"
            )
        
        logger.info(f"{request.provider.title()} API key removed successfully for tenant: {request.tenant_id}")
        
        return {
            "success": True,
            "message": f"{request.provider.title()} API key removed successfully",
            "provider": request.provider
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during API key removal: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during API key removal"
        )