"""
Report Editor API Endpoints
Handles report editing interface, version control, and collaboration
"""
import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

from ..decorators import require_auth, require_permission
from ..services.report_editor_service import report_editor_service
from ..models.template_models import GeneratedReport, ReportVersion
from .. import db

logger = logging.getLogger(__name__)

# Create blueprint
editor_bp = Blueprint('editor', __name__, url_prefix='/api/v1/editor')

@editor_bp.route('/<int:report_id>', methods=['GET'])
@require_auth
def open_report_editor(report_id):
    """
    Open a report in the editor
    
    Returns report content, metadata, and editing session information
    """
    try:
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Get session data from query parameters
        session_data = {
            'client_info': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'opened_at': datetime.utcnow().isoformat()
        }
        
        # Open editor session
        result = report_editor_service.open_editor(
            report_id=report_id,
            user_id=user_id,
            session_data=session_data
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 404 if 'not found' in result['error'].lower() else 403
        
        return jsonify({
            'success': True,
            'session_id': result['session_id'],
            'report': result['report'],
            'collaborators': result['collaborators'],
            'permissions': result['permissions'],
            'websocket_url': f"ws://{request.host}/socket.io",
            'editor_namespace': '/editor'
        })
        
    except Exception as e:
        logger.error(f"Error opening report editor: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/save', methods=['POST'])
@require_auth
def save_report_changes(report_id):
    """
    Save changes to a report
    
    Expected JSON:
    {
        "content": dict,
        "change_summary": str (optional),
        "auto_save": bool (optional, default: false)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content')
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Save changes
        result = report_editor_service.save_changes(
            report_id=report_id,
            user_id=user_id,
            content=content,
            auto_save=data.get('auto_save', False),
            change_summary=data.get('change_summary')
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error saving report changes: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/auto-save', methods=['POST'])
@require_auth
def auto_save_report(report_id):
    """
    Auto-save report content (lightweight endpoint for frequent saves)
    
    Expected JSON:
    {
        "content": dict
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'Content is required'}), 400
        
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Perform auto-save
        result = report_editor_service.save_changes(
            report_id=report_id,
            user_id=user_id,
            content=data['content'],
            auto_save=True,
            change_summary='Auto-save'
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        # Return minimal response for auto-save
        return jsonify({
            'success': True,
            'auto_save': True,
            'saved_at': result.get('saved_at'),
            'message': result.get('message', 'Auto-saved successfully')
        })
        
    except Exception as e:
        logger.error(f"Error auto-saving report: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/versions', methods=['GET'])
@require_auth
def get_report_versions(report_id):
    """
    Get version history for a report
    
    Query parameters:
    - limit: Maximum number of versions to return (default: 50)
    """
    try:
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Get limit from query parameters
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 100)  # Cap at 100 versions
        
        # Get versions
        result = report_editor_service.get_versions(
            report_id=report_id,
            user_id=user_id,
            limit=limit
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 404 if 'not found' in result['error'].lower() else 403
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting report versions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/versions/<int:version_id>', methods=['GET'])
@require_auth
def get_specific_version(report_id, version_id):
    """Get a specific version of a report"""
    try:
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Check access to report
        report = GeneratedReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Basic permission check
        if report.created_by != user_id and not request.current_user.get('is_admin', False):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get the specific version
        version = ReportVersion.query.filter_by(
            id=version_id,
            report_id=report_id
        ).first()
        
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        
        return jsonify({
            'success': True,
            'version': {
                'id': version.id,
                'version_number': version.version_number,
                'content': version.content,
                'created_at': version.created_at.isoformat(),
                'created_by': version.created_by,
                'change_summary': version.change_summary,
                'is_current': version.is_current,
                'is_auto_save': version.is_auto_save,
                'creator_name': f'User {version.created_by}'  # Would get from user service
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting specific version: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/revert/<int:version_id>', methods=['POST'])
@require_auth
@require_permission('edit_reports')
def revert_to_version(report_id, version_id):
    """
    Revert report to a specific version
    
    Expected JSON (optional):
    {
        "change_summary": str (optional)
    }
    """
    try:
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Get optional change summary
        data = request.get_json() or {}
        change_summary = data.get('change_summary')
        
        # Revert to version
        result = report_editor_service.revert_version(
            report_id=report_id,
            version_id=version_id,
            user_id=user_id
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 404 if 'not found' in result['error'].lower() else 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error reverting to version: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/close', methods=['POST'])
@require_auth
def close_editor_session(report_id):
    """Close an editing session"""
    try:
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Close session
        result = report_editor_service.close_session(
            report_id=report_id,
            user_id=user_id
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error closing editor session: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/collaborators', methods=['GET'])
@require_auth
def get_active_collaborators(report_id):
    """Get list of active collaborators for a report"""
    try:
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Check access to report
        report = GeneratedReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Basic permission check
        if report.created_by != user_id and not request.current_user.get('is_admin', False):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get active sessions
        sessions = report_editor_service.get_active_sessions(report_id)
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'collaborators': sessions,
            'total_collaborators': len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Error getting collaborators: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/operation', methods=['POST'])
@require_auth
def handle_collaborative_operation(report_id):
    """
    Handle collaborative editing operation
    
    Expected JSON:
    {
        "operation": {
            "type": str,  # "insert", "delete", "format", etc.
            "position": dict,
            "content": str (optional),
            "length": int (optional),
            "format": dict (optional)
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'operation' not in data:
            return jsonify({'error': 'Operation is required'}), 400
        
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Handle the operation
        result = report_editor_service.handle_collaborative_operation(
            report_id=report_id,
            user_id=user_id,
            operation=data['operation']
        )
        
        if not result['success']:
            return jsonify({'error': result['error']}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error handling collaborative operation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/compare/<int:version1_id>/<int:version2_id>', methods=['GET'])
@require_auth
def compare_versions(report_id, version1_id, version2_id):
    """Compare two versions of a report"""
    try:
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Check access to report
        report = GeneratedReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Basic permission check
        if report.created_by != user_id and not request.current_user.get('is_admin', False):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get both versions
        version1 = ReportVersion.query.filter_by(
            id=version1_id,
            report_id=report_id
        ).first()
        
        version2 = ReportVersion.query.filter_by(
            id=version2_id,
            report_id=report_id
        ).first()
        
        if not version1 or not version2:
            return jsonify({'error': 'One or both versions not found'}), 404
        
        # Generate comparison
        from ..services.enhancedReportService import enhancedReportService
        comparison = enhancedReportService.generateContentDiff(
            version1.content or {},
            version2.content or {}
        )
        
        return jsonify({
            'success': True,
            'comparison': comparison,
            'version1': {
                'id': version1.id,
                'version_number': version1.version_number,
                'created_at': version1.created_at.isoformat(),
                'change_summary': version1.change_summary
            },
            'version2': {
                'id': version2.id,
                'version_number': version2.version_number,
                'created_at': version2.created_at.isoformat(),
                'change_summary': version2.change_summary
            }
        })
        
    except Exception as e:
        logger.error(f"Error comparing versions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/export', methods=['POST'])
@require_auth
def export_report_from_editor(report_id):
    """
    Export report from editor in various formats
    
    Expected JSON:
    {
        "formats": ["pdf", "docx", "html"],
        "version_id": int (optional, defaults to current)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        formats = data.get('formats', ['pdf'])
        version_id = data.get('version_id')
        
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Check access to report
        report = GeneratedReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Basic permission check
        if report.created_by != user_id and not request.current_user.get('is_admin', False):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get content from specific version or current
        if version_id:
            version = ReportVersion.query.filter_by(
                id=version_id,
                report_id=report_id
            ).first()
            
            if not version:
                return jsonify({'error': 'Version not found'}), 404
            
            content = version.content
        else:
            # Get current content
            content = report_editor_service._get_report_content(report)
        
        # Use report generation service to export
        from ..services.report_generation_service import report_generation_service
        
        result = report_generation_service.generate_report_sync(
            template_id=report.template_id,
            data_source=content,
            output_formats=formats,
            user_id=user_id,
            report_name=f"{report.report_name}_export"
        )
        
        if not result['success']:
            return jsonify({'error': result.get('error', 'Export failed')}), 500
        
        # Build download URLs
        base_url = request.url_root.rstrip('/')
        urls = {}
        
        for format_type in formats:
            if format_type in result.get('file_paths', {}):
                urls[format_type] = f"{base_url}/api/v1/reports/{result['report_id']}/download/{format_type}"
        
        return jsonify({
            'success': True,
            'export_id': result['report_id'],
            'formats': formats,
            'urls': urls,
            'exported_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error exporting report from editor: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@editor_bp.route('/<int:report_id>/status', methods=['GET'])
@require_auth
def get_editor_status(report_id):
    """Get current editing status and session information"""
    try:
        # Get user ID from auth context
        user_id = request.current_user.get('user_id', 1)
        
        # Check access to report
        report = GeneratedReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Basic permission check
        if report.created_by != user_id and not request.current_user.get('is_admin', False):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get active sessions and collaborators
        sessions = report_editor_service.get_active_sessions(report_id)
        
        # Get latest version info
        latest_version = ReportVersion.query.filter_by(
            report_id=report_id,
            is_current=True
        ).first()
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'report_name': report.report_name,
            'status': report.status.value,
            'active_sessions': len(sessions),
            'collaborators': sessions,
            'latest_version': {
                'id': latest_version.id,
                'version_number': latest_version.version_number,
                'created_at': latest_version.created_at.isoformat(),
                'change_summary': latest_version.change_summary
            } if latest_version else None,
            'last_modified': report.updated_at.isoformat() if report.updated_at else None
        })
        
    except Exception as e:
        logger.error(f"Error getting editor status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Error handlers
@editor_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request error"""
    return jsonify({'error': 'Bad request'}), 400

@editor_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden error"""
    return jsonify({'error': 'Access denied'}), 403

@editor_bp.errorhandler(404)
def not_found(error):
    """Handle not found error"""
    return jsonify({'error': 'Resource not found'}), 404

@editor_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    logger.error(f"Internal server error in editor API: {error}")
    return jsonify({'error': 'Internal server error'}), 500