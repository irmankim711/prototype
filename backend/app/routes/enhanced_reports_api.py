"""
Enhanced Reports API with Advanced Editing Features
Provides endpoints for report versioning, template management, and collaborative editing
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload
from datetime import datetime
from app import db
from app.models.report_models import ReportVersion, ReportTemplate, ReportEdit
from app.models.form import Report, User
from app.services.report_editing_service import ReportEditingService, TemplateService
import traceback

def get_current_user():
    """Get current user from JWT token"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

enhanced_reports_bp = Blueprint('enhanced_reports', __name__)

@enhanced_reports_bp.route('/reports/<int:report_id>/edit', methods=['PUT'])
@jwt_required()
def update_report_content(report_id):
    """Update report content and create new version"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate user has permission to edit
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        # Extract content and metadata
        content = data.get('content', {})
        change_summary = data.get('change_summary', 'Content updated')
        template_id = data.get('template_id')
        
        # Create new version
        new_version = ReportEditingService.create_version(
            report_id=report_id,
            content=content,
            user_id=current_user.id,
            change_summary=change_summary,
            template_id=template_id
        )
        
        # Log the edit
        edit_log = ReportEdit(
            report_id=report_id,
            user_id=current_user.id,
            edit_type='content',
            new_value=content,
            old_value={}  # Could store previous content if needed
        )
        db.session.add(edit_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Report updated successfully',
            'version': new_version.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to update report', 'details': str(e)}), 500

@enhanced_reports_bp.route('/reports/<int:report_id>/versions', methods=['GET'])
@jwt_required()
def get_report_versions(report_id):
    """Get all versions of a report"""
    try:
        current_user = get_current_user()
        
        # Validate user has permission
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        # Get all versions with creator information
        versions = (ReportVersion.query
                   .filter_by(report_id=report_id)
                   .options(joinedload(ReportVersion.creator))
                   .order_by(desc(ReportVersion.version_number))
                   .all())
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'report_name': report.title,
            'total_versions': len(versions),
            'versions': [version.to_dict() for version in versions]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching versions for report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch versions', 'details': str(e)}), 500

@enhanced_reports_bp.route('/reports/<int:report_id>/versions/<int:version_id>', methods=['GET'])
@jwt_required()
def get_specific_version(report_id, version_id):
    """Get specific version content"""
    try:
        current_user = get_current_user()
        
        # Validate permissions
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        version = ReportVersion.query.filter_by(
            id=version_id, 
            report_id=report_id
        ).first()
        
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        
        return jsonify({
            'success': True,
            'version': version.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching version {version_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch version', 'details': str(e)}), 500

@enhanced_reports_bp.route('/reports/<int:report_id>/versions/<int:version_id>/rollback', methods=['POST'])
@jwt_required()
def rollback_report_version(report_id, version_id):
    """Rollback report to specific version"""
    try:
        current_user = get_current_user()
        
        # Validate permissions
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        # Perform rollback
        new_version = ReportEditingService.rollback_to_version(
            report_id=report_id,
            version_id=version_id,
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'message': f'Report rolled back to version {version_id}',
            'new_version': new_version.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rolling back report {report_id}: {str(e)}")
        return jsonify({'error': 'Failed to rollback report', 'details': str(e)}), 500

@enhanced_reports_bp.route('/reports/<int:report_id>/versions/compare/<int:version1_id>/<int:version2_id>', methods=['GET'])
@jwt_required()
def compare_versions(report_id, version1_id, version2_id):
    """Compare two versions and return differences"""
    try:
        current_user = get_current_user()
        
        # Validate permissions
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        # Get diff
        diff_result = ReportEditingService.get_version_diff(version1_id, version2_id)
        
        return jsonify({
            'success': True,
            'comparison': diff_result
        })
        
    except Exception as e:
        current_app.logger.error(f"Error comparing versions: {str(e)}")
        return jsonify({'error': 'Failed to compare versions', 'details': str(e)}), 500

# Template Management Endpoints

@enhanced_reports_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """Get available report templates"""
    try:
        current_user = get_current_user()
        
        # Get user's templates and public templates
        templates = (ReportTemplate.query
                    .filter(or_(
                        ReportTemplate.created_by == current_user.id,
                        ReportTemplate.is_public == True
                    ))
                    .options(joinedload(ReportTemplate.creator))
                    .order_by(desc(ReportTemplate.usage_count))
                    .all())
        
        return jsonify({
            'success': True,
            'templates': [template.to_dict() for template in templates]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching templates: {str(e)}")
        return jsonify({'error': 'Failed to fetch templates', 'details': str(e)}), 500

@enhanced_reports_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_template():
    """Create a new report template"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'layout_config']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create template
        template = TemplateService.create_template(
            name=data['name'],
            description=data.get('description', ''),
            layout_config=data['layout_config'],
            style_config=data.get('style_config', {}),
            user_id=current_user.id,
            is_public=data.get('is_public', False)
        )
        
        return jsonify({
            'success': True,
            'message': 'Template created successfully',
            'template': template.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating template: {str(e)}")
        return jsonify({'error': 'Failed to create template', 'details': str(e)}), 500

@enhanced_reports_bp.route('/reports/<int:report_id>/apply-template', methods=['POST'])
@jwt_required()
def apply_template_to_report(report_id):
    """Apply a template to a report"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data or 'template_id' not in data:
            return jsonify({'error': 'Template ID required'}), 400
        
        # Validate permissions
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        # Apply template
        new_version = TemplateService.apply_template(
            report_id=report_id,
            template_id=data['template_id'],
            user_id=current_user.id
        )
        
        return jsonify({
            'success': True,
            'message': 'Template applied successfully',
            'version': new_version.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error applying template: {str(e)}")
        return jsonify({'error': 'Failed to apply template', 'details': str(e)}), 500

@enhanced_reports_bp.route('/reports/<int:report_id>/edit-history', methods=['GET'])
@jwt_required()
def get_edit_history(report_id):
    """Get edit history for a report"""
    try:
        current_user = get_current_user()
        
        # Validate permissions
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        # Get edit history
        edits = (ReportEdit.query
                .filter_by(report_id=report_id)
                .options(joinedload(ReportEdit.editor))
                .order_by(desc(ReportEdit.timestamp))
                .limit(50)  # Limit to recent 50 edits
                .all())
        
        return jsonify({
            'success': True,
            'edit_history': [{
                'id': edit.id,
                'edit_type': edit.edit_type,
                'editor': edit.editor.username,
                'timestamp': edit.timestamp.isoformat(),
                'has_changes': bool(edit.old_value or edit.new_value)
            } for edit in edits]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching edit history: {str(e)}")
        return jsonify({'error': 'Failed to fetch edit history', 'details': str(e)}), 500

@enhanced_reports_bp.route('/reports/<int:report_id>/auto-save', methods=['POST'])
@jwt_required()
def auto_save_report(report_id):
    """Auto-save report content (lightweight version of update)"""
    try:
        current_user = get_current_user()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate permissions
        report = Report.query.filter_by(id=report_id, user_id=current_user.id).first()
        if not report:
            return jsonify({'error': 'Report not found or access denied'}), 404
        
        # For auto-save, we might want to update the current version instead of creating new ones
        # to avoid version pollution. Only create new version for explicit saves.
        current_version = ReportVersion.query.filter_by(
            report_id=report_id, 
            is_current=True
        ).first()
        
        if current_version:
            current_version.content = data.get('content', {})
            current_version.change_summary = 'Auto-save'
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Auto-saved successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            # No current version exists, create one
            new_version = ReportEditingService.create_version(
                report_id=report_id,
                content=data.get('content', {}),
                user_id=current_user.id,
                change_summary='Auto-save (initial version)'
            )
            
            return jsonify({
                'success': True,
                'message': 'Auto-saved successfully',
                'version': new_version.to_dict()
            })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error auto-saving report {report_id}: {str(e)}")
        return jsonify({'error': 'Auto-save failed', 'details': str(e)}), 500

# Error handlers
@enhanced_reports_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@enhanced_reports_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500
