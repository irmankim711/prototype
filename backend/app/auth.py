"""
Authentication routes for user login, registration, and token management
"""

from flask import Blueprint, request, jsonify, current_app, make_response
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from datetime import datetime, timedelta
from .. import db
from ..models import User
from ..middleware.firebase_auth import firebase_auth_manager
import secrets
import logging

auth_bp = Blueprint('auth', __name__)
limiter = Limiter(key_func=get_remote_address)

@auth_bp.route('/firebase-login', methods=['POST', 'OPTIONS'])
@limiter.limit("10 per minute")
def firebase_login():
    """Firebase authentication endpoint - verifies Firebase token and syncs user"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid Authorization header',
                'code': 'MISSING_AUTH_HEADER'
            }), 401

        firebase_token = auth_header.replace('Bearer ', '')

        # Check Firebase initialization
        if not firebase_auth_manager._initialized:
            current_app.logger.error("Firebase not initialized for login")
            return jsonify({
                'error': 'Authentication service unavailable',
                'code': 'AUTH_SERVICE_UNAVAILABLE'
            }), 503

        # Verify Firebase token
        try:
            decoded_token = firebase_auth_manager.verify_token(firebase_token)
            if not decoded_token:
                return jsonify({
                    'error': 'Invalid Firebase token',
                    'code': 'INVALID_TOKEN'
                }), 401
        except Exception as e:
            current_app.logger.error(f"Firebase token verification failed: {str(e)}")
            return jsonify({
                'error': 'Firebase token verification failed',
                'code': 'TOKEN_VERIFICATION_FAILED'
            }), 401

        # Extract user info from token
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        name = decoded_token.get('name', '')

        if not firebase_uid or not email:
            return jsonify({
                'error': 'Incomplete user information in token',
                'code': 'INCOMPLETE_USER_INFO'
            }), 400

        current_app.logger.info(f"Firebase login attempt for email: {email}")

        # Get or create user using Firebase auth manager
        user = firebase_auth_manager.get_or_create_user(decoded_token)

        if not user:
            current_app.logger.error(f"Failed to get or create user for {email}")
            return jsonify({
                'error': 'User authentication failed',
                'code': 'USER_AUTH_FAILED'
            }), 401

        # Check if account is active
        if not user.is_active:
            return jsonify({
                'error': 'Account is deactivated',
                'code': 'ACCOUNT_DEACTIVATED'
            }), 401

        current_app.logger.info(f"Firebase login successful for user {user.id}")

        # Return user information (no need for JWT tokens as we use Firebase tokens)
        response_data = {
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None),
                'display_name': getattr(user, 'display_name', name),
                'firebase_uid': user.firebase_uid,
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role) if user.role else 'user'
            }
        }

        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"Firebase login error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/firebase-register', methods=['POST', 'OPTIONS'])
@limiter.limit("5 per hour")
def firebase_register():
    """Firebase registration endpoint - verifies Firebase token and creates/updates user"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid Authorization header',
                'code': 'MISSING_AUTH_HEADER'
            }), 401

        firebase_token = auth_header.replace('Bearer ', '')

        # Check Firebase initialization
        if not firebase_auth_manager._initialized:
            current_app.logger.error("Firebase not initialized for registration")
            return jsonify({
                'error': 'Authentication service unavailable',
                'code': 'AUTH_SERVICE_UNAVAILABLE'
            }), 503

        # Verify Firebase token
        try:
            decoded_token = firebase_auth_manager.verify_token(firebase_token)
            if not decoded_token:
                return jsonify({
                    'error': 'Invalid Firebase token',
                    'code': 'INVALID_TOKEN'
                }), 401
        except Exception as e:
            current_app.logger.error(f"Firebase token verification failed: {str(e)}")
            return jsonify({
                'error': 'Firebase token verification failed',
                'code': 'TOKEN_VERIFICATION_FAILED'
            }), 401

        # Get additional registration data from request body
        additional_data = {}
        if request.is_json:
            additional_data = request.get_json() or {}

        # Extract user info from token
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')

        if not firebase_uid or not email:
            return jsonify({
                'error': 'Incomplete user information in token',
                'code': 'INCOMPLETE_USER_INFO'
            }), 400

        current_app.logger.info(f"Firebase registration attempt for email: {email}")

        # Get or create user using Firebase auth manager with additional data
        user = firebase_auth_manager.get_or_create_user(decoded_token, additional_data)

        if not user:
            current_app.logger.error(f"Failed to create user for {email}")
            return jsonify({
                'error': 'User registration failed',
                'code': 'USER_REGISTRATION_FAILED'
            }), 500

        current_app.logger.info(f"Firebase registration successful for user {user.id}")

        # Return success message with user info
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None),
                'firebase_uid': user.firebase_uid,
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role) if user.role else 'user'
            }
        }), 201

    except Exception as e:
        current_app.logger.error(f"Firebase registration error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@auth_bp.route('/verify-token', methods=['POST', 'OPTIONS'])
@limiter.limit("20 per minute")
def verify_token():
    """Verify Firebase token and return user information"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid Authorization header',
                'code': 'MISSING_AUTH_HEADER',
                'valid': False
            }), 401

        firebase_token = auth_header.replace('Bearer ', '')

        # Check Firebase initialization
        if not firebase_auth_manager._initialized:
            current_app.logger.error("Firebase not initialized for token verification")
            return jsonify({
                'error': 'Authentication service unavailable',
                'code': 'AUTH_SERVICE_UNAVAILABLE',
                'valid': False
            }), 503

        # Verify Firebase token
        try:
            decoded_token = firebase_auth_manager.verify_token(firebase_token)
            if not decoded_token:
                return jsonify({
                    'error': 'Invalid or expired token',
                    'code': 'INVALID_TOKEN',
                    'valid': False
                }), 401
        except Exception as e:
            current_app.logger.error(f"Token verification failed: {str(e)}")
            return jsonify({
                'error': 'Token verification failed',
                'code': 'TOKEN_VERIFICATION_FAILED',
                'valid': False
            }), 401

        # Get user from database
        firebase_uid = decoded_token.get('uid')
        user = User.query.filter_by(firebase_uid=firebase_uid).first()

        if not user:
            # Try to create user from token
            user = firebase_auth_manager.get_or_create_user(decoded_token)

        response_data = {
            'valid': True,
            'token_info': {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False)
            }
        }

        if user:
            response_data['user'] = {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None),
                'firebase_uid': user.firebase_uid,
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role) if user.role else 'user'
            }

        return jsonify(response_data), 200

    except Exception as e:
        current_app.logger.error(f"Token verification error: {str(e)}")
        return jsonify({
            'error': 'Token verification failed',
            'code': 'INTERNAL_ERROR',
            'valid': False
        }), 500

@auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Firebase logout endpoint - Always succeeds to ensure users can logout"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        current_app.logger.info("🔄 Logout endpoint called")

        # With Firebase, logout is handled on the client side
        # We can optionally log the logout event if we have user info
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            firebase_token = auth_header.replace('Bearer ', '')

            if firebase_auth_manager._initialized:
                try:
                    decoded_token = firebase_auth_manager.verify_token(firebase_token)
                    if decoded_token:
                        email = decoded_token.get('email')
                        firebase_uid = decoded_token.get('uid')
                        current_app.logger.info(f"✅ User {email} logged out successfully")

                        # Try to update user logout time (optional, non-critical)
                        try:
                            user = User.query.filter_by(firebase_uid=firebase_uid).first()
                            if user:
                                user.updated_at = datetime.utcnow()
                                db.session.commit()
                        except Exception as db_error:
                            current_app.logger.warning(f"⚠️ Could not update user logout time: {str(db_error)}")
                            try:
                                db.session.rollback()
                            except:
                                pass
                except Exception as token_error:
                    # Token might be expired or invalid - that's OK for logout
                    current_app.logger.info(f"ℹ️ Logout with invalid/expired token: {str(token_error)}")
                    pass

        # Create response with cookie clearing
        response = make_response(jsonify({
            'success': True,
            'message': 'Logout successful'
        }))

        # Clear any cookies that might exist
        response.set_cookie('session', '', expires=0, path='/')
        response.set_cookie('remember_token', '', expires=0, path='/')

        current_app.logger.info("✅ Logout completed successfully")
        return response, 200

    except Exception as e:
        # Even if there's an error, return success for logout
        # We don't want to prevent users from logging out
        current_app.logger.error(f"⚠️ Logout error (returning success anyway): {str(e)}")
        import traceback
        current_app.logger.error(f"📋 Stack trace: {traceback.format_exc()}")

        response = make_response(jsonify({
            'success': True,
            'message': 'Logout successful'
        }))

        # Still try to clear cookies even on error
        response.set_cookie('session', '', expires=0, path='/')
        response.set_cookie('remember_token', '', expires=0, path='/')

        return response, 200

@auth_bp.route('/profile', methods=['GET', 'OPTIONS'])
def get_profile():
    """Get current user profile using Firebase authentication"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid Authorization header',
                'code': 'MISSING_AUTH_HEADER'
            }), 401

        firebase_token = auth_header.replace('Bearer ', '')

        # Check Firebase initialization
        if not firebase_auth_manager._initialized:
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

        # Get user from database
        firebase_uid = decoded_token.get('uid')
        user = User.query.filter_by(firebase_uid=firebase_uid).first()

        if not user:
            return jsonify({
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        return jsonify({
            'user': user.to_dict() if hasattr(user, 'to_dict') else {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None),
                'display_name': getattr(user, 'display_name', None),
                'firebase_uid': user.firebase_uid,
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role) if user.role else 'user'
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve profile',
            'code': 'PROFILE_ERROR'
        }), 500

@auth_bp.route('/profile', methods=['PUT', 'OPTIONS'])
def update_profile():
    """Update current user profile using Firebase authentication"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid Authorization header',
                'code': 'MISSING_AUTH_HEADER'
            }), 401

        firebase_token = auth_header.replace('Bearer ', '')

        # Check Firebase initialization
        if not firebase_auth_manager._initialized:
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

        # Get user from database
        firebase_uid = decoded_token.get('uid')
        user = User.query.filter_by(firebase_uid=firebase_uid).first()

        if not user:
            return jsonify({
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data provided',
                'code': 'NO_DATA'
            }), 400

        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'display_name' in data:
            user.display_name = data['display_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'company' in data:
            user.company = data['company']
        if 'job_title' in data:
            user.job_title = data['job_title']

        user.updated_at = datetime.utcnow()

        db.session.commit()

        current_app.logger.info(f"Profile updated for user {user.id}")

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict() if hasattr(user, 'to_dict') else {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None),
                'display_name': getattr(user, 'display_name', None),
                'firebase_uid': user.firebase_uid,
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role) if user.role else 'user'
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Profile update error: {str(e)}")
        db.session.rollback()
        return jsonify({
            'error': 'Profile update failed',
            'code': 'PROFILE_UPDATE_ERROR'
        }), 500

# Password change is handled by Firebase Authentication on the client side
# We can add a password change confirmation endpoint if needed for logging

@auth_bp.route('/password-change-confirmation', methods=['POST', 'OPTIONS'])
def password_change_confirmation():
    """Confirm password change (for logging purposes - actual change done via Firebase)"""

    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response

    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'error': 'Missing or invalid Authorization header',
                'code': 'MISSING_AUTH_HEADER'
            }), 401

        firebase_token = auth_header.replace('Bearer ', '')

        # Check Firebase initialization
        if not firebase_auth_manager._initialized:
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

        # Log the password change event
        email = decoded_token.get('email')
        current_app.logger.info(f"Password change confirmed for user: {email}")

        return jsonify({
            'success': True,
            'message': 'Password change confirmed'
        }), 200

    except Exception as e:
        current_app.logger.error(f"Password change confirmation error: {str(e)}")
        return jsonify({
            'error': 'Password change confirmation failed',
            'code': 'CONFIRMATION_ERROR'
        }), 500
