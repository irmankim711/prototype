"""
Integration API routes for frontend compatibility
Provides placeholder endpoints for missing integration features
"""
from flask import Blueprint, jsonify

integrations_bp = Blueprint('integrations', __name__, url_prefix='/api/v1/integrations')

@integrations_bp.route('/excel/enhanced-export', methods=['GET', 'POST', 'OPTIONS'])
def enhanced_excel_export():
    """Enhanced Excel export functionality with proper data structure"""
    # Return expected data structure based on the frontend error message
    return jsonify({
        'fields': [
            {'name': 'id', 'type': 'number', 'label': 'ID'},
            {'name': 'name', 'type': 'string', 'label': 'Name'},
            {'name': 'email', 'type': 'email', 'label': 'Email'},
            {'name': 'date', 'type': 'date', 'label': 'Date'},
            {'name': 'status', 'type': 'string', 'label': 'Status'}
        ],
        'dataFields': [
            {'name': 'id', 'type': 'number', 'label': 'ID'},
            {'name': 'name', 'type': 'string', 'label': 'Name'},
            {'name': 'email', 'type': 'email', 'label': 'Email'},
            {'name': 'date', 'type': 'date', 'label': 'Date'},
            {'name': 'status', 'type': 'string', 'label': 'Status'}
        ],
        'columns': ['id', 'name', 'email', 'date', 'status'],
        'data': [],
        'message': 'Sample data structure for Excel integration',
        'status': 'success'
    }), 200

@integrations_bp.route('/excel/status', methods=['GET'])
def excel_export_status():
    """Status endpoint for Excel integration"""
    return jsonify({
        'service': 'excel_integration',
        'status': 'development',
        'features': ['basic_export', 'template_generation'],
        'coming_soon': ['enhanced_export', 'real_time_sync']
    }), 200