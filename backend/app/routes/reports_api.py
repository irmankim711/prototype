"""
Reports API Routes
Handles report generation, preview, editing, and download functionality
"""

from flask import Blueprint, request, jsonify, send_file, current_app

# Rate limiting removed due to import issues
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
import logging
from typing import Dict, Any

from .. import db
from ..decorators import get_current_user_id, firebase_token_optional, firebase_auth_required
from ..models import Report, Form, FormSubmission, User, UserRole, ReportTemplate
from ..services.report_generation_service import report_generation_service
from ..services.excel_export_service import excel_export_service
from ..services.latex_conversion_service import latex_conversion_service
from ..services.report_lifecycle_service import report_lifecycle_service
from ..services.firestore_template_service import firestore_template_service
from ..tasks.enhanced_report_tasks import (
    generate_comprehensive_report_task,
    export_form_to_excel_task,
    auto_generate_form_report_task
)
from ..core.exceptions import ReportGenerationError
from ..decorators import require_role

logger = logging.getLogger(__name__)

def resolve_template_id(generation_config: Dict[str, Any]) -> int:
    """
    Resolve template_id from generation_config containing template_used or template_id
    Returns the actual database template_id (integer) or 1 as default
    """
    if not generation_config:
        return 1  # Default template
    
    # Check for template_used (like "Temp1")
    template_used = generation_config.get('template_used')
    if template_used:
        try:
            # Try to find template by name or placeholder_schema.template_identifier
            templates = ReportTemplate.query.filter_by(is_active=True).all()
            for template in templates:
                placeholder_schema = template.placeholder_schema or {}
                if (placeholder_schema.get('template_identifier') == template_used or
                    template.name.lower().replace(' ', '_') == template_used.lower()):
                    logger.info(f"Resolved template '{template_used}' to ID {template.id}")
                    return template.id
            
            # Fallback: try to find "Standard Business Report" for "Temp1"
            if template_used.lower() == 'temp1':
                standard_template = ReportTemplate.query.filter_by(name='Standard Business Report', is_active=True).first()
                if standard_template:
                    logger.info(f"Resolved 'Temp1' to Standard Business Report ID {standard_template.id}")
                    return standard_template.id
            
            logger.warning(f"Template '{template_used}' not found, using default ID 1")
        except Exception as e:
            logger.error(f"Error resolving template '{template_used}': {e}")
    
    # Check for template_uuid
    template_uuid = generation_config.get('template_uuid')
    if template_uuid:
        try:
            template = ReportTemplate.query.get(int(template_uuid))
            if template and template.is_active:
                return template.id
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid template_uuid '{template_uuid}': {e}")
    
    # Default fallback
    return 1

# Create blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('', methods=['GET'])
@reports_bp.route('/', methods=['GET'])
@firebase_token_optional
def get_all_reports():
    """
    Get all reports for the current user or all reports if no authentication
    GET /api/reports
    """
    try:
        user_id = get_current_user_id()

        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        report_type = request.args.get('report_type')

        # Build query - show all reports for now (demo mode)
        # In production, you would filter by user_id for authenticated users
        query = Report.query

        # Debug: Log what user_id we got
        logger.info(f"Reports query - user_id: {user_id}, showing all reports")
        
        if status:
            query = query.filter_by(status=status)
        if report_type:
            query = query.filter_by(report_type=report_type)
        
        # Order by most recent first
        query = query.order_by(Report.created_at.desc())
        
        # Paginate
        reports = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Convert to dict
        reports_data = []
        for report in reports.items:
            try:
                report_dict = report.to_dict() if hasattr(report, 'to_dict') else {
                    'id': report.id,
                    'uuid': str(report.id),  # Use ID as uuid fallback
                    'title': report.title,
                    'description': report.description,
                    'status': getattr(report, 'generation_status', 'unknown'),
                    'report_type': report.report_type,
                    'file_path': report.file_path,
                    'file_format': report.file_format,
                    'created_at': report.created_at.isoformat() if report.created_at else None,
                    'updated_at': report.created_at.isoformat() if report.created_at else None,
                    'download_count': report.download_count or 0
                }
                reports_data.append(report_dict)
            except Exception as e:
                logger.error(f"Error serializing report {report.id}: {str(e)}")
                # Skip this report if it can't be serialized
                continue
        
        return jsonify({
            'success': True,
            'reports': reports_data,
            'pagination': {
                'page': reports.page,
                'pages': reports.pages,
                'per_page': reports.per_page,
                'total': reports.total,
                'has_next': reports.has_next,
                'has_prev': reports.has_prev
            },
            'total': reports.total
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch reports: {str(e)}'
        }), 500

