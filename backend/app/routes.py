from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db
from .services import report_service, ai_service
from .tasks import generate_report_task

api = Blueprint('api', __name__)

@api.route('/reports', methods=['POST'])
@jwt_required()
def create_report():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'template_id' not in data:
        return jsonify({'error': 'Missing template_id'}), 400
    
    # Queue report generation task
    task = generate_report_task.delay(user_id, data)
    
    return jsonify({
        'task_id': task.id,
        'status': 'processing'
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
