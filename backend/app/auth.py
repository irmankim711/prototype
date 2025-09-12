"""
Authentication routes for user login, registration, and token management
"""

from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from .. import db
from ..models import User
import secrets
import logging

auth_bp = Blueprint('auth', __name__)
limiter = Limiter(key_func=get_remote_address)

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
@limiter.limit("5 per minute")
def login():
    """User login endpoint"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response
    
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        current_app.logger.info(f"Login attempt for email: {email}")
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            current_app.logger.warning(f"Login failed: User not found for email {email}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Check if account is locked
        if hasattr(user, 'is_account_locked') and user.is_account_locked():
            return jsonify({'error': 'Account is temporarily locked due to too many failed attempts'}), 423
        
        # Check if account is active
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Verify password
        if not user.check_password(password):
            # Increment failed login attempts if method exists
            if hasattr(user, 'increment_failed_login'):
                user.increment_failed_login()
            db.session.commit()
            
            current_app.logger.warning(f"Login failed: Invalid password for user {user.id}")
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Successful login - reset failed attempts and update last login
        if hasattr(user, 'update_last_login'):
            user.update_last_login()
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create JWT tokens
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=str(user.id),
            expires_delta=timedelta(days=30)
        )
        
        # Create session token for frontend
        session_token = secrets.token_urlsafe(32)
        
        current_app.logger.info(f"Login successful for user {user.id}")
        
        # Create response with JWT cookies
        response_data = {
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None),
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role) if user.role else 'user'
            },
            'session_token': session_token
        }
        
        response = make_response(jsonify(response_data), 200)
        
        # Set JWT cookies to match backend configuration
        response.set_cookie(
            'access_token_cookie',
            access_token,
            max_age=3600,  # 1 hour in seconds
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax',
            path='/'
        )
        
        response.set_cookie(
            'refresh_token_cookie',
            refresh_token,
            max_age=30*24*3600,  # 30 days in seconds
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax',
            path='/api/auth/refresh'
        )
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
@limiter.limit("3 per hour")
def register():
    """User registration endpoint"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        return response
    
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        if not username:
            username = email.split('@')[0]  # Generate username from email
        
        current_app.logger.info(f"Registration attempt for email: {email}")
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'User with this email already exists'}), 409
        
        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create new user
        user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        current_app.logger.info(f"User registered successfully: {user.id}")
        
        # Return success message
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.id
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Create new access token
        new_access_token = create_access_token(
            identity=current_user_id,
            expires_delta=timedelta(hours=1)
        )
        
        return jsonify({
            'access_token': new_access_token
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    try:
        current_user_id = get_jwt_identity()
        
        # Simple logout - just invalidate on client side
        # Note: In production, implement token blacklisting
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user_id} logged out successfully")
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict() if hasattr(user, 'to_dict') else {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve profile'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
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
            'message': 'Profile updated successfully',
            'user': user.to_dict() if hasattr(user, 'to_dict') else {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None)
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Profile update error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current and new password are required'}), 400
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Set new password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        current_app.logger.info(f"Password changed for user {user.id}")
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Password change error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Password change failed'}), 500
