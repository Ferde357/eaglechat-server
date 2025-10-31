"""
CORS Configuration
"""

from fastapi.middleware.cors import CORSMiddleware
from core.config import settings


def get_cors_origins():
    """Get CORS origins based on environment"""
    cors_origins = [
        "http://localhost",
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://localhost:8888",  # Common WordPress dev port
        "http://localhost:8000",  # WordPress local dev
        "http://localhost:10003",  # Your WordPress port
        "http://localhost:80",
        "https://localhost",
        "https://localhost:3000",
        "https://localhost:8080",
        "https://localhost:8888",
        "https://localhost:10003",  # Your WordPress port (HTTPS)
        # Add your WordPress site URLs here in production
        # "https://yourdomain.com",
        # "https://www.yourdomain.com"
    ]

    # In development mode, be more permissive with CORS
    if settings.api.development_mode:
        # Allow any localhost port in development
        cors_origins.extend([
            "http://localhost:3001",
            "http://localhost:4000",
            "http://localhost:5000",
            "http://localhost:8001",
            "http://localhost:8002",
            "http://localhost:8890",
            "http://localhost:9000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8080",
            "http://127.0.0.1:8888",
        ])
        # Also allow wildcard for development (very permissive)
        cors_origins.append("*")

    return cors_origins


def add_cors_middleware(app):
    """Add CORS middleware to FastAPI app"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],  # Add OPTIONS for CORS preflight
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],  # Add common headers
    )