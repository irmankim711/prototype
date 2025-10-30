"""
Firebase Authentication Routes
Handles Firebase OAuth integration endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging
import traceback

from .. import db
from ..middleware.firebase_auth import firebase_auth_manager, require_firebase_auth, get_current_firebase_user
from ..models.production.user_models import User

logger = logging.getLogger(__name__)

firebase_auth_bp = Blueprint('firebase_auth', __name__, url_prefix='/auth')

@firebase_auth_bp.route('/firebase-sync', methods=['POST', 'OPTIONS'])
@firebase_auth_bp.route('/firebase-login', methods=['POST', 'OPTIONS'])  # Alias for frontend compatibility
def firebase_sync():
    """Sync Firebase user with backend database with comprehensive error handling"""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    request_id = f"sync_{int(datetime.utcnow().timestamp() * 1000)}"
    logger.info(f"🔄 [{request_id}] Firebase sync request started")

    try:
        # Log request details for debugging
        logger.debug(f"📋 [{request_id}] Request headers: {dict(request.headers)}")
        logger.debug(f"📋 [{request_id}] Request remote addr: {request.remote_addr}")

        # Validate Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.warning(f"❌ [{request_id}] No authorization header provided")
            return jsonify({
                'error': 'No authorization header provided',
                'code': 'MISSING_AUTH_HEADER',
                'request_id': request_id
            }), 401
        
        # Parse Authorization header
        token_parts = auth_header.split(' ')
        if len(token_parts) != 2 or token_parts[0] != 'Bearer':
            logger.warning(f"❌ [{request_id}] Invalid authorization header format: {auth_header[:20]}...")
            return jsonify({
                'error': 'Invalid authorization header format',
                'code': 'INVALID_AUTH_HEADER',
                'request_id': request_id,
                'expected_format': 'Bearer <firebase_id_token>'
            }), 401
        
        id_token = token_parts[1]
        logger.debug(f"🔍 [{request_id}] Extracted Firebase token (length: {len(id_token)})")
        
        # Check Firebase initialization status
        if not firebase_auth_manager._initialized:
            logger.error(f"❌ [{request_id}] Firebase not initialized")
            return jsonify({
                'error': 'Firebase authentication service unavailable',
                'code': 'FIREBASE_NOT_INITIALIZED',
                'request_id': request_id,
                'details': firebase_auth_manager._initialization_error
            }), 503
        
        # Verify Firebase token
        logger.debug(f"🔍 [{request_id}] Verifying Firebase token...")
        decoded_token = firebase_auth_manager.verify_token(id_token)
        
        if not decoded_token:
            logger.warning(f"❌ [{request_id}] Firebase token verification failed")
            return jsonify({
                'error': 'Invalid or expired Firebase token',
                'code': 'INVALID_FIREBASE_TOKEN',
                'request_id': request_id,
                'suggestion': 'Please log in again to refresh your authentication token'
            }), 401
        
        # Log successful token verification
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        logger.info(f"✅ [{request_id}] Token verified for user: {email} (UID: {firebase_uid})")
        
        # Get and validate additional user data from request body
        try:
            data = request.get_json() or {}
            logger.debug(f"📋 [{request_id}] Additional data received: {list(data.keys())}")
        except Exception as json_error:
            logger.warning(f"⚠️ [{request_id}] Invalid JSON in request body: {str(json_error)}")
            data = {}
        
        # Validate request data
        if data:
            allowed_fields = ['firstName', 'lastName', 'displayName', 'phoneNumber', 'company', 'jobTitle']
            invalid_fields = [field for field in data.keys() if field not in allowed_fields]
            if invalid_fields:
                logger.warning(f"⚠️ [{request_id}] Invalid fields in request data: {invalid_fields}")
        
        # Create or get user with database transaction
        logger.debug(f"🔍 [{request_id}] Creating or retrieving user...")
        
        try:
            user = firebase_auth_manager.get_or_create_user(decoded_token, data)
            
            if not user:
                logger.error(f"❌ [{request_id}] Failed to create or retrieve user")
                return jsonify({
                    'error': 'Failed to create or retrieve user',
                    'code': 'USER_CREATION_FAILED',
                    'request_id': request_id,
                    'suggestion': 'Please try again or contact support if the issue persists'
                }), 500

            # Log successful user sync
            # Handle both User object and dict from Firestore
            user_email = user.get('email') if isinstance(user, dict) else user.email
            user_id = user.get('id') if isinstance(user, dict) else user.id
            logger.info(f"✅ [{request_id}] User synchronized successfully: {user_email} (ID: {user_id})")
            
            # Prepare response data
            # Handle both User object and dict from Firestore
            if isinstance(user, dict):
                user_dict = {
                    'id': user.get('id'),
                    'email': user.get('email'),
                    'username': user.get('profile', {}).get('displayName', '').split('@')[0] if user.get('profile', {}).get('displayName') else user.get('email', '').split('@')[0],
                    'first_name': user.get('profile', {}).get('firstName', ''),
                    'last_name': user.get('profile', {}).get('lastName', ''),
                    'firebase_uid': user.get('firebaseUid'),
                    'role': user.get('role', 'user'),
                    'is_active': user.get('isActive', True),
                    'is_verified': user.get('isVerified', False)
                }
            else:
                user_dict = user.to_dict()

            response_data = {
                'success': True,
                'message': 'User synchronized successfully',
                'request_id': request_id,
                'user': user_dict,
                'sync_timestamp': datetime.utcnow().isoformat()
            }
            
            # Add sync metadata
            response_data['sync_metadata'] = {
                'firebase_uid': firebase_uid,
                'email_verified': decoded_token.get('email_verified', False),
                'auth_time': decoded_token.get('auth_time'),
                'provider': decoded_token.get('firebase', {}).get('sign_in_provider', 'unknown')
            }
            
            logger.info(f"✅ [{request_id}] Firebase sync completed successfully")
            return jsonify(response_data), 200
            
        except Exception as user_error:
            logger.error(f"❌ [{request_id}] User creation/sync error: {str(user_error)}")
            logger.error(f"📋 [{request_id}] Stack trace: {traceback.format_exc()}")
            
            # Ensure database rollback
            try:
                db.session.rollback()
            except Exception as rollback_error:
                logger.error(f"❌ [{request_id}] Database rollback failed: {str(rollback_error)}")
            
            return jsonify({
                'error': 'User synchronization failed',
                'code': 'USER_SYNC_ERROR',
                'request_id': request_id,
                'details': str(user_error) if current_app.debug else 'Internal error during user sync'
            }), 500
        
    except Exception as e:
        logger.error(f"❌ [{request_id}] Unexpected firebase-sync error: {str(e)}")
        logger.error(f"📋 [{request_id}] Stack trace: {traceback.format_exc()}")
        
        # Ensure database rollback
        try:
            db.session.rollback()
        except Exception as rollback_error:
            logger.error(f"❌ [{request_id}] Database rollback failed: {str(rollback_error)}")
        
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_SERVER_ERROR',
            'request_id': request_id,
            'message': str(e) if current_app.debug else 'An unexpected error occurred'
        }), 500

@firebase_auth_bp.route('/profile', methods=['GET'])
@require_firebase_auth
def get_profile():
    """Get current user profile (Firebase authenticated)"""
    try:
        user = get_current_firebase_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve profile'}), 500

@firebase_auth_bp.route('/profile', methods=['PUT'])
@require_firebase_auth
def update_profile():
    """Update current user profile (Firebase authenticated)"""
    try:
        user = get_current_firebase_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'username', 'phone', 
            'company', 'job_title', 'bio', 'avatar_url'
        ]
        
        updated_fields = []
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
                updated_fields.append(field)
        
        if updated_fields:
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Profile updated for user {user.id}: {updated_fields}")
            
            return jsonify({
                'message': 'Profile updated successfully',
                'updated_fields': updated_fields,
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'message': 'No fields to update'}), 200
        
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Profile update failed'}), 500

@firebase_auth_bp.route('/user-info', methods=['GET'])
@require_firebase_auth
def get_user_info():
    """Get current user information (Firebase authenticated)"""
    try:
        user = get_current_firebase_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Return comprehensive user info
        user_info = user.to_dict()
        
        # Add Firebase-specific info
        firebase_token = getattr(request, 'firebase_token', None)
        if firebase_token:
            user_info['firebase_info'] = {
                'firebase_uid': firebase_token.get('uid'),
                'email_verified': firebase_token.get('email_verified', False),
                'auth_time': firebase_token.get('auth_time'),
                'firebase_provider': firebase_token.get('firebase', {}).get('sign_in_provider')
            }
        
        return jsonify(user_info), 200
        
    except Exception as e:
        logger.error(f"User info error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve user info'}), 500

@firebase_auth_bp.route('/verify-token', methods=['POST', 'OPTIONS'])
def verify_token():
    """Verify Firebase token (utility endpoint)"""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'valid': False, 'error': 'No authorization header'}), 401
        
        token_parts = auth_header.split(' ')
        if len(token_parts) != 2 or token_parts[0] != 'Bearer':
            return jsonify({'valid': False, 'error': 'Invalid header format'}), 401
        
        id_token = token_parts[1]
        decoded_token = firebase_auth_manager.verify_token(id_token)
        
        if decoded_token:
            return jsonify({
                'valid': True,
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False)
            }), 200
        else:
            return jsonify({'valid': False, 'error': 'Invalid token'}), 401
            
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({'valid': False, 'error': 'Verification failed'}), 500

@firebase_auth_bp.route('/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Logout user (Firebase authenticated) - Works even with expired tokens"""
    # Handle OPTIONS request for CORS preflight
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        logger.info("🔄 Logout endpoint called")

        # Try to get user info if token is valid (optional)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.replace('Bearer ', '')
                if firebase_auth_manager._initialized:
                    decoded_token = firebase_auth_manager.verify_token(token)
                    if decoded_token:
                        email = decoded_token.get('email')
                        firebase_uid = decoded_token.get('uid')

                        # Try to update user logout time (optional, non-critical)
                        try:
                            from ..models.production.user_models import User
                            user = User.query.filter_by(firebase_uid=firebase_uid).first()
                            if user:
                                user.updated_at = datetime.utcnow()
                                db.session.commit()
                                logger.info(f"✅ User {user.id} ({email}) logged out")
                        except Exception as db_error:
                            # Don't fail logout if DB update fails
                            logger.warning(f"⚠️ Could not update user logout time: {str(db_error)}")
                            try:
                                db.session.rollback()
                            except:
                                pass
            except Exception as token_error:
                # Token might be expired or invalid - that's OK for logout
                logger.info(f"ℹ️ Logout with invalid/expired token: {str(token_error)}")
                pass

        # Always return success for logout (even with expired/invalid tokens)
        response = jsonify({
            'success': True,
            'message': 'Logout successful'
        })

        # Clear any cookies that might exist
        response.set_cookie('session', '', expires=0, path='/')
        response.set_cookie('remember_token', '', expires=0, path='/')

        logger.info("✅ Logout completed successfully")
        return response, 200

    except Exception as e:
        # Even if there's an error, return success for logout
        # We don't want to prevent users from logging out
        logger.error(f"⚠️ Logout error (returning success anyway): {str(e)}")
        import traceback
        logger.error(f"📋 Stack trace: {traceback.format_exc()}")

        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200

