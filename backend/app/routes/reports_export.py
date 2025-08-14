"""
Reports export API

POST /api/reports/export -> { template_id, data_source, formats: [pdf|docx|html] }
Returns { status, urls: { pdf, docx, html } }
"""
from __future__ import annotations

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import logging
from werkzeug.exceptions import BadRequest

from ..services.export_service import export_service

logger = logging.getLogger(__name__)

reports_export_bp = Blueprint('reports_export', __name__, url_prefix='/api/reports')


def _get_reports_dir():
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    base = os.path.abspath(os.path.join(current_app.root_path, '..', upload_folder))
    reports_dir = os.path.join(base, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


@reports_export_bp.route('/export', methods=['POST'])
@jwt_required(optional=True)
def export_reports():
    try:
        data = request.get_json(silent=True) or {}
        template_id = data.get('template_id')
        data_source = data.get('data_source')
        formats = data.get('formats')

        if not template_id:
            raise BadRequest('template_id is required')
        if not isinstance(data_source, dict):
            raise BadRequest('data_source must be an object')
        if not isinstance(formats, list) or not formats:
            raise BadRequest('formats must be a non-empty array')

        # Validate formats
        valid = {"pdf", "docx", "html"}
        invalid = [f for f in formats if str(f).lower() not in valid]
        if invalid:
            raise BadRequest(f"Invalid format(s): {', '.join(invalid)}")

        # Run export
        result = export_service.export(template_id=str(template_id), data_source=data_source, formats=formats)

        return jsonify({
            'status': result.status,
            'urls': result.urls
        })
    except BadRequest as e:
        return jsonify({'status': 'error', 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({'status': 'error', 'error': 'Failed to export report'}), 500


@reports_export_bp.route('/download/<filename>', methods=['GET'])
@jwt_required(optional=True)
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
