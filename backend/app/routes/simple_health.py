"""
Simple Health Check Endpoint
Lightweight health check that doesn't require database connection
"""

from flask import Blueprint, jsonify
from datetime import datetime

# Create blueprint without URL prefix for root health check
simple_health_bp = Blueprint('simple_health', __name__)

@simple_health_bp.route('/health', methods=['GET'])
@simple_health_bp.route('/api/health', methods=['GET'])
def simple_health():
    """
    Simple health check endpoint that returns immediately
    GET /health or /api/health
    """
    return jsonify({
        'status': 'healthy',
        'service': 'automated_report_platform',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

@simple_health_bp.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Automated Report Platform API',
        'status': 'running',
        'version': '1.0.0',
        'docs': '/api/docs'
    }), 200
