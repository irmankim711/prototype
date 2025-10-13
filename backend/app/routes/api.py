from flask import Blueprint, request, jsonify, current_app, redirect
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from datetime import datetime, timedelta
from sqlalchemy import desc, func, or_
from sqlalchemy.exc import SQLAlchemyError
from .. import celery
from .. import db
from ..models import Report, ReportTemplate, User
from ..services.unified_report_service import unified_report_service
from ..services.ai_service import ai_service
try:
    from ..services.google_forms_service import google_forms_service
    GOOGLE_FORMS_ENABLED = google_forms_service is not None
    print(f"Google Forms service status: {'Enabled' if GOOGLE_FORMS_ENABLED else 'Disabled'}")
except (ImportError, ValueError) as e:
    google_forms_service = None
    GOOGLE_FORMS_ENABLED = False
    print(f"⚠️ Google Forms routes disabled - {str(e)}")
from ..decorators import get_current_user_id
from ..middleware.firebase_auth import firebase_auth_manager
from docxtpl import DocxTemplate
import os
import logging
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
import traceback

api = Blueprint('api', __name__)
limiter = Limiter(key_func=get_remote_address)

TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../templates'))

# Authentication: Verify Firebase ID token and create a backend session
@api.route('/auth/firebase-sync', methods=['POST'])
@limiter.limit("30 per minute")
def firebase_sync():
    """Verify Firebase ID token and establish a session.

    Accepts the token either in the Authorization header as
    "Bearer <idToken>" or in the JSON body as { "idToken": "..." }.
    """
    try:
        # Prefer Authorization header
        auth_header = request.headers.get('Authorization', '')
        id_token = None

        if auth_header.startswith('Bearer '):
            id_token = auth_header.replace('Bearer ', '').strip()
        elif request.is_json:
            data = request.get_json(silent=True) or {}
            id_token = (data.get('idToken') or data.get('token') or '').strip()

        if not id_token:
            return jsonify({
                'error': 'Missing Firebase ID token',
                'code': 'MISSING_ID_TOKEN'
            }), 400

        # Ensure Firebase Admin is initialized
        if not getattr(firebase_auth_manager, '_initialized', False):
            current_app.logger.error('Firebase Admin SDK not initialized')
            return jsonify({
                'error': 'Authentication service unavailable',
                'code': 'AUTH_SERVICE_UNAVAILABLE'
            }), 503

        # Verify token
        decoded = firebase_auth_manager.verify_token(id_token)
        if not decoded:
            return jsonify({
                'error': 'Invalid or expired Firebase token',
                'code': 'INVALID_FIREBASE_TOKEN'
            }), 401

        # Sync or create user
        user = firebase_auth_manager.get_or_create_user(decoded)
        if not user:
            current_app.logger.error('Failed to create/sync user from Firebase token')
            return jsonify({
                'error': 'User synchronization failed',
                'code': 'USER_SYNC_FAILED'
            }), 500

        # Prepare response
        resp = jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, 'username', None),
                'first_name': getattr(user, 'first_name', None),
                'last_name': getattr(user, 'last_name', None),
                'display_name': getattr(user, 'display_name', None),
                'firebase_uid': getattr(user, 'firebase_uid', None),
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role) if getattr(user, 'role', None) else 'user'
            }
        })

        # Issue an HttpOnly cookie for session continuity (client may still use Authorization header)
        # Note: This stores the Firebase ID token for session continuity; adjust strategy as needed.
        secure_cookie = not current_app.config.get('DEBUG', False)
        resp.set_cookie(
            'access_token_cookie',
            id_token,
            max_age=60 * 60,  # 1 hour
            httponly=True,
            secure=secure_cookie,
            samesite='Lax'
        )

        return resp, 200

    except Exception as e:
        current_app.logger.error(f"/api/auth/firebase-sync error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

# Add route for automated reports list
@api.route('/automated-reports', methods=['GET'])
def get_automated_reports():
    """Get all automated reports for the current user"""
    try:
        user_id = get_current_user_id()
        
        # Get reports with pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        reports_query = Report.query.filter_by(user_id=user_id).order_by(desc(Report.updated_at))
        
        # Add filtering
        status_filter = request.args.get('status')
        if status_filter:
            reports_query = reports_query.filter(Report.status == status_filter)
        
        type_filter = request.args.get('type')
        if type_filter:
            reports_query = reports_query.filter(Report.type == type_filter)
        
        reports = reports_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Convert to enhanced format
        enhanced_reports = []
        for report in reports.items:
            report_data = {
                'id': report.id,
                'title': report.title,
                'description': report.description,
                'content': getattr(report, 'content', ''),
                'status': report.status,
                'type': getattr(report, 'type', 'summary'),
                'data_source': getattr(report, 'data_source', 'unknown'),
                'source_id': getattr(report, 'source_id', ''),
                'created_at': report.created_at.isoformat(),
                'updated_at': report.updated_at.isoformat(),
                'generated_by_ai': getattr(report, 'generated_by_ai', False),
                'ai_suggestions': getattr(report, 'ai_suggestions', []),
                'download_formats': ['pdf', 'word', 'excel', 'html'],
                'metrics': {
                    'total_responses': getattr(report, 'total_responses', 0),
                    'completion_rate': getattr(report, 'completion_rate', 0.0),
                    'avg_response_time': getattr(report, 'avg_response_time', 0.0),
                }
            }
            enhanced_reports.append(report_data)
        
        return jsonify(enhanced_reports)
        
    except Exception as e:
        current_app.logger.error(f"Error getting automated reports: {str(e)}")
        return jsonify({'error': 'Failed to get reports'}), 500

def handle_google_form_report_generation(user_id, data):
    """Handle report generation for Google Forms"""
    try:
        # Check if Google Forms service is available
        if not GOOGLE_FORMS_ENABLED or not google_forms_service:
            return jsonify({
                'error': 'Google Forms service not configured',
                'message': 'Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET'
            }), 503
        
        google_form_id = data.get('google_form_id')
        if not google_form_id:
            return jsonify({'error': 'google_form_id is required for Google Form reports'}), 400
        
        # Initialize Google Forms service
        google_service = google_forms_service
        
        # For now, create a placeholder report
        # In a full implementation, you'd generate the actual report from Google Forms data
        title = f"Google Form Report - {google_form_id}"
        description = f"Generated report from Google Form {google_form_id}"
        
        # Create report record (using column assignments)
        report = Report()
        report.title = title
        report.description = description
        report.user_id = user_id
        report.data = {
            'google_form_id': google_form_id,
            'report_type': data.get('report_type'),
            'date_range': data.get('date_range', 'all_time'),
            'form_source': 'google_form'
        }
        report.status = 'completed'  # For now, mark as completed immediately
        
        db.session.add(report)
        db.session.commit()
        
        return jsonify({
            'message': 'Google Form report created successfully',
            'report_id': report.id,
            'status': 'completed'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating Google Form report: {str(e)}")
        return jsonify({'error': 'Failed to create Google Form report'}), 500

def validate_json_data(data, required_fields=None, optional_fields=None):
    """Validate JSON data and return cleaned data"""
    if not data:
        raise BadRequest("No JSON data provided")
    
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")
    
    return data

def handle_report_generation(user_id, data):
    """Handle report generation requests from ReportBuilder"""
    try:
        # Validate required fields for report generation
        required_fields = ['form_id', 'report_type']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        
        if missing_fields:
            current_app.logger.error(f"Missing required fields: {missing_fields}")
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Validate form_id
        form_id = data.get('form_id')
        if not isinstance(form_id, int) or form_id <= 0:
            current_app.logger.error(f"Invalid form_id: {form_id}")
            return jsonify({'error': 'form_id must be a positive integer'}), 400
        
        # Validate report_type
        report_type = data.get('report_type')
        valid_report_types = ['summary', 'detailed', 'analytics', 'export']
        if report_type not in valid_report_types:
            current_app.logger.error(f"Invalid report_type: {report_type}")
            return jsonify({'error': f'report_type must be one of: {", ".join(valid_report_types)}'}), 400
        
        # Validate date_range (optional)
        date_range = data.get('date_range', 'all_time')
        valid_date_ranges = ['last_7_days', 'last_30_days', 'last_90_days', 'all_time']
        if date_range not in valid_date_ranges:
            current_app.logger.error(f"Invalid date_range: {date_range}")
            return jsonify({'error': f'date_range must be one of: {", ".join(valid_date_ranges)}'}), 400
        
        # Check if this is a Google Form report
        form_source = data.get('form_source', 'internal')  # 'internal' or 'google_form'
        
        if form_source == 'google_form':
            # Handle Google Form report generation
            return handle_google_form_report_generation(user_id, data)
        
        # Create a report record with generated title
        title = f"{report_type.title()} Report for Form {form_id}"
        description = f"Generated {report_type} report for form {form_id} covering {date_range.replace('_', ' ')}"
        
        report = Report(
            title=title,
            description=description,
            user_id=user_id,
            data={
                'form_id': form_id,
                'report_type': report_type,
                'date_range': date_range,
                'generated_at': datetime.utcnow().isoformat()
            },
            status='processing'
        )
        
        db.session.add(report)
        db.session.commit()
        
        current_app.logger.info(f"Created report {report.id} for user {user_id}")
        
        # For now, return a success response
        # In a real implementation, you would queue a background task here
        return jsonify({
            'report_id': report.id,
            'status': 'processing',
            'message': f'Report generation initiated for form {form_id}',
            'form_id': form_id,
            'report_type': report_type,
            'date_range': date_range
        }), 202
        
    except Exception as e:
        current_app.logger.error(f"Error in handle_report_generation: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to process report generation request'}), 500

def handle_database_error(error):
    """Handle database errors gracefully"""
    current_app.logger.error(f"Database error: {error}")
    return jsonify({'error': 'Database operation failed'}), 500

@api.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint to verify the API is working"""
    return jsonify({
        'message': 'API is working!',
        'status': 'success',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@api.route('/reports', methods=['GET'])
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
        
        # Handle case when no user is authenticated (for testing)
        if user_id is None:
            # Return empty reports list for unauthenticated users
            return jsonify({
                'reports': [],
                'pagination': {
                    'page': page,
                    'pages': 0,
                    'per_page': per_page,
                    'total': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }), 200
        
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
@limiter.limit("20 per hour")
def create_report():
    """Create a new report"""
    try:
        user_id = get_current_user_id()
        
        # Log the incoming request for debugging
        raw_data = request.get_json()
        current_app.logger.info(f"Received report creation request: {raw_data}")
        
        # Check if this is a report generation request (from ReportBuilder)
        if raw_data and 'form_id' in raw_data and 'report_type' in raw_data:
            # Handle report generation request
            return handle_report_generation(user_id, raw_data)
        
        # Handle traditional report creation
        data = validate_json_data(
            raw_data, 
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
            task = celery.send_task('app.tasks.report_tasks.generate_report_task', args=[user_id, task_data])
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
        current_app.logger.error(f"BadRequest in create_report: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error in create_report: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/recent', methods=['GET'])
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

@api.route('/reports/history', methods=['GET'])
@limiter.limit("100 per hour")
def get_reports_history():
    """Get reports history for the current user with pagination and filtering"""
    try:
        user_id = get_current_user_id()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        
        if page < 1:
            return jsonify({'error': 'Page number must be positive'}), 400
        
        query = Report.query.filter_by(user_id=user_id)
        
        # Filter by status if provided
        if status:
            valid_statuses = ['processing', 'completed', 'failed', 'pending', 'draft']
            if status not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
            query = query.filter_by(status=status)
        
        # Filter by search term if provided
        if search:
            query = query.filter(
                or_(
                    Report.title.ilike(f'%{search}%'),
                    Report.description.ilike(f'%{search}%')
                )
            )
        
        # Order by creation date (newest first) and paginate
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
                'updatedAt': report.updated_at.isoformat() if report.updated_at else report.created_at.isoformat(),
                'templateId': report.template_id,
                'outputUrl': report.output_url,
                'data': report.data  # Include the form data used to generate the report
            } for report in reports.items],
            'pagination': {
                'page': reports.page,
                'pages': reports.pages,
                'per_page': reports.per_page,
                'total': reports.total,
                'has_next': reports.has_next,
                'has_prev': reports.has_prev
            },
            'filters': {
                'status': status,
                'search': search
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in get_reports_history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/reports/stats', methods=['GET'])
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
@limiter.limit("200 per hour")
def get_report_status(task_id):
    """Get the status of a report generation task"""
    try:
        task = celery.AsyncResult(task_id)
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

# Google Forms API Endpoints
if GOOGLE_FORMS_ENABLED and google_forms_service:
    @api.route('/google-forms/auth', methods=['GET'])
    def google_forms_auth():
        """Initiate Google Forms OAuth flow"""
        try:
            user_id = get_current_user_id()
            google_service = google_forms_service
            
            # Get OAuth URL
            auth_url = google_service.get_authorization_url(user_id)
            
            return jsonify({
                'auth_url': auth_url,
                'message': 'Please visit the URL to authorize access to Google Forms'
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Error initiating Google Forms auth: {str(e)}")
            return jsonify({'error': 'Failed to initiate Google Forms authentication'}), 500
else:
    @api.route('/google-forms/auth', methods=['GET'])
    def google_forms_auth_disabled():
        return jsonify({
            'error': 'Google Forms service not configured',
            'message': 'Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET'
        }), 503

if GOOGLE_FORMS_ENABLED and google_forms_service:
    @api.route('/google-forms/callback', methods=['GET'])
    def google_forms_callback():
        """Handle Google Forms OAuth callback"""
        try:
            user_id = get_current_user_id()
            code = request.args.get('code')
            
            if not code:
                return jsonify({'error': 'Authorization code not provided'}), 400
            
            google_service = google_forms_service
            
            # Exchange code for tokens
            success = google_service.handle_oauth_callback(code, user_id)
            
            if success:
                return jsonify({
                    'message': 'Google Forms authorization successful',
                    'status': 'authorized'
                }), 200
            else:
                return jsonify({'error': 'Failed to authorize Google Forms access'}), 400
                
        except Exception as e:
            current_app.logger.error(f"Error handling Google Forms callback: {str(e)}")
            return jsonify({'error': 'Failed to complete Google Forms authorization'}), 500
else:
    @api.route('/google-forms/callback', methods=['GET'])
    def google_forms_callback_disabled():
        return jsonify({
            'error': 'Google Forms service not configured',
            'message': 'Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET'
        }), 503

if GOOGLE_FORMS_ENABLED and google_forms_service:
    @api.route('/google-forms/forms', methods=['GET'])
    def get_google_forms():
        """Get list of user's Google Forms"""
        try:
            user_id = get_current_user_id()
            google_service = google_forms_service
            
            # Get user's forms
            forms = google_service.get_user_forms(user_id)
            
            return jsonify({
                'forms': forms,
                'total': len(forms)
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching Google Forms: {str(e)}")
            return jsonify({'error': 'Failed to fetch Google Forms'}), 500
else:
    @api.route('/google-forms/forms', methods=['GET'])
    def get_google_forms_disabled():
        return jsonify({
            'error': 'Google Forms service not configured',
            'message': 'Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET'
        }), 503

if GOOGLE_FORMS_ENABLED and google_forms_service:
    @api.route('/google-forms/<form_id>/responses', methods=['GET'])
    def get_google_form_responses(form_id):
        """Get responses for a specific Google Form"""
        try:
            user_id = get_current_user_id()
            google_service = google_forms_service
            
            # Get form responses
            responses = google_service.get_form_responses(user_id, form_id)
            
            return jsonify({
                'form_id': form_id,
                'responses': responses,
                'total': len(responses)
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching Google Form responses: {str(e)}")
            return jsonify({'error': 'Failed to fetch Google Form responses'}), 500
else:
    @api.route('/google-forms/<form_id>/responses', methods=['GET'])
    def get_google_form_responses_disabled(form_id):
        return jsonify({
            'error': 'Google Forms service not configured',
            'message': 'Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET'
        }), 503

if GOOGLE_FORMS_ENABLED and google_forms_service:
    @api.route('/google-forms/<form_id>/analytics', methods=['GET'])
    def get_google_form_analytics(form_id):
        """Generate analytics for a specific Google Form"""
        try:
            user_id = get_current_user_id()
            google_service = google_forms_service
            
            # Generate analytics
            analytics = google_service.generate_form_analytics(user_id, form_id)
            
            return jsonify({
                'form_id': form_id,
                'analytics': analytics
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"Error generating Google Form analytics: {str(e)}")
            return jsonify({'error': 'Failed to generate Google Form analytics'}), 500
else:
    @api.route('/google-forms/<form_id>/analytics', methods=['GET'])
    def get_google_form_analytics_disabled(form_id):
        return jsonify({
            'error': 'Google Forms service not configured',
            'message': 'Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET'
        }), 503

@api.route('/reports/export/pdf/<int:report_id>', methods=['GET'])
def export_report_pdf(report_id):
    """Export report as PDF"""
    try:
        from flask import send_file
        from ..services.report_generator import create_pdf_report, format_report_data_for_pdf
        
        # Get current user
        user_id = get_current_user_id()
        
        # Fetch report data
        report = Report.query.filter_by(
            id=report_id, 
            user_id=user_id
        ).first_or_404()
        
        # Prepare data for PDF
        report_data = {
            'form_name': getattr(report, 'title', 'Report'),
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_name': report.author.full_name if report.author else 'System',
            'entry_count': 0,
            'table_data': format_report_data_for_pdf(report),
            'response_rate': 0.0,
            'title': report.title or 'Report',
            'description': report.description or '',
        }
        
        # Add statistics if available
        if report.data and isinstance(report.data, dict):
            if 'statistics' in report.data:
                report_data['statistics'] = report.data['statistics']
            if 'ai_insights' in report.data:
                report_data['ai_insights'] = report.data['ai_insights']
            if 'entry_count' in report.data:
                report_data['entry_count'] = report.data['entry_count']
            if 'response_rate' in report.data:
                report_data['response_rate'] = report.data['response_rate']
        
        # Generate PDF
        pdf_filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Use uploads directory
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        pdf_dir = os.path.join(upload_folder, 'pdfs')
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        
        # Create PDF
        pdf_path = create_pdf_report('form_analysis', report_data, pdf_path)
        
        # Return file as download
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype='application/pdf'
        )
        
    except ImportError as e:
        current_app.logger.error(f"PDF generation library error: {e}")
        return jsonify({'error': 'PDF generation not available. Please install required libraries.'}), 500
    except Exception as e:
        current_app.logger.error(f"PDF export error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate PDF'}), 500

@api.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@api.errorhandler(500)
def internal_error(error):
    current_app.logger.error(f"API Error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
