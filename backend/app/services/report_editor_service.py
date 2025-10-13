"""
Report Editor Service for Real-time Collaborative Editing
Handles report editing sessions, version control, and collaboration
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc
from flask import current_app

from ..models.template_models import GeneratedReport, ReportVersion, ReportEditSession
from .. import db

logger = logging.getLogger(__name__)

class ReportEditorService:
    """Service for managing collaborative report editing"""
    
    def __init__(self):
        self.active_sessions = {}  # In-memory session tracking
        logger.info("Report Editor Service initialized")
    
    def open_editor(self, report_id: int, user_id: int, session_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Open a report for editing and create an editing session
        
        Args:
            report_id: Report ID to edit
            user_id: User ID opening the editor
            session_data: Additional session data
            
        Returns:
            Editor session information
        """
        try:
            # Get the report
            report = GeneratedReport.query.get(report_id)
            if not report:
                return {'success': False, 'error': 'Report not found'}
            
            # Check if user has edit permissions
            if not self._check_edit_permission(report, user_id):
                return {'success': False, 'error': 'Access denied'}
            
            # Create or update editing session
            session = ReportEditSession.query.filter_by(
                report_id=report_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not session:
                session = ReportEditSession(
                    report_id=report_id,
                    user_id=user_id,
                    session_data=session_data or {},
                    started_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    is_active=True
                )
                db.session.add(session)
            else:
                session.last_activity = datetime.utcnow()
                session.session_data = session_data or session.session_data
            
            db.session.commit()
            
            # Get current report content
            current_content = self._get_report_content(report)
            
            # Get active collaborators
            collaborators = self._get_active_collaborators(report_id, exclude_user=user_id)
            
            # Track session in memory
            session_key = f"{report_id}_{user_id}"
            self.active_sessions[session_key] = {
                'session_id': session.id,
                'report_id': report_id,
                'user_id': user_id,
                'started_at': session.started_at,
                'last_activity': session.last_activity
            }
            
            logger.info(f"Opened editor for report {report_id} by user {user_id}")
            
            return {
                'success': True,
                'session_id': session.id,
                'report': {
                    'id': report.id,
                    'name': report.report_name,
                    'content': current_content,
                    'status': report.status.value,
                    'template_id': report.template_id,
                    'created_at': report.created_at.isoformat(),
                    'updated_at': report.updated_at.isoformat()
                },
                'collaborators': collaborators,
                'permissions': self._get_user_permissions(report, user_id)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error opening editor for report {report_id}: {e}")
            return {'success': False, 'error': 'Failed to open editor'}
    
    def save_changes(self, report_id: int, user_id: int, content: Dict[str, Any], 
                    auto_save: bool = False, change_summary: str = None) -> Dict[str, Any]:
        """
        Save changes to a report with version tracking
        
        Args:
            report_id: Report ID
            user_id: User making changes
            content: New content
            auto_save: Whether this is an auto-save
            change_summary: Description of changes
            
        Returns:
            Save result with version information
        """
        try:
            # Get the report and session
            report = GeneratedReport.query.get(report_id)
            if not report:
                return {'success': False, 'error': 'Report not found'}
            
            session = ReportEditSession.query.filter_by(
                report_id=report_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not session:
                return {'success': False, 'error': 'No active editing session'}
            
            # Check if content has actually changed
            current_content = self._get_report_content(report)
            if self._content_equals(current_content, content):
                # Update session activity but don't create version
                session.last_activity = datetime.utcnow()
                db.session.commit()
                return {
                    'success': True,
                    'message': 'No changes detected',
                    'auto_save': auto_save
                }
            
            # Create new version if not auto-save or if significant changes
            version = None
            if not auto_save or self._should_create_version(current_content, content):
                version = self._create_version(
                    report=report,
                    content=content,
                    user_id=user_id,
                    change_summary=change_summary or ('Auto-save' if auto_save else 'Manual save'),
                    is_auto_save=auto_save
                )
            
            # Update report content
            self._update_report_content(report, content)
            
            # Update session
            session.last_activity = datetime.utcnow()
            session.changes_count = (session.changes_count or 0) + 1
            
            db.session.commit()
            
            # Update in-memory session tracking
            session_key = f"{report_id}_{user_id}"
            if session_key in self.active_sessions:
                self.active_sessions[session_key]['last_activity'] = session.last_activity
            
            logger.info(f"Saved changes to report {report_id} by user {user_id} (auto_save: {auto_save})")
            
            result = {
                'success': True,
                'auto_save': auto_save,
                'saved_at': datetime.utcnow().isoformat(),
                'changes_count': session.changes_count
            }
            
            if version:
                result['version'] = {
                    'id': version.id,
                    'version_number': version.version_number,
                    'created_at': version.created_at.isoformat()
                }
            
            return result
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving changes to report {report_id}: {e}")
            return {'success': False, 'error': 'Failed to save changes'}
    
    def get_versions(self, report_id: int, user_id: int, limit: int = 50) -> Dict[str, Any]:
        """
        Get version history for a report
        
        Args:
            report_id: Report ID
            user_id: User requesting versions
            limit: Maximum number of versions to return
            
        Returns:
            Version history data
        """
        try:
            # Check access
            report = GeneratedReport.query.get(report_id)
            if not report:
                return {'success': False, 'error': 'Report not found'}
            
            if not self._check_view_permission(report, user_id):
                return {'success': False, 'error': 'Access denied'}
            
            # Get versions
            versions = ReportVersion.query.filter_by(report_id=report_id)\
                .order_by(desc(ReportVersion.created_at))\
                .limit(limit).all()
            
            # Format version data
            version_list = []
            for version in versions:
                version_data = {
                    'id': version.id,
                    'version_number': version.version_number,
                    'created_at': version.created_at.isoformat(),
                    'created_by': version.created_by,
                    'change_summary': version.change_summary,
                    'is_current': version.is_current,
                    'is_auto_save': version.is_auto_save,
                    'content_size': len(json.dumps(version.content)) if version.content else 0
                }
                
                # Add creator name if available
                # Note: This would need user service integration
                version_data['creator_name'] = f'User {version.created_by}'
                
                version_list.append(version_data)
            
            return {
                'success': True,
                'versions': version_list,
                'total_versions': len(version_list),
                'report_name': report.report_name
            }
            
        except Exception as e:
            logger.error(f"Error getting versions for report {report_id}: {e}")
            return {'success': False, 'error': 'Failed to get versions'}
    
    def revert_version(self, report_id: int, version_id: int, user_id: int) -> Dict[str, Any]:
        """
        Revert report to a specific version
        
        Args:
            report_id: Report ID
            version_id: Version ID to revert to
            user_id: User performing the revert
            
        Returns:
            Revert result
        """
        try:
            # Get report and version
            report = GeneratedReport.query.get(report_id)
            if not report:
                return {'success': False, 'error': 'Report not found'}
            
            version = ReportVersion.query.filter_by(
                id=version_id,
                report_id=report_id
            ).first()
            
            if not version:
                return {'success': False, 'error': 'Version not found'}
            
            # Check permissions
            if not self._check_edit_permission(report, user_id):
                return {'success': False, 'error': 'Access denied'}
            
            # Create new version with reverted content
            new_version = self._create_version(
                report=report,
                content=version.content,
                user_id=user_id,
                change_summary=f'Reverted to version {version.version_number}',
                is_auto_save=False
            )
            
            # Update report content
            self._update_report_content(report, version.content)
            
            db.session.commit()
            
            logger.info(f"Reverted report {report_id} to version {version_id} by user {user_id}")
            
            return {
                'success': True,
                'new_version': {
                    'id': new_version.id,
                    'version_number': new_version.version_number,
                    'created_at': new_version.created_at.isoformat()
                },
                'reverted_to': {
                    'id': version.id,
                    'version_number': version.version_number,
                    'created_at': version.created_at.isoformat()
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error reverting report {report_id} to version {version_id}: {e}")
            return {'success': False, 'error': 'Failed to revert version'}
    
    def close_session(self, report_id: int, user_id: int) -> Dict[str, Any]:
        """
        Close an editing session
        
        Args:
            report_id: Report ID
            user_id: User closing session
            
        Returns:
            Close result
        """
        try:
            # Update database session
            session = ReportEditSession.query.filter_by(
                report_id=report_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if session:
                session.is_active = False
                session.ended_at = datetime.utcnow()
                db.session.commit()
            
            # Remove from memory
            session_key = f"{report_id}_{user_id}"
            if session_key in self.active_sessions:
                del self.active_sessions[session_key]
            
            logger.info(f"Closed editing session for report {report_id} by user {user_id}")
            
            return {'success': True}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error closing session for report {report_id}: {e}")
            return {'success': False, 'error': 'Failed to close session'}
    
    def get_active_sessions(self, report_id: int) -> List[Dict[str, Any]]:
        """Get active editing sessions for a report"""
        try:
            # Clean up expired sessions first
            self._cleanup_expired_sessions()
            
            # Get active sessions from database
            sessions = ReportEditSession.query.filter_by(
                report_id=report_id,
                is_active=True
            ).filter(
                ReportEditSession.last_activity > datetime.utcnow() - timedelta(minutes=30)
            ).all()
            
            session_list = []
            for session in sessions:
                session_data = {
                    'session_id': session.id,
                    'user_id': session.user_id,
                    'started_at': session.started_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'changes_count': session.changes_count or 0
                }
                
                # Add user name if available
                session_data['user_name'] = f'User {session.user_id}'
                
                session_list.append(session_data)
            
            return session_list
            
        except Exception as e:
            logger.error(f"Error getting active sessions for report {report_id}: {e}")
            return []
    
    def handle_collaborative_operation(self, report_id: int, user_id: int, 
                                     operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle collaborative editing operation
        
        Args:
            report_id: Report ID
            user_id: User performing operation
            operation: Operation data (insert, delete, format, etc.)
            
        Returns:
            Operation result
        """
        try:
            # Validate session
            session = ReportEditSession.query.filter_by(
                report_id=report_id,
                user_id=user_id,
                is_active=True
            ).first()
            
            if not session:
                return {'success': False, 'error': 'No active session'}
            
            # Update session activity
            session.last_activity = datetime.utcnow()
            
            # Process operation based on type
            operation_type = operation.get('type')
            
            if operation_type == 'cursor_move':
                # Handle cursor position updates
                result = self._handle_cursor_operation(report_id, user_id, operation)
            elif operation_type == 'text_insert':
                # Handle text insertion
                result = self._handle_text_operation(report_id, user_id, operation)
            elif operation_type == 'text_delete':
                # Handle text deletion
                result = self._handle_text_operation(report_id, user_id, operation)
            elif operation_type == 'format_change':
                # Handle formatting changes
                result = self._handle_format_operation(report_id, user_id, operation)
            else:
                result = {'success': False, 'error': f'Unknown operation type: {operation_type}'}
            
            db.session.commit()
            
            return result
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling collaborative operation: {e}")
            return {'success': False, 'error': 'Operation failed'}
    
    def _check_edit_permission(self, report: GeneratedReport, user_id: int) -> bool:
        """Check if user has edit permission for report"""
        # Basic permission check - can be enhanced with role-based access
        return report.created_by == user_id or self._is_admin(user_id)
    
    def _check_view_permission(self, report: GeneratedReport, user_id: int) -> bool:
        """Check if user has view permission for report"""
        # Basic permission check - can be enhanced with sharing permissions
        return report.created_by == user_id or self._is_admin(user_id)
    
    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin - placeholder implementation"""
        # This would integrate with actual user management system
        return False
    
    def _get_report_content(self, report: GeneratedReport) -> Dict[str, Any]:
        """Get current report content"""
        # Get the latest version or use data_source as fallback
        latest_version = ReportVersion.query.filter_by(
            report_id=report.id,
            is_current=True
        ).first()
        
        if latest_version and latest_version.content:
            return latest_version.content
        
        # Fallback to original data source
        return report.data_source or {}
    
    def _update_report_content(self, report: GeneratedReport, content: Dict[str, Any]):
        """Update report content"""
        # Update the current version
        current_version = ReportVersion.query.filter_by(
            report_id=report.id,
            is_current=True
        ).first()
        
        if current_version:
            current_version.content = content
        
        # Also update report's updated_at timestamp
        report.updated_at = datetime.utcnow()
    
    def _create_version(self, report: GeneratedReport, content: Dict[str, Any], 
                       user_id: int, change_summary: str, is_auto_save: bool = False) -> ReportVersion:
        """Create a new version"""
        # Mark current version as not current
        ReportVersion.query.filter_by(
            report_id=report.id,
            is_current=True
        ).update({'is_current': False})
        
        # Get next version number
        last_version = ReportVersion.query.filter_by(report_id=report.id)\
            .order_by(desc(ReportVersion.version_number)).first()
        
        version_number = (last_version.version_number + 1) if last_version else 1
        
        # Create new version
        version = ReportVersion(
            report_id=report.id,
            version_number=version_number,
            content=content,
            created_by=user_id,
            change_summary=change_summary,
            is_current=True,
            is_auto_save=is_auto_save
        )
        
        db.session.add(version)
        return version
    
    def _content_equals(self, content1: Dict[str, Any], content2: Dict[str, Any]) -> bool:
        """Check if two content objects are equal"""
        try:
            return json.dumps(content1, sort_keys=True) == json.dumps(content2, sort_keys=True)
        except:
            return False
    
    def _should_create_version(self, old_content: Dict[str, Any], new_content: Dict[str, Any]) -> bool:
        """Determine if changes are significant enough to create a version"""
        # Simple heuristic - create version if content size changed significantly
        old_size = len(json.dumps(old_content))
        new_size = len(json.dumps(new_content))
        
        size_change = abs(new_size - old_size) / max(old_size, 1)
        
        # Create version if content changed by more than 5%
        return size_change > 0.05
    
    def _get_active_collaborators(self, report_id: int, exclude_user: int = None) -> List[Dict[str, Any]]:
        """Get list of active collaborators"""
        query = ReportEditSession.query.filter_by(
            report_id=report_id,
            is_active=True
        ).filter(
            ReportEditSession.last_activity > datetime.utcnow() - timedelta(minutes=30)
        )
        
        if exclude_user:
            query = query.filter(ReportEditSession.user_id != exclude_user)
        
        sessions = query.all()
        
        collaborators = []
        for session in sessions:
            collaborators.append({
                'user_id': session.user_id,
                'user_name': f'User {session.user_id}',  # Would get from user service
                'last_activity': session.last_activity.isoformat(),
                'session_id': session.id
            })
        
        return collaborators
    
    def _get_user_permissions(self, report: GeneratedReport, user_id: int) -> Dict[str, bool]:
        """Get user permissions for report"""
        is_owner = report.created_by == user_id
        is_admin = self._is_admin(user_id)
        
        return {
            'can_edit': is_owner or is_admin,
            'can_delete': is_owner or is_admin,
            'can_share': is_owner or is_admin,
            'can_view_versions': True,
            'can_revert': is_owner or is_admin
        }
    
    def _cleanup_expired_sessions(self):
        """Clean up expired editing sessions"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            expired_sessions = ReportEditSession.query.filter(
                and_(
                    ReportEditSession.is_active == True,
                    ReportEditSession.last_activity < cutoff_time
                )
            ).all()
            
            for session in expired_sessions:
                session.is_active = False
                session.ended_at = datetime.utcnow()
            
            if expired_sessions:
                db.session.commit()
                logger.info(f"Cleaned up {len(expired_sessions)} expired editing sessions")
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up expired sessions: {e}")
    
    def _handle_cursor_operation(self, report_id: int, user_id: int, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cursor position operation"""
        # This would be used for real-time cursor tracking
        return {
            'success': True,
            'operation_type': 'cursor_move',
            'broadcast': True,
            'data': {
                'user_id': user_id,
                'position': operation.get('position', {}),
                'selection': operation.get('selection', {})
            }
        }
    
    def _handle_text_operation(self, report_id: int, user_id: int, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text insertion/deletion operation"""
        # This would apply operational transforms for conflict resolution
        return {
            'success': True,
            'operation_type': operation.get('type'),
            'broadcast': True,
            'data': {
                'user_id': user_id,
                'position': operation.get('position', {}),
                'content': operation.get('content', ''),
                'length': operation.get('length', 0)
            }
        }
    
    def _handle_format_operation(self, report_id: int, user_id: int, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Handle formatting operation"""
        return {
            'success': True,
            'operation_type': 'format_change',
            'broadcast': True,
            'data': {
                'user_id': user_id,
                'range': operation.get('range', {}),
                'format': operation.get('format', {}),
                'action': operation.get('action', 'apply')
            }
        }

# Global service instance
report_editor_service = ReportEditorService()