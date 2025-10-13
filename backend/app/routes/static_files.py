"""
Static Files Blueprint
Handles serving of static files, previews, and other assets
"""

from flask import Blueprint, send_from_directory, jsonify
import os
import logging

logger = logging.getLogger(__name__)

static_bp = Blueprint('static_files', __name__, url_prefix='/static')

@static_bp.route('/previews/<filename>')
def serve_preview(filename):
    """Serve HTML preview files"""
    try:
        preview_dir = os.path.join(os.getcwd(), 'static', 'previews')
        
        # Security check - ensure the file exists and is within the preview directory
        filepath = os.path.join(preview_dir, filename)
        if not os.path.exists(filepath) or not os.path.commonpath([preview_dir, filepath]) == preview_dir:
            return jsonify({'error': 'File not found or invalid path'}), 404
            
        return send_from_directory(preview_dir, filename)
    except Exception as e:
        logger.error(f"Error serving preview file {filename}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@static_bp.route('/reports/<filename>')
def serve_report_file(filename):
    """Serve generated report files"""
    try:
        reports_dir = os.path.join(os.getcwd(), 'static', 'generated')
        
        # Security check - ensure the file exists and is within the reports directory
        filepath = os.path.join(reports_dir, filename)
        if not os.path.exists(filepath) or not os.path.commonpath([reports_dir, filepath]) == reports_dir:
            return jsonify({'error': 'File not found or invalid path'}), 404
            
        return send_from_directory(reports_dir, filename)
    except Exception as e:
        logger.error(f"Error serving report file {filename}: {e}")
        return jsonify({'error': 'Internal server error'}), 500