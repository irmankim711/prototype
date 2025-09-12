"""
Health Check Routes

This module provides health check endpoints:
- /health - Detailed system status
- /health/simple - Simple health status
- /metrics - Prometheus metrics
- /health/ready - Readiness probe
- /health/live - Liveness probe
"""

import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..core.health_checks import HealthCheckRegistry, HealthStatus
from ..core.monitoring import performance_monitor, get_metrics, structured_logger

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Get health check registry from app context
        registry = getattr(current_app, 'health_check_registry', None)
        
        if not registry:
            return jsonify({
                'status': 'unknown',
                'message': 'Health check registry not available',
                'timestamp': datetime.utcnow().isoformat(),
                'checks': []
            }), 503
        
        # Run all health checks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(registry.run_all_checks())
        finally:
            loop.close()
        
        # Get overall status
        overall_status = registry.get_overall_status(results)
        summary = registry.get_summary(results)
        
        # Prepare response
        response_data = {
            'status': overall_status.value,
            'message': f"System status: {overall_status.value}",
            'timestamp': datetime.utcnow().isoformat(),
            'summary': summary,
            'checks': [result.to_dict() for result in results],
            'correlation_id': getattr(request, 'correlation_id', None),
        }
        
        # Log health check results
        structured_logger.info("Health check completed", 
                             overall_status=overall_status.value,
                             total_checks=summary['total_checks'],
                             healthy_checks=summary['healthy_checks'],
                             degraded_checks=summary['degraded_checks'],
                             unhealthy_checks=summary['unhealthy_checks'])
        
        # Return appropriate HTTP status code
        if overall_status == HealthStatus.HEALTHY:
            status_code = 200
        elif overall_status == HealthStatus.DEGRADED:
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
        return jsonify({
            'status': 'error',
            'message': 'Health check failed',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'correlation_id': getattr(request, 'correlation_id', None),
        }), 500

