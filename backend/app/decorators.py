from functools import wraps
from flask import jsonify, current_app, request, g
from .models import User
from .middleware.firebase_auth import firebase_auth_manager
import logging

logger = logging.getLogger(__name__)

def get_current_user_id():
    """Get current authenticated user ID from Firebase context."""
    return getattr(g, 'current_user_id', None)

def get_user_id_safe(user):
    """
    Safely get user ID from either dict (Firestore) or User object (SQLAlchemy).

    Args:
        user: User dict from Firestore or User object from SQLAlchemy

    Returns:
        User ID string or None
    """
    if not user:
        return None
    return user.get('id') if isinstance(user, dict) else getattr(user, 'id', None)

def firebase_auth_required(f):
    """Firebase authentication decorator - replaces @jwt_required()"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip auth check for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        try:
            # Get Firebase token from Authorization header
            auth_header = request.headers.get('Authorization', '')
            id_token = None
            if auth_header.startswith('Bearer '):
                id_token = auth_header.replace('Bearer ', '').strip()
            else:
                # Fallback: read HttpOnly cookie set by /api/auth/login
                cookie_name = current_app.config.get('access_token_cookie')
                cookie_token = request.cookies.get(cookie_name)
                if cookie_token:
                    id_token = cookie_token

            if not id_token:
                return jsonify({
                    'error': 'Missing or invalid Authorization header',
                    'code': 'MISSING_AUTH_HEADER'
                }), 401

            firebase_token = id_token

            # Check Firebase initialization
            if not firebase_auth_manager._initialized:
                current_app.logger.error("Firebase not initialized for authentication")
                return jsonify({
                    'error': 'Authentication service unavailable',
                    'code': 'AUTH_SERVICE_UNAVAILABLE'
                }), 503

            # Verify Firebase token
            try:
                decoded_token = firebase_auth_manager.verify_token(firebase_token)
                if not decoded_token:
                    return jsonify({
                        'error': 'Invalid or expired token',
                        'code': 'INVALID_TOKEN'
                    }), 401
            except Exception as e:
                current_app.logger.error(f"Token verification failed: {str(e)}")
                return jsonify({
                    'error': 'Token verification failed',
                    'code': 'TOKEN_VERIFICATION_FAILED'
                }), 401

            # Get or create user
            user = firebase_auth_manager.get_or_create_user(decoded_token)

            if not user:
                return jsonify({
                    'error': 'User authentication failed',
                    'code': 'USER_AUTH_FAILED'
                }), 401

            # Set user context in Flask's g object
            g.current_user = user
            # Handle both dict (Firestore) and User object (SQLAlchemy)
            g.current_user_id = user.get('id') if isinstance(user, dict) else user.id
            g.firebase_token = decoded_token
            g.firebase_uid = decoded_token.get('uid')

            return f(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"Authentication error: {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'code': 'AUTH_ERROR'
            }), 500

    return decorated_function

def require_role(*allowed_roles):
    """Role-based access control decorator. Must be used after @firebase_auth_required"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()

            if not current_user:
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401

            # Handle both dict (Firestore) and User object (SQLAlchemy)
            if isinstance(current_user, dict):
                user_role = current_user.get('role', 'user')
            else:
                user_role = current_user.role
                if hasattr(user_role, 'value'):
                    user_role = user_role.value
                elif hasattr(user_role, 'name'):
                    user_role = user_role.name
                else:
                    user_role = str(user_role)

            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'required_roles': list(allowed_roles),
                    'user_role': user_role
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator

def get_current_user():
    """Get current authenticated user from Firebase context."""
    return getattr(g, 'current_user', None)

def get_firebase_uid():
    """Get Firebase UID of current user."""
    return getattr(g, 'firebase_uid', None)

def get_firebase_token():
    """Get decoded Firebase token data."""
    return getattr(g, 'firebase_token', None)

