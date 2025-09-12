"""
Next-Gen Report Builder API Routes
Provides comprehensive functionality for the enhanced report builder including
template management, Excel automation, and report generation
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
from datetime import datetime, timedelta
import os
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter

from app import db
from app.models import User, Form, FormSubmission
# Import the simple Report model that matches SQLite schema
from app.models import Report
from .reports_api import resolve_template_id
from app.services.form_automation import FormAutomationService
from app.services.export_service import ExportService
from app.services.excel_parser import ExcelParserService
from app.services.template_optimizer import TemplateOptimizerService
import re

logger = logging.getLogger(__name__)

nextgen_bp = Blueprint('nextgen_report_builder', __name__)

# Initialize services
form_automation = FormAutomationService()
excel_parser = ExcelParserService()
template_optimizer = TemplateOptimizerService()

# ================ CORS TEST ENDPOINT ================


@nextgen_bp.route('/cors-test', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True)
def cors_test():
    """Simple endpoint to test CORS configuration"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'message': 'CORS preflight successful'})
        return response

    return jsonify({
        'message': 'CORS test successful',
        'timestamp': datetime.utcnow().isoformat(),
        'origin': request.headers.get('Origin', 'No Origin header'),
        'method': request.method
    })

# ================ DATA SOURCES ================


