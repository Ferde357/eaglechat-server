"""
API Key Validation Module
Validates API keys with actual provider endpoints before storage
"""

import httpx
import json
from typing import Dict, Optional, Tuple
from .logger import logger


class APIKeyValidator:
    """Validates API keys against provider endpoints"""
    
    @staticmethod
    async def validate_anthropic_key(api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Anthropic API key by making a minimal test request
        Returns (is_valid, error_message)
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01'
                }
                
                # Make a minimal test request
                payload = {
                    'model': 'claude-3-haiku-20240307',  # Use cheapest model for validation
                    'max_tokens': 1,  # Minimal tokens to reduce cost
                    'messages': [{'role': 'user', 'content': 'Hi'}]
                }
                
                response = await client.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("Anthropic API key validation successful")
                    return True, None
                elif response.status_code == 401:
                    return False, "Invalid Anthropic API key"
                elif response.status_code == 403:
                    return False, "Anthropic API key access forbidden"
                elif response.status_code == 429:
                    # Rate limited, but key is likely valid
                    logger.warning("Anthropic API rate limited during validation, assuming valid")
                    return True, None
                else:
                    error_text = response.text
                    logger.error(f"Anthropic API validation failed: {response.status_code} - {error_text}")
                    return False, f"Anthropic API error: {response.status_code}"
                
        except httpx.TimeoutException:
            logger.error("Anthropic API validation timeout")
            return False, "Anthropic API timeout during validation"
        except Exception as e:
            logger.error(f"Anthropic API validation error: {str(e)}")
            return False, f"Anthropic API validation failed: {str(e)}"
    
    @staticmethod
    async def validate_openai_key(api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate OpenAI API key by making a minimal test request
        Returns (is_valid, error_message)
        """
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
                
                # Make a minimal test request
                payload = {
                    'model': 'gpt-3.5-turbo',  # Use cheapest model for validation
                    'max_tokens': 1,  # Minimal tokens to reduce cost
                    'messages': [{'role': 'user', 'content': 'Hi'}]
                }
                
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("OpenAI API key validation successful")
                    return True, None
                elif response.status_code == 401:
                    return False, "Invalid OpenAI API key"
                elif response.status_code == 403:
                    return False, "OpenAI API key access forbidden"
                elif response.status_code == 429:
                    # Rate limited, but key is likely valid
                    logger.warning("OpenAI API rate limited during validation, assuming valid")
                    return True, None
                else:
                    error_text = response.text
                    logger.error(f"OpenAI API validation failed: {response.status_code} - {error_text}")
                    return False, f"OpenAI API error: {response.status_code}"
                
        except httpx.TimeoutException:
            logger.error("OpenAI API validation timeout")
            return False, "OpenAI API timeout during validation"
        except Exception as e:
            logger.error(f"OpenAI API validation error: {str(e)}")
            return False, f"OpenAI API validation failed: {str(e)}"
    
    @staticmethod
    async def validate_api_keys(anthropic_key: str = "", openai_key: str = "") -> Dict[str, any]:
        """
        Validate multiple API keys
        Returns validation results for each provider
        """
        results = {
            'anthropic': {'valid': False, 'error': None},
            'openai': {'valid': False, 'error': None},
            'any_valid': False
        }
        
        # Validate Anthropic key if provided
        if anthropic_key:
            is_valid, error = await APIKeyValidator.validate_anthropic_key(anthropic_key)
            results['anthropic'] = {'valid': is_valid, 'error': error}
            if is_valid:
                results['any_valid'] = True
        
        # Validate OpenAI key if provided
        if openai_key:
            is_valid, error = await APIKeyValidator.validate_openai_key(openai_key)
            results['openai'] = {'valid': is_valid, 'error': error}
            if is_valid:
                results['any_valid'] = True
        
        return results


# Global instance
api_key_validator = APIKeyValidator()