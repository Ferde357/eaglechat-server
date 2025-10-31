"""
Anthropic Claude API Integration
"""

import asyncio
from typing import Dict, List, Tuple
import httpx

from .types import TokenUsage, AIServiceError
from ..utils.retry import retry_on_failure
from core.logger import logger


class AnthropicProvider:
    """Anthropic Claude API provider"""
    
    @retry_on_failure(max_retries=2, delay=1.0, backoff=2.0)
    async def generate_response(
        self,
        messages: List[Dict],
        model_name: str,
        temperature: float,
        max_tokens: int,
        tenant_id: str = None
    ) -> Tuple[str, TokenUsage]:
        """Call Anthropic Claude API"""
        # Require tenant-specific API key - no global fallback
        if not tenant_id:
            raise AIServiceError(
                "Tenant ID required for API calls",
                "MISSING_TENANT_ID"
            )
        
        from core.key_manager import key_manager
        api_key = await key_manager.get_tenant_key(tenant_id, 'anthropic')
        
        if not api_key:
            raise AIServiceError(
                "Anthropic API key not configured for this tenant",
                "MISSING_API_KEY"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01'
                }
                
                payload = {
                    'model': model_name,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'messages': messages
                }
                
                response = await client.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                    # Determine if error is retryable based on status code
                    retryable = response.status_code in [429, 500, 502, 503, 504]  # Rate limit, server errors
                    raise AIServiceError(
                        f"Anthropic API error: {response.status_code}",
                        "API_ERROR",
                        response.text,
                        retryable=retryable
                    )
                
                data = response.json()
                content = data['content'][0]['text']
                
                # Extract token usage
                usage_data = data.get('usage', {})
                usage = TokenUsage(
                    input_tokens=usage_data.get('input_tokens', 0),
                    output_tokens=usage_data.get('output_tokens', 0),
                    total_tokens=usage_data.get('input_tokens', 0) + usage_data.get('output_tokens', 0)
                )
                
                return content, usage
                
        except httpx.TimeoutException:
            logger.error("Anthropic API timeout")
            raise AIServiceError("AI service timeout", "TIMEOUT", retryable=True)
        except Exception as e:
            logger.error(f"Anthropic API call failed: {str(e)}")
            raise AIServiceError("AI service unavailable", "SERVICE_UNAVAILABLE", str(e), retryable=True)
    
    async def mock_response(
        self, 
        messages: List[Dict], 
        temperature: float, 
        max_tokens: int
    ) -> Tuple[str, TokenUsage]:
        """Mock Anthropic response for testing"""
        await asyncio.sleep(0.5)  # Simulate API delay
        
        last_message = messages[-1]['content'] if messages else ""
        
        # Generate mock response based on message content
        if "hello" in last_message.lower():
            response = "Hello! I'm Claude, and I'm here to help you with any questions you might have."
        elif "help" in last_message.lower():
            response = "I'd be happy to help! I can assist with a wide range of topics including answering questions, providing explanations, helping with writing, and much more. What would you like help with?"
        else:
            response = f"Thank you for your message. I understand you're asking about '{last_message[:50]}...'. This is a mock response from Claude Sonnet. In a real implementation, I would provide a thoughtful and helpful response based on my training."
        
        # Estimate tokens (rough approximation)
        input_tokens = sum(len(msg['content'].split()) for msg in messages) * 1.3
        output_tokens = len(response.split()) * 1.3
        
        usage = TokenUsage(
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            total_tokens=int(input_tokens + output_tokens)
        )
        
        return response, usage