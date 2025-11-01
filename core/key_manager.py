"""
Secure API Key Management for FastAPI Server
Handles per-tenant encrypted storage of AI API keys in Supabase
"""

import os
import json
import hashlib
from typing import Optional, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from .logger import logger

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If dotenv not available, manually load .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


class SecureKeyManager:
    """Secure API key storage and management using Supabase"""
    
    def __init__(self):
        self._encryption_key = self._get_or_create_master_key()
        self._cipher = Fernet(self._encryption_key)
        # Cache for performance (still fetch from DB for persistence)
        self._cache: Dict[str, Dict[str, str]] = {}
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        master_key = os.getenv('EAGLECHAT_MASTER_KEY')
        
        if not master_key:
            # Generate new master key
            master_key = Fernet.generate_key().decode()
            logger.warning("No master key found. Generated new key. "
                         "Set EAGLECHAT_MASTER_KEY environment variable for persistence.")
            # In production, this should be stored securely
            os.environ['EAGLECHAT_MASTER_KEY'] = master_key
        
        # Derive encryption key from master key
        if isinstance(master_key, str):
            master_key = master_key.encode()
        
        # Use tenant-specific salt for additional security
        salt = b'eaglechat_salt_v1'  # In production, use random salt per tenant
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key))
        return key
    
    async def store_tenant_keys(self, tenant_id: str, anthropic_key: str = "", openai_key: str = "") -> bool:
        """Store encrypted API keys for a tenant in Supabase"""
        try:
            # Import here to avoid circular imports
            from database import db
            
            # Encrypt keys if provided
            anthropic_encrypted = None
            openai_encrypted = None
            
            if anthropic_key:
                anthropic_encrypted = self._cipher.encrypt(anthropic_key.encode()).decode()
            
            if openai_key:
                openai_encrypted = self._cipher.encrypt(openai_key.encode()).decode()
            
            # Store in Supabase
            result = await db.update_tenant_api_keys(
                tenant_id=tenant_id,
                anthropic_key_encrypted=anthropic_encrypted,
                openai_key_encrypted=openai_encrypted
            )
            
            if result.get('success'):
                # Update cache
                cache_entry = {}
                if anthropic_encrypted:
                    cache_entry['anthropic'] = anthropic_encrypted
                if openai_encrypted:
                    cache_entry['openai'] = openai_encrypted
                self._cache[tenant_id] = cache_entry
                
                logger.info(f"API keys stored securely in Supabase for tenant: {tenant_id}")
                return True
            else:
                logger.error(f"Failed to store API keys in Supabase: {result.get('error')}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to store API keys for tenant {tenant_id}: {str(e)}")
            return False
    
    async def get_tenant_key(self, tenant_id: str, provider: str) -> Optional[str]:
        """Retrieve and decrypt API key for a tenant from Supabase"""
        try:
            # Check cache first
            if tenant_id in self._cache:
                encrypted_key = self._cache[tenant_id].get(provider)
                if encrypted_key:
                    decrypted_key = self._cipher.decrypt(encrypted_key.encode()).decode()
                    return decrypted_key
            
            # Import here to avoid circular imports
            from database import db
            
            # Fetch from Supabase
            tenant_data = await db.get_tenant_api_keys(tenant_id)
            logger.info(f"Fetched tenant data for {tenant_id}: {tenant_data}")
            if not tenant_data:
                logger.warning(f"No tenant data found for {tenant_id}")
                return None
            
            # Get the appropriate encrypted key
            encrypted_key = None
            if provider == 'anthropic':
                encrypted_key = tenant_data.get('anthropic_api_key_encrypted')
            elif provider == 'openai':
                encrypted_key = tenant_data.get('openai_api_key_encrypted')
            
            if not encrypted_key:
                return None
            
            # Update cache
            if tenant_id not in self._cache:
                self._cache[tenant_id] = {}
            self._cache[tenant_id][provider] = encrypted_key
            
            # Decrypt and return
            try:
                decrypted_key = self._cipher.decrypt(encrypted_key.encode()).decode()
                logger.info(f"Successfully decrypted {provider} key for tenant {tenant_id}")
                return decrypted_key
            except Exception as decrypt_error:
                logger.error(f"Decryption failed for {provider} key: {str(decrypt_error)}")
                logger.error(f"Encrypted key length: {len(encrypted_key)}")
                raise
            
        except Exception as e:
            logger.error(f"Failed to retrieve API key for tenant {tenant_id}, provider {provider}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {e}")
            return None
    
    async def has_tenant_key(self, tenant_id: str, provider: str) -> bool:
        """Check if tenant has a key for the provider"""
        try:
            # Check cache first
            if tenant_id in self._cache and provider in self._cache[tenant_id]:
                return True
            
            # Check Supabase
            from database import db
            tenant_data = await db.get_tenant_api_keys(tenant_id)
            if not tenant_data:
                return False
            
            # Check if the specific provider key exists
            if provider == 'anthropic':
                return tenant_data.get('anthropic_api_key_encrypted') is not None
            elif provider == 'openai':
                return tenant_data.get('openai_api_key_encrypted') is not None
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check tenant key for {tenant_id}, provider {provider}: {str(e)}")
            return False
    
    async def delete_tenant_keys(self, tenant_id: str) -> bool:
        """Delete all keys for a tenant from Supabase"""
        try:
            from database import db
            
            # Delete from Supabase
            result = await db.delete_tenant_api_keys(tenant_id)
            
            if result.get('success'):
                # Remove from cache
                if tenant_id in self._cache:
                    del self._cache[tenant_id]
                logger.info(f"API keys deleted from Supabase for tenant: {tenant_id}")
                return True
            else:
                logger.error(f"Failed to delete API keys from Supabase: {result.get('error')}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to delete API keys for tenant {tenant_id}: {str(e)}")
            return False
    
    def get_key_hash(self, api_key: str) -> str:
        """Generate secure hash of API key for verification"""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    
    def rotate_tenant_keys(self, tenant_id: str) -> bool:
        """Rotate encryption for a tenant's keys (re-encrypt with new key)"""
        try:
            if tenant_id not in self._tenant_keys:
                return True  # Nothing to rotate
            
            # Decrypt with old key, encrypt with new key
            old_keys = {}
            for provider, encrypted_key in self._tenant_keys[tenant_id].items():
                decrypted_key = self._cipher.decrypt(encrypted_key.encode()).decode()
                old_keys[provider] = decrypted_key
            
            # Re-encrypt
            encrypted_keys = {}
            for provider, key in old_keys.items():
                encrypted_keys[provider] = self._cipher.encrypt(key.encode()).decode()
            
            self._tenant_keys[tenant_id] = encrypted_keys
            
            logger.info(f"API keys rotated for tenant: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate API keys for tenant {tenant_id}: {str(e)}")
            return False
    
    async def store_tenant_hmac_secret(self, tenant_id: str, hmac_secret: str) -> bool:
        """Store encrypted HMAC secret for tenant"""
        try:
            # Encrypt the HMAC secret
            encrypted_secret = self._encrypt_key(hmac_secret)
            
            # Store in Supabase
            from database import db
            result = await db.store_tenant_hmac_secret(tenant_id, encrypted_secret)
            
            if result.get('success'):
                # Update cache
                if tenant_id not in self._cache:
                    self._cache[tenant_id] = {}
                self._cache[tenant_id]['hmac_secret'] = hmac_secret
                
                logger.info(f"HMAC secret stored for tenant: {tenant_id}")
                return True
            else:
                logger.error(f"Failed to store HMAC secret in Supabase for tenant {tenant_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to store HMAC secret for tenant {tenant_id}: {str(e)}")
            return False
    
    async def get_tenant_hmac_secret(self, tenant_id: str) -> Optional[str]:
        """Retrieve and decrypt HMAC secret for tenant"""
        try:
            # Check cache first
            if tenant_id in self._cache and 'hmac_secret' in self._cache[tenant_id]:
                return self._cache[tenant_id]['hmac_secret']
            
            # Fetch from Supabase
            from database import db
            tenant_data = await db.get_tenant_hmac_secret(tenant_id)
            if not tenant_data or not tenant_data.get('hmac_secret_encrypted'):
                return None
            
            # Decrypt the secret
            encrypted_secret = tenant_data['hmac_secret_encrypted']
            decrypted_secret = self._decrypt_key(encrypted_secret)
            
            # Cache the decrypted secret
            if tenant_id not in self._cache:
                self._cache[tenant_id] = {}
            self._cache[tenant_id]['hmac_secret'] = decrypted_secret
            
            return decrypted_secret
            
        except Exception as e:
            logger.error(f"Failed to retrieve HMAC secret for tenant {tenant_id}: {str(e)}")
            return None
    
    async def generate_tenant_hmac_secret(self, tenant_id: str) -> Optional[str]:
        """Generate new HMAC secret for tenant"""
        try:
            import secrets
            
            # Generate cryptographically secure random secret (32 bytes = 64 hex chars)
            hmac_secret = secrets.token_hex(32)
            
            # Store the secret
            success = await self.store_tenant_hmac_secret(tenant_id, hmac_secret)
            
            if success:
                logger.info(f"Generated new HMAC secret for tenant: {tenant_id}")
                return hmac_secret
            else:
                logger.error(f"Failed to store generated HMAC secret for tenant: {tenant_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate HMAC secret for tenant {tenant_id}: {str(e)}")
            return None
    
    async def rotate_tenant_hmac_secret(self, tenant_id: str) -> Optional[str]:
        """Generate new HMAC secret for tenant (alias for generate_tenant_hmac_secret)"""
        return await self.generate_tenant_hmac_secret(tenant_id)
    
    async def has_tenant_hmac_secret(self, tenant_id: str) -> bool:
        """Check if tenant has HMAC secret configured"""
        try:
            # Check cache first
            if tenant_id in self._cache and 'hmac_secret' in self._cache[tenant_id]:
                return True
            
            # Check Supabase
            from database import db
            tenant_data = await db.get_tenant_hmac_secret(tenant_id)
            return tenant_data and tenant_data.get('hmac_secret_encrypted') is not None
            
        except Exception as e:
            logger.error(f"Failed to check HMAC secret for tenant {tenant_id}: {str(e)}")
            return False
    
    async def delete_tenant_hmac_secret(self, tenant_id: str) -> bool:
        """Delete HMAC secret for tenant"""
        try:
            from database import db
            
            # Delete from Supabase
            result = await db.delete_tenant_hmac_secret(tenant_id)
            
            if result.get('success'):
                # Remove from cache
                if tenant_id in self._cache and 'hmac_secret' in self._cache[tenant_id]:
                    del self._cache[tenant_id]['hmac_secret']
                logger.info(f"HMAC secret deleted for tenant: {tenant_id}")
                return True
            else:
                logger.error(f"Failed to delete HMAC secret from Supabase for tenant {tenant_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete HMAC secret for tenant {tenant_id}: {str(e)}")
            return False

    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, bool]:
        """Get statistics about tenant's configured keys"""
        try:
            anthropic_configured = await self.has_tenant_key(tenant_id, 'anthropic')
            openai_configured = await self.has_tenant_key(tenant_id, 'openai')
            hmac_configured = await self.has_tenant_hmac_secret(tenant_id)
            
            total_providers = 0
            if anthropic_configured:
                total_providers += 1
            if openai_configured:
                total_providers += 1
            
            return {
                'anthropic_configured': anthropic_configured,
                'openai_configured': openai_configured,
                'hmac_configured': hmac_configured,
                'total_providers': total_providers
            }
        except Exception as e:
            logger.error(f"Failed to get tenant stats for {tenant_id}: {str(e)}")
            return {
                'anthropic_configured': False,
                'openai_configured': False,
                'hmac_configured': False,
                'total_providers': 0
            }


# Global instance
key_manager = SecureKeyManager()