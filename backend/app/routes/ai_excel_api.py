"""
AI-Enhanced Excel Generation API
Provides endpoints for generating professional Excel files using Claude AI
"""

import os
import logging
from flask import Blueprint, request, jsonify, send_file
from functools import wraps

from ..services.ai_enhanced_excel_service import ai_excel_service
from ..core.exceptions import ReportGenerationError

logger = logging.getLogger(__name__)

ai_excel_bp = Blueprint('ai_excel', __name__, url_prefix='/api/ai-excel')


def require_auth(f):
    """Simple authentication decorator (replace with your actual auth)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add your authentication logic here
        # For now, just check for API key in headers
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@ai_excel_bp.route('/generate', methods=['POST'])
@require_auth
def generate_excel():
    """
    Generate an AI-enhanced Excel file from data

    Request body:
    {
        "data": [{"col1": "val1", "col2": "val2"}, ...],
        "title": "Report Title",
        "options": {
            "include_charts": true,
            "include_summary": true,
            "include_pivot": false
        }
    }

    Returns:
    {
        "success": true,
        "file_path": "/path/to/file.xlsx",
        "file_size": 12345,
        "download_url": "/api/ai-excel/download/filename.xlsx"
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        body = request.get_json()

        # Extract parameters
        data = body.get('data')
        title = body.get('title', 'Excel Report')
        options = body.get('options', {})

        # Validate data
        if not data:
            return jsonify({'error': 'Data is required'}), 400

        if not isinstance(data, list):
            return jsonify({'error': 'Data must be a list of objects'}), 400

        if len(data) == 0:
            return jsonify({'error': 'Data cannot be empty'}), 400

        # Validate options
        if not isinstance(options, dict):
            return jsonify({'error': 'Options must be an object'}), 400

        # Generate Excel file
        logger.info(f"Generating AI-enhanced Excel: {title} with {len(data)} records")
        file_path, file_size = ai_excel_service.generate_enhanced_excel(
            data=data,
            title=title,
            options=options
        )

        # Get filename for download URL
        filename = os.path.basename(file_path)

        return jsonify({
            'success': True,
            'file_path': file_path,
            'file_size': file_size,
            'download_url': f'/api/ai-excel/download/{filename}',
            'message': f'Excel file generated successfully with {len(data)} records'
        }), 200

    except ReportGenerationError as e:
        logger.error(f"Report generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Error generating Excel: {str(e)}")
        return jsonify({'error': 'Failed to generate Excel file'}), 500


@ai_excel_bp.route('/download/<filename>', methods=['GET'])
def download_excel(filename):
    """
    Download a generated Excel file

    Parameters:
        filename: Name of the file to download

    Returns:
        Excel file as attachment
    """
    try:
        # Sanitize filename to prevent directory traversal
        filename = os.path.basename(filename)

        # Construct file path
        reports_dir = os.path.join(os.getcwd(), 'reports', 'excel')
        file_path = os.path.join(reports_dir, filename)

        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404

        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        logger.error(f"Error downloading Excel file: {str(e)}")
        return jsonify({'error': 'Failed to download file'}), 500


@ai_excel_bp.route('/generate-from-form/<int:form_id>', methods=['POST'])
@require_auth
def generate_from_form(form_id):
    """
    Generate AI-enhanced Excel from form submissions

    Parameters:
        form_id: ID of the form

    Request body:
    {
        "options": {
            "include_charts": true,
            "include_summary": true,
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            }
        }
    }

    Returns:
    {
        "success": true,
        "file_path": "/path/to/file.xlsx",
        "download_url": "/api/ai-excel/download/filename.xlsx"
    }
    """
    try:
        from ..models import Form, FormSubmission

        # Get form
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': f'Form {form_id} not found'}), 404

        # Get options
        options = request.get_json() if request.is_json else {}
        options = options.get('options', {})

        # Build query
        query = FormSubmission.query.filter_by(form_id=form_id)

        # Apply date filters if provided
        date_range = options.get('date_range', {})
        if date_range.get('start'):
            from datetime import datetime
            start_date = datetime.fromisoformat(date_range['start'])
            query = query.filter(FormSubmission.submitted_at >= start_date)

        if date_range.get('end'):
            from datetime import datetime
            end_date = datetime.fromisoformat(date_range['end'])
            query = query.filter(FormSubmission.submitted_at <= end_date)

        # Get submissions
        submissions = query.all()

        if not submissions:
            return jsonify({'error': 'No submissions found'}), 404

        # Convert to data format
        data = []
        for submission in submissions:
            row = {
                'id': submission.id,
                'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                'status': submission.status,
                'submitter_email': submission.submitter_email
            }

            # Add form data
            if submission.data:
                row.update(submission.data)

            data.append(row)

        # Generate Excel
        title = f"{form.title} - Submissions Report"
        file_path, file_size = ai_excel_service.generate_enhanced_excel(
            data=data,
            title=title,
            options=options
        )

        filename = os.path.basename(file_path)

        return jsonify({
            'success': True,
            'file_path': file_path,
            'file_size': file_size,
            'download_url': f'/api/ai-excel/download/{filename}',
            'records_count': len(data),
            'message': f'Excel report generated successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error generating form Excel: {str(e)}")
        return jsonify({'error': 'Failed to generate Excel from form'}), 500


@ai_excel_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI-Enhanced Excel Generation',
        'version': '1.0.0'
    }), 200
