from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from .models import db, Report, ReportTemplate, User, Form, FormSubmission
from .services import report_service, ai_service
from .tasks import generate_report_task, generate_automated_report_task
import json
import uuid

api = Blueprint('api', __name__)

@api.route('/reports', methods=['GET'])
@jwt_required()
def get_reports():
    """Get all reports for the current user with pagination"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    
    query = Report.query.filter_by(user_id=user_id)
    
    if status:
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
            'total': reports.total
        }
    }), 200

@api.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """Get a specific report"""
    user_id = get_jwt_identity()
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

@api.route('/reports/<int:report_id>', methods=['PUT'])
@jwt_required()
def update_report(report_id):
    """Update a specific report"""
    user_id = get_jwt_identity()
    report = Report.query.filter_by(id=report_id, user_id=user_id).first()
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    data = request.get_json()
    
    if 'title' in data:
        report.title = data['title']
    if 'description' in data:
        report.description = data['description']
    if 'data' in data:
        report.data = data['data']
    
    report.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Report updated successfully'}), 200

@api.route('/reports/<int:report_id>', methods=['DELETE'])
@jwt_required()
def delete_report(report_id):
    """Delete a specific report"""
    user_id = get_jwt_identity()
    report = Report.query.filter_by(id=report_id, user_id=user_id).first()
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    db.session.delete(report)
    db.session.commit()
    
    return jsonify({'message': 'Report deleted successfully'}), 200

@api.route('/reports', methods=['POST'])
@jwt_required()
def create_report():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Create report record first
    report = Report(
        title=data.get('title', 'New Report'),
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
    task = generate_report_task.delay(user_id, task_data)
    
    return jsonify({
        'report_id': report.id,
        'task_id': task.id,
        'status': 'processing'
    }), 202

@api.route('/reports/recent', methods=['GET'])
@jwt_required()
def get_recent_reports():
    """Get recent reports for the current user"""
    user_id = get_jwt_identity()
    limit = request.args.get('limit', 5, type=int)
    
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

@api.route('/reports/stats', methods=['GET'])
@jwt_required()
def get_report_stats():
    """Get report statistics for the current user"""
    user_id = get_jwt_identity()
    
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
    
    return jsonify({
        'totalReports': total,
        'completedReports': completed,
        'processingReports': processing,
        'failedReports': failed,
        'reportsThisWeek': this_week,
        'successRate': round((completed / total * 100) if total > 0 else 0, 1)
    }), 200

@api.route('/reports/<task_id>', methods=['GET'])
@jwt_required()
def get_report_status(task_id):
    task = generate_report_task.AsyncResult(task_id)
    response = {
        'task_id': task_id,
        'status': task.status,
    }
    if task.status == 'SUCCESS':
        response['result'] = task.get()
    return jsonify(response)

@api.route('/reports/templates', methods=['GET'])
@jwt_required()
def get_report_templates():
    templates = report_service.get_templates()
    return jsonify(templates)

@api.route('/ai/analyze', methods=['POST'])
@jwt_required()
def analyze_data():
    data = request.get_json()
    analysis = ai_service.analyze_data(data)
    return jsonify(analysis)

@api.route('/forms/submit', methods=['POST'])
def submit_form_data():
    """Handle form submissions from external sources and trigger automated reports"""
    try:
        data = request.get_json()
        
        # Extract form information
        form_id = data.get('form_id')
        form_data = data.get('data', {})
        submitter_info = data.get('submitter', {})
        source = data.get('source', 'external')  # google_forms, microsoft_forms, custom
        
        # Validate required fields
        if not form_id or not form_data:
            return jsonify({'error': 'Missing required fields: form_id and data'}), 400
        
        # Get or create form
        form = Form.query.get(form_id)
        if not form:
            return jsonify({'error': 'Form not found'}), 404
        
        # Create form submission
        submission = FormSubmission(
            form_id=form_id,
            data=form_data,
            submitter_email=submitter_info.get('email'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            submission_source=source,
            submitted_at=datetime.utcnow()
        )
        
        db.session.add(submission)
        db.session.commit()
        
        # Trigger automated report generation if form has auto-report enabled
        if form.form_settings and form.form_settings.get('auto_generate_reports'):
            # Queue automated report generation task
            task = generate_automated_report_task.delay(
                form_id=form_id,
                submission_id=submission.id,
                trigger_type='form_submission'
            )
            
            return jsonify({
                'message': 'Form submitted successfully',
                'submission_id': submission.id,
                'report_task_id': task.id,
                'auto_report_triggered': True
            }), 201
        
        return jsonify({
            'message': 'Form submitted successfully',
            'submission_id': submission.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to submit form: {str(e)}'}), 500

@api.route('/forms/<int:form_id>/submissions', methods=['GET'])
@jwt_required()
def get_form_submissions(form_id):
    """Get all submissions for a specific form"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Check if user has access to this form
    form = Form.query.filter_by(id=form_id, creator_id=user_id).first()
    if not form:
        return jsonify({'error': 'Form not found or access denied'}), 404
    
    submissions = FormSubmission.query.filter_by(form_id=form_id)\
        .order_by(desc(FormSubmission.submitted_at))\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'submissions': [{
            'id': sub.id,
            'data': sub.data,
            'submitter_email': sub.submitter_email,
            'submitted_at': sub.submitted_at.isoformat(),
            'status': sub.status,
            'source': sub.submission_source
        } for sub in submissions.items],
        'pagination': {
            'page': submissions.page,
            'pages': submissions.pages,
            'per_page': submissions.per_page,
            'total': submissions.total
        }
    }), 200

@api.route('/reports/automated/generate', methods=['POST'])
@jwt_required()
def trigger_automated_report():
    """Manually trigger automated report generation for a form"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    form_id = data.get('form_id')
    report_type = data.get('report_type', 'summary')  # summary, detailed, trends
    date_range = data.get('date_range', 'last_30_days')
    
    if not form_id:
        return jsonify({'error': 'form_id is required'}), 400
    
    # Check if user has access to this form
    form = Form.query.filter_by(id=form_id, creator_id=user_id).first()
    if not form:
        return jsonify({'error': 'Form not found or access denied'}), 404
    
    # Queue automated report generation
    task = generate_automated_report_task.delay(
        form_id=form_id,
        report_type=report_type,
        date_range=date_range,
        trigger_type='manual',
        user_id=user_id
    )
    
    return jsonify({
        'message': 'Automated report generation started',
        'task_id': task.id,
        'form_id': form_id,
        'report_type': report_type
    }), 202

@api.route('/reports/automated/status/<task_id>', methods=['GET'])
@jwt_required()
def get_automated_report_status(task_id):
    """Get status of automated report generation task"""
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    if result.ready():
        if result.successful():
            return jsonify({
                'status': 'completed',
                'result': result.result
            }), 200
        else:
            return jsonify({
                'status': 'failed',
                'error': str(result.result)
            }), 200
    else:
        return jsonify({
            'status': 'processing',
            'task_id': task_id
        }), 200
