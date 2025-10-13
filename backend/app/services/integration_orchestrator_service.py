"""
Integration Orchestrator Service

Coordinates Google Forms to Sheets integration operations including:
- Creating and configuring integrations
- Managing export operations with progress tracking
- Integration validation and health checking
- Export execution logic with error handling
- Background task coordination

This service acts as the main coordinator for all integration activities.
"""

import os
import uuid
from datetime import datetime, timedelta, time as dt_time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_

from app import db
from app.models.production.integration_models import IntegrationConfig, ExportHistory, OAuthTokens
from app.core.logging import get_logger
from app.core.cache import cache_manager

logger = get_logger(__name__)


class IntegrationStatus(Enum):
    """Integration status enumeration"""
    ACTIVE = 'active'
    PAUSED = 'paused'
    ERROR = 'error'


class ExportStatus(Enum):
    """Export status enumeration"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'


class ExportType(Enum):
    """Export type enumeration"""
    MANUAL = 'manual'
    SCHEDULED = 'scheduled'


@dataclass
class IntegrationValidationResult:
    """Result of integration validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    health_score: float  # 0.0 to 1.0
    last_checked: datetime


@dataclass
class ExportResult:
    """Result of export operation"""
    export_id: str
    status: ExportStatus
    records_processed: int
    records_exported: int
    records_skipped: int
    duration_seconds: Optional[float]
    result_sheet_url: Optional[str]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]


@dataclass
class ScheduleConfig:
    """Configuration for scheduled exports"""
    frequency: str  # 'hourly', 'daily', 'weekly'
    time: Optional[dt_time] = None  # For daily/weekly schedules
    enabled: bool = True


