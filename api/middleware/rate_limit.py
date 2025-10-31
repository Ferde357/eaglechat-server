"""
Rate Limiting Middleware
"""

import time
from collections import defaultdict
from threading import Lock
from fastapi import Request, HTTPException
from core.logger import context_logger

# Rate limiting storage
rate_limit_storage = defaultdict(list)
rate_limit_lock = Lock()


def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check for forwarded headers (if behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    return request.client.host if request.client else "unknown"


def check_rate_limit(ip: str, limit: int = 20, window: int = 60) -> bool:
    """
    Check if IP is within rate limit
    Args:
        ip: Client IP address
        limit: Maximum requests per window
        window: Time window in seconds
    Returns:
        True if within limit, False if exceeded
    """
    with rate_limit_lock:
        current_time = time.time()
        
        # Clean old entries
        rate_limit_storage[ip] = [
            timestamp for timestamp in rate_limit_storage[ip]
            if current_time - timestamp < window
        ]
        
        # Check if limit exceeded
        if len(rate_limit_storage[ip]) >= limit:
            return False
        
        # Add current request
        rate_limit_storage[ip].append(current_time)
        return True


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip rate limiting for health check
    if request.url.path == "/":
        return await call_next(request)
    
    client_ip = get_client_ip(request)
    
    # Check rate limit
    if not check_rate_limit(client_ip):
        context_logger.warning("Rate limit exceeded", 
                             client_ip=client_ip,
                             endpoint=request.url.path)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return await call_next(request)