"""
CSRF Token Management Routes

This module provides endpoints for CSRF token generation and management.
"""

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..middleware.enhanced_security import EnhancedCSRFMiddleware
import logging

logger = logging.getLogger(__name__)

csrf_bp = Blueprint('csrf', __name__)

@csrf_bp.route('/token', methods=['GET'])
@jwt_required()
def get_csrf_token():
    """Get a new CSRF token for the authenticated user."""
    try:
        user_id = get_jwt_identity()
        
        # Get CSRF middleware instance
        csrf_middleware = getattr(current_app, 'csrf_middleware', None)
        if not csrf_middleware:
            # Fallback: create a new instance
            csrf_middleware = EnhancedCSRFMiddleware(current_app)
        
        # Generate new token
        token = csrf_middleware.generate_csrf_token(user_id)
        
        # Create response with token
        response = jsonify({
            'success': True,
            'csrf_token': token,
            'message': 'CSRF token generated successfully'
        })
        
        # Set CSRF token as cookie for double submit pattern
        response.set_cookie(
            'csrf_token',
            token,
            max_age=3600,  # 1 hour
            secure=current_app.config.get('SESSION_COOKIE_SECURE', True),
            httponly=False,  # Allow JavaScript access
            samesite='Strict'
        )
        
        return response, 200
        
    except Exception as e:
        logger.error(f"Failed to generate CSRF token: {e}")
        return jsonify({
            'success': False,
            'error': 'TOKEN_GENERATION_FAILED',
            'message': 'Failed to generate CSRF token'
        }), 500

@csrf_bp.route('/validate', methods=['POST'])
def validate_csrf_token():
    """Validate a CSRF token (for testing purposes)."""
    try:
        token = request.json.get('csrf_token')
        if not token:
            return jsonify({
                'success': False,
                'error': 'MISSING_TOKEN',
                'message': 'CSRF token is required'
            }), 400
        
        # Get CSRF middleware instance
        csrf_middleware = getattr(current_app, 'csrf_middleware', None)
        if not csrf_middleware:
            return jsonify({
                'success': False,
                'error': 'MIDDLEWARE_NOT_FOUND',
                'message': 'CSRF middleware not available'
            }), 500
        
        # Validate token
        is_valid = csrf_middleware._is_valid_csrf_token(token)
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'message': 'CSRF token validation completed'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to validate CSRF token: {e}")
        return jsonify({
            'success': False,
            'error': 'VALIDATION_FAILED',
            'message': 'Failed to validate CSRF token'
        }), 500

@csrf_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_csrf_token():
    """Refresh the current CSRF token."""
    try:
        user_id = get_jwt_identity()
        
        # Get CSRF middleware instance
        csrf_middleware = getattr(current_app, 'csrf_middleware', None)
        if not csrf_middleware:
            # Fallback: create a new instance
            csrf_middleware = EnhancedCSRFMiddleware(current_app)
        
        # Generate new token
        new_token = csrf_middleware.generate_csrf_token(user_id)
        
        # Create response with new token
        response = jsonify({
            'success': True,
            'csrf_token': new_token,
            'message': 'CSRF token refreshed successfully'
        })
        
        # Set new CSRF token as cookie
        response.set_cookie(
            'csrf_token',
            new_token,
            max_age=3600,  # 1 hour
            secure=current_app.config.get('SESSION_COOKIE_SECURE', True),
            httponly=False,  # Allow JavaScript access
            samesite='Strict'
        )
        
        return response, 200
        
    except Exception as e:
        logger.error(f"Failed to refresh CSRF token: {e}")
        return jsonify({
            'success': False,
            'error': 'TOKEN_REFRESH_FAILED',
            'message': 'Failed to refresh CSRF token'
        }), 500
