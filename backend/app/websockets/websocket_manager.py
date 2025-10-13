"""
WebSocket Manager for Real-time Collaboration
Handles WebSocket connections, rooms, and message broadcasting
"""
import logging
from typing import Dict, List, Any, Optional
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
# JWT removed

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and real-time collaboration"""
    
    def __init__(self):
        self.socketio = None
        self.active_connections = {}  # session_id -> connection_info
        self.room_participants = {}   # room_id -> list of session_ids
        self.user_sessions = {}       # user_id -> list of session_ids
        logger.info("WebSocket Manager initialized")
    
    def init_app(self, app, socketio_instance):
        """Initialize WebSocket manager with Flask app and SocketIO"""
        self.socketio = socketio_instance
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("WebSocket Manager initialized with Flask app")
    
    def _register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle client connection"""
            try:
                # Authenticate user
                user_info = self._authenticate_connection(auth)
                if not user_info:
                    logger.warning(f"Unauthorized WebSocket connection from {request.sid}")
                    disconnect()
                    return False
                
                # Store connection info
                self.active_connections[request.sid] = {
                    'user_id': user_info['user_id'],
                    'user_name': user_info.get('user_name', f"User {user_info['user_id']}"),
                    'connected_at': self._get_current_time(),
                    'rooms': set()
                }
                
                # Track user sessions
                user_id = user_info['user_id']
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = set()
                self.user_sessions[user_id].add(request.sid)
                
                logger.info(f"User {user_id} connected with session {request.sid}")
                
                emit('connection_established', {
                    'session_id': request.sid,
                    'user_id': user_id,
                    'message': 'Connected successfully'
                })
                
                return True
                
            except Exception as e:
                logger.error(f"Error handling connection: {e}")
                disconnect()
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            try:
                if request.sid in self.active_connections:
                    connection_info = self.active_connections[request.sid]
                    user_id = connection_info['user_id']
                    
                    # Leave all rooms
                    for room_id in connection_info['rooms'].copy():
                        self._leave_room_internal(request.sid, room_id)
                    
                    # Remove from user sessions
                    if user_id in self.user_sessions:
                        self.user_sessions[user_id].discard(request.sid)
                        if not self.user_sessions[user_id]:
                            del self.user_sessions[user_id]
                    
                    # Remove connection
                    del self.active_connections[request.sid]
                    
                    logger.info(f"User {user_id} disconnected (session {request.sid})")
                
            except Exception as e:
                logger.error(f"Error handling disconnection: {e}")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room join request"""
            try:
                if request.sid not in self.active_connections:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                room_id = data.get('room_id')
                if not room_id:
                    emit('error', {'message': 'Room ID required'})
                    return
                
                # Validate room access
                user_id = self.active_connections[request.sid]['user_id']
                if not self._validate_room_access(room_id, user_id):
                    emit('error', {'message': 'Access denied to room'})
                    return
                
                # Join room
                join_room(room_id)
                self.active_connections[request.sid]['rooms'].add(room_id)
                
                # Track room participants
                if room_id not in self.room_participants:
                    self.room_participants[room_id] = set()
                self.room_participants[room_id].add(request.sid)
                
                # Notify room about new participant
                user_info = self.active_connections[request.sid]
                emit('user_joined', {
                    'user_id': user_info['user_id'],
                    'user_name': user_info['user_name'],
                    'session_id': request.sid
                }, room=room_id, include_self=False)
                
                # Send current room state to new participant
                room_state = self._get_room_state(room_id)
                emit('room_joined', {
                    'room_id': room_id,
                    'participants': room_state['participants'],
                    'message': f'Joined room {room_id}'
                })
                
                logger.info(f"User {user_id} joined room {room_id}")
                
            except Exception as e:
                logger.error(f"Error joining room: {e}")
                emit('error', {'message': 'Failed to join room'})
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leave request"""
            try:
                if request.sid not in self.active_connections:
                    return
                
                room_id = data.get('room_id')
                if not room_id:
                    return
                
                self._leave_room_internal(request.sid, room_id)
                
                emit('room_left', {
                    'room_id': room_id,
                    'message': f'Left room {room_id}'
                })
                
            except Exception as e:
                logger.error(f"Error leaving room: {e}")
        
        @self.socketio.on('editor_operation')
        def handle_editor_operation(data):
            """Handle collaborative editing operation"""
            try:
                if request.sid not in self.active_connections:
                    emit('error', {'message': 'Not authenticated'})
                    return
                
                room_id = data.get('room_id')
                operation = data.get('operation')
                
                if not room_id or not operation:
                    emit('error', {'message': 'Room ID and operation required'})
                    return
                
                # Validate user is in room
                if room_id not in self.active_connections[request.sid]['rooms']:
                    emit('error', {'message': 'Not in room'})
                    return
                
                # Process operation
                user_id = self.active_connections[request.sid]['user_id']
                processed_operation = self._process_editor_operation(
                    room_id, user_id, operation
                )
                
                if processed_operation.get('success'):
                    # Broadcast to room (excluding sender)
                    emit('operation_broadcast', {
                        'operation': processed_operation['operation'],
                        'user_id': user_id,
                        'timestamp': self._get_current_time()
                    }, room=room_id, include_self=False)
                    
                    # Acknowledge to sender
                    emit('operation_acknowledged', {
                        'operation_id': operation.get('id'),
                        'success': True
                    })
                else:
                    emit('operation_error', {
                        'operation_id': operation.get('id'),
                        'error': processed_operation.get('error', 'Operation failed')
                    })
                
            except Exception as e:
                logger.error(f"Error handling editor operation: {e}")
                emit('error', {'message': 'Operation failed'})
        
        @self.socketio.on('cursor_update')
        def handle_cursor_update(data):
            """Handle cursor position update"""
            try:
                if request.sid not in self.active_connections:
                    return
                
                room_id = data.get('room_id')
                cursor_data = data.get('cursor_data')
                
                if not room_id or not cursor_data:
                    return
                
                # Validate user is in room
                if room_id not in self.active_connections[request.sid]['rooms']:
                    return
                
                user_id = self.active_connections[request.sid]['user_id']
                user_name = self.active_connections[request.sid]['user_name']
                
                # Broadcast cursor update to room (excluding sender)
                emit('cursor_broadcast', {
                    'user_id': user_id,
                    'user_name': user_name,
                    'cursor_data': cursor_data,
                    'timestamp': self._get_current_time()
                }, room=room_id, include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling cursor update: {e}")
        
        @self.socketio.on('ping')
        def handle_ping():
            """Handle ping for connection keepalive"""
            emit('pong', {'timestamp': self._get_current_time()})
    
    def _authenticate_connection(self, auth_data) -> Optional[Dict[str, Any]]:
        """Authenticate WebSocket connection"""
        try:
            if not auth_data or 'token' not in auth_data:
                return None
            
            token = auth_data['token']
            
            # Note: JWT authentication has been removed
            # This is a placeholder that should be replaced with Firebase token validation
            try:
                return {
                    'user_id': 1,  # Default user
                    'user_name': 'User 1'
                }
                
            except Exception:
                # Fallback for development - accept any token
                return {
                    'user_id': 1,
                    'user_name': 'Development User'
                }
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def _validate_room_access(self, room_id: str, user_id: int) -> bool:
        """Validate if user has access to room"""
        try:
            # Extract report ID from room ID (format: "report_123")
            if room_id.startswith('report_'):
                report_id = int(room_id.split('_')[1])
                
                # Check if user has access to this report
                from ..services.report_editor_service import report_editor_service
                from ..models.template_models import GeneratedReport
                
                report = GeneratedReport.query.get(report_id)
                if not report:
                    return False
                
                # Basic access check - can be enhanced
                return report.created_by == user_id or self._is_admin(user_id)
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating room access: {e}")
            return False
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        # Placeholder - integrate with actual user management
        return False
    
    def _leave_room_internal(self, session_id: str, room_id: str):
        """Internal method to handle leaving a room"""
        try:
            # Leave the room
            leave_room(room_id)
            
            # Update connection info
            if session_id in self.active_connections:
                self.active_connections[session_id]['rooms'].discard(room_id)
                user_info = self.active_connections[session_id]
                
                # Update room participants
                if room_id in self.room_participants:
                    self.room_participants[room_id].discard(session_id)
                    
                    # Notify room about user leaving
                    emit('user_left', {
                        'user_id': user_info['user_id'],
                        'user_name': user_info['user_name'],
                        'session_id': session_id
                    }, room=room_id)
                    
                    # Clean up empty room
                    if not self.room_participants[room_id]:
                        del self.room_participants[room_id]
                
                logger.info(f"User {user_info['user_id']} left room {room_id}")
                
        except Exception as e:
            logger.error(f"Error leaving room: {e}")
    
    def _get_room_state(self, room_id: str) -> Dict[str, Any]:
        """Get current state of a room"""
        participants = []
        
        if room_id in self.room_participants:
            for session_id in self.room_participants[room_id]:
                if session_id in self.active_connections:
                    user_info = self.active_connections[session_id]
                    participants.append({
                        'user_id': user_info['user_id'],
                        'user_name': user_info['user_name'],
                        'session_id': session_id,
                        'connected_at': user_info['connected_at']
                    })
        
        return {
            'room_id': room_id,
            'participants': participants,
            'participant_count': len(participants)
        }
    
    def _process_editor_operation(self, room_id: str, user_id: int, 
                                operation: Dict[str, Any]) -> Dict[str, Any]:
        """Process collaborative editing operation"""
        try:
            # Extract report ID from room ID
            if not room_id.startswith('report_'):
                return {'success': False, 'error': 'Invalid room ID'}
            
            report_id = int(room_id.split('_')[1])
            
            # Use report editor service to handle operation
            from ..services.report_editor_service import report_editor_service
            
            result = report_editor_service.handle_collaborative_operation(
                report_id, user_id, operation
            )
            
            if result.get('success'):
                return {
                    'success': True,
                    'operation': result.get('data', operation)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Operation failed')
                }
                
        except Exception as e:
            logger.error(f"Error processing editor operation: {e}")
            return {'success': False, 'error': 'Processing failed'}
    
    def _get_current_time(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def broadcast_to_room(self, room_id: str, event: str, data: Dict[str, Any], 
                         exclude_session: str = None):
        """Broadcast message to all participants in a room"""
        try:
            if self.socketio:
                if exclude_session:
                    # Broadcast to room excluding specific session
                    self.socketio.emit(event, data, room=room_id, skip_sid=exclude_session)
                else:
                    self.socketio.emit(event, data, room=room_id)
                    
        except Exception as e:
            logger.error(f"Error broadcasting to room {room_id}: {e}")
    
    def send_to_user(self, user_id: int, event: str, data: Dict[str, Any]):
        """Send message to all sessions of a specific user"""
        try:
            if user_id in self.user_sessions:
                for session_id in self.user_sessions[user_id]:
                    if self.socketio:
                        self.socketio.emit(event, data, room=session_id)
                        
        except Exception as e:
            logger.error(f"Error sending to user {user_id}: {e}")
    
    def get_room_participants(self, room_id: str) -> List[Dict[str, Any]]:
        """Get list of participants in a room"""
        return self._get_room_state(room_id)['participants']
    
    def get_user_rooms(self, user_id: int) -> List[str]:
        """Get list of rooms a user is currently in"""
        rooms = set()
        
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                if session_id in self.active_connections:
                    rooms.update(self.active_connections[session_id]['rooms'])
        
        return list(rooms)
    
    def cleanup_inactive_connections(self):
        """Clean up inactive connections and rooms"""
        try:
            from datetime import datetime, timedelta
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)
            inactive_sessions = []
            
            for session_id, connection_info in self.active_connections.items():
                # This would need to track last activity time
                # For now, just log the cleanup attempt
                pass
            
            # Clean up empty rooms
            empty_rooms = [
                room_id for room_id, participants in self.room_participants.items()
                if not participants
            ]
            
            for room_id in empty_rooms:
                del self.room_participants[room_id]
            
            if empty_rooms:
                logger.info(f"Cleaned up {len(empty_rooms)} empty rooms")
                
        except Exception as e:
            logger.error(f"Error cleaning up connections: {e}")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()