@health_bp.route('/health/simple', methods=['GET'])
def simple_health_check():
    """Simple health check endpoint for load balancers."""
    try:
        # Get health check registry from app context
        registry = getattr(current_app, 'health_check_registry', None)
        
        if not registry:
            return jsonify({
                'status': 'unknown',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Run basic checks only (database, redis)
        basic_checks = [check for check in registry.checks 
                       if check.name in ['database', 'redis']]
        
        if not basic_checks:
            return jsonify({
                'status': 'unknown',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Run basic checks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(asyncio.gather(*[check.check() for check in basic_checks]))
        finally:
            loop.close()
        
        # Determine overall status
        overall_status = registry.get_overall_status(results)
        
        response_data = {
            'status': overall_status.value,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Return appropriate HTTP status code
        if overall_status == HealthStatus.HEALTHY:
            status_code = 200
        elif overall_status == HealthStatus.DEGRADED:
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/ready', methods=['GET'])
def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    try:
        # Check if application is ready to receive traffic
        # This includes database connectivity, Redis, and other critical services
        
        registry = getattr(current_app, 'health_check_registry', None)
        
        if not registry:
            return jsonify({
                'status': 'not_ready',
                'message': 'Health check registry not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Run critical health checks
        critical_checks = [check for check in registry.checks 
                          if check.name in ['database', 'redis']]
        
        if not critical_checks:
            return jsonify({
                'status': 'not_ready',
                'message': 'Critical health checks not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Run critical checks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(asyncio.gather(*[check.check() for check in critical_checks]))
        finally:
            loop.close()
        
        # Check if all critical services are healthy
        all_healthy = all(result.status == HealthStatus.HEALTHY for result in results)
        
        if all_healthy:
            return jsonify({
                'status': 'ready',
                'message': 'Application is ready to receive traffic',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'not_ready',
                'message': 'Critical services are not healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'unhealthy_services': [result.name for result in results if result.status != HealthStatus.HEALTHY]
            }), 503
        
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}")
        
        return jsonify({
            'status': 'not_ready',
            'message': 'Readiness check failed',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@health_bp.route('/health/live', methods=['GET'])
def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    try:
        # Simple check to see if the application is alive
        # This should be very lightweight and fast
        
        return jsonify({
            'status': 'alive',
            'message': 'Application is alive',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}")
        
        return jsonify({
            'status': 'dead',
            'message': 'Application is not responding',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    try:
        # Return Prometheus metrics
        return get_metrics()
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        
        return jsonify({
            'error': 'Metrics collection failed',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/performance', methods=['GET'])
@jwt_required()
def performance_metrics():
    """Performance metrics endpoint (requires authentication)."""
    try:
        # Get performance summary
        hours = request.args.get('hours', 24, type=int)
        summary = performance_monitor.get_performance_summary(hours)
        
        return jsonify({
            'status': 'success',
            'data': summary,
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': getattr(request, 'correlation_id', None),
        }), 200
        
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve performance metrics',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/check/<check_name>', methods=['GET'])
def specific_health_check(check_name: str):
    """Run a specific health check by name."""
    try:
        registry = getattr(current_app, 'health_check_registry', None)
        
        if not registry:
            return jsonify({
                'status': 'error',
                'message': 'Health check registry not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Find the specific check
        check = next((c for c in registry.checks if c.name == check_name), None)
        
        if not check:
            return jsonify({
                'status': 'error',
                'message': f'Health check "{check_name}" not found',
                'timestamp': datetime.utcnow().isoformat()
            }), 404
        
        # Run the specific check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(check.check())
        finally:
            loop.close()
        
        return jsonify({
            'status': 'success',
            'data': result.to_dict(),
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': getattr(request, 'correlation_id', None),
        }), 200
        
    except Exception as e:
        logger.error(f"Specific health check failed: {e}")
        
        return jsonify({
            'status': 'error',
            'message': f'Health check "{check_name}" failed',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/refresh', methods=['POST'])
@jwt_required()
def refresh_health_checks():
    """Force refresh of health check cache."""
    try:
        registry = getattr(current_app, 'health_check_registry', None)
        
        if not registry:
            return jsonify({
                'status': 'error',
                'message': 'Health check registry not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Force refresh
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(registry.run_all_checks(force_refresh=True))
        finally:
            loop.close()
        
        # Get overall status
        overall_status = registry.get_overall_status(results)
        summary = registry.get_summary(results)
        
        return jsonify({
            'status': 'success',
            'message': 'Health checks refreshed successfully',
            'data': {
                'overall_status': overall_status.value,
                'summary': summary,
                'checks': [result.to_dict() for result in results]
            },
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': getattr(request, 'correlation_id', None),
        }), 200
        
    except Exception as e:
        logger.error(f"Health check refresh failed: {e}")
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to refresh health checks',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/health/status', methods=['GET'])
def health_status():
    """Get current health status without running checks."""
    try:
        registry = getattr(current_app, 'health_check_registry', None)
        
        if not registry:
            return jsonify({
                'status': 'unknown',
                'message': 'Health check registry not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 503
        
        # Return cached results if available
        if registry.cached_results and registry.last_check_time:
            overall_status = registry.get_overall_status(registry.cached_results)
            summary = registry.get_summary(registry.cached_results)
            
            return jsonify({
                'status': 'success',
                'data': {
                    'overall_status': overall_status.value,
                    'summary': summary,
                    'last_check': registry.last_check_time.isoformat(),
                    'cache_age_seconds': (datetime.utcnow() - registry.last_check_time).total_seconds()
                },
                'timestamp': datetime.utcnow().isoformat(),
                'correlation_id': getattr(request, 'correlation_id', None),
            }), 200
        else:
            return jsonify({
                'status': 'no_data',
                'message': 'No health check data available',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
    except Exception as e:
        logger.error(f"Health status check failed: {e}")
        
        return jsonify({
            'status': 'error',
            'message': 'Failed to get health status',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