@reports_bp.route('/generate', methods=['POST'])
def generate_report():
    """
    Generate a comprehensive report (PDF, DOCX, Excel)
    POST /api/reports/generate
    """
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['title', 'data', 'config']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Resolve template_id from generation_config
        template_id = resolve_template_id(data['config'])

        # Get template file path and add to config
        # Priority 1: Try to get latest template from Firestore
        firestore_template = firestore_template_service.get_latest_puncak_alam_template()
        if firestore_template:
            template_file_path = firestore_template_service.get_template_file_path(firestore_template['id'])
            if template_file_path and os.path.exists(template_file_path):
                data['config']['docx_template_path'] = template_file_path
                data['config']['firestore_template_id'] = firestore_template['id']
                logger.info(f"✅ Using latest Firestore template: {firestore_template.get('name')} (v{firestore_template.get('version')})")
                logger.info(f"   File path: {template_file_path}")

                # Increment usage count
                firestore_template_service.increment_usage_count(firestore_template['id'])
            else:
                logger.warning(f"⚠️ Firestore template file not found, falling back to database")

        # Priority 2: Check database (SQL/Supabase)
        if 'docx_template_path' not in data['config']:
            template_record = ReportTemplate.query.get(template_id)
            if template_record and template_record.file_path and os.path.exists(template_record.file_path):
                data['config']['docx_template_path'] = template_record.file_path
                logger.info(f"Using database template file: {template_record.file_path}")

        # Priority 3: Fallback to filesystem
        if 'docx_template_path' not in data['config']:
            templates_dir = os.path.join(current_app.root_path, '..', 'templates', 'report_templates')
            template_files = [
                '04- LAPORAN FU _ PUNCAK ALAM (1).docx',  # Primary template
                '04- LAPORAN FU _ PUNCAK ALAM_final.docx'  # Fallback
            ]
            for template_file in template_files:
                template_path = os.path.join(templates_dir, template_file)
                if os.path.exists(template_path):
                    data['config']['docx_template_path'] = template_path
                    logger.info(f"Using filesystem template: {template_path}")
                    break

        # Prepare data for template placeholders
        # Extract data from data_source and format for template
        template_data = {}
        if isinstance(data.get('data'), dict):
            template_data = data['data']

        # Add common fields with defaults
        template_data.setdefault('tarikh', data.get('tarikh', ''))
        template_data.setdefault('lokasi', data.get('lokasi', ''))
        template_data.setdefault('perunding', data.get('perunding', ''))
        template_data.setdefault('anjuran', data.get('anjuran', ''))

        # Store formatted data for template rendering
        data['config']['template_data'] = template_data

        # Create report record with proper UUID format
        import uuid
        report = Report(
            id=str(uuid.uuid4()),
            title=data['title'],
            description=data.get('description', ''),
            report_type=data.get('report_type', 'custom'),
            status='pending',
            generation_status='pending',
            template_id=str(template_id),
            program_id=1,  # Default program
            generation_config=data['config'],
            data_source=data['data'],
            user_id=user_id,  # This sets created_by via the property setter
            organization_id=None,  # Set to None to avoid foreign key constraint
            download_count=0,
            view_count=0
        )
        
        try:
            db.session.add(report)
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            logger.error(f"Database error creating report: {str(db_error)}")
            return jsonify({
                'success': False,
                'error': f'Failed to create report in database: {str(db_error)}'
            }), 500
        
        # Start background report generation
        generate_comprehensive_report_task.delay(report.id, data['data'], data['config'])
        
        logger.info(f"Report generation initiated for user {user_id}, report {report.id}")
        
        return jsonify({
            'success': True,
            'message': 'Report generation started',
            'reportId': report.id,  # Frontend expects reportId
            'reportTitle': report.title,  # Frontend expects reportTitle
            'reportType': report.report_type,  # Frontend expects reportType
            'report_id': report.id,  # Keep for backward compatibility
            'status': 'pending',
            'download_urls': {
                'pdf': f"/api/reports/{report.id}/download/pdf",
                'docx': f"/api/reports/{report.id}/download/docx",
                'excel': f"/api/reports/{report.id}/download/excel"
            }
        }), 202
        
    except Exception as e:
        logger.error(f"Error in report generation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start report generation: {str(e)}'
        }), 500

