# Comprehensive Health Check and Monitoring System

This document outlines the comprehensive health check and monitoring system implemented for the application, including system status monitoring, performance metrics, and graceful shutdown handling.

## 🏥 Health Check System

### Overview
The health check system provides comprehensive monitoring of:
- **Database connectivity** and performance
- **Redis connectivity** and performance  
- **External API connectivity** (Google, Microsoft, OpenAI)
- **System resources** (CPU, memory, disk)
- **Application status** and responsiveness

### Health Check Endpoints

#### 1. `/health` - Comprehensive Health Check
```bash
GET /health
```
Returns detailed system status including:
- Overall system health (healthy/degraded/unhealthy)
- Individual service status
- Performance metrics
- Timestamps and correlation IDs

**Response Example:**
```json
{
  "status": "healthy",
  "message": "System status: healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "summary": {
    "status": "healthy",
    "total_checks": 5,
    "healthy_checks": 5,
    "degraded_checks": 0,
    "unhealthy_checks": 0
  },
  "checks": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Database connection healthy",
      "details": {
        "query_duration_ms": 45.2,
        "connection_pool_size": 10
      }
    }
  ]
}
```

#### 2. `/health/simple` - Simple Health Check
```bash
GET /health/simple
```
Lightweight endpoint for load balancers and basic health monitoring.

#### 3. `/health/ready` - Readiness Probe
```bash
GET /health/ready
```
Kubernetes readiness probe endpoint. Checks if the application is ready to receive traffic.

#### 4. `/health/live` - Liveness Probe
```bash
GET /health/live
```
Kubernetes liveness probe endpoint. Verifies the application is alive and responding.

#### 5. `/health/performance` - Performance Metrics
```bash
GET /health/performance?hours=24
```
Returns performance metrics for the last N hours (requires authentication).

#### 6. `/health/check/<check_name>` - Specific Health Check
```bash
GET /health/check/database
GET /health/check/redis
GET /health/check/system_resources
```
Run a specific health check by name.

#### 7. `/health/refresh` - Force Refresh
```bash
POST /health/refresh
```
Force refresh of health check cache (requires authentication).

#### 8. `/health/status` - Current Status
```bash
GET /health/status
```
Get current health status without running checks.

## 📊 Metrics and Monitoring

### Prometheus Integration
The system provides a `/metrics` endpoint that exposes Prometheus-compatible metrics:

- **HTTP Metrics**: Request count, duration, size, active requests
- **Database Metrics**: Query count, duration, connection count
- **Redis Metrics**: Operation count, duration, connection count
- **Business Metrics**: User logins, form submissions, report generations

### Performance Monitoring
The `PerformanceMonitor` class tracks:
- Request performance metrics
- Database query performance
- Redis operation performance
- External API call performance
- System resource usage

### Structured Logging
All health checks and monitoring events use structured logging with:
- Correlation IDs for request tracking
- Request context (user ID, IP address, user agent)
- Performance metrics
- Error details and stack traces

## 🔧 Configuration

### Health Check Configuration
```python
# Register health checks
from app.core.health_checks import (
    HealthCheckRegistry,
    DatabaseHealthCheck,
    RedisHealthCheck,
    ExternalAPIHealthCheck,
    SystemResourceHealthCheck
)

registry = HealthCheckRegistry()

# Database health check
db_check = DatabaseHealthCheck(db_session)
registry.register_check(db_check)

# Redis health check
redis_check = RedisHealthCheck(redis_client)
registry.register_check(redis_check)

# External API checks
google_check = ExternalAPIHealthCheck("google", "https://www.google.com")
microsoft_check = ExternalAPIHealthCheck("microsoft", "https://www.microsoft.com")
openai_check = ExternalAPIHealthCheck("openai", "https://api.openai.com")

registry.register_check(google_check)
registry.register_check(microsoft_check)
registry.register_check(openai_check)

# System resources check
system_check = SystemResourceHealthCheck()
registry.register_check(system_check)
```

### Monitoring Configuration
```python
# Initialize monitoring
from app.core.monitoring import (
    CorrelationIDMiddleware,
    performance_monitor,
    structured_logger
)

# Add correlation ID middleware
correlation_middleware = CorrelationIDMiddleware(app)

# Use performance monitoring decorators
@monitor_performance(endpoint="user_creation", method="POST")
def create_user(user_data):
    # Function implementation
    pass

@monitor_database_queries(operation="insert", table="users")
def insert_user(user_data):
    # Database operation
    pass

@monitor_redis_operations(operation="set")
def cache_user_data(user_id, data):
    # Redis operation
    pass
```

## 🚪 Graceful Shutdown

### Overview
The graceful shutdown system ensures proper cleanup of resources when the application is terminated.

### Features
- **Signal Handling**: SIGTERM and SIGINT handling
- **Priority-based Cleanup**: Ordered resource cleanup
- **Timeout Management**: Configurable timeouts for cleanup operations
- **Critical Hook Management**: Critical vs. non-critical cleanup operations

### Usage
```python
from app.core.graceful_shutdown import (
    register_shutdown_hook,
    register_common_shutdown_hooks,
    is_shutting_down,
    require_running
)

# Register custom shutdown hooks
def cleanup_custom_resources():
    logger.info("Cleaning up custom resources...")
    # Cleanup logic

register_shutdown_hook(
    name="custom_cleanup",
    callback=cleanup_custom_resources,
    priority=3,
    timeout=15.0,
    critical=False
)

# Register common shutdown hooks
register_common_shutdown_hooks(app, db, redis_client, celery_app)

# Use shutdown-aware decorators
@require_running
def critical_operation():
    # This function won't run during shutdown
    pass

# Use shutdown-aware context manager
from app.core.graceful_shutdown import shutdown_aware_operation

with shutdown_aware_operation():
    # Operations that should not run during shutdown
    pass
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements-monitoring.txt
```

