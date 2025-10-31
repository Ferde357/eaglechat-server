"""
AI Service Module for EagleChat
Handles integration with various AI APIs (Claude, OpenAI)
"""

from .base import AIService
from .models.types import AIServiceError, TokenUsage

# Global AI service instance
ai_service = AIService()

__all__ = ["AIService", "AIServiceError", "TokenUsage", "ai_service"]