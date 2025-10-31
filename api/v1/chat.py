"""
Chat Endpoints
"""

import time
from fastapi import APIRouter, HTTPException
from core.validators import ChatRequest, ChatResponse
from database import db
from ai import ai_service, AIServiceError
from core.conversation_manager import conversation_manager
from core.logger import logger, context_logger

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests from WordPress tenants"""
    start_time = time.time()
    
    try:
        # Set context for this request
        context_logger.set_context(
            tenant_id=request.tenant_id,
            session_id=request.session_id,
            ai_model=request.ai_config.model
        )
        
        context_logger.log_tenant_activity(
            request.tenant_id, 
            "chat_request",
            session_id=request.session_id,
            message_length=len(request.message)
        )
        
        # Validate tenant credentials
        is_valid = await db.validate_tenant(request.tenant_id, request.api_key)
        if not is_valid:
            context_logger.log_tenant_activity(
                request.tenant_id,
                "auth_failed",
                reason="invalid_credentials"
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid tenant credentials"
            )
        
        # Log AI configuration for debugging
        context_logger.info("Processing chat request", 
                           temperature=request.ai_config.temperature,
                           max_tokens=request.ai_config.max_tokens,
                           memory_setting=request.ai_config.conversation_memory)
        
        # Use conversation history from request if provided, otherwise fetch it
        if request.conversation_history is not None:
            logger.info(f"Using conversation history from request: {len(request.conversation_history)} entries")
            conversation_history = request.conversation_history
        else:
            # Fallback: Retrieve conversation history based on memory settings
            logger.info("No conversation history in request, attempting to fetch from WordPress")
            conversation_history = await conversation_manager.get_conversation_history(
                tenant_id=request.tenant_id,
                session_id=request.session_id,
                memory_setting=request.ai_config.conversation_memory,
                max_tokens=request.ai_config.max_tokens
            )
        
        # Generate AI response
        response = await ai_service.generate_response(
            message=request.message,
            ai_config=request.ai_config,
            conversation_history=conversation_history,
            session_id=request.session_id,
            tenant_id=request.tenant_id
        )
        
        # Log performance and response metrics
        duration = (time.time() - start_time) * 1000
        context_logger.log_performance(
            "chat_request",
            duration,
            response_length=len(response.response),
            total_tokens=response.total_tokens
        )
        
        return response
        
    except HTTPException:
        raise
    except AIServiceError as e:
        context_logger.error("AI service error", 
                           error_code=e.error_code,
                           error_details=e.details)
        raise HTTPException(
            status_code=503,
            detail=f"AI service error: {e.message}"
        )
    except Exception as e:
        context_logger.error("Unexpected error in chat endpoint", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Internal server error during chat processing"
        )