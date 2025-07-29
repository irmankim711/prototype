from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from datetime import datetime
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from ..models import db, Form, FormSubmission, Permission, User, FormQRCode
from ..decorators import require_permission, get_current_user_id, get_current_user
import json
import uuid
import qrcode
import io
import base64
import os
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
from ..services.form_automation import FormAutomationService
import logging

forms_bp = Blueprint('forms', __name__)
limiter = Limiter(key_func=get_remote_address)

# Form field types and their configurations
FIELD_TYPES = {
    'text': {
        'label': 'Text Input',
        'description': 'Single line text input',
        'icon': 'TextFields',
        'category': 'Basic',
        'color': '#2196F3',
        'validation': ['required', 'minLength', 'maxLength', 'pattern']
    },
    'textarea': {
        'label': 'Text Area',
        'description': 'Multi-line text input',
        'icon': 'Subject',
        'category': 'Basic',
        'color': '#4CAF50',
        'validation': ['required', 'minLength', 'maxLength']
    },
    'email': {
        'label': 'Email',
        'description': 'Email address field',
        'icon': 'Email',
        'category': 'Basic',
        'color': '#FF9800',
        'validation': ['required', 'pattern']
    },
    'number': {
        'label': 'Number',
        'description': 'Numeric input field',
        'icon': 'Numbers',
        'category': 'Basic',
        'color': '#9C27B0',
        'validation': ['required', 'min', 'max']
    },
    'select': {
        'label': 'Dropdown',
        'description': 'Single choice dropdown',
        'icon': 'ArrowDropDown',
        'category': 'Choice',
        'color': '#607D8B',
        'validation': ['required']
    },
    'radio': {
        'label': 'Radio Buttons',
        'description': 'Single choice radio buttons',
        'icon': 'RadioButtonChecked',
        'category': 'Choice',
        'color': '#795548',
        'validation': ['required']
    },
    'checkbox': {
        'label': 'Checkboxes',
        'description': 'Multiple choice checkboxes',
        'icon': 'CheckBox',
        'category': 'Choice',
        'color': '#FF5722',
        'validation': ['required']
    },
    'date': {
        'label': 'Date',
        'description': 'Date picker',
        'icon': 'DateRange',
        'category': 'Date & Time',
        'color': '#3F51B5',
        'validation': ['required', 'min', 'max']
    },
    'time': {
        'label': 'Time',
        'description': 'Time picker',
        'icon': 'AccessTime',
        'category': 'Date & Time',
        'color': '#009688',
        'validation': ['required']
    },
    'datetime': {
        'label': 'Date & Time',
        'description': 'Date and time picker',
        'icon': 'Event',
        'category': 'Date & Time',
        'color': '#673AB7',
        'validation': ['required', 'min', 'max']
    },
    'file': {
        'label': 'File Upload',
        'description': 'File upload field',
        'icon': 'AttachFile',
        'category': 'File',
        'color': '#E91E63',
        'validation': ['required', 'fileType', 'maxSize']
    },
    'phone': {
        'label': 'Phone Number',
        'description': 'Phone number input',
        'icon': 'Phone',
        'category': 'Contact',
        'color': '#00BCD4',
        'validation': ['required', 'pattern']
    },
    'url': {
        'label': 'URL',
        'description': 'Website URL input',
        'icon': 'Link',
        'category': 'Contact',
        'color': '#8BC34A',
        'validation': ['required', 'pattern']
    },
    'rating': {
        'label': 'Rating',
        'description': 'Star rating input',
        'icon': 'Star',
        'category': 'Feedback',
        'color': '#FFC107',
        'validation': ['required', 'min', 'max']
    },
    'location': {
        'label': 'Location',
        'description': 'Location picker',
        'icon': 'LocationOn',
        'category': 'Location',
        'color': '#F44336',
        'validation': ['required']
    }
}