# Health check for Firebase connection
@firebase_auth_bp.route('/firebase-health', methods=['GET'])
def firebase_health():
    """Check Firebase connection health with detailed status"""
    try:
        initialization_status = firebase_auth_manager.get_initialization_status()
        
        health_data = {
            'status': 'healthy' if initialization_status['initialized'] else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'firebase_initialized': initialization_status['initialized'],
            'initialization_attempts': initialization_status['initialization_attempts'],
            'max_attempts': initialization_status['max_attempts'],
            'project_id': initialization_status['project_id'],
            'has_service_account_path': initialization_status['has_service_account_path'],
            'has_private_key': initialization_status['has_private_key']
        }
        
        if initialization_status['initialized']:
            health_data['message'] = 'Firebase Admin SDK is ready'
            health_data['app_name'] = initialization_status['app_name']
        else:
            health_data['message'] = 'Firebase Admin SDK not initialized'
            health_data['initialization_error'] = initialization_status['initialization_error']
        
        status_code = 200 if initialization_status['initialized'] else 503
        return jsonify(health_data), status_code
            
    except Exception as e:
        logger.error(f"Firebase health check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Health check failed: {str(e)}'
        }), 500

@firebase_auth_bp.route('/firebase-config-validation', methods=['GET'])
def firebase_config_validation():
    """Validate Firebase configuration and return detailed status"""
    try:
        validation_result = firebase_auth_manager.validate_configuration()
        
        response_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'configuration_valid': validation_result['valid'],
            'validation_details': validation_result
        }
        
        status_code = 200 if validation_result['valid'] else 400
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Firebase configuration validation error: {str(e)}")
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'configuration_valid': False,
            'error': f'Configuration validation failed: {str(e)}'
        }), 500

