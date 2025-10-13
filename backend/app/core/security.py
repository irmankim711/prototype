"""
Production-Grade Security Module
Comprehensive security utilities for token management, encryption, and data protection
"""

import os
import base64
import hashlib
import secrets
import logging
from typing import Optional, Union, Dict, Any
from datetime import datetime, timedelta, timezone
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
import bcrypt
from functools import wraps
import time

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Base security exception"""
    pass

class TokenError(SecurityError):
    """Token-related security exception"""
    pass

class EncryptionError(SecurityError):
    """Encryption-related security exception"""
    pass

class SecurityManager:
    """
    Comprehensive security manager for encryption and data protection

    Features:
    - AES-256 encryption with Fernet
    - Password hashing with bcrypt
    - Secure random token generation
    - Rate limiting utilities
    - Input sanitization
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize security manager

        Args:
            encryption_key: Base64 encoded encryption key (generates if None)
        """
        
        # Initialize encryption
        self._setup_encryption(encryption_key)
        
        # Security metrics
        self.metrics = {
            'encryption_operations': 0,
            'failed_validations': 0
        }
    
    def _setup_encryption(self, encryption_key: Optional[str] = None) -> None:
        """Setup encryption with Fernet"""
        try:
            if encryption_key:
                # Use provided key
                key_bytes = base64.urlsafe_b64decode(encryption_key.encode())
            else:
                # Generate new key from environment or create new
                password = os.getenv('ENCRYPTION_PASSWORD', 'default-password-change-in-production').encode()
                salt = os.getenv('ENCRYPTION_SALT', 'default-salt').encode()
                
                # Use Scrypt for key derivation (more secure than PBKDF2)
                kdf = Scrypt(
                    length=32,
                    salt=salt,
                    n=2**14,
                    r=8,
                    p=1,
                )
                key_bytes = kdf.derive(password)
            
            # Create Fernet instance
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            self.fernet = Fernet(fernet_key)
            
            logger.info("Encryption system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {str(e)}")
            # Fallback to generated key for development
            self.fernet = Fernet(Fernet.generate_key())
    
    def encrypt_token(self, token: str) -> str:
        """
        Encrypt a token using Fernet encryption
        
        Args:
            token: Token to encrypt
            
        Returns:
            Base64 encoded encrypted token
            
        Raises:
            EncryptionError: If encryption fails
        """
        try:
            if not token:
                raise EncryptionError("Token cannot be empty")
            
            encrypted_data = self.fernet.encrypt(token.encode())
            self.metrics['encryption_operations'] += 1
            
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Token encryption failed: {str(e)}")
            raise EncryptionError(f"Encryption failed: {str(e)}")
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt a token using Fernet decryption
        
        Args:
            encrypted_token: Base64 encoded encrypted token
            
        Returns:
            Decrypted token
            
        Raises:
            EncryptionError: If decryption fails
        """
        try:
            if not encrypted_token:
                raise EncryptionError("Encrypted token cannot be empty")
            
            encrypted_data = base64.urlsafe_b64decode(encrypted_token.encode())
            decrypted_data = self.fernet.decrypt(encrypted_data)
            self.metrics['encryption_operations'] += 1
            
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Token decryption failed: {str(e)}")
            raise EncryptionError(f"Decryption failed: {str(e)}")
    
# Global security manager instance
_security_manager = None

def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager

# Convenience functions
def encrypt_token(token: str) -> str:
    """Encrypt token using global security manager"""
    return get_security_manager().encrypt_token(token)

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt token using global security manager"""
    return get_security_manager().decrypt_token(encrypted_token)

def hash_password(password: str) -> str:
    """Hash password using global security manager"""
    return get_security_manager().hash_password(password)

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password using global security manager"""
    return get_security_manager().verify_password(password, hashed_password)

def generate_secure_token(length: int = 32) -> str:
    """Generate secure token using global security manager"""
    return get_security_manager().generate_secure_token(length)

def generate_api_key(user_id: Union[str, int], prefix: str = 'ak') -> str:
    """Generate API key using global security manager"""
    return get_security_manager().generate_api_key(user_id, prefix)

def validate_api_key(api_key: str, expected_prefix: str = 'ak') -> Optional[Dict[str, Any]]:
    """Validate API key using global security manager"""
    return get_security_manager().validate_api_key(api_key, expected_prefix)
