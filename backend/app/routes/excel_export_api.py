"""
Excel Export API Routes
Handles form data export to Excel with background processing
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_limiter import limiter
from datetime import datetime
import os
import logging
from typing import Dict, Any

from ..models import db, Form, FormSubmission, User
from ..services.excel_export_service import excel_export_service
from ..tasks.enhanced_report_tasks import export_form_to_excel_task
from ..core.exceptions import ExportError
from ..decorators import role_required, UserRole

logger = logging.getLogger(__name__)

# Create blueprint
excel_export_bp = Blueprint('excel_export', __name__, url_prefix='/api/forms')

@excel_export_bp.route('/<int:form_id>/export-excel', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def export_form_to_excel(form_id):
    """
    Export form submissions to Excel
    POST /api/forms/{form_id}/export-excel
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get form and validate access
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        # Check if user has access to this form
        if form.creator_id != user_id and user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get export options
        data = request.get_json() or {}
        export_options = {
            'date_range': data.get('date_range', {}),
            'filters': data.get('filters', {}),
            'include_metadata': data.get('include_metadata', True),
            'max_records': data.get('max_records', 10000)
        }
        
        # Check if immediate export is requested
        if data.get('immediate', False):
            # Generate Excel file immediately
            try:
                file_path, file_size = excel_export_service.export_form_submissions(
                    form_id, user_id, export_options
                )
                
                # Generate download URL
                base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
                download_url = f"{base_url}/api/forms/{form_id}/download-excel"
                
                return jsonify({
                    'success': True,
                    'message': 'Excel export completed',
                    'form_id': form_id,
                    'file_path': file_path,
                    'file_size': file_size,
                    'download_url': download_url,
                    'exported_at': datetime.utcnow().isoformat()
                }), 200
                
            except Exception as e:
                logger.error(f"Immediate Excel export failed for form {form_id}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Excel export failed: {str(e)}'
                }), 500
        
        else:
            # Start background export
            task_result = export_form_to_excel_task.delay(form_id, user_id, export_options)
            
            logger.info(f"Background Excel export started for form {form_id} by user {user_id}")
            
            return jsonify({
                'success': True,
                'message': 'Excel export started in background',
                'form_id': form_id,
                'task_id': task_result.id,
                'status': 'processing'
            }), 202
        
    except Exception as e:
        logger.error(f"Error starting Excel export for form {form_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start Excel export: {str(e)}'
        }), 500

@excel_export_bp.route('/<int:form_id>/download-excel', methods=['GET'])
@jwt_required()
def download_excel_export(form_id):
    """
    Download Excel export file
    GET /api/forms/{form_id}/download-excel
    """
    try:
        user_id = get_jwt_identity()
        
        # Get form and validate access
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        # Check if user has access to this form
        if form.creator_id != user_id:
            user = User.query.get(user_id)
            if not user or user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
                return jsonify({'error': 'Access denied'}), 403
        
        # Look for the most recent Excel export file
        export_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads/exports')
        if not os.path.exists(export_dir):
            return jsonify({'error': 'No exports available'}), 404
        
        # Find the most recent Excel file for this form
        excel_files = []
        for filename in os.listdir(export_dir):
            if filename.endswith('.xlsx') and f"Form_{form_id}" in filename:
                file_path = os.path.join(export_dir, filename)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    excel_files.append((file_path, file_stat.st_mtime))
        
        if not excel_files:
            return jsonify({'error': 'No Excel export found for this form'}), 404
        
        # Get the most recent file
        excel_files.sort(key=lambda x: x[1], reverse=True)
        latest_file_path = excel_files[0][0]
        
        # Generate filename
        filename = f"{form.title.replace(' ', '_')}_export_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        # Send file
        return send_file(
            latest_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Error downloading Excel export for form {form_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to download Excel export: {str(e)}'
        }), 500