@reports_bp.route('/generate/latex', methods=['POST'])
def generate_latex_report():
    """
    Generate a report from LaTeX template with automatic conversion to PDF/DOCX
    POST /api/reports/generate/latex
    """
    try:
        user_id = get_current_user_id()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['title', 'latex_file_path', 'config']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate LaTeX file exists
        latex_file_path = data['latex_file_path']
        if not os.path.exists(latex_file_path):
            return jsonify({'error': 'LaTeX file not found'}), 404
        
        # Resolve template_id from generation_config
        template_id = resolve_template_id(data['config'])
        
        # Create report record
        report = Report(
            title=data['title'],
            description=data.get('description', ''),
            report_type='latex_based',
            generation_status='pending',
            template_id=template_id,
            program_id=1,  # Default program
            generation_config=data['config'],
            data_source=data.get('data', {})
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Start background LaTeX-based report generation
        generate_comprehensive_report_task.delay(report.id, data.get('data', {}), data['config'])
        
        logger.info(f"LaTeX-based report generation initiated for user {user_id}, report {report.id}")
        
        return jsonify({
            'success': True,
            'message': 'LaTeX-based report generation started',
            'report_id': report.id,
            'status': 'pending',
            'latex_source': latex_file_path,
            'download_urls': {
                'pdf': f"/api/reports/{report.id}/download/pdf",
                'docx': f"/api/reports/{report.id}/download/docx",
                'excel': f"/api/reports/{report.id}/download/excel"
            }
        }), 202
        
    except Exception as e:
        logger.error(f"Error in LaTeX report generation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start LaTeX report generation: {str(e)}'
        }), 500

