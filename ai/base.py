"""
AI Service Main Class
Handles integration with various AI APIs (Claude, OpenAI)
"""

import time
from typing import Dict, List, Optional

from .models.types import AIServiceError
from .models.anthropic import AnthropicProvider
from .models.openai import OpenAIProvider
from .services.conversation import build_conversation_context, log_conversation_debug
from .utils.config import MODEL_CONFIGS
from core.logger import logger, context_logger
from core.validators import AIConfig, ChatResponse


class AIService:
    """Main AI service class for handling different AI providers"""
    
    def __init__(self):
        # No global API keys - all keys come from tenants
        # This prevents accidentally billing our account for customer usage
        
        self.model_configs = MODEL_CONFIGS
        self.anthropic = AnthropicProvider()
        self.openai = OpenAIProvider()
    
    async def generate_response(
        self, 
        message: str, 
        ai_config: AIConfig,
        conversation_history: Optional[List[Dict]] = None,
        session_id: str = None,
        tenant_id: str = None
    ) -> ChatResponse:
        """
        Generate AI response based on configuration
        
        Args:
            message: User message
            ai_config: AI configuration settings
            conversation_history: Previous conversation messages
            session_id: Chat session identifier
            
        Returns:
            ChatResponse with AI response and token usage
        """
        try:
            start_time = time.time()
            
            context_logger.info("Starting AI response generation", 
                              model=ai_config.model,
                              temperature=ai_config.temperature)
            
            # Get model configuration
            if ai_config.model not in self.model_configs:
                raise AIServiceError(
                    f"Unsupported model: {ai_config.model}",
                    "UNSUPPORTED_MODEL"
                )
            
            model_config = self.model_configs[ai_config.model]
            provider = model_config['provider']
            
            # Build conversation context
            messages = build_conversation_context(message, conversation_history)
            context_logger.info("Built conversation context", 
                              message_count=len(messages),
                              history_entries=len(conversation_history) if conversation_history else 0)
            
            # Enhanced debugging for conversation context
            log_conversation_debug(message, conversation_history, messages)
            
            # Calculate max tokens
            max_tokens = ai_config.max_tokens or model_config['max_tokens_default']
            
            # Route to appropriate provider
            if provider == 'anthropic':
                response, usage = await self.anthropic.generate_response(
                    messages=messages,
                    model_name=model_config['model_name'],
                    temperature=ai_config.temperature,
                    max_tokens=max_tokens,
                    tenant_id=tenant_id
                )
            elif provider == 'openai':
                response, usage = await self.openai.generate_response(
                    messages=messages,
                    model_name=model_config['model_name'],
                    temperature=ai_config.temperature,
                    max_tokens=max_tokens,
                    tenant_id=tenant_id
                )
            else:
                raise AIServiceError(
                    f"Unsupported provider: {provider}",
                    "UNSUPPORTED_PROVIDER"
                )
            
            # Log AI request completion
            duration = (time.time() - start_time) * 1000
            context_logger.log_ai_request(
                model=ai_config.model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                duration=duration
            )
            
            return ChatResponse(
                response=response,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                total_tokens=usage.total_tokens,
                model_used=ai_config.model,
                finish_reason="stop",
                session_id=session_id
            )
            
        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AI service: {str(e)}")
            raise AIServiceError(
                "Internal AI service error",
                "INTERNAL_ERROR",
                str(e)
            )