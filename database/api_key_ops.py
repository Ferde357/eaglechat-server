"""
API Key Database Operations
"""

from typing import Optional, Dict, Any
from .supabase_manager import SupabaseManager
from core.logger import logger


class APIKeyOperations:
    """Handles API key-related database operations"""
    
    def __init__(self, supabase_manager: SupabaseManager):
        self.client = supabase_manager.client
    
    async def update_tenant_api_keys(
        self, 
        tenant_id: str, 
        anthropic_key_encrypted: Optional[str] = None,
        openai_key_encrypted: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update encrypted API keys for a tenant"""
        try:
            result = self.client.rpc('update_tenant_api_keys', {
                'p_tenant_id': tenant_id,
                'p_anthropic_key_encrypted': anthropic_key_encrypted,
                'p_openai_key_encrypted': openai_key_encrypted
            }).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to update tenant API keys: {str(e)}")
            raise
    
    async def get_tenant_api_keys(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get encrypted API keys for a tenant"""
        try:
            result = self.client.rpc('get_tenant_api_keys', {
                'p_tenant_id': tenant_id
            }).execute()
            
            logger.info(f"Raw Supabase response for get_tenant_api_keys: {result.data}")
            
            if result.data and result.data.get('success'):
                return result.data.get('data')
            else:
                logger.warning(f"get_tenant_api_keys failed or returned no data: {result.data}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get tenant API keys: {str(e)}")
            return None
    
    async def delete_tenant_api_keys(self, tenant_id: str) -> Dict[str, Any]:
        """Delete encrypted API keys for a tenant"""
        try:
            result = self.client.rpc('delete_tenant_api_keys', {
                'p_tenant_id': tenant_id
            }).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to delete tenant API keys: {str(e)}")
            raise
    
    async def remove_tenant_api_key(self, tenant_id: str, provider: str) -> Dict[str, Any]:
        """Remove a specific API key for a tenant"""
        try:
            result = self.client.rpc('remove_tenant_api_key', {
                'p_tenant_id': tenant_id,
                'p_provider': provider
            }).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to remove tenant API key: {str(e)}")
            raise