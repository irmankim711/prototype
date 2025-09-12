"""
Form Data Pipeline Routes
Handles webhook ingestion, manual exports, and data source management
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from typing import Dict, List, Optional, Any
import hmac
import hashlib
import json
from datetime import datetime, timedelta
import os

from ..models import (
    db, User, FormDataSource, FormDataSubmission, 
    ExcelExport, FormSyncLog
)
from ..utils.form_processors import FormProcessor
from ..tasks.excel_generation import generate_excel_export
from ..utils.validators import validate_webhook_signature
from ..utils.socket_events import emit_sync_update, emit_export_update

form_pipeline_bp = Blueprint('form_pipeline', __name__, url_prefix='/api/forms')

# ========== WEBHOOK ENDPOINTS ==========

@form_pipeline_bp.route('/webhook/<source_type>', methods=['POST'])
def webhook_handler(source_type: str):
    """
    Universal webhook handler for different form sources
    Supports: google_forms, microsoft_forms, zoho_forms, typeform, etc.
    """
    try:
        # Get request data
        webhook_data = request.get_json() or {}
        headers = dict(request.headers)
        
        current_app.logger.info(f"Received webhook from {source_type}: {webhook_data}")
        
        # Find data source by source_type and external identifier
        data_source = None
        
        if source_type == 'google_forms':
            form_id = webhook_data.get('formId') or headers.get('X-Goog-Resource-ID')
            data_source = FormDataSource.query.filter_by(
                source_type='google_forms',
                source_id=form_id,
                is_active=True
            ).first()
            
        elif source_type == 'microsoft_forms':
            form_id = webhook_data.get('formId') or webhook_data.get('resource', {}).get('id')
            data_source = FormDataSource.query.filter_by(
                source_type='microsoft_forms',
                source_id=form_id,
                is_active=True
            ).first()
            
        elif source_type == 'zoho_forms':
            form_id = webhook_data.get('formLinkName') or webhook_data.get('formId')
            data_source = FormDataSource.query.filter_by(
                source_type='zoho_forms',
                source_id=form_id,
                is_active=True
            ).first()
            
        elif source_type == 'typeform':
            form_id = webhook_data.get('form_response', {}).get('form_id')
            data_source = FormDataSource.query.filter_by(
                source_type='typeform',
                source_id=form_id,
                is_active=True
            ).first()
        
        if not data_source:
            current_app.logger.warning(f"No data source found for {source_type} webhook")
            return jsonify({
                'error': 'Data source not found',
                'source_type': source_type,
                'status': 'ignored'
            }), 404
        
        # Verify webhook signature if configured
        if data_source.webhook_secret:
            signature_header = headers.get('X-Hub-Signature-256') or headers.get('X-Webhook-Signature')
            if not validate_webhook_signature(
                data_source.webhook_secret, 
                request.data, 
                signature_header
            ):
                current_app.logger.warning(f"Invalid webhook signature for {source_type}")
                return jsonify({'error': 'Invalid signature'}), 403
        
        # Process the webhook data
        processor = FormProcessor(data_source)
        result = processor.process_webhook_data(webhook_data, headers)
        
        # Log the sync activity
        sync_log = FormSyncLog(
            data_source_id=data_source.id,
            sync_type='webhook',
            sync_status=result['status'],
            new_submissions=result.get('new_submissions', 0),
            updated_submissions=result.get('updated_submissions', 0),
            error_count=result.get('error_count', 0),
            sync_details=result.get('details', {}),
            error_details=result.get('errors', {})
        )
        db.session.add(sync_log)
        
        # Update last sync time
        data_source.last_sync = datetime.utcnow()
        db.session.commit()
        
        # Emit real-time update
        emit_sync_update(data_source.id, result)
        
        # Trigger auto-export if configured
        if data_source.auto_sync and result.get('new_submissions', 0) > 0:
            # Find auto-export configurations for this data source
            auto_exports = ExcelExport.query.filter(
                ExcelExport.data_sources.contains([data_source.id]),
                ExcelExport.is_auto_generated == True
            ).all()
            
            for export_config in auto_exports:
                generate_excel_export.delay(export_config.id, auto_trigger=True)
        
        return jsonify({
            'status': 'success',
            'message': f'Webhook processed successfully',
            'data_source_id': data_source.id,
            'result': result
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({
            'error': 'Webhook processing failed',
            'message': str(e)
        }), 500

@form_pipeline_bp.route('/webhook/test/<source_type>', methods=['POST'])
@jwt_required()
def test_webhook(source_type: str):
    """Test webhook endpoint for development"""
    try:
        user_id = get_jwt_identity()
        webhook_data = request.get_json() or {}
        
        # Create a test processor
        test_data_source = FormDataSource(
            name=f"Test {source_type.title()} Source",
            source_type=source_type,
            source_id="test_form_id",
            created_by=int(user_id)
        )
        
        processor = FormProcessor(test_data_source)
        result = processor.process_webhook_data(webhook_data, dict(request.headers))
        
        return jsonify({
            'status': 'test_success',
            'source_type': source_type,
            'processed_data': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== DATA SOURCE MANAGEMENT ==========

@form_pipeline_bp.route('/data-sources', methods=['GET'])
@jwt_required()
def get_data_sources():
    """Get all data sources for the current user"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        source_type = request.args.get('source_type')
        is_active = request.args.get('is_active')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Build query
        query = FormDataSource.query.filter_by(created_by=int(user_id))
        
        if source_type:
            query = query.filter_by(source_type=source_type)
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')
        
        # Paginate
        data_sources = query.order_by(FormDataSource.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'data_sources': [ds.to_dict() for ds in data_sources.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': data_sources.total,
                'pages': data_sources.pages,
                'has_next': data_sources.has_next,
                'has_prev': data_sources.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@form_pipeline_bp.route('/data-sources', methods=['POST'])
@jwt_required()
def create_data_source():
    """Create a new data source"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'source_type', 'source_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if data source already exists
        existing = FormDataSource.query.filter_by(
            source_type=data['source_type'],
            source_id=data['source_id']
        ).first()
        
        if existing:
            return jsonify({
                'error': 'Data source already exists',
                'existing_id': existing.id
            }), 409
        
        # Create new data source
        data_source = FormDataSource(
            name=data['name'],
            source_type=data['source_type'],
            source_id=data['source_id'],
            source_url=data.get('source_url'),
            webhook_secret=data.get('webhook_secret'),
            api_config=data.get('api_config', {}),
            field_mapping=data.get('field_mapping', {}),
            auto_sync=data.get('auto_sync', True),
            sync_interval=data.get('sync_interval', 300),
            created_by=int(user_id)
        )
        
        db.session.add(data_source)
        db.session.commit()
        
        return jsonify({
            'message': 'Data source created successfully',
            'data_source': data_source.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@form_pipeline_bp.route('/data-sources/<int:data_source_id>', methods=['PUT'])
@jwt_required()
def update_data_source(data_source_id: int):
    """Update a data source"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        data_source = FormDataSource.query.filter_by(
            id=data_source_id,
            created_by=int(user_id)
        ).first()
        
        if not data_source:
            return jsonify({'error': 'Data source not found'}), 404
        
        # Update allowed fields
        allowed_fields = [
            'name', 'source_url', 'webhook_secret', 'api_config',
            'field_mapping', 'is_active', 'auto_sync', 'sync_interval'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(data_source, field, data[field])
        
        data_source.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Data source updated successfully',
            'data_source': data_source.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@form_pipeline_bp.route('/data-sources/<int:data_source_id>/sync', methods=['POST'])
@jwt_required()
def manual_sync(data_source_id: int):
    """Manually trigger synchronization for a data source"""
    try:
        user_id = get_jwt_identity()
        
        data_source = FormDataSource.query.filter_by(
            id=data_source_id,
            created_by=int(user_id)
        ).first()
        
        if not data_source:
            return jsonify({'error': 'Data source not found'}), 404
        
        # Process manual sync
        processor = FormProcessor(data_source)
        result = processor.manual_sync()
        
        # Log the sync activity
        sync_log = FormSyncLog(
            data_source_id=data_source.id,
            sync_type='manual',
            sync_status=result['status'],
            new_submissions=result.get('new_submissions', 0),
            updated_submissions=result.get('updated_submissions', 0),
            error_count=result.get('error_count', 0),
            sync_details=result.get('details', {}),
            error_details=result.get('errors', {})
        )
        db.session.add(sync_log)
        
        # Update last sync time
        data_source.last_sync = datetime.utcnow()
        db.session.commit()
        
        # Emit real-time update
        emit_sync_update(data_source.id, result)
        
        return jsonify({
            'message': 'Manual sync completed',
            'result': result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== EXCEL EXPORT ENDPOINTS ==========

@form_pipeline_bp.route('/export', methods=['POST'])
@jwt_required()
def create_excel_export():
    """Create and trigger an Excel export"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Export name is required'}), 400
        
        if not data.get('data_sources'):
            return jsonify({'error': 'At least one data source must be selected'}), 400
        
        # Verify user owns the data sources
        data_source_ids = data['data_sources']
        user_data_sources = FormDataSource.query.filter(
            FormDataSource.id.in_(data_source_ids),
            FormDataSource.created_by == int(user_id)
        ).all()
        
        if len(user_data_sources) != len(data_source_ids):
            return jsonify({'error': 'Invalid data source selection'}), 403
        
        # Create export record
        export = ExcelExport(
            name=data['name'],
            description=data.get('description'),
            data_sources=data_source_ids,
            date_range_start=datetime.fromisoformat(data['date_range_start']) if data.get('date_range_start') else None,
            date_range_end=datetime.fromisoformat(data['date_range_end']) if data.get('date_range_end') else None,
            filters=data.get('filters', {}),
            template_config=data.get('template_config', {}),
            export_status='pending',
            created_by=int(user_id),
            is_auto_generated=data.get('is_auto_generated', False),
            auto_schedule=data.get('auto_schedule')
        )
        
        db.session.add(export)
        db.session.commit()
        
        # Trigger background export generation
        generate_excel_export.delay(export.id)
        
        return jsonify({
            'message': 'Excel export created and processing started',
            'export': export.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@form_pipeline_bp.route('/export', methods=['GET'])
@jwt_required()
def get_excel_exports():
    """Get Excel exports for the current user"""
    try:
        user_id = get_jwt_identity()
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        status = request.args.get('status')
        
        # Build query
        query = ExcelExport.query.filter_by(created_by=int(user_id))
        
        if status:
            query = query.filter_by(export_status=status)
        
        # Paginate
        exports = query.order_by(ExcelExport.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'exports': [export.to_dict() for export in exports.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': exports.total,
                'pages': exports.pages,
                'has_next': exports.has_next,
                'has_prev': exports.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@form_pipeline_bp.route('/export/<int:export_id>/download', methods=['GET'])
@jwt_required()
def download_excel_export(export_id: int):
    """Download a completed Excel export"""
    try:
        user_id = get_jwt_identity()
        
        export = ExcelExport.query.filter_by(
            id=export_id,
            created_by=int(user_id)
        ).first()
        
        if not export:
            return jsonify({'error': 'Export not found'}), 404
        
        if export.export_status != 'completed':
            return jsonify({
                'error': 'Export not completed',
                'status': export.export_status
            }), 400
        
        if not export.file_path or not os.path.exists(export.file_path):
            return jsonify({'error': 'Export file not found'}), 404
        
        return send_file(
            export.file_path,
            as_attachment=True,
            download_name=export.file_name or f"export_{export_id}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@form_pipeline_bp.route('/export/<int:export_id>', methods=['DELETE'])
@jwt_required()
def delete_excel_export(export_id: int):
    """Delete an Excel export and its file"""
    try:
        user_id = get_jwt_identity()
        
        export = ExcelExport.query.filter_by(
            id=export_id,
            created_by=int(user_id)
        ).first()
        
        if not export:
            return jsonify({'error': 'Export not found'}), 404
        
        # Delete file if it exists
        if export.file_path and os.path.exists(export.file_path):
            os.remove(export.file_path)
        
        # Delete database record
        db.session.delete(export)
        db.session.commit()
        
        return jsonify({'message': 'Export deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ========== DATA ANALYTICS ENDPOINTS ==========

@form_pipeline_bp.route('/analytics/summary', methods=['GET'])
@jwt_required()
def get_analytics_summary():
    """Get analytics summary for user's data sources"""
    try:
        user_id = get_jwt_identity()
        
        # Get user's data sources
        data_sources = FormDataSource.query.filter_by(created_by=int(user_id)).all()
        data_source_ids = [ds.id for ds in data_sources]
        
        if not data_source_ids:
            return jsonify({
                'total_data_sources': 0,
                'total_submissions': 0,
                'recent_submissions': 0,
                'active_exports': 0,
                'last_sync': None,
                'data_sources': []
            }), 200
        
        # Get submission counts
        total_submissions = FormDataSubmission.query.filter(
            FormDataSubmission.data_source_id.in_(data_source_ids)
        ).count()
        
        # Recent submissions (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_submissions = FormDataSubmission.query.filter(
            FormDataSubmission.data_source_id.in_(data_source_ids),
            FormDataSubmission.submitted_at >= recent_cutoff
        ).count()
        
        # Active exports
        active_exports = ExcelExport.query.filter(
            ExcelExport.created_by == int(user_id),
            ExcelExport.export_status.in_(['pending', 'processing'])
        ).count()
        
        # Last sync time
        last_sync = db.session.query(db.func.max(FormDataSource.last_sync)).filter(
            FormDataSource.created_by == int(user_id)
        ).scalar()
        
        return jsonify({
            'total_data_sources': len(data_sources),
            'total_submissions': total_submissions,
            'recent_submissions': recent_submissions,
            'active_exports': active_exports,
            'last_sync': last_sync.isoformat() if last_sync else None,
            'data_sources': [ds.to_dict() for ds in data_sources]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== ERROR HANDLERS ==========

@form_pipeline_bp.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Resource not found'}), 404

@form_pipeline_bp.errorhandler(403)
def handle_403(e):
    return jsonify({'error': 'Access forbidden'}), 403

@form_pipeline_bp.errorhandler(500)
def handle_500(e):
    return jsonify({'error': 'Internal server error'}), 500
