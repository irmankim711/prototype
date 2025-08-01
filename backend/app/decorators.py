from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from .models import User, Permission

def get_current_user_id():
    """Helper function to get current authenticated user ID as integer."""
    user_id = get_jwt_identity()
    return int(user_id) if user_id else None

def require_permission(permission: Permission):
    """Decorator to require specific permission for route access."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
                
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
                
            if not user.has_permission(permission):
                return jsonify({'error': 'Insufficient permissions'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(required_role):
    """Decorator to require specific role for route access."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
                
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
                
            if user.role != required_role:
                return jsonify({'error': f'Role {required_role.value} required'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Helper function to get current authenticated user."""
    from .models import User, UserRole, Permission
    
    user_id = get_jwt_identity()
    
    # Handle bypass user for development
    if user_id == 'bypass-user':
        # Create a mock user object for bypass mode
        bypass_user = User()
        bypass_user.id = 999999  # Special ID for bypass user
        bypass_user.email = 'bypass@test.com'
        bypass_user.username = 'Bypass User'
        bypass_user.is_active = True
        bypass_user.role = UserRole.ADMIN  # Give admin privileges for testing
        return bypass_user
    
    user_id = get_current_user_id()
    if user_id:
        return User.query.get(user_id)
    return None