@firebase_auth_bp.route('/firebase-reinitialize', methods=['POST'])
def firebase_reinitialize():
    """Force reinitialize Firebase (for testing/recovery)"""
    try:
        logger.info("🔄 Manual Firebase reinitialization requested")
        success = firebase_auth_manager.force_reinitialize()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Firebase reinitialized successfully',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Firebase reinitialization failed',
                'timestamp': datetime.utcnow().isoformat(),
                'error': firebase_auth_manager._initialization_error
            }), 500
            
    except Exception as e:
        logger.error(f"Firebase reinitialization error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Reinitialization failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@firebase_auth_bp.route('/firebase-circuit-breaker', methods=['GET'])
def firebase_circuit_breaker_status():
    """Get Firebase circuit breaker status"""
    try:
        circuit_breaker_status = firebase_auth_manager.get_circuit_breaker_status()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'circuit_breaker': circuit_breaker_status
        }), 200
        
    except Exception as e:
        logger.error(f"Circuit breaker status error: {str(e)}")
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'error': f'Failed to get circuit breaker status: {str(e)}'
        }), 500

@firebase_auth_bp.route('/firebase-circuit-breaker/reset', methods=['POST'])
def firebase_circuit_breaker_reset():
    """Manually reset Firebase circuit breaker"""
    try:
        logger.info("🔄 Manual circuit breaker reset requested")
        firebase_auth_manager._reset_circuit_breaker()
        
        return jsonify({
            'success': True,
            'message': 'Circuit breaker reset successfully',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Circuit breaker reset error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Circuit breaker reset failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@firebase_auth_bp.route('/firebase-initialization-history', methods=['GET'])
def firebase_initialization_history():
    """Get Firebase initialization attempt history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(max(limit, 1), 50)  # Limit between 1 and 50
        
        history = firebase_auth_manager.get_initialization_history(limit)
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'initialization_history': history,
            'total_attempts': len(firebase_auth_manager._initialization_history),
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Initialization history error: {str(e)}")
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'error': f'Failed to get initialization history: {str(e)}'
        }), 500