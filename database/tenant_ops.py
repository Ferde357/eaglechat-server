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
        metadata: Optional[Dict[str, Any]] = None,
        domain: Optional[str] = None,
        hmac_secret_encrypted: Optional[str] = None,
        site_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new tenant in the database"""
        try:
            # Call the register_tenant function with domain verification data
            result = self.client.rpc('register_tenant', {
                'p_tenant_id': tenant_id,
                'p_api_key': api_key,
                'p_site_url': site_url,
                'p_admin_email': admin_email,
                'p_metadata': metadata or {},
                'p_domain': domain,
                'p_hmac_secret_encrypted': hmac_secret_encrypted,
                'p_site_hash': site_hash
            }).execute()
            
            # Function now returns simple BOOLEAN - if we get here, it succeeded
            if result.data is True:
                return {
                    'success': True,
                    'tenant_id': tenant_id,
                    'message': 'Tenant registered successfully',
                    'hmac_configured': bool(hmac_secret_encrypted)
                }
            else:
                return {
                    'success': False,
                    'error': 'Registration returned false'
                }
            
        except Exception as e:
            # Function now raises exceptions for errors, so we can handle them properly
            error_message = str(e)
            logger.error(f"Failed to register tenant: {error_message}")
            
            return {
                'success': False,
                'error': error_message
            }
    
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
    
    async def store_tenant_hmac_secret(self, tenant_id: str, encrypted_secret: str) -> Dict[str, Any]:
        """Store encrypted HMAC secret for tenant"""
        try:
            result = self.client.table('tenants').update({
                'hmac_secret_encrypted': encrypted_secret,
                'hmac_secret_updated_at': 'now()'
            }).eq('id', tenant_id).execute()
            
            if result.data:
                logger.info(f"HMAC secret stored for tenant: {tenant_id}")
                return {'success': True, 'data': result.data[0]}
            else:
                logger.error(f"No tenant found with ID: {tenant_id}")
                return {'success': False, 'error': 'Tenant not found'}
            
        except Exception as e:
            logger.error(f"Failed to store HMAC secret for tenant {tenant_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_tenant_hmac_secret(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get encrypted HMAC secret for tenant"""
        try:
            result = self.client.table('tenants').select(
                'hmac_secret_encrypted, hmac_secret_updated_at'
            ).eq('id', tenant_id).execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"Failed to get HMAC secret for tenant {tenant_id}: {str(e)}")
            return None
    
    async def get_tenant_hmac_domain(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get HMAC secret and domain verification data for tenant"""
        try:
            # Call the get_tenant_hmac_domain function
            result = self.client.rpc('get_tenant_hmac_domain', {
                'p_tenant_id': tenant_id
            }).execute()
            
            if result.data and len(result.data) > 0:
                # Function returns table rows, take the first one
                tenant_data = result.data[0]
                return {
                    'success': True,
                    'hmac_secret_encrypted': tenant_data.get('hmac_secret_encrypted'),
                    'domain': tenant_data.get('domain'),
                    'site_hash': tenant_data.get('site_hash'),
                    'hmac_secret_updated_at': tenant_data.get('hmac_secret_updated_at')
                }
            else:
                return {'success': False, 'error': 'Tenant not found'}
            
        except Exception as e:
            logger.error(f"Failed to get HMAC domain data for tenant {tenant_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def delete_tenant_hmac_secret(self, tenant_id: str) -> Dict[str, Any]:
        """Delete HMAC secret for tenant"""
        try:
            result = self.client.table('tenants').update({
                'hmac_secret_encrypted': None,
                'hmac_secret_updated_at': None
            }).eq('id', tenant_id).execute()
            
            if result.data:
                logger.info(f"HMAC secret deleted for tenant: {tenant_id}")
                return {'success': True, 'data': result.data[0]}
            else:
                logger.error(f"No tenant found with ID: {tenant_id}")
                return {'success': False, 'error': 'Tenant not found'}
            
        except Exception as e:
            logger.error(f"Failed to delete HMAC secret for tenant {tenant_id}: {str(e)}")
            return {'success': False, 'error': str(e)}