def firebase_token_optional(f):
    """Optional Firebase authentication decorator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get Firebase token from Authorization header
            auth_header = request.headers.get('Authorization', '')

            # If no auth header, continue without authentication
            firebase_token = None
            if auth_header.startswith('Bearer '):
                firebase_token = auth_header.replace('Bearer ', '').strip()
            else:
                # Try cookie fallback
                cookie_name = current_app.config.get('JWT_ACCESS_COOKIE_NAME', 'access_token_cookie')
                cookie_token = request.cookies.get(cookie_name)
                if cookie_token:
                    firebase_token = cookie_token
                else:
                    g.current_user = None
                    g.current_user_id = None
                    g.firebase_token = None
                    g.firebase_uid = None
                    return f(*args, **kwargs)

            # Check Firebase initialization
            if not firebase_auth_manager._initialized:
                g.current_user = None
                g.current_user_id = None
                g.firebase_token = None
                g.firebase_uid = None
                return f(*args, **kwargs)

            # Verify Firebase token
            try:
                decoded_token = firebase_auth_manager.verify_token(firebase_token)
                if decoded_token:
                    # Try to get user
                    user = firebase_auth_manager.get_or_create_user(decoded_token)

                    # Set user context if successful
                    g.current_user = user
                    # Handle both dict (Firestore) and User object (SQLAlchemy)
                    g.current_user_id = (user.get('id') if isinstance(user, dict) else user.id) if user else None
                    g.firebase_token = decoded_token
                    g.firebase_uid = decoded_token.get('uid')
                else:
                    # Invalid token, continue without authentication
                    g.current_user = None
                    g.current_user_id = None
                    g.firebase_token = None
                    g.firebase_uid = None
            except Exception:
                # Token verification failed, continue without authentication
                g.current_user = None
                g.current_user_id = None
                g.firebase_token = None
                g.firebase_uid = None

            return f(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"Optional authentication error: {str(e)}")
            # Set empty context and continue
            g.current_user = None
            g.current_user_id = None
            g.firebase_token = None
            g.firebase_uid = None
            return f(*args, **kwargs)

    return decorated_function

def admin_required(f):
    """Admin-only access decorator."""
    return require_role('admin', 'ADMIN')(f)

def require_permission(*required_permissions):
    """Permission-based access control decorator. Must be used after @firebase_auth_required"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()

            if not current_user:
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401

            # For now, allow all authenticated users (simplified permission system)
            # In a full implementation, you would check user.permissions against required_permissions
            return f(*args, **kwargs)

        return decorated_function
    return decorator

def require_auth(f):
    """Alias for firebase_auth_required for backward compatibility"""
    return firebase_auth_required(f)

def require_form_access(f):
    """
    Decorator to check if user has access to a specific form.
    Must be used after @firebase_auth_required.
    Expects 'form_id' or 'google_form_id' in route parameters or request data.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from .models import Form

        current_user = get_current_user()

        if not current_user:
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401

        # Get form_id from route parameters or request body
        form_id = kwargs.get('form_id') or request.view_args.get('form_id')

        # For Google Forms, we'll allow access if user is authenticated
        # since they manage their own OAuth tokens
        google_form_id = kwargs.get('google_form_id') or request.view_args.get('google_form_id')
        if google_form_id:
            # User has their own Google OAuth - they can only access their own forms
            return f(*args, **kwargs)

        if not form_id:
            return jsonify({
                'success': False,
                'error': 'Form ID is required',
                'code': 'MISSING_FORM_ID'
            }), 400

        # Check if form exists and user has access
        form = Form.query.get(form_id)
        if not form:
            return jsonify({
                'success': False,
                'error': f'Form {form_id} not found',
                'code': 'FORM_NOT_FOUND'
            }), 404

        # Check if user is the creator OR form is public OR user is admin
        # Handle both dict (Firestore) and User object (SQLAlchemy)
        if isinstance(current_user, dict):
            user_role = current_user.get('role', 'user')
            user_id = current_user.get('id')
        else:
            user_role = getattr(current_user.role, 'value', str(current_user.role))
            user_id = current_user.id

        is_admin = user_role in ('admin', 'ADMIN')
        is_creator = form.creator_id == user_id
        is_public = form.is_public

        if not (is_admin or is_creator or is_public):
            return jsonify({
                'success': False,
                'error': 'You do not have permission to access this form',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403

        # Store form in g for use in the route
        g.current_form = form

        return f(*args, **kwargs)

    return decorated_function

