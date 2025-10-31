"""
Conversation Context Building and Management
"""

from typing import Dict, List, Optional
from core.logger import logger


def build_conversation_context(
    current_message: str, 
    history: Optional[List[Dict]] = None
) -> List[Dict]:
    """Build conversation context for AI API"""
    messages = []
    
    # Add conversation history
    if history:
        for msg in history:
            # Add user message
            if msg.get('user_message'):
                messages.append({
                    'role': 'user',
                    'content': msg['user_message']
                })
            # Add assistant response
            if msg.get('bot_response'):
                messages.append({
                    'role': 'assistant', 
                    'content': msg['bot_response']
                })
    
    # Add current message
    messages.append({
        'role': 'user',
        'content': current_message
    })
    
    return messages


def log_conversation_debug(message: str, conversation_history: Optional[List[Dict]] = None, messages: List[Dict] = None):
    """Enhanced debugging for conversation context"""
    logger.info(f"=== CONVERSATION CONTEXT DEBUG ===")
    logger.info(f"Current message: {message}")
    logger.info(f"Conversation history provided: {len(conversation_history) if conversation_history else 0} entries")
    
    if conversation_history:
        for i, entry in enumerate(conversation_history):
            logger.info(f"  History {i+1}: User='{entry.get('user_message', '')[:50]}...', Bot='{entry.get('bot_response', '')[:50]}...'")
    
    if messages:
        logger.info(f"Final messages for AI: {len(messages)} total")
        for i, msg in enumerate(messages):
            logger.info(f"  Message {i+1} ({msg['role']}): {msg['content'][:100]}...")
    logger.info(f"=== END CONVERSATION CONTEXT DEBUG ===")