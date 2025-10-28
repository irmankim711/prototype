from flask import Blueprint, request, jsonify, current_app

from ..models import db, User
from ..middleware.firebase_auth import FirebaseAuthManager
import logging
import uuid
from datetime import timedelta

logger = logging.getLogger(__name__)
firebase_auth_bp = Blueprint('firebase_auth', __name__)
firebase_auth = FirebaseAuthManager()

@firebase_auth_bp.route('/firebase-sync', methods=['POST'])
def firebase_sync():
    """
    Endpoint to sync Firebase authentication with backend
    - Verifies Firebase ID token
    - Creates or updates user in database
    - Returns JWT tokens for API authentication
    """
    try:
        # Get Firebase token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        
        firebase_token = auth_header.replace('Bearer ', '')
        
        # Verify Firebase token
        try:
            decoded_token = firebase_auth.verify_token(firebase_token)
            if not decoded_token:
                return jsonify({'error': 'Invalid Firebase token'}), 401
        except Exception as e:
            logger.error(f"Firebase token verification failed: {str(e)}")
            return jsonify({'error': 'Firebase token verification failed'}), 401
        
        # Extract user info from token
        firebase_uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        name = decoded_token.get('name') or email.split('@')[0]
        
        if not firebase_uid or not email:
            return jsonify({'error': 'Incomplete user information in token'}), 400
        
        # Find existing user by firebase_uid or email
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if not user:
            # Try to find by email for existing users
            user = User.query.filter_by(email=email).first()
            
        # Create or update user
        if not user:
            # Create new user
            user = User(
                email=email,
                username=email,
                firebase_uid=firebase_uid,
                display_name=name,
                is_active=True,
                request_id=str(uuid.uuid4())
            )
            db.session.add(user)
        else:
            # Update existing user with Firebase UID if needed
            if not user.firebase_uid:
                user.firebase_uid = firebase_uid
            
            # Update other fields if needed
            if not user.display_name and name:
                user.display_name = name
        
        db.session.commit()
        
        # Create access and refresh tokens
        access_token = ''

        refresh_token = ''
        
        # Return tokens and user info
        return jsonify({
            'success': True,
            'accessToken': access_token,
            'refreshToken': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'displayName': user.display_name,
                'firebaseUid': user.firebase_uid
            }
        })
        
    except Exception as e:
        logger.error(f"Firebase sync error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Firebase sync failed: {str(e)}'}), 500