def validate_form_schema(schema):
    """Validate form schema structure"""
    if not isinstance(schema, dict):
        raise BadRequest("Schema must be a JSON object")
    
    if 'fields' not in schema:
        raise BadRequest("Schema must contain 'fields' array")
    
    if not isinstance(schema['fields'], list):
        raise BadRequest("Fields must be an array")
    
    for i, field in enumerate(schema['fields']):
        if not isinstance(field, dict):
            raise BadRequest(f"Field {i} must be an object")
        
        if 'id' not in field:
            raise BadRequest(f"Field {i} must have an 'id'")
        
        if 'type' not in field:
            raise BadRequest(f"Field {i} must have a 'type'")
        
        if field['type'] not in FIELD_TYPES:
            raise BadRequest(f"Field {i} has invalid type '{field['type']}'")
        
        if 'label' not in field:
            raise BadRequest(f"Field {i} must have a 'label'")
    
    return True

def validate_form_data(form_schema, data):
    """Validate submitted form data against schema"""
    errors = []
    
    for field in form_schema.get('fields', []):
        field_id = field['id']
        field_value = data.get(field_id)
        
        # Check required fields
        if field.get('required', False) and (field_value is None or field_value == ''):
            errors.append(f"Field '{field['label']}' is required")
            continue
        
        # Skip validation for empty optional fields
        if field_value is None or field_value == '':
            continue
        
        # Type-specific validation
        field_type = field['type']
        
        if field_type == 'email':
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(field_value)):
                errors.append(f"Field '{field['label']}' must be a valid email address")
        
        elif field_type == 'number':
            try:
                num_value = float(field_value)
                if 'min' in field and num_value < field['min']:
                    errors.append(f"Field '{field['label']}' must be at least {field['min']}")
                if 'max' in field and num_value > field['max']:
                    errors.append(f"Field '{field['label']}' must be at most {field['max']}")
            except ValueError:
                errors.append(f"Field '{field['label']}' must be a number")
        
        elif field_type in ['text', 'textarea']:
            text_value = str(field_value)
            if 'minLength' in field and len(text_value) < field['minLength']:
                errors.append(f"Field '{field['label']}' must be at least {field['minLength']} characters")
            if 'maxLength' in field and len(text_value) > field['maxLength']:
                errors.append(f"Field '{field['label']}' must be at most {field['maxLength']} characters")
        
        elif field_type == 'select':
            if 'options' in field and field_value not in field['options']:
                errors.append(f"Field '{field['label']}' has an invalid option")
        
        elif field_type == 'rating':
            try:
                rating_value = int(field_value)
                if rating_value < 1 or rating_value > 5:
                    errors.append(f"Field '{field['label']}' must be between 1 and 5")
            except ValueError:
                errors.append(f"Field '{field['label']}' must be a number between 1 and 5")
    
    return errors