class IntegrationOrchestratorService:
    """
    Service for orchestrating Google Forms to Sheets integrations.
    
    This service coordinates all aspects of integration management including:
    - Integration lifecycle management
    - Export operation coordination
    - Health monitoring and validation
    - Progress tracking and status updates
    """

    def __init__(self):
        """Initialize the Integration Orchestrator Service"""
        self.logger = get_logger(self.__class__.__name__)
        self.cache = cache_manager
        
        # Configuration
        self.max_concurrent_exports = int(os.getenv('MAX_CONCURRENT_EXPORTS', '5'))
        self.export_timeout_minutes = int(os.getenv('EXPORT_TIMEOUT_MINUTES', '30'))
        self.health_check_interval_hours = int(os.getenv('HEALTH_CHECK_INTERVAL_HOURS', '24'))
        
        self.logger.info("Integration Orchestrator Service initialized")

    def create_integration(self, user_id: int, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[IntegrationConfig]]:
        """
        Create a new Google Forms to Sheets integration.
        
        Args:
            user_id: ID of the user creating the integration
            config_data: Integration configuration data
            
        Returns:
            Tuple of (success, message, integration_config)
        """
        try:
            # Validate required fields
            required_fields = ['name', 'google_form_id']
            missing_fields = [field for field in required_fields if not config_data.get(field)]
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}", None
            
            # Validate user has OAuth tokens for Google
            oauth_tokens = self._get_user_oauth_tokens(user_id)
            if not oauth_tokens or not oauth_tokens.is_active:
                return False, "User must authenticate with Google first", None
            
            # Create integration configuration
            integration = IntegrationConfig(
                user_id=user_id,
                name=config_data['name'],
                description=config_data.get('description', ''),
                google_form_id=config_data['google_form_id'],
                google_form_title=config_data.get('google_form_title', ''),
                google_sheet_id=config_data.get('google_sheet_id'),
                google_sheet_title=config_data.get('google_sheet_title', ''),
                sheet_tab_name=config_data.get('sheet_tab_name', 'Form Responses'),
                export_mode=config_data.get('export_mode', 'append_only'),
                include_timestamps=config_data.get('include_timestamps', True),
                include_response_id=config_data.get('include_response_id', True),
                transformation_rules=config_data.get('transformation_rules'),
                formatting_rules=config_data.get('formatting_rules'),
                custom_headers=config_data.get('custom_headers'),
                schedule_enabled=config_data.get('schedule_enabled', False),
                schedule_frequency=config_data.get('schedule_frequency', 'daily'),
                schedule_time=self._parse_schedule_time(config_data.get('schedule_time')),
                status=IntegrationStatus.ACTIVE.value
            )
            
            # Calculate next export time if scheduling is enabled
            if integration.schedule_enabled:
                integration.next_export_at = self._calculate_next_export_time(
                    integration.schedule_frequency,
                    integration.schedule_time
                )
            
            # Save to database
            db.session.add(integration)
            db.session.commit()
            
            self.logger.info(f"Created integration {integration.id} for user {user_id}")
            
            # Perform initial validation
            validation_result = self.validate_integration(integration.id)
            if not validation_result.is_valid:
                self.logger.warning(f"Integration {integration.id} created with validation warnings: {validation_result.errors}")
            
            return True, "Integration created successfully", integration
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error creating integration: {e}")
            return False, "Database error occurred", None
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating integration: {e}")
            return False, str(e), None

    def update_integration(self, integration_id: str, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[IntegrationConfig]]:
        """
        Update an existing integration configuration.
        
        Args:
            integration_id: ID of the integration to update
            config_data: Updated configuration data
            
        Returns:
            Tuple of (success, message, integration_config)
        """
        try:
            integration = IntegrationConfig.query.get(integration_id)
            if not integration:
                return False, "Integration not found", None
            
            # Update allowed fields
            updatable_fields = [
                'name', 'description', 'google_sheet_id', 'google_sheet_title',
                'sheet_tab_name', 'export_mode', 'include_timestamps', 'include_response_id',
                'transformation_rules', 'formatting_rules', 'custom_headers',
                'schedule_enabled', 'schedule_frequency', 'schedule_time', 'status'
            ]
            
            for field in updatable_fields:
                if field in config_data:
                    if field == 'schedule_time':
                        setattr(integration, field, self._parse_schedule_time(config_data[field]))
                    else:
                        setattr(integration, field, config_data[field])
            
            # Recalculate next export time if schedule changed
            if 'schedule_enabled' in config_data or 'schedule_frequency' in config_data or 'schedule_time' in config_data:
                if integration.schedule_enabled:
                    integration.next_export_at = self._calculate_next_export_time(
                        integration.schedule_frequency,
                        integration.schedule_time
                    )
                else:
                    integration.next_export_at = None
            
            integration.updated_at = datetime.utcnow()
            db.session.commit()
            
            self.logger.info(f"Updated integration {integration_id}")
            
            # Re-validate integration
            validation_result = self.validate_integration(integration_id)
            if not validation_result.is_valid:
                self.logger.warning(f"Integration {integration_id} updated with validation warnings: {validation_result.errors}")
            
            return True, "Integration updated successfully", integration
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error updating integration: {e}")
            return False, "Database error occurred", None
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating integration: {e}")
            return False, str(e), None

    def delete_integration(self, integration_id: str) -> Tuple[bool, str]:
        """
        Delete an integration and all associated data.
        
        Args:
            integration_id: ID of the integration to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            integration = IntegrationConfig.query.get(integration_id)
            if not integration:
                return False, "Integration not found"
            
            # Delete associated export history (cascade should handle this)
            db.session.delete(integration)
            db.session.commit()
            
            # Clear cache
            self._clear_integration_cache(integration_id)
            
            self.logger.info(f"Deleted integration {integration_id}")
            return True, "Integration deleted successfully"
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error deleting integration: {e}")
            return False, "Database error occurred"
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deleting integration: {e}")
            return False, str(e)

    def execute_export(self, integration_id: str, export_type: ExportType = ExportType.MANUAL, user_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Execute an export operation for the specified integration.
        
        Args:
            integration_id: ID of the integration to export
            export_type: Type of export (manual or scheduled)
            user_id: ID of the user requesting the export (for manual exports)
            
        Returns:
            Tuple of (success, message, export_id)
        """
        try:
            # Get integration configuration
            integration = IntegrationConfig.query.get(integration_id)
            if not integration:
                return False, "Integration not found", None
            
            # Check if integration is active
            if integration.status != IntegrationStatus.ACTIVE.value:
                return False, f"Integration is {integration.status}, cannot export", None
            
            # Check for concurrent exports
            active_exports = ExportHistory.query.filter(
                and_(
                    ExportHistory.integration_id == integration_id,
                    ExportHistory.status.in_([ExportStatus.PENDING.value, ExportStatus.RUNNING.value])
                )
            ).count()
            
            if active_exports >= self.max_concurrent_exports:
                return False, "Maximum concurrent exports reached for this integration", None
            
            # Create export history record
            export_history = ExportHistory(
                integration_id=integration_id,
                export_type=export_type.value,
                status=ExportStatus.PENDING.value,
                started_at=datetime.utcnow()
            )
            
            db.session.add(export_history)
            db.session.commit()
            
            export_id = export_history.id
            
            # Queue the export task (this would typically be a Celery task)
            # For now, we'll mark it as running and simulate the process
            self._queue_export_task(export_id, integration, export_type)
            
            # Update last export time for scheduled exports
            if export_type == ExportType.SCHEDULED:
                integration.last_export_at = datetime.utcnow()
                integration.next_export_at = self._calculate_next_export_time(
                    integration.schedule_frequency,
                    integration.schedule_time
                )
                db.session.commit()
            
            self.logger.info(f"Queued export {export_id} for integration {integration_id}")
            return True, "Export queued successfully", export_id
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error executing export: {e}")
            return False, "Database error occurred", None
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error executing export: {e}")
            return False, str(e), None

    def get_export_status(self, export_id: str) -> Optional[ExportResult]:
        """
        Get the status and results of an export operation.
        
        Args:
            export_id: ID of the export to check
            
        Returns:
            ExportResult object or None if not found
        """
        try:
            export_history = ExportHistory.query.get(export_id)
            if not export_history:
                return None
            
            # Calculate duration if completed
            duration_seconds = None
            if export_history.completed_at and export_history.started_at:
                duration_seconds = (export_history.completed_at - export_history.started_at).total_seconds()
            
            return ExportResult(
                export_id=export_history.id,
                status=ExportStatus(export_history.status),
                records_processed=export_history.records_processed,
                records_exported=export_history.records_exported,
                records_skipped=export_history.records_skipped,
                duration_seconds=duration_seconds,
                result_sheet_url=export_history.result_sheet_url,
                error_message=export_history.error_message,
                error_details=export_history.error_details
            )
            
        except Exception as e:
            self.logger.error(f"Error getting export status: {e}")
            return None

    def cancel_export(self, export_id: str) -> Tuple[bool, str]:
        """
        Cancel a pending or running export operation.
        
        Args:
            export_id: ID of the export to cancel
            
        Returns:
            Tuple of (success, message)
        """
        try:
            export_history = ExportHistory.query.get(export_id)
            if not export_history:
                return False, "Export not found"
            
            if export_history.status not in [ExportStatus.PENDING.value, ExportStatus.RUNNING.value]:
                return False, f"Cannot cancel export with status: {export_history.status}"
            
            # Update export status
            export_history.status = ExportStatus.FAILED.value
            export_history.completed_at = datetime.utcnow()
            export_history.error_message = "Export cancelled by user"
            
            db.session.commit()
            
            # Cancel the background task (implementation depends on task queue)
            self._cancel_export_task(export_id)
            
            self.logger.info(f"Cancelled export {export_id}")
            return True, "Export cancelled successfully"
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error cancelling export: {e}")
            return False, "Database error occurred"
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error cancelling export: {e}")
            return False, str(e)

    def validate_integration(self, integration_id: str) -> IntegrationValidationResult:
        """
        Validate an integration configuration and check its health.
        
        Args:
            integration_id: ID of the integration to validate
            
        Returns:
            IntegrationValidationResult with validation details
        """
        try:
            integration = IntegrationConfig.query.get(integration_id)
            if not integration:
                return IntegrationValidationResult(
                    is_valid=False,
                    errors=["Integration not found"],
                    warnings=[],
                    health_score=0.0,
                    last_checked=datetime.utcnow()
                )
            
            errors = []
            warnings = []
            health_score = 1.0
            
            # Check OAuth tokens
            oauth_tokens = self._get_user_oauth_tokens(integration.user_id)
            if not oauth_tokens:
                errors.append("User OAuth tokens not found")
                health_score -= 0.3
            elif not oauth_tokens.is_active:
                errors.append("User OAuth tokens are inactive")
                health_score -= 0.3
            elif oauth_tokens.is_expired():
                warnings.append("OAuth tokens are expired but may be refreshable")
                health_score -= 0.1
            
            # Check Google Form access
            if not integration.google_form_id:
                errors.append("Google Form ID is required")
                health_score -= 0.2
            else:
                # This would typically involve checking form accessibility
                # For now, we'll assume it's accessible if we have tokens
                pass
            
            # Check Google Sheet configuration
            if integration.export_mode in ['update_existing'] and not integration.google_sheet_id:
                errors.append("Google Sheet ID is required for update_existing mode")
                health_score -= 0.2
            
            # Check schedule configuration
            if integration.schedule_enabled:
                if not integration.schedule_frequency:
                    errors.append("Schedule frequency is required when scheduling is enabled")
                    health_score -= 0.1
                
                if integration.schedule_frequency in ['daily', 'weekly'] and not integration.schedule_time:
                    warnings.append("Schedule time not set for daily/weekly frequency")
                    health_score -= 0.05
            
            # Check recent export failures
            recent_failures = ExportHistory.query.filter(
                and_(
                    ExportHistory.integration_id == integration_id,
                    ExportHistory.status == ExportStatus.FAILED.value,
                    ExportHistory.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).count()
            
            if recent_failures > 5:
                warnings.append(f"High number of recent failures: {recent_failures}")
                health_score -= 0.1
            elif recent_failures > 2:
                warnings.append(f"Some recent failures: {recent_failures}")
                health_score -= 0.05
            
            # Ensure health score doesn't go below 0
            health_score = max(0.0, health_score)
            
            is_valid = len(errors) == 0
            
            return IntegrationValidationResult(
                is_valid=is_valid,
                errors=errors,
                warnings=warnings,
                health_score=health_score,
                last_checked=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error validating integration: {e}")
            return IntegrationValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                health_score=0.0,
                last_checked=datetime.utcnow()
            )

    def get_integration_health_status(self, integration_id: str) -> Dict[str, Any]:
        """
        Get comprehensive health status for an integration.
        
        Args:
            integration_id: ID of the integration to check
            
        Returns:
            Dictionary with health status information
        """
        try:
            integration = IntegrationConfig.query.get(integration_id)
            if not integration:
                return {"error": "Integration not found"}
            
            # Get validation results
            validation = self.validate_integration(integration_id)
            
            # Get recent export statistics
            recent_exports = ExportHistory.query.filter(
                and_(
                    ExportHistory.integration_id == integration_id,
                    ExportHistory.created_at >= datetime.utcnow() - timedelta(days=30)
                )
            ).all()
            
            total_exports = len(recent_exports)
            successful_exports = len([e for e in recent_exports if e.status == ExportStatus.COMPLETED.value])
            failed_exports = len([e for e in recent_exports if e.status == ExportStatus.FAILED.value])
            
            success_rate = (successful_exports / total_exports * 100) if total_exports > 0 else 0
            
            # Calculate average export time
            completed_exports = [e for e in recent_exports if e.status == ExportStatus.COMPLETED.value and e.duration_seconds]
            avg_export_time = sum(e.duration_seconds for e in completed_exports) / len(completed_exports) if completed_exports else 0
            
            return {
                "integration_id": integration_id,
                "status": integration.status,
                "health_score": validation.health_score,
                "is_valid": validation.is_valid,
                "errors": validation.errors,
                "warnings": validation.warnings,
                "last_validated": validation.last_checked.isoformat(),
                "export_statistics": {
                    "total_exports_30d": total_exports,
                    "successful_exports_30d": successful_exports,
                    "failed_exports_30d": failed_exports,
                    "success_rate_percent": round(success_rate, 2),
                    "average_export_time_seconds": round(avg_export_time, 2)
                },
                "last_export": integration.last_export_at.isoformat() if integration.last_export_at else None,
                "next_export": integration.next_export_at.isoformat() if integration.next_export_at else None,
                "schedule_enabled": integration.schedule_enabled
            }
            
        except Exception as e:
            self.logger.error(f"Error getting integration health status: {e}")
            return {"error": str(e)}

    def get_user_integrations(self, user_id: int, include_inactive: bool = False) -> List[IntegrationConfig]:
        """
        Get all integrations for a specific user.
        
        Args:
            user_id: ID of the user
            include_inactive: Whether to include inactive integrations
            
        Returns:
            List of IntegrationConfig objects
        """
        try:
            query = IntegrationConfig.query.filter(IntegrationConfig.user_id == user_id)
            
            if not include_inactive:
                query = query.filter(IntegrationConfig.status == IntegrationStatus.ACTIVE.value)
            
            return query.order_by(IntegrationConfig.created_at.desc()).all()
            
        except Exception as e:
            self.logger.error(f"Error getting user integrations: {e}")
            return []

    def get_scheduled_integrations(self) -> List[IntegrationConfig]:
        """
        Get all integrations that are due for scheduled export.
        
        Returns:
            List of IntegrationConfig objects ready for export
        """
        try:
            now = datetime.utcnow()
            
            return IntegrationConfig.query.filter(
                and_(
                    IntegrationConfig.schedule_enabled == True,
                    IntegrationConfig.status == IntegrationStatus.ACTIVE.value,
                    or_(
                        IntegrationConfig.next_export_at <= now,
                        IntegrationConfig.next_export_at.is_(None)
                    )
                )
            ).all()
            
        except Exception as e:
            self.logger.error(f"Error getting scheduled integrations: {e}")
            return []

    # Private helper methods

    def _get_user_oauth_tokens(self, user_id: int) -> Optional[OAuthTokens]:
        """Get active OAuth tokens for a user"""
        return OAuthTokens.query.filter(
            and_(
                OAuthTokens.user_id == user_id,
                OAuthTokens.provider == 'google',
                OAuthTokens.is_active == True
            )
        ).first()

    def _parse_schedule_time(self, time_str: Optional[str]) -> Optional[dt_time]:
        """Parse schedule time string to time object"""
        if not time_str:
            return None
        
        try:
            if isinstance(time_str, str):
                # Parse HH:MM format
                hour, minute = map(int, time_str.split(':'))
                return dt_time(hour, minute)
            return time_str
        except (ValueError, AttributeError):
            self.logger.warning(f"Invalid schedule time format: {time_str}")
            return None

    def _calculate_next_export_time(self, frequency: str, schedule_time: Optional[dt_time]) -> datetime:
        """Calculate the next export time based on frequency and schedule"""
        now = datetime.utcnow()
        
        if frequency == 'hourly':
            return now + timedelta(hours=1)
        elif frequency == 'daily':
            next_time = now.replace(
                hour=schedule_time.hour if schedule_time else 0,
                minute=schedule_time.minute if schedule_time else 0,
                second=0,
                microsecond=0
            )
            if next_time <= now:
                next_time += timedelta(days=1)
            return next_time
        elif frequency == 'weekly':
            # Schedule for same time next week
            next_time = now.replace(
                hour=schedule_time.hour if schedule_time else 0,
                minute=schedule_time.minute if schedule_time else 0,
                second=0,
                microsecond=0
            )
            days_ahead = 7 - now.weekday()  # Days until next Monday
            if days_ahead == 7:  # If today is Monday
                days_ahead = 0
            next_time += timedelta(days=days_ahead)
            if next_time <= now:
                next_time += timedelta(days=7)
            return next_time
        else:
            # Default to daily
            return now + timedelta(days=1)

    def _queue_export_task(self, export_id: str, integration: IntegrationConfig, export_type: ExportType):
        """Queue an export task for background processing"""
        # This would typically queue a Celery task
        # For now, we'll just log the action
        self.logger.info(f"Queuing export task for export {export_id}, integration {integration.id}")
        
        # Update status to running (in a real implementation, this would be done by the task)
        try:
            export_history = ExportHistory.query.get(export_id)
            if export_history:
                export_history.status = ExportStatus.RUNNING.value
                db.session.commit()
        except Exception as e:
            self.logger.error(f"Error updating export status: {e}")

    def _cancel_export_task(self, export_id: str):
        """Cancel a background export task"""
        # This would typically cancel a Celery task
        self.logger.info(f"Cancelling export task for export {export_id}")

    def _clear_integration_cache(self, integration_id: str):
        """Clear cached data for an integration"""
        if self.cache:
            cache_keys = [
                f"integration_validation_{integration_id}",
                f"integration_health_{integration_id}",
                f"integration_exports_{integration_id}"
            ]
            for key in cache_keys:
                self.cache.delete(key)