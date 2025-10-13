# Integration Orchestrator Service

## Overview

The Integration Orchestrator Service is a comprehensive service that coordinates Google Forms to Sheets integration operations. It acts as the main coordinator for all integration activities, managing the lifecycle of integrations, export operations, and health monitoring.

## Features

### Core Functionality
- **Integration Management**: Create, update, delete, and manage Google Forms to Sheets integrations
- **Export Coordination**: Execute and monitor export operations with progress tracking
- **Health Monitoring**: Validate integration configurations and monitor health status
- **Schedule Management**: Handle scheduled exports with flexible frequency options
- **Error Handling**: Comprehensive error handling and recovery mechanisms

### Key Components

#### Integration Lifecycle Management
- Create new integrations with validation
- Update existing integration configurations
- Delete integrations and associated data
- Manage integration status (active, paused, error)

#### Export Operations
- Execute manual and scheduled exports
- Track export progress and status
- Handle concurrent export limitations
- Cancel running exports
- Maintain export history

#### Validation and Health Checking
- Validate integration configurations
- Check OAuth token status and expiration
- Monitor integration health scores
- Generate comprehensive health reports

#### Schedule Management
- Support for hourly, daily, and weekly schedules
- Calculate next export times
- Manage scheduled export execution
- Handle schedule configuration changes

## API Reference

### Core Methods

#### Integration Management

```python
def create_integration(user_id: int, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[IntegrationConfig]]
```
Creates a new Google Forms to Sheets integration.

**Parameters:**
- `user_id`: ID of the user creating the integration
- `config_data`: Integration configuration data

**Returns:**
- Tuple of (success, message, integration_config)

**Required config_data fields:**
- `name`: Integration name
- `google_form_id`: Google Form ID to integrate

**Optional config_data fields:**
- `description`: Integration description
- `google_sheet_id`: Target Google Sheet ID
- `export_mode`: 'create_new', 'update_existing', or 'append_only'
- `schedule_enabled`: Enable scheduled exports
- `schedule_frequency`: 'hourly', 'daily', or 'weekly'
- `transformation_rules`: Data transformation rules
- `formatting_rules`: Data formatting rules

```python
def update_integration(integration_id: str, config_data: Dict[str, Any]) -> Tuple[bool, str, Optional[IntegrationConfig]]
```
Updates an existing integration configuration.

```python
def delete_integration(integration_id: str) -> Tuple[bool, str]
```
Deletes an integration and all associated data.

#### Export Operations

```python
def execute_export(integration_id: str, export_type: ExportType = ExportType.MANUAL, user_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]
```
Executes an export operation for the specified integration.

**Parameters:**
- `integration_id`: ID of the integration to export
- `export_type`: ExportType.MANUAL or ExportType.SCHEDULED
- `user_id`: ID of the user requesting the export (for manual exports)

**Returns:**
- Tuple of (success, message, export_id)

```python
def get_export_status(export_id: str) -> Optional[ExportResult]
```
Gets the status and results of an export operation.

```python
def cancel_export(export_id: str) -> Tuple[bool, str]
```
Cancels a pending or running export operation.

#### Validation and Health

```python
def validate_integration(integration_id: str) -> IntegrationValidationResult
```
Validates an integration configuration and checks its health.

**Returns:**
- `IntegrationValidationResult` with validation details including:
  - `is_valid`: Boolean indicating if integration is valid
  - `errors`: List of validation errors
  - `warnings`: List of validation warnings
  - `health_score`: Float from 0.0 to 1.0 indicating health
  - `last_checked`: Timestamp of validation

```python
def get_integration_health_status(integration_id: str) -> Dict[str, Any]
```
Gets comprehensive health status for an integration.

#### User and Schedule Management

```python
def get_user_integrations(user_id: int, include_inactive: bool = False) -> List[IntegrationConfig]
```
Gets all integrations for a specific user.

```python
def get_scheduled_integrations() -> List[IntegrationConfig]
```
Gets all integrations that are due for scheduled export.

## Data Models

### IntegrationConfig
Represents a Google Forms to Sheets integration configuration.

**Key Fields:**
- `id`: Unique integration identifier
- `user_id`: Owner user ID
- `name`: Integration name
- `google_form_id`: Source Google Form ID
- `google_sheet_id`: Target Google Sheet ID (optional)
- `export_mode`: Export behavior ('create_new', 'update_existing', 'append_only')
- `schedule_enabled`: Whether scheduling is enabled
- `schedule_frequency`: Schedule frequency ('hourly', 'daily', 'weekly')
- `status`: Integration status ('active', 'paused', 'error')

### ExportHistory
Tracks export operations and their results.

**Key Fields:**
- `id`: Unique export identifier
- `integration_id`: Associated integration ID
- `export_type`: 'manual' or 'scheduled'
- `status`: Export status ('pending', 'running', 'completed', 'failed')
- `records_processed`: Number of records processed
- `records_exported`: Number of records successfully exported
- `duration_seconds`: Export duration
- `result_sheet_url`: URL of the resulting Google Sheet

### ExportResult
Data class representing export operation results.

**Fields:**
- `export_id`: Export identifier
- `status`: Export status
- `records_processed`: Number of records processed
- `records_exported`: Number of records exported
- `records_skipped`: Number of records skipped
- `duration_seconds`: Export duration
- `result_sheet_url`: Result sheet URL
- `error_message`: Error message if failed
- `error_details`: Detailed error information

