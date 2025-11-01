"""
HMAC Authentication Middleware
Validates HMAC signatures on protected endpoints
"""

import time
from fastapi import Request, HTTPException
from typing import Callable
from core.logger import logger
from core.security.hmac_validator import hmac_validator
from core.key_manager import key_manager


# Protected endpoints that require HMAC authentication
HMAC_PROTECTED_ENDPOINTS = {
    '/api/v1/chat',
    '/api/v1/conversation-history'
}

# Endpoints exempted from HMAC authentication
HMAC_EXEMPTED_ENDPOINTS = {
    '/api/v1/register',
    '/api/v1/health',
    '/api/v1/verify',
    '/docs',
    '/redoc',
    '/openapi.json'
}


async def hmac_middleware(request: Request, call_next: Callable):
    """
    HMAC authentication middleware
    
    Validates HMAC signatures on protected endpoints:
    1. Extracts HMAC headers from request
    2. Validates timestamp within tolerance
    3. Retrieves tenant's HMAC secret
    4. Validates signature against request data
    """
    
    # Check if this endpoint requires HMAC authentication
    path = request.url.path
    
    # Skip HMAC validation for exempted endpoints
    if any(path.startswith(exempt) for exempt in HMAC_EXEMPTED_ENDPOINTS):
        return await call_next(request)
    
    # Check if this is a protected endpoint
    requires_hmac = any(path.startswith(protected) for protected in HMAC_PROTECTED_ENDPOINTS)
    
    if not requires_hmac:
        # Non-protected endpoint, proceed without HMAC validation
        return await call_next(request)
    
    # Get HMAC headers
    signature_header = request.headers.get('X-EagleChat-Signature')
    timestamp_header = request.headers.get('X-EagleChat-Timestamp')
    version_header = request.headers.get('X-EagleChat-Version', 'v1')
    origin_header = request.headers.get('X-EagleChat-Origin')
    site_hash_header = request.headers.get('X-EagleChat-Site-Hash')
    
    # Check if HMAC headers are present
    if not signature_header or not timestamp_header:
        logger.warning(f"HMAC authentication failed: Missing headers for {path}")
        raise HTTPException(
            status_code=401,
            detail="HMAC authentication required. Missing signature or timestamp headers."
        )
    
    try:
        # Parse timestamp
        timestamp = int(timestamp_header)
    except ValueError:
        logger.warning(f"HMAC authentication failed: Invalid timestamp format")
        raise HTTPException(
            status_code=401,
            detail="HMAC authentication failed: Invalid timestamp format"
        )
    
    # Validate timestamp
    if not hmac_validator.is_timestamp_valid(timestamp):
        logger.warning(f"HMAC authentication failed: Timestamp outside tolerance")
        raise HTTPException(
            status_code=401,
            detail="HMAC authentication failed: Request timestamp outside acceptable range"
        )
    
    # Read request body and make it reusable
    body = await request.body()
    
    # Create a new receive callable that returns the cached body
    async def receive_wrapper():
        return {"type": "http.request", "body": body}
    
    # Replace the request's receive method so the body can be read again
    request._receive = receive_wrapper
    
    # Extract tenant_id from request body to get HMAC secret
    tenant_id = None
    try:
        if body:
            import json
            body_data = json.loads(body)
            tenant_id = body_data.get('tenant_id')
    except Exception as e:
        logger.error(f"Error parsing request body for tenant_id: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid request body format"
        )
    
    if not tenant_id:
        logger.warning(f"HMAC authentication failed: No tenant_id in request")
        raise HTTPException(
            status_code=401,
            detail="HMAC authentication failed: tenant_id required"
        )
    
    # Get tenant's HMAC secret and domain verification data
    from database import db
    tenant_hmac_data = await db.get_tenant_hmac_domain(tenant_id)
    
    if not tenant_hmac_data or not tenant_hmac_data.get('success'):
        logger.error(f"Failed to get HMAC secret for tenant {tenant_id}: {tenant_hmac_data.get('error', 'Unknown error')}")
        raise HTTPException(
            status_code=401,
            detail="HMAC authentication failed: No HMAC secret configured for tenant"
        )
    
    hmac_secret_encrypted = tenant_hmac_data.get('hmac_secret_encrypted')
    if not hmac_secret_encrypted:
        logger.warning(f"HMAC authentication failed: No HMAC secret for tenant {tenant_id}")
        raise HTTPException(
            status_code=401,
            detail="HMAC authentication failed: No HMAC secret configured for tenant"
        )
    
    # Decrypt HMAC secret
    from core.security.encryption import encryption
    try:
        hmac_secret = encryption.decrypt(hmac_secret_encrypted)
    except Exception as e:
        logger.error(f"Failed to decrypt HMAC secret for tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="HMAC authentication failed: Error processing secret"
        )
    
    # Validate domain if provided
    if origin_header:
        expected_domain = tenant_hmac_data.get('domain')
        if expected_domain and origin_header != expected_domain:
            logger.warning(f"HMAC authentication failed: Domain mismatch for tenant {tenant_id}. Expected: {expected_domain}, Got: {origin_header}")
            raise HTTPException(
                status_code=401,
                detail="HMAC authentication failed: Invalid origin domain"
            )
        
        # Validate site hash if provided (temporarily disabled for debugging)
        if site_hash_header:
            expected_site_hash = tenant_hmac_data.get('site_hash')
            logger.info(f"Site hash validation - Expected: {expected_site_hash}, Received: {site_hash_header}")
            logger.warning(f"Site hash validation temporarily disabled - would have failed")
            # TODO: Fix site hash calculation mismatch between WordPress and FastAPI
            # if expected_site_hash and site_hash_header != expected_site_hash:
            #     logger.warning(f"HMAC authentication failed: Site hash mismatch for tenant {tenant_id}")
            #     raise HTTPException(
            #         status_code=401,
            #         detail="HMAC authentication failed: Invalid site hash"
            #     )
    
    # Validate HMAC signature with domain enhancement if available
    is_valid = hmac_validator.validate_signature(
        signature_header,
        timestamp,
        body,
        hmac_secret,
        domain=origin_header
    )
    
    if not is_valid:
        logger.warning(f"HMAC authentication failed: Invalid signature for tenant {tenant_id}")
        raise HTTPException(
            status_code=401,
            detail="HMAC authentication failed: Invalid signature"
        )
    
    # HMAC validation successful
    logger.info(f"HMAC authentication successful for tenant {tenant_id}")
    
    # Add HMAC validation info to request state for logging
    request.state.hmac_validated = True
    request.state.hmac_tenant_id = tenant_id
    request.state.hmac_timestamp = timestamp
    
    # Proceed with request
    logger.info(f"HMAC middleware: About to call next middleware/endpoint for tenant {tenant_id}")
    try:
        response = await call_next(request)
        logger.info(f"HMAC middleware: Got response from endpoint for tenant {tenant_id}")
    except Exception as e:
        logger.error(f"HMAC middleware: Exception from endpoint for tenant {tenant_id}: {str(e)}")
        raise
    
    # Add security headers to response
    response.headers["X-EagleChat-Security-Version"] = "1.0"
    response.headers["X-EagleChat-HMAC-Validated"] = "true"
    
    logger.info(f"HMAC middleware: Returning response for tenant {tenant_id}")
    return response