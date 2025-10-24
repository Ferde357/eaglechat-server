import httpx
import asyncio
from typing import Optional
from logger import logger
from config import settings


class WordPressCallbackClient:
    """Handle WordPress callback verification with retry logic"""
    
    def __init__(self):
        self.retry_attempts = settings.callback.retry_attempts
        self.retry_delay = settings.callback.retry_delay_seconds
    
    async def verify_callback_token(self, site_url: str, callback_token: str) -> bool:
        """
        Verify the callback token with WordPress
        
        Args:
            site_url: The WordPress site URL
            callback_token: The token to verify
            
        Returns:
            True if verification successful, False otherwise
        """
        # Ensure site URL doesn't have trailing slash
        if site_url.endswith('/'):
            site_url = site_url[:-1]
        
        callback_url = f"{site_url}/wp-json/eaglechat-plugin/v1/verify"
        
        logger.info(f"Attempting to verify callback token with WordPress: {callback_url}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt in range(self.retry_attempts):
                try:
                    response = await client.post(
                        callback_url,
                        json={"callback_token": callback_token},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success", False):
                            logger.info(f"Callback token verified successfully for {site_url}")
                            return True
                        else:
                            logger.warning(f"WordPress rejected callback token for {site_url}: {result.get('message', 'Unknown error')}")
                            return False
                    else:
                        logger.warning(f"WordPress callback returned status {response.status_code} for {site_url}")
                        
                        # Don't retry on client errors (4xx)
                        if 400 <= response.status_code < 500:
                            return False
                            
                except httpx.RequestError as e:
                    logger.error(f"Request error during callback verification (attempt {attempt + 1}/{self.retry_attempts}): {str(e)}")
                except Exception as e:
                    logger.error(f"Unexpected error during callback verification: {str(e)}")
                
                # If this wasn't the last attempt, wait before retrying
                if attempt < self.retry_attempts - 1:
                    logger.info(f"Retrying callback verification in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
        
        logger.error(f"Failed to verify callback token after {self.retry_attempts} attempts for {site_url}")
        return False


# Create singleton instance
wp_client = WordPressCallbackClient()