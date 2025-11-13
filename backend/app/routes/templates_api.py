"""
Template Management API Routes
RESTful endpoints for template CRUD operations
"""
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app, send_file

from ..services.template_service import template_service
from ..decorators import get_current_user_id
from ..decorators import firebase_auth_required

logger = logging.getLogger(__name__)

templates_api = Blueprint('templates_api', __name__)

# Allowed file extensions for template uploads
ALLOWED_EXTENSIONS = {'docx', 'doc', 'txt', 'html', 'tex', 'jinja', 'jinja2'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_template_upload_path():
    """Get the path for template file uploads"""
    upload_path = Path(current_app.root_path).parent / 'templates' / 'uploads'
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path

@templates_api.route('/api/v1/templates/debug', methods=['GET'])
def debug_templates():
    """Debug endpoint to check template database"""
    try:
        from ..models.template_models import Template
        from .. import db

        # Get database info
        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')

        # Query templates directly
        all_templates = Template.query.all()
        active_templates = Template.query.filter_by(is_active=True).all()

        return jsonify({
            'database_url': db_url,
            'total_templates': len(all_templates),
            'active_templates': len(active_templates),
            'templates': [{'id': t.id, 'name': t.name, 'active': t.is_active} for t in all_templates]
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@templates_api.route('/api/v1/templates', methods=['GET'])
def get_templates():
    """
    Get all active templates with optional filtering (Public endpoint)

    Query Parameters:
    - category: Filter by template category
    - template_type: Filter by template type (report, document, form)
    - search: Search in name and description
    - supports_excel: Filter by Excel support (true/false)
    """
    try:
        # Allow public access to templates list (read-only)
        user_id = None
        try:
            user_id = get_current_user_id()
        except (AttributeError, RuntimeError):
            pass  # No authentication required for reading templates

        # Parse query parameters
        filters = {}
        if request.args.get('category'):
            filters['category'] = request.args.get('category')

        if request.args.get('template_type'):
            filters['template_type'] = request.args.get('template_type')

        if request.args.get('search'):
            filters['search'] = request.args.get('search')

        if request.args.get('supports_excel'):
            filters['supports_excel'] = request.args.get('supports_excel').lower() == 'true'

        # Get all templates - create new service instance to ensure proper app context
        from ..services.template_service import TemplateService
        service = TemplateService()
        templates = service.get_templates(user_id=user_id, filters=filters)

        logger.info(f"API returning {len(templates)} templates")

        return jsonify({
            'success': True,
            'templates': templates,
            'total_count': len(templates),
            'filters_applied': filters
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch templates',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/<template_id>', methods=['GET'])
@firebase_auth_required
def get_template(template_id):
    """Get a specific template by ID (accepts both int and string IDs)"""
    try:
        template = template_service.get_template(template_id)
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
        
        return jsonify({
            'success': True,
            'template': template
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch template',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates', methods=['POST'])
@firebase_auth_required
def create_template():
    """
    Create a new template (admin only)
    
    Request Body:
    {
        "name": "Template Name",
        "description": "Template description",
        "category": "business",
        "template_content": "Template content with {{variables}}",
        "variables": [{"name": "var1", "type": "string", "required": true}],
        "template_type": "report",
        "supports_excel": true,
        "required_fields": ["field1", "field2"]
    }
    """
    try:
        user_id = get_current_user_id()
        
        # Check if user has permission to create templates
        # This should be implemented based on your user role system
        # For now, allowing all authenticated users
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate template data
        validation_result = template_service.validate_template(data)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': 'Template validation failed',
                'validation_errors': validation_result['errors'],
                'warnings': validation_result['warnings']
            }), 400
        
        # Create template
        template = template_service.create_template(data, user_id)
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Failed to create template'
            }), 500
        
        return jsonify({
            'success': True,
            'template': template,
            'validation': validation_result
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create template',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/<template_id>', methods=['PUT'])
@firebase_auth_required
def update_template(template_id):
    """
    Update an existing template (accepts both int and string IDs)

    Request Body: Same as create_template, but all fields are optional
    """
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Validate template data if template_content is being updated
        if 'template_content' in data:
            validation_result = template_service.validate_template(data)
            if not validation_result['valid']:
                return jsonify({
                    'success': False,
                    'error': 'Template validation failed',
                    'validation_errors': validation_result['errors'],
                    'warnings': validation_result['warnings']
                }), 400
        
        # Update template
        template = template_service.update_template(template_id, data, user_id)
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found or update failed'
            }), 404
        
        return jsonify({
            'success': True,
            'template': template
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating template {template_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update template',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/<template_id>', methods=['DELETE'])
@firebase_auth_required
def delete_template(template_id):
    """Delete a template (admin only, accepts both int and string IDs)"""
    try:
        user_id = get_current_user_id()
        
        # Check if user has permission to delete templates
        # This should be implemented based on your user role system
        
        success = template_service.delete_template(template_id, user_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Template not found or cannot be deleted'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Template deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting template {template_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete template',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/<template_id>/validate', methods=['POST'])
@firebase_auth_required
def validate_template_data(template_id):
    """
    Validate template structure and content (accepts both int and string IDs)

    Request Body:
    {
        "template_content": "Template content to validate",
        "variables": [{"name": "var1", "type": "string"}]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Get existing template if validating updates
        if template_id:
            existing_template = template_service.get_template(template_id)
            if existing_template:
                # Merge existing data with updates
                template_data = existing_template.copy()
                template_data.update(data)
            else:
                template_data = data
        else:
            template_data = data
        
        validation_result = template_service.validate_template(template_data)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating template: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to validate template',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/<template_id>/variables', methods=['GET'])
@firebase_auth_required
def get_template_variables(template_id):
    """Get template variables with metadata (accepts both int and string IDs)"""
    try:
        variables = template_service.get_template_variables(template_id)
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'variables': variables,
            'variables_count': len(variables)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching template variables: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch template variables',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/<template_id>/preview', methods=['POST'])
@firebase_auth_required
def preview_template(template_id):
    """
    Generate template preview with sample or provided data (accepts both int and string IDs)

    Request Body (optional):
    {
        "sample_data": {
            "variable1": "value1",
            "variable2": "value2"
        }
    }
    """
    try:
        data = request.get_json() or {}
        sample_data = data.get('sample_data')
        
        preview_result = template_service.generate_template_preview(template_id, sample_data)
        
        if 'error' in preview_result:
            return jsonify({
                'success': False,
                'error': preview_result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'preview': preview_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating template preview: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate preview',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/categories', methods=['GET'])
@firebase_auth_required
def get_template_categories():
    """Get all available template categories"""
    try:
        # This could be made dynamic by querying the database
        categories = [
            {'id': 'business', 'name': 'Business Reports', 'description': 'Professional business report templates'},
            {'id': 'academic', 'name': 'Academic Reports', 'description': 'Academic and research report templates'},
            {'id': 'financial', 'name': 'Financial Reports', 'description': 'Financial analysis and reporting templates'},
            {'id': 'marketing', 'name': 'Marketing Reports', 'description': 'Marketing campaign and analysis templates'},
            {'id': 'technical', 'name': 'Technical Reports', 'description': 'Technical documentation and analysis templates'},
            {'id': 'general', 'name': 'General Templates', 'description': 'General purpose report templates'}
        ]
        
        return jsonify({
            'success': True,
            'categories': categories
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching template categories: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch categories',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/types', methods=['GET'])
@firebase_auth_required
def get_template_types():
    """Get all available template types"""
    try:
        types = [
            {'id': 'report', 'name': 'Report', 'description': 'Standard report templates'},
            {'id': 'document', 'name': 'Document', 'description': 'Document templates'},
            {'id': 'form', 'name': 'Form', 'description': 'Form templates'},
            {'id': 'presentation', 'name': 'Presentation', 'description': 'Presentation templates'},
            {'id': 'letter', 'name': 'Letter', 'description': 'Letter and correspondence templates'}
        ]
        
        return jsonify({
            'success': True,
            'types': types
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching template types: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch types',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/upload', methods=['POST'])
@firebase_auth_required
def upload_template_file():
    """
    Upload a template file (DOCX, DOC, TXT, etc.)
    
    Form Data:
    - file: The template file to upload
    - name: Template name (optional, defaults to filename)
    - description: Template description (optional)
    - category: Template category (optional)
    - template_type: Template type (optional, defaults to 'docx' for DOCX files)
    """
    try:
        user_id = get_current_user_id()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Get template metadata from form data
        template_name = request.form.get('name') or secure_filename(file.filename).rsplit('.', 1)[0]
        description = request.form.get('description', '')
        category = request.form.get('category', 'general')
        template_type = request.form.get('template_type', '')
        
        # Determine template type from file extension if not provided
        if not template_type:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext == 'docx' or ext == 'doc':
                template_type = 'docx'
            elif ext == 'tex':
                template_type = 'latex'
            elif ext in ['jinja', 'jinja2']:
                template_type = 'jinja2'
            else:
                template_type = 'text'
        
        # Save uploaded file
        upload_path = get_template_upload_path()
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = upload_path / unique_filename
        file.save(str(file_path))
        
        # Read file content if it's a text-based template
        template_content = ''
        if file_ext in ['txt', 'html', 'tex', 'jinja', 'jinja2']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read template content: {e}")
        
        # Create template record
        template_data = {
            'name': template_name,
            'description': description,
            'category': category,
            'template_type': template_type,
            'template_content': template_content,
            'file_path': str(file_path),
            'is_active': True
        }
        
        # Create template using service
        template = template_service.create_template(template_data, user_id)
        
        if not template:
            # Clean up uploaded file if template creation failed
            if file_path.exists():
                file_path.unlink()
            return jsonify({
                'success': False,
                'error': 'Failed to create template'
            }), 500
        
        return jsonify({
            'success': True,
            'template': template,
            'message': 'Template uploaded successfully'
        }), 201
        
    except Exception as e:
        logger.exception("Error uploading template file")
        return jsonify({
            'success': False,
            'error': 'Failed to upload template file',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/<template_id>/download', methods=['GET'])
@firebase_auth_required
def download_template_file(template_id):
    """
    Download a template file (accepts both int and string IDs)

    Returns the template file if it exists
    """
    try:
        user_id = get_current_user_id()
        
        # Get template
        template = template_service.get_template(template_id)
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
        
        # Check if template has a file path
        file_path = template.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Template file not found'
            }), 404
        
        # Determine MIME type based on file extension
        file_ext = Path(file_path).suffix.lower()
        mimetype_map = {
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.tex': 'application/x-tex',
            '.jinja': 'text/plain',
            '.jinja2': 'text/plain'
        }
        mimetype = mimetype_map.get(file_ext, 'application/octet-stream')
        
        # Get original filename or construct from template name
        original_filename = template.get('name', 'template')
        if file_ext:
            original_filename = f"{original_filename}{file_ext}"
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=original_filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.exception("Error downloading template file")
        return jsonify({
            'success': False,
            'error': 'Failed to download template file',
            'message': str(e)
        }), 500

@templates_api.route('/api/v1/templates/<template_id>/file', methods=['GET'])
@firebase_auth_required
def get_template_file_info(template_id):
    """
    Get template file information (without downloading, accepts both int and string IDs)

    Returns file metadata and download URL
    """
    try:
        user_id = get_current_user_id()
        
        # Get template
        template = template_service.get_template(template_id)
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template not found'
            }), 404
        
        # Check if template has a file path
        file_path = template.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Template file not found'
            }), 404
        
        # Get file statistics
        file_stat = os.stat(file_path)
        file_ext = Path(file_path).suffix.lower()
        
        return jsonify({
            'success': True,
            'file_info': {
                'file_path': file_path,
                'file_size': file_stat.st_size,
                'file_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'file_extension': file_ext,
                'download_url': f'/api/v1/templates/{template_id}/download',
                'template_name': template.get('name'),
                'template_type': template.get('template_type')
            }
        }), 200
        
    except Exception as e:
        logger.exception("Error getting template file info")
        return jsonify({
            'success': False,
            'error': 'Failed to get template file info',
            'message': str(e)
        }), 500

# Error handlers
@templates_api.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': str(error)
    }), 400

@templates_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'message': str(error)
    }), 404

@templates_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(error)
    }), 500