"""
Settings API routes for user preferences and profile settings
✅ SECURITY PATCHED: Updated to use new Firebase auth with UserAdapter
"""
from flask import Blueprint, request, jsonify
from app import db
from app.models.simple_user import SimpleUser
from app.middleware.firebase_auth import require_firebase_auth, get_current_firebase_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

settings_api = Blueprint('settings_api', __name__, url_prefix='/api/settings')

@settings_api.route('', methods=['GET'])
@require_firebase_auth
def get_settings():
    """Get user settings - ✅ PATCHED"""
    try:
        # ✅ SECURITY FIX: Use new UserAdapter pattern
        user_adapter = get_current_firebase_user()
        if not user_adapter:
            return jsonify({'error': 'User not found'}), 404

        # Look up SimpleUser by firebase_uid (not by ID)
        user = SimpleUser.query.filter_by(firebase_uid=user_adapter.firebase_uid).first()

        if not user:
            logger.warning(f"SimpleUser not found for firebase_uid: {user_adapter.firebase_uid}")
            return jsonify({'error': 'User settings not found'}), 404

        settings_data = {
            'general': {
                'companyName': user.company or '',
                'timezone': user.timezone or 'UTC',
                'enableNotifications': user.email_notifications,
                'firstName': user.first_name or '',
                'lastName': user.last_name or '',
                'phone': user.phone or '',
                'jobTitle': user.job_title or '',
                'bio': user.bio or '',
                'avatarUrl': user.avatar_url or ''
            },
            'preferences': {
                'theme': user.theme or 'light',
                'language': user.language or 'en',
                'emailNotifications': user.email_notifications,
                'pushNotifications': user.push_notifications
            },
            'profile': {
                'email': user.email,
                'username': user.username,
                'isVerified': user.is_verified,
                'createdAt': user.created_at.isoformat() if user.created_at else None,
                'lastLogin': user.last_login_at.isoformat() if user.last_login_at else None
            }
        }

        return jsonify(settings_data), 200

    except Exception as e:
        logger.error(f"Get settings error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@settings_api.route('', methods=['POST'])
@require_firebase_auth
def update_settings():
    """Update user settings - ✅ PATCHED"""
    try:
        # ✅ SECURITY FIX: Use new UserAdapter pattern
        user_adapter = get_current_firebase_user()
        if not user_adapter:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Look up SimpleUser by firebase_uid
        user = SimpleUser.query.filter_by(firebase_uid=user_adapter.firebase_uid).first()

        if not user:
            logger.warning(f"SimpleUser not found for firebase_uid: {user_adapter.firebase_uid}")
            return jsonify({'error': 'User not found'}), 404

        # Update general settings
        if 'companyName' in data:
            user.company = data['companyName']
        if 'timezone' in data:
            user.timezone = data['timezone']
        if 'enableNotifications' in data:
            user.email_notifications = data['enableNotifications']
        if 'firstName' in data:
            user.first_name = data['firstName']
        if 'lastName' in data:
            user.last_name = data['lastName']
        if 'phone' in data:
            user.phone = data['phone']
        if 'jobTitle' in data:
            user.job_title = data['jobTitle']
        if 'bio' in data:
            user.bio = data['bio']
        if 'avatarUrl' in data:
            user.avatar_url = data['avatarUrl']

        # Update preferences
        if 'theme' in data:
            user.theme = data['theme']
        if 'language' in data:
            user.language = data['language']
        if 'emailNotifications' in data:
            user.email_notifications = data['emailNotifications']
        if 'pushNotifications' in data:
            user.push_notifications = data['pushNotifications']

        # Update automation settings (if needed for future)
        if 'enableAutoReports' in data:
            # Store in user preferences or separate table
            pass
        if 'enableAutoEmails' in data:
            # Store in user preferences or separate table
            pass
        if 'reportSchedule' in data:
            # Store in user preferences or separate table
            pass

        user.updated_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Settings updated for user {user_adapter.id} ({user_adapter.email})")

        return jsonify({
            'message': 'Settings updated successfully',
            'settings': {
                'general': {
                    'companyName': user.company,
                    'timezone': user.timezone,
                    'enableNotifications': user.email_notifications
                },
                'preferences': {
                    'theme': user.theme,
                    'language': user.language,
                    'emailNotifications': user.email_notifications,
                    'pushNotifications': user.push_notifications
                }
            }
        }), 200

    except Exception as e:
        logger.error(f"Update settings error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_api.route('/profile', methods=['GET'])
@require_firebase_auth
def get_profile():
    """Get user profile - ✅ PATCHED"""
    try:
        # ✅ SECURITY FIX: Use new UserAdapter pattern
        user_adapter = get_current_firebase_user()
        if not user_adapter:
            return jsonify({'error': 'User not found'}), 404

        # Look up SimpleUser by firebase_uid
        user = SimpleUser.query.filter_by(firebase_uid=user_adapter.firebase_uid).first()

        if not user:
            logger.warning(f"SimpleUser not found for firebase_uid: {user_adapter.firebase_uid}")
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user.to_dict()), 200

    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@settings_api.route('/profile', methods=['PUT'])
@require_firebase_auth
def update_profile():
    """Update user profile - ✅ PATCHED"""
    try:
        # ✅ SECURITY FIX: Use new UserAdapter pattern
        user_adapter = get_current_firebase_user()
        if not user_adapter:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Look up SimpleUser by firebase_uid
        user = SimpleUser.query.filter_by(firebase_uid=user_adapter.firebase_uid).first()

        if not user:
            logger.warning(f"SimpleUser not found for firebase_uid: {user_adapter.firebase_uid}")
            return jsonify({'error': 'User not found'}), 404

        # Update allowed profile fields
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'company',
            'job_title', 'bio', 'avatar_url', 'timezone',
            'language', 'theme'
        ]

        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        user.updated_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Profile updated for user {user_adapter.id} ({user_adapter.email})")

        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@settings_api.route('/notifications', methods=['PUT'])
@require_firebase_auth
def update_notifications():
    """Update notification preferences - ✅ PATCHED"""
    try:
        # ✅ SECURITY FIX: Use new UserAdapter pattern
        user_adapter = get_current_firebase_user()
        if not user_adapter:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()

        # Look up SimpleUser by firebase_uid
        user = SimpleUser.query.filter_by(firebase_uid=user_adapter.firebase_uid).first()

        if not user:
            logger.warning(f"SimpleUser not found for firebase_uid: {user_adapter.firebase_uid}")
            return jsonify({'error': 'User not found'}), 404

        if 'email_notifications' in data:
            user.email_notifications = data['email_notifications']
        if 'push_notifications' in data:
            user.push_notifications = data['push_notifications']

        user.updated_at = datetime.utcnow()
        db.session.commit()

        logger.info(f"Notification preferences updated for user {user_adapter.id} ({user_adapter.email})")

        return jsonify({
            'message': 'Notification preferences updated successfully',
            'email_notifications': user.email_notifications,
            'push_notifications': user.push_notifications
        }), 200

    except Exception as e:
        logger.error(f"Update notifications error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
