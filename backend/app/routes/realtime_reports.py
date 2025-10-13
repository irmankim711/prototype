"""
Real-time Reports API Routes
Handles Server-Sent Events (SSE) for real-time data streaming, template population, and PDF generation
"""

from flask import Blueprint, request, jsonify, Response, current_app

import json
import time
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Generator
import logging

from .. import db
from ..decorators import get_current_user_id
from ..models import Report, User, ReportTemplate
from ..services.report_generation_service import report_generation_service
from ..core.exceptions import ReportGenerationError

logger = logging.getLogger(__name__)

# Create blueprint
realtime_reports_bp = Blueprint('realtime_reports', __name__, url_prefix='/api/realtime/reports')

# Global storage for active SSE connections and progress tracking
active_connections: Dict[str, Dict] = {}
data_collection_progress: Dict[str, Dict] = {}

class DataCollectionTracker:
    """Tracks data collection progress for real-time streaming"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.utcnow()
        self.total_steps = 0
        self.completed_steps = 0
        self.current_step = ""
        self.collected_data = {}
        self.status = "initializing"
        self.error_message = None
    
    def update_progress(self, step: str, progress: int, data: Dict = None):
        """Update progress and notify SSE clients"""
        self.current_step = step
        self.completed_steps = progress
        if data:
            self.collected_data.update(data)
        
        # Calculate percentage
        percentage = (progress / max(self.total_steps, 1)) * 100
        
        # Create progress event
        progress_event = {
            'type': 'progress',
            'session_id': self.session_id,
            'step': step,
            'progress': progress,
            'total_steps': self.total_steps,
            'percentage': min(percentage, 100),
            'status': self.status,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data or {}
        }
        
        # Store progress
        data_collection_progress[self.session_id] = progress_event
        
        # Notify active connections
        self._notify_connections(progress_event)
        
        logger.info(f"Data collection progress [{self.session_id}]: {step} - {percentage:.1f}%")
    
    def complete(self, final_data: Dict = None):
        """Mark data collection as complete"""
        self.status = "completed"
        if final_data:
            self.collected_data.update(final_data)
        
        completion_event = {
            'type': 'completed',
            'session_id': self.session_id,
            'status': 'completed',
            'total_data_points': len(self.collected_data),
            'collection_duration': (datetime.utcnow() - self.start_time).total_seconds(),
            'data': self.collected_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        data_collection_progress[self.session_id] = completion_event
        self._notify_connections(completion_event)
        
        logger.info(f"Data collection completed [{self.session_id}]: {len(self.collected_data)} data points")
    
    def set_error(self, error_message: str):
        """Set error status"""
        self.status = "error"
        self.error_message = error_message
        
        error_event = {
            'type': 'error',
            'session_id': self.session_id,
            'status': 'error',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        data_collection_progress[self.session_id] = error_event
        self._notify_connections(error_event)
        
        logger.error(f"Data collection error [{self.session_id}]: {error_message}")
    
    def _notify_connections(self, event_data: Dict):
        """Notify all active SSE connections"""
        for conn_id, connection in active_connections.items():
            if connection.get('session_id') == self.session_id:
                try:
                    connection['queue'].put(event_data)
                except Exception as e:
                    logger.error(f"Error notifying connection {conn_id}: {e}")

def simulate_data_collection(tracker: DataCollectionTracker, config: Dict):
    """Simulate data collection process with real-time updates"""
    try:
        # Set total steps based on config
        data_sources = config.get('data_sources', [])
        tracker.total_steps = len(data_sources) * 3  # 3 sub-steps per source
        tracker.status = "collecting"
        
        collected_data = {}
        step_count = 0
        
        for i, source in enumerate(data_sources):
            source_name = source.get('name', f'Source_{i+1}')
            
            # Step 1: Connect to source
            step_count += 1
            tracker.update_progress(f"Connecting to {source_name}", step_count)
            time.sleep(0.5)  # Simulate connection time
            
            # Step 2: Fetch data
            step_count += 1
            tracker.update_progress(f"Fetching data from {source_name}", step_count)
            time.sleep(1.0)  # Simulate data fetch
            
            # Simulate collected data
            source_data = {
                f'{source_name}_records': [
                    {'id': j, 'value': f'data_{j}', 'timestamp': datetime.utcnow().isoformat()}
                    for j in range(source.get('record_count', 10))
                ],
                f'{source_name}_metadata': {
                    'total_records': source.get('record_count', 10),
                    'source_type': source.get('type', 'database'),
                    'last_updated': datetime.utcnow().isoformat()
                }
            }
            
            # Step 3: Process data
            step_count += 1
            tracker.update_progress(f"Processing {source_name} data", step_count, source_data)
            time.sleep(0.3)  # Simulate processing time
            
            collected_data.update(source_data)
        
        # Complete data collection
        tracker.complete(collected_data)
        
    except Exception as e:
        tracker.set_error(str(e))

@realtime_reports_bp.route('/stream/<session_id>', methods=['GET'])
def stream_data_collection(session_id):
    """
    SSE endpoint for real-time data collection progress
    GET /api/realtime/reports/stream/{session_id}
    """
    def event_stream():
        user_id = get_current_user_id()
        connection_id = str(uuid.uuid4())
        
        # Set up SSE headers
        def generate():
            try:
                # Register this connection
                import queue
                event_queue = queue.Queue()
                active_connections[connection_id] = {
                    'user_id': user_id,
                    'session_id': session_id,
                    'queue': event_queue,
                    'connected_at': datetime.utcnow()
                }
                
                # Send initial connection event
                yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id, 'connection_id': connection_id})}\n\n"
                
                # Send existing progress if available
                if session_id in data_collection_progress:
                    existing_progress = data_collection_progress[session_id]
                    yield f"data: {json.dumps(existing_progress)}\n\n"
                
                # Keep connection alive and send events
                while True:
                    try:
                        # Wait for events with timeout
                        event = event_queue.get(timeout=30)  # 30-second timeout
                        yield f"data: {json.dumps(event)}\n\n"
                    except queue.Empty:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                    except Exception as e:
                        logger.error(f"SSE stream error: {e}")
                        break
                        
            except Exception as e:
                logger.error(f"SSE connection error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            finally:
                # Clean up connection
                if connection_id in active_connections:
                    del active_connections[connection_id]
                logger.info(f"SSE connection {connection_id} closed")
        
        return Response(
            generate(),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
    
    return event_stream()

@realtime_reports_bp.route('/start-collection', methods=['POST'])
def start_data_collection():
    """
    Start real-time data collection process
    POST /api/realtime/reports/start-collection
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No configuration provided'}), 400
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create data collection tracker
        tracker = DataCollectionTracker(session_id)
        
        # Default configuration for demo
        config = data.get('config', {
            'data_sources': [
                {'name': 'UserDatabase', 'type': 'database', 'record_count': 15},
                {'name': 'FormSubmissions', 'type': 'api', 'record_count': 8},
                {'name': 'AnalyticsData', 'type': 'service', 'record_count': 12}
            ]
        })
        
        # Start data collection in background thread
        collection_thread = threading.Thread(
            target=simulate_data_collection,
            args=(tracker, config)
        )
        collection_thread.daemon = True
        collection_thread.start()
        
        logger.info(f"Data collection started for session {session_id} by user {user_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Data collection started',
            'stream_url': f'/api/realtime/reports/stream/{session_id}',
            'config': config
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting data collection: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start data collection: {str(e)}'
        }), 500

