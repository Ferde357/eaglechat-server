"""
Tenant Database Operations
"""

from typing import Optional, Dict, Any
from .supabase_manager import SupabaseManager
from core.logger import logger


class TenantOperations:
    """Handles tenant-related database operations"""
    
    def __init__(self, supabase_manager: SupabaseManager):
        self.client = supabase_manager.client
    
    async def register_tenant(
        self, 
        tenant_id: str, 
        api_key: str, 
        site_url: str, 
        admin_email: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register a new tenant in the database"""
        try:
            # Call the register_tenant function
            result = self.client.rpc('register_tenant', {
                'p_tenant_id': tenant_id,
                'p_api_key': api_key,
                'p_site_url': site_url,
                'p_admin_email': admin_email,
                'p_metadata': metadata or {}
            }).execute()
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to register tenant: {str(e)}")
            raise
    
    async def validate_tenant(self, tenant_id: str, api_key: str) -> bool:
        """Validate tenant credentials"""
        try:
            result = self.client.rpc('validate_tenant', {
                'p_tenant_id': tenant_id,
                'p_api_key': api_key
            }).execute()
            
            return result.data if result.data is not None else False
            
        except Exception as e:
            logger.error(f"Failed to validate tenant: {str(e)}")
            return False
    
    async def check_existing_site(self, site_url: str) -> bool:
        """Check if a site URL already exists"""
        try:
            # Normalize URL - remove trailing slash
            if site_url.endswith('/'):
                site_url = site_url[:-1]
            
            result = self.client.table('tenants').select('id').eq('site_url', site_url).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to check existing site: {str(e)}")
            raise
    
    async def get_tenant_by_email(self, admin_email: str) -> Optional[Dict[str, Any]]:
        """Get tenant information by admin email"""
        try:
            result = self.client.table('tenants').select('*').eq('admin_email', admin_email).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get tenant by email: {str(e)}")
            return None