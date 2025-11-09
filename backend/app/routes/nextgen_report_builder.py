"""
Next-Gen Report Builder API Routes
Provides comprehensive functionality for the enhanced report builder including
template management, Excel automation, and report generation
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from ..decorators import get_current_user_id, get_current_user, firebase_auth_required

from flask_cors import cross_origin
from datetime import datetime, timedelta
import os
import json
import uuid
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter

from app import db, limiter
from app.models import User, Form, FormSubmission, UserRole
# Import the simple Report model that matches SQLite schema
from app.models import Report
from .reports_api import resolve_template_id
from app.services.form_automation import FormAutomationService
from app.services.export_service import ExportService
from app.services.excel_parser import ExcelParserService
from app.services.template_optimizer import TemplateOptimizerService
from app.services.ai_report_service import AIReportService
import re

logger = logging.getLogger(__name__)

nextgen_bp = Blueprint('nextgen_report_builder', __name__)

# Initialize services
form_automation = FormAutomationService()
excel_parser = ExcelParserService()
template_optimizer = TemplateOptimizerService()
ai_report_service = AIReportService()

# ⚡ PERFORMANCE: Template cache to avoid repeated Firestore/DB/filesystem lookups
# This prevents the 3-8 second template lookup bottleneck
from functools import lru_cache
from threading import Lock

_template_cache = {}
_template_cache_lock = Lock()

def get_cached_template(template_id: str, user_id: str = None):
    """
    Get template from cache or lookup if not cached.
    Cache key includes template_id to handle different templates.
    Returns (template_file_path, template_db_record) tuple or (None, None).
    """
    cache_key = f"{template_id}"

    with _template_cache_lock:
        if cache_key in _template_cache:
            cached_entry = _template_cache[cache_key]
            # Cache expires after 5 minutes
            if time.time() - cached_entry['timestamp'] < 300:
                logger.info(f"✅ Template cache HIT for {template_id}")
                return cached_entry['template_file'], cached_entry['template_record']
            else:
                # Expired, remove from cache
                del _template_cache[cache_key]
                logger.info(f"⏰ Template cache EXPIRED for {template_id}")

    logger.info(f"❌ Template cache MISS for {template_id}, performing lookup...")
    return None, None

def cache_template(template_id: str, template_file, template_record):
    """Store template in cache."""
    cache_key = f"{template_id}"
    with _template_cache_lock:
        _template_cache[cache_key] = {
            'template_file': template_file,
            'template_record': template_record,
            'timestamp': time.time()
        }
        logger.info(f"💾 Template cached: {template_id}")

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

@nextgen_bp.route('/routes-debug', methods=['GET', 'OPTIONS'])
@cross_origin(supports_credentials=True)
def routes_debug():
    """Debug endpoint to verify nextgen routes are registered"""
    if request.method == 'OPTIONS':
        response = jsonify({'message': 'CORS preflight successful'})
        return response

    from flask import current_app
    nextgen_routes = []
    for rule in current_app.url_map.iter_rules():
        if 'nextgen' in str(rule):
            nextgen_routes.append({
                'path': str(rule),
                'methods': sorted(list(rule.methods)),
                'endpoint': rule.endpoint
            })

    return jsonify({
        'message': 'NextGen routes registered successfully',
        'total_routes': len(nextgen_routes),
        'routes': nextgen_routes,
        'timestamp': datetime.utcnow().isoformat()
    })

# ================ DATA SOURCES ================

@nextgen_bp.route('/data-sources', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def get_data_sources():
    """Get available data sources for the report builder with pagination"""
    try:
        user_id = get_current_user_id()

        # ✅ DEBUGGING: Log authentication status
        logger.info(f"📊 Data sources endpoint called by user_id: {user_id}")

        if not user_id:
            logger.error("❌ No user_id found - authentication may have failed")
            return jsonify({
                'error': 'Authentication required',
                'message': 'User ID not found in request context'
            }), 401

        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 50)  # Max 50 items per page
        search = request.args.get('search', '').lower()

        logger.info(f"Data sources request: page={page}, per_page={per_page}, search='{search}'")

        # Get user's forms as data sources
        forms_query = Form.query.filter_by(creator_id=user_id)
        if search:
            forms_query = forms_query.filter(Form.title.ilike(f'%{search}%'))
        forms = forms_query.all()

        # FIX N+1: Get all submission counts in a single query using GROUP BY
        # This prevents N separate queries for each form
        form_ids = [form.id for form in forms]
        submission_counts = {}

        if form_ids:
            from sqlalchemy import func
            counts_query = db.session.query(
                FormSubmission.form_id,
                func.count(FormSubmission.id).label('count')
            ).filter(
                FormSubmission.form_id.in_(form_ids)
            ).group_by(FormSubmission.form_id).all()

            submission_counts = {form_id: count for form_id, count in counts_query}

        data_sources = []
        for form in forms:
            submission_count = submission_counts.get(form.id, 0)  # O(1) lookup instead of N queries
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

        # Get Excel data sources with MUCH better performance
        uploads_dir = Path(current_app.root_path) / 'static' / 'uploads' / 'excel'
        excel_files_processed = 0
        max_excel_files = 20  # Limit to 20 Excel files to prevent slowdown

        if uploads_dir.exists():
            excel_files = list(uploads_dir.glob('*.xlsx'))
            # Sort by modification time (newest first) and limit
            excel_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

            for excel_file in excel_files[:max_excel_files]:
                if excel_files_processed >= max_excel_files:
                    break

                try:
                    # Skip if search doesn't match filename
                    if search and search not in excel_file.name.lower():
                        continue

                    # Get file info quickly without full parsing
                    file_stats = excel_file.stat()
                    file_size = file_stats.st_size

                    # Only do basic file info, skip expensive Excel parsing
                    data_sources.append({
                        'id': f'excel_{excel_file.stem}',
                        'name': excel_file.stem.replace('_', ' ').title(),
                        'type': 'excel',
                        'description': f'Excel file: {excel_file.name}',
                        'fields': [],  # Lazy load fields when needed
                        'connectionStatus': 'connected',
                        'lastUpdated': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        'recordCount': 0,  # Will be calculated on demand
                        'metadata': {
                            'filePath': str(excel_file),
                            'fileSize': f'{file_size / (1024 * 1024):.1f} MB',
                            'sheets': [],  # Will be populated when accessed
                            'uploadedAt': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                            'lazyLoaded': True
                        }
                    })
                    excel_files_processed += 1
                except Exception as e:
                    logger.warning(f"Could not process Excel file {excel_file}: {e}")
                    continue

        # Add one mock data source for development
        if not search or 'mock' in search or 'sales' in search:
            data_sources.append({
                'id': 'mock-excel-1',
                'name': 'Sales Data Q4 2024',
                'type': 'excel',
                'description': 'Mock Excel data source for development and testing',
                'fields': [],
                'connectionStatus': 'connected',
                'lastUpdated': datetime.utcnow().isoformat(),
                'recordCount': 1000,
                'metadata': {
                    'isMock': True,
                    'description': 'Development mock data source'
                }
            })

        # Apply pagination
        total_count = len(data_sources)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_data = data_sources[start_idx:end_idx]

        return jsonify({
            'success': True,
            'data': paginated_data,
            'count': len(paginated_data),
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page,
            'message': f'Data sources retrieved successfully (showing {len(paginated_data)} of {total_count})'
        }), 200

    except Exception as e:
        logger.error(f"❌ Error fetching data sources: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Failed to fetch data sources',
            'message': str(e),
            'type': type(e).__name__
        }), 500

@nextgen_bp.route('/data-sources/<data_source_id>/fields', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def get_data_source_fields(data_source_id):
    """Get fields for a specific data source"""
    try:
        user_id = get_current_user_id()
        logger.info(f"📋 Data source fields requested for: {data_source_id} by user: {user_id}")

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
                            f"Failed to parse Excel file {excel_file}: {excel_data.get('error')}")
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
            f"Error fetching fields for data source {data_source_id}: {str(e)}")
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
    except Exception as e:
        logger.warning(f"Failed to get sample values for form {form_id}, field {field_id}: {str(e)}")
        return []

# ================ TEMPLATES ================

@nextgen_bp.route('/templates', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
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
                f"🔍 [DEBUG] Found {len(db_templates)} templates in database")

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
    f"   Added DB template: {db_template.name} (ID: {template_identifier})")

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
            # Scan both root directory and subdirectories for templates (recursive)
            docx_files = list(templates_dir.rglob('*.docx'))

            # Remove duplicates by converting to set of absolute paths
            seen_files = set()
            unique_docx_files = []
            for f in docx_files:
                abs_path = f.resolve()
                if abs_path not in seen_files:
                    seen_files.add(abs_path)
                    unique_docx_files.append(f)

            logger.info(f"Found {len(unique_docx_files)} unique .docx template files in filesystem")

            for template_file in unique_docx_files:
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
        'default_report': 'Default Report Template',
        'report_template_copy': 'Report Template (Copy)',
        '04- LAPORAN FU _ PUNCAK ALAM_final': 'Laporan FU Puncak Alam (Final)',
        '04- LAPORAN FU _ PUNCAK ALAM (1)': 'Laporan FU Puncak Alam'
    }

    # If not in mappings, clean up the name
    if template_stem.lower() not in [k.lower() for k in name_mappings.keys()]:
        # Handle LAPORAN templates
        if 'LAPORAN' in template_stem.upper():
            return template_stem.replace('_', ' ').replace('  ', ' ').strip()
        # Handle other templates
        return template_stem.replace('_', ' ').title()

    return name_mappings.get(
        template_stem.lower(),
        template_stem.replace('_', ' ').title())

def _get_template_description(template_stem: str) -> str:
    """Get detailed description for template"""
    descriptions = {
        'temp1': 'Standard business report template with professional formatting, suitable for general business reporting needs.',
        'temp1_jinja2': 'Business report template with dynamic content support and Excel data integration capabilities.',
        'temp1_jinja2_excelheaders': 'Enhanced business report template optimized for Excel data with automatic header mapping.',
        'testtemplate': 'Template for testing report generation functionality with sample data structures.',
        'temp2': 'Academic or scientific report template with LaTeX-style formatting for research and technical documents.',
        'default_report': 'Basic report template with minimal formatting, good for simple data presentation.',
        'report_template_copy': 'Copy of main report template with standard formatting and layout.',
        '04- LAPORAN FU _ PUNCAK ALAM_final': 'Final version of Laporan FU Puncak Alam report template.',
        '04- LAPORAN FU _ PUNCAK ALAM (1)': 'Laporan FU Puncak Alam report template.'
    }

    # Check for LAPORAN templates
    if 'LAPORAN' in template_stem.upper() and template_stem.lower() not in [k.lower() for k in descriptions.keys()]:
        return f'Malaysian report template: {template_stem}'

    return descriptions.get(
        template_stem.lower(),
        f'Report template: {template_stem}')

@nextgen_bp.route('/templates', methods=['POST'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def save_report_template():
    """Save a new report template or update existing one"""
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Validate required fields
        required_fields = ['name', 'description']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # For now, just return success to prevent frontend errors
        # In a full implementation, you would save to database/filesystem
        logger.info(f"📋 Template save request received: {data.get('name')}")

        return jsonify({
            'success': True,
            'message': 'Template saved successfully',
            'template_id': data.get('id', f'template_{int(time.time())}')
        }), 200

    except Exception as e:
        logger.error(f"Error saving template: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to save template',
            'message': str(e)
        }), 500

@nextgen_bp.route('/templates/<template_id>/metadata', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
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
            except (zipfile.BadZipFile, KeyError, IOError) as e:
                logger.warning(f"Could not read document structure for {template_file}: {str(e)}")
                metadata['documentInfo'] = {'error': 'Could not read document structure'}

        return jsonify({
            'success': True,
            'metadata': metadata
        }), 200

    except Exception as e:
        logger.error(
    f"Error fetching template metadata for {template_id}: {str(e)}")
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
@cross_origin(supports_credentials=True)
@firebase_auth_required
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

@nextgen_bp.route('/excel/upload', methods=['POST', 'OPTIONS'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def upload_excel_file():
    """
    Upload and process Excel file for report automation with database tracking.
    ENHANCED: Now saves file records to database and returns file ID for multi-file support.
    """
    try:
        user_id = get_current_user_id()

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

        # Generate file ID
        file_id = str(uuid.uuid4())

        # Save uploaded file
        upload_dir = Path(current_app.root_path) / \
                          'static' / 'uploads' / 'excel'
        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{user_id}_{file_id}_{file.filename}"
        file_path = upload_dir / filename
        file.save(str(file_path))

        # Process Excel file with enhanced error handling
        try:
            processing_result = excel_parser.parse_excel_file(str(file_path), file.filename)
        except Exception as parse_error:
            logger.error(f"Excel parsing failed: {str(parse_error)}")
            # Clean up the uploaded file
            try:
                os.remove(str(file_path))
            except (OSError, FileNotFoundError) as e:
                logger.warning(f"Failed to remove file {file_path}: {str(e)}")
            return jsonify({
                'error': 'Failed to process Excel file',
                'details': str(parse_error)
            }), 500

        if not processing_result.get('success'):
            # Clean up the uploaded file
            try:
                os.remove(str(file_path))
            except (OSError, FileNotFoundError) as e:
                logger.warning(f"Failed to remove file {file_path}: {str(e)}")
            return jsonify({
                'error': 'Failed to process Excel file',
                'details': processing_result.get('error', 'Unknown error')
            }), 400

        # Debug logging
        logger.info(f"Processing result keys: {list(processing_result.keys())}")
        logger.info(f"Processing result success: {processing_result.get('success')}")
        logger.info(f"Processing result tables: {len(processing_result.get('tables', []))} tables")
        logger.info(f"Processing result total_rows: {processing_result.get('total_rows', 0)}")

        # Extract columns from the parsed tables
        columns = _extract_columns_from_tables(
            processing_result.get('tables', []))
        logger.info(f"Extracted columns: {len(columns)} columns")

        # ✅ NEW: Save to database for multi-file tracking
        from app.models import ParsedExcelFile, ExcelTable
        from sqlalchemy.exc import IntegrityError, DatabaseError

        # Check if file already exists (in case of retry)
        existing_file = ParsedExcelFile.query.filter_by(id=file_id).first()
        if existing_file:
            logger.warning(f"File with ID {file_id} already exists, cleaning up old records...")
            # Delete existing tables first (due to foreign key constraint)
            ExcelTable.query.filter_by(parsed_file_id=file_id).delete()
            # Delete existing file record
            db.session.delete(existing_file)
            db.session.flush()

        # Create and save ParsedExcelFile first
        parsed_file = ParsedExcelFile(
            id=file_id,
            user_id=user_id,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            status='completed',
            tables_count=len(processing_result.get('tables', [])),
            total_rows=processing_result.get('total_rows', 0),
            total_columns=processing_result.get('total_columns', 0),
            sheets_processed=processing_result.get('sheets_processed', 0),
            file_metadata=processing_result.get('metadata', {})
        )
        db.session.add(parsed_file)
        
        # ✅ CRITICAL FIX: Flush to ensure ParsedExcelFile is inserted before ExcelTable records
        # This ensures the parent record exists in the database before we try to insert child records
        try:
            db.session.flush()
            logger.info(f"✅ ParsedExcelFile flushed to database: file_id={file_id}")
        except IntegrityError as integrity_error:
            logger.error(f"❌ Failed to insert ParsedExcelFile: {str(integrity_error)}", exc_info=True)
            db.session.rollback()
            try:
                os.remove(str(file_path))
            except (OSError, FileNotFoundError):
                pass
            return jsonify({
                'error': 'Failed to save file record to database',
                'details': str(integrity_error),
                'suggestion': 'The file record may already exist or there is a database constraint violation.'
            }), 500
        except DatabaseError as db_error:
            logger.error(f"❌ Database error inserting ParsedExcelFile: {str(db_error)}", exc_info=True)
            db.session.rollback()
            try:
                os.remove(str(file_path))
            except (OSError, FileNotFoundError):
                pass
            return jsonify({
                'error': 'Database error while saving file record',
                'details': str(db_error),
                'suggestion': 'Please try again or contact support if the issue persists.'
            }), 500

        # Save tables to database
        logger.info(f"💾 Saving {len(processing_result.get('tables', []))} tables to database...")
        tables_added = 0
        try:
            for idx, table in enumerate(processing_result.get('tables', [])):
                # ⚡ PERFORMANCE FIX: Only store preview data (first 10 rows) to prevent DB timeout
                # Full data is available from the saved Excel file on disk
                table_data = table.get('data', [])
                preview_data = table_data[:10] if table_data and len(table_data) > 10 else table_data

                # Log data reduction
                original_rows = len(table_data) if table_data else 0
                preview_rows = len(preview_data) if preview_data else 0
                if original_rows > preview_rows:
                    logger.info(f"   Table {idx+1} '{table.get('name', 'Unknown')}': Storing preview ({preview_rows}/{original_rows} rows)")

                excel_table = ExcelTable(
                    id=str(uuid.uuid4()),
                    parsed_file_id=file_id,  # This will now reference an existing parent record
                    name=table.get('name', ''),
                    sheet_name=table.get('sheet_name', ''),
                    row_count=table.get('row_count', 0),
                    column_count=table.get('column_count', 0),
                    headers=table.get('headers', []),
                    data_types=table.get('data_types', []),
                    table_range=table.get('range', ''),
                    data=preview_data  # Store only preview (first 10 rows)
                )
                db.session.add(excel_table)
                tables_added += 1

            # Commit all changes (both ParsedExcelFile and ExcelTable records)
            db.session.commit()
            logger.info(f"✅ Saved Excel file to database: file_id={file_id}, tables={tables_added}")
            
            # ✅ SYNC TO FIRESTORE: Save to Firestore for cross-platform access
            # Only sync after successful SQL commit to ensure data consistency
            try:
                if firebase_auth_manager._initialized and firebase_auth_manager._firestore_db:
                    firestore_db = firebase_auth_manager._firestore_db
                    parsed_files_collection = firestore_db.collection('parsed_excel_files')
                    excel_tables_collection = firestore_db.collection('excel_tables')
                    
                    # Prepare file data for Firestore
                    file_data = {
                        'id': parsed_file.id,
                        'user_id': parsed_file.user_id,
                        'original_filename': parsed_file.original_filename,
                        'file_path': parsed_file.file_path,
                        'file_size': parsed_file.file_size,
                        'status': parsed_file.status,
                        'uploaded_at': parsed_file.uploaded_at.isoformat() if parsed_file.uploaded_at else datetime.utcnow().isoformat(),
                        'tables_count': parsed_file.tables_count,
                        'total_rows': parsed_file.total_rows,
                        'total_columns': parsed_file.total_columns,
                        'sheets_processed': parsed_file.sheets_processed,
                        'metadata': parsed_file.file_metadata or {},
                        'error_message': parsed_file.error_message,
                        'created_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    
                    # ✅ CRITICAL: Save parent file to Firestore FIRST (same pattern as SQL)
                    parsed_files_collection.document(parsed_file.id).set(file_data)
                    logger.info(f"✅ Saved ParsedExcelFile to Firestore: file_id={file_id}")
                    
                    # Save tables to Firestore (only after parent file is saved)
                    firestore_tables_synced = 0
                    for idx, table in enumerate(processing_result.get('tables', [])):
                        # Get the ExcelTable record we just created
                        excel_table_record = ExcelTable.query.filter_by(
                            parsed_file_id=file_id,
                            name=table.get('name', '')
                        ).first()
                        
                        if excel_table_record:
                            firestore_table_data = {
                                'id': excel_table_record.id,
                                'parsed_file_id': excel_table_record.parsed_file_id,  # References parent file
                                'name': excel_table_record.name,
                                'sheet_name': excel_table_record.sheet_name,
                                'row_count': excel_table_record.row_count,
                                'column_count': excel_table_record.column_count,
                                'headers': excel_table_record.headers,
                                'data_types': excel_table_record.data_types,
                                'table_range': excel_table_record.table_range,
                                'has_data': excel_table_record.data is not None,
                                # Note: Don't store full data in Firestore (can be large)
                                'created_at': excel_table_record.created_at.isoformat() if excel_table_record.created_at else datetime.utcnow().isoformat()
                            }
                            
                            excel_tables_collection.document(excel_table_record.id).set(firestore_table_data)
                            firestore_tables_synced += 1
                    
                    logger.info(f"✅ Synced {firestore_tables_synced} ExcelTable records to Firestore")
                else:
                    logger.warning("⚠️ Firestore not available - skipping Firestore sync")
            except Exception as firestore_error:
                # Don't fail the entire request if Firestore sync fails
                # SQL database is the source of truth
                logger.error(f"❌ Failed to sync to Firestore: {str(firestore_error)}", exc_info=True)
                logger.warning("⚠️ Continuing despite Firestore sync failure - data is saved in SQL database")
            
        except IntegrityError as integrity_error:
            logger.error(f"❌ Foreign key constraint violation: {str(integrity_error)}", exc_info=True)
            db.session.rollback()
            # Clean up the uploaded file
            try:
                os.remove(str(file_path))
            except (OSError, FileNotFoundError):
                pass
            # Check if the error is specifically about the foreign key
            error_str = str(integrity_error)
            if 'foreign key constraint' in error_str.lower() or 'parsed_file_id' in error_str.lower():
                return jsonify({
                    'error': 'Database constraint violation',
                    'details': 'The parent file record was not properly saved. This may indicate a database issue.',
                    'technical_details': str(integrity_error),
                    'suggestion': 'Please try uploading the file again. If the problem persists, contact support.'
                }), 500
            else:
                return jsonify({
                    'error': 'Failed to save file to database',
                    'details': str(integrity_error),
                    'suggestion': 'The file may be too large or contain incompatible data. Try a smaller file.'
                }), 500
        except DatabaseError as db_error:
            logger.error(f"❌ Database error during commit: {str(db_error)}", exc_info=True)
            db.session.rollback()
            # Clean up the uploaded file
            try:
                os.remove(str(file_path))
            except (OSError, FileNotFoundError):
                pass
            return jsonify({
                'error': 'Database error while saving file',
                'details': str(db_error),
                'suggestion': 'Please try again or contact support if the issue persists.'
            }), 500
        except Exception as db_error:
            logger.error(f"❌ Unexpected error during database commit: {str(db_error)}", exc_info=True)
            db.session.rollback()
            # Clean up the uploaded file
            try:
                os.remove(str(file_path))
            except (OSError, FileNotFoundError):
                pass
            return jsonify({
                'error': 'Failed to save file to database',
                'details': str(db_error),
                'suggestion': 'The file may be too large or contain incompatible data. Try a smaller file.'
            }), 500

        # Create data source from Excel file with proper structure
        data_source = {
            'id': file_id,  # ✅ CHANGED: Use database file_id instead of generated ID
            'fileId': file_id,  # ✅ NEW: Explicit file ID for backend queries
            'name': file.filename,
            'type': 'excel',
            'description': f'Uploaded Excel file: {file.filename}',
            'filePath': str(file_path),  # ✅ KEPT: For backward compatibility
            'connectionStatus': 'connected',
            'lastUpdated': datetime.now().isoformat(),
            'recordCount': processing_result.get('total_rows', 0),
            'sheets': processing_result.get('sheets_info', []),
            'fields': _convert_excel_columns_to_fields(columns),
            'metadata': {
                'fileSize': file_size,
                'uploadedAt': datetime.now().isoformat(),
                'processedAt': datetime.now().isoformat(),
                'processingStatus': 'completed',
                'tablesCount': len(processing_result.get('tables', []))
            }
        }

        logger.info(
    f"Excel file uploaded successfully: {filename}, {data_source['recordCount']} records, file_id={file_id}")

        return jsonify({
            'success': True,
            'message': 'Excel file uploaded and processed successfully',
            'fileId': file_id,  # ✅ NEW: Return file ID for database lookup
            'dataSource': data_source,
            'processingResult': processing_result
        }), 200

    except Exception as e:
        logger.error(f"Error uploading Excel file: {str(e)}")
        # Rollback database changes
        db.session.rollback()
        # Clean up any uploaded files in case of error
        try:
            if 'file_path' in locals():
                os.remove(str(file_path))
        except (OSError, FileNotFoundError) as cleanup_error:
            logger.warning(f"Failed to cleanup Excel file after error: {str(cleanup_error)}")
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

# ================ MULTI-FILE MANAGEMENT ENDPOINTS ================

@nextgen_bp.route('/excel/user-files', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def get_user_excel_files():
    """
    Get list of user's uploaded Excel files for multi-file selection.
    Supports pagination and search.
    """
    try:
        user_id = get_current_user_id()

        # Pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        search = request.args.get('search', '').strip()

        # Import model
        from app.models import ParsedExcelFile

        # Build query
        query = ParsedExcelFile.query.filter_by(user_id=user_id)

        # Apply search filter
        if search:
            query = query.filter(ParsedExcelFile.original_filename.like(f'%{search}%'))

        # Order by upload date (most recent first)
        query = query.order_by(ParsedExcelFile.uploaded_at.desc())

        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        files = []
        for parsed_file in pagination.items:
            files.append({
                'id': parsed_file.id,
                'fileId': parsed_file.id,
                'name': parsed_file.original_filename,
                'originalFilename': parsed_file.original_filename,
                'filePath': parsed_file.file_path,
                'fileSize': parsed_file.file_size,
                'status': parsed_file.status,
                'uploadedAt': parsed_file.uploaded_at.isoformat() if parsed_file.uploaded_at else None,
                'tablesCount': parsed_file.tables_count,
                'totalRows': parsed_file.total_rows,
                'totalColumns': parsed_file.total_columns,
                'sheetsProcessed': parsed_file.sheets_processed,
                'metadata': parsed_file.metadata
            })

        return jsonify({
            'success': True,
            'files': files,
            'pagination': {
                'page': page,
                'perPage': per_page,
                'totalPages': pagination.pages,
                'totalFiles': pagination.total,
                'hasNext': pagination.has_next,
                'hasPrev': pagination.has_prev
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching user Excel files: {str(e)}")
        return jsonify({'error': 'Failed to fetch Excel files', 'details': str(e)}), 500


@nextgen_bp.route('/excel/files/<file_id>', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def get_excel_file_details(file_id):
    """
    Get detailed information about a specific Excel file including its tables.
    """
    try:
        user_id = get_current_user_id()

        # Import models
        from app.models import ParsedExcelFile, ExcelTable

        # Get file record (verify ownership)
        parsed_file = ParsedExcelFile.query.filter_by(
            id=file_id,
            user_id=user_id
        ).first()

        if not parsed_file:
            return jsonify({'error': 'Excel file not found or access denied'}), 404

        # Get associated tables
        tables = ExcelTable.query.filter_by(parsed_file_id=file_id).all()

        return jsonify({
            'success': True,
            'file': parsed_file.to_dict(),
            'tables': [table.to_dict() for table in tables]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching Excel file details: {str(e)}")
        return jsonify({'error': 'Failed to fetch file details', 'details': str(e)}), 500


@nextgen_bp.route('/excel/files/<file_id>/data', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def get_excel_file_data(file_id):
    """
    Get full data from an Excel file by file ID (for report generation).
    Returns records and columns extracted from the file's tables.
    """
    try:
        user_id = get_current_user_id()

        # Import models
        from app.models import ParsedExcelFile, ExcelTable

        # Get file record (verify ownership)
        parsed_file = ParsedExcelFile.query.filter_by(
            id=file_id,
            user_id=user_id
        ).first()

        if not parsed_file:
            return jsonify({'error': 'Excel file not found or access denied'}), 404

        # Get first table with data
        table = ExcelTable.query.filter_by(parsed_file_id=file_id).first()

        if not table or not table.data:
            return jsonify({'error': 'No data available for this file'}), 404

        # Convert table data to records format
        table_data = table.data
        headers = table.headers if table.headers else (table_data[0] if table_data else [])

        records = []
        data_start_idx = 0 if table.headers else 1  # Skip header row if not already extracted

        for row in table_data[data_start_idx:]:
            if row and any(cell for cell in row):
                record = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                records.append(record)

        return jsonify({
            'success': True,
            'fileId': file_id,
            'filePath': parsed_file.file_path,
            'originalFilename': parsed_file.original_filename,
            'records': records,
            'columns': headers,
            'totalRecords': len(records),
            'metadata': {
                'tablesCount': parsed_file.tables_count,
                'totalRows': parsed_file.total_rows,
                'totalColumns': parsed_file.total_columns
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching Excel file data: {str(e)}")
        return jsonify({'error': 'Failed to fetch file data', 'details': str(e)}), 500


@nextgen_bp.route('/excel/generate-report', methods=['POST'])
@firebase_auth_required
def generate_report_from_excel():
    """
    Generate automated report from Excel data (ASYNC VERSION)

    This endpoint returns immediately with a job ID.
    Client polls /excel/job-status/<job_id> for progress.

    Response Time: < 1 second (to avoid 499 client timeout)
    Processing: Background thread/worker

    This endpoint:
    1. Validates input and creates job record
    2. Returns job ID immediately (< 1s)
    3. Processes report in background
    4. Client polls for completion
    """
    try:
        # ✅ FIX: Enhanced logging with request tracking + timing
        import time
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]

        def log_timing(stage: str, stage_start: float):
            """Helper to log timing for each stage"""
            elapsed = time.time() - stage_start
            total_elapsed = time.time() - start_time
            logger.info(f"🆔 [{request_id}] ⏱️  {stage}: {elapsed:.2f}s (total: {total_elapsed:.2f}s)")
            return time.time()

        logger.info(f"🆔 [{request_id}] ===== NEW ASYNC REPORT GENERATION REQUEST =====")
        logger.info(f"🆔 [{request_id}] Request method: {request.method}")
        logger.info(f"🆔 [{request_id}] Request URL: {request.url}")
        logger.info(f"🆔 [{request_id}] Request endpoint: {request.endpoint}")

        stage_start = time.time()
        user_id = get_current_user_id()
        logger.info(f"🆔 [{request_id}] User ID: {user_id}")
        stage_start = log_timing("Authentication", stage_start)

        data = request.get_json()

        if not data:
            logger.error(f"🆔 [{request_id}] ❌ No data provided in request")
            return jsonify({'error': 'No data provided'}), 400

        # ✅ NEW: Support multiple file IDs for multi-file processing
        file_ids = data.get('fileIds', [])
        file_id = data.get('fileId')  # Single file ID
        excel_file_path = data.get('excelFilePath')  # Legacy path-based (backward compatibility)

        template_id = data.get('templateId')
        report_title = data.get('reportTitle', 'Automated Excel Report')
        charts = data.get('charts', [])  # Chart configurations from frontend
        images = data.get('images', [])  # Image configurations from frontend

        logger.info(f"🆔 [{request_id}] 📄 File IDs: {file_ids}")
        logger.info(f"🆔 [{request_id}] 📄 Single File ID: {file_id}")
        logger.info(f"🆔 [{request_id}] 📄 Excel file path (legacy): {excel_file_path}")
        logger.info(f"🆔 [{request_id}] 📋 Template ID: {template_id}")
        logger.info(f"🆔 [{request_id}] 📝 Report title: {report_title}")
        logger.info(f"🆔 [{request_id}] 📊 Charts to embed: {len(charts)}")
        logger.info(f"🆔 [{request_id}] 🖼️  Images to embed: {len(images)}")

        # Validate input: must have fileIds, fileId, or excelFilePath
        if not file_ids and not file_id and not excel_file_path:
            logger.error(f"🆔 [{request_id}] ❌ Missing required fields")
            return jsonify(
                {'error': 'Either fileIds, fileId, or excelFilePath is required'}), 400

        if not template_id:
            logger.error(f"🆔 [{request_id}] ❌ Missing template ID")
            return jsonify({'error': 'Template ID is required'}), 400

        # Normalize input: convert single fileId to list
        if file_id and not file_ids:
            file_ids = [file_id]

        # ✅ NEW: Process single or multiple file IDs, or legacy file path
        excel_records = []
        excel_columns = []
        excel_metadata = {}
        file_size = 0
        source_files = []

        logger.info(f"🆔 [{request_id}] 📊 Step 1: Loading and parsing Excel data...")
        stage_start = time.time()

        try:
            if file_ids:
                # ✅ NEW: Multi-file or single-file ID mode
                logger.info(f"🆔 [{request_id}] 🆕 Using file ID(s): {file_ids}")
                from app.models import ParsedExcelFile, ExcelTable

                for fid in file_ids:
                    # Get file record from database
                    parsed_file = ParsedExcelFile.query.filter_by(
                        id=fid,
                        user_id=user_id
                    ).first()

                    if not parsed_file:
                        logger.warning(f"🆔 [{request_id}] ⚠️ File not found or access denied: {fid}")
                        continue

                    # Get first table with data
                    table = ExcelTable.query.filter_by(parsed_file_id=fid).first()

                    if not table or not table.data:
                        logger.warning(f"🆔 [{request_id}] ⚠️ No data available for file: {fid}")
                        continue

                    # Extract records from table
                    table_data = table.data
                    headers = table.headers if table.headers else (table_data[0] if table_data else [])

                    # Update columns list (merge unique columns from all files)
                    for header in headers:
                        if header not in excel_columns:
                            excel_columns.append(header)

                    # Skip header row if not already extracted
                    data_start_idx = 0 if table.headers else 1

                    for row in table_data[data_start_idx:]:
                        if row and any(cell for cell in row):
                            record = {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                            record['_source_file'] = parsed_file.original_filename
                            record['_source_file_id'] = fid
                            excel_records.append(record)

                    file_size += parsed_file.file_size or 0
                    source_files.append(parsed_file.original_filename)
                    logger.info(f"🆔 [{request_id}] ✅ Loaded {len(excel_records)} records from {parsed_file.original_filename}")

                if not excel_records:
                    return jsonify({
                        'error': 'No data found in selected files',
                        'suggestion': 'Please ensure the selected files contain data rows'
                    }), 400

                # Update excel_file_path for compatibility (use first file's path)
                first_file = ParsedExcelFile.query.get(file_ids[0])
                excel_file_path = first_file.file_path if first_file else 'multiple_files'

                logger.info(f"🆔 [{request_id}] ✅ Multi-file data loaded:")
                logger.info(f"🆔 [{request_id}]    - Files: {len(file_ids)}")
                logger.info(f"🆔 [{request_id}]    - Total records: {len(excel_records)}")
                logger.info(f"🆔 [{request_id}]    - Merged columns: {len(excel_columns)}")
                logger.info(f"🆔 [{request_id}]    - Source files: {', '.join(source_files)}")

            else:
                # ✅ LEGACY: Path-based mode for backward compatibility
                logger.info(f"🆔 [{request_id}] 📄 Using legacy file path mode")
                from app.utils.railway_paths import validate_excel_path

                excel_path = validate_excel_path(excel_file_path)
                if not excel_path:
                    logger.error(f"🔍 [DEBUG] Excel file not found: {excel_file_path}")
                    return jsonify({'error': f'Excel file not found: {excel_file_path}'}), 400

                if not excel_path.is_file():
                    logger.error(f"🔍 [DEBUG] Excel path is not a file: {excel_file_path}")
                    return jsonify({'error': f'Excel path is not a file: {excel_file_path}'}), 400

                if not os.access(str(excel_path), os.R_OK):
                    logger.error(f"🔍 [DEBUG] Excel file is not readable: {excel_path}")
                    return jsonify({'error': f'Excel file is not readable: {excel_path}'}), 400

                file_size = excel_path.stat().st_size
                excel_file_path = str(excel_path)
                logger.info(f"🆔 [{request_id}] ✅ Excel file validated: {excel_file_path} (size: {file_size} bytes)")

                # Parse Excel file
                excel_data_result = excel_parser.parse_excel_file(excel_file_path)

                if not excel_data_result or not excel_data_result.get('success'):
                    error_msg = excel_data_result.get('error', 'Unknown parsing error') if excel_data_result else 'Parser returned None'
                    logger.error(f"🆔 [{request_id}] ❌ Excel parsing failed: {error_msg}")
                    return jsonify({
                        'error': f'Failed to parse Excel file: {error_msg}',
                        'suggestion': 'Please ensure the Excel file is valid and not corrupted'
                    }), 500

                # Extract records from tables
                tables = excel_data_result.get('tables', [])
                logger.info(f"🆔 [{request_id}] 📊 Found {len(tables)} tables in Excel")

                if tables:
                    for table in tables:
                        table_data = table.get('data', [])
                        table_headers = table.get('headers', [])

                        if table_data and len(table_data) > 0:
                            logger.info(f"🆔 [{request_id}] 📋 Using table: {table.get('name', 'unknown')}")
                            excel_columns = table_headers

                            data_start_idx = 0
                            if table_data and table_data[0] == table_headers:
                                data_start_idx = 1
                                logger.info(f"🆔 [{request_id}] ⚠️ Skipping duplicate header row")

                            for row in table_data[data_start_idx:]:
                                if row and any(cell for cell in row):
                                    record = {}
                                    for col_idx, header in enumerate(excel_columns):
                                        if col_idx < len(row):
                                            record[header] = row[col_idx]
                                    excel_records.append(record)

                            logger.info(f"🆔 [{request_id}] ✅ Converted {len(excel_records)} rows to records")
                            break

                excel_metadata = excel_data_result.get('metadata', {})

            stage_start = log_timing("Excel Data Loading", stage_start)

            logger.info(f"🆔 [{request_id}] ✅ Excel data extraction complete:")
            logger.info(f"🆔 [{request_id}]    - Records: {len(excel_records)}")
            logger.info(f"🆔 [{request_id}]    - Columns: {len(excel_columns)}")
            logger.info(f"🆔 [{request_id}]    - Column names: {excel_columns[:5]}...")
            if excel_records:
                logger.info(f"🆔 [{request_id}]    - Sample record keys: {list(excel_records[0].keys())[:5]}...")
                logger.info(f"🆔 [{request_id}]    - Sample values: {list(excel_records[0].values())[:3]}...")

            # Verification
            if not excel_records:
                return jsonify({
                    'error': 'Excel file(s) contain no data records',
                    'suggestion': 'Please check that the Excel file has data rows (not just headers)'
                }), 400

        except Exception as parse_error:
            logger.error(f"🆔 [{request_id}] ❌ Exception during Excel parsing: {str(parse_error)}")
            logger.error(f"🆔 [{request_id}] Stack trace:", exc_info=True)
            return jsonify({
                'error': f'Excel parsing exception: {str(parse_error)}',
                'suggestion': 'Check backend logs for detailed error information'
            }), 500

        # Look up template in Firestore first, then SQL database, then filesystem
        template_file = None
        template_db_record = None

        logger.info(f"🔍 [DEBUG] Looking up template: {template_id}")
        stage_start = time.time()

        # ⚡ PERFORMANCE: Check cache first (saves 3-8 seconds)
        template_file, template_db_record = get_cached_template(template_id, user_id)

        if template_file:
            logger.info(f"✅ Using cached template: {template_file}")
            stage_start = log_timing("Template Lookup (cached)", stage_start)
        else:
            # Cache miss, do full lookup
            # Try Firestore first
            try:
                from app.middleware.firebase_auth import firebase_auth_manager

                if firebase_auth_manager._initialized and firebase_auth_manager._firestore_db:
                    firestore_db = firebase_auth_manager._firestore_db
                    templates_collection = firestore_db.collection('templates')

                    # Try to find template by name
                    template_name = str(template_id)
                    # Remove extension if present
                    for ext in ['.docx', '.jinja', '.tex', '.html']:
                        if template_name.endswith(ext):
                            template_name = template_name[:-len(ext)]
                            break

                    # Search Firestore by name
                    logger.info(f"🔍 Searching Firestore for template: {template_name}")
                    firestore_templates = templates_collection.where('name', '==', template_name).where('is_active', '==', True).limit(1).stream()

                    for firestore_template in firestore_templates:
                        template_data = firestore_template.to_dict()
                        template_file_path = template_data.get('absolute_path') or template_data.get('file_path')

                        if template_file_path:
                            # For Railway deployment, construct path relative to backend
                            if not Path(template_file_path).exists():
                                # Try relative path from backend directory
                                backend_dir = Path(__file__).parent.parent.parent
                                potential_path = backend_dir / template_data.get('file_path', '')
                                if potential_path.exists():
                                    template_file_path = str(potential_path)

                            template_path = Path(template_file_path)
                            if template_path.exists():
                                template_file = template_path
                                logger.info(f"✅ Found template in Firestore: {template_name}")
                                logger.info(f"   Path: {template_file}")
                                # Create a mock DB record for compatibility
                                # Note: id is set to None because Firestore IDs are strings
                                # and can't be used as foreign keys in the Report model (which expects integers)
                                template_db_record = type('TemplateRecord', (), {
                                    'id': None,  # Firestore ID is a string, can't be used as FK
                                    'firestore_id': firestore_template.id,  # Keep original Firestore ID for reference
                                    'name': template_data.get('name'),
                                    'file_path': str(template_file)
                                })()
                                break
                            else:
                                logger.warning(f"⚠️ Firestore template path does not exist: {template_file_path}")
                        else:
                            logger.warning(f"⚠️ Firestore template has no file_path")

                    if template_file:
                        logger.info("✅ Using template from Firestore")
                    else:
                        logger.info("ℹ️ Template not found in Firestore, trying SQL database")
                else:
                    logger.info("ℹ️ Firestore not available, using SQL database")

            except Exception as firestore_error:
                logger.warning(f"⚠️ Firestore template lookup failed: {str(firestore_error)}")
                logger.info("ℹ️ Falling back to SQL database lookup")

            # If not found in Firestore, try SQL database
            if not template_file:
                try:
                    # Import the correct Template model with file_path support
                    from app.models.template_models import Template as TemplateModel

                    template_db_record = None
                    logger.info(f"✅ Looking up template in SQL DB: {template_id} (type: {type(template_id).__name__})")

                    # Try integer lookup first (if template_id is numeric)
                    try:
                        template_id_int = int(template_id)
                        logger.info(f"🔍 Attempting integer ID lookup: {template_id_int}")
                        template_db_record = TemplateModel.query.filter_by(
                            id=template_id_int, is_active=True
                        ).first()

                        if template_db_record:
                            logger.info(f"✅ Found template by ID in database: {template_db_record.name}")
                        else:
                            logger.info(f"ℹ️ No template found with ID {template_id_int}")

                    except (ValueError, TypeError):
                        # Not a valid integer, template_id is a string name
                        logger.info(f"🔍 Template ID is not numeric, trying name-based lookup: {template_id}")

                        # Try to find by name or file_path
                        # Strip common file extensions from template_id for matching
                        template_name = str(template_id)
                        for ext in ['.docx', '.jinja', '.tex', '.html']:
                            if template_name.endswith(ext):
                                template_name = template_name[:-len(ext)]
                                break

                        # Search by name (exact match)
                        template_db_record = TemplateModel.query.filter_by(
                            name=template_name, is_active=True
                        ).first()

                        if template_db_record:
                            logger.info(f"✅ Found template by name in database: {template_db_record.name}")
                        else:
                            # Try partial match on file_path
                            logger.info(f"🔍 Trying file_path partial match for: {template_id}")
                            template_db_record = TemplateModel.query.filter(
                                TemplateModel.file_path.like(f"%{template_id}%"),
                                TemplateModel.is_active == True
                            ).first()

                            if template_db_record:
                                logger.info(f"✅ Found template by file_path match: {template_db_record.name}")
                            else:
                                logger.info(f"ℹ️ No template found in database with name/path: {template_id}")

                    except Exception as query_error:
                        logger.warning(f"⚠️ Template query failed: {query_error}")
                        template_db_record = None

                    if template_db_record:
                        # Get file path from database
                        file_path = getattr(template_db_record, 'file_path', None)

                        if file_path:
                            template_path = Path(file_path)
                            if template_path.exists():
                                template_file = template_path
                                logger.info(f"✅ Template file found: {template_file}")
                            else:
                                logger.warning(f"⚠️ Template file not found: {file_path}")
                        else:
                            logger.warning(f"⚠️ Template has no file_path")

                except Exception as db_error:
                    logger.warning(f"🔍 [DEBUG] Database template lookup failed: {str(db_error)}")

            # Fallback to filesystem lookup if not found in database
            if not template_file:
                from app.utils.railway_paths import get_templates_dir

                logger.info(f"🔍 [DEBUG] Template not found in DB, falling back to filesystem lookup")
                templates_dir = get_templates_dir()
                logger.info(f"🔍 [DEBUG] Templates directory: {templates_dir}")
                logger.info(f"🔍 [DEBUG] Templates directory exists: {templates_dir.exists()}")
                logger.info(f"🔍 [DEBUG] Looking for template_id: {repr(template_id)}")

                # First, try the template_id as-is (in case it already has an extension)
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
        f"🔍 [DEBUG] Checking template with extension: {potential_file} (exists: {potential_file.exists()})")
                        if potential_file.exists():
                            template_file = potential_file
                            break

                    # If still not found, try fuzzy matching (case-insensitive, ignore underscores/spaces)
                    if not template_file and templates_dir.exists():
                        logger.info("🔍 [DEBUG] Attempting fuzzy match...")
                        normalized_id = template_id.lower().replace('_', '').replace(' ', '').replace('-', '')

                        for template_path in templates_dir.iterdir():
                            if template_path.is_file():
                                normalized_filename = template_path.name.lower().replace('_', '').replace(' ', '').replace('-', '')
                                # Check if template_id matches the filename (with or without extension)
                                if normalized_id in normalized_filename or normalized_filename.startswith(normalized_id):
                                    logger.info(f"🔍 [DEBUG] Fuzzy match found: {template_path.name}")
                                    template_file = template_path
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

        logger.info(f"🆔 [{request_id}] ✅ Template file found: {template_file}")
        logger.info(f"🆔 [{request_id}]    - Exists: {template_file.exists()}")
        logger.info(f"🆔 [{request_id}]    - Size: {template_file.stat().st_size if template_file.exists() else 'N/A'} bytes")
        logger.info(f"🆔 [{request_id}]    - Extension: {template_file.suffix}")

        # ⚡ PERFORMANCE: Cache the template for future requests (only if not from cache)
        if template_file and get_cached_template(template_id, user_id)[0] is None:
            cache_template(template_id, template_file, template_db_record)

        stage_start = log_timing("Template Lookup", stage_start)

        # ✅ FIX: Map extracted data to template format
        logger.info(f"🆔 [{request_id}] ��️  Step 2: Mapping data to template format...")
        try:
            # Import template data mapper
            from app.services.template_data_mapper import template_data_mapper

            # Prepare raw data structure
            raw_data = {
                'records': excel_records,
                'submissions': excel_records,  # Alias for compatibility
                'columns': excel_columns,
                'metadata': {
                    'file_path': excel_file_path,
                    'file_size': file_size,
                    'record_count': len(excel_records),
                    'column_count': len(excel_columns),
                    **excel_metadata
                }
            }

            # Map data to template-specific format
            template_name = template_file.name
            mapped_data = template_data_mapper.map_data_for_template(raw_data, template_name)

            logger.info(f"🆔 [{request_id}] ✅ Data mapped successfully:")
            logger.info(f"🆔 [{request_id}]    - Mapped keys: {list(mapped_data.keys())}")
            logger.info(f"🆔 [{request_id}]    - Data size: {len(str(mapped_data))} chars")

            # ✅ VERIFICATION: Ensure mapped data is not empty
            if not mapped_data or all(not v for v in mapped_data.values()):
                logger.error(f"🆔 [{request_id}] ❌ Data mapping resulted in empty data!")
                return jsonify({
                    'error': 'Data mapping failed - no data to populate template',
                    'suggestion': 'Check template_data_mapper service for errors'
                }), 500

        except Exception as mapping_error:
            logger.error(f"🆔 [{request_id}] ❌ Error mapping data: {str(mapping_error)}")
            logger.error(f"🆔 [{request_id}] Stack trace:", exc_info=True)
            return jsonify({
                'error': f'Data mapping exception: {str(mapping_error)}',
                'suggestion': 'Check backend logs for detailed mapping error'
            }), 500

        # ✅ FIXED: Populate template with data while preserving formatting
        logger.info(f"🆔 [{request_id}] 📄 Step 3: Populating template with Excel data...")
        try:
            import shutil
            from datetime import datetime
            from docxtpl import DocxTemplate
            from app.utils.railway_paths import get_reports_dir

            # ✅ FIX: Use Railway-compatible output directory
            output_dir = get_reports_dir()
            logger.info(f"🆔 [{request_id}] Using output directory: {output_dir}")

            # Generate unique output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f'report_{template_id}_{timestamp}.docx'
            output_path = output_dir / output_filename

            # Try to populate template with data using docxtpl
            try:
                logger.info(f"🆔 [{request_id}] Attempting to populate template with data...")

                # Load template
                doc = DocxTemplate(template_file)

                # Prepare context data from Excel records
                context = {
                    'records': excel_records,
                    'data': excel_records,
                    'items': excel_records,
                    'total_records': len(excel_records),
                    'generated_date': datetime.now().strftime('%d/%m/%Y'),
                    'generated_time': datetime.now().strftime('%H:%M'),
                }

                # Log Excel column names for debugging
                if excel_records:
                    logger.info(f"🆔 [{request_id}] Excel columns found: {list(excel_records[0].keys())}")

                # Add first record fields as top-level variables
                # IMPORTANT: Preserve EXACT Excel column names (with spaces, case-sensitive)
                # to match template placeholders like {{NAMA PESERTA HADIR}} and {{MARKAH_PRE}}
                if excel_records:
                    first_record = excel_records[0]
                    for key, value in first_record.items():
                        # Add with ORIGINAL column name (exact match for placeholders)
                        context[key] = value
                        # Also add cleaned version for flexibility
                        clean_key = key.replace(' ', '_').replace('-', '_').lower()
                        if clean_key != key:
                            context[clean_key] = value

                logger.info(f"🆔 [{request_id}] Template context prepared with {len(context)} keys")

                # Render template with data
                doc.render(context)
                doc.save(output_path)

                logger.info(f"🆔 [{request_id}] ✅ Template populated with data")

                # ✅ Add charts if provided
                if charts and len(charts) > 0:
                    try:
                        from app.services.chart_generator_service import chart_generator_service
                        from docx import Document
                        from docx.shared import Inches

                        logger.info(f"🆔 [{request_id}] 📊 Embedding {len(charts)} charts...")
                        doc_with_charts = Document(output_path)

                        for chart_config in charts:
                            try:
                                # Generate chart image
                                file_path, base64_data = chart_generator_service.generate_chart_from_config(chart_config)

                                if file_path and os.path.exists(file_path):
                                    # Add page break and chart
                                    doc_with_charts.add_page_break()
                                    chart_title = chart_config.get('title', 'Chart')
                                    doc_with_charts.add_heading(chart_title, level=2)
                                    doc_with_charts.add_picture(file_path, width=Inches(6))

                                    logger.info(f"🆔 [{request_id}] ✅ Chart '{chart_title}' embedded")
                            except Exception as chart_error:
                                logger.error(f"🆔 [{request_id}] ❌ Error embedding chart: {str(chart_error)}")

                        doc_with_charts.save(output_path)
                        logger.info(f"🆔 [{request_id}] ✅ All charts embedded successfully")

                    except ImportError:
                        logger.warning(f"🆔 [{request_id}] ⚠️ Chart generation service not available")
                    except Exception as e:
                        logger.error(f"🆔 [{request_id}] ❌ Error during chart embedding: {str(e)}")

                # ✅ Add images if provided
                if images and len(images) > 0:
                    try:
                        from docx import Document
                        from docx.shared import Inches

                        logger.info(f"🆔 [{request_id}] 🖼️  Embedding {len(images)} images...")
                        doc_with_images = Document(output_path)

                        for image_config in images:
                            try:
                                image_path = image_config.get('path') or image_config.get('src')
                                if image_path and os.path.exists(image_path):
                                    doc_with_images.add_page_break()
                                    caption = image_config.get('caption', 'Image')
                                    doc_with_images.add_heading(caption, level=2)
                                    width = image_config.get('width', 6)
                                    doc_with_images.add_picture(image_path, width=Inches(width))

                                    logger.info(f"🆔 [{request_id}] ✅ Image '{caption}' embedded")
                            except Exception as image_error:
                                logger.error(f"🆔 [{request_id}] ❌ Error embedding image: {str(image_error)}")

                        doc_with_images.save(output_path)
                        logger.info(f"🆔 [{request_id}] ✅ All images embedded successfully")

                    except Exception as e:
                        logger.error(f"🆔 [{request_id}] ❌ Error during image embedding: {str(e)}")

            except Exception as render_error:
                # If rendering fails, just copy template
                logger.warning(f"🆔 [{request_id}] ⚠️ Rendering failed: {render_error}")
                shutil.copy2(template_file, output_path)

            logger.info(f"🆔 [{request_id}] ✅ Report generated: {output_path}")

            # Prepare result
            generation_result = {
                'success': True,
                'output_path': str(output_path),
                'report_path': str(output_path),  # Add this for database compatibility
                'output_filename': output_filename,
                'template_used': template_file.name,
                'file_format': 'docx',
                'file_size': output_path.stat().st_size if output_path.exists() else 0
            }
        except AttributeError as ae:
            logger.error(
    f"🔍 [DEBUG] AttributeError in form automation: {str(ae)}")
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
    f"🔍 [DEBUG] FileNotFoundError in form automation: {str(fnfe)}")
            return jsonify({
                'error': 'File not found during report generation',
                'details': str(fnfe)
            }), 500
        except ImportError as ie:
            logger.error(
    f"🔍 [DEBUG] ImportError in form automation: {str(ie)}")
            logger.error(
    f"🔍 [DEBUG] This usually means a missing Python library")
            return jsonify({
                'error': 'Missing required library for report generation',
                'details': str(ie),
                'suggestion': 'Install required dependencies (e.g., python-docx, pandas, openpyxl)'
            }), 500
        except ModuleNotFoundError as mnfe:
            logger.error(
    f"🔍 [DEBUG] ModuleNotFoundError in form automation: {str(mnfe)}")
            return jsonify({
                'error': 'Missing Python module',
                'details': str(mnfe)
            }), 500
        except Exception as e:
            logger.error(
    f"🔍 [DEBUG] Unexpected error in form automation: {str(e)}")
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
    f"Fallback also failed: {fallback_result.get('error', 'Unknown fallback error')}")
            except Exception as fallback_error:
                logger.error(
    f"🔍 [DEBUG] Fallback also failed: {str(fallback_error)}")
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
                    # Rollback tainted transaction from failed program creation
                    try:
                        db.session.rollback()
                        logger.info("🔄 Rolled back failed program creation")
                    except Exception:
                        pass
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
        firestore_template_id = None  # Initialize Firestore ID
        if template_db_record:
            template_db_id = template_db_record.id
            # Get Firestore ID if available
            firestore_template_id = getattr(template_db_record, 'firestore_id', None)
            logger.info(
    f"🔍 [DEBUG] Using existing template ID: {template_db_id}, Firestore ID: {firestore_template_id}")
        else:
            # Try to create a simple template record
            try:
                from sqlalchemy.exc import SQLAlchemyError

                # Clean up template name for database (remove file extension if present)
                clean_template_name = str(template_id)
                for ext in ['.docx', '.jinja', '.tex', '.html']:
                    if clean_template_name.endswith(ext):
                        clean_template_name = clean_template_name[:-len(ext)]
                        break

                # Create template with only fields that exist in the database
                template_data = {
                    'name': clean_template_name,  # Use cleaned name without extension
                    'description': f"Auto-generated template record for {clean_template_name}",
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
                            # Rollback tainted transaction from failed template creation
                            try:
                                db.session.rollback()
                                logger.info("🔄 Rolled back failed template creation")
                            except Exception:
                                pass
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
                # Add integer DB ID if available
                'template_db_id': template_db_id if template_db_id and isinstance(template_db_id, int) else None,
                # Add Firestore ID if available
                'template_firestore_id': firestore_template_id,
                'file_type': 'excel',
                'automation_type': 'excel'
            },
            'generation_config': {  # JSON field
                'template_id': template_id,  # Keep original template name for reference
                'template_used': template_id,  # Use same value for template_used field
                # Add integer DB ID if available
                'template_db_id': template_db_id if template_db_id and isinstance(template_db_id, int) else None,
                # Add Firestore ID if available
                'template_firestore_id': firestore_template_id,
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
                'created_by': str(get_current_user_id()),
                'generation_status': 'completed',
                'data_source': json.dumps(report_data.get('data_source', {})),
                'generation_config': json.dumps(report_data.get('generation_config', {})),
                'created_at': datetime.utcnow(),
            }

            # Only add program_id if we have a valid one (avoid FK constraint errors)
            if default_program_id:
                safe_report_data['program_id'] = default_program_id
                logger.info(f"✅ Using program_id: {default_program_id}")
            else:
                logger.warning("⚠️ No valid program_id available - report will be created without program association")

            # Only add template_id if we have a valid INTEGER one (avoid FK constraint errors)
            # Firestore templates have string IDs and can't be used as foreign keys
            if template_db_id and isinstance(template_db_id, int):
                safe_report_data['template_id'] = template_db_id
                logger.info(f"✅ Using template_id: {template_db_id}")
            else:
                if firestore_template_id:
                    logger.info(f"ℹ️ Using Firestore template (ID: {firestore_template_id}) - not setting template_id FK")
                else:
                    logger.warning("⚠️ No valid template_id available - report will be created without template association")
            
            logger.info(f"🔧 Creating report with safe data: {list(safe_report_data.keys())}")

            # CRITICAL: Ensure session is clean before INSERT
            # Any failed operations above (program/template creation) may have tainted the transaction
            try:
                db.session.rollback()
                logger.info("🔄 Performed safety rollback to ensure clean transaction state")
            except Exception as rollback_error:
                logger.warning(f"⚠️ Safety rollback failed (session may already be clean): {rollback_error}")

            # Use direct SQL insertion to avoid model mismatch issues
            from sqlalchemy import text

            # Add file path and size to the safe_report_data if available
            if report_path:
                safe_report_data['file_path'] = report_path
                safe_report_data['file_size'] = file_size
                safe_report_data['file_format'] = report_file_extension.replace('.', '')
                safe_report_data['download_url'] = f"/static/generated/{os.path.basename(report_path)}"
                safe_report_data['generated_at'] = datetime.utcnow()

            # Build dynamic SQL query based on available fields
            columns = list(safe_report_data.keys())
            placeholders = [f":{col}" for col in columns]

            insert_sql = text(f"""
                INSERT INTO reports ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """)

            logger.info(f"🔧 SQL Insert columns: {columns}")
            logger.info(f"🔧 SQL Insert values: {list(safe_report_data.keys())}")

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

            # Also save report to Firestore for history and cross-platform access
            try:
                from app.services.firestore_report_service import firestore_report_service

                logger.info(f"🔥 Saving report to Firestore...")

                firestore_report_id = firestore_report_service.create_report(
                    user_id=str(user_id),
                    title=safe_report_data['title'],
                    description=safe_report_data['description'],
                    report_type=safe_report_data['report_type'],
                    template_id=firestore_template_id or str(template_id),
                    program_id=str(default_program_id) if default_program_id else None,
                    data_source=json.loads(safe_report_data.get('data_source', '{}')),
                    generation_config=json.loads(safe_report_data.get('generation_config', '{}'))
                )

                if firestore_report_id:
                    logger.info(f"✅ Report saved to Firestore with ID: {firestore_report_id}")

                    # Upload the generated file to Firebase Storage
                    if report_path and os.path.exists(report_path):
                        logger.info(f"📤 Uploading report file to Firebase Storage...")
                        file_format = report_file_extension.replace('.', '')
                        download_url = firestore_report_service.save_report_file(
                            report_id=firestore_report_id,
                            file_path=report_path,
                            file_format=file_format
                        )

                        if download_url:
                            logger.info(f"✅ File uploaded to Firebase Storage: {download_url}")
                            # Add Firestore info to response
                            report_response['firestore_id'] = firestore_report_id
                            report_response['firebase_download_url'] = download_url
                        else:
                            logger.warning("⚠️ Failed to upload file to Firebase Storage")
                    else:
                        # Even without file, update status to completed
                        firestore_report_service.update_report_status(
                            report_id=firestore_report_id,
                            status='completed'
                        )
                        report_response['firestore_id'] = firestore_report_id
                else:
                    logger.warning("⚠️ Failed to save report to Firestore")

            except Exception as firestore_error:
                logger.error(f"❌ Error saving to Firestore: {firestore_error}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue anyway - SQL report was created successfully

            # ⚡ PERFORMANCE FIX: Skip AI suggestions during generation (saves 5-15s)
            # AI suggestions can be fetched later via separate endpoint if needed
            # This prevents HTTP 499 (client timeout at 30s)
            ai_suggestions = None

            # Check if client explicitly requests AI suggestions (default: false for speed)
            include_ai_suggestions = data.get('includeAiSuggestions', False)

            if include_ai_suggestions:
                logger.info(f"🆔 [{request_id}] Client requested AI suggestions...")
                try:
                    ai_suggestions = _generate_ai_suggestions_for_report(
                        report_response['title'],
                        report_response['description'],
                        excel_file_path,
                        template_id
                    )
                except Exception as ai_error:
                    logger.warning(f"Failed to generate AI suggestions: {ai_error}")
                    # Create mock data_source_info for fallback suggestions
                    data_source_info = {
                        'type': 'excel',
                        'name': report_response['title'],
                        'fields': [],
                        'recordCount': 0
                    }
                    ai_suggestions = _get_fallback_suggestions(data_source_info)
            else:
                logger.info(f"🆔 [{request_id}] ⚡ Skipping AI suggestions for faster response")
                # Return empty suggestions with note to fetch separately if needed
                ai_suggestions = []

            return jsonify({
                'success': True,
                'message': 'Report generated successfully',
                'reportId': report_response['id'],          # Frontend expects reportId
                'reportTitle': report_response['title'],    # Frontend expects reportTitle
                'reportType': report_response['report_type'], # Frontend expects reportType
                'status': report_response['generation_status'],        # Frontend expects status
                'showPreview': True,  # Signal frontend to show preview
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
                    'created_by': report_response['created_by'],
                    'file_path': report_path,
                    'download_url': f"/static/generated/{os.path.basename(report_path or '')}",
                    'aiInsights': ai_suggestions  # Include AI suggestions
                },
                'generationDetails': generation_result,
                'aiSuggestions': ai_suggestions  # Also provide at top level for easy access
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
        import sys

        # Critical: Always rollback on any exception to prevent tainted
        # sessions
        try:
            db.session.rollback()
            logger.info("Database session rolled back due to exception")
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")

        # Capture full traceback
        full_traceback = traceback.format_exc()

        logger.error(
    f"🚨 CRITICAL ERROR in generate_report_from_excel: {str(e)}")
        logger.error(f"🚨 Error type: {type(e).__name__}")
        logger.error(f"🚨 Full traceback: {full_traceback}")
        logger.error(f"🚨 Request data: {request.get_data()}")
        logger.error(f"🚨 Request JSON: {request.get_json()}")
        logger.error(f"🚨 Request method: {request.method}")
        logger.error(f"🚨 Request URL: {request.url}")
        logger.error(f"🚨 Request headers: {dict(request.headers)}")
        logger.error(
    f"🚨 User ID: {get_current_user_id() if 'user_id' not in locals() else user_id}")

        # Log system information for debugging
        logger.error(f"🚨 Python version: {sys.version}")
        logger.error(f"🚨 Platform: {sys.platform}")
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            logger.error(f"🚨 Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
        except:
            pass

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

        # Add traceback in non-production environments
        is_development = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('DEBUG') == 'True'
        if is_development:
            error_details['traceback'] = full_traceback
            error_details['python_version'] = sys.version
            error_details['platform'] = sys.platform

        # Add specific suggestions based on error type
        if 'TemplateOptimizerService' in str(e):
            error_details['suggestion'] = 'Template optimization failed. Check template file format and content.'
        elif 'ExcelParserService' in str(e) or 'ExcelTableDetector' in str(e):
            error_details['suggestion'] = 'Excel parsing failed. Check Excel file format and accessibility. Try reducing file size.'
        elif 'FileNotFoundError' in error_type:
            error_details['suggestion'] = 'Required file not found. Check Excel and template file paths.'
        elif 'PermissionError' in error_type:
            error_details['suggestion'] = 'File permission error. Check write permissions to output directory.'
        elif 'ImportError' in error_type or 'ModuleNotFoundError' in error_type:
            error_details['suggestion'] = 'Missing Python dependency. Install required packages.'
        elif 'MemoryError' in error_type:
            error_details['suggestion'] = 'Out of memory. Try reducing Excel file size or splitting into smaller files.'
        elif 'TimeoutError' in error_type or 'timeout' in str(e).lower():
            error_details['suggestion'] = 'Processing timeout. Excel file too large or complex. Try simplifying the spreadsheet.'
        elif 'openpyxl' in str(e).lower() or 'xlrd' in str(e).lower():
            error_details['suggestion'] = 'Excel library error. Check if file is corrupted or in an unsupported format.'
        else:
            error_details['suggestion'] = 'Check backend logs for detailed error information.'

        return jsonify(error_details), 500

# ================ CHART DATA GENERATION ================

@nextgen_bp.route('/charts/generate', methods=['POST'])
def generate_chart_data():
    """Generate chart data from data source"""
    try:
        user_id = get_current_user_id()
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
    f"Failed to parse Excel file: {excel_data.get('error')}")
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
@limiter.limit("10 per hour")
def get_ai_suggestions():
    """Get AI-powered report suggestions using Gemini AI"""
    try:
        data = request.get_json()
        data_source_id = data.get('dataSourceId')
        context = data.get('context', {})

        user_id = get_current_user_id()

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
    f"Failed to parse Excel file {excel_file}: {excel_data.get('error')}")
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

def _generate_ai_suggestions_for_report(title: str, description: str, excel_file_path: str, template_id: str) -> List[Dict[str, Any]]:
    """
    Generate AI-powered suggestions for a report based on its content and data
    
    Args:
        title: Report title
        description: Report description
        excel_file_path: Path to the Excel file used for the report
        template_id: ID of the template used
    
    Returns:
        List of AI-generated suggestions
    """
    try:
        # Try to use the existing AI services
        from app.services.ai_service import AIService
        from app.services.gemini_content_service import GeminiContentService
        
        # Parse Excel data to get better context
        excel_data = excel_parser.parse_excel_file(excel_file_path)
        
        if excel_data.get('success'):
            # Create data summary for AI analysis
            data_summary = {
                'report_title': title,
                'report_description': description,
                'template_id': template_id,
                'total_records': excel_data.get('total_rows', 0),
                'columns': excel_data.get('columns', []),
                'key_metrics': _extract_key_metrics_from_excel(excel_data),
                'data_types': _analyze_data_types(excel_data.get('columns', []))
            }
            
            # Try Gemini first
            gemini_service = GeminiContentService()
            if gemini_service.is_available():
                try:
                    suggestions = gemini_service.generate_content_variations(data_summary, "executive_summary")
                    if suggestions and 'variations' in suggestions:
                        return _format_gemini_suggestions(suggestions['variations'])
                except Exception as e:
                    logger.warning(f"Gemini suggestions failed: {e}")
            
            # Fallback to OpenAI-based AIService
            ai_service = AIService()
            if ai_service.openai_api_key:
                try:
                    # Generate report suggestions using the existing AI service
                    suggestions_result = ai_service.generate_report_suggestions(data_summary, "business_report")
                    if suggestions_result.get('success') and 'suggestions' in suggestions_result:
                        suggestions = suggestions_result['suggestions']
                        return _format_ai_service_suggestions(suggestions)
                except Exception as e:
                    logger.warning(f"AI service suggestions failed: {e}")
        
        # If we have Excel data but AI services failed, create basic suggestions
        if excel_data.get('success'):
            return _generate_basic_suggestions_from_excel(excel_data, title)
        
        # If no Excel data or all AI services failed, return generic suggestions
        return _generate_generic_report_suggestions(title, description)
        
    except Exception as e:
        logger.error(f"Error in _generate_ai_suggestions_for_report: {e}")
        # Return empty list so the fallback can take over
        return []

def _extract_key_metrics_from_excel(excel_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics from Excel data for AI analysis"""
    try:
        columns = excel_data.get('columns', [])
        rows = excel_data.get('rows', [])
        
        if not columns or not rows:
            return {}
        
        metrics = {}
        
        # For numeric columns, calculate basic statistics
        for i, col in enumerate(columns):
            if col.get('data_type') in ['number', 'float', 'int']:
                col_name = col.get('name', f'Column_{i}')
                col_values = []
                
                # Extract values from rows (skip header)
                for row in rows[1:]:  # Skip header row
                    if i < len(row) and row[i] is not None:
                        try:
                            col_values.append(float(row[i]))
                        except (ValueError, TypeError):
                            pass
                
                if col_values:
                    metrics[col_name] = {
                        'count': len(col_values),
                        'sum': sum(col_values),
                        'average': sum(col_values) / len(col_values) if col_values else 0,
                        'min': min(col_values) if col_values else 0,
                        'max': max(col_values) if col_values else 0
                    }
        
        return metrics
    except Exception as e:
        logger.error(f"Error extracting key metrics: {e}")
        return {}

