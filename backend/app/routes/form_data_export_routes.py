"""
API Routes for Form Data Export
Handles export of form submissions to Excel, CSV, and Google Sheets
"""

from flask import Blueprint, request, jsonify, send_file, current_app
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import time

from ..services.form_data_export_service import form_data_export_service
from ..services.google_forms_service import google_forms_service
from ..services.google_forms_excel_service import google_forms_excel_service
from ..decorators import (
    firebase_auth_required as require_auth,
    get_current_user_id as get_current_user,
    require_form_access,
    admin_required
)
from ..models import Form, ExportFile
from .. import db
from ..core.rate_limiter import rate_limit, RateLimitStrategy, RateLimitScope
from ..utils.export_cleanup import get_cleanup_service
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

# Create blueprint
form_export_bp = Blueprint('form_export', __name__, url_prefix='/api/forms')


@form_export_bp.route('/<int:form_id>/export', methods=['POST', 'OPTIONS'])
@require_auth
@require_form_access
@rate_limit('form_export', requests=10, window=3600, strategy=RateLimitStrategy.SLIDING_WINDOW, scope=RateLimitScope.USER)
def export_form_data(form_id: int):
    """
    Export form submissions to Excel, CSV, or Google Sheets

    POST /api/forms/{form_id}/export

    Request Body:
    {
        "format": "excel" | "csv" | "googlesheets",
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-12-31"
        },
        "filters": {
            "status": "approved" | "rejected" | "pending" | "all",
            "submitter_email": "user@example.com"
        },
        "include_analytics": true,
        "excel_options": {
            "include_form_schema": true,
            "include_submission_metadata": true,
            "formatting": "professional" | "basic" | "custom",
            "compression": true
        }
    }

    Response:
    {
        "success": true,
        "message": "Successfully exported 45 submissions to excel",
        "download_url": "/api/exports/download/form_1_export_20250105_143022_abc123.xlsx",
        "file_size": 25600,
        "submissions_count": 45,
        "total_available": 50,
        "generation_time": 1.25,
        "data_quality_score": 0.92,
        "format": "excel"
    }
    """
    try:
        # Handle OPTIONS preflight request
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        # Verify form exists
        form = Form.query.get(form_id)
        if not form:
            return jsonify({
                'success': False,
                'error': f'Form {form_id} not found'
            }), 404

        # Get request data
        data = request.get_json() or {}

        export_format = data.get('format', 'excel').lower()

        # Validate format
        if export_format not in ['excel', 'xlsx', 'csv', 'googlesheets']:
            return jsonify({
                'success': False,
                'error': f'Invalid export format: {export_format}. Must be excel, csv, or googlesheets'
            }), 400

        # Prepare export options
        options = {
            'date_range': data.get('date_range', {}),
            'filters': data.get('filters', {}),
            'include_analytics': data.get('include_analytics', True),
            'excel_options': data.get('excel_options', {}),
            'max_records': data.get('max_records', 10000)
        }

        # Perform export
        result = form_data_export_service.export_form_data(
            form_id=form_id,
            export_format=export_format,
            options=options
        )

        # Audit log the export
        user_id = get_current_user()
        logger.info(f"Export audit: user_id={user_id}, form_id={form_id}, format={export_format}, "
                   f"success={result.get('success')}, submissions_count={result.get('submissions_count', 0)}, "
                   f"file_size={result.get('file_size', 0)}")

        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error in export_form_data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@form_export_bp.route('/google-forms/<string:google_form_id>/export', methods=['POST', 'OPTIONS'])
