from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from ..models import db, User, UserRole, Permission
from ..decorators import require_permission, require_role, get_current_user

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.full_name,
        'role': user.role.value,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat(),
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'permissions': [p.value for p in user.get_permissions()]
    }), 200

@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Profile updated successfully'}), 200

@users_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user's password."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    if len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long'}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200

@users_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    """Get user settings"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Return default settings - in a real app this would come from a settings table
    settings = {
        'notifications': {
            'email': True,
            'push': False,
            'sms': False
        },
        'preferences': {
            'theme': 'light',
            'language': 'en',
            'timezone': 'UTC'
        },
        'privacy': {
            'profile_visible': True,
            'data_sharing': False
        }
    }
    
    return jsonify(settings), 200
@jwt_required()
def get_settings():
    """Get user settings (placeholder for future implementation)."""
    return jsonify({
        'notifications': True,
        'theme': 'light',
        'language': 'en',
        'timezone': 'UTC'
    }), 200

@users_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    """Update user settings"""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # In a real app, you'd save these to a settings table
    # For now, just return success
    
    return jsonify({'message': 'Settings updated successfully'}), 200

# Admin-only user management endpoints
@users_bp.route('/', methods=['GET'])
@jwt_required()
@require_permission(Permission.VIEW_USERS)
def list_users():
    """List all users (admin/manager only)."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    role_filter = request.args.get('role')
    
    query = User.query
    
    if role_filter:
        try:
            role = UserRole(role_filter)
            query = query.filter_by(role=role)
        except ValueError:
            return jsonify({'error': 'Invalid role filter'}), 400
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [{
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role.value,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        } for user in users.items],
        'pagination': {
            'page': users.page,
            'pages': users.pages,
            'per_page': users.per_page,
            'total': users.total
        }
    }), 200

@users_bp.route('/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@require_permission(Permission.MANAGE_USERS)
def update_user_role(user_id):
    """Update user's role (admin only)."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    new_role = data.get('role')
    
    try:
        new_role = UserRole(new_role)
        user.role = new_role
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': f'User role updated to {new_role.value}'}), 200
    except ValueError:
        return jsonify({'error': 'Invalid role'}), 400

@users_bp.route('/<int:user_id>/status', methods=['PUT'])
@jwt_required()
@require_permission(Permission.MANAGE_USERS)
def update_user_status(user_id):
    """Update user's active status (admin only)."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    is_active = data.get('is_active')
    
    if is_active is None:
        return jsonify({'error': 'is_active field is required'}), 400
    
    user.is_active = bool(is_active)
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    status_text = 'activated' if is_active else 'deactivated'
    return jsonify({'message': f'User {status_text} successfully'}), 200
    
    try:
        role = UserRole(new_role)
        user.role = role
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': f'User role updated to {role.value}'}), 200
    except ValueError:
        return jsonify({'error': 'Invalid role'}), 400

@users_bp.route('/<int:user_id>/status', methods=['PUT'])
@jwt_required()
@require_permission(Permission.MANAGE_USERS)
def update_user_status(user_id):
    """Activate/deactivate user (admin only)."""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    is_active = data.get('is_active')
    
    if is_active is None:
        return jsonify({'error': 'is_active field is required'}), 400
    
    user.is_active = bool(is_active)
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    status = 'activated' if is_active else 'deactivated'
    return jsonify({'message': f'User {status} successfully'}), 200
