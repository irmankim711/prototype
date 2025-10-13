"""
Reports export API

POST /api/reports/export -> { template_id, data_source, formats: [pdf|docx|html] }
Returns { status, urls: { pdf, docx, html } }
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify, current_app, send_file

import os
import logging
from werkzeug.exceptions import BadRequest

from ..services.export_service import export_service
from ..validation.decorators import ErrorHandler

logger = logging.getLogger(__name__)

reports_export_bp = Blueprint('reports_export', __name__, url_prefix='/api/reports/export')

def _get_reports_dir():
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    base = os.path.abspath(os.path.join(current_app.root_path, '..', upload_folder))
    reports_dir = os.path.join(base, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir

@reports_export_bp.route('/', methods=['POST'])
def export_reports():
    try:
        data = request.get_json(silent=True) or {}
        template_id = data.get('template_id')
        data_source = data.get('data_source')
        formats = data.get('formats')

        # Validate required fields
        missing_fields = []
        if not template_id:
            missing_fields.append('template_id')
        if not data_source:
            missing_fields.append('data_source')
        if not formats:
            missing_fields.append('formats')

        if missing_fields:
            return ErrorHandler.bad_request_error(
                message='Missing required fields for report export',
                missing_fields=missing_fields
            )

        # Validate data types
        invalid_fields = {}
        if not isinstance(data_source, dict):
            invalid_fields['data_source'] = 'Must be an object/dictionary'
        if not isinstance(formats, list) or not formats:
            invalid_fields['formats'] = 'Must be a non-empty array'

        if invalid_fields:
            return ErrorHandler.bad_request_error(
                message='Invalid field formats',
                invalid_fields=invalid_fields
            )

        # Validate formats
        valid_formats = {"pdf", "docx", "html"}
        invalid_formats = [f for f in formats if str(f).lower() not in valid_formats]
        if invalid_formats:
            return ErrorHandler.bad_request_error(
                message=f"Invalid export format(s): {', '.join(invalid_formats)}",
                invalid_fields={'formats': f"Allowed formats: {', '.join(valid_formats)}"}
            )

        # Run export
        result = export_service.export(template_id=str(template_id), data_source=data_source, formats=formats)

        return jsonify({
            'status': result.status,
            'urls': result.urls
        })
    except BadRequest as e:
        return ErrorHandler.bad_request_error(str(e))
    except Exception as e:
        logger.error(f"Export error: {e}")
        return ErrorHandler.internal_error('Failed to export report')

@reports_export_bp.route('/download/<filename>', methods=['GET'])
def download_export(filename: str):
    try:
        reports_dir = _get_reports_dir()
        file_path = os.path.join(reports_dir, filename)
        # Fallback: existing code sometimes stores PDFs under uploads/pdfs
        if not os.path.isfile(file_path):
            alt_dir = os.path.join(os.path.dirname(reports_dir), 'pdfs')
            alt_path = os.path.join(alt_dir, filename)
            if os.path.isfile(alt_path):
                file_path = alt_path
        if not os.path.isfile(file_path):
            # As a last resort, search recursively under UPLOAD_FOLDER for the filename
            base_upload = os.path.abspath(os.path.join(current_app.root_path, '..', current_app.config.get('UPLOAD_FOLDER', 'uploads')))
            for root, _dirs, files in os.walk(base_upload):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    break
            if not os.path.isfile(file_path):
                return jsonify({'status': 'error', 'error': 'File not found'}), 404

        # Infer mimetype
        ext = os.path.splitext(filename)[1].lower()
        mimetype = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.html': 'text/html; charset=utf-8'
        }.get(ext, 'application/octet-stream')

        return send_file(file_path, as_attachment=True, download_name=filename, mimetype=mimetype)
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'status': 'error', 'error': 'Failed to download file'}), 500
