"""
Unit tests for Integration Orchestrator Service

Tests all aspects of integration orchestration including:
- Integration creation, update, and deletion
- Export execution and status tracking
- Integration validation and health checking
- Schedule management and calculations
- Error handling and edge cases
"""

import pytest
import uuid
from datetime import datetime, timedelta, time as dt_time
from unittest.mock import Mock, patch, MagicMock

from app import create_app, db
from app.models.production.integration_models import IntegrationConfig, ExportHistory, OAuthTokens
from app.services.integration_orchestrator_service import (
    IntegrationOrchestratorService,
    IntegrationStatus,
    ExportStatus,
    ExportType,
    IntegrationValidationResult,
    ExportResult,
    ScheduleConfig
)


@pytest.fixture
def app():
    """Create test Flask application"""
    app, socketio = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def orchestrator_service():
    """Create Integration Orchestrator Service instance"""
    return IntegrationOrchestratorService()


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return 1


@pytest.fixture
def sample_oauth_tokens(app, sample_user_id):
    """Create sample OAuth tokens for testing"""
    with app.app_context():
        tokens = OAuthTokens(
            user_id=sample_user_id,
            provider='google',
            access_token='encrypted_access_token',
            refresh_token='encrypted_refresh_token',
            expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=['https://www.googleapis.com/auth/forms.responses.readonly'],
            is_active=True
        )
        db.session.add(tokens)
        db.session.commit()
        return tokens


@pytest.fixture
def sample_integration_config():
    """Sample integration configuration data"""
    return {
        'name': 'Test Integration',
        'description': 'Test integration for unit tests',
        'google_form_id': 'test_form_id_123',
        'google_form_title': 'Test Form',
        'google_sheet_id': 'test_sheet_id_456',
        'google_sheet_title': 'Test Sheet',
        'sheet_tab_name': 'Responses',
        'export_mode': 'append_only',
        'include_timestamps': True,
        'include_response_id': True,
        'schedule_enabled': True,
        'schedule_frequency': 'daily',
        'schedule_time': '09:00'
    }


class TestIntegrationCreation:
    """Test integration creation functionality"""

    def test_create_integration_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test successful integration creation"""
        with app.app_context():
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            
            assert success is True
            assert "successfully" in message
            assert integration is not None
            assert integration.name == sample_integration_config['name']
            assert integration.user_id == sample_user_id
            assert integration.status == IntegrationStatus.ACTIVE.value
            assert integration.next_export_at is not None  # Should be calculated for scheduled integration

    def test_create_integration_missing_required_fields(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens):
        """Test integration creation with missing required fields"""
        with app.app_context():
            incomplete_config = {'description': 'Missing name and form_id'}
            
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, incomplete_config
            )
            
            assert success is False
            assert "Missing required fields" in message
            assert integration is None

    def test_create_integration_no_oauth_tokens(self, app, orchestrator_service, sample_user_id, sample_integration_config):
        """Test integration creation without OAuth tokens"""
        with app.app_context():
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            
            assert success is False
            assert "authenticate with Google" in message
            assert integration is None

    def test_create_integration_inactive_oauth_tokens(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test integration creation with inactive OAuth tokens"""
        with app.app_context():
            # Make tokens inactive
            sample_oauth_tokens.is_active = False
            db.session.commit()
            
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            
            assert success is False
            assert "authenticate with Google" in message
            assert integration is None


class TestIntegrationUpdate:
    """Test integration update functionality"""

    def test_update_integration_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test successful integration update"""
        with app.app_context():
            # Create integration first
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Update integration
            update_data = {
                'name': 'Updated Integration Name',
                'description': 'Updated description',
                'schedule_frequency': 'weekly'
            }
            
            success, message, updated_integration = orchestrator_service.update_integration(
                integration.id, update_data
            )
            
            assert success is True
            assert "successfully" in message
            assert updated_integration.name == update_data['name']
            assert updated_integration.description == update_data['description']
            assert updated_integration.schedule_frequency == update_data['schedule_frequency']

    def test_update_integration_not_found(self, app, orchestrator_service):
        """Test updating non-existent integration"""
        with app.app_context():
            fake_id = str(uuid.uuid4())
            update_data = {'name': 'Updated Name'}
            
            success, message, integration = orchestrator_service.update_integration(
                fake_id, update_data
            )
            
            assert success is False
            assert "not found" in message
            assert integration is None

    def test_update_integration_schedule_changes(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test integration update with schedule changes"""
        with app.app_context():
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            original_next_export = integration.next_export_at
            
            # Update schedule
            update_data = {
                'schedule_frequency': 'hourly',
                'schedule_time': None
            }
            
            success, message, updated_integration = orchestrator_service.update_integration(
                integration.id, update_data
            )
            
            assert success is True
            assert updated_integration.schedule_frequency == 'hourly'
            assert updated_integration.next_export_at != original_next_export


