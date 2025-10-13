"""
Minimal Excel->DOCX preview route for debugging
Provides GET /api/excel-to-docx/<id>/preview which returns a preview_url JSON
This is intentionally minimal to help local debugging. Remove or secure in production.
"""

from flask import Blueprint, jsonify, current_app
import os

from ..models import Report

preview_bp = Blueprint('excel_to_docx_preview', __name__, url_prefix='/api/excel-to-docx')

@preview_bp.route('/<int:report_id>/preview', methods=['GET'])
def preview_report(report_id):
    try:
        report = Report.query.get(report_id)
        if not report:
            return jsonify({'success': False, 'error': 'Report not found'}), 404

        # Try common fields or fallbacks
        preview = getattr(report, 'preview_url', None) or getattr(report, 'file_path', None) or getattr(report, 'output_url', None) or getattr(report, 'download_url', None)
        if not preview:
            return jsonify({'success': False, 'error': 'No preview available for this report'}), 404

        # If local file path, point to preview-content endpoint if present
        if not (str(preview).startswith('http://') or str(preview).startswith('https://')):
            # Return a preview-content URL (the bridge provides /api/excel-to-docx/preview-content/<id>)
            content_url = f'/api/excel-to-docx/preview-content/{report_id}'
            return jsonify({'success': True, 'preview_url': content_url}), 200

        return jsonify({'success': True, 'preview_url': preview}), 200
    except Exception as e:
        current_app.logger.error(f'Preview endpoint error: {e}')
        return jsonify({'success': False, 'error': 'Internal error'}), 500