@excel_export_bp.route('/<int:form_id>/export-status', methods=['GET'])
@jwt_required()
def get_export_status(form_id):
    """
    Get Excel export status
    GET /api/forms/{form_id}/export-status
    """
    try:
        user_id = get_jwt_identity()
        
        # Get form and validate access
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        # Check if user has access to this form
        if form.creator_id != user_id:
            user = User.query.get(user_id)
            if not user or user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
                return jsonify({'error': 'Access denied'}), 403
        
        # Check for available exports
        export_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads/exports')
        if not os.path.exists(export_dir):
            return jsonify({
                'success': True,
                'form_id': form_id,
                'status': 'no_exports',
                'message': 'No exports available'
            }), 200
        
        # Find Excel files for this form
        excel_files = []
        for filename in os.listdir(export_dir):
            if filename.endswith('.xlsx') and f"Form_{form_id}" in filename:
                file_path = os.path.join(export_dir, filename)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    excel_files.append({
                        'filename': filename,
                        'file_path': file_path,
                        'file_size': file_stat.st_size,
                        'created_at': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })
        
        # Sort by creation time (newest first)
        excel_files.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'form_id': form_id,
            'status': 'exports_available' if excel_files else 'no_exports',
            'exports': excel_files,
            'total_exports': len(excel_files)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting export status for form {form_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get export status: {str(e)}'
        }), 500

@excel_export_bp.route('/<int:form_id>/export-history', methods=['GET'])
@jwt_required()
@role_required([UserRole.ADMIN, UserRole.MANAGER])
def get_export_history(form_id):
    """
    Get Excel export history for a form
    GET /api/forms/{form_id}/export-history
    """
    try:
        user_id = get_jwt_identity()
        
        # Get form
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        # Get export options
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query for export history (you might want to create an ExportLog model)
        # For now, we'll return file system information
        export_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads/exports')
        if not os.path.exists(export_dir):
            return jsonify({
                'success': True,
                'form_id': form_id,
                'exports': [],
                'total': 0,
                'page': page,
                'per_page': per_page
            }), 200
        
        # Get all Excel files for this form
        excel_files = []
        for filename in os.listdir(export_dir):
            if filename.endswith('.xlsx') and f"Form_{form_id}" in filename:
                file_path = os.path.join(export_dir, filename)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    created_at = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    # Apply date filters if provided
                    if date_from:
                        try:
                            from_date = datetime.fromisoformat(date_from)
                            if created_at < from_date:
                                continue
                        except ValueError:
                            pass
                    
                    if date_to:
                        try:
                            to_date = datetime.fromisoformat(date_to)
                            if created_at > to_date:
                                continue
                        except ValueError:
                            pass
                    
                    excel_files.append({
                        'filename': filename,
                        'file_path': file_path,
                        'file_size': file_stat.st_size,
                        'created_at': created_at.isoformat(),
                        'download_url': f"/api/forms/{form_id}/download-excel"
                    })
        
        # Sort by creation time (newest first)
        excel_files.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply pagination
        total = len(excel_files)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_exports = excel_files[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'form_id': form_id,
            'exports': paginated_exports,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting export history for form {form_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get export history: {str(e)}'
        }), 500

@excel_export_bp.route('/bulk-export', methods=['POST'])
@jwt_required()
@role_required([UserRole.ADMIN, UserRole.MANAGER])
def bulk_export_forms():
    """
    Bulk export multiple forms to Excel
    POST /api/forms/bulk-export
    """
    try:
        user_id = get_jwt_identity()
        
        # Get request data
        data = request.get_json()
        if not data or 'form_ids' not in data:
            return jsonify({'error': 'No form IDs provided'}), 400
        
        form_ids = data['form_ids']
        if not isinstance(form_ids, list) or len(form_ids) == 0:
            return jsonify({'error': 'Invalid form IDs'}), 400
        
        # Validate form access
        accessible_forms = []
        for form_id in form_ids:
            form = Form.query.get(form_id)
            if form and (form.creator_id == user_id or 
                        User.query.get(user_id).role in [UserRole.ADMIN, UserRole.MANAGER]):
                accessible_forms.append(form_id)
        
        if not accessible_forms:
            return jsonify({'error': 'No accessible forms found'}), 403
        
        # Get export options
        export_options = data.get('export_options', {})
        
        # Start background export for each form
        task_results = []
        for form_id in accessible_forms:
            task_result = export_form_to_excel_task.delay(form_id, user_id, export_options)
            task_results.append({
                'form_id': form_id,
                'task_id': task_result.id
            })
        
        logger.info(f"Bulk Excel export started for {len(accessible_forms)} forms by user {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Bulk export started for {len(accessible_forms)} forms',
            'total_forms': len(accessible_forms),
            'accessible_forms': accessible_forms,
            'task_results': task_results,
            'status': 'processing'
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting bulk Excel export: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start bulk export: {str(e)}'
        }), 500
