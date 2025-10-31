a"""
OpenAI GPT API Integration
"""

import asyncio
from typing import Dict, List, Tuple
import httpx

from .types import TokenUsage, AIServiceError
from ..utils.retry import retry_on_failure
from core.logger import logger


class OpenAIProvider:
    """OpenAI GPT API provider"""
    
    @retry_on_failure(max_retries=2, delay=1.0, backoff=2.0)
    async def generate_response(
        self,
        messages: List[Dict],
        model_name: str, 
        temperature: float,
        max_tokens: int,
        tenant_id: str = None
    ) -> Tuple[str, TokenUsage]:
        """Call OpenAI GPT API"""
        # Require tenant-specific API key - no global fallback
        if not tenant_id:
            raise AIServiceError(
                "Tenant ID required for API calls",
                "MISSING_TENANT_ID"
            )
        
        from core.key_manager import key_manager
        api_key = await key_manager.get_tenant_key(tenant_id, 'openai')
        
        if not api_key:
            raise AIServiceError(
                "OpenAI API key not configured for this tenant",
                "MISSING_API_KEY"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
                
                payload = {
                    'model': model_name,
                    'messages': messages,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
                
                response = await client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    # Determine if error is retryable based on status code
                    retryable = response.status_code in [429, 500, 502, 503, 504]  # Rate limit, server errors
                    raise AIServiceError(
                        f"OpenAI API error: {response.status_code}",
                        "API_ERROR", 
                        response.text,
                        retryable=retryable
                    )
                
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # Extract token usage
                usage_data = data.get('usage', {})
                usage = TokenUsage(
                    input_tokens=usage_data.get('prompt_tokens', 0),
                    output_tokens=usage_data.get('completion_tokens', 0),
                    total_tokens=usage_data.get('total_tokens', 0)
                )
                
                return content, usage
                
        except httpx.TimeoutException:
            logger.error("OpenAI API timeout")
            raise AIServiceError("AI service timeout", "TIMEOUT", retryable=True)
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise AIServiceError("AI service unavailable", "SERVICE_UNAVAILABLE", str(e), retryable=True)
    
    async def mock_response(
        self, 
        messages: List[Dict], 
        temperature: float, 
        max_tokens: int
    ) -> Tuple[str, TokenUsage]:
        """Mock OpenAI response for testing"""
        await asyncio.sleep(0.3)  # Simulate API delay
        
        last_message = messages[-1]['content'] if messages else ""
        
        # Generate mock response based on message content
        if "hello" in last_message.lower():
            response = "Hello! I'm an AI assistant powered by OpenAI. How can I help you today?"
        elif "help" in last_message.lower():
            response = "I'm here to help! I can assist with answering questions, creative writing, analysis, coding, and many other tasks. What do you need help with?"
        else:
            response = f"I see you've asked about '{last_message[:50]}...'. This is a mock response from the OpenAI model. In production, I would provide a detailed and helpful response based on my training data."
        
        # Estimate tokens (rough approximation)
        input_tokens = sum(len(msg['content'].split()) for msg in messages) * 1.2
        output_tokens = len(response.split()) * 1.2
        
        usage = TokenUsage(
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens), 
            total_tokens=int(input_tokens + output_tokens)
        )
        
        return response, usage