@require_auth
@rate_limit('google_forms_export', requests=5, window=3600, strategy=RateLimitStrategy.SLIDING_WINDOW, scope=RateLimitScope.USER)
def export_google_form_data(google_form_id: str):
    """
    Export Google Forms responses to Excel or CSV

    POST /api/forms/google-forms/{google_form_id}/export

    Request Body:
    {
        "format": "excel" | "csv",
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-12-31"
        },
        "include_analytics": true
    }

    Response:
    {
        "success": true,
        "message": "Successfully exported 128 Google Form responses to excel",
        "download_url": "/api/exports/download/google_form_abc123_export_20250105_143022.xlsx",
        "file_size": 35400,
        "responses_count": 128,
        "generation_time": 2.1,
        "format": "excel"
    }
    """
    try:
        # Handle OPTIONS preflight request
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200

        # Get request data
        data = request.get_json() or {}

        # Log received data for debugging AI enhancement
        logger.info(f"📥 Export request data: format={data.get('format')}, use_ai_enhancement={data.get('use_ai_enhancement')}, include_analytics={data.get('include_analytics')}")

        export_format = data.get('format', 'excel').lower()

        # Validate format
        if export_format not in ['excel', 'xlsx', 'csv']:
            return jsonify({
                'success': False,
                'error': f'Invalid export format for Google Forms: {export_format}. Must be excel or csv'
            }), 400

        # Fetch Google Forms data
        try:
            # Get current user ID for Google Forms API
            user_id = get_current_user()

            responses_data = google_forms_service.get_form_responses(
                user_id=str(user_id),
                form_id=google_form_id,
                limit=data.get('max_records', 1000),
                include_analysis=data.get('include_analytics', True)
            )

            if not responses_data.get('success'):
                return jsonify({
                    'success': False,
                    'error': responses_data.get('error', 'Failed to fetch Google Forms data')
                }), 400

        except Exception as fetch_error:
            logger.error(f"Error fetching Google Forms data: {str(fetch_error)}")
            return jsonify({
                'success': False,
                'error': f'Failed to fetch Google Forms data: {str(fetch_error)}'
            }), 500

        # Export data using Google Forms Excel service (supports AI enhancement)
        logger.info(f"Starting export of {len(responses_data.get('responses', []))} Google Form responses")

        result = google_forms_excel_service.export_google_form_to_excel(
            user_id=str(user_id),
            form_id=google_form_id,
            options={
                'date_range': data.get('date_range', {}),
                'include_analytics': data.get('include_analytics', True),
                'use_ai_enhancement': data.get('use_ai_enhancement', False),
                'excel_options': data.get('excel_options', {}),
                'max_responses': data.get('max_records', 1000)
            }
        )

        # Audit log the Google Forms export
        user_id = get_current_user()
        logger.info(f"Google Forms export audit: user_id={user_id}, google_form_id={google_form_id}, "
                   f"format={export_format}, success={result.get('success')}, "
                   f"responses_count={result.get('responses_count', 0)}, "
                   f"file_size={result.get('file_size', 0)}, "
                   f"file_path={result.get('file_path', 'N/A')}, "
                   f"download_url={result.get('download_url', 'N/A')}")

        if result.get('success'):
            # SECURITY: Register the export file for access control with retry logic
            filename = os.path.basename(result.get('file_path', ''))
            max_retries = 3
            retry_delay = 0.5  # seconds

            for attempt in range(max_retries):
                try:
                    # Rollback any pending transactions before retry
                    if attempt > 0:
                        db.session.rollback()
                        time.sleep(retry_delay * attempt)  # Exponential backoff

                    ExportFile.register_export(
                        filename=filename,
                        user_id=str(user_id),
                        file_type='google_forms_export',
                        file_format=export_format,
                        file_size=result.get('file_size', 0),
                        file_path=result.get('file_path', ''),
                        related_id=google_form_id,
                        related_type='google_form',
                        expires_at=datetime.utcnow() + timedelta(hours=24)  # Expire after 24 hours
                    )
                    logger.info(f"Registered export file: {filename} for user {user_id}")
                    break  # Success, exit retry loop
                except OperationalError as db_error:
                    logger.warning(f"Database connection error on attempt {attempt + 1}/{max_retries}: {str(db_error)}")
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to register export file after {max_retries} attempts: {str(db_error)}", exc_info=True)
                        # Don't fail the request if registration fails, but log it
                except Exception as reg_error:
                    logger.error(f"Failed to register export file: {str(reg_error)}", exc_info=True)
                    # Don't fail the request if registration fails, but log it
                    break  # Exit on non-connection errors

            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error in export_google_form_data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@form_export_bp.route('/<int:form_id>/preview', methods=['POST', 'OPTIONS'])
