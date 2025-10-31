"""
AI Model Types and Data Classes
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TokenUsage:
    """Token usage tracking"""
    input_tokens: int
    output_tokens: int
    total_tokens: int


class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    def __init__(self, message: str, error_code: str = "AI_ERROR", details: Optional[str] = None, retryable: bool = False):
        self.message = message
        self.error_code = error_code
        self.details = details
        self.retryable = retryable
        super().__init__(message)