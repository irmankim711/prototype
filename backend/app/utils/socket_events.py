"""
Socket.IO event utilities for real-time updates
"""

from flask import current_app
from flask_socketio import emit, join_room, leave_room
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def emit_sync_update(data_source_id: int, sync_result: Dict[str, Any]):
    """
    Emit real-time update when data source is synchronized
    """
    try:
        from .. import socketio
        
        event_data = {
            'type': 'data_source_sync',
            'data_source_id': data_source_id,
            'timestamp': sync_result.get('timestamp'),
            'status': sync_result.get('status'),
            'new_submissions': sync_result.get('new_submissions', 0),
            'updated_submissions': sync_result.get('updated_submissions', 0),
            'error_count': sync_result.get('error_count', 0),
            'message': sync_result.get('message', 'Data source synchronized')
        }
        
        # Emit to specific data source room
        socketio.emit('sync_update', event_data, room=f'data_source_{data_source_id}')
        
        # Also emit to general dashboard room
        socketio.emit('dashboard_update', event_data, room='dashboard')
        
        logger.info(f"Emitted sync update for data source {data_source_id}")
        
    except Exception as e:
        logger.error(f"Error emitting sync update: {str(e)}")

def emit_export_update(export_id: int, export_data: Dict[str, Any]):
    """
    Emit real-time update when Excel export status changes
    """
    try:
        from .. import socketio
        
        event_data = {
            'type': 'excel_export_update',
            'export_id': export_id,
            'status': export_data.get('status'),
            'progress': export_data.get('progress', 0),
            'message': export_data.get('message'),
            'file_name': export_data.get('file_name'),
            'error': export_data.get('error'),
            'timestamp': export_data.get('timestamp')
        }
        
        # Emit to specific export room
        socketio.emit('export_update', event_data, room=f'export_{export_id}')
        
        # Also emit to general dashboard room
        socketio.emit('dashboard_update', event_data, room='dashboard')
        
        logger.info(f"Emitted export update for export {export_id}")
        
    except Exception as e:
        logger.error(f"Error emitting export update: {str(e)}")

def emit_new_submission(data_source_id: int, submission_data: Dict[str, Any]):
    """
    Emit real-time notification when new form submission is received
    """
    try:
        from .. import socketio
        
        event_data = {
            'type': 'new_submission',
            'data_source_id': data_source_id,
            'submission_id': submission_data.get('id'),
            'submitter_email': submission_data.get('submitter_email'),
            'submitter_name': submission_data.get('submitter_name'),
            'submitted_at': submission_data.get('submitted_at'),
            'preview_data': submission_data.get('preview_data', {})
        }
        
        # Emit to specific data source room
        socketio.emit('new_submission', event_data, room=f'data_source_{data_source_id}')
        
        # Also emit to general dashboard room
        socketio.emit('dashboard_update', event_data, room='dashboard')
        
        logger.info(f"Emitted new submission notification for data source {data_source_id}")
        
    except Exception as e:
        logger.error(f"Error emitting new submission notification: {str(e)}")

def emit_error_notification(user_id: int, error_data: Dict[str, Any]):
    """
    Emit error notification to specific user
    """
    try:
        from .. import socketio
        
        event_data = {
            'type': 'error_notification',
            'severity': error_data.get('severity', 'error'),
            'message': error_data.get('message'),
            'details': error_data.get('details'),
            'timestamp': error_data.get('timestamp'),
            'action_required': error_data.get('action_required', False)
        }
        
        # Emit to specific user room
        socketio.emit('error_notification', event_data, room=f'user_{user_id}')
        
        logger.info(f"Emitted error notification to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error emitting error notification: {str(e)}")

def emit_analytics_update(user_id: int, analytics_data: Dict[str, Any]):
    """
    Emit analytics update to dashboard
    """
    try:
        from .. import socketio
        
        event_data = {
            'type': 'analytics_update',
            'total_submissions': analytics_data.get('total_submissions'),
            'recent_submissions': analytics_data.get('recent_submissions'),
            'active_data_sources': analytics_data.get('active_data_sources'),
            'pending_exports': analytics_data.get('pending_exports'),
            'timestamp': analytics_data.get('timestamp')
        }
        
        # Emit to user's dashboard room
        socketio.emit('analytics_update', event_data, room=f'dashboard_user_{user_id}')
        
        logger.info(f"Emitted analytics update to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error emitting analytics update: {str(e)}")

# Socket.IO event handlers (to be registered in main app)

def handle_join_room(data):
    """Handle client joining specific rooms for real-time updates"""
    try:
        room_type = data.get('room_type')
        room_id = data.get('room_id')
        
        if room_type and room_id:
            room_name = f"{room_type}_{room_id}"
            join_room(room_name)
            emit('status', {'message': f'Joined room {room_name}'})
            logger.info(f"Client joined room: {room_name}")
        
    except Exception as e:
        logger.error(f"Error handling join room: {str(e)}")
        emit('error', {'message': 'Failed to join room'})

def handle_leave_room(data):
    """Handle client leaving specific rooms"""
    try:
        room_type = data.get('room_type')
        room_id = data.get('room_id')
        
        if room_type and room_id:
            room_name = f"{room_type}_{room_id}"
            leave_room(room_name)
            emit('status', {'message': f'Left room {room_name}'})
            logger.info(f"Client left room: {room_name}")
        
    except Exception as e:
        logger.error(f"Error handling leave room: {str(e)}")
        emit('error', {'message': 'Failed to leave room'})

def handle_subscribe_dashboard(data):
    """Handle client subscribing to dashboard updates"""
    try:
        user_id = data.get('user_id')
        if user_id:
            join_room('dashboard')
            join_room(f'dashboard_user_{user_id}')
            emit('status', {'message': 'Subscribed to dashboard updates'})
            logger.info(f"Client subscribed to dashboard updates for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error subscribing to dashboard: {str(e)}")
        emit('error', {'message': 'Failed to subscribe to dashboard updates'})