@require_auth
@require_form_access
def preview_form_data(form_id: int):
    """
    Preview form data before export (returns sample of first 10 submissions)

    POST /api/forms/{form_id}/preview

    Request Body: Same filters as export endpoint

    Response:
    {
        "success": true,
        "form": { "id": 1, "title": "Employee Survey" },
        "submissions": [...],
        "pagination": {
            "total": 45,
            "page": 1,
            "per_page": 10
        },
        "analytics": {
            "status_breakdown": {...},
            "submission_timeline": {...}
        }
    }
    """
    try:
        from ..services.analytics_service import analytics_service
        from ..models import FormSubmission

        # Verify form exists
        form = Form.query.get(form_id)
        if not form:
            return jsonify({
                'success': False,
                'error': f'Form {form_id} not found'
            }), 404

        # Get request data
        data = request.get_json() or {}

        # Get filtered submissions (limit to 10 for preview)
        options = {
            'date_range': data.get('date_range', {}),
            'filters': data.get('filters', {}),
            'max_records': 10
        }

        submissions, total_count = form_data_export_service._get_filtered_submissions(
            form_id, options
        )

        # Serialize submissions
        submissions_data = []
        for sub in submissions:
            submissions_data.append({
                'id': sub.id,
                'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else None,
                'status': sub.status,
                'submitter_email': sub.submitter_email,
                'data': sub.data
            })

        # Build response
        response = {
            'success': True,
            'form': {
                'id': form.id,
                'title': form.title,
                'fields': form.schema.get('fields', []) if form.schema else []
            },
            'submissions': submissions_data,
            'pagination': {
                'total': total_count,
                'page': 1,
                'per_page': 10
            }
        }

        # Add analytics if requested
        if data.get('include_analytics', True):
            # Status breakdown
            status_counts = {}
            for sub in submissions:
                status = sub.status or 'submitted'
                status_counts[status] = status_counts.get(status, 0) + 1

            response['analytics'] = {
                'status_breakdown': status_counts,
                'total_submissions': total_count,
                'preview_count': len(submissions)
            }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in preview_form_data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@form_export_bp.route('/google-forms/<string:google_form_id>/preview', methods=['GET'])
