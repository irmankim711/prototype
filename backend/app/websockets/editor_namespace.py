"""
Editor Namespace for Real-time Collaborative Editing
Specialized WebSocket namespace for report editing operations
"""
import logging
from typing import Dict, Any, List
from flask import request
from flask_socketio import Namespace, emit, join_room, leave_room, disconnect

logger = logging.getLogger(__name__)

class EditorNamespace(Namespace):
    """WebSocket namespace for collaborative report editing"""
    
    def __init__(self, namespace='/editor'):
        super().__init__(namespace)
        self.active_editors = {}  # session_id -> editor_info
        self.report_sessions = {}  # report_id -> set of session_ids
        logger.info(f"Editor namespace initialized: {namespace}")
    
    def on_connect(self, auth=None):
        """Handle editor connection"""
        try:
            # Authenticate connection
            user_info = self._authenticate_editor(auth)
            if not user_info:
                logger.warning(f"Unauthorized editor connection from {request.sid}")
                disconnect()
                return False
            
            # Store editor info
            self.active_editors[request.sid] = {
                'user_id': user_info['user_id'],
                'user_name': user_info.get('user_name', f"User {user_info['user_id']}"),
                'connected_at': self._get_current_time(),
                'current_report': None,
                'cursor_position': None,
                'selection': None
            }
            
            logger.info(f"Editor connected: User {user_info['user_id']} (session {request.sid})")
            
            emit('editor_connected', {
                'session_id': request.sid,
                'user_id': user_info['user_id'],
                'message': 'Editor connected successfully'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error in editor connection: {e}")
            disconnect()
            return False
    
    def on_disconnect(self):
        """Handle editor disconnection"""
        try:
            if request.sid in self.active_editors:
                editor_info = self.active_editors[request.sid]
                user_id = editor_info['user_id']
                current_report = editor_info.get('current_report')
                
                # Leave current report session if any
                if current_report:
                    self._leave_report_session(request.sid, current_report)
                
                # Remove from active editors
                del self.active_editors[request.sid]
                
                logger.info(f"Editor disconnected: User {user_id} (session {request.sid})")
                
        except Exception as e:
            logger.error(f"Error in editor disconnection: {e}")
    
    def on_join_report(self, data):
        """Join a report editing session"""
        try:
            if request.sid not in self.active_editors:
                emit('error', {'message': 'Not authenticated'})
                return
            
            report_id = data.get('report_id')
            if not report_id:
                emit('error', {'message': 'Report ID required'})
                return
            
            # Validate report access
            user_id = self.active_editors[request.sid]['user_id']
            if not self._validate_report_access(report_id, user_id):
                emit('error', {'message': 'Access denied to report'})
                return
            
            # Leave current report if any
            current_report = self.active_editors[request.sid].get('current_report')
            if current_report and current_report != report_id:
                self._leave_report_session(request.sid, current_report)
            
            # Join new report session
            self._join_report_session(request.sid, report_id)
            
            # Get report state and collaborators
            report_state = self._get_report_state(report_id)
            collaborators = self._get_report_collaborators(report_id, exclude_session=request.sid)
            
            # Notify user about successful join
            emit('report_joined', {
                'report_id': report_id,
                'report_state': report_state,
                'collaborators': collaborators,
                'message': f'Joined report {report_id} editing session'
            })
            
            # Notify other collaborators
            editor_info = self.active_editors[request.sid]
            emit('collaborator_joined', {
                'user_id': editor_info['user_id'],
                'user_name': editor_info['user_name'],
                'session_id': request.sid,
                'joined_at': self._get_current_time()
            }, room=f'report_{report_id}', include_self=False)
            
            logger.info(f"User {user_id} joined report {report_id} editing session")
            
        except Exception as e:
            logger.error(f"Error joining report: {e}")
            emit('error', {'message': 'Failed to join report'})
    
    def on_leave_report(self, data):
        """Leave a report editing session"""
        try:
            if request.sid not in self.active_editors:
                return
            
            report_id = data.get('report_id')
            if not report_id:
                return
            
            self._leave_report_session(request.sid, report_id)
            
            emit('report_left', {
                'report_id': report_id,
                'message': f'Left report {report_id} editing session'
            })
            
        except Exception as e:
            logger.error(f"Error leaving report: {e}")
    
    def on_content_change(self, data):
        """Handle content change operation"""
        try:
            if request.sid not in self.active_editors:
                emit('error', {'message': 'Not authenticated'})
                return
            
            report_id = data.get('report_id')
            operation = data.get('operation')
            
            if not report_id or not operation:
                emit('error', {'message': 'Report ID and operation required'})
                return
            
            # Validate user is in report session
            editor_info = self.active_editors[request.sid]
            if editor_info.get('current_report') != report_id:
                emit('error', {'message': 'Not in report session'})
                return
            
            # Process the content change
            user_id = editor_info['user_id']
            result = self._process_content_change(report_id, user_id, operation)
            
            if result.get('success'):
                # Broadcast to other collaborators
                emit('content_changed', {
                    'report_id': report_id,
                    'operation': result['operation'],
                    'user_id': user_id,
                    'user_name': editor_info['user_name'],
                    'timestamp': self._get_current_time()
                }, room=f'report_{report_id}', include_self=False)
                
                # Acknowledge to sender
                emit('change_acknowledged', {
                    'operation_id': operation.get('id'),
                    'success': True,
                    'server_timestamp': self._get_current_time()
                })
                
                # Auto-save if configured
                if data.get('auto_save', False):
                    self._trigger_auto_save(report_id, user_id, result['content'])
                
            else:
                emit('change_error', {
                    'operation_id': operation.get('id'),
                    'error': result.get('error', 'Content change failed')
                })
                
        except Exception as e:
            logger.error(f"Error handling content change: {e}")
            emit('error', {'message': 'Content change failed'})
    
    def on_cursor_move(self, data):
        """Handle cursor movement"""
        try:
            if request.sid not in self.active_editors:
                return
            
            report_id = data.get('report_id')
            cursor_data = data.get('cursor_data')
            
            if not report_id or not cursor_data:
                return
            
            # Validate user is in report session
            editor_info = self.active_editors[request.sid]
            if editor_info.get('current_report') != report_id:
                return
            
            # Update cursor position
            editor_info['cursor_position'] = cursor_data.get('position')
            editor_info['selection'] = cursor_data.get('selection')
            
            # Broadcast cursor position to other collaborators
            emit('cursor_moved', {
                'user_id': editor_info['user_id'],
                'user_name': editor_info['user_name'],
                'cursor_data': cursor_data,
                'timestamp': self._get_current_time()
            }, room=f'report_{report_id}', include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling cursor move: {e}")
    
    def on_selection_change(self, data):
        """Handle text selection change"""
        try:
            if request.sid not in self.active_editors:
                return
            
            report_id = data.get('report_id')
            selection_data = data.get('selection_data')
            
            if not report_id:
                return
            
            # Validate user is in report session
            editor_info = self.active_editors[request.sid]
            if editor_info.get('current_report') != report_id:
                return
            
            # Update selection
            editor_info['selection'] = selection_data
            
            # Broadcast selection to other collaborators
            emit('selection_changed', {
                'user_id': editor_info['user_id'],
                'user_name': editor_info['user_name'],
                'selection_data': selection_data,
                'timestamp': self._get_current_time()
            }, room=f'report_{report_id}', include_self=False)
            
        except Exception as e:
            logger.error(f"Error handling selection change: {e}")
    
    def on_save_request(self, data):
        """Handle manual save request"""
        try:
            if request.sid not in self.active_editors:
                emit('error', {'message': 'Not authenticated'})
                return
            
            report_id = data.get('report_id')
            content = data.get('content')
            change_summary = data.get('change_summary', 'Manual save')
            
            if not report_id or not content:
                emit('error', {'message': 'Report ID and content required'})
                return
            
            # Validate user is in report session
            editor_info = self.active_editors[request.sid]
            if editor_info.get('current_report') != report_id:
                emit('error', {'message': 'Not in report session'})
                return
            
            # Save the report
            user_id = editor_info['user_id']
            result = self._save_report(report_id, user_id, content, change_summary)
            
            if result.get('success'):
                # Notify user of successful save
                emit('save_completed', {
                    'report_id': report_id,
                    'version': result.get('version'),
                    'saved_at': result.get('saved_at'),
                    'message': 'Report saved successfully'
                })
                
                # Notify other collaborators
                emit('report_saved', {
                    'report_id': report_id,
                    'saved_by': editor_info['user_name'],
                    'version': result.get('version'),
                    'saved_at': result.get('saved_at')
                }, room=f'report_{report_id}', include_self=False)
                
            else:
                emit('save_error', {
                    'report_id': report_id,
                    'error': result.get('error', 'Save failed')
                })
                
        except Exception as e:
            logger.error(f"Error handling save request: {e}")
            emit('error', {'message': 'Save failed'})
    
    def on_request_sync(self, data):
        """Handle request for content synchronization"""
        try:
            if request.sid not in self.active_editors:
                emit('error', {'message': 'Not authenticated'})
                return
            
            report_id = data.get('report_id')
            if not report_id:
                emit('error', {'message': 'Report ID required'})
                return
            
            # Get current report state
            report_state = self._get_report_state(report_id)
            
            emit('content_sync', {
                'report_id': report_id,
                'content': report_state.get('content'),
                'version': report_state.get('version'),
                'last_modified': report_state.get('last_modified'),
                'timestamp': self._get_current_time()
            })
            
        except Exception as e:
            logger.error(f"Error handling sync request: {e}")
            emit('error', {'message': 'Sync failed'})
    
    def _authenticate_editor(self, auth_data) -> Dict[str, Any]:
        """Authenticate editor connection"""
        try:
            if not auth_data or 'token' not in auth_data:
                return None
            
            # Use the same authentication as main WebSocket manager
            from .websocket_manager import websocket_manager
            return websocket_manager._authenticate_connection(auth_data)
            
        except Exception as e:
            logger.error(f"Editor authentication error: {e}")
            return None
    
    def _validate_report_access(self, report_id: int, user_id: int) -> bool:
        """Validate if user has access to report"""
        try:
            from ..models.template_models import GeneratedReport
            
            report = GeneratedReport.query.get(report_id)
            if not report:
                return False
            
            # Basic access check - can be enhanced with sharing permissions
            return report.created_by == user_id or self._is_admin(user_id)
            
        except Exception as e:
            logger.error(f"Error validating report access: {e}")
            return False
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        # Placeholder - integrate with actual user management
        return False
    
    def _join_report_session(self, session_id: str, report_id: int):
        """Join a report editing session"""
        room_name = f'report_{report_id}'
        join_room(room_name)
        
        # Update editor info
        self.active_editors[session_id]['current_report'] = report_id
        
        # Track report sessions
        if report_id not in self.report_sessions:
            self.report_sessions[report_id] = set()
        self.report_sessions[report_id].add(session_id)
    
    def _leave_report_session(self, session_id: str, report_id: int):
        """Leave a report editing session"""
        room_name = f'report_{report_id}'
        leave_room(room_name)
        
        # Update editor info
        if session_id in self.active_editors:
            self.active_editors[session_id]['current_report'] = None
            self.active_editors[session_id]['cursor_position'] = None
            self.active_editors[session_id]['selection'] = None
            
            # Notify other collaborators
            editor_info = self.active_editors[session_id]
            emit('collaborator_left', {
                'user_id': editor_info['user_id'],
                'user_name': editor_info['user_name'],
                'session_id': session_id,
                'left_at': self._get_current_time()
            }, room=room_name)
        
        # Update report sessions
        if report_id in self.report_sessions:
            self.report_sessions[report_id].discard(session_id)
            if not self.report_sessions[report_id]:
                del self.report_sessions[report_id]
    
    def _get_report_state(self, report_id: int) -> Dict[str, Any]:
        """Get current state of a report"""
        try:
            from ..services.report_editor_service import report_editor_service
            from ..models.template_models import GeneratedReport
            
            report = GeneratedReport.query.get(report_id)
            if not report:
                return {}
            
            # Get current content from editor service
            content = report_editor_service._get_report_content(report)
            
            return {
                'report_id': report_id,
                'content': content,
                'version': 1,  # Would get from version system
                'last_modified': report.updated_at.isoformat() if report.updated_at else None,
                'status': report.status.value
            }
            
        except Exception as e:
            logger.error(f"Error getting report state: {e}")
            return {}
    
    def _get_report_collaborators(self, report_id: int, exclude_session: str = None) -> List[Dict[str, Any]]:
        """Get list of active collaborators for a report"""
        collaborators = []
        
        if report_id in self.report_sessions:
            for session_id in self.report_sessions[report_id]:
                if session_id != exclude_session and session_id in self.active_editors:
                    editor_info = self.active_editors[session_id]
                    collaborators.append({
                        'user_id': editor_info['user_id'],
                        'user_name': editor_info['user_name'],
                        'session_id': session_id,
                        'connected_at': editor_info['connected_at'],
                        'cursor_position': editor_info.get('cursor_position'),
                        'selection': editor_info.get('selection')
                    })
        
        return collaborators
    
    def _process_content_change(self, report_id: int, user_id: int, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Process content change operation"""
        try:
            from ..services.report_editor_service import report_editor_service
            
            # Use report editor service to handle the operation
            result = report_editor_service.handle_collaborative_operation(
                report_id, user_id, operation
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing content change: {e}")
            return {'success': False, 'error': 'Processing failed'}
    
    def _save_report(self, report_id: int, user_id: int, content: Dict[str, Any], 
                    change_summary: str) -> Dict[str, Any]:
        """Save report content"""
        try:
            from ..services.report_editor_service import report_editor_service
            
            result = report_editor_service.save_changes(
                report_id=report_id,
                user_id=user_id,
                content=content,
                auto_save=False,
                change_summary=change_summary
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return {'success': False, 'error': 'Save failed'}
    
    def _trigger_auto_save(self, report_id: int, user_id: int, content: Dict[str, Any]):
        """Trigger auto-save for report"""
        try:
            from ..services.report_editor_service import report_editor_service
            
            # Perform auto-save in background
            result = report_editor_service.save_changes(
                report_id=report_id,
                user_id=user_id,
                content=content,
                auto_save=True
            )
            
            if result.get('success'):
                # Notify all collaborators about auto-save
                emit('auto_save_completed', {
                    'report_id': report_id,
                    'saved_at': result.get('saved_at'),
                    'auto_save': True
                }, room=f'report_{report_id}')
            
        except Exception as e:
            logger.error(f"Error in auto-save: {e}")
    
    def _get_current_time(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def broadcast_to_report(self, report_id: int, event: str, data: Dict[str, Any], 
                          exclude_session: str = None):
        """Broadcast message to all editors in a report session"""
        try:
            room_name = f'report_{report_id}'
            if exclude_session:
                emit(event, data, room=room_name, skip_sid=exclude_session)
            else:
                emit(event, data, room=room_name)
                
        except Exception as e:
            logger.error(f"Error broadcasting to report {report_id}: {e}")
    
    def get_report_participants(self, report_id: int) -> List[Dict[str, Any]]:
        """Get list of participants in a report editing session"""
        return self._get_report_collaborators(report_id)