@forms_bp.route('/', methods=['GET'])
@jwt_required()  # JWT required for forms access
@limiter.limit("100 per hour")
def get_forms():
    """Get all forms for the current user with pagination and filtering."""
    try:
        user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        show_all = request.args.get('show_all', 'false').lower() == 'true'
        status = request.args.get('status')  # active, inactive, all
        search = request.args.get('search', '').strip()
        
        # Build query
        if show_all and user.has_permission(Permission.VIEW_USERS):
            query = Form.query
        else:
            query = Form.query.filter_by(creator_id=user.id)
        
        # Apply status filter
        if status == 'active':
            query = query.filter_by(is_active=True)
        elif status == 'inactive':
            query = query.filter_by(is_active=False)
        # 'all' or no status filter shows all forms
        
        # Apply search filter
        if search:
            query = query.filter(
                Form.title.ilike(f'%{search}%') | 
                Form.description.ilike(f'%{search}%')
            )
        
        # Apply pagination
        forms = query.order_by(desc(Form.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'forms': [{
                'id': form.id,
                'title': form.title,
                'description': form.description,
                'schema': form.schema,
                'is_active': form.is_active,
                'is_public': form.is_public,
                'creator_id': form.creator_id,
                'created_at': form.created_at.isoformat(),
                'updated_at': form.updated_at.isoformat(),
                'submission_count': len(form.submissions),
                'creator_name': form.creator.full_name if form.creator else 'Unknown'
            } for form in forms.items],
            'pagination': {
                'page': forms.page,
                'pages': forms.pages,
                'per_page': forms.per_page,
                'total': forms.total,
                'has_next': forms.has_next,
                'has_prev': forms.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_forms: {str(e)}")
        return jsonify({'error': 'Failed to retrieve forms'}), 500

@forms_bp.route('/<int:form_id>', methods=['GET'])
@jwt_required()
@limiter.limit("200 per hour")
def get_form(form_id):
    """Get a specific form with detailed information."""
    try:
        user = get_current_user()
        form = Form.query.get_or_404(form_id)
        
        # Check permissions
        if not form.is_public and form.creator_id != user.id and not user.has_permission(Permission.VIEW_USERS):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get submission statistics
        total_submissions = len(form.submissions)
        recent_submissions = len([s for s in form.submissions if (datetime.utcnow() - s.submitted_at).days <= 7])
        
        return jsonify({
            'id': form.id,
            'title': form.title,
            'description': form.description,
            'schema': form.schema,
            'is_active': form.is_active,
            'is_public': form.is_public,
            'creator_id': form.creator_id,
            'creator_name': form.creator.full_name if form.creator else 'Unknown',
            'created_at': form.created_at.isoformat(),
            'updated_at': form.updated_at.isoformat(),
            'statistics': {
                'total_submissions': total_submissions,
                'recent_submissions': recent_submissions,
                'submission_rate': round(recent_submissions / 7, 2) if total_submissions > 0 else 0
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_form: {str(e)}")
        return jsonify({'error': 'Failed to retrieve form'}), 500

@forms_bp.route('/', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def create_form():
    """Create a new form with validation."""
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Form title is required'}), 400
        
        if not data.get('schema'):
            return jsonify({'error': 'Form schema is required'}), 400
        
        # Validate schema structure
        try:
            validate_form_schema(data['schema'])
        except BadRequest as e:
            return jsonify({'error': str(e)}), 400
        
        # Create form
        form = Form(
            title=data['title'].strip(),
            description=data.get('description', '').strip(),
            schema=data['schema'],
            is_active=data.get('is_active', True),
            is_public=data.get('is_public', False),
            creator_id=user.id
        )
        
        db.session.add(form)
        db.session.commit()
        
        current_app.logger.info(f"Form '{form.title}' created by user {user.id}")
        
        return jsonify({
            'id': form.id,
            'message': 'Form created successfully',
            'form': {
                'id': form.id,
                'title': form.title,
                'description': form.description,
                'schema': form.schema,
                'is_active': form.is_active,
                'is_public': form.is_public,
                'created_at': form.created_at.isoformat()
            }
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in create_form: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error in create_form: {str(e)}")
        return jsonify({'error': 'Failed to create form'}), 500

@forms_bp.route('/<int:form_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("50 per hour")
def update_form(form_id):
    """Update a form with validation."""
    try:
        user = get_current_user()
        form = Form.query.get_or_404(form_id)
        
        # Check permissions
        if form.creator_id != user.id and not user.has_permission(Permission.UPDATE_TEMPLATE):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields
        if 'title' in data:
            if not data['title'].strip():
                return jsonify({'error': 'Form title cannot be empty'}), 400
            form.title = data['title'].strip()
        
        if 'description' in data:
            form.description = data['description'].strip()
        
        if 'schema' in data:
            try:
                validate_form_schema(data['schema'])
                form.schema = data['schema']
            except BadRequest as e:
                return jsonify({'error': str(e)}), 400
        
        if 'is_active' in data:
            form.is_active = bool(data['is_active'])
        
        if 'is_public' in data:
            form.is_public = bool(data['is_public'])
        
        form.updated_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Form '{form.title}' updated by user {user.id}")
        
        return jsonify({
            'message': 'Form updated successfully',
            'form': {
                'id': form.id,
                'title': form.title,
                'description': form.description,
                'schema': form.schema,
                'is_active': form.is_active,
                'is_public': form.is_public,
                'updated_at': form.updated_at.isoformat()
            }
        }), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_form: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error in update_form: {str(e)}")
        return jsonify({'error': 'Failed to update form'}), 500

@forms_bp.route('/<int:form_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("30 per hour")
def delete_form(form_id):
    """Delete a form (soft delete)."""
    try:
        user = get_current_user()
        form = Form.query.get_or_404(form_id)
        
        # Check permissions
        if form.creator_id != user.id and not user.has_permission(Permission.MANAGE_USERS):
            return jsonify({'error': 'Permission denied'}), 403
        
        # Soft delete
        form.is_active = False
        form.updated_at = datetime.utcnow()
        db.session.commit()
        
        current_app.logger.info(f"Form '{form.title}' deleted by user {user.id}")
        
        return jsonify({'message': 'Form deleted successfully'}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in delete_form: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error in delete_form: {str(e)}")
        return jsonify({'error': 'Failed to delete form'}), 500

@forms_bp.route('/field-types', methods=['GET'])
@jwt_required()
def get_field_types():
    """Get available field types and their configurations."""
    return jsonify({
        'field_types': FIELD_TYPES,
        'categories': {
            'Basic': ['text', 'textarea', 'email', 'number'],
            'Choice': ['select', 'radio', 'checkbox'],
            'Date & Time': ['date', 'time', 'datetime'],
            'File': ['file'],
            'Contact': ['phone', 'url'],
            'Feedback': ['rating'],
            'Location': ['location']
        }
    }), 200

@forms_bp.route('/<int:form_id>/submissions', methods=['POST'])
@limiter.limit("10 per minute")
def submit_form(form_id):
    """Submit a form (public endpoint with validation)."""
    try:
        form = Form.query.filter_by(id=form_id, is_active=True).first_or_404()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate form data
        validation_errors = validate_form_data(form.schema, data.get('data', {}))
        if validation_errors:
            return jsonify({
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Get current user if authenticated
        user_id = get_current_user_id()
        submitter_email = data.get('email')
        
        # For public forms, allow anonymous submissions
        if not form.is_public and not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Create submission
        submission = FormSubmission(
            form_id=form.id,
            data=data['data'],
            submitter_id=user_id,
            submitter_email=submitter_email
        )
        
        db.session.add(submission)
        db.session.commit()
        
        current_app.logger.info(f"Form submission created for form {form_id}")
        
        return jsonify({
            'id': submission.id,
            'message': 'Form submitted successfully',
            'submission_id': submission.id
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in submit_form: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error in submit_form: {str(e)}")
        return jsonify({'error': 'Failed to submit form'}), 500

@forms_bp.route('/<int:form_id>/submissions', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_form_submissions(form_id):
    """Get submissions for a form with filtering and pagination."""
    try:
        user = get_current_user()
        form = Form.query.get_or_404(form_id)
        
        # Check permissions
        if form.creator_id != user.id and not user.has_permission(Permission.VIEW_USERS):
            return jsonify({'error': 'Permission denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = FormSubmission.query.filter_by(form_id=form_id)
        
        # Apply status filter
        if status:
            query = query.filter_by(status=status)
        
        # Apply date filters
        if date_from:
            try:
                from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                query = query.filter(FormSubmission.submitted_at >= from_date)
            except ValueError:
                return jsonify({'error': 'Invalid date_from format'}), 400
        
        if date_to:
            try:
                to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                query = query.filter(FormSubmission.submitted_at <= to_date)
            except ValueError:
                return jsonify({'error': 'Invalid date_to format'}), 400
        
        # Apply pagination
        submissions = query.order_by(desc(FormSubmission.submitted_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'submissions': [{
                'id': sub.id,
                'data': sub.data,
                'submitter_id': sub.submitter_id,
                'submitter_email': sub.submitter_email,
                'submitted_at': sub.submitted_at.isoformat(),
                'status': sub.status
            } for sub in submissions.items],
            'pagination': {
                'page': submissions.page,
                'pages': submissions.pages,
                'per_page': submissions.per_page,
                'total': submissions.total,
                'has_next': submissions.has_next,
                'has_prev': submissions.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_form_submissions: {str(e)}")
        return jsonify({'error': 'Failed to retrieve submissions'}), 500

@forms_bp.route('/submissions/<int:submission_id>/status', methods=['PUT'])
@jwt_required()
@limiter.limit("50 per hour")
def update_submission_status(submission_id):
    """Update submission status."""
    try:
        user = get_current_user()
        submission = FormSubmission.query.get_or_404(submission_id)
        form = submission.form
        
        # Check permissions
        if form.creator_id != user.id and not user.has_permission(Permission.UPDATE_TEMPLATE):
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        valid_statuses = ['submitted', 'reviewed', 'approved', 'rejected']
        if data['status'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        submission.status = data['status']
        db.session.commit()
        
        current_app.logger.info(f"Submission {submission_id} status updated to {data['status']} by user {user.id}")
        
        return jsonify({'message': 'Submission status updated successfully'}), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in update_submission_status: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error in update_submission_status: {str(e)}")
        return jsonify({'error': 'Failed to update submission status'}), 500

# Error handlers for this blueprint
@forms_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Form not found'}), 404

@forms_bp.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@forms_bp.errorhandler(500)
def internal_error(error):
    current_app.logger.error(f"Forms API Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# QR Code Generation Utilities
def generate_qr_code(url, size=200, error_correction='M', border=4, bg_color='#FFFFFF', fg_color='#000000'):
    """Generate QR code for a given URL"""
    try:
        # Map error correction levels
        error_levels = {
            'L': qrcode.constants.ERROR_CORRECT_L,
            'M': qrcode.constants.ERROR_CORRECT_M,
            'Q': qrcode.constants.ERROR_CORRECT_Q,
            'H': qrcode.constants.ERROR_CORRECT_H,
        }
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
            box_size=max(1, size // 25),  # Calculate box size based on desired total size
            border=border,
        )
        
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color=fg_color, back_color=bg_color)
        
        # Resize if needed
        if hasattr(img, 'resize'):
            img = img.resize((size, size))
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        current_app.logger.error(f"Error generating QR code: {str(e)}")
        raise

# QR Code Management Endpoints

@forms_bp.route('/<int:form_id>/qr-codes', methods=['POST'])
@jwt_required()
def create_form_qr_code(form_id):
    """Create a QR code for a form"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get form and check permissions
        form = Form.query.get_or_404(form_id)
        if form.creator_id != user.id and not user.has_permission(Permission.UPDATE_TEMPLATE):
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate required fields
        if 'external_url' not in data:
            return jsonify({'error': 'external_url is required'}), 400
        
        external_url = data['external_url'].strip()
        if not external_url:
            return jsonify({'error': 'external_url cannot be empty'}), 400
        
        # Generate QR code
        qr_settings = {
            'size': data.get('size', 200),
            'error_correction': data.get('error_correction', 'M'),
            'border': data.get('border', 4),
            'bg_color': data.get('background_color', '#FFFFFF'),
            'fg_color': data.get('foreground_color', '#000000'),
        }
        
        qr_code_data = generate_qr_code(external_url, **qr_settings)
        
        # Create QR code record
        form_qr = FormQRCode(
            form_id=form.id,
            qr_code_data=qr_code_data,
            external_url=external_url,
            title=data.get('title', f'QR Code for {form.title}'),
            description=data.get('description', ''),
            size=qr_settings['size'],
            error_correction=qr_settings['error_correction'],
            border=qr_settings['border'],
            background_color=qr_settings['bg_color'],
            foreground_color=qr_settings['fg_color']
        )
        
        db.session.add(form_qr)
        db.session.commit()
        
        current_app.logger.info(f"QR code created for form {form_id} by user {user.id}")
        
        return jsonify({
            'message': 'QR code created successfully',
            'qr_code': {
                'id': form_qr.id,
                'qr_code_data': form_qr.qr_code_data,
                'external_url': form_qr.external_url,
                'title': form_qr.title,
                'description': form_qr.description,
                'created_at': form_qr.created_at.isoformat(),
                'settings': {
                    'size': form_qr.size,
                    'error_correction': form_qr.error_correction,
                    'border': form_qr.border,
                    'background_color': form_qr.background_color,
                    'foreground_color': form_qr.foreground_color
                }
            }
        }), 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error in create_form_qr_code: {str(e)}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Error in create_form_qr_code: {str(e)}")
        return jsonify({'error': 'Failed to create QR code'}), 500

@forms_bp.route('/<int:form_id>/qr-codes', methods=['GET'])
@jwt_required()
def get_form_qr_codes(form_id):
    """Get all QR codes for a form"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        # Get form and check permissions
        form = Form.query.get_or_404(form_id)
        if not form.is_public and form.creator_id != user.id and not user.has_permission(Permission.VIEW_USERS):
            return jsonify({'error': 'Permission denied'}), 403
        
        qr_codes = FormQRCode.query.filter_by(form_id=form_id, is_active=True).all()
        
        qr_codes_data = []
        for qr in qr_codes:
            qr_codes_data.append({
                'id': qr.id,
                'qr_code_data': qr.qr_code_data,
                'external_url': qr.external_url,
                'title': qr.title,
                'description': qr.description,
                'created_at': qr.created_at.isoformat(),
                'updated_at': qr.updated_at.isoformat(),
                'scan_count': qr.scan_count,
                'last_scanned': qr.last_scanned.isoformat() if qr.last_scanned else None,
                'settings': {
                    'size': qr.size,
                    'error_correction': qr.error_correction,
                    'border': qr.border,
                    'background_color': qr.background_color,
                    'foreground_color': qr.foreground_color
                }
            })
        
        return jsonify({
            'qr_codes': qr_codes_data,
            'count': len(qr_codes_data)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_form_qr_codes: {str(e)}")
        return jsonify({'error': 'Failed to retrieve QR codes'}), 500

@forms_bp.route('/qr/<int:qr_id>/scan', methods=['POST'])
def track_qr_scan(qr_id):
    """Track QR code scan (public endpoint)"""
    try:
        qr_code = FormQRCode.query.filter_by(id=qr_id, is_active=True).first_or_404()
        
        # Update scan statistics
        qr_code.scan_count += 1
        qr_code.last_scanned = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Scan tracked successfully',
            'redirect_url': qr_code.external_url
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in track_qr_scan: {str(e)}")
        return jsonify({'error': 'Failed to track scan'}), 500


# =============================================================================
# FORM AUTOMATION ENDPOINTS - Complete Form-to-Excel-to-Report Workflow
# =============================================================================

@forms_bp.route('/automation/create-from-template', methods=['POST'])
@jwt_required()
def create_form_from_template():
    """
    Create a dynamic form from a template file
    POST /api/forms/automation/create-from-template
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if template file is uploaded
        if 'template_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Template file is required'
            }), 400
        
        template_file = request.files['template_file']
        form_title = request.form.get('form_title', '')
        
        if not template_file.filename:
            return jsonify({
                'success': False,
                'error': 'No template file selected'
            }), 400
        
        # Save template temporarily
        import tempfile
        temp_dir = tempfile.mkdtemp()
        template_path = os.path.join(temp_dir, template_file.filename)
        template_file.save(template_path)
        
        # Create form using automation service
        automation_service = FormAutomationService()
        result = automation_service.create_form_from_template(template_path, form_title)
        
        # Clean up temporary file
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating form from template: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@forms_bp.route('/automation/export-to-excel/<int:form_id>', methods=['POST'])
@jwt_required()
def export_form_to_excel(form_id):
    """
    Export form submissions to formatted Excel file
    POST /api/forms/automation/export-to-excel/{form_id}
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if form exists and user has permission
        form = Form.query.get_or_404(form_id)
        
        # Get options from request
        data = request.get_json() or {}
        include_analytics = data.get('include_analytics', True)
        custom_filename = data.get('filename')
        
        # Export using automation service
        automation_service = FormAutomationService()
        result = automation_service.export_form_data_to_excel(
            form_id, 
            output_path=custom_filename,
            include_analytics=include_analytics
        )
        
        if result['success']:
            # Return download URL
            download_url = f"/api/forms/automation/download/{os.path.basename(result['file_path'])}"
            result['download_url'] = download_url
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Error exporting form to Excel: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@forms_bp.route('/automation/generate-report', methods=['POST'])
@jwt_required()
def generate_automated_report():
    """
    Generate report from Excel data using template
    POST /api/forms/automation/generate-report
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check for required files
        if 'excel_file' not in request.files or 'template_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Both Excel data file and template file are required'
            }), 400
        
        excel_file = request.files['excel_file']
        template_file = request.files['template_file']
        
        # Save files temporarily
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        excel_path = os.path.join(temp_dir, excel_file.filename)
        template_path = os.path.join(temp_dir, template_file.filename)
        
        excel_file.save(excel_path)
        template_file.save(template_path)
        
        # Generate report using automation service
        automation_service = FormAutomationService()
        result = automation_service.generate_report_from_excel(excel_path, template_path)
        
        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        if result['success']:
            # Return download URL
            download_url = f"/api/forms/automation/download/{os.path.basename(result['report_path'])}"
            result['download_url'] = download_url
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Error generating automated report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@forms_bp.route('/automation/create-workflow', methods=['POST'])
@jwt_required()
def create_automated_workflow():
    """
    Create complete automated workflow: Template → Form → Excel → Report
    POST /api/forms/automation/create-workflow
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check for template file
        if 'template_file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Template file is required to create workflow'
            }), 400
        
        template_file = request.files['template_file']
        workflow_name = request.form.get('workflow_name', f"Workflow - {template_file.filename}")
        
        # Save template temporarily
        import tempfile
        temp_dir = tempfile.mkdtemp()
        template_path = os.path.join(temp_dir, template_file.filename)
        template_file.save(template_path)
        
        # Create workflow using automation service
        automation_service = FormAutomationService()
        result = automation_service.create_automated_workflow(template_path, workflow_name)
        
        # If successful, create the actual form in database
        if result['success']:
            form_schema = result['form_schema']
            
            # Create form record
            new_form = Form(
                title=result['workflow_name'],
                description=f"Automated form created from template: {template_file.filename}",
                schema=form_schema,
                is_active=True,
                is_public=True,  # Make public for easy access
                creator_id=user.id
            )
            
            db.session.add(new_form)
            db.session.commit()
            
            # Add form ID to result
            result['form_id'] = new_form.id
            result['form_url'] = f"/forms/{new_form.id}"
            result['qr_code_available'] = True
        
        # Clean up temporary file
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating automated workflow: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@forms_bp.route('/automation/workflow-status/<int:form_id>', methods=['GET'])
@jwt_required()
def get_workflow_status(form_id):
    """
    Get the status of an automated workflow
    GET /api/forms/automation/workflow-status/{form_id}
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get form and its submissions
        form = Form.query.get_or_404(form_id)
        submissions = FormSubmission.query.filter_by(form_id=form_id).all()
        
        # Calculate workflow status
        workflow_status = {
            'form_id': form_id,
            'form_title': form.title,
            'created_at': form.created_at.isoformat(),
            'is_active': form.is_active,
            'total_submissions': len(submissions),
            'steps': [
                {
                    'step': 1,
                    'name': 'Form Creation',
                    'status': 'completed',
                    'completion_date': form.created_at.isoformat()
                },
                {
                    'step': 2,
                    'name': 'Data Collection',
                    'status': 'completed' if submissions else 'in_progress',
                    'submissions_count': len(submissions),
                    'last_submission': submissions[-1].submitted_at.isoformat() if submissions else None
                },
                {
                    'step': 3,
                    'name': 'Excel Export',
                    'status': 'ready' if submissions else 'waiting',
                    'action_url': f"/api/forms/automation/export-to-excel/{form_id}" if submissions else None
                },
                {
                    'step': 4,
                    'name': 'Report Generation',
                    'status': 'ready' if submissions else 'waiting',
                    'action_url': "/api/forms/automation/generate-report" if submissions else None
                }
            ],
            'next_actions': []
        }
        
        # Determine next actions
        if not submissions:
            workflow_status['next_actions'].append({
                'action': 'Share form to collect data',
                'url': f"/forms/{form_id}",
                'description': 'Share this form URL to start collecting submissions'
            })
        else:
            workflow_status['next_actions'].extend([
                {
                    'action': 'Export to Excel',
                    'url': f"/api/forms/automation/export-to-excel/{form_id}",
                    'description': 'Export collected data to formatted Excel file'
                },
                {
                    'action': 'Generate Report',
                    'url': "/api/forms/automation/generate-report",
                    'description': 'Generate final report using template and collected data'
                }
            ])
        
        return jsonify(workflow_status), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting workflow status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@forms_bp.route('/automation/download/<filename>', methods=['GET'])
def download_generated_file(filename):
    """
    Download generated files (Excel exports, reports, etc.)
    GET /api/forms/automation/download/{filename}
    """
    try:
        # Check in exports directory
        exports_dir = os.path.join(os.path.dirname(__file__), '../../static/exports')
        exports_path = os.path.join(exports_dir, filename)
        
        if os.path.exists(exports_path):
            from flask import send_file
            return send_file(exports_path, as_attachment=True)
        
        # Check in generated directory
        generated_dir = os.path.join(os.path.dirname(__file__), '../../static/generated')
        generated_path = os.path.join(generated_dir, filename)
        
        if os.path.exists(generated_path):
            from flask import send_file
            return send_file(generated_path, as_attachment=True)
        
        return jsonify({'error': 'File not found'}), 404
        
    except Exception as e:
        current_app.logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500
