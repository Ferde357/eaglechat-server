"""
HMAC Request Signature Validation
Provides cryptographic verification of request authenticity and integrity
"""

import hmac
import hashlib
import time
from typing import Optional, Tuple
from core.logger import logger


class HMACValidator:
    """HMAC signature validator for request authentication"""
    
    def __init__(self, hash_algorithm: str = 'sha256', timestamp_tolerance: int = 300):
        """
        Initialize HMAC validator
        
        Args:
            hash_algorithm: HMAC hash algorithm (sha256, sha512)
            timestamp_tolerance: Max age of request in seconds (5 minutes default)
        """
        self.hash_algorithm = hash_algorithm
        self.timestamp_tolerance = timestamp_tolerance
        
        # Validate hash algorithm
        if hash_algorithm not in ['sha256', 'sha512']:
            raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
            
        self.hash_func = getattr(hashlib, hash_algorithm)
    
    def generate_signature(self, timestamp: int, body: bytes, secret: str) -> str:
        """
        Generate HMAC signature for request data (legacy format)
        
        Args:
            timestamp: Unix timestamp when request was signed
            body: Request body as bytes
            secret: HMAC secret key
            
        Returns:
            HMAC signature in format "hmac-sha256=<hex_signature>"
        """
        try:
            # Create string to sign: timestamp + newline + body
            string_to_sign = f"{timestamp}\n".encode('utf-8') + body
            
            # Generate HMAC signature
            signature = hmac.new(
                secret.encode('utf-8'),
                string_to_sign,
                self.hash_func
            ).hexdigest()
            
            return f"hmac-{self.hash_algorithm}={signature}"
            
        except Exception as e:
            logger.error(f"Error generating HMAC signature: {str(e)}")
            raise
    
    def generate_signature_with_domain(self, timestamp: int, body: bytes, domain: str, secret: str) -> str:
        """
        Generate HMAC signature with domain verification
        
        Args:
            timestamp: Unix timestamp when request was signed
            body: Request body as bytes
            domain: Normalized domain for origin verification
            secret: HMAC secret key
            
        Returns:
            HMAC signature in format "hmac-sha256=<hex_signature>"
        """
        try:
            # Create string to sign: timestamp + newline + domain + newline + body
            string_to_sign = f"{timestamp}\n{domain}\n".encode('utf-8') + body
            
            # Generate HMAC signature
            signature = hmac.new(
                secret.encode('utf-8'),
                string_to_sign,
                self.hash_func
            ).hexdigest()
            
            return f"hmac-{self.hash_algorithm}={signature}"
            
        except Exception as e:
            logger.error(f"Error generating HMAC signature with domain: {str(e)}")
            raise
    
    def validate_signature(
        self, 
        signature: str, 
        timestamp: int, 
        body: bytes, 
        secret: str,
        domain: Optional[str] = None
    ) -> bool:
        """
        Validate HMAC signature against request data
        
        Args:
            signature: HMAC signature from request header
            timestamp: Unix timestamp from request header
            body: Request body as bytes
            secret: HMAC secret key for tenant
            domain: Optional domain for enhanced signature validation
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Validate timestamp first (fast check)
            if not self.is_timestamp_valid(timestamp):
                logger.warning(f"HMAC validation failed: Invalid timestamp {timestamp}")
                return False
            
            # Parse signature format
            expected_format = f"hmac-{self.hash_algorithm}="
            if not signature.startswith(expected_format):
                logger.warning(f"HMAC validation failed: Invalid signature format")
                return False
            
            # Generate expected signature - use domain-enhanced if domain provided
            if domain:
                expected_signature = self.generate_signature_with_domain(timestamp, body, domain, secret)
            else:
                expected_signature = self.generate_signature(timestamp, body, secret)
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error validating HMAC signature: {str(e)}")
            return False
    
    def is_timestamp_valid(self, timestamp: int) -> bool:
        """
        Check if timestamp is within acceptable tolerance
        
        Args:
            timestamp: Unix timestamp to validate
            
        Returns:
            True if timestamp is valid, False otherwise
        """
        current_time = int(time.time())
        time_diff = abs(current_time - timestamp)
        
        # Allow for clock skew and network delays
        return time_diff <= self.timestamp_tolerance
    
    def parse_signature_header(self, signature_header: str) -> Optional[Tuple[str, str]]:
        """
        Parse HMAC signature header
        
        Args:
            signature_header: Value of X-EagleChat-Signature header
            
        Returns:
            Tuple of (algorithm, signature) or None if invalid
        """
        try:
            if not signature_header:
                return None
                
            # Expected format: "hmac-sha256=abc123..."
            if '=' not in signature_header:
                return None
                
            prefix, signature = signature_header.split('=', 1)
            
            # Validate prefix format
            if not prefix.startswith('hmac-'):
                return None
                
            algorithm = prefix.split('-', 1)[1]
            
            # Validate algorithm
            if algorithm not in ['sha256', 'sha512']:
                return None
                
            return algorithm, signature
            
        except Exception as e:
            logger.error(f"Error parsing signature header: {str(e)}")
            return None


# Global HMAC validator instance
hmac_validator = HMACValidator()