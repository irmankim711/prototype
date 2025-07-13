from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy import desc
from ..models import db, Form, FormSubmission, Permission
from ..decorators import require_permission, get_current_user_id, get_current_user

forms_bp = Blueprint('forms', __name__)

@forms_bp.route('/', methods=['GET'])
@jwt_required()
def get_forms():
    """Get all forms for the current user with pagination."""
    user = get_current_user()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    show_all = request.args.get('show_all', 'false').lower() == 'true'
    
    if show_all and user.has_permission(Permission.VIEW_USERS):
        # Admin/Manager can see all forms
        query = Form.query
    else:
        # Regular users see only their forms
        query = Form.query.filter_by(creator_id=user.id)
    
    forms = query.filter_by(is_active=True).order_by(desc(Form.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'forms': [{
            'id': form.id,
            'title': form.title,
            'description': form.description,
            'is_public': form.is_public,
            'creator_id': form.creator_id,
            'created_at': form.created_at.isoformat(),
            'updated_at': form.updated_at.isoformat(),
            'submission_count': len(form.submissions)
        } for form in forms.items],
        'pagination': {
            'page': forms.page,
            'pages': forms.pages,
            'per_page': forms.per_page,
            'total': forms.total
        }
    }), 200

@forms_bp.route('/<int:form_id>', methods=['GET'])
@jwt_required()
def get_form(form_id):
    """Get a specific form."""
    user = get_current_user()
    form = Form.query.get_or_404(form_id)
    
    # Check permissions
    if not form.is_public and form.creator_id != user.id and not user.has_permission(Permission.VIEW_USERS):
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': form.id,
        'title': form.title,
        'description': form.description,
        'fields': form.fields,
        'is_public': form.is_public,
        'creator_id': form.creator_id,
        'created_at': form.created_at.isoformat(),
        'updated_at': form.updated_at.isoformat(),
        'submission_count': len(form.submissions)
    }), 200
    if form.creator_id != user.id and not form.is_public and not user.has_permission(Permission.VIEW_USERS):
        return jsonify({'error': 'Form not found'}), 404
    
    return jsonify({
        'id': form.id,
        'title': form.title,
        'description': form.description,
        'schema': form.schema,
        'is_public': form.is_public,
        'creator_id': form.creator_id,
        'created_at': form.created_at.isoformat(),
        'updated_at': form.updated_at.isoformat(),
        'submission_count': len(form.submissions)
    }), 200

@forms_bp.route('/', methods=['POST'])
@jwt_required()
@require_permission(Permission.CREATE_TEMPLATE)
def create_form():
    """Create a new form."""
    user = get_current_user()
    data = request.get_json()
    
    if not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    form = Form(
        title=data['title'],
        description=data.get('description', ''),
        fields=data.get('fields', []),
        is_public=data.get('is_public', False),
        creator_id=user.id
    )
    
    db.session.add(form)
    db.session.commit()
    
    return jsonify({
        'id': form.id,
        'message': 'Form created successfully'
    }), 201
    """Create a new form."""
    user = get_current_user()
    data = request.get_json()
    
    if not data.get('title'):
        return jsonify({'error': 'Form title is required'}), 400
    
    if not data.get('schema'):
        return jsonify({'error': 'Form schema is required'}), 400
    
    form = Form(
        title=data['title'],
        description=data.get('description', ''),
        schema=data['schema'],
        is_public=data.get('is_public', False),
        creator_id=user.id
    )
    
    db.session.add(form)
    db.session.commit()
    
    return jsonify({
        'id': form.id,
        'message': 'Form created successfully'
    }), 201

@forms_bp.route('/<int:form_id>', methods=['PUT'])
@jwt_required()
def update_form(form_id):
    """Update a form."""
    user = get_current_user()
    form = Form.query.get_or_404(form_id)
    
    # Check permissions - only creator or admin can update
    if form.creator_id != user.id and not user.has_permission(Permission.UPDATE_TEMPLATE):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    
    if 'title' in data:
        form.title = data['title']
    if 'description' in data:
        form.description = data['description']
    if 'fields' in data:
        form.fields = data['fields']
    if 'is_public' in data:
        form.is_public = data['is_public']
    
    form.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Form updated successfully'}), 200

@forms_bp.route('/<int:form_id>', methods=['DELETE'])
@jwt_required()
def delete_form(form_id):
    """Delete a form (soft delete)."""
    user = get_current_user()
    form = Form.query.get_or_404(form_id)
    
    # Check ownership or admin permission
    if form.creator_id != user.id and not user.has_permission(Permission.MANAGE_USERS):
        return jsonify({'error': 'Permission denied'}), 403
    
    form.is_active = False
    form.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Form deleted successfully'}), 200

# Form Submissions
    db.session.commit()
    
    return jsonify({'message': 'Form deleted successfully'}), 200

# Form Submissions
@forms_bp.route('/<int:form_id>/submissions', methods=['POST'])
def submit_form(form_id):
    """Submit a form (public endpoint)."""
    form = Form.query.filter_by(id=form_id, is_active=True).first_or_404()
    data = request.get_json()
    
    if not data.get('data'):
        return jsonify({'error': 'Form data is required'}), 400
    
    # Get current user if authenticated
    user_id = get_current_user_id()
    submitter_email = data.get('email')
    
    # For public forms, allow anonymous submissions
    if not form.is_public and not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    submission = FormSubmission(
        form_id=form.id,
        data=data['data'],
        submitter_id=user_id,
        submitter_email=submitter_email
    )
    
    db.session.add(submission)
    db.session.commit()
    
    return jsonify({
        'id': submission.id,
        'message': 'Form submitted successfully'
    }), 201

@forms_bp.route('/<int:form_id>/submissions', methods=['GET'])
@jwt_required()
def get_form_submissions(form_id):
    """Get submissions for a form."""
    user = get_current_user()
    form = Form.query.get_or_404(form_id)
    
    # Check permissions
    if form.creator_id != user.id and not user.has_permission(Permission.VIEW_USERS):
        return jsonify({'error': 'Permission denied'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    submissions = FormSubmission.query.filter_by(form_id=form_id)\
        .order_by(desc(FormSubmission.submitted_at))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
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
            'total': submissions.total
        }
    }), 200

@forms_bp.route('/submissions/<int:submission_id>/status', methods=['PUT'])
@jwt_required()
@require_permission(Permission.UPDATE_TEMPLATE)
def update_submission_status(submission_id):
    """Update submission status."""
    submission = FormSubmission.query.get_or_404(submission_id)
    data = request.get_json()
    
    new_status = data.get('status')
    if new_status not in ['submitted', 'reviewed', 'approved', 'rejected']:
        return jsonify({'error': 'Invalid status'}), 400
    
    submission.status = new_status
    db.session.commit()
    
    return jsonify({'message': 'Submission status updated'}), 200
