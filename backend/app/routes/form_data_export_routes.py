"""
API Routes for Form Data Export
Handles export of form submissions to Excel, CSV, and Google Sheets
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_cors import cross_origin
import os
import logging
from typing import Dict, Any

from ..services.form_data_export_service import form_data_export_service
from ..services.google_forms_service import google_forms_service
from ..core.security import require_auth, get_current_user
from ..models import Form

logger = logging.getLogger(__name__)

# Create blueprint
form_export_bp = Blueprint('form_export', __name__, url_prefix='/api/forms')


@form_export_bp.route('/<int:form_id>/export', methods=['POST'])
@cross_origin()
@require_auth
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


@form_export_bp.route('/google-forms/<string:google_form_id>/export', methods=['POST'])
@cross_origin()
@require_auth
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
        # Get request data
        data = request.get_json() or {}

        export_format = data.get('format', 'excel').lower()

        # Validate format
        if export_format not in ['excel', 'xlsx', 'csv']:
            return jsonify({
                'success': False,
                'error': f'Invalid export format for Google Forms: {export_format}. Must be excel or csv'
            }), 400

        # Fetch Google Forms data
        try:
            responses_data = google_forms_service.get_form_responses(
                google_form_id,
                options={'limit': data.get('max_records', 1000)}
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

        # Export data
        result = form_data_export_service.export_google_form_responses(
            google_form_id=google_form_id,
            form_responses=responses_data.get('responses', []),
            form_info=responses_data.get('form_info', {}),
            export_format=export_format,
            options={
                'date_range': data.get('date_range', {}),
                'include_analytics': data.get('include_analytics', True)
            }
        )

        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error in export_google_form_data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@form_export_bp.route('/<int:form_id>/preview', methods=['POST'])
@cross_origin()
@require_auth
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
@cross_origin()
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

        # Fetch Google Forms data
        result = google_forms_service.get_form_responses(
            google_form_id,
            options={
                'limit': limit,
                'include_analysis': include_analysis
            }
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


@exports_bp.route('/download/<filename>', methods=['GET'])
@cross_origin()
def download_export_file(filename: str):
    """
    Download an exported file

    GET /api/exports/download/{filename}

    Returns: File download
    """
    try:
        # Security: Validate filename (prevent directory traversal)
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'success': False,
                'error': 'Invalid filename'
            }), 400

        # Get file path
        export_folder = form_data_export_service.export_folder
        file_path = os.path.join(export_folder, filename)

        # Check file exists
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        # Determine mimetype
        if filename.endswith('.xlsx'):
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.endswith('.csv'):
            mimetype = 'text/csv'
        else:
            mimetype = 'application/octet-stream'

        # Send file
        return send_file(
            file_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Error downloading file {filename}: {str(e)}", exc_info=True)
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