@nextgen_bp.route('/data-sources', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_data_sources():
    """Get available data sources for the report builder"""
    try:
        user_id = get_jwt_identity()

        # Get user's forms as data sources
        forms = Form.query.filter_by(creator_id=user_id).all()

        data_sources = []
        for form in forms:
            submission_count = FormSubmission.query.filter_by(
                form_id=form.id).count()

            data_sources.append({
                'id': f'form_{form.id}',
                'name': form.title,
                'type': 'form',
                'description': form.description or 'Form-based data source',
                'fields': [],  # Will be populated in the fields endpoint
                'connectionStatus': 'connected',
                'lastUpdated': form.updated_at.isoformat() if form.updated_at else form.created_at.isoformat(),
                'recordCount': submission_count,
                'metadata': {
                    'formId': form.id,
                    'createdAt': form.created_at.isoformat(),
                    'submissionCount': submission_count
                }
            })

        # Get real Excel data sources from uploads
        uploads_dir = Path(current_app.root_path) / \
                           'static' / 'uploads' / 'excel'
        if uploads_dir.exists():
            for excel_file in uploads_dir.glob('*.xlsx'):
                try:
                    # Get file info
                    file_stats = excel_file.stat()
                    file_size = file_stats.st_size

                    # Parse Excel file to get real data
                    excel_data = excel_parser.parse_excel_file(str(excel_file))

                    if excel_data.get('success'):
                        data_sources.append({
                            'id': f'excel_{excel_file.stem}',
                            'name': excel_file.stem.replace('_', ' ').title(),
                            'type': 'excel',
                            'description': f'Excel file: {excel_file.name}',
                            'fields': _convert_excel_columns_to_fields(excel_data.get('columns', [])),
                            'connectionStatus': 'connected',
                            'lastUpdated': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                            'recordCount': excel_data.get('total_rows', 0),
                            'metadata': {
                                'filePath': str(excel_file),
                                'fileSize': f'{file_size / (1024 * 1024):.1f} MB',
                                'sheets': excel_data.get('sheets_info', []),
                                'uploadedAt': datetime.fromtimestamp(file_stats.st_ctime).isoformat()
                            }
                        })
                except Exception as e:
                    logger.warning(
    f"Could not process Excel file {excel_file}: {e}")
                    continue

        # Add mock data sources for development/testing
        mock_data_sources = [
            {
                'id': 'mock-excel-1',
                'name': 'Sales Data Q4 2024',
                'type': 'excel',
                'description': 'Mock Excel data source for development and testing',
                'fields': [],  # Will be populated in the fields endpoint
                'connectionStatus': 'connected',
                'lastUpdated': datetime.utcnow().isoformat(),
                'recordCount': 1000,
                'metadata': {
                    'isMock': True,
                    'description': 'Development mock data source'
                }
            }
        ]
        data_sources.extend(mock_data_sources)

        return jsonify({
            'success': True,
            'data': data_sources,
            'count': len(data_sources),
            'message': 'Data sources retrieved successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error fetching data sources: {str(e)}")
        return jsonify({'error': 'Failed to fetch data sources'}), 500


@nextgen_bp.route('/data-sources/<data_source_id>/fields', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_data_source_fields(data_source_id):
    """Get fields for a specific data source"""
    try:
        user_id = get_jwt_identity()

        fields = []

        if data_source_id.startswith('form_'):
            # Extract form ID and get form fields
            form_id = int(data_source_id.replace('form_', ''))
            form = Form.query.filter_by(id=form_id, creator_id=user_id).first()

            if form and form.schema:
                for field in form.schema.get('fields', []):
                    field_type = 'dimension' if field.get('type') in [
    'select', 'radio', 'checkbox'] else 'measure'
                    data_type = 'categorical' if field_type == 'dimension' else 'numerical'

                    if field.get('type') in ['date', 'datetime']:
                        data_type = 'temporal'
                    elif field.get('type') in ['text', 'textarea', 'email']:
                        data_type = 'text'

                    fields.append({
                        'id': field.get('id', ''),
                        'name': field.get('label', ''),
                        'type': field_type,
                        'dataType': data_type,
                        'sampleValues': _get_sample_values(form_id, field.get('id')),
                        'usageCount': 0,
                        'description': field.get('description', '')
                    })
        elif data_source_id == 'mock-excel-1':
            # Return mock fields for development/testing
            fields = [
                {
                    'id': 'sales_region',
                    'name': 'Sales Region',
                    'type': 'dimension',
                    'dataType': 'categorical',
                    'sampleValues': ['North', 'South', 'East', 'West'],
                    'usageCount': 3,
                    'description': 'Geographic sales regions'
                },
                {
                    'id': 'revenue',
                    'name': 'Revenue',
                    'type': 'measure',
                    'dataType': 'numerical',
                    'sampleValues': [50000, 75000, 100000, 120000],
                    'usageCount': 8,
                    'description': 'Total revenue in USD'
                },
                {
                    'id': 'quarter',
                    'name': 'Quarter',
                    'type': 'dimension',
                    'dataType': 'temporal',
                    'sampleValues': ['Q1', 'Q2', 'Q3', 'Q4'],
                    'usageCount': 5,
                    'description': 'Fiscal quarters'
                },
                {
                    'id': 'profit_margin',
                    'name': 'Profit Margin',
                    'type': 'measure',
                    'dataType': 'numerical',
                    'sampleValues': [0.15, 0.22, 0.18, 0.25],
                    'usageCount': 2,
                    'description': 'Profit margin percentage'
                }
            ]
        else:
            # Get real Excel data for Excel sources
            excel_id = data_source_id.replace('excel_', '')
            uploads_dir = Path(current_app.root_path) / \
                               'static' / 'uploads' / 'excel'

            excel_file = None
            # Find the Excel file
            for file in uploads_dir.glob('*.xlsx'):
                if file.stem == excel_id:
                    excel_file = file
                    break

            if excel_file and excel_file.exists():
                try:
                    # Parse Excel file to get real columns and data
                    excel_data = excel_parser.parse_excel_file(str(excel_file))

                    if excel_data.get('success'):
                        fields = _convert_excel_columns_to_fields(
                            excel_data.get('columns', []))
                    else:
                        fields = []
                        logger.error(
    f"Failed to parse Excel file {excel_file}: {
        excel_data.get('error')}")
                except Exception as e:
                    logger.error(f"Error parsing Excel file {excel_file}: {e}")
                    fields = []
            else:
                fields = []
                logger.warning(
    f"Excel file not found for data source {data_source_id}")

        return jsonify({
            'success': True,
            'data': fields,
            'count': len(fields),
            'dataSourceId': data_source_id,
            'message': f'Fields retrieved successfully for {data_source_id}'
        }), 200

    except Exception as e:
        logger.error(
    f"Error fetching fields for data source {data_source_id}: {
        str(e)}")
        return jsonify({'error': 'Failed to fetch data source fields'}), 500


def _get_sample_values(form_id: int, field_id: str) -> List[str]:
    """Get sample values for a form field"""
    try:
        submissions = FormSubmission.query.filter_by(
            form_id=form_id).limit(10).all()
        values = []
        for submission in submissions:
            if submission.data and field_id in submission.data:
                value = submission.data[field_id]
                if value and str(value) not in values:
                    values.append(str(value))
        return values[:5]  # Return max 5 sample values
    except:
        return []

# ================ TEMPLATES ================


@nextgen_bp.route('/templates', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_report_templates():
    """Get available report templates from database with filesystem fallback"""
    try:
        templates = []

        # First, get templates from database
        try:
            # Use regular template model for development (SQLite compatible)
            from app.models import ReportTemplate
            db_templates = ReportTemplate.query.filter_by(is_active=True).all()

            logger.info(
    f"🔍 [DEBUG] Found {
        len(db_templates)} templates in database")

            for db_template in db_templates:
                placeholder_schema = db_template.placeholder_schema or {}
                template_identifier = placeholder_schema.get(
                    'template_identifier', str(db_template.id))

                template_info = {
                    'id': template_identifier,  # Use identifier for frontend compatibility
                    'db_id': db_template.id,    # Keep DB ID for reference
                    'name': db_template.name,
                    'description': db_template.description or 'Database template',
                    'filepath': db_template.file_path or '',
                    'type': db_template.template_type or 'docx',
                    'category': db_template.category or 'general',
                    'lastModified': db_template.updated_at.isoformat() if db_template.updated_at else db_template.created_at.isoformat(),
                    'fileSize': placeholder_schema.get('file_size', 0),
                    'supports': ['formatting'] + (['images'] if db_template.supports_images else []) + (['charts'] if db_template.supports_charts else []),
                    'isDefault': template_identifier.lower() in ['temp1', 'testtemplate'],
                    'preview': f'/v1/nextgen/templates/{template_identifier}/preview',
                    'source': 'database'
                }

                templates.append(template_info)
                logger.info(
    f"   Added DB template: {
        db_template.name} (ID: {template_identifier})")

        except Exception as db_error:
            import traceback
            logger.warning(f"Database template lookup failed: {str(db_error)}")
            logger.warning(f"DB error traceback: {traceback.format_exc()}")

        # Define templates directory path
        templates_dir = Path(__file__).parent.parent.parent / 'templates'
        
        # Track template IDs to prevent duplicates
        existing_template_ids = {t['id'] for t in templates}
        
        # Fallback: Get templates from the templates directory if no DB
        # templates found or to supplement existing templates
        if not templates:
            logger.info(
                "No database templates found, falling back to filesystem")
        else:
            logger.info(f"Found {len(templates)} database templates, checking filesystem for additional templates")

        if templates_dir.exists():
            # Focus on .docx files first as they are the main templates
            docx_files = list(templates_dir.glob('*.docx'))

            for template_file in docx_files:
                # Create user-friendly names for templates
                template_name = template_file.stem
                
                # Skip if this template ID already exists from database
                if template_name in existing_template_ids:
                    logger.info(f"Skipping duplicate template from filesystem: {template_name}")
                    continue
                
                display_name = _get_template_display_name(template_name)
                description = _get_template_description(template_name)

                template_info = {
                    'id': template_file.stem,
                    'name': display_name,
                    'description': description,
                    'filepath': str(template_file),
                    'type': 'docx',
                    'category': 'document',
                    'lastModified': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat(),
                    'fileSize': template_file.stat().st_size,
                    'supports': ['formatting', 'images', 'tables', 'charts'],
                    'isDefault': template_name.lower() in ['temp1', 'testtemplate'],
                    'preview': f'/v1/nextgen/templates/{template_file.stem}/preview',
                    'source': 'filesystem'
                }

                templates.append(template_info)
                existing_template_ids.add(template_name)

            # Also include other template types
            other_extensions = ['.jinja', '.tex', '.html']
            for ext in other_extensions:
                for template_file in templates_dir.glob(f'*{ext}'):
                    template_name = template_file.stem
                    
                    # Skip if this template ID already exists
                    if template_name in existing_template_ids:
                        logger.info(f"Skipping duplicate template from filesystem: {template_name}{ext}")
                        continue
                        
                    template_info = {
                        'id': template_file.stem,
                        'name': template_file.stem.replace('_', ' ').title(),
                        'description': f'{ext[1:].upper()} template: {template_file.name}',
                        'filepath': str(template_file),
                        'type': ext[1:],
                        'category': 'text' if ext == '.jinja' else 'scientific' if ext == '.tex' else 'web',
                        'lastModified': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat(),
                        'fileSize': template_file.stat().st_size,
                        'supports': ['variables', 'loops', 'conditions'] if ext == '.jinja' else ['formatting'],
                        'isDefault': False,
                        'preview': f'/v1/nextgen/templates/{template_file.stem}/preview',
                        'source': 'filesystem'
                    }
                    templates.append(template_info)
                    existing_template_ids.add(template_name)

        # If no templates found in directory, provide default ones
        if not templates:
            logger.info(
                "No templates found in directory, providing default templates")
            templates = [
                {
                    'id': '1',
                    'name': 'Basic Report',
                    'description': 'Simple report template with professional formatting',
                    'filepath': 'default',
                    'type': 'jinja2',
                    'category': 'business',
                    'lastModified': datetime.utcnow().isoformat(),
                    'fileSize': 0,
                    'supports': ['variables', 'loops', 'conditions'],
                    'isDefault': True,
                    'preview': '/v1/nextgen/templates/1/preview'
                },
                {
                    'id': '2',
                    'name': 'Detailed Report',
                    'description': 'Comprehensive report template for detailed analysis',
                    'filepath': 'default',
                    'type': 'latex',
                    'category': 'scientific',
                    'lastModified': datetime.utcnow().isoformat(),
                    'fileSize': 0,
                    'supports': ['formatting', 'mathematical', 'citations'],
                    'isDefault': True,
                    'preview': '/v1/nextgen/templates/2/preview'
                }
            ]

        # Sort templates: .docx first, then by name
        templates.sort(key=lambda t: (t['type'] != 'docx', t['name']))

        return jsonify({
            'success': True,
            'templates': templates,
            'total': len(templates),
            'docxCount': len([t for t in templates if t['type'] == 'docx']),
            'recommendedTemplates': [t['id'] for t in templates if t.get('isDefault', False)]
        }), 200

    except Exception as e:
        import traceback
        logger.error(f"Error fetching templates: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Failed to fetch templates',
            'details': str(e),
            'success': False
        }), 500


def _get_template_display_name(template_stem: str) -> str:
    """Get user-friendly display name for template"""
    name_mappings = {
        'temp1': 'Standard Business Report',
        'temp1_jinja2': 'Business Report with Excel Headers',
        'temp1_jinja2_excelheaders': 'Enhanced Business Report',
        'testtemplate': 'Test Report Template',
        'temp2': 'Academic/Scientific Report',
        'default_report': 'Default Report Template'
    }

    return name_mappings.get(
    template_stem.lower(),
    template_stem.replace(
        '_',
         ' ').title())


def _get_template_description(template_stem: str) -> str:
    """Get detailed description for template"""
    descriptions = {
        'temp1': 'Standard business report template with professional formatting, suitable for general business reporting needs.',
        'temp1_jinja2': 'Business report template with dynamic content support and Excel data integration capabilities.',
        'temp1_jinja2_excelheaders': 'Enhanced business report template optimized for Excel data with automatic header mapping.',
        'testtemplate': 'Template for testing report generation functionality with sample data structures.',
        'temp2': 'Academic or scientific report template with LaTeX-style formatting for research and technical documents.',
        'default_report': 'Basic report template with minimal formatting, good for simple data presentation.'
    }

    return descriptions.get(
    template_stem.lower(),
     f'Report template: {template_stem}')


@nextgen_bp.route('/templates/<template_id>/metadata', methods=['GET'])
@jwt_required()
def get_template_metadata(template_id):
    """Get detailed metadata for a specific template"""
    try:
        templates_dir = Path(__file__).parent.parent.parent / 'templates'

        # Find the template file
        template_file = None
        for ext in ['.docx', '.jinja', '.tex', '.html']:
            potential_file = templates_dir / f'{template_id}{ext}'
            if potential_file.exists():
                template_file = potential_file
                break

        if not template_file:
            return jsonify({'error': 'Template not found'}), 404

        metadata = {
            'id': template_id,
            'name': _get_template_display_name(template_id),
            'description': _get_template_description(template_id),
            'type': template_file.suffix[1:],
            'filepath': str(template_file),
            'fileSize': template_file.stat().st_size,
            'lastModified': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat(),
            'isRecommended': template_id.lower() in ['temp1', 'testtemplate'],
            'usageInstructions': _get_template_usage_instructions(template_id),
            'compatibleFormats': ['docx', 'pdf'] if template_file.suffix == '.docx' else ['txt', 'html']
        }

        # Add format-specific metadata
        if template_file.suffix == '.docx':
            try:
                # Try to get some basic document info
                import zipfile
                with zipfile.ZipFile(template_file, 'r') as docx_zip:
                    metadata['documentInfo'] = {
                        'hasStyles': 'word/styles.xml' in docx_zip.namelist(),
                        'hasImages': any('media/' in name for name in docx_zip.namelist()),
                        'hasHeaders': 'word/header' in str(docx_zip.namelist()),
                        'hasFooters': 'word/footer' in str(docx_zip.namelist())
                    }
            except:
                metadata['documentInfo'] = {
    'error': 'Could not read document structure'}

        return jsonify({
            'success': True,
            'metadata': metadata
        }), 200

    except Exception as e:
        logger.error(
    f"Error fetching template metadata for {template_id}: {
        str(e)}")
        return jsonify({'error': 'Failed to fetch template metadata'}), 500


def _get_template_usage_instructions(template_id: str) -> str:
    """Get usage instructions for template"""
    instructions = {
        'temp1': 'Upload Excel data with columns for regions, quarters, revenue, and metrics. The template will automatically generate charts and summaries.',
        'temp1_jinja2': 'This template supports dynamic variables. Ensure your Excel data has consistent column headers for best results.',
        'temp1_jinja2_excelheaders': 'Optimized for Excel files. Column headers will be automatically mapped to template variables.',
        'testtemplate': 'Use this template for testing report generation. Compatible with sample data formats.',
        'temp2': 'Scientific/academic template. Best for research data with statistical analysis requirements.',
        'default_report': 'Basic template suitable for any data type. Minimal formatting with focus on content.'
    }

    return instructions.get(
    template_id.lower(),
     'Upload your Excel data and the template will generate a formatted report automatically.')


@nextgen_bp.route('/templates/<template_id>', methods=['GET'])
@jwt_required()
def get_template_content(template_id):
    """Get template content by ID"""
    try:
        templates_dir = Path(__file__).parent.parent.parent / 'templates'

        # Try to find the template file
        template_file = None
        for ext in ['.jinja', '.docx', '.tex', '.html']:
            potential_file = templates_dir / f'{template_id}{ext}'
            if potential_file.exists():
                template_file = potential_file
                break

        if not template_file:
            return jsonify({'error': 'Template not found'}), 404

        # Read template content based on type
        content = None
        metadata = {}

        if template_file.suffix in ['.jinja', '.tex', '.html']:
            # Text-based templates
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Analyze template for placeholders
            from app.services.template_converter import TemplateConverter
            syntax_type = TemplateConverter.analyze_template_syntax(content)
            placeholders = _extract_template_placeholders(content)

            metadata = {
                'syntax_type': syntax_type,
                'placeholders': placeholders,
                'line_count': len(content.split('\n')),
                'word_count': len(content.split())
            }
        elif template_file.suffix == '.docx':
            # Document templates - return metadata only
            metadata = {
                'file_type': 'document',
                'file_size': template_file.stat().st_size,
                'supports_automation': True,
                'note': 'Binary file - use for automated report generation'
            }

        return jsonify({
            'success': True,
            'template': {
                'id': template_id,
                'name': template_file.stem.replace('_', ' ').title(),
                'type': template_file.suffix[1:],
                'content': content,
                'metadata': metadata,
                'lastModified': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat()
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching template {template_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch template content'}), 500


def _extract_template_placeholders(content: str) -> List[str]:
    """Extract placeholders from template content"""
    import re

    placeholders = []

    # Jinja2 variables
    jinja_pattern = r'\{\{\s*([^}]+)\s*\}\}'
    for match in re.finditer(jinja_pattern, content):
        placeholder = match.group(1).strip()
        if placeholder not in placeholders:
            placeholders.append(placeholder)

    # Mustache variables
    mustache_pattern = r'\{\{\{?\s*([^}]+)\s*\}?\}\}'
    for match in re.finditer(mustache_pattern, content):
        placeholder = match.group(1).strip()
        if placeholder not in placeholders:
            placeholders.append(placeholder)

    return placeholders

# ================ EXCEL AUTOMATION ================


@nextgen_bp.route('/excel/upload', methods=['POST'])
@jwt_required()
def upload_excel_file():
    """Upload and process Excel file for report automation"""
    try:
        user_id = get_jwt_identity()

        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify(
                {'error': 'File must be an Excel file (.xlsx or .xls)'}), 400

        # Validate file size (max 50MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return jsonify({'error': 'File size exceeds 50MB limit'}), 400

        # Save uploaded file
        upload_dir = Path(current_app.root_path) / \
                          'static' / 'uploads' / 'excel'
        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{user_id}_{uuid.uuid4().hex}_{file.filename}"
        file_path = upload_dir / filename
        file.save(str(file_path))

        # Process Excel file with enhanced error handling
        try:
            processing_result = excel_parser.parse_excel_file(str(file_path))
        except Exception as parse_error:
            logger.error(f"Excel parsing failed: {str(parse_error)}")
            # Clean up the uploaded file
            try:
                os.remove(str(file_path))
            except:
                pass
            return jsonify({
                'error': 'Failed to process Excel file',
                'details': str(parse_error)
            }), 500

        if not processing_result.get('success'):
            # Clean up the uploaded file
            try:
                os.remove(str(file_path))
            except:
                pass
            return jsonify({
                'error': 'Failed to process Excel file',
                'details': processing_result.get('error', 'Unknown error')
            }), 400

        # Debug logging to see what processing_result contains
        logger.info(
    f"Processing result keys: {
        list(
            processing_result.keys())}")
        logger.info(
    f"Processing result success: {
        processing_result.get('success')}")
        logger.info(
    f"Processing result tables: {
        processing_result.get(
            'tables', [])}")
        logger.info(
    f"Processing result total_rows: {
        processing_result.get(
            'total_rows', 0)}")

        # Extract columns from the parsed tables
        columns = _extract_columns_from_tables(
            processing_result.get('tables', []))
        logger.info(f"Extracted columns: {len(columns)} columns")
        for i, col in enumerate(columns):
            logger.info(
    f"Column {
        i +
        1}: {
            col.get(
                'name',
                'Unknown')} - {
                    col.get(
                        'data_type',
                         'unknown')}")

        # Create data source from Excel file with proper structure
        data_source = {
            'id': f'excel_{uuid.uuid4().hex}',
            'name': file.filename,
            'type': 'excel',
            'description': f'Uploaded Excel file: {file.filename}',
            'filePath': str(file_path),
            'connectionStatus': 'connected',
            'lastUpdated': datetime.now().isoformat(),
            'recordCount': processing_result.get('total_rows', 0),
            'sheets': processing_result.get('sheets_info', []),
            'fields': _convert_excel_columns_to_fields(columns),
            'metadata': {
                'fileSize': file_size,
                'uploadedAt': datetime.now().isoformat(),
                'processedAt': datetime.now().isoformat(),
                'processingStatus': 'completed'
            }
        }

        logger.info(
    f"Excel file uploaded successfully: {filename}, {
        data_source['recordCount']} records")

        return jsonify({
            'success': True,
            'message': 'Excel file uploaded and processed successfully',
            'dataSource': data_source,
            'processingResult': processing_result
        }), 200

    except Exception as e:
        logger.error(f"Error uploading Excel file: {str(e)}")
        # Clean up any uploaded files in case of error
        try:
            if 'file_path' in locals():
                os.remove(str(file_path))
        except:
            pass
        return jsonify(
            {'error': 'Failed to upload Excel file', 'details': str(e)}), 500


def _extract_columns_from_tables(tables: List[Dict]) -> List[Dict]:
    """Extract columns from parsed Excel tables"""
    columns = []

    logger.info(f"Extracting columns from {len(tables)} tables")

    if not tables:
        logger.warning("No tables provided for column extraction")
        return columns

    # Use the first table (usually the main data)
    table = tables[0]
    logger.info(f"Processing first table: {table.keys()}")

    table_data = table.get('data', [])
    logger.info(f"Table data length: {len(table_data)} rows")

    if not table_data or len(table_data) < 1:
        logger.warning("No table data found")
        return columns

    # First row contains headers
    headers = table_data[0]

    # Process each column
    for col_idx, header in enumerate(headers):
        if not header or str(header).strip() == '':
            continue

        # Extract sample values from the column (skip header row)
        sample_values = []
        data_types = []

        for row_idx in range(
            1, min(len(table_data), 6)):  # Get up to 5 sample values
            if row_idx < len(table_data) and col_idx < len(
                table_data[row_idx]):
                value = table_data[row_idx][col_idx]
                if value is not None and str(value).strip() != '':
                    sample_values.append(value)

                    # Determine data type
                    if isinstance(value, (int, float)):
                        data_types.append('number')
                    elif isinstance(value, str):
                        # Try to detect date
                        try:
                            datetime.strptime(value, '%Y-%m-%d')
                            data_types.append('date')
                        except ValueError:
                            data_types.append('text')
                    else:
                        data_types.append('text')

        # Determine most common data type
        if data_types:
            from collections import Counter
            most_common_type = Counter(data_types).most_common(1)[0][0]
        else:
            most_common_type = 'text'

        columns.append({
            'name': str(header).strip(),
            'data_type': most_common_type,
            'sample_values': sample_values[:5],  # Limit to 5 sample values
            'column_index': col_idx
        })

    return columns


def _convert_excel_columns_to_fields(columns: List[Dict]) -> List[Dict]:
    """Convert Excel columns to data fields format"""
    fields = []

    for col in columns:
        # Determine field type based on data type
        data_type = col.get('data_type', 'text')
        field_type = 'measure' if data_type in [
    'number', 'float', 'int'] else 'dimension'

        if data_type in ['date', 'datetime']:
            data_type_category = 'temporal'
        elif data_type in ['number', 'float', 'int']:
            data_type_category = 'numerical'
        elif data_type in ['text', 'string']:
            data_type_category = 'text'
        else:
            data_type_category = 'categorical'

        fields.append({
            'id': col.get('name', '').lower().replace(' ', '_'),
            'name': col.get('name', ''),
            'type': field_type,
            'dataType': data_type_category,
            'sampleValues': col.get('sample_values', []),
            'usageCount': 0,
            'description': f"Excel column: {col.get('name', '')}"
        })

    return fields


@nextgen_bp.route('/excel/generate-report', methods=['POST'])
@jwt_required()
def generate_report_from_excel():
    """Generate automated report from Excel data"""
    try:
        # IMMEDIATE DEBUGGING: Log request details
        logger.info(
    f"🔍 [DEBUG] generate_report_from_excel called with data: {
        request.get_data()}")
        logger.info(f"🔍 [DEBUG] Request JSON: {request.get_json()}")
        logger.info(f"🔍 [DEBUG] Request method: {request.method}")
        logger.info(f"🔍 [DEBUG] Request URL: {request.url}")
        logger.info(f"🔍 [DEBUG] Request headers: {dict(request.headers)}")
        logger.info(f"🔍 [DEBUG] Request endpoint: {request.endpoint}")
        logger.info(f"🔍 [DEBUG] Request blueprint: {request.blueprint}")

        user_id = get_jwt_identity()
        logger.info(f"🔍 [DEBUG] User ID: {user_id}")

        data = request.get_json()

        if not data:
            logger.error("🔍 [DEBUG] No data provided in request")
            return jsonify({'error': 'No data provided'}), 400

        excel_file_path = data.get('excelFilePath')
        template_id = data.get('templateId')
        report_title = data.get('reportTitle', 'Automated Excel Report')

        logger.info(f"🔍 [DEBUG] Excel file path: {excel_file_path}")
        logger.info(f"🔍 [DEBUG] Template ID: {template_id}")
        logger.info(f"🔍 [DEBUG] Report title: {report_title}")

        if not excel_file_path or not template_id:
            logger.error("🔍 [DEBUG] Missing required fields")
            return jsonify(
                {'error': 'Excel file path and template ID are required'}), 400

        # Validate Excel file exists and is accessible
        try:
            excel_path = Path(excel_file_path)
            if not excel_path.exists():
                logger.error(
    f"🔍 [DEBUG] Excel file does not exist: {excel_file_path}")
                return jsonify(
                    {'error': f'Excel file not found: {excel_file_path}'}), 400

            if not excel_path.is_file():
                logger.error(
    f"🔍 [DEBUG] Excel path is not a file: {excel_file_path}")
                return jsonify(
                    {'error': f'Excel path is not a file: {excel_file_path}'}), 400

            # Check if file is readable
            if not os.access(excel_file_path, os.R_OK):
                logger.error(
    f"🔍 [DEBUG] Excel file is not readable: {excel_file_path}")
                return jsonify(
                    {'error': f'Excel file is not readable: {excel_file_path}'}), 400

            logger.info(
    f"🔍 [DEBUG] Excel file validated: {excel_file_path} (size: {
        excel_path.stat().st_size} bytes)")

        except Exception as e:
            logger.error(f"🔍 [DEBUG] Error validating Excel file: {str(e)}")
            return jsonify(
                {'error': f'Error accessing Excel file: {str(e)}'}), 400

        # Look up template in database first, then fall back to filesystem
        template_file = None
        template_db_record = None

        logger.info(
    f"🔍 [DEBUG] Looking up template in database: {template_id}")

        try:
            # Use regular template model for development (SQLite compatible)
            from app.models import ReportTemplate

            # For development, create a simple template record if none exists
            template_db_record = None
            logger.info(f"🔍 [DEBUG] Development mode - simplifying template lookup for template_id: {template_id}")
            
            try:
                # Try simple template lookup first
                if template_id.isdigit():
                    template_db_record = ReportTemplate.query.get(int(template_id))
                
                if not template_db_record:
                    # In development, just use the first available template or create a simple fallback
                    template_db_record = ReportTemplate.query.first()
                    logger.info(f"🔍 [DEBUG] Using first available template: {template_db_record}")
                    
            except Exception as query_error:
                logger.warning(f"Template query failed: {query_error}")
                template_db_record = None

            if template_db_record:
                # Check if the model has file_path attribute (handle schema
                # mismatch)
                file_path = getattr(template_db_record, 'file_path', None)
                if file_path and Path(file_path).exists():
                    template_file = Path(file_path)
                    logger.info(
    f"🔍 [DEBUG] Found template in database: {
        template_db_record.name} -> {template_file}")
                elif file_path:
                    logger.warning(
    f"🔍 [DEBUG] Template in DB but file missing: {file_path}")
                else:
                    logger.info(
    f"🔍 [DEBUG] Template found in DB but no file_path column: {
        template_db_record.name}")

        except Exception as db_error:
            logger.warning(
    f"🔍 [DEBUG] Database template lookup failed: {
        str(db_error)}")

        # Fallback to filesystem lookup if not found in database
        if not template_file:
            logger.info(
    f"🔍 [DEBUG] Template not found in DB, falling back to filesystem lookup")
            templates_dir = Path(__file__).parent.parent.parent / 'templates'
            logger.info(f"🔍 [DEBUG] Templates directory: {templates_dir}")

            # First, try the template_id as-is (in case it already has an
            # extension)
            potential_file = templates_dir / template_id
            logger.info(
                f"🔍 [DEBUG] Checking template as-is: {potential_file} (exists: {potential_file.exists()})")
            if potential_file.exists():
                template_file = potential_file
            else:
                # If not found, try adding extensions
                for ext in ['.jinja', '.docx', '.tex', '.html']:
                    potential_file = templates_dir / f'{template_id}{ext}'
                    logger.info(
    f"🔍 [DEBUG] Checking template with extension: {potential_file} (exists: {
        potential_file.exists()})")
                    if potential_file.exists():
                        template_file = potential_file
                        break

        if not template_file:
            logger.error(f"🔍 [DEBUG] Template not found for ID: {template_id}")
            # List available templates for debugging
            available_templates = []
            if templates_dir.exists():
                for template_path in templates_dir.iterdir():
                    if template_path.is_file():
                        available_templates.append(template_path.name)
            logger.error(
    f"🔍 [DEBUG] Available templates: {available_templates}")
            return jsonify({
                'error': f'Template not found: {template_id}',
                'available_templates': available_templates
            }), 404

        logger.info(f"🔍 [DEBUG] Template file found: {template_file}")
        logger.info(
    f"🔍 [DEBUG] Template file exists: {
        template_file.exists()}")
        logger.info(
    f"🔍 [DEBUG] Template file size: {
        template_file.stat().st_size if template_file.exists() else 'N/A'}")
        logger.info(
    f"🔍 [DEBUG] About to call form_automation.generate_report_from_excel")

        # Generate report using form automation service with enhanced error
        # handling
        try:
            logger.info(
    f"🔍 [DEBUG] Calling form_automation.generate_report_from_excel with:")
            logger.info(f"🔍 [DEBUG] - excel_path: {excel_file_path}")
            logger.info(f"🔍 [DEBUG] - template_path: {str(template_file)}")
            logger.info(
                f"🔍 [DEBUG] - Template file extension: {template_file.suffix}")

            generation_result = form_automation.generate_report_from_excel(
                excel_path=excel_file_path,
                template_path=str(template_file),
                output_path=None  # Will auto-generate
            )
            logger.info(
    f"🔍 [DEBUG] Form automation call completed successfully")
        except AttributeError as ae:
            logger.error(
    f"🔍 [DEBUG] AttributeError in form automation: {
        str(ae)}")
            logger.error(
    f"🔍 [DEBUG] This usually means a missing field or method")
            return jsonify({
                'error': 'Attribute error during report generation',
                'details': str(ae),
                'suggestion': 'Check if Excel data has expected columns/structure'
            }), 500
        except KeyError as ke:
            logger.error(f"🔍 [DEBUG] KeyError in form automation: {str(ke)}")
            logger.error(
    f"🔍 [DEBUG] This usually means missing required data field")
            return jsonify({
                'error': 'Missing required data field',
                'details': f'Key not found: {str(ke)}',
                'suggestion': 'Check if Excel data contains expected columns'
            }), 500
        except FileNotFoundError as fnfe:
            logger.error(
    f"🔍 [DEBUG] FileNotFoundError in form automation: {
        str(fnfe)}")
            return jsonify({
                'error': 'File not found during report generation',
                'details': str(fnfe)
            }), 500
        except ImportError as ie:
            logger.error(
    f"🔍 [DEBUG] ImportError in form automation: {
        str(ie)}")
            logger.error(
    f"🔍 [DEBUG] This usually means a missing Python library")
            return jsonify({
                'error': 'Missing required library for report generation',
                'details': str(ie),
                'suggestion': 'Install required dependencies (e.g., python-docx, pandas, openpyxl)'
            }), 500
        except ModuleNotFoundError as mnfe:
            logger.error(
    f"🔍 [DEBUG] ModuleNotFoundError in form automation: {
        str(mnfe)}")
            return jsonify({
                'error': 'Missing Python module',
                'details': str(mnfe)
            }), 500
        except Exception as e:
            logger.error(
    f"🔍 [DEBUG] Unexpected error in form automation: {
        str(e)}")
            logger.error(f"🔍 [DEBUG] Error type: {type(e).__name__}")
            import traceback
            logger.error(f"🔍 [DEBUG] Full traceback: {traceback.format_exc()}")

            # Try fallback simple report generation
            logger.info(f"🔍 [DEBUG] Attempting fallback report generation")
            try:
                fallback_result = _generate_simple_report_fallback(
                    excel_file_path,
                    str(template_file),
                    report_title
                )
                if fallback_result['success']:
                    logger.info(
    f"🔍 [DEBUG] Fallback report generation succeeded")
                    generation_result = fallback_result
                else:
                    raise Exception(
    f"Fallback also failed: {
        fallback_result.get(
            'error',
             'Unknown fallback error')}")
            except Exception as fallback_error:
                logger.error(
    f"🔍 [DEBUG] Fallback also failed: {
        str(fallback_error)}")
                return jsonify({
                    'error': 'Both primary and fallback report generation failed',
                    'primary_error': str(e),
                    'fallback_error': str(fallback_error),
                    'error_type': type(e).__name__
                }), 500

        logger.info(f"🔍 [DEBUG] Generation result: {generation_result}")

        if not generation_result['success']:
            logger.error(
    f"🔍 [DEBUG] Report generation failed: {generation_result}")
            return jsonify({
                'error': 'Failed to generate report',
                'details': generation_result.get('error', 'Unknown error')
            }), 500

        # Calculate file size if file exists
        report_path = generation_result.get('report_path')
        file_size = 0
        if report_path and os.path.exists(report_path):
            file_size = os.path.getsize(report_path)

        # Save report record to database with proper UUID handling
        # Get or create program and template with proper UUID values
        default_program_id = None  # Start with None - optional field
        template_db_id = None      # Start with None - will resolve or skip

        # CRITICAL FIX: Ensure we always have a valid program_id
        try:
            from app.models import Program
            default_program = Program.query.first()
            if default_program:
                default_program_id = default_program.id
                logger.info(f"🔍 [DEBUG] Using existing program ID: {default_program_id}")
            else:
                # Create a default program - this MUST succeed for database integrity
                try:
                    default_program = Program(
                        title="Default Program",
                        description="Automatically created default program for reports",
                        start_date=datetime.utcnow(),
                        end_date=datetime.utcnow() + timedelta(days=365),  # 1 year from now
                        location="System Generated",
                        organizer="System"
                    )
                    db.session.add(default_program)
                    db.session.flush()
                    default_program_id = default_program.id
                    logger.info(f"🔍 [DEBUG] Created default program ID: {default_program_id}")
                except Exception as create_error:
                    logger.error(f"❌ CRITICAL: Failed to create default program: {create_error}")
                    # Try to use a hardcoded fallback ID if creation fails
                    try:
                        # Check if any programs exist at all
                        program_count = Program.query.count()
                        if program_count > 0:
                            # Use the first program we can find
                            fallback_program = Program.query.first()
                            if fallback_program:
                                default_program_id = fallback_program.id
                                logger.warning(f"⚠️ Using fallback program ID: {default_program_id}")
                        else:
                            raise Exception("No programs exist in database")
                    except Exception as fallback_error:
                        logger.error(f"❌ CRITICAL: No program fallback available: {fallback_error}")
                        # Last resort - use a dummy ID (will likely fail but gives better error)
                        default_program_id = 1
                        logger.error(f"🚨 EMERGENCY: Using dummy program_id: {default_program_id}")
        except Exception as program_error:
            logger.error(f"❌ CRITICAL: Could not setup program: {program_error}")
            default_program_id = 1  # Emergency fallback

        # Try to get template ID
        if template_db_record:
            template_db_id = template_db_record.id
            logger.info(
    f"🔍 [DEBUG] Using existing template ID: {template_db_id}")
        else:
            # Try to create a simple template record
            try:
                from sqlalchemy.exc import SQLAlchemyError

                # Create template with only fields that exist in the database
                template_data = {
                    'name': template_id,
                    'description': f"Template for {template_id}",
                    'template_type': "docx",
                }

                # Only add fields that exist in the model/database
                optional_fields = {
                    'category': "automation",
                    'created_by': user_id,
                    'updated_at': datetime.utcnow(),
                    'is_active': True,
                    'version': "1.0",
                    'usage_count': 0,
                    'supports_charts': False,
                    'supports_images': False,
                }

                for field, value in optional_fields.items():
                    if hasattr(ReportTemplate, field):
                        template_data[field] = value

                # Only add file_path if the model supports it
                if hasattr(ReportTemplate, 'file_path') and template_file:
                    template_data['file_path'] = str(template_file)

                new_template = ReportTemplate(**template_data)
                db.session.add(new_template)
                db.session.flush()  # Get the ID
                template_db_id = new_template.id
                logger.info(
    f"🔍 [DEBUG] Created new template ID: {template_db_id}")
            except SQLAlchemyError as template_error:
                logger.error(
    f"SQLAlchemy error creating template: {template_error}")
                db.session.rollback()  # Critical: Rollback the tainted session
                # Try to find any existing template instead of hardcoded ID
                try:
                    # Use safe template model that matches actual database
                    # schema
                    from app.models.safe_template_model import SafeReportTemplate as ReportTemplate
                    fallback_template = ReportTemplate.query.first()
                    if fallback_template:
                        template_db_id = fallback_template.id
                        logger.info(
    f"Using fallback template ID: {template_db_id}")
                    else:
                        logger.warning(
                            "No templates available - report will be created without template_id")
                except Exception:
                    logger.warning("Could not find fallback template")
            except Exception as template_error:
                logger.error(f"❌ CRITICAL: Could not create template record: {template_error}")
                db.session.rollback()  # Critical: Rollback the tainted session
                # CRITICAL FIX: Ensure we always have a valid template_id
                try:
                    # Use safe template model that matches actual database schema
                    from app.models.safe_template_model import SafeReportTemplate as ReportTemplate
                    fallback_template = ReportTemplate.query.first()
                    if fallback_template:
                        template_db_id = fallback_template.id
                        logger.info(f"Using fallback template ID: {template_db_id}")
                    else:
                        # Try to create a default template if none exists
                        try:
                            default_template = ReportTemplate(
                                name="Default Template",
                                description="Automatically created default template",
                                template_type="docx",
                                is_active=True,
                                file_path=str(template_file) if template_file else None
                            )
                            db.session.add(default_template)
                            db.session.flush()
                            template_db_id = default_template.id
                            logger.info(f"🔍 [DEBUG] Created default template ID: {template_db_id}")
                        except Exception as create_template_error:
                            logger.error(f"❌ CRITICAL: Failed to create default template: {create_template_error}")
                            # Try to use any existing template as emergency fallback
                            try:
                                any_template = ReportTemplate.query.first()
                                if any_template:
                                    template_db_id = any_template.id
                                    logger.warning(f"⚠️ Using emergency template fallback ID: {template_db_id}")
                                else:
                                    raise Exception("No templates exist in database")
                            except Exception as emergency_error:
                                logger.error(f"❌ CRITICAL: No template emergency fallback: {emergency_error}")
                                template_db_id = 1  # Emergency dummy ID
                                logger.error(f"🚨 EMERGENCY: Using dummy template_id: {template_db_id}")
                except Exception as fallback_error:
                    logger.error(f"❌ CRITICAL: Could not setup template fallback: {fallback_error}")
                    template_db_id = 1  # Emergency fallback

        # Determine file format
        report_file_extension = Path(
            report_path).suffix.lower() if report_path else '.tex'

        logger.info(
            f"REPORT CREATION DEBUG - JWT user_id: {user_id} (type: {type(user_id)})")
        logger.info(
    f"REPORT CREATION DEBUG - Program ID: {default_program_id}, Template ID: {template_db_id}")

        # Create report with dynamic field assignment to handle different
        # schemas
        report_data = {
            'title': report_title,
            'description': f"Automated report generated from {os.path.basename(excel_file_path)}",
            'report_type': 'automated',
            'generation_status': 'completed',
            'data_source': {},  # Database has data_source field
            'generation_config': {}  # Database has generation_config field
        }

        # Handle template_id - database expects UUID but we have integer
        # For now, set to NULL since we don't have UUID mapping
        # This is a schema mismatch that should be resolved later
        report_data['template_id'] = None  # Database column is UUID, skip for now
        logger.warning(f"Skipping template_id due to UUID/integer mismatch - template: {template_id}")

        # Only add program_id if we have a valid one and the model supports it
        if default_program_id is not None:
            try:
                # Test if program_id field exists in the model by trying to
                # access it
                from app.models import Report as ReportModel
                if hasattr(ReportModel, 'program_id'):
                    report_data['program_id'] = default_program_id
                    logger.info(
    f"REPORT CREATION DEBUG - Added program_id: {default_program_id}")
                else:
                    logger.info(
    f"REPORT CREATION DEBUG - Skipping program_id (field not in model)")
            except Exception as field_check_error:
                logger.warning(
    f"Could not check program_id field: {field_check_error}")

        # Add remaining fields to report_data
        report_data.update({
            # File information - using the correct simple fields
            'file_path': report_path,
            'file_size': file_size,
            # Remove dot
            'file_format': report_file_extension.replace('.', ''),
            'download_url': f"/static/generated/{os.path.basename(report_path or '')}",

            # Data and configuration - using JSON fields
            'data_source': {  # JSON field
                'excel_source': excel_file_path,
                'template_used': template_id,  # Keep original template name for reference
                # Add actual UUID
                'template_uuid': str(template_db_id) if template_db_id else None,
                'file_type': 'excel',
                'automation_type': 'excel'
            },
            'generation_config': {  # JSON field
                'template_id': template_id,  # Keep original template name for reference
                'template_used': template_id,  # Use same value for template_used field
                # Add actual UUID
                'template_uuid': str(template_db_id) if template_db_id else None,
                'template_file': str(template_file),
                'excel_file': excel_file_path,
                'automation_method': 'form_automation_service'
            },

            # Generation metadata
            'generated_at': datetime.utcnow(),
            'generation_time_seconds': 0  # Could calculate actual duration
        })

        # Create report with safe field mapping for development
        try:
            # Only include fields that exist in the database
            safe_report_data = {
                'title': report_data.get('title', 'Excel Report'),
                'description': report_data.get('description', 'Generated from Excel data'),
                'report_type': report_data.get('report_type', 'automated'),
                'created_by': str(get_jwt_identity()),
                'generation_status': 'completed',
                'data_source': json.dumps(report_data.get('data_source', {})),
                'generation_config': json.dumps(report_data.get('generation_config', {})),
                'created_at': datetime.utcnow(),
                'program_id': default_program_id or 1,  # Use fallback program_id
                'template_id': template_db_id or 1  # Use fallback template_id
            }
            
            logger.info(f"🔧 Creating report with safe data: {list(safe_report_data.keys())}")
            
            # Use direct SQL insertion to avoid model mismatch issues
            from sqlalchemy import text
            
            insert_sql = text("""
                INSERT INTO reports (title, description, report_type, created_by, generation_status, data_source, generation_config, created_at, program_id, template_id)
                VALUES (:title, :description, :report_type, :created_by, :generation_status, :data_source, :generation_config, :created_at, :program_id, :template_id)
            """)
            
            result = db.session.execute(insert_sql, safe_report_data)
            report_id = result.lastrowid
            db.session.commit()
            
            logger.info(f"✅ Report created successfully with ID: {report_id}")
            
            # IMPORTANT: Never use MockReport or any non-SQLAlchemy models with db.session.add()
            # The report was already inserted via direct SQL above - just return response data
            report_response = {
                'id': report_id,
                'title': safe_report_data['title'],
                'description': safe_report_data['description'],
                'report_type': safe_report_data['report_type'],
                'generation_status': safe_report_data['generation_status'],
                'created_by': safe_report_data['created_by'],
                'created_at': safe_report_data['created_at'].isoformat()
            }

            return jsonify({
                'success': True,
                'message': 'Report generated successfully',
                'reportId': report_response['id'],          # Frontend expects reportId
                'reportTitle': report_response['title'],    # Frontend expects reportTitle
                'reportType': report_response['report_type'], # Frontend expects reportType
                'status': report_response['generation_status'],        # Frontend expects status
                'report': {
                    'id': report_response['id'],
                    'title': report_response['title'],
                    'description': report_response['description'],
                    'status': report_response['generation_status'],
                    'report_type': report_response['report_type'],
                    'created_at': report_response['created_at'],
                    'generated_at': report_response['created_at'],  # Use same timestamp
                    'templateUsed': template_id,
                    'excelSource': excel_file_path,
                    'generation_time_seconds': None,  # Not tracked in our simplified version
                    'program_id': safe_report_data.get('program_id'),
                    'template_id': safe_report_data.get('template_id'),
                    'created_by': report_response['created_by']
                },
                'generationDetails': generation_result
            }), 200
        except Exception as db_error:
            logger.error(f"❌ Database error creating report: {str(db_error)}")
            logger.error(f"❌ Error type: {type(db_error).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            
            try:
                db.session.rollback()
                logger.info("✅ Database session rolled back successfully")
            except Exception as rollback_error:
                logger.error(f"❌ Failed to rollback database session: {str(rollback_error)}")
            
            return jsonify({
                'success': False,
                'error': f'Failed to create report in database: {str(db_error)}',
                'errorType': type(db_error).__name__
            }), 500

    except Exception as e:
        import traceback

        # Critical: Always rollback on any exception to prevent tainted
        # sessions
        try:
            db.session.rollback()
            logger.info("Database session rolled back due to exception")
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")

        logger.error(
    f"🚨 CRITICAL ERROR in generate_report_from_excel: {
        str(e)}")
        logger.error(f"🚨 Error type: {type(e).__name__}")
        logger.error(f"🚨 Full traceback: {traceback.format_exc()}")
        logger.error(f"🚨 Request data: {request.get_data()}")
        logger.error(f"🚨 Request JSON: {request.get_json()}")
        logger.error(f"🚨 Request method: {request.method}")
        logger.error(f"🚨 Request URL: {request.url}")
        logger.error(f"🚨 Request headers: {dict(request.headers)}")
        logger.error(
    f"🚨 User ID: {
        get_jwt_identity() if 'user_id' not in locals() else user_id}")

        # Return detailed error for debugging with more specific error
        # categories
        error_type = type(e).__name__
        error_details = {
            'error': 'Internal server error during report generation',
            'error_type': error_type,
            'details': str(e),
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4()),
            'suggestion': ''
        }

        # Add specific suggestions based on error type
        if 'TemplateOptimizerService' in str(e):
            error_details['suggestion'] = 'Template optimization failed. Check template file format and content.'
        elif 'ExcelParserService' in str(e):
            error_details['suggestion'] = 'Excel parsing failed. Check Excel file format and accessibility.'
        elif 'FileNotFoundError' in error_type:
            error_details['suggestion'] = 'Required file not found. Check Excel and template file paths.'
        elif 'PermissionError' in error_type:
            error_details['suggestion'] = 'File permission error. Check write permissions to output directory.'
        elif 'ImportError' in error_type or 'ModuleNotFoundError' in error_type:
            error_details['suggestion'] = 'Missing Python dependency. Install required packages.'
        else:
            error_details['suggestion'] = 'Check backend logs for detailed error information.'

        return jsonify(error_details), 500

# ================ CHART DATA GENERATION ================


@nextgen_bp.route('/charts/generate', methods=['POST'])
@jwt_required()
def generate_chart_data():
    """Generate chart data from data source"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No configuration provided'}), 400

        data_source_id = data.get('dataSourceId')
        chart_config = data.get('config', {})

        if not data_source_id:
            return jsonify({'error': 'Data source ID is required'}), 400

        # Generate real chart data from data source
        chart_type = chart_config.get('chartType', 'bar')

        # Get real data from the data source
        if data_source_id.startswith('excel_'):
            # Extract Excel file and generate real chart data
            excel_id = data_source_id.replace('excel_', '')
            uploads_dir = Path(current_app.root_path) / \
                               'static' / 'uploads' / 'excel'

            excel_file = None
            for file in uploads_dir.glob('*.xlsx'):
                if file.stem == excel_id:
                    excel_file = file
                    break

            if excel_file and excel_file.exists():
                try:
                    # Parse Excel file to get real data
                    excel_data = excel_parser.parse_excel_file(str(excel_file))

                    if excel_data.get('success'):
                        chart_data = _generate_real_chart_data(
                            excel_data, chart_type, chart_config)
                    else:
                        chart_data = _generate_fallback_chart_data(chart_type)
                        logger.error(
    f"Failed to parse Excel file: {
        excel_data.get('error')}")
                except Exception as e:
                    logger.error(
    f"Error generating chart data from Excel: {e}")
                    chart_data = _generate_fallback_chart_data(chart_type)
            else:
                chart_data = _generate_fallback_chart_data(chart_type)
                logger.warning(
    f"Excel file not found for data source {data_source_id}")
        else:
            # For form data sources, generate chart data from submissions
            chart_data = _generate_form_chart_data(
    data_source_id, chart_type, chart_config, user_id)

        return jsonify({
            'success': True,
            'chartData': chart_data,
            'metadata': {
                'chartType': chart_type,
                'dataSourceId': data_source_id,
                'generatedAt': datetime.now().isoformat(),
                'recordCount': len(chart_data['labels'])
            }
        }), 200

    except Exception as e:
        logger.error(f"Error generating chart data: {str(e)}")
        return jsonify({'error': 'Failed to generate chart data'}), 500


def _generate_real_chart_data(
    excel_data: Dict[str, Any], chart_type: str, chart_config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate real chart data from Excel data"""
    try:
        columns = excel_data.get('columns', [])
        rows = excel_data.get('rows', [])

        if not columns or not rows:
            return _generate_fallback_chart_data(chart_type)

        # Get column names and data
        column_names = [col.get('name', '') for col in columns]
        data_rows = rows[:100]  # Limit to first 100 rows for performance

        if chart_type == 'line':
            # Find temporal and numerical columns
            temporal_col = None
            numerical_col = None

            for i, col in enumerate(columns):
                if col.get('data_type') in ['date', 'datetime']:
                    temporal_col = i
                elif col.get('data_type') in ['number', 'float', 'int']:
                    numerical_col = i

            if temporal_col is not None and numerical_col is not None:
                # Sort by temporal column
                sorted_data = sorted(
    data_rows, key=lambda x: x[temporal_col] if x[temporal_col] else '')

                chart_data = {
                    'labels': [str(row[temporal_col]) for row in sorted_data if row[temporal_col]],
                    'datasets': [{
                        'label': column_names[numerical_col],
                        'data': [float(row[numerical_col]) if row[numerical_col] else 0 for row in sorted_data if row[temporal_col]],
                        'backgroundColor': 'rgba(37, 99, 235, 0.2)',
                        'borderColor': 'rgba(37, 99, 235, 1)',
                        'borderWidth': 2,
                        'fill': False
                    }]
                }
            else:
                chart_data = _generate_fallback_chart_data(chart_type)

        elif chart_type == 'pie':
            # Find categorical and numerical columns
            categorical_col = None
            numerical_col = None

            for i, col in enumerate(columns):
                if col.get('data_type') in ['text', 'string']:
                    categorical_col = i
                elif col.get('data_type') in ['number', 'float', 'int']:
                    numerical_col = i

            if categorical_col is not None and numerical_col is not None:
                # Group by categorical column and sum numerical values
                from collections import defaultdict
                grouped_data = defaultdict(float)

                for row in data_rows:
                    if row[categorical_col] and row[numerical_col]:
                        grouped_data[str(row[categorical_col])
                                         ] += float(row[numerical_col])

                chart_data = {
                    'labels': list(grouped_data.keys()),
                    'datasets': [{
                        'label': column_names[numerical_col],
                        'data': list(grouped_data.values()),
                        'backgroundColor': [
                            'rgba(37, 99, 235, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(147, 51, 234, 0.8)',
                            'rgba(236, 72, 153, 0.8)'
                        ][:len(grouped_data)]
                    }]
                }
            else:
                chart_data = _generate_fallback_chart_data(chart_type)

        else:  # bar chart (default)
            # Find categorical and numerical columns
            categorical_col = None
            numerical_col = None

            for i, col in enumerate(columns):
                if col.get('data_type') in ['text', 'string']:
                    categorical_col = i
                elif col.get('data_type') in ['number', 'float', 'int']:
                    numerical_col = i

            if categorical_col is not None and numerical_col is not None:
                # Group by categorical column and sum numerical values
                from collections import defaultdict
                grouped_data = defaultdict(float)

                for row in data_rows:
                    if row[categorical_col] and row[numerical_col]:
                        grouped_data[str(row[categorical_col])
                                         ] += float(row[numerical_col])

                chart_data = {
                    'labels': list(grouped_data.keys()),
                    'datasets': [{
                        'label': column_names[numerical_col],
                        'data': list(grouped_data.values()),
                        'backgroundColor': [
                            'rgba(37, 99, 235, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(245, 158, 11, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(147, 51, 234, 0.8)',
                            'rgba(236, 72, 153, 0.8)'
                        ][:len(grouped_data)]
                    }]
                }
            else:
                chart_data = _generate_fallback_chart_data(chart_type)

        return chart_data

    except Exception as e:
        logger.error(f"Error generating real chart data: {e}")
        return _generate_fallback_chart_data(chart_type)


def _generate_fallback_chart_data(chart_type: str) -> Dict[str, Any]:
    """Generate fallback chart data when real data is not available"""
    if chart_type == 'line':
        return {
            'labels': ['No Data'],
            'datasets': [{
                'label': 'No Data Available',
                'data': [0],
                'backgroundColor': 'rgba(156, 163, 175, 0.2)',
                'borderColor': 'rgba(156, 163, 175, 1)',
                'borderWidth': 2,
                'fill': False
            }]
        }
    elif chart_type == 'pie':
        return {
            'labels': ['No Data'],
            'datasets': [{
                'label': 'No Data Available',
                'data': [1],
                'backgroundColor': ['rgba(156, 163, 175, 0.8)']
            }]
        }
    else:  # bar chart
        return {
            'labels': ['No Data'],
            'datasets': [{
                'label': 'No Data Available',
                'data': [0],
                'backgroundColor': ['rgba(156, 163, 175, 0.8)']
            }]
        }


def _generate_form_chart_data(data_source_id: str,
    chart_type: str,
    chart_config: Dict[str,
    Any],
    user_id: str) -> Dict[str,
     Any]:
    """Generate chart data from form submissions"""
    try:
        form_id = int(data_source_id.replace('form_', ''))
        form = Form.query.filter_by(id=form_id, user_id=user_id).first()

        if not form or not form.schema:
            return _generate_fallback_chart_data(chart_type)

        # Get form submissions
        submissions = FormSubmission.query.filter_by(
            form_id=form_id).limit(100).all()

        if not submissions:
            return _generate_fallback_chart_data(chart_type)

        # Analyze form fields and generate appropriate chart data
        fields = form.schema.get('fields', [])

        # Find suitable fields for chart type
        if chart_type == 'line':
            # Look for date/time and numerical fields
            temporal_field = None
            numerical_field = None

            for field in fields:
                if field.get('type') in ['date', 'datetime']:
                    temporal_field = field
                elif field.get('type') in ['number']:
                    numerical_field = field

            if temporal_field and numerical_field:
                # Group submissions by date and sum numerical values
                from collections import defaultdict
                grouped_data = defaultdict(float)

                for submission in submissions:
                    if submission.data:
                        date_val = submission.data.get(temporal_field['id'])
                        num_val = submission.data.get(numerical_field['id'])

                        if date_val and num_val:
                            try:
                                grouped_data[date_val] += float(num_val)
                            except (ValueError, TypeError):
                                continue

                if grouped_data:
                    sorted_data = sorted(grouped_data.items())
                    chart_data = {
                        'labels': [str(date) for date, _ in sorted_data],
                        'datasets': [{
                            'label': numerical_field.get('label', 'Value'),
                            'data': [float(val) for _, val in sorted_data],
                            'backgroundColor': 'rgba(37, 99, 235, 0.2)',
                            'borderColor': 'rgba(37, 99, 235, 1)',
                            'borderWidth': 2,
                            'fill': False
                        }]
                    }
                else:
                    chart_data = _generate_fallback_chart_data(chart_type)
            else:
                chart_data = _generate_fallback_chart_data(chart_type)

        elif chart_type == 'pie':
            # Look for categorical fields
            categorical_field = None

            for field in fields:
                if field.get('type') in ['select', 'radio', 'checkbox']:
                    categorical_field = field
                    break

            if categorical_field:
                # Count submissions by category
                from collections import Counter
                category_counts = Counter()

                for submission in submissions:
                    if submission.data:
                        category = submission.data.get(categorical_field['id'])
                        if category:
                            category_counts[str(category)] += 1

                if category_counts:
                    chart_data = {
                        'labels': list(category_counts.keys()),
                        'datasets': [{
                            'label': categorical_field.get('label', 'Category'),
                            'data': list(category_counts.values()),
                            'backgroundColor': [
                                'rgba(37, 99, 235, 0.8)',
                                'rgba(16, 185, 129, 0.8)',
                                'rgba(245, 158, 11, 0.8)',
                                'rgba(239, 68, 68, 0.8)',
                                'rgba(147, 51, 234, 0.8)',
                                'rgba(236, 72, 153, 0.8)'
                            ][:len(category_counts)]
                        }]
                    }
                else:
                    chart_data = _generate_fallback_chart_data(chart_type)
            else:
                chart_data = _generate_fallback_chart_data(chart_type)

        else:  # bar chart (default)
            # Look for categorical and numerical fields
            categorical_field = None
            numerical_field = None

            for field in fields:
                if field.get('type') in ['select', 'radio', 'checkbox']:
                    categorical_field = field
                elif field.get('type') in ['number']:
                    numerical_field = field

            if categorical_field and numerical_field:
                # Group by category and sum numerical values
                from collections import defaultdict
                grouped_data = defaultdict(float)

                for submission in submissions:
                    if submission.data:
                        category = submission.data.get(categorical_field['id'])
                        num_val = submission.data.get(numerical_field['id'])

                        if category and num_val:
                            try:
                                grouped_data[str(category)] += float(num_val)
                            except (ValueError, TypeError):
                                continue

                if grouped_data:
                    chart_data = {
                        'labels': list(grouped_data.keys()),
                        'datasets': [{
                            'label': numerical_field.get('label', 'Value'),
                            'data': list(grouped_data.values()),
                            'backgroundColor': [
                                'rgba(37, 99, 235, 0.8)',
                                'rgba(16, 185, 129, 0.8)',
                                'rgba(245, 158, 11, 0.8)',
                                'rgba(239, 68, 68, 0.8)',
                                'rgba(147, 51, 234, 0.8)',
                                'rgba(236, 72, 153, 0.8)'
                            ][:len(grouped_data)]
                        }]
                    }
                else:
                    chart_data = _generate_fallback_chart_data(chart_type)
            else:
                chart_data = _generate_fallback_chart_data(chart_type)

        return chart_data

    except Exception as e:
        logger.error(f"Error generating form chart data: {e}")
        return _generate_fallback_chart_data(chart_type)

# ================ AI SUGGESTIONS ================


@nextgen_bp.route('/ai/suggestions', methods=['POST'])
@jwt_required()
def get_ai_suggestions():
    """Get AI-powered report suggestions using Gemini AI"""
    try:
        data = request.get_json()
        data_source_id = data.get('dataSourceId')
        context = data.get('context', {})

        user_id = get_jwt_identity()

        # Get data source information
        data_source_info = _get_data_source_info(data_source_id, user_id)

        # Use AI service to generate suggestions
        ai_suggestions = _generate_ai_suggestions_with_gemini(
            data_source_info, context)

        # Fallback to static suggestions if AI fails
        if not ai_suggestions:
            ai_suggestions = _get_fallback_suggestions(data_source_info)

        return jsonify({
            'success': True,
            'suggestions': ai_suggestions,
            'dataSourceId': data_source_id,
            'generatedAt': datetime.now().isoformat(),
            'aiGenerated': len(ai_suggestions) > 0
        }), 200

    except Exception as e:
        logger.error(f"Error generating AI suggestions: {str(e)}")
        return jsonify({'error': 'Failed to generate AI suggestions'}), 500


def _get_data_source_info(data_source_id: str, user_id: str) -> Dict[str, Any]:
    """Get information about the data source for AI analysis"""
    try:
        if data_source_id.startswith('form_'):
            # Extract form ID and get form fields
            form_id = int(data_source_id.replace('form_', ''))
            form = Form.query.filter_by(id=form_id, creator_id=user_id).first()

            if form and form.schema:
                fields = []
                for field in form.schema.get('fields', []):
                    fields.append({
                        'name': field.get('label', ''),
                        'type': field.get('type', ''),
                        'id': field.get('id', '')
                    })

                # Get some sample submissions for context
                submissions = FormSubmission.query.filter_by(
                    form_id=form_id).limit(5).all()
                sample_data = []
                for submission in submissions:
                    if submission.data:
                        sample_data.append(submission.data)

                return {
                    'type': 'form',
                    'name': form.title,
                    'fields': fields,
                    'recordCount': FormSubmission.query.filter_by(form_id=form_id).count(),
                    'sampleData': sample_data[:3]  # Limit sample data
                }

        # Get real Excel data for Excel sources
        excel_id = data_source_id.replace('excel_', '')
        uploads_dir = Path(current_app.root_path) / \
                           'static' / 'uploads' / 'excel'

        # Find the Excel file
        excel_file = None
        for file in uploads_dir.glob('*.xlsx'):
            if file.stem == excel_id:
                excel_file = file
                break

        if excel_file and excel_file.exists():
            try:
                # Parse Excel file to get real data
                excel_data = excel_parser.parse_excel_file(str(excel_file))

                if excel_data.get('success'):
                    fields = _convert_excel_columns_to_fields(
                        excel_data.get('columns', []))
                    sample_data = excel_data.get(
                        'rows', [])[:3]  # First 3 rows as sample

                    return {
                        'type': 'excel',
                        'name': excel_file.stem.replace('_', ' ').title(),
                        'fields': fields,
                        'recordCount': excel_data.get('total_rows', 0),
                        'sampleData': sample_data
                    }
                else:
                    logger.error(
    f"Failed to parse Excel file {excel_file}: {
        excel_data.get('error')}")
            except Exception as e:
                logger.error(f"Error parsing Excel file {excel_file}: {e}")

        # Return empty data if Excel file not found or parsing failed
        return {
            'type': 'excel',
            'name': 'Unknown Excel File',
            'fields': [],
            'recordCount': 0,
            'sampleData': []
        }

    except Exception as e:
        logger.error(f"Error getting data source info: {str(e)}")
        return {'type': 'unknown', 'fields': [], 'recordCount': 0}


def _generate_ai_suggestions_with_gemini(
    data_source_info: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate AI suggestions using Gemini AI service"""
    try:
        # Import AI services
        from app.services.ai_service import AIService
        from app.services.gemini_content_service import GeminiContentService

        # Try Gemini first, then fallback to AIService
        gemini_service = GeminiContentService()

        if gemini_service.is_available():
            return _generate_suggestions_with_gemini(
                gemini_service, data_source_info, context)

        # Fallback to AIService
        ai_service = AIService()
        if ai_service.gemini_available:
            return _generate_suggestions_with_ai_service(
                ai_service, data_source_info, context)

        logger.warning("No AI service available for suggestions")
        return []

    except Exception as e:
        logger.error(f"Error generating AI suggestions: {str(e)}")
        return []


def _generate_suggestions_with_gemini(
    gemini_service: Any, data_source_info: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate suggestions using GeminiContentService"""
    try:
        # Prepare prompt for Gemini
        fields_info = ", ".join(
            [f"{field['name']} ({field['type']})" for field in data_source_info.get('fields', [])])

        prompt = f"""
        Analyze this data source and suggest the best visualization and analysis approaches:

        Data Source: {data_source_info.get('name', 'Unknown')}
        Type: {data_source_info.get('type', 'unknown')}
        Record Count: {data_source_info.get('recordCount', 0)}
        Fields: {fields_info}

        Generate 4-6 specific, actionable visualization suggestions. For each suggestion, provide:
        1. A clear, descriptive title
        2. The recommended chart type (bar, line, pie, table, scatter, etc.)
        3. Which fields to use for X-axis, Y-axis, grouping, etc.
        4. A brief explanation of why this visualization is valuable
        5. Confidence score (0.0 to 1.0)

        Focus on the most insightful and practical visualizations for business reporting.
        """

        # Use Gemini to generate suggestions
        result = gemini_service.generate_content_variations({
            'data_info': data_source_info,
            'context': context,
            'prompt': prompt
        }, section_type="data_visualization")

        if result and 'variations' in result:
            # Parse the variations to extract visualization suggestions
            return _parse_gemini_variations(
    result['variations'], data_source_info)

        return []

    except Exception as e:
        logger.error(f"Error with Gemini suggestions: {str(e)}")
        return []


def _generate_suggestions_with_ai_service(
    ai_service: Any, data_source_info: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate suggestions using AIService with Gemini"""
    try:
        # Prepare data analysis prompt
        fields = data_source_info.get('fields', [])

        analysis_prompt = f"""
        Data Analysis Request:
        - Data Source: {data_source_info.get('name')}
        - Fields Available: {', '.join([f"{f['name']} ({f['type']})" for f in fields])}
        - Record Count: {data_source_info.get('recordCount', 0)}

        Generate visualization suggestions in JSON format with this structure:
        {{
            "suggestions": [
                {{
                    "id": "unique_id",
                    "title": "Descriptive Title",
                    "chartType": "bar|line|pie|table|scatter",
                    "confidence": 0.85,
                    "preview": "Brief description of what this shows",
                    "reasoning": "Why this visualization is recommended",
                    "mappings": {{
                        "x": "field_name_for_x_axis",
                        "y": "field_name_for_y_axis",
                        "groupBy": "field_name_for_grouping"
                    }},
                    "estimatedValue": "High|Medium|Low - business value"
                }}
            ]
        }}
        """

        # Use Gemini through AIService
        suggestions_data = ai_service._gemini_generate_json(analysis_prompt)

        if suggestions_data and 'suggestions' in suggestions_data:
            return suggestions_data['suggestions']

        return []

    except Exception as e:
        logger.error(f"Error with AI service suggestions: {str(e)}")
        return []


def _parse_gemini_variations(
    variations: List[Dict[str, Any]], data_source_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Gemini variations into structured visualization suggestions"""
    try:
        suggestions = []
        fields = data_source_info.get('fields', [])

        for i, variation in enumerate(variations):
            title = variation.get('title', f'AI Suggestion {i + 1}')
            content = variation.get('content', '')
            style = variation.get('style', 'professional')

            # Extract chart type from content
            chart_type = _extract_chart_type_from_content(content, title)

            # Create suggestion
            suggestion = {
                'id': f"gemini_suggestion_{i + 1}",
                'title': title,
                'confidence': 0.85,  # High confidence for Gemini-generated content
                'preview': content[:100] + "..." if len(content) > 100 else content,
                'reasoning': f"AI-generated suggestion using {style} style analysis",
                'chartType': chart_type,
                'mappings': {},
                'estimatedValue': 'High - AI-powered analysis',
                'aiGenerated': True,
                'style': style
            }

            # Enhance with field mappings
            _enhance_suggestion_mappings(suggestion, fields)
            suggestions.append(suggestion)

        return suggestions[:6]  # Limit to 6 suggestions

    except Exception as e:
        logger.error(f"Error parsing Gemini variations: {str(e)}")
        return []


def _extract_chart_type_from_content(content: str, title: str) -> str:
    """Extract chart type from Gemini content"""
    content_lower = content.lower()
    title_lower = title.lower()

    # Check for chart type indicators
    if any(
    word in content_lower for word in [
        'trend',
        'time',
        'temporal',
         'over time']):
        return 'line'
    elif any(word in content_lower for word in ['distribution', 'pie', 'share', 'percentage']):
        return 'pie'
    elif any(word in content_lower for word in ['comparison', 'compare', 'bar', 'category']):
        return 'bar'
    elif any(word in content_lower for word in ['table', 'detailed', 'comprehensive']):
        return 'table'
    elif any(word in content_lower for word in ['scatter', 'correlation', 'relationship']):
        return 'scatter'
    else:
        return 'bar'  # Default to bar chart


def _parse_gemini_suggestions(
    content: str, data_source_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Gemini response into structured suggestions (legacy method)"""
    try:
        suggestions = []
        fields = data_source_info.get('fields', [])

        # Try to extract structured information from Gemini response
        lines = content.split('\n')
        current_suggestion = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for suggestion titles (numbered or bullet points)
            if re.match(r'^\d+\.|\*|\-', line):
                if current_suggestion:
                    suggestions.append(current_suggestion)

                current_suggestion = {
                    'id': f"ai_suggestion_{len(suggestions) + 1}",
                    'title': re.sub(r'^\d+\.|\*|\-\s*', '', line),
                    'confidence': 0.8,
                    'preview': '',
                    'reasoning': '',
                    'chartType': 'bar',
                    'mappings': {},
                    'estimatedValue': 'Medium'
                }
            elif current_suggestion:
                # Add details to current suggestion
                if 'chart' in line.lower() or 'visualization' in line.lower():
                    current_suggestion['preview'] = line
                elif 'because' in line.lower() or 'reason' in line.lower():
                    current_suggestion['reasoning'] = line

        # Add the last suggestion
        if current_suggestion:
            suggestions.append(current_suggestion)

        # Enhance suggestions with field mappings
        for suggestion in suggestions:
            _enhance_suggestion_mappings(suggestion, fields)

        return suggestions[:6]  # Limit to 6 suggestions

    except Exception as e:
        logger.error(f"Error parsing Gemini suggestions: {str(e)}")
        return []


def _enhance_suggestion_mappings(
    suggestion: Dict[str, Any], fields: List[Dict[str, Any]]) -> None:
    """Enhance suggestion with appropriate field mappings"""
    try:
        # Find appropriate fields for common chart types
        numerical_fields = [
    f for f in fields if f.get('type') in [
        'numerical', 'number']]
        categorical_fields = [
    f for f in fields if f.get('type') in [
        'categorical', 'text', 'select']]
        temporal_fields = [
    f for f in fields if f.get('type') in [
        'temporal', 'date', 'datetime']]

        chart_type = suggestion.get('chartType', 'bar')
        title_lower = suggestion.get('title', '').lower()

        # Determine chart type from title if not specified
        if 'trend' in title_lower or 'time' in title_lower:
            suggestion['chartType'] = 'line'
            if temporal_fields and numerical_fields:
                suggestion['mappings'] = {
                    'x': temporal_fields[0]['name'],
                    'y': numerical_fields[0]['name']
                }
        elif 'distribution' in title_lower or 'share' in title_lower:
            suggestion['chartType'] = 'pie'
            if categorical_fields and numerical_fields:
                suggestion['mappings'] = {
                    'labels': categorical_fields[0]['name'],
                    'values': numerical_fields[0]['name']
                }
        elif 'comparison' in title_lower or 'compare' in title_lower:
            suggestion['chartType'] = 'bar'
            if categorical_fields and numerical_fields:
                suggestion['mappings'] = {
                    'x': categorical_fields[0]['name'],
                    'y': numerical_fields[0]['name']
                }
        elif 'table' in title_lower or 'detail' in title_lower:
            suggestion['chartType'] = 'table'
            suggestion['mappings'] = {
                'columns': [f['name'] for f in fields[:4]]  # First 4 fields
            }

    except Exception as e:
        logger.error(f"Error enhancing suggestion mappings: {str(e)}")


def _get_fallback_suggestions(
    data_source_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate fallback suggestions when AI is not available"""
    fields = data_source_info.get('fields', [])
    suggestions = []

    # Generate basic suggestions based on field types
    numerical_fields = [
    f for f in fields if f.get('type') in [
        'numerical', 'number']]
    categorical_fields = [
    f for f in fields if f.get('type') in [
        'categorical', 'text', 'select']]
    temporal_fields = [
    f for f in fields if f.get('type') in [
        'temporal', 'date', 'datetime']]

    if temporal_fields and numerical_fields:
        suggestions.append({
            'id': 'trend_analysis',
            'title': f'{numerical_fields[0]["name"]} Trend Over Time',
            'confidence': 0.85,
            'preview': f'Line chart showing {numerical_fields[0]["name"]} trends over {temporal_fields[0]["name"]}',
            'reasoning': 'Time-series data detected, perfect for trend analysis',
            'chartType': 'line',
            'mappings': {
                'x': temporal_fields[0]['name'],
                'y': numerical_fields[0]['name']
            },
            'estimatedValue': 'High - Shows temporal patterns'
        })

    if categorical_fields and numerical_fields:
        suggestions.append({
            'id': 'category_comparison',
            'title': f'{numerical_fields[0]["name"]} by {categorical_fields[0]["name"]}',
            'confidence': 0.80,
            'preview': f'Bar chart comparing {numerical_fields[0]["name"]} across different {categorical_fields[0]["name"]}',
            'reasoning': 'Categorical and numerical data ideal for comparison analysis',
            'chartType': 'bar',
            'mappings': {
                'x': categorical_fields[0]['name'],
                'y': numerical_fields[0]['name']
            },
            'estimatedValue': 'Medium - Good for category insights'
        })

    if len(categorical_fields) > 0 and len(numerical_fields) > 0:
        suggestions.append({
            'id': 'distribution_analysis',
            'title': f'{categorical_fields[0]["name"]} Distribution',
            'confidence': 0.75,
            'preview': f'Pie chart showing distribution of {categorical_fields[0]["name"]}',
            'reasoning': 'Categorical data suitable for distribution visualization',
            'chartType': 'pie',
            'mappings': {
                'labels': categorical_fields[0]['name'],
                'values': numerical_fields[0]['name'] if numerical_fields else 'count'
            },
            'estimatedValue': 'Medium - Visual distribution overview'
        })

    if len(fields) > 2:
        suggestions.append({
            'id': 'detailed_table',
            'title': 'Detailed Data Table',
            'confidence': 0.70,
            'preview': 'Comprehensive table view of all available data',
            'reasoning': 'Multiple fields available for detailed analysis',
            'chartType': 'table',
            'mappings': {
                'columns': [f['name'] for f in fields[:6]]
            },
            'estimatedValue': 'High - Complete data overview'
        })

    return suggestions

# ================ REPORT MANAGEMENT ================


@nextgen_bp.route('/reports', methods=['POST'])
@cross_origin(supports_credentials=True)
@jwt_required()
def create_report():
    """Create a new report"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract report data
        title = data.get('title', 'Untitled Report')
        description = data.get('description', '')
        elements = data.get('elements', [])
        layout = data.get('layout', {})

        # Create report record with dynamic field handling
        report_data = {
            'title': title,
            'description': description,
            'created_by': user_id,  # Use user_id as-is (UUID or integer)
            'data_source': {
                'elements': elements,
                'layout': layout,
                'metadata': data.get('metadata', {})
            },
            'generation_status': 'draft'
        }

        # Try to get a valid template_id instead of hardcoding
        try:
            # Use regular template model for development (SQLite compatible)
            from app.models import ReportTemplate
            template = ReportTemplate.query.first()
            if template:
                report_data['template_id'] = template.id
                logger.info(f"Using template ID: {template.id}")
            else:
                logger.warning("No templates available - creating report without template_id")
        except Exception as template_error:
            logger.warning(f"Could not get template: {template_error}")
        
        # Try to get a valid program_id instead of hardcoding
        try:
            from app.models import Report as ReportModel, Program
            if hasattr(ReportModel, 'program_id'):
                program = Program.query.first()
                if program:
                    report_data['program_id'] = program.id
                    logger.info(f"Using program ID: {program.id}")
                else:
                    logger.warning("No programs available - creating report without program_id")
        except Exception as program_error:
            logger.warning(f"Could not get program: {program_error}")
        
        # Create report with safe field mapping for development
        try:
            # Only include fields that exist in the current Report model
            safe_report_data = {
                'title': report_data.get('title', 'Report'),
                'description': report_data.get('description', 'Generated report'),
                'report_type': 'custom',
                'status': 'completed',
                'generation_status': 'draft',
                'user_id': user_id,
                'generation_config': {},
                'data_source': report_data.get('data_source', {}),
                'created_at': datetime.utcnow()
            }
            
            logger.info(f"🔧 Creating report with safe data: {list(safe_report_data.keys())}")
            
            # Use direct SQL insertion to avoid model mismatch issues
            from sqlalchemy import text
            
            insert_sql = text("""
                INSERT INTO reports (title, description, report_type, generation_status, data_source, generation_config, created_at, program_id, template_id)
                VALUES (:title, :description, :report_type, :generation_status, :data_source, :generation_config, :created_at, :program_id, :template_id)
            """)
            
            # Ensure JSON fields are properly serialized
            safe_report_data['data_source'] = json.dumps(safe_report_data.get('data_source', {}))
            safe_report_data['generation_config'] = json.dumps(safe_report_data.get('generation_config', {}))
            safe_report_data['program_id'] = safe_report_data.get('program_id', 1)
            safe_report_data['template_id'] = safe_report_data.get('template_id', 1)
            
            result = db.session.execute(insert_sql, safe_report_data)
            report_id = result.lastrowid
            db.session.commit()
            
            logger.info(f"✅ Report created successfully with ID: {report_id}")
            
            # Create response data
            report_response = {
                'id': report_id,
                'title': safe_report_data['title'],
                'description': safe_report_data['description'],
                'report_type': safe_report_data['report_type'],
                'generation_status': safe_report_data['generation_status'],
                'created_at': safe_report_data['created_at'].isoformat()
            }
            
            return jsonify({
                'success': True,
                'reportId': report_response['id'],          # Frontend expects reportId
                'reportTitle': report_response['title'],    # Frontend expects reportTitle
                'reportType': report_response['report_type'], # Frontend expects reportType
                'status': report_response['generation_status'],        # Frontend expects status
                'report': {
                    'id': report_response['id'],
                    'title': report_response['title'],
                    'description': report_response['description'],
                    'status': report_response['generation_status'],
                    'created_at': report_response['created_at'],
                    'elements': report_data.get('data_source', {}).get('elements', []),
                    'layout': report_data.get('data_source', {}).get('layout', {})
                }
            }), 201
        except Exception as db_error:
            logger.error(f"❌ Database error creating report: {str(db_error)}")
            logger.error(f"❌ Error type: {type(db_error).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            
            try:
                db.session.rollback()
                logger.info("✅ Database session rolled back successfully")
            except Exception as rollback_error:
                logger.error(f"❌ Failed to rollback database session: {str(rollback_error)}")
            
            return jsonify({
                'success': False,
                'error': f'Failed to create report in database: {str(db_error)}',
                'errorType': type(db_error).__name__
            }), 500
        
    except Exception as e:
        logger.error(f"Error creating report: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create report'}), 500

@nextgen_bp.route('/reports/<int:report_id>', methods=['PUT'])
@cross_origin(supports_credentials=True)
@jwt_required()
def update_report(report_id):
    """Update an existing report"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get the report
        report = Report.query.filter_by(id=report_id, created_by=user_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Update report fields
        if 'title' in data:
            report.title = data['title']
        if 'description' in data:
            report.description = data['description']
        if 'elements' in data:
            if not hasattr(report, 'generated_data') or report.generated_data is None:
                report.generated_data = {}
            report.generated_data['elements'] = data['elements']
        if 'layout' in data:
            if not hasattr(report, 'generated_data') or report.generated_data is None:
                report.generated_data = {}
            report.generated_data['layout'] = data['layout']
        
        report.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            return jsonify({
                'success': True,
                'report': {
                    'id': report.id,
                    'title': report.title,
                    'description': report.description,
                    'status': report.status,
                    'createdAt': report.created_at.isoformat(),
                    'updatedAt': report.updated_at.isoformat(),
                    'elements': report.generated_data.get('elements', []) if report.generated_data else [],
                    'layout': report.generated_data.get('layout', {}) if report.generated_data else {}
                }
            })
        except Exception as db_error:
            from sqlalchemy.exc import SQLAlchemyError
            if isinstance(db_error, SQLAlchemyError):
                logger.error(f"Database error updating report: {db_error}")
                db.session.rollback()
            raise  # Re-raise to trigger main exception handler, 200
        
    except Exception as e:
        logger.error(f"Error updating report: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update report'}), 500

@nextgen_bp.route('/reports/<int:report_id>', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_report(report_id):
    """Get a specific report"""
    try:
        user_id = get_jwt_identity()
        logger.info(f"GET REPORT DEBUG - JWT user_id: {user_id} (type: {type(user_id)})")
        
        # Debug: Check all reports for this user with different formats
        all_reports = Report.query.filter_by(id=report_id).all()
        logger.info(f"DEBUG - Found {len(all_reports)} reports with ID {report_id}")
        for r in all_reports:
            logger.info(f"DEBUG - Report ID {r.id}: created_by='{r.created_by}' (type: {type(r.created_by)})")
        
        report = Report.query.filter_by(id=report_id, created_by=user_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({
            'success': True,
            'report': {
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'status': report.status,
                'createdAt': report.created_at.isoformat() if report.created_at else None,
                'elements': report.data_source.get('elements', []) if report.data_source else [],
                'layout': report.data_source.get('layout', {}) if report.data_source else {},
                'file_path': report.file_path,
                'download_url': report.download_url
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching report: {str(e)}")
        return jsonify({'error': 'Failed to update report'}), 500

@nextgen_bp.route('/reports', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_user_reports():
    """Get all reports for the current user"""
    try:
        user_id = get_jwt_identity()
        
        reports = Report.query.filter_by(created_by=user_id).order_by(Report.created_at.desc()).all()
        
        reports_data = []
        for report in reports:
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'status': report.status,
                'createdAt': report.created_at.isoformat() if report.created_at else None,
                'elements': report.data_source.get('elements', []) if report.data_source else [],
                'layout': report.data_source.get('layout', {}) if report.data_source else {},
                'file_path': report.file_path,
                'download_url': report.download_url
            })
        
        return jsonify({
            'success': True,
            'reports': reports_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching user reports: {str(e)}")
        return jsonify({'error': 'Failed to fetch reports'}), 500

@nextgen_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@cross_origin(supports_credentials=True)
@jwt_required()
def delete_report(report_id):
    """Delete a report"""
    try:
        user_id = get_jwt_identity()
        
        report = Report.query.filter_by(id=report_id, created_by=user_id).first()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        try:
            db.session.delete(report)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Report deleted successfully'
            }), 200
        except Exception as db_error:
            from sqlalchemy.exc import SQLAlchemyError
            if isinstance(db_error, SQLAlchemyError):
                logger.error(f"Database error deleting report: {db_error}")
                db.session.rollback()
            raise  # Re-raise to trigger main exception handler
        
    except Exception as e:
        logger.error(f"Error deleting report: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete report'}), 500

# ================ REPORT PREVIEW ================

@nextgen_bp.route('/reports/<int:report_id>/preview', methods=['GET'])
@cross_origin(supports_credentials=True)
@jwt_required()
def preview_report(report_id):
    """Preview a report without downloading"""
    try:
        user_id = get_jwt_identity()
        
        # Get the report
        report = Report.query.filter_by(id=report_id, created_by=user_id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        preview_data = {
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'status': report.status,
            'report_type': report.report_type,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'files': {},
            'metadata': {}
        }
        
        # Add file information
        if report.docx_file_path:
            preview_data['files']['docx'] = {
                'path': report.docx_file_path,
                'size': report.docx_file_size,
                'download_url': report.docx_download_url,
                'exists': os.path.exists(report.docx_file_path) if report.docx_file_path else False
            }
        
        if report.pdf_file_path:
            preview_data['files']['pdf'] = {
                'path': report.pdf_file_path,
                'size': report.pdf_file_size,
                'download_url': report.pdf_download_url,
                'exists': os.path.exists(report.pdf_file_path) if report.pdf_file_path else False
            }
            
        if report.excel_file_path:
            preview_data['files']['excel'] = {
                'path': report.excel_file_path,
                'size': report.excel_file_size,
                'download_url': report.excel_download_url,
                'exists': os.path.exists(report.excel_file_path) if report.excel_file_path else False
            }
        
        # Add metadata
        if hasattr(report, 'generated_data') and report.generated_data:
            preview_data['metadata'] = report.generated_data
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'message': 'Report preview retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error previewing report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to preview report'}), 500

# ================ REPORT EXPORT ================

@nextgen_bp.route('/reports/<report_id>/export', methods=['GET'])
@jwt_required()
def export_report(report_id):
    """Export report in specified format"""
    try:
        user_id = get_jwt_identity()
        export_format = request.args.get('format', 'pdf').lower()
        
        # Get report
        report = Report.query.filter_by(id=report_id, created_by=user_id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        # Use export service for export
        try:
            # Create instance of ExportService
            export_service = ExportService()
            
            # Get report data for export
            report_data = {
                'title': report.title,
                'description': report.description,
                'data': report.data or {},
                'metadata': {
                    'report_id': report.id,
                    'created_at': report.created_at.isoformat() if report.created_at else None,
                    'user_id': user_id
                }
            }
            
            # Export in the requested format
            export_result = export_service.export(
                template_id=str(report.id),
                data_source=report_data,
                formats=[export_format]
            )
            
            # Get the exported file path
            if export_format == 'pdf' and export_result.filenames.get('pdf'):
                filename = export_result.filenames['pdf']
                file_path = Path(current_app.root_path) / '..' / 'uploads' / 'reports' / filename
                return send_file(str(file_path), as_attachment=True, download_name=filename, mimetype='application/pdf')
            elif export_format == 'docx' and export_result.filenames.get('docx'):
                filename = export_result.filenames['docx']
                file_path = Path(current_app.root_path) / '..' / 'uploads' / 'reports' / filename
                return send_file(str(file_path), as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            elif export_format == 'html' and export_result.filenames.get('html'):
                filename = export_result.filenames['html']
                file_path = Path(current_app.root_path) / '..' / 'uploads' / 'reports' / filename
                return send_file(str(file_path), as_attachment=True, download_name=filename, mimetype='text/html')
            else:
                return jsonify({'error': f'Export format {export_format} not supported or failed'}), 400
            
        except Exception as export_error:
            logger.error(f"Export service error: {str(export_error)}")
            
            # Fallback: try to serve existing file if available
            if report.output_url:
                # Remove leading slash and convert to file path
                output_url = getattr(report, 'excel_download_url', None) or getattr(report, 'pdf_download_url', None)
                file_path = Path(current_app.root_path) / 'static' / output_url.lstrip('/')
                if file_path.exists():
                    return send_file(str(file_path), as_attachment=True)
            
            return jsonify({'error': 'Export failed - no output file available'}), 500
        
    except Exception as e:
        logger.error(f"Error exporting report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to export report'}), 500

# ================ ERROR HANDLERS ================

@nextgen_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@nextgen_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@nextgen_bp.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': 'File size too large'}), 413

# ================ DEBUG ENDPOINTS ================

@nextgen_bp.route('/templates/debug', methods=['GET'])
@cross_origin(supports_credentials=True)
def debug_templates():
    """Debug endpoint to check template discovery without authentication"""
    try:
        from pathlib import Path
        
        # Test the path resolution
        templates_dir = Path(__file__).parent.parent.parent / 'templates'
        
        debug_info = {
            'templates_dir_path': str(templates_dir.absolute()),
            'templates_dir_exists': templates_dir.exists(),
            'current_file': __file__,
            'parent_paths': [
                str(Path(__file__).parent),
                str(Path(__file__).parent.parent),
                str(Path(__file__).parent.parent.parent)
            ]
        }
        
        if templates_dir.exists():
            files = []
            for f in templates_dir.glob('*'):
                if f.is_file():
                    files.append({
                        'name': f.name,
                        'suffix': f.suffix,
                        'size': f.stat().st_size,
                        'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                    })
            debug_info['files'] = files
            debug_info['file_count'] = len(files)
        else:
            debug_info['files'] = []
            debug_info['file_count'] = 0
        
        return jsonify(debug_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': str(e.__traceback__)}), 500


def _generate_simple_report_fallback(excel_path: str, template_path: str, report_title: str) -> Dict[str, Any]:
    """
    Simple fallback report generation that doesn't depend on complex services
    """
    try:
        import pandas as pd
        from datetime import datetime
        
        logger.info(f"🔍 [FALLBACK] Starting simple report generation")
        logger.info(f"🔍 [FALLBACK] Excel path: {excel_path}")
        logger.info(f"🔍 [FALLBACK] Template path: {template_path}")
        
        # Read Excel data using pandas
        try:
            df = pd.read_excel(excel_path)
            logger.info(f"🔍 [FALLBACK] Successfully read Excel file: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"🔍 [FALLBACK] Columns: {list(df.columns)}")
        except Exception as excel_error:
            logger.error(f"🔍 [FALLBACK] Failed to read Excel: {str(excel_error)}")
            return {
                'success': False,
                'error': f'Failed to read Excel file: {str(excel_error)}'
            }
        
        # Generate simple text report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_fallback_{timestamp}.txt"
        output_dir = Path(current_app.root_path) / 'static' / 'generated'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        # Create simple report content
        report_content = f"""
AUTOMATED REPORT - {report_title}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Source: {Path(excel_path).name}
Template: {Path(template_path).name}

EXCEL DATA SUMMARY:
- Total rows: {len(df)}
- Total columns: {len(df.columns)}
- Columns: {', '.join(df.columns)}

DATA PREVIEW (First 10 rows):
{df.head(10).to_string()}

BASIC STATISTICS:
{df.describe().to_string()}

---
Report generated using fallback method due to primary service unavailability.
"""
        
        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        logger.info(f"🔍 [FALLBACK] Successfully generated fallback report: {output_path}")
        
        return {
            'success': True,
            'report_path': str(output_path),
            'filename': filename,
            'template_used': template_path,
            'data_source': excel_path,
            'generation_timestamp': datetime.now().isoformat(),
            'fallback': True,
            'message': 'Report generated using fallback method'
        }
        
    except Exception as e:
        logger.error(f"🔍 [FALLBACK] Fallback generation failed: {str(e)}")
        return {
            'success': False,
            'error': f'Fallback generation failed: {str(e)}'
        }


# ================ AI TEXT ENHANCEMENT ENDPOINTS ================

@nextgen_bp.route('/reports/<int:report_id>/view', methods=['GET'])
@jwt_required()
@cross_origin(supports_credentials=True)
def get_report_content(report_id):
    """Get report content for viewing and editing"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get report from database
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT id, title, description, report_type, generation_status, 
                   data_source, generation_config, created_at
            FROM reports 
            WHERE id = :report_id AND created_by = :user_id
        """), {'report_id': report_id, 'user_id': current_user_id})
        
        report = result.fetchone()
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Get the generated LaTeX file
        tex_files = list(Path(current_app.root_path).glob(f"static/generated/report_*_{report_id}_*.tex"))
        if not tex_files:
            # Try finding by title
            tex_files = list(Path(current_app.root_path).glob("static/generated/report_*.tex"))
            tex_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not tex_files:
            return jsonify({'error': 'Report content not found'}), 404
        
        # Read the latest LaTeX file
        latest_tex_file = tex_files[0]
        with open(latest_tex_file, 'r', encoding='utf-8') as f:
            latex_content = f.read()
        
        report_data = {
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'report_type': report.report_type,
            'status': report.generation_status,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'latex_content': latex_content,
            'file_path': str(latest_tex_file)
        }
        
        return jsonify({
            'success': True,
            'report': report_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting report content: {str(e)}")
        return jsonify({'error': 'Failed to get report content'}), 500


@nextgen_bp.route('/reports/<int:report_id>/edit', methods=['PUT'])
@jwt_required()
@cross_origin(supports_credentials=True)
def update_report_content(report_id):
    """Update report content with edited text"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'latex_content' not in data:
            return jsonify({'error': 'LaTeX content is required'}), 400
        
        # Verify user owns the report
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT id FROM reports 
            WHERE id = :report_id AND created_by = :user_id
        """), {'report_id': report_id, 'user_id': current_user_id})
        
        if not result.fetchone():
            return jsonify({'error': 'Report not found'}), 404
        
        # Save the updated content
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_edited_{report_id}_{timestamp}.tex"
        output_dir = Path(current_app.root_path) / 'static' / 'generated'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(data['latex_content'])
        
        # Update the report status to indicate it was edited
        db.session.execute(text("""
            UPDATE reports 
            SET generation_status = 'edited', updated_at = :updated_at
            WHERE id = :report_id
        """), {'report_id': report_id, 'updated_at': datetime.utcnow()})
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report content updated successfully',
            'file_path': str(output_path)
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating report content: {str(e)}")
        return jsonify({'error': 'Failed to update report content'}), 500


@nextgen_bp.route('/ai/enhance-text', methods=['POST'])
@jwt_required()
@cross_origin(supports_credentials=True)
def enhance_text_with_ai():
    """Use AI to enhance/improve selected text"""
    try:
        from app.services.ai_service import ai_service
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text content is required'}), 400
        
        text = data.get('text', '')
        enhancement_type = data.get('type', 'improve')  # improve, formal, casual, technical, summary
        context = data.get('context', 'general')
        
        # Create enhancement prompt based on type
        prompts = {
            'improve': "Improve the following text to be clearer, more professional, and better structured:",
            'formal': "Rewrite the following text in a more formal, professional tone:",
            'casual': "Rewrite the following text in a more casual, conversational tone:",
            'technical': "Enhance the following text with more technical detail and precision:",
            'summary': "Create a concise summary of the following text:",
            'expand': "Expand the following text with more detail and examples:",
        }
        
        prompt = f"""
        {prompts.get(enhancement_type, prompts['improve'])}
        
        Original text: {text}
        
        Context: {context}
        
        Requirements:
        - Maintain the original meaning and key information
        - Improve clarity and readability
        - Use appropriate tone for {enhancement_type} style
        - Return only the enhanced text without explanations
        """
        
        # Try to use AI service
        try:
            if ai_service.openai_api_key:
                response = ai_service.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional text editor and writing assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
                
                enhanced_text = response.choices[0].message.content.strip()
                
                return jsonify({
                    'success': True,
                    'original_text': text,
                    'enhanced_text': enhanced_text,
                    'enhancement_type': enhancement_type,
                    'ai_powered': True
                }), 200
            
            else:
                # Fallback enhancement
                fallback_text = _enhance_text_fallback(text, enhancement_type)
                return jsonify({
                    'success': True,
                    'original_text': text,
                    'enhanced_text': fallback_text,
                    'enhancement_type': enhancement_type,
                    'ai_powered': False,
                    'message': 'AI service unavailable - used basic enhancement'
                }), 200
                
        except Exception as ai_error:
            logger.warning(f"AI enhancement failed: {ai_error}")
            fallback_text = _enhance_text_fallback(text, enhancement_type)
            return jsonify({
                'success': True,
                'original_text': text,
                'enhanced_text': fallback_text,
                'enhancement_type': enhancement_type,
                'ai_powered': False,
                'message': 'AI enhancement failed - used fallback'
            }), 200
        
    except Exception as e:
        logger.error(f"Error enhancing text: {str(e)}")
        return jsonify({'error': 'Failed to enhance text'}), 500


@nextgen_bp.route('/ai/translate-text', methods=['POST'])
@jwt_required()
@cross_origin(supports_credentials=True)
def translate_text():
    """Translate text to different language"""
    try:
        from app.services.ai_service import ai_service
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text content is required'}), 400
        
        text = data.get('text', '')
        target_language = data.get('target_language', 'English')
        source_language = data.get('source_language', 'auto')
        
        prompt = f"""
        Translate the following text from {source_language} to {target_language}.
        Maintain the original formatting and meaning.
        
        Text to translate: {text}
        
        Return only the translated text without explanations.
        """
        
        try:
            if ai_service.openai_api_key:
                response = ai_service.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a professional translator specializing in {target_language} translation."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                translated_text = response.choices[0].message.content.strip()
                
                return jsonify({
                    'success': True,
                    'original_text': text,
                    'translated_text': translated_text,
                    'source_language': source_language,
                    'target_language': target_language,
                    'ai_powered': True
                }), 200
            
            else:
                return jsonify({
                    'success': False,
                    'error': 'Translation requires AI service',
                    'message': 'AI service not configured'
                }), 400
                
        except Exception as ai_error:
            logger.warning(f"AI translation failed: {ai_error}")
            return jsonify({
                'success': False,
                'error': 'Translation failed',
                'message': str(ai_error)
            }), 500
        
    except Exception as e:
        logger.error(f"Error translating text: {str(e)}")
        return jsonify({'error': 'Failed to translate text'}), 500


@nextgen_bp.route('/ai/suggestions', methods=['POST'])
@jwt_required()
@cross_origin(supports_credentials=True)
def get_ai_suggestions():
    """Get AI suggestions for improving content"""
    try:
        from app.services.ai_service import ai_service
        
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text content is required'}), 400
        
        text = data.get('text', '')
        context = data.get('context', 'report')
        
        prompt = f"""
        Analyze the following {context} text and provide improvement suggestions:
        
        Text: {text}
        
        Provide suggestions in the following categories:
        1. Grammar and style improvements
        2. Clarity and readability enhancements  
        3. Content structure suggestions
        4. Professional writing improvements
        
        Return suggestions as a JSON array with format:
        [
            {{
                "category": "grammar|style|clarity|structure|professional",
                "suggestion": "specific suggestion text",
                "importance": "high|medium|low"
            }}
        ]
        """
        
        try:
            if ai_service.openai_api_key:
                response = ai_service.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional writing coach and editor. Provide actionable suggestions."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                
                suggestions_text = response.choices[0].message.content.strip()
                
                # Try to parse JSON response
                try:
                    suggestions = json.loads(suggestions_text)
                except json.JSONDecodeError:
                    # Fallback parsing
                    suggestions = _parse_suggestions_text(suggestions_text)
                
                return jsonify({
                    'success': True,
                    'suggestions': suggestions,
                    'context': context,
                    'ai_powered': True
                }), 200
            
            else:
                # Basic fallback suggestions
                suggestions = _get_basic_suggestions(text)
                return jsonify({
                    'success': True,
                    'suggestions': suggestions,
                    'context': context,
                    'ai_powered': False,
                    'message': 'AI service unavailable - basic suggestions provided'
                }), 200
                
        except Exception as ai_error:
            logger.warning(f"AI suggestions failed: {ai_error}")
            suggestions = _get_basic_suggestions(text)
            return jsonify({
                'success': True,
                'suggestions': suggestions,
                'context': context,
                'ai_powered': False,
                'message': 'AI suggestions failed - basic suggestions provided'
            }), 200
        
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {str(e)}")
        return jsonify({'error': 'Failed to get suggestions'}), 500


def _enhance_text_fallback(text: str, enhancement_type: str) -> str:
    """Fallback text enhancement when AI is unavailable"""
    if enhancement_type == 'formal':
        # Basic formal conversion
        text = text.replace("can't", "cannot").replace("won't", "will not").replace("don't", "do not")
        text = text.replace("it's", "it is").replace("we're", "we are").replace("they're", "they are")
    elif enhancement_type == 'summary':
        # Basic summarization (first sentence or first 100 words)
        sentences = text.split('.')
        if len(sentences) > 1:
            return sentences[0] + '.'
        else:
            words = text.split()
            return ' '.join(words[:100]) + ('...' if len(words) > 100 else '')
    elif enhancement_type == 'expand':
        # Basic expansion (add connecting phrases)
        return text + " This point is particularly important and deserves further consideration."
    
    # Default improvement
    return text.strip().replace('  ', ' ')


def _parse_suggestions_text(text: str) -> List[Dict[str, str]]:
    """Parse suggestions from non-JSON text"""
    suggestions = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and not line.startswith('[') and not line.startswith(']'):
            suggestions.append({
                'category': 'general',
                'suggestion': line,
                'importance': 'medium'
            })
    
    return suggestions[:5]  # Limit to 5 suggestions


def _get_basic_suggestions(text: str) -> List[Dict[str, str]]:
    """Basic text analysis suggestions"""
    suggestions = []
    
    # Check text length
    if len(text) < 50:
        suggestions.append({
            'category': 'structure',
            'suggestion': 'Consider expanding the content for better detail',
            'importance': 'medium'
        })
    elif len(text) > 1000:
        suggestions.append({
            'category': 'clarity',
            'suggestion': 'Consider breaking long text into smaller paragraphs',
            'importance': 'medium'
        })
    
    # Check for common issues
    if text.count('very') > 3:
        suggestions.append({
            'category': 'style',
            'suggestion': 'Consider replacing some instances of "very" with stronger adjectives',
            'importance': 'low'
        })
    
    if not text.strip().endswith('.') and not text.strip().endswith('!') and not text.strip().endswith('?'):
        suggestions.append({
            'category': 'grammar',
            'suggestion': 'Consider adding proper punctuation at the end',
            'importance': 'high'
        })
    
    # Sentence length analysis
    sentences = text.split('.')
    long_sentences = [s for s in sentences if len(s.split()) > 20]
    if len(long_sentences) > len(sentences) * 0.5:
        suggestions.append({
            'category': 'clarity',
            'suggestion': 'Some sentences are quite long - consider breaking them into shorter ones',
            'importance': 'medium'
        })
    
    return suggestions
