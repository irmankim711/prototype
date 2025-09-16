from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db
from .services import report_service
from .services.ai_service import get_ai_service
from .tasks import generate_report_task

api = Blueprint('api', __name__)

from .models import Report, User
@api.route('/reports', methods=['POST'])
@jwt_required()
def create_report():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()
    data = request.get_json()

    if not data or 'template_id' not in data:
        return jsonify({'error': 'Missing template_id'}), 400
    
    # Create a new report record
    new_report = Report(
        title=data.get('title'),
        report_type=data.get('report_type'),
        user_id=user.id,
        status='processing'
    )
    db.session.add(new_report)
    db.session.commit()

    # Add the report_id to the data payload for the task
    data['report_id'] = new_report.id

    # Queue report generation task
    task = generate_report_task.delay(user.id, data)
    
    return jsonify({
        'task_id': task.id,
        'status': 'processing',
        'report_id': new_report.id
    }), 202

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

# @api.route('/reports/templates', methods=['GET'])
# @jwt_required()
# def get_report_templates():
#     templates = report_service.get_templates()
#     return jsonify(templates)

@api.route('/ai/analyze', methods=['POST'])
@jwt_required()
def analyze_data():
    data = request.get_json()
    analysis = get_ai_service().analyze_data(data)
    return jsonify(analysis)
