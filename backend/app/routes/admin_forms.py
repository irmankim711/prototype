"""
Enhanced Admin Form Management API
Provides CRUD operations for form management with proper validation and error handling
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from .. import db
from ..models import Form, User
from ..decorators import require_permission, get_current_user
import json
import uuid

admin_forms_bp = Blueprint('admin_forms', __name__)

# Form field validation schema
ALLOWED_FIELD_TYPES = [
    'text', 'textarea', 'email', 'number', 'tel', 'url', 'password',
    'select', 'radio', 'checkbox', 'date', 'time', 'datetime-local',
    'file', 'range', 'color', 'hidden'
]

def validate_form_data(data):
    """Validate form data structure and content"""
    errors = []
    
    # Required fields
    if not data.get('title'):
        errors.append('Title is required')
    elif len(data['title'].strip()) < 3:
        errors.append('Title must be at least 3 characters long')
    
    # Optional but validated fields
    if 'description' in data and len(data['description']) > 1000:
        errors.append('Description cannot exceed 1000 characters')
    
    # External URL validation
    if data.get('external_url'):
        url = data['external_url'].strip()
        if not (url.startswith('http://') or url.startswith('https://')):
            errors.append('External URL must start with http:// or https://')
    
    # Schema validation (fields array)
    if 'schema' in data and data['schema']:
        if not isinstance(data['schema'], list):
            errors.append('Schema must be an array of field objects')
        else:
            for i, field in enumerate(data['schema']):
                if not isinstance(field, dict):
                    errors.append(f'Field {i+1} must be an object')
                    continue
                
                if not field.get('type') in ALLOWED_FIELD_TYPES:
                    errors.append(f'Field {i+1} has invalid type: {field.get("type")}')
                
                if not field.get('label'):
                    errors.append(f'Field {i+1} must have a label')
                
                if not field.get('id'):
                    errors.append(f'Field {i+1} must have an id')
    
    return errors

@admin_forms_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_forms():
    """Get all forms for admin management"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        # Get filter parameters
        is_public = request.args.get('is_public')
        is_active = request.args.get('is_active')
        search = request.args.get('search', '').strip()
        
        # Build query
        query = Form.query
        
        # Apply filters
        if is_public is not None:
            query = query.filter(Form.is_public == (is_public.lower() == 'true'))
        
        if is_active is not None:
            query = query.filter(Form.is_active == (is_active.lower() == 'true'))
        
        if search:
            query = query.filter(
                db.or_(
                    Form.title.ilike(f'%{search}%'),
                    Form.description.ilike(f'%{search}%')
                )
            )
        
        # Order by creation date (newest first)
        query = query.order_by(Form.created_at.desc())
        
        # Apply pagination
        forms_paginated = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialize forms
        forms_data = []
        for form in forms_paginated.items:
            field_count = 0
            if form.schema and isinstance(form.schema, list):
                field_count = len(form.schema)
            
            forms_data.append({
                'id': form.id,
                'title': form.title,
                'description': form.description,
                'is_public': form.is_public,
                'is_active': form.is_active,
                'external_url': form.external_url,
                'field_count': field_count,
                'view_count': form.view_count or 0,
                'submission_count': len(form.submissions) if form.submissions else 0,
                'created_at': form.created_at.isoformat() if form.created_at else None,
                'updated_at': form.updated_at.isoformat() if form.updated_at else None,
                'creator': {
                    'id': form.creator.id,
                    'name': form.creator.full_name,
                    'email': form.creator.email
                } if form.creator else None
            })
        
        return jsonify({
            'forms': forms_data,
            'pagination': {
                'page': page,
                'pages': forms_paginated.pages,
                'per_page': per_page,
                'total': forms_paginated.total,
                'has_next': forms_paginated.has_next,
                'has_prev': forms_paginated.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching forms: {str(e)}")
        return jsonify({'error': 'Failed to fetch forms'}), 500

@admin_forms_bp.route('/', methods=['POST'])
@jwt_required()
def create_form():
    """Create a new form"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate form data
        validation_errors = validate_form_data(data)
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        # Create new form
        new_form = Form()
        new_form.title = data['title'].strip()
        new_form.description = data.get('description', '').strip()
        new_form.schema = data.get('schema', [])
        new_form.is_public = data.get('is_public', False)
        new_form.is_active = data.get('is_active', True)
        new_form.external_url = data.get('external_url', '').strip() or None
        new_form.creator_id = current_user.id
        new_form.access_key = str(uuid.uuid4())  # Generate unique access key
        
        db.session.add(new_form)
        db.session.commit()
        
        # Return created form
        field_count = len(new_form.schema) if new_form.schema else 0
        
        return jsonify({
            'message': 'Form created successfully',
            'form': {
                'id': new_form.id,
                'title': new_form.title,
                'description': new_form.description,
                'is_public': new_form.is_public,
                'is_active': new_form.is_active,
                'external_url': new_form.external_url,
                'field_count': field_count,
                'created_at': new_form.created_at.isoformat(),
                'access_key': new_form.access_key
            }
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error creating form: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error creating form: {str(e)}")
        return jsonify({'error': 'Failed to create form'}), 500

@admin_forms_bp.route('/<int:form_id>', methods=['GET'])
@jwt_required()
def get_form(form_id):
    """Get a specific form by ID"""
    try:
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        field_count = len(form.schema) if form.schema else 0
        
        return jsonify({
            'id': form.id,
            'title': form.title,
            'description': form.description,
            'schema': form.schema,
            'is_public': form.is_public,
            'is_active': form.is_active,
            'external_url': form.external_url,
            'field_count': field_count,
            'view_count': form.view_count or 0,
            'submission_count': len(form.submissions) if form.submissions else 0,
            'created_at': form.created_at.isoformat() if form.created_at else None,
            'updated_at': form.updated_at.isoformat() if form.updated_at else None,
            'access_key': form.access_key,
            'creator': {
                'id': form.creator.id,
                'name': form.creator.full_name,
                'email': form.creator.email
            } if form.creator else None
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching form {form_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch form'}), 500

@admin_forms_bp.route('/<int:form_id>', methods=['PUT'])
@jwt_required()
def update_form(form_id):
    """Update an existing form"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate form data
        validation_errors = validate_form_data(data)
        if validation_errors:
            return jsonify({'error': 'Validation failed', 'details': validation_errors}), 400
        
        # Update form fields
        if 'title' in data:
            form.title = data['title'].strip()
        if 'description' in data:
            form.description = data['description'].strip()
        if 'schema' in data:
            form.schema = data['schema']
        if 'is_public' in data:
            form.is_public = data['is_public']
        if 'is_active' in data:
            form.is_active = data['is_active']
        if 'external_url' in data:
            form.external_url = data['external_url'].strip() or None
        
        form.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Return updated form
        field_count = len(form.schema) if form.schema else 0
        
        return jsonify({
            'message': 'Form updated successfully',
            'form': {
                'id': form.id,
                'title': form.title,
                'description': form.description,
                'is_public': form.is_public,
                'is_active': form.is_active,
                'external_url': form.external_url,
                'field_count': field_count,
                'updated_at': form.updated_at.isoformat()
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error updating form {form_id}: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error updating form {form_id}: {str(e)}")
        return jsonify({'error': 'Failed to update form'}), 500

@admin_forms_bp.route('/<int:form_id>', methods=['DELETE'])
@jwt_required()
def delete_form(form_id):
    """Delete a form"""
    try:
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        # Store form info for response
        form_title = form.title
        
        # Delete form (cascade will handle related records)
        db.session.delete(form)
        db.session.commit()
        
        return jsonify({
            'message': f'Form "{form_title}" deleted successfully'
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error deleting form {form_id}: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error deleting form {form_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete form'}), 500

@admin_forms_bp.route('/<int:form_id>/toggle/<string:field>', methods=['PATCH'])
@jwt_required()
def toggle_form_field(form_id, field):
    """Toggle boolean fields (is_public, is_active)"""
    try:
        if field not in ['is_public', 'is_active']:
            return jsonify({'error': 'Invalid field. Only is_public and is_active can be toggled'}), 400
        
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        # Toggle the field
        current_value = getattr(form, field)
        setattr(form, field, not current_value)
        form.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Form {field} toggled successfully',
            'form': {
                'id': form.id,
                'title': form.title,
                field: getattr(form, field),
                'updated_at': form.updated_at.isoformat()
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error toggling {field} for form {form_id}: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error toggling {field} for form {form_id}: {str(e)}")
        return jsonify({'error': f'Failed to toggle {field}'}), 500

@admin_forms_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_form_stats():
    """Get form statistics for admin dashboard"""
    try:
        total_forms = Form.query.count()
        public_forms = Form.query.filter_by(is_public=True).count()
        active_forms = Form.query.filter_by(is_active=True).count()
        external_forms = Form.query.filter(Form.external_url.isnot(None)).count()
        
        # Recent forms (last 7 days)
        from datetime import datetime, timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_forms = Form.query.filter(Form.created_at >= week_ago).count()
        
        return jsonify({
            'total_forms': total_forms,
            'public_forms': public_forms,
            'active_forms': active_forms,
            'external_forms': external_forms,
            'recent_forms': recent_forms,
            'private_forms': total_forms - public_forms,
            'inactive_forms': total_forms - active_forms
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error fetching form stats: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500