@reports_bp.route('/upload/file', methods=['POST'])
def upload_file_for_report():
    """Upload a file for report generation (DOCX, DOC, etc.)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        allowed_extensions = {'.docx', '.doc', '.pdf', '.txt'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'File type {file_ext} not allowed. Supported: {", ".join(allowed_extensions)}'}), 400
        
        # Generate unique filename
        original_filename = file.filename # Use original filename for display
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'reports')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Return file information
        return jsonify({
            'success': True,
            'file_path': file_path,
            'filename': unique_filename,
            'original_filename': original_filename,
            'file_size': file_size,
            'mime_type': file.mimetype,
            'message': 'File uploaded successfully for report generation'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error uploading file for report: {str(e)}")
        return jsonify({
            'error': 'Failed to upload file',
            'details': str(e)
        }), 500

@reports_bp.route('/<int:report_id>/status', methods=['GET'])
def get_report_status(report_id):
    """
    Get report generation status
    GET /api/reports/{report_id}/status
    """
    try:
        user_id = get_current_user_id()

        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Convert both to string for comparison to handle type mismatches
        if str(report.user_id) != str(user_id) and not is_admin:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({
            'success': True,
            'report': report.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting report status {report_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get report status: {str(e)}'
        }), 500

@reports_bp.route('/<int:report_id>/preview', methods=['GET'])
@firebase_auth_required
def preview_report(report_id):
    """
    Enhanced preview generated report with file information and download links
    GET /api/reports/{report_id}/preview
    """
    try:
        user_id = get_current_user_id()

        # Ensure user is authenticated (should not be None due to @firebase_auth_required)
        if user_id is None:
            logger.warning(f"Preview request for report {report_id} - user_id is None despite authentication decorator")
            return jsonify({
                'error': 'Authentication required',
                'code': 'UNAUTHORIZED'
            }), 401

        # Get report
        report = Report.query.get(report_id)
        if not report:
            logger.warning(f"Preview request for report {report_id} - report not found")
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Get report owner - handle both created_by and user_id properties
        report_owner_id = report.user_id  # This uses the property that extracts from created_by
        report_created_by = report.created_by  # Direct field access

        # Log authorization attempt for debugging
        logger.info(f"Preview authorization check - user_id: {user_id}, report_owner_id: {report_owner_id}, "
                   f"report_created_by: {report_created_by}, is_admin: {is_admin}")

        # Check authorization: user must own the report OR be an admin
        # Handle None values properly
        user_owns_report = False
        if report_owner_id is not None and user_id is not None:
            # Both are not None, compare them
            user_owns_report = str(report_owner_id) == str(user_id)
        elif report_created_by is not None and user_id is not None:
            # Fallback: check created_by directly if user_id property returned None
            # created_by might be a string representation of user_id
            try:
                # Try to convert created_by to int for comparison
                created_by_int = int(report_created_by) if report_created_by.isdigit() else None
                if created_by_int is not None:
                    user_owns_report = created_by_int == int(user_id)
            except (ValueError, TypeError):
                # If conversion fails, compare as strings
                user_owns_report = str(report_created_by) == str(user_id)

        if not user_owns_report and not is_admin:
            logger.warning(f"Access denied for user {user_id} attempting to preview report {report_id} "
                          f"(owned by {report_owner_id or report_created_by})")
            return jsonify({
                'error': 'Access denied - you do not have permission to view this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403
        
        # Check if report is ready
        if report.status != 'completed':
            return jsonify({
                'success': False,
                'error': 'Report not ready for preview',
                'status': report.status,
                'progress': report.generation_progress
            }), 400
        
        # Return enhanced preview data using actual model fields
        preview_data = {
            'report_id': report.id,
            'title': report.title,
            'description': report.description,
            'report_type': report.report_type,
            'generation_status': report.generation_status,
            'status': report.status,  # Computed property
            'generated_at': report.generated_at.isoformat() if report.generated_at else None,
            'file_path': report.file_path,
            'file_size': report.file_size,
            'file_format': report.file_format,
            'download_url': report.download_url,
            'download_count': report.download_count,
            'last_downloaded': report.last_downloaded.isoformat() if report.last_downloaded else None,
            'data_source': report.data_source,
            'generation_config': report.generation_config,
            'error_message': report.error_message,
            'completeness_score': report.completeness_score,
            'processing_notes': report.processing_notes,
            'created_by': report.created_by,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'storage_info': {
                'total_size_mb': round(report.file_size / (1024 * 1024), 2) if report.file_size else 0
            }
        }

        # Return response with both top-level fields for frontend compatibility
        # and nested preview data for backward compatibility
        return jsonify({
            'success': True,
            'reportId': report.id,           # Frontend expects reportId at top level
            'reportTitle': report.title,     # Frontend expects reportTitle at top level
            'reportType': report.report_type, # Frontend expects reportType at top level
            'id': report.id,                 # Also include id for consistency
            'title': report.title,           # Also include title for consistency
            'preview': preview_data          # Keep nested structure for backward compatibility
        }), 200
        
    except Exception as e:
        logger.error(f"Error previewing report {report_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to preview report: {str(e)}'
        }), 500

@reports_bp.route('/<int:report_id>/edit', methods=['PUT'])
def edit_report(report_id):
    """
    Edit report data and regenerate
    PUT /api/reports/{report_id}/edit
    """
    try:
        user_id = get_current_user_id()

        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Convert both to string for comparison to handle type mismatches
        if str(report.user_id) != str(user_id) and not is_admin:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get updated data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update report data
        if 'title' in data:
            report.title = data['title']
        if 'description' in data:
            report.description = data['description']
        if 'data_source' in data:
            report.data_source = data['data_source']
        if 'generation_config' in data:
            report.generation_config = data['generation_config']

        # Reset status for regeneration
        report.status = 'pending'
        report.generated_at = None
        report.generation_time_seconds = None
        report.error_message = None

        # Clear old file references (use actual database fields)
        report.file_path = None
        report.file_size = None
        report.file_format = None
        
        db.session.commit()
        
        # Start regeneration
        generate_comprehensive_report_task.delay(report.id, report.data_source, report.generation_config)
        
        logger.info(f"Report {report_id} edited and regeneration started")
        
        return jsonify({
            'success': True,
            'message': 'Report updated and regeneration started',
            'report_id': report.id,
            'status': 'pending'
        }), 200
        
    except Exception as e:
        logger.error(f"Error editing report {report_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to edit report: {str(e)}'
        }), 500

@reports_bp.route('/<int:report_id>/convert/latex', methods=['POST'])
def convert_latex_report(report_id):
    """
    Convert existing LaTeX file to PDF/DOCX for a report
    POST /api/reports/{report_id}/convert/latex
    """
    try:
        user_id = get_current_user_id()

        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Convert both to string for comparison to handle type mismatches
        if str(report.user_id) != str(user_id) and not is_admin:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get LaTeX file path from request
        data = request.get_json()
        if not data or 'latex_file_path' not in data:
            return jsonify({'error': 'LaTeX file path required'}), 400
        
        latex_file_path = data['latex_file_path']
        if not os.path.exists(latex_file_path):
            return jsonify({'error': 'LaTeX file not found'}), 404
        
        # Update report status
        report.update_status('generating')
        db.session.commit()

        try:
            # Convert LaTeX to PDF
            pdf_filename = f"{os.path.splitext(os.path.basename(latex_file_path))[0]}.pdf"
            pdf_path, pdf_size = latex_conversion_service.convert_latex_to_pdf(
                latex_file_path, pdf_filename
            )

            # Convert LaTeX to DOCX
            docx_filename = f"{os.path.splitext(os.path.basename(latex_file_path))[0]}.docx"
            docx_path, docx_size = latex_conversion_service.convert_latex_to_docx(
                latex_file_path, docx_filename
            )

            # Update report with new files (store primary format in file_path)
            report.file_path = pdf_path  # Store PDF as primary
            report.file_size = pdf_size
            report.file_format = 'pdf'

            # Generate download URLs
            base_url = data.get('base_url', 'http://localhost:5000')
            report.download_url = f"{base_url}/api/reports/{report_id}/download/pdf"

            # Mark as completed
            report.update_status('completed')
            db.session.commit()

            logger.info(f"LaTeX conversion completed for report {report_id}")

            return jsonify({
                'success': True,
                'message': 'LaTeX conversion completed successfully',
                'report_id': report_id,
                'pdf_file_path': pdf_path,
                'docx_file_path': docx_path,
                'file_sizes': {
                    'pdf': pdf_size,
                    'docx': docx_size
                },
                'download_urls': {
                    'pdf': f"{base_url}/api/reports/{report_id}/download/pdf",
                    'docx': f"{base_url}/api/reports/{report_id}/download/docx"
                }
            }), 200
            
        except Exception as e:
            report.update_status('failed', error_message=str(e))
            db.session.commit()
            raise e
        
    except Exception as e:
        logger.error(f"Error converting LaTeX for report {report_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to convert LaTeX: {str(e)}'
        }), 500

@reports_bp.route('/<int:report_id>/download/<file_type>', methods=['GET'])
@firebase_auth_required
def download_report(report_id, file_type):
    """
    Download generated report file
    GET /api/reports/{report_id}/download/{file_type}

    Uses the generic file_path field and constructs format-specific paths
    based on the requested file_type since the Report model uses a single
    file_path field rather than format-specific fields.
    """
    try:
        user_id = get_current_user_id()

        # Ensure user is authenticated (should not be None due to @firebase_auth_required)
        if user_id is None:
            logger.warning(f"Download request for report {report_id} - user_id is None despite authentication decorator")
            return jsonify({
                'error': 'Authentication required',
                'code': 'UNAUTHORIZED'
            }), 401

        # Get report
        report = Report.query.get(report_id)
        if not report:
            logger.warning(f"Download request for report {report_id} - report not found")
            return jsonify({
                'error': 'Report not found',
                'code': 'NOT_FOUND'
            }), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Get report owner - handle both created_by and user_id properties
        report_owner_id = report.user_id  # This uses the property that extracts from created_by
        report_created_by = report.created_by  # Direct field access

        # Check authorization: user must own the report OR be an admin
        # Handle None values properly
        user_owns_report = False
        if report_owner_id is not None and user_id is not None:
            # Both are not None, compare them
            user_owns_report = str(report_owner_id) == str(user_id)
        elif report_created_by is not None and user_id is not None:
            # Fallback: check created_by directly if user_id property returned None
            # created_by might be a string representation of user_id
            try:
                # Try to convert created_by to int for comparison
                created_by_int = int(report_created_by) if report_created_by.isdigit() else None
                if created_by_int is not None:
                    user_owns_report = created_by_int == int(user_id)
            except (ValueError, TypeError):
                # If conversion fails, compare as strings
                user_owns_report = str(report_created_by) == str(user_id)

        if not user_owns_report and not is_admin:
            logger.warning(f"Access denied for user {user_id} attempting to download report {report_id} "
                          f"(owned by {report_owner_id or report_created_by})")
            return jsonify({
                'error': 'Access denied - you do not have permission to download this report',
                'code': 'INSUFFICIENT_PERMISSIONS'
            }), 403

        # Check if report is ready
        if report.status != 'completed':
            return jsonify({
                'success': False,
                'error': 'Report not ready for download',
                'status': report.status
            }), 400

        # Validate file type
        valid_types = ['pdf', 'docx', 'excel']
        if file_type not in valid_types:
            return jsonify({'error': f'Invalid file type. Must be one of: {", ".join(valid_types)}'}), 400

        # Construct file path based on type
        # The service stores files with different extensions but in the same directory
        file_path = None
        filename = None

        if report.file_path:
            # Get the base path and directory
            base_path_without_ext = os.path.splitext(report.file_path)[0]
            report_dir = os.path.dirname(report.file_path)

            # Map file type to extension
            extension_map = {
                'pdf': 'pdf',
                'docx': 'docx',
                'excel': 'xlsx'
            }

            # Try to find the file with the requested extension
            extension = extension_map[file_type]
            file_path = f"{base_path_without_ext}.{extension}"
            filename = f"{report.title.replace(' ', '_')}.{extension}"

            # If the constructed path doesn't exist, try looking in the same directory
            if not os.path.exists(file_path):
                # Try alternative naming pattern (report might have been saved with different naming)
                import glob
                pattern = os.path.join(report_dir, f"*{report.id}*.{extension}")
                matches = glob.glob(pattern)
                if matches:
                    file_path = matches[0]
                else:
                    # Try another pattern based on report title
                    safe_title = report.title.replace(' ', '_')
                    pattern = os.path.join(report_dir, f"*{safe_title}*.{extension}")
                    matches = glob.glob(pattern)
                    if matches:
                        file_path = matches[0]

        if not file_path or not os.path.exists(file_path):
            logger.error(f"File not found for report {report_id} type {file_type}. Checked path: {file_path}")
            return jsonify({
                'error': 'File not found',
                'details': f'The {file_type} file for this report is not available. It may not have been generated yet.',
                'report_status': report.status,
                'file_format': report.file_format
            }), 404

        # Update download tracking
        report.download_count = (report.download_count or 0) + 1
        report.last_downloaded = datetime.utcnow()
        db.session.commit()

        logger.info(f"Serving file {file_path} for report {report_id} type {file_type}")

        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        logger.error(f"Error downloading report {report_id} {file_type}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Failed to download report: {str(e)}'
        }), 500

@reports_bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """
    Get a single report by ID
    GET /api/reports/{report_id}
    """
    try:
        user_id = get_current_user_id()

        # Get report with user info
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # If user is authenticated, check access - allow if user owns the report OR user is admin
        if user_id is not None:
            user = User.query.get(user_id)
            is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

            # Convert both to string for comparison to handle type mismatches
            if str(report.user_id) != str(user_id) and not is_admin:
                return jsonify({'error': 'Access denied'}), 403
        else:
            # Unauthenticated users cannot access reports
            logger.warning(f"Unauthenticated user attempted to access report {report_id}")
            return jsonify({
                'error': 'Authentication required',
                'code': 'UNAUTHORIZED'
            }), 401

        # Convert to dictionary using the model's to_dict method or fallback
        report_data = report.to_dict() if hasattr(report, 'to_dict') else {
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'status': report.status,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'user_id': report.user_id,
            'file_path': report.file_path,
            'file_format': report.file_format,
            'file_size': report.file_size,
            'template_id': report.template_id,
            'download_url': report.download_url
        }

        logger.info(f"Report {report_id} retrieved successfully")
        return jsonify({
            'success': True,
            'report': report_data
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve report: {str(e)}'
        }), 500

@reports_bp.route('/<int:report_id>', methods=['DELETE'])
@firebase_auth_required
def delete_report(report_id):
    """
    Delete a report and its files
    DELETE /api/reports/{report_id}
    """
    try:
        user_id = get_current_user_id()

        # Authentication is guaranteed by @firebase_auth_required decorator
        # This check provides an additional safety layer
        if user_id is None:
            logger.error(f"Authentication failed for delete_report {report_id} - user_id is None despite decorator")
            return jsonify({
                'error': 'Authentication required',
                'code': 'UNAUTHORIZED'
            }), 401

        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Check access - allow if user owns the report OR user is admin
        user = User.query.get(user_id)
        is_admin = user and user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

        # Convert both to string for comparison to handle type mismatches
        if str(report.user_id) != str(user_id) and not is_admin:
            logger.warning(f"User {user_id} (admin={is_admin}) attempted to delete report {report_id} owned by user {report.user_id}")
            return jsonify({'error': 'Access denied - you can only delete your own reports'}), 403

        # Remove files - try all possible formats based on the base file_path
        if report.file_path:
            base_path_without_ext = os.path.splitext(report.file_path)[0]
            report_dir = os.path.dirname(report.file_path)

            # Try to delete all format variants
            for ext in ['pdf', 'docx', 'xlsx']:
                file_path = f"{base_path_without_ext}.{ext}"
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove file {file_path}: {str(e)}")

            # Also try to find files using glob patterns
            import glob
            patterns = [
                os.path.join(report_dir, f"*{report.id}*"),
                os.path.join(report_dir, f"*{report.title.replace(' ', '_')}*")
            ]
            for pattern in patterns:
                for file_path in glob.glob(pattern):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove file {file_path}: {str(e)}")
        
        # Delete from database
        db.session.delete(report)
        db.session.commit()
        
        logger.info(f"Report {report_id} deleted successfully")
        
        return jsonify({
            'success': True,
            'message': 'Report deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete report: {str(e)}'
        }), 500

@reports_bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_reports(user_id):
    """
    Get all reports for a user
    GET /api/reports/user/{user_id}
    """
    try:
        current_user_id = get_current_user_id()

        # Check access - convert both to string for comparison to handle type mismatches
        if str(current_user_id) != str(user_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get reports
        reports = Report.query.filter_by(user_id=user_id).order_by(Report.created_at.desc()).all()
        
        reports_data = [report.to_dict() for report in reports]
        
        return jsonify({
            'success': True,
            'reports': reports_data,
            'total': len(reports_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting reports for user {user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get reports: {str(e)}'
        }), 500

@reports_bp.route('/auto-generate/<int:form_id>', methods=['POST'])
@require_role([UserRole.ADMIN, UserRole.USER])
def trigger_auto_report_generation(form_id):
    """
    Manually trigger auto-report generation for a form
    POST /api/reports/auto-generate/{form_id}
    """
    try:
        user_id = get_current_user_id()
        
        # Check if form exists
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        # Start auto-report generation
        result = auto_generate_form_report_task.delay(form_id)
        
        logger.info(f"Auto-report generation triggered for form {form_id} by user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Auto-report generation triggered',
            'form_id': form_id,
            'task_id': result.id
        }), 202
        
    except Exception as e:
        logger.error(f"Error triggering auto-report generation for form {form_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to trigger auto-report generation: {str(e)}'
        }), 500

@reports_bp.route('/lifecycle/cleanup', methods=['POST'])
@require_role([UserRole.ADMIN, UserRole.USER])
def cleanup_reports():
    """
    Manually trigger report cleanup
    POST /api/reports/lifecycle/cleanup
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json() or {}
        force = data.get('force', False)
        
        # Perform cleanup
        result = report_lifecycle_service.cleanup_expired_reports(force=force)
        
        logger.info(f"Report cleanup triggered by user {user_id}: {result}")
        
        return jsonify({
            'success': True,
            'message': 'Report cleanup completed',
            'result': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error during report cleanup: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to cleanup reports: {str(e)}'
        }), 500

