from flask import Blueprint, request, jsonify, current_app
from .models import db, Form, FormSubmission
from sqlalchemy import desc
import json

public_bp = Blueprint('public', __name__)

@public_bp.route('/forms', methods=['GET'])
def get_public_forms():
    """Get all forms for public access with optional authentication."""
    try:
        # Check for bypass token in development mode
        auth_header = request.headers.get('Authorization')
        if auth_header and current_app.debug:
            token = auth_header.replace('Bearer ', '')
            if token == 'dev-bypass-token':
                current_app.logger.info("Public forms accessed with development bypass token")
            # Continue regardless of token validity in debug mode
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        # Get all active AND public forms
        from sqlalchemy import or_
        query = Form.query.filter(
            Form.is_active == True,
            Form.is_public == True
        )
        
        # Apply pagination
        forms_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        forms_data = []
        for form in forms_paginated.items:
            # Count total fields
            field_count = 0
            if hasattr(form, 'schema') and form.schema:
                if isinstance(form.schema, list):
                    field_count = len(form.schema)
                elif isinstance(form.schema, str):
                    try:
                        import json
                        schema_json = json.loads(form.schema)
                        field_count = len(schema_json) if isinstance(schema_json, list) else 0
                    except:
                        field_count = 0
            
            forms_data.append({
                'id': form.id,  # Keep as integer for easier handling
                'title': form.title,
                'description': form.description or 'No description provided',
                'is_active': form.is_active,
                'is_public': getattr(form, 'is_public', False),
                'has_external_url': bool(getattr(form, 'external_url', None)),
                'external_url': getattr(form, 'external_url', None),
                'created_at': form.created_at.isoformat() if form.created_at else None,
                'updated_at': form.updated_at.isoformat() if form.updated_at else None,
                'field_count': field_count,
                'fields': form.schema if hasattr(form, 'schema') else []
            })
        
        return jsonify({
            'forms': forms_data,
            'pagination': {
                'page': page,
                'pages': forms_paginated.pages,
                'per_page': per_page,
                'total': forms_paginated.total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@public_bp.route('/forms/field-types', methods=['GET'])
def get_field_types():
    """Get available field types for form building."""
    field_types = [
        {
            'type': 'text',
            'label': 'Text Input',
            'description': 'Single line text input',
            'properties': ['placeholder', 'maxLength', 'required']
        },
        {
            'type': 'textarea',
            'label': 'Text Area',
            'description': 'Multi-line text input',
            'properties': ['placeholder', 'rows', 'maxLength', 'required']
        },
        {
            'type': 'email',
            'label': 'Email',
            'description': 'Email input with validation',
            'properties': ['placeholder', 'required']
        },
        {
            'type': 'number',
            'label': 'Number',
            'description': 'Numeric input',
            'properties': ['min', 'max', 'step', 'required']
        },
        {
            'type': 'select',
            'label': 'Dropdown',
            'description': 'Dropdown selection',
            'properties': ['options', 'required']
        },
        {
            'type': 'radio',
            'label': 'Radio Buttons',
            'description': 'Single choice from options',
            'properties': ['options', 'required']
        },
        {
            'type': 'checkbox',
            'label': 'Checkboxes',
            'description': 'Multiple choice options',
            'properties': ['options', 'required']
        },
        {
            'type': 'date',
            'label': 'Date',
            'description': 'Date picker',
            'properties': ['min', 'max', 'required']
        }
    ]
    
    return jsonify({'field_types': field_types}), 200

@public_bp.route('/forms', methods=['POST'])
def create_public_form():
    """Create a new form (public access)."""
    try:
        data = request.get_json()
        
        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        # Create new form
        form = Form(
            title=data['title'],
            description=data.get('description', ''),
            fields=data.get('fields', []),
            is_active=True,
            creator_id=1  # Default user for public access
        )
        
        db.session.add(form)
        db.session.commit()
        
        return jsonify({
            'id': str(form.id),
            'title': form.title,
            'description': form.description,
            'fields': form.fields,
            'is_active': form.is_active,
            'created_at': form.created_at.isoformat() if form.created_at else None
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@public_bp.route('/forms/<form_id>', methods=['DELETE'])
def delete_public_form(form_id):
    """Delete a form (public access)."""
    try:
        form = Form.query.get_or_404(form_id)
        
        # Soft delete
        form.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'Form deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
