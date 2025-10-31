"""
Database Module for EagleChat
Handles all database operations via Supabase
"""

from .supabase_manager import SupabaseManager
from .tenant_ops import TenantOperations
from .api_key_ops import APIKeyOperations


class Database:
    """Unified database interface"""
    
    def __init__(self):
        self.supabase_manager = SupabaseManager()
        self.tenant_ops = TenantOperations(self.supabase_manager)
        self.api_key_ops = APIKeyOperations(self.supabase_manager)
    
    # Tenant operations
    async def register_tenant(self, tenant_id: str, api_key: str, site_url: str, admin_email: str, metadata=None):
        return await self.tenant_ops.register_tenant(tenant_id, api_key, site_url, admin_email, metadata)
    
    async def validate_tenant(self, tenant_id: str, api_key: str):
        return await self.tenant_ops.validate_tenant(tenant_id, api_key)
    
    async def check_existing_site(self, site_url: str):
        return await self.tenant_ops.check_existing_site(site_url)
    
    async def get_tenant_by_email(self, admin_email: str):
        return await self.tenant_ops.get_tenant_by_email(admin_email)
    
    # API key operations
    async def update_tenant_api_keys(self, tenant_id: str, anthropic_key_encrypted=None, openai_key_encrypted=None):
        return await self.api_key_ops.update_tenant_api_keys(tenant_id, anthropic_key_encrypted, openai_key_encrypted)
    
    async def get_tenant_api_keys(self, tenant_id: str):
        return await self.api_key_ops.get_tenant_api_keys(tenant_id)
    
    async def delete_tenant_api_keys(self, tenant_id: str):
        return await self.api_key_ops.delete_tenant_api_keys(tenant_id)
    
    async def remove_tenant_api_key(self, tenant_id: str, provider: str):
        return await self.api_key_ops.remove_tenant_api_key(tenant_id, provider)


# Create singleton instance
db = Database()

__all__ = ["Database", "db"]