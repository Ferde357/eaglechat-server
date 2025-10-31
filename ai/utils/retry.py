"""
Retry Decorator for AI Service Calls
"""

import asyncio
from ..models.types import AIServiceError
from core.logger import logger


class RetryOnFailure:
    """
    Class-based decorator for retrying failed API calls with exponential backoff.
    
    This decorator automatically retries async functions when they fail, using exponential
    backoff to gradually increase the delay between retry attempts. It handles both
    AIServiceError exceptions (which can specify whether they're retryable) and unexpected
    exceptions (which are converted to retryable AIServiceErrors).
    
    Args:
        max_retries (int, optional): Maximum number of retry attempts before giving up.
            Total attempts will be max_retries + 1 (original attempt + retries).
            Defaults to 3.
        delay (float, optional): Initial delay in seconds between retry attempts.
            This delay increases exponentially with each retry. Defaults to 1.0.
        backoff (float, optional): Multiplication factor for exponential backoff.
            Each retry delay = previous_delay * backoff. Defaults to 2.0.
    
    Returns:
        Decorated function that will automatically retry on failure according to the
        configured retry policy. The decorated function returns the same value as
        the original function on success, or raises the last exception encountered
        after all retries are exhausted.
    
    Raises:
        AIServiceError: When max retries are exceeded or a non-retryable error occurs.
        The original exception details are preserved in the AIServiceError.
    
    Example:
        @RetryOnFailure(max_retries=2, delay=1.0, backoff=2.0)
        async def api_call():
            # This will retry up to 2 times with delays of 1s, then 2s
            return await some_api_request()
    
    Note:
        - Non-retryable AIServiceErrors (retryable=False) will not be retried
        - Unexpected exceptions are converted to retryable AIServiceErrors
        - All retry attempts and failures are logged for debugging
    """
    
    def __init__(self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
        self.max_retries = max_retries
        self.delay = delay
        self.backoff = backoff
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = self.delay
            
            for attempt in range(self.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except AIServiceError as e:
                    last_exception = e
                    
                    if not e.retryable or attempt == self.max_retries:
                        if not e.retryable:
                            logger.warning(f"Non-retryable error in {func.__name__}: {e.message}")
                        else:
                            logger.error(f"Max retries ({self.max_retries}) exceeded in {func.__name__}: {e.message}")
                        raise
                    
                    logger.warning(f"Attempt {attempt + 1} failed in {func.__name__}: {e.message}. Retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= self.backoff
                    
                except Exception as e:
                    # Convert unexpected errors to AIServiceError
                    last_exception = AIServiceError(
                        "Unexpected error during API call",
                        "UNEXPECTED_ERROR", 
                        str(e),
                        retryable=True
                    )
                    
                    if attempt == self.max_retries:
                        logger.error(f"Max retries ({self.max_retries}) exceeded in {func.__name__}: {str(e)}")
                        raise last_exception
                    
                    logger.warning(f"Unexpected error in {func.__name__}: {str(e)}. Retrying in {current_delay}s...")
                    await asyncio.sleep(current_delay)
                    current_delay *= self.backoff
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper


# For backward compatibility, provide the original function interface
def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Function-based interface for backward compatibility"""
    return RetryOnFailure(max_retries=max_retries, delay=delay, backoff=backoff)