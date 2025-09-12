"""
Reports API Routes
Handles report generation, preview, editing, and download functionality
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
# Rate limiting removed due to import issues
from datetime import datetime
import os
import uuid
from werkzeug.utils import secure_filename
import logging
from typing import Dict, Any

from .. import db
from ..models import Report, Form, FormSubmission, User, UserRole, ReportTemplate
from ..services.report_generation_service import report_generation_service
from ..services.excel_export_service import excel_export_service
from ..services.latex_conversion_service import latex_conversion_service
from ..services.report_lifecycle_service import report_lifecycle_service
from ..tasks.enhanced_report_tasks import (
    generate_comprehensive_report_task,
    export_form_to_excel_task,
    auto_generate_form_report_task
)
from ..core.exceptions import ReportGenerationError
from ..decorators import require_role
from ..core.auth import require_permission, Permission

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
@jwt_required()
def get_all_reports():
    """
    Get all reports for the current user
    GET /api/reports
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        report_type = request.args.get('report_type')
        
        # Build query
        query = Report.query.filter_by(user_id=user_id)
        
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
            report_dict = report.to_dict() if hasattr(report, 'to_dict') else {
                'id': report.id,
                'uuid': report.uuid,
                'title': report.title,
                'description': report.description,
                'status': report.status,
                'report_type': report.report_type,
                'file_path': report.file_path,
                'file_format': report.file_format,
                'created_at': report.created_at.isoformat(),
                'updated_at': report.updated_at.isoformat(),
                'download_count': report.download_count
            }
            reports_data.append(report_dict)
        
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
@jwt_required()
def generate_report():
    """
    Generate a comprehensive report (PDF, DOCX, Excel)
    POST /api/reports/generate
    """
    try:
        user_id = get_jwt_identity()
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
            user_id=user_id,
            organization_id=None,  # Set to None to avoid foreign key constraint
            created_by=None,  # Set to None to avoid foreign key constraint - in production, use authenticated user's UUID
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
@jwt_required()
def generate_latex_report():
    """
    Generate a report from LaTeX template with automatic conversion to PDF/DOCX
    POST /api/reports/generate/latex
    """
    try:
        user_id = get_jwt_identity()
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
@jwt_required()
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
@jwt_required()
def get_report_status(report_id):
    """
    Get report generation status
    GET /api/reports/{report_id}/status
    """
    try:
        user_id = get_jwt_identity()
        
        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check access
        if report.user_id != user_id:
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
@jwt_required()
def preview_report(report_id):
    """
    Enhanced preview generated report with file information and download links
    GET /api/reports/{report_id}/preview
    """
    try:
        user_id = get_jwt_identity()
        
        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check access
        if report.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if report is ready
        if report.status != 'completed':
            return jsonify({
                'success': False,
                'error': 'Report not ready for preview',
                'status': report.status,
                'progress': report.generation_progress
            }), 400
        
        # Return enhanced preview data
        preview_data = {
            'report_id': report.id,
            'title': report.title,
            'description': report.description,
            'report_type': report.report_type,
            'generated_at': report.generation_completed_at.isoformat() if report.generation_completed_at else None,
            'file_sizes': {
                'pdf': report.pdf_file_size,
                'docx': report.docx_file_size,
                'excel': report.excel_file_size
            },
            'download_urls': {
                'pdf': report.pdf_download_url,
                'docx': report.docx_download_url,
                'excel': report.excel_download_url
            },
            'file_paths': {
                'pdf': report.pdf_file_path,
                'docx': report.docx_file_path,
                'excel': report.excel_file_path
            },
            'generated_data': report.generated_data,
            'report_config': report.report_config,
            'storage_info': {
                'total_size_mb': round(sum(filter(None, [report.pdf_file_size, report.docx_file_size, report.excel_file_size])) / (1024 * 1024), 2) if any([report.pdf_file_size, report.docx_file_size, report.excel_file_size]) else 0
            }
        }
        
        return jsonify({
            'success': True,
            'preview': preview_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error previewing report {report_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to preview report: {str(e)}'
        }), 500

@reports_bp.route('/<int:report_id>/edit', methods=['PUT'])
@jwt_required()
def edit_report(report_id):
    """
    Edit report data and regenerate
    PUT /api/reports/{report_id}/edit
    """
    try:
        user_id = get_jwt_identity()
        
        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check access
        if report.user_id != user_id:
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
        if 'generated_data' in data:
            report.generated_data = data['generated_data']
        if 'report_config' in data:
            report.report_config = data['report_config']
        
        # Reset status for regeneration
        report.status = 'pending'
        report.generation_progress = 0
        report.generation_started_at = None
        report.generation_completed_at = None
        report.generation_duration = None
        report.error_message = None
        
        # Clear old file references
        report.pdf_file_path = None
        report.docx_file_path = None
        report.excel_file_path = None
        report.pdf_file_size = None
        report.docx_file_size = None
        report.excel_file_size = None
        
        db.session.commit()
        
        # Start regeneration
        generate_comprehensive_report_task.delay(report.id, report.generated_data, report.report_config)
        
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
@jwt_required()
def convert_latex_report(report_id):
    """
    Convert existing LaTeX file to PDF/DOCX for a report
    POST /api/reports/{report_id}/convert/latex
    """
    try:
        user_id = get_jwt_identity()
        
        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check access
        if report.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get LaTeX file path from request
        data = request.get_json()
        if not data or 'latex_file_path' not in data:
            return jsonify({'error': 'LaTeX file path required'}), 400
        
        latex_file_path = data['latex_file_path']
        if not os.path.exists(latex_file_path):
            return jsonify({'error': 'LaTeX file not found'}), 404
        
        # Update report status
        report.update_status('generating', progress=10)
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
            
            # Update report with new files
            report.pdf_file_path = pdf_path
            report.docx_file_path = docx_path
            report.pdf_file_size = pdf_size
            report.docx_file_size = docx_size
            
            # Generate download URLs
            base_url = data.get('base_url', 'http://localhost:5000')
            report.pdf_download_url = f"{base_url}/api/reports/{report_id}/download/pdf"
            report.docx_download_url = f"{base_url}/api/reports/{report_id}/download/docx"
            
            # Mark as completed
            report.update_status('completed', progress=100)
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
                    'pdf': report.pdf_download_url,
                    'docx': report.docx_download_url
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
@jwt_required()
def download_report(report_id, file_type):
    """
    Download generated report file
    GET /api/reports/{report_id}/download/{file_type}
    """
    try:
        user_id = get_jwt_identity()
        
        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check access
        if report.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if report is ready
        if report.status != 'completed':
            return jsonify({
                'success': False,
                'error': 'Report not ready for download',
                'status': report.status
            }), 400
        
        # Get file path based on type
        file_path = None
        filename = None
        
        if file_type == 'pdf':
            file_path = report.pdf_file_path
            filename = f"{report.title.replace(' ', '_')}.pdf"
        elif file_type == 'docx':
            file_path = report.docx_file_path
            filename = f"{report.title.replace(' ', '_')}.docx"
        elif file_type == 'excel':
            file_path = report.excel_file_path
            filename = f"{report.title.replace(' ', '_')}.xlsx"
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error downloading report {report_id} {file_type}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to download report: {str(e)}'
        }), 500