@reports_bp.route('/lifecycle/storage', methods=['GET'])
@firebase_token_optional
def get_storage_usage():
    """
    Get storage usage statistics
    GET /api/reports/lifecycle/storage
    """
    try:
        user_id = get_current_user_id()

        # Get storage usage
        usage = report_lifecycle_service.get_storage_usage()

        logger.info(f"Storage usage requested by user {user_id or 'anonymous'}")
        
        return jsonify({
            'success': True,
            'storage_usage': usage
        }), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error getting storage usage: {str(e)}")
        logger.error(f"Full stack trace: {error_details}")
        print("STORAGE USAGE ERROR:", str(e))
        print("FULL STACK TRACE:", error_details)
        return jsonify({
            'success': False,
            'error': f'Failed to get storage usage: {str(e)}',
            'details': error_details,  # Include full stack trace for debugging
            'error_type': type(e).__name__
        }), 500

@reports_bp.route('/lifecycle/retention', methods=['PUT'])
@require_role([UserRole.ADMIN])
def update_retention_policy():
    """
    Update retention policy
    PUT /api/reports/lifecycle/retention
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data or 'retention_days' not in data:
            return jsonify({'error': 'Retention days required'}), 400
        
        retention_days = data['retention_days']
        if not isinstance(retention_days, int) or retention_days < 1:
            return jsonify({'error': 'Retention days must be a positive integer'}), 400
        
        # Update retention policy
        report_lifecycle_service.update_retention_policy(retention_days)
        
        logger.info(f"Retention policy updated to {retention_days} days by user {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Retention policy updated to {retention_days} days',
            'retention_days': retention_days
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating retention policy: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to update retention policy: {str(e)}'
        }), 500

@reports_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for reports service
    GET /api/reports/health
    """
    try:
        # Basic health check
        health_status = {
            'service': 'reports',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'service': 'reports',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
