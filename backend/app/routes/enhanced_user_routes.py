"""
Enhanced User Profile Routes
Provides comprehensive user profile management with validation, image upload, and security features
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Any
from werkzeug.utils import secure_filename
from PIL import Image
import io

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import IntegrityError

from ..decorators import get_current_user_id, require_auth
from ..models.production.user_models import User
from ..core.exceptions import ValidationError
from .. import db

logger = logging.getLogger(__name__)

# Create blueprint
enhanced_user_bp = Blueprint('enhanced_users', __name__, url_prefix='/api/users')

# Rate limiter
limiter = Limiter(
    app=current_app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Allowed file extensions for avatar uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_profile_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Validate profile data and return validation errors"""
    errors = {}

    # First name validation
    if 'first_name' in data:
        first_name = data['first_name'].strip() if data['first_name'] else ''
        if len(first_name) > 50:
            errors['first_name'] = 'First name cannot exceed 50 characters'
        elif first_name and not first_name.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            errors['first_name'] = 'First name can only contain letters, spaces, hyphens, and apostrophes'

    # Last name validation
    if 'last_name' in data:
        last_name = data['last_name'].strip() if data['last_name'] else ''
        if len(last_name) > 50:
            errors['last_name'] = 'Last name cannot exceed 50 characters'
        elif last_name and not last_name.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            errors['last_name'] = 'Last name can only contain letters, spaces, hyphens, and apostrophes'

    # Check if at least one name is provided
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    if not first_name and not last_name:
        errors['first_name'] = 'Please provide at least a first name or last name'

    # Username validation
    if 'username' in data and data['username']:
        username = data['username'].strip()
        if len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters'
        elif len(username) > 30:
            errors['username'] = 'Username cannot exceed 30 characters'
        elif not username[0].isalpha():
            errors['username'] = 'Username must start with a letter'
        elif not username.replace('_', '').isalnum():
            errors['username'] = 'Username can only contain letters, numbers, and underscores'

    # Phone validation
    if 'phone' in data and data['phone']:
        phone = data['phone'].strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not phone.replace('+', '').isdigit():
            errors['phone'] = 'Phone number can only contain digits, spaces, and + - ( ) characters'
        elif len(phone.replace('+', '')) < 10:
            errors['phone'] = 'Phone number must be at least 10 digits'

    # Bio validation
    if 'bio' in data and data['bio']:
        if len(data['bio']) > 500:
            errors['bio'] = 'Bio cannot exceed 500 characters'

    # Company validation
    if 'company' in data and data['company']:
        if len(data['company']) > 100:
            errors['company'] = 'Company name cannot exceed 100 characters'

    # Job title validation
    if 'job_title' in data and data['job_title']:
        if len(data['job_title']) > 100:
            errors['job_title'] = 'Job title cannot exceed 100 characters'

    return errors