@reports_bp.route('/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """
    Get a single report by ID
    GET /api/reports/{report_id}
    """
    try:
        user_id = get_jwt_identity()

        # Get report with user info
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Check access
        if report.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403

        # Convert to dictionary
        report_data = report.to_dict() if hasattr(report, 'to_dict') else {
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'status': report.status,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None,
            'user_id': report.user_id,
            'form_id': report.form_id,
            'pdf_file_path': report.pdf_file_path,
            'docx_file_path': report.docx_file_path,
            'excel_file_path': report.excel_file_path,
            'template_id': report.template_id
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
@jwt_required()
def delete_report(report_id):
    """
    Delete a report and its files
    DELETE /api/reports/{report_id}
    """
    try:
        user_id = get_jwt_identity()
        
        # Get report
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Check access
        if report.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Remove files
        for file_path in [report.pdf_file_path, report.docx_file_path, report.excel_file_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
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
@jwt_required()
def get_user_reports(user_id):
    """
    Get all reports for a user
    GET /api/reports/user/{user_id}
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Check access
        if current_user_id != user_id:
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
@jwt_required()
@require_role([UserRole.ADMIN, UserRole.USER])
def trigger_auto_report_generation(form_id):
    """
    Manually trigger auto-report generation for a form
    POST /api/reports/auto-generate/{form_id}
    """
    try:
        user_id = get_jwt_identity()
        
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
@jwt_required()
@require_role([UserRole.ADMIN, UserRole.USER])
def cleanup_reports():
    """
    Manually trigger report cleanup
    POST /api/reports/lifecycle/cleanup
    """
    try:
        user_id = get_jwt_identity()
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
@jwt_required()
@require_role([UserRole.ADMIN, UserRole.USER])
def get_storage_usage():
    """
    Get storage usage statistics
    GET /api/reports/lifecycle/storage
    """
    try:
        user_id = get_jwt_identity()
        
        # Get storage usage
        usage = report_lifecycle_service.get_storage_usage()
        
        logger.info(f"Storage usage requested by user {user_id}")
        
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
@jwt_required()
@require_role([UserRole.ADMIN])
def update_retention_policy():
    """
    Update retention policy
    PUT /api/reports/lifecycle/retention
    """
    try:
        user_id = get_jwt_identity()
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
