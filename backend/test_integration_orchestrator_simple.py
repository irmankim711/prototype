"""
Simple unit test for Integration Orchestrator Service
Tests the service logic without database dependencies
"""

import pytest
from datetime import datetime, time as dt_time
from unittest.mock import Mock, patch

from app.services.integration_orchestrator_service import (
    IntegrationOrchestratorService,
    IntegrationStatus,
    ExportStatus,
    ExportType
)


def test_orchestrator_service_initialization():
    """Test that the service initializes correctly"""
    service = IntegrationOrchestratorService()
    
    assert service is not None
    assert hasattr(service, 'logger')
    assert hasattr(service, 'cache')
    assert service.max_concurrent_exports >= 1
    assert service.export_timeout_minutes > 0


def test_parse_schedule_time_valid():
    """Test parsing valid schedule time"""
    service = IntegrationOrchestratorService()
    
    time_obj = service._parse_schedule_time('14:30')
    
    assert time_obj is not None
    assert time_obj.hour == 14
    assert time_obj.minute == 30


def test_parse_schedule_time_invalid():
    """Test parsing invalid schedule time"""
    service = IntegrationOrchestratorService()
    
    time_obj = service._parse_schedule_time('invalid_time')
    
    assert time_obj is None


def test_calculate_next_export_time_hourly():
    """Test hourly schedule calculation"""
    service = IntegrationOrchestratorService()
    
    next_time = service._calculate_next_export_time('hourly', None)
    
    assert next_time > datetime.utcnow()
    assert (next_time - datetime.utcnow()).total_seconds() <= 3600  # Within 1 hour


def test_calculate_next_export_time_daily():
    """Test daily schedule calculation"""
    service = IntegrationOrchestratorService()
    
    schedule_time = dt_time(9, 0)  # 9:00 AM
    next_time = service._calculate_next_export_time('daily', schedule_time)
    
    assert next_time > datetime.utcnow()
    assert next_time.hour == 9
    assert next_time.minute == 0


def test_calculate_next_export_time_weekly():
    """Test weekly schedule calculation"""
    service = IntegrationOrchestratorService()
    
    schedule_time = dt_time(10, 30)  # 10:30 AM
    next_time = service._calculate_next_export_time('weekly', schedule_time)
    
    assert next_time > datetime.utcnow()
    assert next_time.hour == 10
    assert next_time.minute == 30


if __name__ == '__main__':
    pytest.main([__file__])