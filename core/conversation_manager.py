"""
Conversation Memory Manager for EagleChat
Handles conversation history retrieval and context management
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import httpx
from .logger import logger
from .validators import AIConfig


@dataclass
class ConversationMessage:
    """Single conversation message"""
    user_message: str
    bot_response: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    timestamp: str


class ConversationManager:
    """Manages conversation memory and context for AI requests"""
    
    def __init__(self):
        self.memory_limits = {
            'short': 3,    # Last 3 exchanges
            'medium': 8,   # Last 8 exchanges  
            'long': 15     # Last 15 exchanges
        }
    
    async def get_conversation_history(
        self,
        tenant_id: str,
        session_id: str,
        memory_setting: str,
        max_tokens: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve conversation history for a session
        
        Args:
            tenant_id: Tenant UUID
            session_id: Chat session ID
            memory_setting: Memory setting (short/medium/long)
            max_tokens: Maximum tokens allowed for conversation context
            
        Returns:
            List of conversation messages for AI context
        """
        try:
            # Get exchange limit based on memory setting
            exchange_limit = self.memory_limits.get(memory_setting, 8)
            
            logger.info(f"Retrieving conversation history for session {session_id}, "
                       f"memory: {memory_setting}, limit: {exchange_limit}")
            
            # For now, we'll implement a mock conversation history
            # In production, this would query the WordPress database
            history = await self._fetch_conversation_from_wordpress(
                tenant_id, session_id, exchange_limit
            )
            
            # If max_tokens is specified, prune conversation to fit within token limit
            if max_tokens and history:
                history = self._prune_conversation_by_tokens(history, max_tokens)
            
            logger.info(f"Retrieved {len(history)} conversation messages for context")
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []  # Return empty history on error to continue processing
    
    async def _fetch_conversation_from_wordpress(
        self,
        tenant_id: str,
        session_id: str,
        limit: int
    ) -> List[Dict]:
        """
        Fetch conversation history from WordPress database via REST API
        """
        try:
            # Get tenant's API key for authentication
            from key_manager import key_manager
            from database import db
            
            # Get tenant data to verify credentials
            tenant_data = await db.get_tenant_api_keys(tenant_id)
            if not tenant_data:
                logger.warning(f"No tenant data found for {tenant_id}")
                return []
            
            api_key = tenant_data.get('api_key', '')
            if not api_key:
                logger.warning(f"No API key found for tenant {tenant_id}")
                return []
            
            # For now, use localhost since WordPress and FastAPI are on the same system
            # In production, this would be configurable per tenant
            # Try different common WordPress URLs
            possible_urls = [
                "http://localhost:8080",  # Common XAMPP/WAMP port
                "http://localhost",       # Standard HTTP
                "http://127.0.0.1",      # Localhost IP
                "http://localhost:80"    # Explicit port 80
            ]
            
            wordpress_base_url = possible_urls[0]  # Start with most common
            
            # Construct the REST API endpoint
            api_endpoint = f"{wordpress_base_url}/wp-json/eaglechat-plugin/v1/conversation-history"
            
            # Prepare the request data
            request_data = {
                'tenant_id': tenant_id,
                'api_key': api_key,
                'session_id': session_id,
                'limit': limit
            }
            
            # Enhanced debugging and API call to WordPress
            logger.info(f"Attempting to fetch conversation history for session {session_id[:8]}... from {api_endpoint}")
            logger.info(f"Request data: tenant_id={tenant_id}, session_id={session_id[:8]}..., limit={limit}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await client.post(
                        api_endpoint,
                        json=request_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    logger.info(f"WordPress API response: HTTP {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"WordPress API response data: {data}")
                        
                        if data.get('success') and 'conversations' in data:
                            conversations = data['conversations']
                            logger.info(f"SUCCESS: Retrieved {len(conversations)} conversation entries for session {session_id[:8]}...")
                            
                            # Log the actual conversations for debugging
                            for i, conv in enumerate(conversations):
                                logger.info(f"  Conversation {i+1}: User='{conv.get('user_message', '')[:50]}...', Bot='{conv.get('bot_response', '')[:50]}...'")
                            
                            return conversations
                        else:
                            logger.warning(f"WordPress API returned success=false or no conversations: {data}")
                            return []
                            
                    elif response.status_code == 404:
                        logger.info(f"WordPress API returned 404 - no conversation history found for session {session_id[:8]}...")
                        return []
                        
                    else:
                        logger.error(f"WordPress API error: HTTP {response.status_code}")
                        logger.error(f"Response text: {response.text}")
                        return []
                        
                except httpx.ConnectError as e:
                    logger.error(f"Failed to connect to WordPress at {api_endpoint}: {e}")
                    logger.error("This might indicate WordPress is not running or accessible at this URL")
                    return []
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching conversation from WordPress for tenant {tenant_id}")
            return []
        except Exception as e:
            logger.error(f"Error fetching conversation from WordPress: {str(e)}")
            return []
    
    def _prune_conversation_by_tokens(
        self,
        conversation: List[Dict],
        max_tokens: int
    ) -> List[Dict]:
        """
        Prune conversation history to fit within token limits
        
        Args:
            conversation: List of conversation messages
            max_tokens: Maximum tokens allowed
            
        Returns:
            Pruned conversation list that fits within token limit
        """
        if not conversation:
            return conversation
        
        # Reserve some tokens for the new response (estimated)
        reserved_tokens = max_tokens // 4  # Reserve 25% for response
        available_tokens = max_tokens - reserved_tokens
        
        # Calculate tokens for each message
        total_tokens = 0
        pruned_conversation = []
        
        # Start from the most recent messages and work backwards
        for message in reversed(conversation):
            message_tokens = message.get('total_tokens', 0)
            
            # Estimate tokens if not available
            if message_tokens == 0:
                user_tokens = len(message.get('user_message', '').split()) * 1.3
                bot_tokens = len(message.get('bot_response', '').split()) * 1.3
                message_tokens = int(user_tokens + bot_tokens)
            
            if total_tokens + message_tokens <= available_tokens:
                total_tokens += message_tokens
                pruned_conversation.insert(0, message)  # Insert at beginning to maintain order
            else:
                logger.info(f"Pruned conversation to {len(pruned_conversation)} messages "
                           f"({total_tokens} tokens) to fit within {available_tokens} token limit")
                break
        
        return pruned_conversation
    
    def estimate_conversation_tokens(self, conversation: List[Dict]) -> int:
        """
        Estimate total tokens in conversation history
        
        Args:
            conversation: List of conversation messages
            
        Returns:
            Estimated total tokens
        """
        total_tokens = 0
        
        for message in conversation:
            if 'total_tokens' in message and message['total_tokens'] > 0:
                total_tokens += message['total_tokens']
            else:
                # Estimate if actual token count not available
                user_tokens = len(message.get('user_message', '').split()) * 1.3
                bot_tokens = len(message.get('bot_response', '').split()) * 1.3
                total_tokens += int(user_tokens + bot_tokens)
        
        return total_tokens


# Global conversation manager instance
conversation_manager = ConversationManager()