@enhanced_user_bp.route('/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """Get current user's profile"""
    try:
        from flask import g

        # Get user from g.current_user (set by @require_auth decorator)
        user = getattr(g, 'current_user', None)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Handle both Firestore dict and SQLAlchemy User object
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
                'is_verified': user.get('isVerified', False),
                'avatar_url': user.get('profile', {}).get('photoURL', ''),
                'phone': user.get('profile', {}).get('phoneNumber', ''),
                'bio': user.get('profile', {}).get('bio', ''),
                'company': user.get('profile', {}).get('company', ''),
                'job_title': user.get('profile', {}).get('jobTitle', ''),
            }
        else:
            user_dict = user.to_dict()

        return jsonify({
            'success': True,
            'user': user_dict
        })

    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to fetch profile'
        }), 500

@enhanced_user_bp.route('/profile', methods=['PUT'])
@require_auth
@limiter.limit("10 per minute")
def update_user_profile():
    """Update current user's profile"""
    try:
        from flask import g
        from firebase_admin import firestore

        # Get user from g.current_user (set by @require_auth decorator)
        user = getattr(g, 'current_user', None)
        user_id = get_current_user_id()

        logger.info(f"Update profile request for user_id: {user_id}")

        if not user:
            logger.warning(f"User not found: {user_id}")
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        data = request.get_json()
        logger.info(f"Received profile update data: {data}")

        if not data:
            logger.warning("No data provided in request")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate the data
        validation_errors = validate_profile_data(data)
        logger.info(f"Validation errors: {validation_errors}")
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'validation_errors': validation_errors
            }), 400

        # Handle both Firestore dict and SQLAlchemy User object
        if isinstance(user, dict):
            # Firestore user - update in Firestore
            try:
                from app.middleware.firebase_auth import firebase_auth_manager

                if not firebase_auth_manager._firestore_db:
                    return jsonify({
                        'success': False,
                        'error': 'Firestore not available'
                    }), 503

                # Get Firestore reference
                doc_ref = firebase_auth_manager._firestore_db.collection('users').document(user_id)

                # Build update data with nested profile structure
                update_data = {
                    'profile.firstName': data.get('first_name', ''),
                    'profile.lastName': data.get('last_name', ''),
                    'profile.displayName': data.get('username', user.get('profile', {}).get('displayName', '')),
                    'profile.phoneNumber': data.get('phone', ''),
                    'profile.company': data.get('company', ''),
                    'profile.jobTitle': data.get('job_title', ''),
                    'profile.bio': data.get('bio', ''),
                    'updatedAt': firestore.SERVER_TIMESTAMP
                }

                # Filter out fields that weren't provided
                update_data = {k: v for k, v in update_data.items() if k.split('.')[-1] in ['firstName', 'lastName', 'displayName', 'phoneNumber', 'company', 'jobTitle', 'bio', 'updatedAt'] or k == 'updatedAt'}

                # Update Firestore document
                doc_ref.update(update_data)

                # Get updated user data
                updated_doc = doc_ref.get()
                updated_user = updated_doc.to_dict()
                updated_user['id'] = updated_doc.id

                logger.info(f"✅ Updated Firestore user: {user.get('email')}")

                # Return formatted response
                user_dict = {
                    'id': updated_user.get('id'),
                    'email': updated_user.get('email'),
                    'username': updated_user.get('profile', {}).get('displayName', '').split('@')[0],
                    'first_name': updated_user.get('profile', {}).get('firstName', ''),
                    'last_name': updated_user.get('profile', {}).get('lastName', ''),
                    'firebase_uid': updated_user.get('firebaseUid'),
                    'role': updated_user.get('role', 'user'),
                    'is_active': updated_user.get('isActive', True),
                    'is_verified': updated_user.get('isVerified', False),
                    'avatar_url': updated_user.get('profile', {}).get('photoURL', ''),
                    'phone': updated_user.get('profile', {}).get('phoneNumber', ''),
                    'bio': updated_user.get('profile', {}).get('bio', ''),
                    'company': updated_user.get('profile', {}).get('company', ''),
                    'job_title': updated_user.get('profile', {}).get('jobTitle', ''),
                }

                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'user': user_dict
                })

            except Exception as firestore_error:
                logger.error(f"Firestore update error: {firestore_error}")
                import traceback
                logger.error(traceback.format_exc())
                return jsonify({
                    'success': False,
                    'error': 'Failed to update Firestore profile'
                }), 500
        else:
            # SQLAlchemy user - update in database
            # Check for username uniqueness if username is being changed
            if 'username' in data and data['username'] and data['username'] != user.username:
                existing_user = User.query.filter_by(username=data['username']).first()
                if existing_user:
                    return jsonify({
                        'success': False,
                        'error': 'Username already taken',
                        'validation_errors': {'username': 'This username is already taken'}
                    }), 400

            # Update user fields
            updatable_fields = [
                'first_name', 'last_name', 'username', 'phone', 'company',
                'job_title', 'bio', 'timezone', 'language', 'theme',
                'email_notifications', 'push_notifications'
            ]

            for field in updatable_fields:
                if field in data:
                    # Handle boolean fields
                    if field in ['email_notifications', 'push_notifications']:
                        setattr(user, field, bool(data[field]))
                    else:
                        # Trim string fields
                        value = data[field].strip() if isinstance(data[field], str) else data[field]
                        setattr(user, field, value)

            user.updated_at = datetime.utcnow()

            try:
                db.session.commit()

                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'user': user.to_dict()
                })

            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"Database integrity error: {e}")
                return jsonify({
                    'success': False,
                    'error': 'Database constraint violation'
                }), 400

    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if 'db' in dir():
            db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to update profile'
        }), 500