### IntegrationValidationResult
Data class representing integration validation results.

**Fields:**
- `is_valid`: Whether integration is valid
- `errors`: List of validation errors
- `warnings`: List of validation warnings
- `health_score`: Health score (0.0 to 1.0)
- `last_checked`: Validation timestamp

## Configuration

### Environment Variables

- `MAX_CONCURRENT_EXPORTS`: Maximum concurrent exports per integration (default: 5)
- `EXPORT_TIMEOUT_MINUTES`: Export timeout in minutes (default: 30)
- `HEALTH_CHECK_INTERVAL_HOURS`: Health check interval in hours (default: 24)

### Dependencies

The service requires:
- Valid OAuth tokens for Google API access
- Database models for integration storage
- Caching system for performance optimization
- Logging system for monitoring and debugging

## Usage Examples

### Creating an Integration

```python
from app.services.integration_orchestrator_service import IntegrationOrchestratorService

orchestrator = IntegrationOrchestratorService()

config_data = {
    'name': 'Customer Feedback Integration',
    'description': 'Export customer feedback to analysis sheet',
    'google_form_id': '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
    'google_sheet_id': '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
    'export_mode': 'append_only',
    'schedule_enabled': True,
    'schedule_frequency': 'daily',
    'schedule_time': '09:00'
}

success, message, integration = orchestrator.create_integration(user_id=1, config_data=config_data)

if success:
    print(f"Integration created: {integration.id}")
else:
    print(f"Failed to create integration: {message}")
```

### Executing an Export

```python
success, message, export_id = orchestrator.execute_export(
    integration_id=integration.id,
    export_type=ExportType.MANUAL,
    user_id=1
)

if success:
    print(f"Export queued: {export_id}")
    
    # Check export status
    export_result = orchestrator.get_export_status(export_id)
    if export_result:
        print(f"Export status: {export_result.status}")
        print(f"Records processed: {export_result.records_processed}")
```

### Validating an Integration

```python
validation_result = orchestrator.validate_integration(integration.id)

print(f"Integration valid: {validation_result.is_valid}")
print(f"Health score: {validation_result.health_score}")

if validation_result.errors:
    print("Errors:")
    for error in validation_result.errors:
        print(f"  - {error}")

if validation_result.warnings:
    print("Warnings:")
    for warning in validation_result.warnings:
        print(f"  - {warning}")
```

### Getting Health Status

```python
health_status = orchestrator.get_integration_health_status(integration.id)

print(f"Health score: {health_status['health_score']}")
print(f"Success rate: {health_status['export_statistics']['success_rate_percent']}%")
print(f"Total exports (30d): {health_status['export_statistics']['total_exports_30d']}")
```

## Error Handling

The service implements comprehensive error handling:

### Database Errors
- Automatic rollback on database failures
- Graceful handling of constraint violations
- Connection pool management

### API Errors
- OAuth token validation and refresh
- Google API rate limiting handling
- Network timeout management

### Validation Errors
- Configuration validation
- Data integrity checks
- Permission verification

### Recovery Mechanisms
- Automatic retry for transient failures
- Circuit breaker pattern for API failures
- Graceful degradation on service unavailability

## Testing

The service includes comprehensive unit tests covering:

- Integration lifecycle operations
- Export execution and monitoring
- Validation and health checking
- Schedule calculations
- Error handling scenarios

### Running Tests

```bash
# Run all tests
python -m pytest tests/test_integration_orchestrator_service.py -v

# Run specific test class
python -m pytest tests/test_integration_orchestrator_service.py::TestIntegrationCreation -v

# Run simple unit tests (no database)
python test_integration_orchestrator_simple.py
```

## Performance Considerations

### Caching
- Integration validation results cached for 30 minutes
- User credentials cached for 15 minutes
- Form metadata cached for 1 hour

### Concurrency
- Configurable maximum concurrent exports per integration
- Background task queuing for export operations
- Non-blocking validation and health checks

### Database Optimization
- Indexed queries for integration lookups
- Connection pooling for concurrent operations
- Efficient pagination for large result sets

## Security

### Data Protection
- OAuth tokens encrypted at rest
- Secure credential storage and rotation
- Input validation and sanitization

### Access Control
- User-based resource isolation
- Role-based permission checking
- Audit logging for all operations

### API Security
- Rate limiting per user and endpoint
- HTTPS-only communications
- Token-based authentication

## Monitoring and Logging

The service provides comprehensive monitoring:

### Metrics
- Export completion times and success rates
- Integration health scores
- API response times and error rates
- Resource utilization statistics

### Logging
- Structured JSON logging
- Configurable log levels
- Request/response correlation IDs
- Performance timing information

### Alerting
- Failed export notifications
- Health score degradation alerts
- OAuth token expiration warnings
- System resource alerts

## Future Enhancements

### Planned Features
- Multi-destination export support
- Advanced data transformation rules
- Real-time export progress tracking
- Integration templates and presets
- Bulk operation support

### Performance Improvements
- Streaming export for large datasets
- Parallel processing optimization
- Advanced caching strategies
- Database query optimization

### Monitoring Enhancements
- Real-time dashboards
- Predictive health monitoring
- Automated recovery mechanisms
- Advanced analytics and reporting