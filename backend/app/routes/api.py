from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from sqlalchemy.exc import SQLAlchemyError
from ..models import db, Report, ReportTemplate, User
from ..services.report_service import report_service
from ..services.ai_service import ai_service
from ..tasks import generate_report_task
from ..decorators import get_current_user_id
from docxtpl import DocxTemplate
import os
import logging
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
import traceback

api = Blueprint('api', __name__)
limiter = Limiter(key_func=get_remote_address)

TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))

def validate_json_data(data, required_fields=None, optional_fields=None):
    """Validate JSON data and return cleaned data"""
    if not data:
        raise BadRequest("No JSON data provided")
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")
    
    return data

def handle_database_error(error):
    """Handle database errors gracefully"""
    current_app.logger.error(f"Database error: {error}")
    return jsonify({'error': 'Database operation failed'}), 500

@api.route('/reports', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_reports():
    """Get all reports for the current user with pagination"""
    try:
        user_id = get_current_user_id()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)  # Max 100 per page
        status = request.args.get('status')
        
        if page < 1:
            return jsonify({'error': 'Page number must be positive'}), 400
        
        query = Report.query.filter_by(user_id=user_id)
        
        if status:
            valid_statuses = ['processing', 'completed', 'failed', 'pending']
            if status not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
            query = query.filter_by(status=status)
        
        reports = query.order_by(desc(Report.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'reports': [{
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'status': report.status,
                'createdAt': report.created_at.isoformat(),
                'updatedAt': report.updated_at.isoformat(),
                'templateId': report.template_id,
                'outputUrl': report.output_url
            } for report in reports.items],
            'pagination': {
                'page': reports.page,
                'pages': reports.pages,
                'per_page': reports.per_page,
                'total': reports.total,
                'has_next': reports.has_next,
                'has_prev': reports.has_prev
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_reports: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
@limiter.limit("200 per hour")
def get_report(report_id):
    """Get a specific report"""
    try:
        user_id = get_current_user_id()
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({
            'id': report.id,
            'title': report.title,
            'description': report.description,
            'status': report.status,
            'createdAt': report.created_at.isoformat(),
            'updatedAt': report.updated_at.isoformat(),
            'templateId': report.template_id,
            'data': report.data,
            'outputUrl': report.output_url
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/<int:report_id>', methods=['PUT'])
@jwt_required()
@limiter.limit("50 per hour")
def update_report(report_id):
    """Update a specific report"""
    try:
        user_id = get_current_user_id()
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        data = validate_json_data(request.get_json(), optional_fields=['title', 'description', 'data'])
        
        if 'title' in data:
            if not data['title'] or len(data['title'].strip()) == 0:
                return jsonify({'error': 'Title cannot be empty'}), 400
            report.title = data['title'].strip()
            
        if 'description' in data:
            report.description = data['description']
            
        if 'data' in data:
            if not isinstance(data['data'], dict):
                return jsonify({'error': 'Data must be a JSON object'}), 400
            report.data = data['data']
        
        report.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Report updated successfully'}), 200
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in update_report: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/<int:report_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("30 per hour")
def delete_report(report_id):
    """Delete a specific report"""
    try:
        user_id = get_current_user_id()
        report = Report.query.filter_by(id=report_id, user_id=user_id).first()
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Delete associated files if they exist
        if report.output_url:
            try:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], report.output_url)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                current_app.logger.warning(f"Could not delete file {report.output_url}: {e}")
        
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({'message': 'Report deleted successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in delete_report: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports', methods=['POST'])
@jwt_required()
@limiter.limit("20 per hour")
def create_report():
    """Create a new report"""
    try:
        user_id = get_current_user_id()
        data = validate_json_data(
            request.get_json(), 
            required_fields=['title'],
            optional_fields=['description', 'template_id', 'data']
        )
        
        # Validate title
        if not data['title'] or len(data['title'].strip()) == 0:
            return jsonify({'error': 'Title cannot be empty'}), 400
        
        # Validate template_id if provided
        if 'template_id' in data and data['template_id']:
            template = ReportTemplate.query.get(data['template_id'])
            if not template:
                return jsonify({'error': 'Template not found'}), 404
        
        # Create report record
        report = Report(
            title=data['title'].strip(),
            description=data.get('description', ''),
            user_id=user_id,
            template_id=data.get('template_id'),
            data=data.get('data', {}),
            status='processing'
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Add report_id to task data
        task_data = {**data, 'report_id': report.id}
        
        # Queue report generation task
        try:
            task = generate_report_task.delay(user_id, task_data)
            task_id = task.id
        except Exception as e:
            current_app.logger.error(f"Failed to queue task: {e}")
            report.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'Failed to queue report generation'}), 500
        
        return jsonify({
            'report_id': report.id,
            'task_id': task_id,
            'status': 'processing',
            'message': 'Report creation initiated'
        }), 202
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in create_report: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/recent', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_recent_reports():
    """Get recent reports for the current user"""
    try:
        user_id = get_current_user_id()
        limit = min(request.args.get('limit', 5, type=int), 50)  # Max 50
        
        reports = Report.query.filter_by(user_id=user_id)\
            .order_by(desc(Report.created_at))\
            .limit(limit)\
            .all()
        
        return jsonify([{
            'id': report.id,
            'title': report.title,
            'status': report.status,
            'createdAt': report.created_at.isoformat(),
            'updatedAt': report.updated_at.isoformat(),
            'templateId': report.template_id,
            'outputUrl': report.output_url
        } for report in reports]), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_recent_reports: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/stats', methods=['GET'])
@jwt_required()
@limiter.limit("50 per hour")
def get_report_stats():
    """Get report statistics for the current user"""
    try:
        user_id = get_current_user_id()
        
        total = Report.query.filter_by(user_id=user_id).count()
        completed = Report.query.filter_by(user_id=user_id, status='completed').count()
        processing = Report.query.filter_by(user_id=user_id, status='processing').count()
        failed = Report.query.filter_by(user_id=user_id, status='failed').count()
        
        # Reports created this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        this_week = Report.query.filter(
            Report.user_id == user_id,
            Report.created_at >= week_ago
        ).count()
        
        success_rate = round((completed / total * 100) if total > 0 else 0, 1)
        
        return jsonify({
            'totalReports': total,
            'completedReports': completed,
            'processingReports': processing,
            'failedReports': failed,
            'reportsThisWeek': this_week,
            'successRate': success_rate
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_report_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/<task_id>/status', methods=['GET'])
@jwt_required()
@limiter.limit("200 per hour")
def get_report_status(task_id):
    """Get the status of a report generation task"""
    try:
        task = generate_report_task.AsyncResult(task_id)
        response = {
            'task_id': task_id,
            'status': task.status,
        }
        
        if task.status == 'PENDING':
            response['message'] = 'Task is pending'
        elif task.status == 'PROGRESS':
            response['message'] = 'Task is in progress'
            response['info'] = task.info
        elif task.status == 'SUCCESS':
            response['message'] = 'Task completed successfully'
            response['result'] = task.result
        elif task.status == 'FAILURE':
            response['message'] = 'Task failed'
            response['error'] = str(task.info)
        
        return jsonify(response), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_report_status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/templates', methods=['GET'])
@jwt_required()
@limiter.limit("100 per hour")
def get_report_templates():
    """Get available report templates"""
    try:
        templates = ReportTemplate.query.all()
        return jsonify([{
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'createdAt': template.created_at.isoformat()
        } for template in templates]), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_report_templates: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/ai/analyze', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def analyze_data():
    """Analyze data using AI"""
    try:
        data = validate_json_data(
            request.get_json(),
            required_fields=['data'],
            optional_fields=['analysis_type', 'prompt']
        )
        
        # Validate data size
        if len(str(data['data'])) > 10000:  # 10KB limit
            return jsonify({'error': 'Data too large for analysis'}), 400
        
        # Perform AI analysis
        result = ai_service.analyze_data(
            data['data'],
            analysis_type=data.get('analysis_type', 'general'),
            prompt=data.get('prompt')
        )
        
        return jsonify({
            'analysis': result,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except BadRequest as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in analyze_data: {str(e)}")
        return jsonify({'error': 'Analysis failed'}), 500

# Error handlers for this blueprint
@api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@api.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@api.errorhandler(500)
def internal_error(error):
    current_app.logger.error(f"API Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