@enhanced_user_bp.route('/avatar', methods=['POST'])
@require_auth
@limiter.limit("5 per minute")
def upload_avatar():
    """Upload user avatar image"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        if 'avatar' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400

        file = request.files['avatar']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, WEBP'
            }), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': 'File size too large. Maximum size is 5MB'
            }), 400

        # Process and save the image
        try:
            # Read and validate image
            image_data = file.read()
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background

            # Resize image to a reasonable size
            max_size = (400, 400)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Generate unique filename
            file_extension = secure_filename(file.filename).rsplit('.', 1)[1].lower()
            unique_filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"

            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, '..', 'static', 'uploads', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)

            # Save the processed image
            file_path = os.path.join(upload_dir, unique_filename)
            image.save(file_path, format='JPEG', quality=85, optimize=True)

            # Update user's avatar URL
            avatar_url = f"/static/uploads/avatars/{unique_filename}"

            # Delete old avatar if it exists
            if user.avatar_url and user.avatar_url.startswith('/static/uploads/avatars/'):
                old_file_path = os.path.join(current_app.root_path, '..', user.avatar_url.lstrip('/'))
                try:
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete old avatar: {e}")

            user.avatar_url = avatar_url
            user.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Avatar uploaded successfully',
                'avatar_url': avatar_url
            })

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return jsonify({
                'success': False,
                'error': 'Failed to process image'
            }), 400

    except Exception as e:
        logger.error(f"Error uploading avatar: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to upload avatar'
        }), 500

@enhanced_user_bp.route('/change-password', methods=['POST'])
@require_auth
@limiter.limit("3 per minute")
def change_password():
    """Change user password"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')

        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'error': 'Current password and new password are required'
            }), 400

        # Verify current password
        if not user.check_password(current_password):
            return jsonify({
                'success': False,
                'error': 'Current password is incorrect'
            }), 400

        # Validate new password
        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'error': 'New password must be at least 8 characters long'
            }), 400

        # Check if new password is different from current
        if user.check_password(new_password):
            return jsonify({
                'success': False,
                'error': 'New password must be different from current password'
            }), 400

        # Update password
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })

    except Exception as e:
        logger.error(f"Error changing password: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to change password'
        }), 500

@enhanced_user_bp.route('/account', methods=['DELETE'])
@require_auth
@limiter.limit("1 per hour")
def delete_account():
    """Delete user account (soft delete)"""
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Perform soft delete by deactivating account
        user.is_active = False
        user.updated_at = datetime.utcnow()

        # Clear sensitive data
        user.first_name = f"Deleted_{user_id}"
        user.last_name = ""
        user.phone = ""
        user.bio = ""
        user.avatar_url = ""

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Account deactivated successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete account'
        }), 500

@enhanced_user_bp.route('/avatar/<filename>')
def serve_avatar(filename):
    """Serve avatar images"""
    try:
        avatar_dir = os.path.join(current_app.root_path, '..', 'static', 'uploads', 'avatars')
        return send_file(os.path.join(avatar_dir, filename))
    except Exception as e:
        logger.error(f"Error serving avatar: {e}")
        return jsonify({'error': 'File not found'}), 404

# Error handlers
@enhanced_user_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    return jsonify({
        'success': False,
        'error': 'Validation failed',
        'validation_errors': error.errors
    }), 400

@enhanced_user_bp.errorhandler(413)
def handle_file_too_large(error):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 5MB'
    }), 413

@enhanced_user_bp.errorhandler(429)
def handle_rate_limit(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded. Please try again later'
    }), 429