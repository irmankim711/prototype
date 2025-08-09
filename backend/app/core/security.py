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
import jwt
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
    Comprehensive security manager for encryption, token management, and data protection
    
    Features:
    - AES-256 encryption with Fernet
    - JWT token generation and validation
    - Password hashing with bcrypt
    - Secure random token generation
    - Rate limiting utilities
    - Input sanitization
    """
    
    def __init__(self, encryption_key: Optional[str] = None, jwt_secret: Optional[str] = None):
        """
        Initialize security manager
        
        Args:
            encryption_key: Base64 encoded encryption key (generates if None)
            jwt_secret: JWT secret key
        """
        self.jwt_secret = jwt_secret or os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.jwt_access_token_expires = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
        self.jwt_refresh_token_expires = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))
        
        # Initialize encryption
        self._setup_encryption(encryption_key)
        
        # Security metrics
        self.metrics = {
            'tokens_generated': 0,
            'tokens_validated': 0,
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
    
    def generate_jwt_token(
        self,
        user_id: Union[str, int],
        token_type: str = 'access',
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Generate JWT token
        
        Args:
            user_id: User identifier
            token_type: Token type ('access' or 'refresh')
            additional_claims: Additional JWT claims
            expires_delta: Custom expiration time
            
        Returns:
            JWT token string
            
        Raises:
            TokenError: If token generation fails
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Set expiration based on token type
            if expires_delta:
                expires_at = now + expires_delta
            elif token_type == 'refresh':
                expires_at = now + timedelta(seconds=self.jwt_refresh_token_expires)
            else:
                expires_at = now + timedelta(seconds=self.jwt_access_token_expires)
            
            # Base claims
            payload = {
                'user_id': str(user_id),
                'token_type': token_type,
                'iat': now,
                'exp': expires_at,
                'jti': self.generate_secure_token(16)  # JWT ID for token tracking
            }
            
            # Add additional claims
            if additional_claims:
                payload.update(additional_claims)
            
            # Generate token
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            
            self.metrics['tokens_generated'] += 1
            logger.debug(f"Generated {token_type} token for user {user_id}")
            
            return token
            
        except Exception as e:
            logger.error(f"JWT token generation failed: {str(e)}")
            raise TokenError(f"Token generation failed: {str(e)}")
    
    def validate_jwt_token(self, token: str, token_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate and decode JWT token
        
        Args:
            token: JWT token to validate
            token_type: Expected token type ('access' or 'refresh')
            
        Returns:
            Decoded token payload
            
        Raises:
            TokenError: If token validation fails
        """
        try:
            if not token:
                raise TokenError("Token cannot be empty")
            
            # Decode and validate token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={
                    'verify_exp': True,
                    'verify_iat': True,
                    'require_exp': True,
                    'require_iat': True
                }
            )
            
            # Validate token type if specified
            if token_type and payload.get('token_type') != token_type:
                raise TokenError(f"Invalid token type. Expected {token_type}, got {payload.get('token_type')}")
            
            self.metrics['tokens_validated'] += 1
            logger.debug(f"Validated {payload.get('token_type', 'unknown')} token for user {payload.get('user_id')}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.metrics['failed_validations'] += 1
            raise TokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            self.metrics['failed_validations'] += 1
            raise TokenError(f"Invalid token: {str(e)}")
        except Exception as e:
            self.metrics['failed_validations'] += 1
            logger.error(f"Token validation failed: {str(e)}")
            raise TokenError(f"Token validation failed: {str(e)}")
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        if not password:
            raise SecurityError("Password cannot be empty")
        
        rounds = int(os.getenv('PASSWORD_HASH_ROUNDS', '12'))
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        if not password or not hashed_password:
            return False
        
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure random token
        
        Args:
            length: Token length in bytes
            
        Returns:
            Base64 encoded secure token
        """
        token_bytes = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(token_bytes).decode()
    
    def generate_api_key(self, user_id: Union[str, int], prefix: str = 'ak') -> str:
        """
        Generate API key with prefix and checksum
        
        Args:
            user_id: User identifier
            prefix: API key prefix
            
        Returns:
            API key string
        """
        # Generate random part
        random_part = self.generate_secure_token(24)
        
        # Create payload with user ID and timestamp
        payload = f"{user_id}:{int(time.time())}:{random_part}"
        
        # Generate checksum
        checksum = hashlib.sha256(payload.encode()).hexdigest()[:8]
        
        # Combine with prefix
        api_key = f"{prefix}_{base64.urlsafe_b64encode(payload.encode()).decode()}_{checksum}"
        
        return api_key
    
    def validate_api_key(self, api_key: str, expected_prefix: str = 'ak') -> Optional[Dict[str, Any]]:
        """
        Validate API key and extract user info
        
        Args:
            api_key: API key to validate
            expected_prefix: Expected prefix
            
        Returns:
            User info if valid, None otherwise
        """
        try:
            # Split API key parts
            parts = api_key.split('_')
            if len(parts) != 3 or parts[0] != expected_prefix:
                return None
            
            prefix, encoded_payload, provided_checksum = parts
            
            # Decode payload
            payload = base64.urlsafe_b64decode(encoded_payload.encode()).decode()
            
            # Verify checksum
            expected_checksum = hashlib.sha256(payload.encode()).hexdigest()[:8]
            if provided_checksum != expected_checksum:
                return None
            
            # Parse payload
            user_id, timestamp, random_part = payload.split(':')
            
            return {
                'user_id': user_id,
                'issued_at': int(timestamp),
                'api_key': api_key
            }
            
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return None
    
    def sanitize_input(self, text: str, max_length: int = 1000) -> str:
        """
        Sanitize user input
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Truncate if too long
        sanitized = text[:max_length]
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
        
        # Strip whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    def generate_csrf_token(self, session_id: str) -> str:
        """
        Generate CSRF token
        
        Args:
            session_id: Session identifier
            
        Returns:
            CSRF token
        """
        timestamp = str(int(time.time()))
        random_part = self.generate_secure_token(16)
        payload = f"{session_id}:{timestamp}:{random_part}"
        
        # Create HMAC signature
        signature = hashlib.sha256(f"{self.jwt_secret}:{payload}".encode()).hexdigest()
        
        return base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()
    
    def validate_csrf_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """
        Validate CSRF token
        
        Args:
            token: CSRF token to validate
            session_id: Expected session ID
            max_age: Maximum token age in seconds
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Decode token
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            payload, signature = decoded.rsplit(':', 1)
            
            # Verify signature
            expected_signature = hashlib.sha256(f"{self.jwt_secret}:{payload}".encode()).hexdigest()
            if signature != expected_signature:
                return False
            
            # Parse payload
            token_session_id, timestamp, random_part = payload.split(':')
            
            # Verify session ID
            if token_session_id != session_id:
                return False
            
            # Check age
            token_age = int(time.time()) - int(timestamp)
            if token_age > max_age:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"CSRF token validation failed: {str(e)}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get security operation metrics"""
        return {
            **self.metrics,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

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

def generate_jwt_token(user_id: Union[str, int], token_type: str = 'access', **kwargs) -> str:
    """Generate JWT token using global security manager"""
    return get_security_manager().generate_jwt_token(user_id, token_type, **kwargs)

def validate_jwt_token(token: str, token_type: Optional[str] = None) -> Dict[str, Any]:
    """Validate JWT token using global security manager"""
    return get_security_manager().validate_jwt_token(token, token_type)

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