### 2. Initialize Health Checks
```python
# In your Flask app initialization
from app.core.health_checks import HealthCheckRegistry
from app.core.monitoring import CorrelationIDMiddleware

# Create health check registry
registry = HealthCheckRegistry()
app.health_check_registry = registry

# Register health checks
# ... (see configuration section)

# Add correlation ID middleware
correlation_middleware = CorrelationIDMiddleware(app)
```

### 3. Register Health Check Routes
```python
from app.routes.health import health_bp

app.register_blueprint(health_bp, url_prefix='/api')
```

### 4. Initialize Graceful Shutdown
```python
from app.core.graceful_shutdown import register_common_shutdown_hooks

# Register shutdown hooks
register_common_shutdown_hooks(app, db, redis_client, celery_app)
```

## 📈 Monitoring Dashboard

### Health Check Dashboard
Access `/health` to view the comprehensive health dashboard showing:
- Overall system status
- Individual service health
- Performance metrics
- Recent health check results

### Prometheus Metrics
Access `/metrics` to view Prometheus-compatible metrics for:
- Infrastructure monitoring
- Application performance
- Business metrics

### Performance Dashboard
Access `/health/performance` (authenticated) to view:
- Request performance over time
- Database query performance
- Redis operation performance
- System resource usage

## 🔍 Troubleshooting

### Common Issues

#### 1. Health Checks Failing
- **Check Dependencies**: Ensure Redis and database are running
- **Verify Configuration**: Check connection strings and credentials
- **Review Logs**: Check application logs for detailed error messages

#### 2. Metrics Not Collecting
- **Verify Prometheus Client**: Ensure prometheus-client is installed
- **Check Endpoint**: Verify `/metrics` endpoint is accessible
- **Review Configuration**: Check monitoring configuration

#### 3. Graceful Shutdown Issues
- **Signal Handling**: Verify signal handlers are registered
- **Hook Priorities**: Check shutdown hook priorities
- **Timeout Issues**: Adjust timeout values for slow operations

### Debug Mode
Enable debug logging for detailed monitoring information:
```python
import logging
logging.getLogger('app.core.health_checks').setLevel(logging.DEBUG)
logging.getLogger('app.core.monitoring').setLevel(logging.DEBUG)
```

## 🧪 Testing

### Health Check Testing
```python
import pytest
from app.core.health_checks import HealthCheckRegistry

def test_health_check_registry():
    registry = HealthCheckRegistry()
    assert len(registry.checks) == 0
    
    # Add test checks
    # Run health checks
    # Verify results
```

### Performance Monitoring Testing
```python
def test_performance_monitoring():
    # Test performance monitoring decorators
    # Verify metrics collection
    # Check performance data
```

## 📚 API Reference

### Health Check Classes
- `HealthCheckRegistry`: Manages health checks
- `DatabaseHealthCheck`: Database connectivity monitoring
- `RedisHealthCheck`: Redis connectivity monitoring
- `ExternalAPIHealthCheck`: External API monitoring
- `SystemResourceHealthCheck`: System resource monitoring

### Monitoring Classes
- `CorrelationIDMiddleware`: Request correlation and logging
- `PerformanceMonitor`: Performance metrics collection
- `StructuredLogger`: Structured logging with context

### Shutdown Classes
- `GracefulShutdownHandler`: Application shutdown management
- `ShutdownHook`: Individual shutdown operations

## 🔒 Security Considerations

### Authentication
- Performance metrics endpoint requires JWT authentication
- Health check endpoints are public for monitoring purposes
- Consider rate limiting for public endpoints

### Data Privacy
- Health checks do not expose sensitive data
- Performance metrics are anonymized
- Correlation IDs are randomly generated

### Access Control
- Monitor access to health check endpoints
- Log all health check requests
- Consider IP whitelisting for production monitoring

## 📊 Production Deployment

### Kubernetes Integration
```yaml
# Liveness probe
livenessProbe:
  httpGet:
    path: /health/live
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10

# Readiness probe
readinessProbe:
  httpGet:
    path: /health/ready
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Load Balancer Configuration
```yaml
# Health check for load balancer
healthCheck:
  path: /health/simple
  port: 5000
  interval: 30s
  timeout: 5s
  healthyThreshold: 2
  unhealthyThreshold: 3
```

### Monitoring Stack
- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **AlertManager**: Alerting and notification
- **Jaeger/Zipkin**: Distributed tracing

## 🤝 Contributing

When contributing to the monitoring system:

1. **Follow Monitoring Standards**: Use established monitoring patterns
2. **Add Tests**: Include tests for new health checks and monitoring features
3. **Update Documentation**: Keep this README current
4. **Performance Impact**: Ensure monitoring has minimal performance impact
5. **Security Review**: Review security implications of new monitoring features

## 📄 License

This monitoring system is part of the main project and follows the same license terms.

---

**⚠️ Monitoring Notice**: This system provides comprehensive monitoring capabilities. Regularly review and update monitoring thresholds, add new health checks as services evolve, and ensure monitoring data is properly secured and retained according to your organization's policies.
