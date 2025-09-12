from flask import Blueprint, request, jsonify, current_app, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from datetime import datetime, timedelta
from .. import db
from ..models import QuickAccessToken, Form, FormSubmission
from ..services.twilio_service import twilio_service
import random
import string
import secrets
import hashlib
import requests
import os
# from ..services.email_service import send_otp_email  # Will implement later
import logging

quick_auth_bp = Blueprint('quick_auth', __name__)
limiter = Limiter(key_func=get_remote_address)

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def generate_access_token():
    """Generate a secure access token"""
    return secrets.token_urlsafe(32)

def verify_google_token(token):
    """Verify Google OAuth token with Google's API"""
    try:
        # Use Google's tokeninfo endpoint to verify the token
        response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token}",
            timeout=10
        )
        
        if response.status_code == 200:
            token_info = response.json()
            
            # Verify the token is for our app
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            if token_info.get('aud') == client_id:
                return {
                    'valid': True,
                    'email': token_info.get('email'),
                    'name': token_info.get('name'),
                    'picture': token_info.get('picture'),
                    'sub': token_info.get('sub')  # Google user ID
                }
        
        return {'valid': False, 'error': 'Invalid token'}
        
    except requests.RequestException as e:
        current_app.logger.error(f"Google token verification failed: {e}")
        return {'valid': False, 'error': 'Token verification failed'}

