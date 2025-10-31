"""
Health Check Endpoints
"""

from fastapi import APIRouter
from core.config import settings

router = APIRouter()


@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.api.title,
        "version": settings.api.version,
        "development_mode": settings.api.development_mode
    }