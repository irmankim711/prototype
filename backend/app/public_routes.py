from flask import Blueprint, request, jsonify
from .models import db, Form, FormSubmission
from sqlalchemy import desc
import json

public_bp = Blueprint('public', __name__)

@public_bp.route('/forms', methods=['GET'])
def get_public_forms():
    """Get all forms for public access (no authentication required)."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        # Get all active forms
        query = Form.query.filter_by(is_active=True)
        
        # Apply pagination
        forms_paginated = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        forms_data = []
        for form in forms_paginated.items:
            forms_data.append({
                'id': str(form.id),
                'title': form.title,
                'description': form.description,
                'is_active': form.is_active,
                'created_at': form.created_at.isoformat() if form.created_at else None,
                'fields': form.fields if hasattr(form, 'fields') else []
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