class TestIntegrationDeletion:
    """Test integration deletion functionality"""

    def test_delete_integration_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test successful integration deletion"""
        with app.app_context():
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            integration_id = integration.id
            
            # Delete integration
            success, message = orchestrator_service.delete_integration(integration_id)
            
            assert success is True
            assert "successfully" in message
            
            # Verify deletion
            deleted_integration = IntegrationConfig.query.get(integration_id)
            assert deleted_integration is None

    def test_delete_integration_not_found(self, app, orchestrator_service):
        """Test deleting non-existent integration"""
        with app.app_context():
            fake_id = str(uuid.uuid4())
            
            success, message = orchestrator_service.delete_integration(fake_id)
            
            assert success is False
            assert "not found" in message


class TestExportExecution:
    """Test export execution functionality"""

    def test_execute_export_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test successful export execution"""
        with app.app_context():
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Execute export
            success, message, export_id = orchestrator_service.execute_export(
                integration.id, ExportType.MANUAL, sample_user_id
            )
            
            assert success is True
            assert "queued successfully" in message
            assert export_id is not None
            
            # Verify export history record
            export_history = ExportHistory.query.get(export_id)
            assert export_history is not None
            assert export_history.integration_id == integration.id
            assert export_history.export_type == ExportType.MANUAL.value

    def test_execute_export_integration_not_found(self, app, orchestrator_service):
        """Test export execution with non-existent integration"""
        with app.app_context():
            fake_id = str(uuid.uuid4())
            
            success, message, export_id = orchestrator_service.execute_export(
                fake_id, ExportType.MANUAL
            )
            
            assert success is False
            assert "not found" in message
            assert export_id is None

    def test_execute_export_inactive_integration(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test export execution with inactive integration"""
        with app.app_context():
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Make integration inactive
            integration.status = IntegrationStatus.PAUSED.value
            db.session.commit()
            
            # Try to execute export
            success, message, export_id = orchestrator_service.execute_export(
                integration.id, ExportType.MANUAL
            )
            
            assert success is False
            assert "paused" in message
            assert export_id is None

    @patch('app.services.integration_orchestrator_service.IntegrationOrchestratorService.max_concurrent_exports', 1)
    def test_execute_export_max_concurrent_reached(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test export execution when max concurrent exports reached"""
        with app.app_context():
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Create a running export
            running_export = ExportHistory(
                integration_id=integration.id,
                export_type=ExportType.MANUAL.value,
                status=ExportStatus.RUNNING.value,
                started_at=datetime.utcnow()
            )
            db.session.add(running_export)
            db.session.commit()
            
            # Try to execute another export
            success, message, export_id = orchestrator_service.execute_export(
                integration.id, ExportType.MANUAL
            )
            
            assert success is False
            assert "Maximum concurrent exports" in message
            assert export_id is None


class TestExportStatus:
    """Test export status functionality"""

    def test_get_export_status_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test getting export status"""
        with app.app_context():
            # Create integration and export
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            success, message, export_id = orchestrator_service.execute_export(
                integration.id, ExportType.MANUAL
            )
            assert success is True
            
            # Get export status
            export_result = orchestrator_service.get_export_status(export_id)
            
            assert export_result is not None
            assert export_result.export_id == export_id
            assert export_result.status in [ExportStatus.PENDING, ExportStatus.RUNNING]

    def test_get_export_status_not_found(self, app, orchestrator_service):
        """Test getting status for non-existent export"""
        with app.app_context():
            fake_id = str(uuid.uuid4())
            
            export_result = orchestrator_service.get_export_status(fake_id)
            
            assert export_result is None


class TestExportCancellation:
    """Test export cancellation functionality"""

    def test_cancel_export_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test successful export cancellation"""
        with app.app_context():
            # Create integration and export
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            success, message, export_id = orchestrator_service.execute_export(
                integration.id, ExportType.MANUAL
            )
            assert success is True
            
            # Cancel export
            success, message = orchestrator_service.cancel_export(export_id)
            
            assert success is True
            assert "cancelled successfully" in message
            
            # Verify cancellation
            export_history = ExportHistory.query.get(export_id)
            assert export_history.status == ExportStatus.FAILED.value
            assert "cancelled" in export_history.error_message

    def test_cancel_export_not_found(self, app, orchestrator_service):
        """Test cancelling non-existent export"""
        with app.app_context():
            fake_id = str(uuid.uuid4())
            
            success, message = orchestrator_service.cancel_export(fake_id)
            
            assert success is False
            assert "not found" in message

    def test_cancel_export_already_completed(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test cancelling already completed export"""
        with app.app_context():
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Create completed export
            completed_export = ExportHistory(
                integration_id=integration.id,
                export_type=ExportType.MANUAL.value,
                status=ExportStatus.COMPLETED.value,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.session.add(completed_export)
            db.session.commit()
            
            # Try to cancel
            success, message = orchestrator_service.cancel_export(completed_export.id)
            
            assert success is False
            assert "Cannot cancel" in message


class TestIntegrationValidation:
    """Test integration validation functionality"""

    def test_validate_integration_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test successful integration validation"""
        with app.app_context():
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Validate integration
            validation_result = orchestrator_service.validate_integration(integration.id)
            
            assert isinstance(validation_result, IntegrationValidationResult)
            assert validation_result.is_valid is True
            assert validation_result.health_score > 0.5
            assert len(validation_result.errors) == 0

    def test_validate_integration_not_found(self, app, orchestrator_service):
        """Test validating non-existent integration"""
        with app.app_context():
            fake_id = str(uuid.uuid4())
            
            validation_result = orchestrator_service.validate_integration(fake_id)
            
            assert validation_result.is_valid is False
            assert "not found" in validation_result.errors[0]
            assert validation_result.health_score == 0.0

    def test_validate_integration_no_oauth_tokens(self, app, orchestrator_service, sample_user_id, sample_integration_config):
        """Test validating integration without OAuth tokens"""
        with app.app_context():
            # Create integration without OAuth tokens
            integration = IntegrationConfig(
                user_id=sample_user_id,
                name=sample_integration_config['name'],
                google_form_id=sample_integration_config['google_form_id'],
                status=IntegrationStatus.ACTIVE.value
            )
            db.session.add(integration)
            db.session.commit()
            
            # Validate integration
            validation_result = orchestrator_service.validate_integration(integration.id)
            
            assert validation_result.is_valid is False
            assert any("OAuth tokens not found" in error for error in validation_result.errors)
            assert validation_result.health_score < 0.8

    def test_validate_integration_expired_tokens(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test validating integration with expired OAuth tokens"""
        with app.app_context():
            # Make tokens expired
            sample_oauth_tokens.expires_at = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Validate integration
            validation_result = orchestrator_service.validate_integration(integration.id)
            
            assert len(validation_result.warnings) > 0
            assert any("expired" in warning for warning in validation_result.warnings)


class TestHealthStatus:
    """Test integration health status functionality"""

    def test_get_integration_health_status_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test getting integration health status"""
        with app.app_context():
            # Create integration
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Get health status
            health_status = orchestrator_service.get_integration_health_status(integration.id)
            
            assert "error" not in health_status
            assert health_status["integration_id"] == integration.id
            assert health_status["status"] == integration.status
            assert "health_score" in health_status
            assert "export_statistics" in health_status
            assert health_status["schedule_enabled"] == integration.schedule_enabled

    def test_get_integration_health_status_not_found(self, app, orchestrator_service):
        """Test getting health status for non-existent integration"""
        with app.app_context():
            fake_id = str(uuid.uuid4())
            
            health_status = orchestrator_service.get_integration_health_status(fake_id)
            
            assert "error" in health_status
            assert "not found" in health_status["error"]


class TestUserIntegrations:
    """Test user integration retrieval functionality"""

    def test_get_user_integrations_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test getting user integrations"""
        with app.app_context():
            # Create multiple integrations
            success, message, integration1 = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            config2 = sample_integration_config.copy()
            config2['name'] = 'Second Integration'
            config2['google_form_id'] = 'form_id_2'
            
            success, message, integration2 = orchestrator_service.create_integration(
                sample_user_id, config2
            )
            assert success is True
            
            # Get user integrations
            integrations = orchestrator_service.get_user_integrations(sample_user_id)
            
            assert len(integrations) == 2
            assert all(integration.user_id == sample_user_id for integration in integrations)

    def test_get_user_integrations_include_inactive(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test getting user integrations including inactive ones"""
        with app.app_context():
            # Create active integration
            success, message, active_integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Create inactive integration
            config2 = sample_integration_config.copy()
            config2['name'] = 'Inactive Integration'
            config2['google_form_id'] = 'form_id_2'
            
            success, message, inactive_integration = orchestrator_service.create_integration(
                sample_user_id, config2
            )
            assert success is True
            
            # Make second integration inactive
            inactive_integration.status = IntegrationStatus.PAUSED.value
            db.session.commit()
            
            # Get active integrations only
            active_integrations = orchestrator_service.get_user_integrations(sample_user_id, include_inactive=False)
            assert len(active_integrations) == 1
            assert active_integrations[0].status == IntegrationStatus.ACTIVE.value
            
            # Get all integrations
            all_integrations = orchestrator_service.get_user_integrations(sample_user_id, include_inactive=True)
            assert len(all_integrations) == 2


class TestScheduledIntegrations:
    """Test scheduled integration functionality"""

    def test_get_scheduled_integrations_success(self, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test getting scheduled integrations"""
        with app.app_context():
            # Create scheduled integration with past next_export_at
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            assert success is True
            
            # Set next export time to past
            integration.next_export_at = datetime.utcnow() - timedelta(hours=1)
            db.session.commit()
            
            # Get scheduled integrations
            scheduled_integrations = orchestrator_service.get_scheduled_integrations()
            
            assert len(scheduled_integrations) >= 1
            assert integration.id in [i.id for i in scheduled_integrations]
            assert all(i.schedule_enabled for i in scheduled_integrations)
            assert all(i.status == IntegrationStatus.ACTIVE.value for i in scheduled_integrations)


class TestScheduleCalculations:
    """Test schedule calculation functionality"""

    def test_calculate_next_export_time_hourly(self, app, orchestrator_service):
        """Test hourly schedule calculation"""
        with app.app_context():
            next_time = orchestrator_service._calculate_next_export_time('hourly', None)
            
            assert next_time > datetime.utcnow()
            assert (next_time - datetime.utcnow()).total_seconds() <= 3600  # Within 1 hour

    def test_calculate_next_export_time_daily(self, app, orchestrator_service):
        """Test daily schedule calculation"""
        with app.app_context():
            schedule_time = dt_time(9, 0)  # 9:00 AM
            next_time = orchestrator_service._calculate_next_export_time('daily', schedule_time)
            
            assert next_time > datetime.utcnow()
            assert next_time.hour == 9
            assert next_time.minute == 0

    def test_calculate_next_export_time_weekly(self, app, orchestrator_service):
        """Test weekly schedule calculation"""
        with app.app_context():
            schedule_time = dt_time(10, 30)  # 10:30 AM
            next_time = orchestrator_service._calculate_next_export_time('weekly', schedule_time)
            
            assert next_time > datetime.utcnow()
            assert next_time.hour == 10
            assert next_time.minute == 30

    def test_parse_schedule_time_valid(self, app, orchestrator_service):
        """Test parsing valid schedule time"""
        with app.app_context():
            time_obj = orchestrator_service._parse_schedule_time('14:30')
            
            assert time_obj is not None
            assert time_obj.hour == 14
            assert time_obj.minute == 30

    def test_parse_schedule_time_invalid(self, app, orchestrator_service):
        """Test parsing invalid schedule time"""
        with app.app_context():
            time_obj = orchestrator_service._parse_schedule_time('invalid_time')
            
            assert time_obj is None


class TestErrorHandling:
    """Test error handling in various scenarios"""

    @patch('app.services.integration_orchestrator_service.db.session.commit')
    def test_create_integration_database_error(self, mock_commit, app, orchestrator_service, sample_user_id, sample_oauth_tokens, sample_integration_config):
        """Test handling database errors during integration creation"""
        with app.app_context():
            mock_commit.side_effect = Exception("Database error")
            
            success, message, integration = orchestrator_service.create_integration(
                sample_user_id, sample_integration_config
            )
            
            assert success is False
            assert "Database error" in message
            assert integration is None

    @patch('app.services.integration_orchestrator_service.IntegrationConfig.query')
    def test_validate_integration_query_error(self, mock_query, app, orchestrator_service):
        """Test handling query errors during validation"""
        with app.app_context():
            mock_query.get.side_effect = Exception("Query error")
            
            validation_result = orchestrator_service.validate_integration("test_id")
            
            assert validation_result.is_valid is False
            assert "Validation error" in validation_result.errors[0]
            assert validation_result.health_score == 0.0


if __name__ == '__main__':
    pytest.main([__file__])