@realtime_reports_bp.route('/generate-with-template', methods=['POST'])
def generate_report_with_template():
    """
    Generate report with template population using collected data
    POST /api/realtime/reports/generate-with-template
    """
    try:
        user_id = get_current_user_id()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['session_id', 'template_id', 'title']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        session_id = data['session_id']
        template_id = data['template_id']
        
        # Check if data collection is complete
        if session_id not in data_collection_progress:
            return jsonify({'error': 'Data collection session not found'}), 404
        
        collection_data = data_collection_progress[session_id]
        if collection_data.get('type') != 'completed':
            return jsonify({
                'error': 'Data collection not completed',
                'status': collection_data.get('status', 'unknown')
            }), 400
        
        # Get template
        template = ReportTemplate.query.get(template_id)
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Create report record
        report = Report(
            id=str(uuid.uuid4()),
            title=data['title'],
            description=data.get('description', f'Real-time report generated from session {session_id}'),
            report_type='realtime',
            status='pending',
            generation_status='pending',
            template_id=str(template_id),
            program_id=1,
            generation_config={
                'session_id': session_id,
                'template_used': template.name,
                'realtime_generation': True,
                'data_sources': data.get('data_sources', [])
            },
            data_source=collection_data.get('data', {}),
            user_id=user_id,
            created_by=str(user_id),
            download_count=0,
            view_count=0
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Start report generation using collected data
        from ..tasks.enhanced_report_tasks import generate_comprehensive_report_task
        generate_comprehensive_report_task.delay(report.id, collection_data.get('data', {}), report.generation_config)
        
        logger.info(f"Real-time report generation started: {report.id} for session {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Real-time report generation started',
            'report_id': report.id,
            'session_id': session_id,
            'template_name': template.name,
            'data_points': len(collection_data.get('data', {})),
            'download_urls': {
                'pdf': f"/api/reports/{report.id}/download/pdf",
                'docx': f"/api/reports/{report.id}/download/docx",
                'excel': f"/api/reports/{report.id}/download/excel"
            }
        }), 202
        
    except Exception as e:
        logger.error(f"Error generating report with template: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate report: {str(e)}'
        }), 500

@realtime_reports_bp.route('/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """
    Get data collection session status
    GET /api/realtime/reports/session/{session_id}/status
    """
    try:
        user_id = get_current_user_id()
        
        if session_id not in data_collection_progress:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = data_collection_progress[session_id]
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': session_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get session status: {str(e)}'
        }), 500

@realtime_reports_bp.route('/active-connections', methods=['GET'])
def get_active_connections():
    """
    Get active SSE connections (for debugging)
    GET /api/realtime/reports/active-connections
    """
    try:
        user_id = get_current_user_id()
        
        connections_info = []
        for conn_id, conn_data in active_connections.items():
            if conn_data['user_id'] == user_id:  # Only show user's own connections
                connections_info.append({
                    'connection_id': conn_id,
                    'session_id': conn_data['session_id'],
                    'connected_at': conn_data['connected_at'].isoformat(),
                    'duration_seconds': (datetime.utcnow() - conn_data['connected_at']).total_seconds()
                })
        
        return jsonify({
            'success': True,
            'active_connections': connections_info,
            'total_connections': len(connections_info)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting active connections: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get active connections: {str(e)}'
        }), 500

@realtime_reports_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check for real-time reports service
    GET /api/realtime/reports/health
    """
    try:
        health_status = {
            'service': 'realtime-reports',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'active_connections': len(active_connections),
            'active_sessions': len(data_collection_progress)
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'service': 'realtime-reports',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500