@require_auth
def preview_google_form_data(google_form_id: str):
    """
    Preview Google Forms responses before export

    GET /api/forms/google-forms/{google_form_id}/preview?limit=10&include_analysis=true

    Response:
    {
        "success": true,
        "form_info": {
            "title": "Customer Feedback Survey",
            "questions": [...]
        },
        "responses": [...],
        "total_count": 128,
        "analysis": {...}
    }
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        include_analysis = request.args.get('include_analysis', 'true').lower() == 'true'

        # Get current user ID for Google Forms API
        user_id = get_current_user()

        # Fetch Google Forms data
        result = google_forms_service.get_form_responses(
            user_id=str(user_id),
            form_id=google_form_id,
            limit=limit,
            include_analysis=include_analysis
        )

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"Error in preview_google_form_data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Download endpoint (served from static exports folder)
exports_bp = Blueprint('exports', __name__, url_prefix='/api/exports')


@exports_bp.route('/debug/<filename>', methods=['GET'])
@require_auth  # SECURITY: Require authentication
@admin_required  # SECURITY: Admin only
def debug_export_file(filename: str):
    """
    Debug endpoint to check export file status (admin only, development only)
    GET /api/exports/debug/{filename}
    """
    try:
        import os as os_module
        
        # Only allow in development
        if current_app.config.get('ENV') != 'development' and os_module.environ.get('FLASK_ENV') != 'development':
            return jsonify({'error': 'Not Found'}), 404
        
        export_folder = form_data_export_service.export_folder
        file_path = os.path.join(export_folder, filename)

        # Sanitize response - no absolute paths or directory listings
        debug_info = {
            'filename': filename,
            'file_exists': os.path.exists(file_path),
            'status': 'ok' if os.path.exists(file_path) else 'not_found'
        }

        if os.path.exists(file_path):
            debug_info['file_size'] = os.path.getsize(file_path)
            debug_info['file_mtime'] = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

        return jsonify(debug_info), 200

    except Exception as e:
        logger.error(f"Error in debug_export_file: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to check file status',
            'status': 'error'
        }), 500


@exports_bp.route('/download/<filename>', methods=['GET'])
@require_auth  # SECURITY: Require authentication
@rate_limit('export_download', requests=50, window=3600, strategy=RateLimitStrategy.SLIDING_WINDOW, scope=RateLimitScope.USER)
def download_export_file(filename: str):
    """
    Download an exported file (SECURE - requires authentication and ownership)

    GET /api/exports/download/{filename}

    Returns: File download

    Security:
    - Requires authentication (@require_auth)
    - Verifies file ownership (user can only download their own files)
    - Prevents directory traversal attacks
    - Logs all download attempts with user info
    """
    try:
        # Get current user
        user_id = get_current_user()
        logger.info(f"Download request for file: {filename} from user: {user_id}")

        # Security: Validate filename (prevent directory traversal)
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"Invalid filename attempted: {filename} by user: {user_id}")
            return jsonify({
                'success': False,
                'error': 'Invalid filename'
            }), 400

        # SECURITY: Verify file ownership
        if not ExportFile.verify_access(filename, str(user_id)):
            logger.warning(f"Unauthorized download attempt: {filename} by user: {user_id}")
            return jsonify({
                'success': False,
                'error': 'File not found or access denied'
            }), 404

        # Get file record
        export_file = ExportFile.get_file_by_filename(filename)
        if not export_file:
            logger.error(f"Export file record not found: {filename}")
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        file_path = export_file.file_path
        logger.info(f"Looking for file at: {file_path}")

        # Check file exists on disk
        if not os.path.exists(file_path):
            logger.error(f"File not found on disk: {file_path}")
            export_folder = form_data_export_service.export_folder
            logger.info(f"Export folder contents: {os.listdir(export_folder) if os.path.exists(export_folder) else 'folder does not exist'}")
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        file_size = os.path.getsize(file_path)
        logger.info(f"File found. Size: {file_size} bytes. Owned by: {export_file.user_id}")

        # Determine mimetype
        if filename.endswith('.xlsx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.csv'):
            mimetype = 'text/csv'
        else:
            mimetype = 'application/octet-stream'

        logger.info(f"Sending file with mimetype: {mimetype}")

        # Update download statistics
        export_file.mark_downloaded()

        # Send file - use absolute path and open in binary mode
        try:
            response = send_file(
                os.path.abspath(file_path),
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename,
                conditional=False  # Disable conditional GET to avoid 304 responses
            )
            logger.info(f"File sent successfully to user {user_id}")
            return response
        except Exception as send_error:
            logger.error(f"Error in send_file: {str(send_error)}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"Error downloading file {filename}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Cleanup management endpoints
@exports_bp.route('/cleanup/stats', methods=['GET'])
@require_auth
@admin_required
def get_cleanup_stats():
    """
    Get export cleanup statistics (admin only)

    GET /api/exports/cleanup/stats

    Response:
    {
        "last_cleanup": "2025-01-23T10:30:00",
        "files_deleted": 45,
        "bytes_freed": 125000000,
        "disk_usage_percent": 45.2
    }
    """
    try:
        cleanup_service = get_cleanup_service(form_data_export_service.export_folder)
        stats = cleanup_service.get_cleanup_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting cleanup stats: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@exports_bp.route('/cleanup/trigger', methods=['POST'])
@require_auth
@admin_required
def trigger_cleanup():
    """
    Manually trigger export cleanup (admin only)

    POST /api/exports/cleanup/trigger
    {
        "force": false
    }

    Response:
    {
        "success": true,
        "files_deleted": 12,
        "bytes_freed_mb": 45.3,
        "elapsed_seconds": 0.15
    }
    """
    try:
        data = request.get_json() or {}
        force = data.get('force', False)

        cleanup_service = get_cleanup_service(form_data_export_service.export_folder)
        result = cleanup_service.cleanup_old_files(force=force)

        return jsonify(result), 200 if result.get('success') else 500
    except Exception as e:
        logger.error(f"Error triggering cleanup: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@exports_bp.route('/cleanup/list', methods=['GET'])
@require_auth
@admin_required
def list_old_files():
    """
    List export files that would be cleaned up (admin only)

    GET /api/exports/cleanup/list

    Response:
    {
        "success": true,
        "old_files": [
            {
                "filename": "form_1_export_20250101_120000.xlsx",
                "age_hours": 36.5,
                "size_mb": 2.3
            }
        ],
        "total_files": 5,
        "total_size_mb": 12.8
    }
    """
    try:
        cleanup_service = get_cleanup_service(form_data_export_service.export_folder)
        old_files = cleanup_service.list_old_files()

        total_size_bytes = sum(f['size_bytes'] for f in old_files)

        return jsonify({
            'success': True,
            'old_files': old_files,
            'total_files': len(old_files),
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2)
        }), 200
    except Exception as e:
        logger.error(f"Error listing old files: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Register blueprints helper
def register_export_blueprints(app):
    """Register export blueprints with the Flask app"""
    app.register_blueprint(form_export_bp)
    app.register_blueprint(exports_bp)
    logger.info("Form data export routes registered successfully")

    # Initialize cleanup service and schedule periodic cleanups
    try:
        from ..utils.export_cleanup import schedule_periodic_cleanup
        schedule_periodic_cleanup(interval_hours=6)  # Run cleanup every 6 hours
        logger.info("Scheduled periodic export cleanup (every 6 hours)")
    except Exception as e:
        logger.warning(f"Could not schedule periodic cleanup: {str(e)}")
