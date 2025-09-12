"""
Authentication and Authorization Module
Production-grade auth utilities with JWT, role-based access control, and session management
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union, Callable
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
import redis
from dataclasses import dataclass
from enum import Enum

from .security import get_security_manager, SecurityError, TokenError
from .logging import get_logger, LogContext

logger = get_logger(__name__)

class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    API_USER = "api_user"

class Permission(Enum):
    """Permission enumeration"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    MANAGE_FORMS = "manage_forms"
    MANAGE_REPORTS = "manage_reports"
    EXPORT_DATA = "export_data"
    UPLOAD_FILE = "upload_file"

@dataclass
class UserInfo:
    """User information container"""
    id: str
    email: str
    roles: List[UserRole]
    permissions: List[Permission]
    is_active: bool = True
    last_login: Optional[datetime] = None
    session_id: Optional[str] = None
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role"""
        return role in self.roles
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions or Permission.ADMIN in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'roles': [role.value for role in self.roles],
            'permissions': [perm.value for perm in self.permissions],
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'session_id': self.session_id
        }

class AuthenticationError(Exception):
    """Authentication error"""
    pass

class AuthorizationError(Exception):
    """Authorization error"""
    pass

class SessionManager:
    """
    Session management with Redis backend
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        )
        self.session_ttl = int(os.getenv('SESSION_TTL', '86400'))  # 24 hours
        self.max_sessions_per_user = int(os.getenv('MAX_SESSIONS_PER_USER', '5'))
    
    def create_session(self, user_info: UserInfo) -> str:
        """
        Create new user session
        
        Args:
            user_info: User information
            
        Returns:
            Session ID
        """
        try:
            session_id = get_security_manager().generate_secure_token(32)
            
            # Store session data
            session_key = f"session:{session_id}"
            session_data = {
                **user_info.to_dict(),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'last_accessed': datetime.now(timezone.utc).isoformat()
            }
            
            self.redis_client.setex(session_key, self.session_ttl, json.dumps(session_data, default=str))
            
            # Track user sessions
            user_sessions_key = f"user_sessions:{user_info.id}"
            self.redis_client.sadd(user_sessions_key, session_id)
            self.redis_client.expire(user_sessions_key, self.session_ttl)
            
            # Cleanup old sessions if limit exceeded
            self._cleanup_user_sessions(user_info.id)
            
            logger.info(
                f"Created session for user {user_info.id}",
                context=LogContext(user_id=user_info.id, session_id=session_id)
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise AuthenticationError(f"Session creation failed: {str(e)}")
    
    def get_session(self, session_id: str) -> Optional[UserInfo]:
        """
        Get session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            UserInfo if session exists and valid, None otherwise
        """
        try:
            session_key = f"session:{session_id}"
            session_data = self.redis_client.get(session_key)
            
            if not session_data:
                return None
            
            # Handle bytes/string conversion for session data
            try:
                session_str = session_data.decode() if isinstance(session_data, bytes) else str(session_data)
                data = json.loads(session_str)
            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                logger.error(f"Failed to decode session data for {session_id}")
                return None
            
            # Update last accessed time
            data['last_accessed'] = datetime.now(timezone.utc).isoformat()
            self.redis_client.setex(session_key, self.session_ttl, json.dumps(data, default=str))
            
            # Convert to UserInfo
            user_info = UserInfo(
                id=data['id'],
                email=data['email'],
                roles=[UserRole(role) for role in data['roles']],
                permissions=[Permission(perm) for perm in data['permissions']],
                is_active=data['is_active'],
                last_login=datetime.fromisoformat(data['last_login']) if data.get('last_login') else None,
                session_id=session_id
            )
            
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None
    
    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was invalidated, False otherwise
        """
        try:
            session_key = f"session:{session_id}"
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                # Handle bytes/string conversion
                session_str = session_data.decode() if isinstance(session_data, bytes) else str(session_data)
                data = json.loads(session_str)
                user_id = data.get('id')
                
                # Remove from Redis
                self.redis_client.delete(session_key)
                
                # Remove from user sessions set
                if user_id:
                    user_sessions_key = f"user_sessions:{user_id}"
                    self.redis_client.srem(user_sessions_key, session_id)
                
                logger.info(
                    f"Invalidated session {session_id}",
                    context=LogContext(user_id=user_id, session_id=session_id)
                )
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {str(e)}")
            return False
    
    def invalidate_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of sessions invalidated
        """
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            
            # Get session IDs with proper error handling
            try:
                session_ids_raw = self.redis_client.smembers(user_sessions_key)
                session_ids = session_ids_raw if session_ids_raw else set()
            except Exception:
                session_ids = set()
            
            count = 0
            # Convert to list to avoid iteration issues
            session_list = list(session_ids) if session_ids else []  # type: ignore
            
            for session_id_bytes in session_list:
                try:
                    session_id = session_id_bytes.decode() if isinstance(session_id_bytes, bytes) else str(session_id_bytes)
                    session_key = f"session:{session_id}"
                    if self.redis_client.delete(session_key):
                        count += 1
                except (UnicodeDecodeError, AttributeError):
                    continue
            
            # Clear the user sessions set
            self.redis_client.delete(user_sessions_key)
            
            logger.info(f"Invalidated {count} sessions for user {user_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to invalidate sessions for user {user_id}: {str(e)}")
            return 0
    
    def _cleanup_user_sessions(self, user_id: str):
        """Cleanup old sessions if limit exceeded"""
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            
            # Get session IDs with proper error handling
            try:
                session_ids_raw = self.redis_client.smembers(user_sessions_key)
                session_list = list(session_ids_raw) if session_ids_raw else []  # type: ignore
            except Exception:
                session_list = []
            
            if len(session_list) > self.max_sessions_per_user:
                # Get session creation times
                session_times = []
                for session_id_bytes in session_list:
                    try:
                        session_id = session_id_bytes.decode() if isinstance(session_id_bytes, bytes) else str(session_id_bytes)
                        session_key = f"session:{session_id}"
                        session_data = self.redis_client.get(session_key)
                        if session_data:
                            try:
                                session_str = session_data.decode() if isinstance(session_data, bytes) else str(session_data)
                                data = json.loads(session_str)
                                created_at = datetime.fromisoformat(data['created_at'])
                                session_times.append((session_id, created_at))
                            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                                continue
                    except (UnicodeDecodeError, AttributeError):
                        continue
                
                # Sort by creation time and remove oldest
                session_times.sort(key=lambda x: x[1])
                sessions_to_remove = len(session_times) - self.max_sessions_per_user
                
                for i in range(sessions_to_remove):
                    session_id = session_times[i][0]
                    self.invalidate_session(session_id)
                    
        except Exception as e:
            logger.error(f"Failed to cleanup sessions for user {user_id}: {str(e)}")

class AuthManager:
    """
    Main authentication and authorization manager
    """
    
    def __init__(self, app=None, redis_client: Optional[redis.Redis] = None):
        self.app = app
        self.session_manager = SessionManager(redis_client)
        self.security_manager = get_security_manager()
        
        # Role-permission mapping
        self.role_permissions = {
            UserRole.ADMIN: [
                Permission.READ, Permission.WRITE, Permission.DELETE,
                Permission.ADMIN, Permission.MANAGE_USERS,
                Permission.MANAGE_FORMS, Permission.MANAGE_REPORTS,
                Permission.EXPORT_DATA
            ],
            UserRole.USER: [
                Permission.READ, Permission.WRITE,
                Permission.MANAGE_FORMS, Permission.MANAGE_REPORTS,
                Permission.EXPORT_DATA
            ],
            UserRole.VIEWER: [Permission.READ],
            UserRole.API_USER: [Permission.READ, Permission.WRITE, Permission.EXPORT_DATA]
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Setup JWT
        self.jwt = JWTManager(app)
        
        # JWT error handlers
        @self.jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({"error": "Token has expired"}), 401
        
        @self.jwt.invalid_token_loader
        def invalid_token_callback(error_string):
            return jsonify({"error": "Invalid token"}), 401
        
        @self.jwt.unauthorized_loader
        def missing_token_callback(error_string):
            return jsonify({"error": "Authorization token required"}), 401
    
    def authenticate_user(self, email: str, password: str) -> Optional[UserInfo]:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: User password
            
        Returns:
            UserInfo if authentication successful, None otherwise
        """
        try:
            # In a real implementation, this would query the database
            # For now, this is a mock implementation
            
            # Mock user data (replace with actual database query)
            mock_users = {
                "admin@example.com": {
                    "id": "1",
                    "email": "admin@example.com",
                    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8/M8wbJ4He",  # "admin123"
                    "roles": [UserRole.ADMIN],
                    "is_active": True
                },
                "user@example.com": {
                    "id": "2",
                    "email": "user@example.com",
                    "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj8/M8wbJ4He",  # "user123"
                    "roles": [UserRole.USER],
                    "is_active": True
                }
            }
            
            user_data = mock_users.get(email)
            if not user_data or not user_data['is_active']:
                return None
            
            # Verify password
            if not self.security_manager.verify_password(password, user_data['password_hash']):
                return None
            
            # Get permissions for user roles
            permissions = set()
            for role in user_data['roles']:
                permissions.update(self.role_permissions.get(role, []))
            
            # Create UserInfo
            user_info = UserInfo(
                id=user_data['id'],
                email=user_data['email'],
                roles=user_data['roles'],
                permissions=list(permissions),
                is_active=user_data['is_active'],
                last_login=datetime.now(timezone.utc)
            )
            
            return user_info
            
        except Exception as e:
            logger.error(f"Authentication failed for {email}: {str(e)}")
            return None
    
    def create_tokens(self, user_info: UserInfo) -> Dict[str, str]:
        """
        Create access and refresh tokens for user
        
        Args:
            user_info: User information
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        try:
            # Create session
            session_id = self.session_manager.create_session(user_info)
            
            # Additional claims
            additional_claims = {
                'email': user_info.email,
                'roles': [role.value for role in user_info.roles],
                'session_id': session_id
            }
            
            # Generate tokens
            access_token = self.security_manager.generate_jwt_token(
                user_id=user_info.id,
                token_type='access',
                additional_claims=additional_claims
            )
            
            refresh_token = self.security_manager.generate_jwt_token(
                user_id=user_info.id,
                token_type='refresh',
                additional_claims=additional_claims
            )
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Token creation failed: {str(e)}")
            raise AuthenticationError(f"Token creation failed: {str(e)}")
    
    def get_current_user_from_token(self, token: str) -> Optional[UserInfo]:
        """
        Get current user from JWT token
        
        Args:
            token: JWT token
            
        Returns:
            UserInfo if token is valid, None otherwise
        """
        try:
            # Validate token
            payload = self.security_manager.validate_jwt_token(token)
            
            # Get session
            session_id = payload.get('session_id')
            if session_id:
                user_info = self.session_manager.get_session(session_id)
                if user_info:
                    return user_info
            
            # Fallback: create UserInfo from token payload
            user_info = UserInfo(
                id=payload['user_id'],
                email=payload.get('email', ''),
                roles=[UserRole(role) for role in payload.get('roles', [])],
                permissions=[],  # Will be populated based on roles
                is_active=True
            )
            
            # Get permissions for user roles
            permissions = set()
            for role in user_info.roles:
                permissions.update(self.role_permissions.get(role, []))
            user_info.permissions = list(permissions)
            
            return user_info
            
        except TokenError:
            return None
        except Exception as e:
            logger.error(f"Failed to get user from token: {str(e)}")
            return None

# Global auth manager instance
_auth_manager = None

def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager

def get_current_user() -> Optional[UserInfo]:
    """
    Get current authenticated user
    
    Returns:
        UserInfo if user is authenticated, None otherwise
    """
    try:
        # Check if user is already in request context
        if hasattr(g, 'current_user'):
            return g.current_user
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        auth_manager = get_auth_manager()
        user_info = auth_manager.get_current_user_from_token(token)
        
        # Store in request context
        g.current_user = user_info
        
        return user_info
        
    except Exception as e:
        logger.error(f"Failed to get current user: {str(e)}")
        return None

def require_auth(f):
    """
    Decorator to require authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_role(*required_roles: UserRole):
    """
    Decorator to require specific roles
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            
            if not any(user.has_role(role) for role in required_roles):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_permission(*required_permissions: Permission):
    """
    Decorator to require specific permissions
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            
            if not any(user.has_permission(perm) for perm in required_permissions):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

import json  # Add missing import
