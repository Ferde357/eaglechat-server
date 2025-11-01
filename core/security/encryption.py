"""
Encryption utilities for sensitive data
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from core.config import settings
from core.logger import logger


class Encryption:
    """Handle encryption/decryption of sensitive data"""
    
    def __init__(self):
        """Initialize encryption with key derived from settings"""
        self._fernet = self._get_fernet()
    
    def _get_fernet(self) -> Fernet:
        """Create Fernet instance with derived key"""
        # Use a combination of secret key and salt for key derivation
        key_material = f"{settings.api.secret_key}:hmac_encryption".encode()
        
        # Derive a proper 32-byte key for Fernet
        key = hashlib.pbkdf2_hmac('sha256', key_material, b'salt_hmac_2024', 100000)
        fernet_key = base64.urlsafe_b64encode(key)
        
        return Fernet(fernet_key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        try:
            if not data:
                return ""
            
            # Convert to bytes and encrypt
            data_bytes = data.encode('utf-8')
            encrypted_bytes = self._fernet.encrypt(data_bytes)
            
            # Return base64 encoded string
            return base64.b64encode(encrypted_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded data and return original string"""
        try:
            if not encrypted_data:
                return ""
            
            # Decode base64 and decrypt
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Return original string
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def generate_site_hash(self, domain: str, tenant_id: str) -> str:
        """Generate site verification hash"""
        try:
            # Combine domain, tenant_id, and secret for uniqueness
            hash_data = f"{domain}|{tenant_id}|{settings.api.secret_key}".encode('utf-8')
            
            # Generate SHA256 hash
            site_hash = hashlib.sha256(hash_data).hexdigest()
            
            return site_hash
            
        except Exception as e:
            logger.error(f"Site hash generation failed: {str(e)}")
            raise


# Global encryption instance
encryption = Encryption()