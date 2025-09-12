"""
Health Check API Routes
Provides comprehensive system health monitoring
"""

from flask import Blueprint, jsonify, current_app
from datetime import datetime
import logging
import os
from typing import Dict, Any

from ..models import db, User, Form, FormSubmission, Report
from ..tasks.enhanced_report_tasks import health_check_task

logger = logging.getLogger(__name__)

# Create blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api/health')

@health_bp.route('/', methods=['GET'])
def health_check():
    """
    Comprehensive health check endpoint
    GET /api/health
    """
    try:
        health_status = {
            'service': 'automated_report_platform',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'checks': {}
        }
        
        overall_status = 'healthy'
        
        # Database health check
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            
            # Check table counts
            user_count = User.query.count()
            form_count = Form.query.count()
            submission_count = FormSubmission.query.count()
            report_count = Report.query.count()
            
            health_status['checks']['database'] = {
                'status': 'healthy',
                'connection': 'connected',
                'tables': {
                    'users': user_count,
                    'forms': form_count,
                    'submissions': submission_count,
                    'reports': report_count
                }
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'connection': 'disconnected',
                'error': str(e)
            }
            overall_status = 'degraded'
        
        # Redis health check
        try:
            from .. import celery
            if celery.control.inspect().active():
                health_status['checks']['redis'] = {
                    'status': 'healthy',
                    'connection': 'connected',
                    'workers': 'active'
                }
            else:
                health_status['checks']['redis'] = {
                    'status': 'unhealthy',
                    'connection': 'connected',
                    'workers': 'inactive'
                }
                overall_status = 'degraded'
        except Exception as e:
            health_status['checks']['redis'] = {
                'status': 'unhealthy',
                'connection': 'disconnected',
                'error': str(e)
            }
            overall_status = 'degraded'
        
        # File system health check
        try:
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            if os.path.exists(upload_dir) and os.access(upload_dir, os.W_OK):
                health_status['checks']['filesystem'] = {
                    'status': 'healthy',
                    'upload_directory': 'accessible',
                    'permissions': 'read_write'
                }
            else:
                health_status['checks']['filesystem'] = {
                    'status': 'unhealthy',
                    'upload_directory': 'inaccessible',
                    'permissions': 'no_access'
                }
                overall_status = 'degraded'
        except Exception as e:
            health_status['checks']['filesystem'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'degraded'
        
        # Celery worker health check
        try:
            from .. import celery
            active_workers = celery.control.inspect().active()
            registered_workers = celery.control.inspect().registered()
            
            if active_workers and registered_workers:
                worker_count = len(active_workers)
                health_status['checks']['celery'] = {
                    'status': 'healthy',
                    'workers': 'active',
                    'worker_count': worker_count,
                    'queues': list(active_workers.keys()) if active_workers else []
                }
            else:
                health_status['checks']['celery'] = {
                    'status': 'unhealthy',
                    'workers': 'inactive',
                    'worker_count': 0
                }
                overall_status = 'degraded'
        except Exception as e:
            health_status['checks']['celery'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'degraded'
        
        # Environment check
        try:
            env_vars = {
                'FLASK_ENV': os.getenv('FLASK_ENV', 'not_set'),
                'DATABASE_URL': 'set' if os.getenv('DATABASE_URL') else 'not_set',
                'REDIS_URL': 'set' if os.getenv('REDIS_URL') else 'not_set',
                'SECRET_KEY': 'set' if os.getenv('SECRET_KEY') else 'not_set'
            }
            
            missing_vars = [k for k, v in env_vars.items() if v == 'not_set']
            
            if missing_vars:
                health_status['checks']['environment'] = {
                    'status': 'degraded',
                    'missing_variables': missing_vars,
                    'variables': env_vars
                }
                if overall_status == 'healthy':
                    overall_status = 'degraded'
            else:
                health_status['checks']['environment'] = {
                    'status': 'healthy',
                    'variables': env_vars
                }
        except Exception as e:
            health_status['checks']['environment'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            overall_status = 'degraded'
        
        # Update overall status
        health_status['status'] = overall_status
        
        # Add performance metrics
        try:
            import psutil
            health_status['system'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except ImportError:
            health_status['system'] = {
                'note': 'psutil not available for system metrics'
            }
        
        # Determine HTTP status code
        if overall_status == 'healthy':
            status_code = 200
        elif overall_status == 'degraded':
            status_code = 200  # Still operational
        else:
            status_code = 503  # Service unavailable
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'service': 'automated_report_platform',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/database', methods=['GET'])
def database_health():
    """
    Database-specific health check
    GET /api/health/database
    """
    try:
        health_status = {
            'service': 'database',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        # Test connection
        try:
            db.session.execute('SELECT 1')
            health_status['checks']['connection'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['checks']['connection'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Check table accessibility
        try:
            user_count = User.query.count()
            health_status['checks']['users_table'] = {
                'status': 'healthy',
                'record_count': user_count
            }
        except Exception as e:
            health_status['checks']['users_table'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        try:
            form_count = Form.query.count()
            health_status['checks']['forms_table'] = {
                'status': 'healthy',
                'record_count': form_count
            }
        except Exception as e:
            health_status['checks']['forms_table'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        try:
            submission_count = FormSubmission.query.count()
            health_status['checks']['submissions_table'] = {
                'status': 'healthy',
                'record_count': submission_count
            }
        except Exception as e:
            health_status['checks']['submissions_table'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        try:
            report_count = Report.query.count()
            health_status['checks']['reports_table'] = {
                'status': 'healthy',
                'record_count': report_count
            }
        except Exception as e:
            health_status['checks']['reports_table'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Check database configuration
        try:
            db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'not_set')
            if db_url != 'not_set':
                health_status['checks']['configuration'] = {
                    'status': 'healthy',
                    'database_url': 'configured'
                }
            else:
                health_status['checks']['configuration'] = {
                    'status': 'unhealthy',
                    'database_url': 'not_configured'
                }
                health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['checks']['configuration'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return jsonify({
            'service': 'database',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/workers', methods=['GET'])
def workers_health():
    """
    Celery workers health check
    GET /api/health/workers
    """
    try:
        health_status = {
            'service': 'celery_workers',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        try:
            from .. import celery
            
            # Check active workers
            active_workers = celery.control.inspect().active()
            if active_workers:
                health_status['checks']['active_workers'] = {
                    'status': 'healthy',
                    'count': len(active_workers),
                    'workers': list(active_workers.keys())
                }
            else:
                health_status['checks']['active_workers'] = {
                    'status': 'unhealthy',
                    'count': 0,
                    'message': 'No active workers found'
                }
                health_status['status'] = 'unhealthy'
            
            # Check registered workers
            registered_workers = celery.control.inspect().registered()
            if registered_workers:
                health_status['checks']['registered_workers'] = {
                    'status': 'healthy',
                    'count': len(registered_workers),
                    'workers': list(registered_workers.keys())
                }
            else:
                health_status['checks']['registered_workers'] = {
                    'status': 'unhealthy',
                    'count': 0,
                    'message': 'No registered workers found'
                }
                health_status['status'] = 'unhealthy'
            
            # Check worker stats
            try:
                stats = celery.control.inspect().stats()
                if stats:
                    health_status['checks']['worker_stats'] = {
                        'status': 'healthy',
                        'stats_available': True,
                        'worker_count': len(stats)
                    }
                else:
                    health_status['checks']['worker_stats'] = {
                        'status': 'unhealthy',
                        'stats_available': False
                    }
                    health_status['status'] = 'unhealthy'
            except Exception as e:
                health_status['checks']['worker_stats'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['status'] = 'unhealthy'
            
        except Exception as e:
            health_status['checks']['celery_connection'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        # Check Redis connection
        try:
            redis_url = current_app.config.get('CELERY_BROKER_URL', 'not_set')
            if redis_url != 'not_set':
                health_status['checks']['redis_config'] = {
                    'status': 'healthy',
                    'redis_url': 'configured'
                }
            else:
                health_status['checks']['redis_config'] = {
                    'status': 'unhealthy',
                    'redis_url': 'not_configured'
                }
                health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['checks']['redis_config'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'unhealthy'
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Workers health check failed: {str(e)}")
        return jsonify({
            'service': 'celery_workers',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with background task
    GET /api/health/detailed
    """
    try:
        # Start background health check task
        task_result = health_check_task.delay()
        
        return jsonify({
            'success': True,
            'message': 'Detailed health check started',
            'task_id': task_result.id,
            'status': 'processing',
            'check_url': f"/api/health/task/{task_result.id}"
        }), 202
        
    except Exception as e:
        logger.error(f"Failed to start detailed health check: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start health check: {str(e)}'
        }), 500

@health_bp.route('/task/<task_id>', methods=['GET'])
def get_health_task_status(task_id):
    """
    Get health check task status
    GET /api/health/task/{task_id}
    """
    try:
        from .. import celery
        
        # Get task result
        task_result = celery.AsyncResult(task_id)
        
        if task_result.ready():
            if task_result.successful():
                result = task_result.result
                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'status': 'completed',
                    'result': result
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(task_result.result)
                }), 500
        else:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'status': 'processing',
                'state': task_result.state
            }), 200
        
    except Exception as e:
        logger.error(f"Error getting health task status {task_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get task status: {str(e)}'
        }), 500