@quick_auth_bp.route('/request-otp', methods=['POST', 'OPTIONS'])
@limiter.limit("5 per minute")
def request_otp():
    """Request OTP for quick access authentication"""
    
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
        phone = data.get('phone')  # New: support phone numbers
        name = data.get('name', 'Guest User')
        
        # Clean phone number (remove spaces)
        if phone:
            phone = phone.strip().replace(' ', '')
        
        current_app.logger.info(f"OTP request received - Email: {email}, Phone: {phone}")
        
        if not email and not phone:
            return jsonify({'error': 'Email or phone number is required'}), 400
        
        # Basic validation
        if phone and len(phone.replace('+', '').replace(' ', '')) < 10:
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        if email and '@' not in email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Use phone as primary identifier if provided, otherwise email
        identifier = phone or email
        contact_method = 'phone' if phone else 'email'
        
        # For phone-only requests, create a dummy email to satisfy DB constraints
        if phone and not email:
            # Create a unique dummy email to avoid conflicts  
            clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '')
            timestamp = int(datetime.utcnow().timestamp())
            email = f"phone_{clean_phone}_{timestamp}@temp.local"
        
        # Generate OTP and token
        otp_code = generate_otp()
        access_token = generate_access_token()
        
        # Set expiration (10 minutes for OTP)
        otp_expires = datetime.utcnow() + timedelta(minutes=10)
        token_expires = datetime.utcnow() + timedelta(hours=24)  # Token valid for 24 hours
        
        # Create or update quick access token
        existing_token = QuickAccessToken.query.filter_by(email=email).first() if email else None
        if not existing_token and phone:
            existing_token = QuickAccessToken.query.filter_by(phone=phone).first()
        
        if existing_token:
            # Update existing token
            existing_token.otp_code = otp_code
            existing_token.otp_expires_at = otp_expires
            existing_token.otp_verified = False
            existing_token.expires_at = token_expires
            if phone:
                existing_token.phone = phone
            token_record = existing_token
        else:
            # Create new token
            token_record = QuickAccessToken(
                token=access_token,
                email=email,
                phone=phone,
                name=name,
                otp_code=otp_code,
                otp_expires_at=otp_expires,
                expires_at=token_expires,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(token_record)
        
        db.session.commit()
        
        # Send OTP via email or SMS
        try:
            if contact_method == 'phone':
                # Send SMS using Twilio Verify
                if twilio_service.is_verify_configured():
                    verify_result = twilio_service.send_verification_code(phone)
                    if verify_result['success']:
                        current_app.logger.info(f"Verification code sent successfully to {phone}")
                        message = 'Verification code sent via SMS'
                        # For Twilio Verify, use a shorter marker that fits in 6 chars
                        token_record.otp_code = 'TWILIO'  # Shorter marker
                        token_record.phone = phone  # Ensure phone is set
                        db.session.commit()  # Save the updated record
                    else:
                        current_app.logger.error(f"Verification sending failed: {verify_result['error']}")
                        return jsonify({'error': f'Failed to send verification code: {verify_result["error"]}'}), 500
                else:
                        current_app.logger.error("Twilio Verify not configured properly")
                        return jsonify({'error': 'SMS verification service not configured'}), 500
            else:
                current_app.logger.info(f"Email OTP for {email}: {otp_code}")
                message = 'OTP sent via email (not implemented yet)'
            
            return jsonify({
                'message': message,
                'token_id': token_record.id,
                'contact_method': contact_method,
                'expires_in': 600  # 10 minutes
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Failed to send verification: {str(e)}")
            return jsonify({'error': 'Failed to send verification'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error in request_otp: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@quick_auth_bp.route('/verify-otp', methods=['POST', 'OPTIONS'])
@limiter.limit("10 per minute")
def verify_otp():
    """Verify OTP and get access token"""
    
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
        
        token_id = data.get('token_id')
        otp_code = data.get('otp_code')
        
        current_app.logger.info(f"OTP verification request - Token ID: {token_id}")
        
        if not token_id or not otp_code:
            return jsonify({'error': 'Token ID and OTP code are required'}), 400
        
        # Find token record
        token_record = QuickAccessToken.query.get(token_id)
        
        if not token_record:
            return jsonify({'error': 'Invalid token'}), 400
        
        # For phone-based verification using Twilio Verify
        elif token_record.phone and token_record.otp_code == 'TWILIO':
            # Use Twilio Verify to check the code
            if twilio_service.is_verify_configured():
                clean_phone = token_record.phone.strip().replace(' ', '')
                verify_result = twilio_service.verify_code(clean_phone, otp_code)
                
                if verify_result['success']:
                    # Mark OTP as verified
                    token_record.otp_verified = True
                    token_record.last_used = datetime.utcnow()
                    db.session.commit()
                    
                    current_app.logger.info(f"Phone verification successful for {clean_phone}")
                else:
                    current_app.logger.error(f"Phone verification failed: {verify_result.get('error', 'Invalid code')}")
                    return jsonify({'error': 'Invalid verification code'}), 400
            else:
                return jsonify({'error': 'Phone verification service not configured'}), 500
        else:
            # Traditional OTP verification (for email)
            # Check if OTP is valid
            if not token_record.otp_code or token_record.otp_code != otp_code:
                return jsonify({'error': 'Invalid OTP code'}), 400
            
            # Check if OTP has expired
            if token_record.otp_expires_at < datetime.utcnow():
                return jsonify({'error': 'OTP has expired'}), 400
            
            # Mark OTP as verified
            token_record.otp_verified = True
            token_record.last_used = datetime.utcnow()
            db.session.commit()
        
        # Create JWT token for session management
        jwt_token = create_access_token(
            identity=f"quick_access:{token_record.id}",
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Authentication successful',
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': 86400,  # 24 hours
            'user_info': {
                'name': token_record.name,
                'email': token_record.email,
                'access_type': 'quick_access'
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in verify_otp: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@quick_auth_bp.route('/access-with-token', methods=['POST'])
@limiter.limit("20 per minute")
def access_with_token():
    """Direct access with pre-shared token (for events/invites)"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        
        if not access_token:
            return jsonify({'error': 'Access token is required'}), 400
        
        # Find token record
        token_record = QuickAccessToken.query.filter_by(token=access_token).first()
        
        if not token_record or not token_record.is_valid():
            return jsonify({'error': 'Invalid or expired access token'}), 400
        
        # Create JWT token for session management
        jwt_token = create_access_token(
            identity=f"quick_access:{token_record.id}",
            expires_delta=timedelta(hours=24)
        )
        
        # Update last used
        token_record.last_used = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Authentication successful',
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': 86400,  # 24 hours
            'user_info': {
                'name': token_record.name,
                'email': token_record.email,
                'access_type': 'quick_access'
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in access_with_token: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@quick_auth_bp.route('/validate-access', methods=['GET'])
@jwt_required()
def validate_access():
    """Validate current quick access session"""
    try:
        identity = get_jwt_identity()
        
        if not identity.startswith('quick_access:'):
            return jsonify({'error': 'Invalid session type'}), 400
        
        token_id = identity.split(':')[1]
        token_record = QuickAccessToken.query.get(token_id)
        
        if not token_record or not token_record.is_valid():
            return jsonify({'error': 'Session expired or invalid'}), 401
        
        return jsonify({
            'valid': True,
            'user_info': {
                'name': token_record.name,
                'email': token_record.email,
                'access_type': 'quick_access',
                'uses_remaining': token_record.max_uses - token_record.current_uses if token_record.max_uses else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in validate_access: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Helper function to check quick access permission
def check_quick_access_permission(form_id=None):
    """Check if current user has quick access permission"""
    try:
        identity = get_jwt_identity()
        
        if not identity or not identity.startswith('quick_access:'):
            return False, None
        
        token_id = identity.split(':')[1]
        token_record = QuickAccessToken.query.get(token_id)
        
        if not token_record or not token_record.is_valid():
            return False, None
        
        if form_id and not token_record.can_access_form(form_id):
            return False, None
        
        return True, token_record
        
    except Exception:
        return False, None

@quick_auth_bp.route('/google-signin', methods=['POST', 'OPTIONS'])
@limiter.limit("10 per minute")
def google_signin():
    """Authenticate with Google Sign-In token"""
    
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
        
        google_token = data.get('googleToken', '').strip()
        
        current_app.logger.info(f"Google signin request received with token: {google_token[:20]}...")
        
        if not google_token:
            return jsonify({'error': 'Google token is required'}), 400
        
        # Verify the Google token with Google's API
        verification_result = verify_google_token(google_token)
        
        if not verification_result['valid']:
            return jsonify({'error': verification_result.get('error', 'Invalid Google token')}), 400
        
        # Extract user info from verified token
        google_email = verification_result['email']
        google_name = verification_result['name']
        google_picture = verification_result.get('picture', '')
        google_user_id = verification_result['sub']
        
        # Generate access token
        access_token = generate_access_token()
        
        # Check for existing token for this Google account
        existing_token = QuickAccessToken.query.filter_by(email=google_email).first()
        
        if existing_token:
            # Update existing token
            existing_token.otp_verified = True
            existing_token.last_used = datetime.utcnow()
            existing_token.expires_at = datetime.utcnow() + timedelta(hours=24)
            token_record = existing_token
        else:
            # Create new token
            token_record = QuickAccessToken(
                token=access_token,
                email=google_email,
                name=google_name,
                access_type='google_signin',
                otp_verified=True,  # Google auth bypasses OTP
                expires_at=datetime.utcnow() + timedelta(hours=24),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(token_record)
        
        db.session.commit()
        
        # Create JWT token for session management
        jwt_token = create_access_token(
            identity=f"quick_access:{token_record.id}",
            expires_delta=timedelta(hours=24)
        )
        
        return jsonify({
            'message': 'Google Sign-In successful',
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': 86400,  # 24 hours
            'user_info': {
                'name': token_record.name,
                'email': token_record.email,
                'access_type': 'google_signin'
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in google_signin: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@quick_auth_bp.route('/bypass-login', methods=['POST'])
def bypass_login():
    """Development bypass login - creates a temporary user session"""
    try:
        # Only allow in development mode
        if not current_app.config.get('TESTING', False):
            return jsonify({'error': 'Bypass login not available'}), 403
        
        # Create a JWT token for bypass user
        jwt_token = create_access_token(
            identity='bypass-user',
            expires_delta=timedelta(hours=24)
        )
        
        # Create response with cookie
        response = make_response(jsonify({
            'message': 'Bypass login successful',
            'access_token': jwt_token,
            'token_type': 'Bearer',
            'expires_in': 86400,
            'user_info': {
                'name': 'Bypass User',
                'email': 'bypass@test.com',
                'access_type': 'bypass'
            }
        }))
        
        # Set the JWT token as a cookie for browser-based requests
        response.set_cookie(
            'access_token_cookie',
            jwt_token,
            max_age=86400,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite='Lax'
        )
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error in bypass_login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