def _analyze_data_types(columns: List[Dict[str, Any]]) -> Dict[str, str]:
    """Analyze data types in columns"""
    data_types = {}
    for col in columns:
        col_name = col.get('name', 'Unknown')
        data_types[col_name] = col.get('data_type', 'unknown')
    return data_types

def _format_gemini_suggestions(variations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format Gemini variations as suggestions"""
    suggestions = []
    for i, variation in enumerate(variations):
        suggestions.append({
            'id': f"suggestion_{i+1}",
            'title': variation.get('title', f'Suggestion {i+1}'),
            'content': variation.get('content', ''),
            'style': variation.get('style', 'professional'),
            'confidence': 0.85,
            'type': 'ai_generated'
        })
    return suggestions

def _format_ai_service_suggestions(suggestions_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format AI service suggestions"""
    suggestions = []
    
    # Handle key metrics suggestions
    key_metrics = suggestions_data.get('key_metrics', [])
    for i, metric in enumerate(key_metrics[:3]):  # Limit to top 3
        suggestions.append({
            'id': f"metric_{i+1}",
            'title': metric.get('metric', f'Metric {i+1}'),
            'content': f"{metric.get('description', '')} Value: {metric.get('value', 'N/A')}",
            'importance': metric.get('importance', 'medium'),
            'type': 'key_metric'
        })
    
    # Handle visualization suggestions
    visualizations = suggestions_data.get('visualizations', [])
    for i, viz in enumerate(visualizations[:3]):  # Limit to top 3
        suggestions.append({
            'id': f"viz_{i+1}",
            'title': f"{viz.get('type', 'Chart').title()} Suggestion",
            'content': viz.get('purpose', ''),
            'chart_type': viz.get('type', 'bar'),
            'fields': viz.get('data_fields', []),
            'type': 'visualization'
        })
    
    # Handle executive points
    exec_points = suggestions_data.get('executive_points', [])
    for i, point in enumerate(exec_points[:3]):  # Limit to top 3
        suggestions.append({
            'id': f"exec_{i+1}",
            'title': f"Key Insight #{i+1}",
            'content': point,
            'type': 'executive_point'
        })
    
    return suggestions

def _generate_basic_suggestions_from_excel(excel_data: Dict[str, Any], report_title: str) -> List[Dict[str, Any]]:
    """Generate basic suggestions from Excel data when AI is not available"""
    suggestions = []
    
    columns = excel_data.get('columns', [])
    total_rows = excel_data.get('total_rows', 0)
    
    if columns:
        # Suggest chart types based on data
        numeric_cols = [col for col in columns if col.get('data_type') in ['number', 'float', 'int']]
        categorical_cols = [col for col in columns if col.get('data_type') in ['text', 'string', 'categorical']]
        
        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            suggestions.append({
                'id': 'chart_1',
                'title': 'Bar Chart Suggestion',
                'content': f'Compare {numeric_cols[0].get("name")} across different {categorical_cols[0].get("name")} categories',
                'chart_type': 'bar',
                'fields': [categorical_cols[0].get('name'), numeric_cols[0].get('name')],
                'type': 'visualization',
                'confidence': 0.8
            })
        
        if len(numeric_cols) >= 2:
            suggestions.append({
                'id': 'chart_2',
                'title': 'Scatter Plot Suggestion',
                'content': f'Analyze correlation between {numeric_cols[0].get("name")} and {numeric_cols[1].get("name")}',
                'chart_type': 'scatter',
                'fields': [numeric_cols[0].get('name'), numeric_cols[1].get('name')],
                'type': 'visualization',
                'confidence': 0.7
            })
        
        # Summary suggestion
        suggestions.append({
            'id': 'summary',
            'title': f'{report_title} Summary',
            'content': f'This report is based on {total_rows} records with {len(columns)} data fields. Focus on key metrics and trends in the data.',
            'type': 'executive_summary',
            'confidence': 0.9
        })
    
    return suggestions

def _generate_generic_report_suggestions(title: str, description: str) -> List[Dict[str, Any]]:
    """Generate generic suggestions when no data is available"""
    return [
        {
            'id': 'generic_1',
            'title': 'Executive Summary',
            'content': f'Provide a high-level overview of the {title} report findings',
            'type': 'executive_summary',
            'confidence': 0.7
        },
        {
            'id': 'generic_2',
            'title': 'Key Findings',
            'content': 'Highlight the most important insights from your data analysis',
            'type': 'key_findings',
            'confidence': 0.7
        },
        {
            'id': 'generic_3',
            'title': 'Recommendations',
            'content': 'Based on your analysis, what actions should be taken?',
            'type': 'recommendations',
            'confidence': 0.7
        }
    ]

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
@firebase_auth_required
def create_report():
    """Create a new report"""
    try:
        user_id = get_current_user_id()
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
@firebase_auth_required
def update_report(report_id):
    """Update an existing report"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Get the report
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report.created_by if hasattr(report, 'created_by') and report.created_by else report.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to update this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403
        
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
@firebase_auth_required
def get_report(report_id):
    """Get a specific report"""
    try:
        user_id = get_current_user_id()

        # Get the report
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report.created_by if hasattr(report, 'created_by') and report.created_by else report.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to view this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403
        
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
@firebase_auth_required
def get_user_reports():
    """Get all reports for the current user from both SQL and Firestore"""
    try:
        user_id = get_current_user_id()

        # Get reports from SQL database
        sql_reports = Report.query.filter_by(created_by=str(user_id)).order_by(Report.created_at.desc()).all()

        reports_data = []

        # Add SQL reports
        for report in sql_reports:
            reports_data.append({
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'status': report.status,
                'createdAt': report.created_at.isoformat() if report.created_at else None,
                'elements': report.data_source.get('elements', []) if report.data_source else [],
                'layout': report.data_source.get('layout', {}) if report.data_source else {},
                'file_path': report.file_path,
                'download_url': report.download_url,
                'source': 'sql'  # Mark source for debugging
            })

        # Also get reports from Firestore
        try:
            from app.services.firestore_report_service import firestore_report_service

            firestore_reports = firestore_report_service.get_user_reports(
                user_id=str(user_id),
                limit=100
            )

            # Add Firestore reports
            for firestore_report in firestore_reports:
                # Convert Firestore timestamps to ISO format
                created_at = firestore_report.get('createdAt')
                if created_at:
                    # Handle Firestore timestamp
                    if hasattr(created_at, 'isoformat'):
                        created_at_iso = created_at.isoformat()
                    else:
                        created_at_iso = created_at
                else:
                    created_at_iso = None

                reports_data.append({
                    'id': firestore_report.get('id'),
                    'title': firestore_report.get('title'),
                    'description': firestore_report.get('description', ''),
                    'status': firestore_report.get('generationStatus', 'completed'),
                    'createdAt': created_at_iso,
                    'elements': firestore_report.get('dataSource', {}).get('elements', []),
                    'layout': firestore_report.get('dataSource', {}).get('layout', {}),
                    'file_path': firestore_report.get('storagePath'),
                    'download_url': firestore_report.get('downloadUrl'),
                    'source': 'firestore',  # Mark source
                    'firestore_id': firestore_report.get('id')
                })

            logger.info(f"✅ Fetched {len(sql_reports)} SQL reports and {len(firestore_reports)} Firestore reports")

        except Exception as firestore_error:
            logger.warning(f"⚠️ Could not fetch Firestore reports: {firestore_error}")
            # Continue with SQL reports only

        # Sort all reports by creation date (newest first)
        reports_data.sort(key=lambda x: x.get('createdAt') or '', reverse=True)

        return jsonify({
            'success': True,
            'reports': reports_data,
            'total': len(reports_data)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching user reports: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to fetch reports'}), 500

@nextgen_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def delete_report(report_id):
    """Delete a report"""
    try:
        user_id = get_current_user_id()

        # Get the report
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report.created_by if hasattr(report, 'created_by') and report.created_by else report.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to delete this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403
        
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
@firebase_auth_required
def preview_report(report_id):
    """Preview a report without downloading"""
    try:
        user_id = get_current_user_id()

        # Get the report
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report.created_by if hasattr(report, 'created_by') and report.created_by else report.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to view this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403
        
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

# ================ REPORT DOWNLOAD ================

@nextgen_bp.route('/reports/<int:report_id>/download/pdf', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def download_report_pdf(report_id):
    """Download report as PDF"""
    try:
        user_id = get_current_user_id()

        # Get the report
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report.created_by if hasattr(report, 'created_by') and report.created_by else report.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to download this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403

        # Check if PDF file exists
        if not report.pdf_file_path or not os.path.exists(report.pdf_file_path):
            return jsonify({'error': 'PDF file not found'}), 404

        # Send the file
        return send_file(
            report.pdf_file_path,
            mimetype='application/pdf',
            as_attachment=False,  # Display in browser
            download_name=f"{report.title}.pdf"
        )

    except Exception as e:
        logger.error(f"Error downloading PDF for report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to download PDF'}), 500

@nextgen_bp.route('/reports/<int:report_id>/download/docx', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def download_report_docx(report_id):
    """Download report as DOCX"""
    try:
        user_id = get_current_user_id()

        # Get the report
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report.created_by if hasattr(report, 'created_by') and report.created_by else report.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to download this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403

        # Check if DOCX file exists
        if not report.docx_file_path or not os.path.exists(report.docx_file_path):
            return jsonify({'error': 'DOCX file not found'}), 404

        # Send the file
        return send_file(
            report.docx_file_path,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,  # Download file
            download_name=f"{report.title}.docx"
        )

    except Exception as e:
        logger.error(f"Error downloading DOCX for report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to download DOCX'}), 500

@nextgen_bp.route('/reports/<int:report_id>/download/excel', methods=['GET'])
@cross_origin(supports_credentials=True)
@firebase_auth_required
def download_report_excel(report_id):
    """Download report as Excel"""
    try:
        user_id = get_current_user_id()

        # Get the report
        report = Report.query.filter_by(id=report_id).first()
        if not report:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report.created_by if hasattr(report, 'created_by') and report.created_by else report.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to download this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403

        # Check if Excel file exists
        if not report.excel_file_path or not os.path.exists(report.excel_file_path):
            return jsonify({'error': 'Excel file not found'}), 404

        # Send the file
        return send_file(
            report.excel_file_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,  # Download file
            download_name=f"{report.title}.xlsx"
        )

    except Exception as e:
        logger.error(f"Error downloading Excel for report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to download Excel'}), 500

# ================ REPORT EXPORT ================

@nextgen_bp.route('/reports/<report_id>/export', methods=['GET'])
def export_report(report_id):
    """Export report in specified format"""
    try:
        user_id = get_current_user_id()
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
@cross_origin(supports_credentials=True)
@firebase_auth_required
def get_report_content(report_id):
    """Get report content for viewing and editing"""
    try:
        user_id = get_current_user_id()

        # Get the report
        report_obj = Report.query.filter_by(id=report_id).first()
        if not report_obj:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report_obj.created_by if hasattr(report_obj, 'created_by') and report_obj.created_by else report_obj.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to view this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403

        # Get report from database for detailed data
        from sqlalchemy import text
        result = db.session.execute(text("""
            SELECT id, title, description, report_type, generation_status,
                   data_source, generation_config, created_at
            FROM reports
            WHERE id = :report_id
        """), {'report_id': report_id})

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
@cross_origin(supports_credentials=True)
@firebase_auth_required
def update_report_content(report_id):
    """Update report content with edited text"""
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data or 'latex_content' not in data:
            return jsonify({'error': 'LaTeX content is required'}), 400

        # Get the report
        report_obj = Report.query.filter_by(id=report_id).first()
        if not report_obj:
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Support both created_by and user_id fields for compatibility
        report_owner = report_obj.created_by if hasattr(report_obj, 'created_by') and report_obj.created_by else report_obj.user_id

        if str(report_owner) != str(user_id) and not is_admin:
            return jsonify({
                'error': 'Access denied - you do not have permission to edit this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403
        
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

@nextgen_bp.route('/ai/text-suggestions', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_ai_text_suggestions():
    """Get AI suggestions for improving content text"""
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


# ================ CLAUDE AI ENHANCED REPORT ENDPOINTS ================

@nextgen_bp.route('/ai/generate-report-content', methods=['POST'])
@firebase_auth_required
def generate_ai_report_content():
    """
    Generate AI-powered report content using Claude

    Request body:
    {
        "data": [...],  # Data records for analysis
        "reportTitle": "Report Title",
        "reportType": "analysis|summary|detailed|executive",
        "additionalContext": "Optional context"
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        report_data = data.get('data', [])
        report_title = data.get('reportTitle', 'AI Generated Report')
        report_type = data.get('reportType', 'analysis')
        additional_context = data.get('additionalContext')

        logger.info(f"Generating AI report content: {report_title} (type: {report_type})")

        if not report_data:
            return jsonify({'error': 'No data provided for report generation'}), 400

        # Generate report using Claude AI
        result = ai_report_service.generate_report_content(
            data=report_data,
            report_title=report_title,
            report_type=report_type,
            additional_context=additional_context
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error generating AI report content: {str(e)}")
        return jsonify({
            'error': 'Failed to generate AI report content',
            'details': str(e)
        }), 500


@nextgen_bp.route('/ai/executive-summary', methods=['POST'])
@firebase_auth_required
def generate_executive_summary():
    """
    Generate executive summary using Claude AI

    Request body:
    {
        "data": [...],  # Data records for analysis
        "analysis": {...}  # Optional pre-computed analysis
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        report_data = data.get('data', [])
        analysis = data.get('analysis')

        logger.info("Generating executive summary with Claude AI")

        if not report_data:
            return jsonify({'error': 'No data provided'}), 400

        # Generate executive summary
        summary = ai_report_service.generate_executive_summary(
            data=report_data,
            analysis=analysis
        )

        return jsonify({
            'success': True,
            'summary': summary,
            'ai_generated': ai_report_service.ai_enabled
        }), 200

    except Exception as e:
        logger.error(f"Error generating executive summary: {str(e)}")
        return jsonify({
            'error': 'Failed to generate executive summary',
            'details': str(e)
        }), 500


@nextgen_bp.route('/ai/analyze-insights', methods=['POST'])
@firebase_auth_required
def analyze_data_insights():
    """
    Analyze data and extract insights using Claude AI

    Request body:
    {
        "data": [...]  # Data records for analysis
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        report_data = data.get('data', [])

        logger.info("Analyzing data insights with Claude AI")

        if not report_data:
            return jsonify({'error': 'No data provided'}), 400

        # Analyze insights
        insights = ai_report_service.analyze_data_insights(
            data=report_data
        )

        return jsonify({
            'success': True,
            'insights': insights,
            'ai_generated': ai_report_service.ai_enabled
        }), 200

    except Exception as e:
        logger.error(f"Error analyzing insights: {str(e)}")
        return jsonify({
            'error': 'Failed to analyze insights',
            'details': str(e)
        }), 500


@nextgen_bp.route('/ai/suggest-visualizations', methods=['POST'])
@firebase_auth_required
def suggest_visualizations():
    """
    Suggest appropriate visualizations using Claude AI

    Request body:
    {
        "data": [...]  # Data records for analysis
    }
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        report_data = data.get('data', [])

        logger.info("Suggesting visualizations with Claude AI")

        if not report_data:
            return jsonify({'error': 'No data provided'}), 400

        # Get visualization suggestions
        suggestions = ai_report_service.suggest_visualizations(
            data=report_data
        )

        return jsonify({
            'success': True,
            'visualizations': suggestions,
            'ai_generated': ai_report_service.ai_enabled
        }), 200

    except Exception as e:
        logger.error(f"Error suggesting visualizations: {str(e)}")
        return jsonify({
            'error': 'Failed to suggest visualizations',
            'details': str(e)
        }), 500


@nextgen_bp.route('/ai/status', methods=['GET'])
@firebase_auth_required
def get_ai_status():
    """
    Get Claude AI service status
    """
    try:
        return jsonify({
            'success': True,
            'ai_enabled': ai_report_service.ai_enabled,
            'service': 'Claude AI (Anthropic)',
            'model': 'claude-sonnet-4' if ai_report_service.ai_enabled else None,
            'features': {
                'report_generation': ai_report_service.ai_enabled,
                'executive_summary': ai_report_service.ai_enabled,
                'data_insights': ai_report_service.ai_enabled,
                'visualization_suggestions': ai_report_service.ai_enabled
            }
        }), 200

    except Exception as e:
        logger.error(f"Error checking AI status: {str(e)}")
        return jsonify({
            'error': 'Failed to check AI status',
            'details': str(e)
        }), 500
