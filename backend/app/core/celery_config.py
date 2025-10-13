"""
Enhanced Celery Configuration for Performance Optimization
Provides centralized configuration for task prioritization, worker optimization, and resource management
"""

import os
from datetime import timedelta
from kombu import Queue, Exchange


class CeleryConfig:
    """Enhanced Celery configuration class with performance optimizations"""
    
    # Broker and Backend Configuration
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Task Serialization and Compression
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    task_compression = 'gzip'
    result_compression = 'gzip'
    
    # Timezone Configuration
    timezone = 'UTC'
    enable_utc = True
    
    # Task Execution Configuration
    task_track_started = True
    task_send_sent_event = True
    task_acks_late = True  # Acknowledge tasks only after completion
    task_reject_on_worker_lost = True  # Reject tasks if worker is lost
    task_time_limit = int(os.getenv('CELERY_TASK_TIME_LIMIT', '1800'))  # 30 minutes hard limit
    task_soft_time_limit = int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '1500'))  # 25 minutes soft limit
    
    # Enhanced Worker Configuration
    worker_prefetch_multiplier = int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', '1'))
    worker_max_tasks_per_child = int(os.getenv('CELERY_WORKER_MAX_TASKS_PER_CHILD', '500'))
    worker_concurrency = int(os.getenv('CELERY_WORKER_CONCURRENCY', '4'))
    worker_pool = os.getenv('CELERY_WORKER_POOL', 'prefork')
    worker_pool_restarts = True
    worker_disable_rate_limits = False
    worker_max_memory_per_child = int(os.getenv('CELERY_WORKER_MAX_MEMORY_PER_CHILD', '200000'))  # 200MB
    
    # Task Retry Configuration with Exponential Backoff
    task_default_retry_delay = int(os.getenv('CELERY_TASK_RETRY_DELAY', '60'))
    task_default_max_retries = int(os.getenv('CELERY_TASK_MAX_RETRIES', '3'))
    task_retry_backoff = True
    task_retry_backoff_max = int(os.getenv('CELERY_TASK_RETRY_BACKOFF_MAX', '600'))  # Max 10 minutes
    task_retry_jitter = True
    
    # Result Backend Configuration
    result_expires = int(os.getenv('CELERY_RESULT_EXPIRES', '3600'))  # 1 hour
    result_persistent = True
    result_cache_max = int(os.getenv('CELERY_RESULT_CACHE_MAX', '10000'))
    
    # Monitoring and Events
    send_events = True
    send_task_events = True
    worker_send_task_events = True
    
    # Connection Pool Configuration
    broker_pool_limit = int(os.getenv('CELERY_BROKER_POOL_LIMIT', '10'))
    broker_connection_retry = True
    broker_connection_retry_on_startup = True
    broker_connection_max_retries = int(os.getenv('CELERY_BROKER_CONNECTION_MAX_RETRIES', '3'))
    
    # Queue and Routing Configuration
    task_default_queue = 'normal_priority'
    task_create_missing_queues = True
    task_default_exchange = 'tasks'
    task_default_exchange_type = 'direct'
    task_default_routing_key = 'task'
    
    # Define Exchanges
    task_exchanges = (
        Exchange('critical_priority', type='direct'),
        Exchange('high_priority', type='direct'),
        Exchange('normal_priority', type='direct'),
        Exchange('low_priority', type='direct'),
    )
    
    # Define Queues with Priority Support
    task_queues = (
        Queue('critical_priority', 
              Exchange('critical_priority'), 
              routing_key='critical_priority',
              queue_arguments={'x-max-priority': 10}),
        Queue('high_priority', 
              Exchange('high_priority'), 
              routing_key='high_priority',
              queue_arguments={'x-max-priority': 7}),
        Queue('normal_priority', 
              Exchange('normal_priority'), 
              routing_key='normal_priority',
              queue_arguments={'x-max-priority': 5}),
        Queue('low_priority', 
              Exchange('low_priority'), 
              routing_key='low_priority',
              queue_arguments={'x-max-priority': 1}),
    )
    
    # Enhanced Task Routes for Priority Queues
    task_routes = {
        # Critical priority tasks (immediate user-facing operations)
        'app.tasks.generate_report_task': {'queue': 'critical_priority', 'priority': 10},
        'app.tasks.generate_automated_report_task': {'queue': 'critical_priority', 'priority': 10},
        'app.tasks.process_excel_file_task': {'queue': 'critical_priority', 'priority': 9},
        'app.tasks.generate_pdf_task': {'queue': 'critical_priority', 'priority': 9},
        'app.tasks.report_tasks.generate_report_task': {'queue': 'critical_priority', 'priority': 10},
        'app.tasks.report_tasks.generate_form_report': {'queue': 'critical_priority', 'priority': 9},
        
        # High priority tasks (user-facing operations)
        'app.tasks.send_notification_task': {'queue': 'high_priority', 'priority': 7},
        'app.tasks.sync_data_task': {'queue': 'high_priority', 'priority': 6},
        'app.tasks.report_tasks.trigger_auto_report_generation': {'queue': 'high_priority', 'priority': 7},
        
        # Normal priority tasks (background processing)
        'app.tasks.backup_data_task': {'queue': 'normal_priority', 'priority': 5},
        'app.tasks.report_tasks.send_report_notification': {'queue': 'normal_priority', 'priority': 4},
        'app.tasks.report_tasks.generate_scheduled_reports': {'queue': 'normal_priority', 'priority': 5},
        
        # Low priority tasks (maintenance and cleanup)
        'app.tasks.cleanup_tasks.*': {'queue': 'low_priority', 'priority': 1},
        'app.tasks.schedule_automated_reports': {'queue': 'low_priority', 'priority': 2},
        'app.tasks.archive_old_reports': {'queue': 'low_priority', 'priority': 1},
        'app.tasks.report_tasks.cleanup_old_reports': {'queue': 'low_priority', 'priority': 1},
    }
    
    # Batch Processing Configuration
    task_batch_size = int(os.getenv('CELERY_TASK_BATCH_SIZE', '10'))
    task_batch_timeout = int(os.getenv('CELERY_TASK_BATCH_TIMEOUT', '300'))  # 5 minutes
    
    # Beat Schedule Configuration (for periodic tasks)
    beat_schedule = {
        'cleanup-old-reports': {
            'task': 'app.tasks.report_tasks.cleanup_old_reports',
            'schedule': timedelta(hours=24),  # Run daily
            'options': {'queue': 'low_priority', 'priority': 1}
        },
        'generate-scheduled-reports': {
            'task': 'app.tasks.report_tasks.generate_scheduled_reports',
            'schedule': timedelta(hours=1),  # Run hourly
            'options': {'queue': 'normal_priority', 'priority': 5}
        },
    }
    
    # Security Configuration
    task_always_eager = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'false').lower() == 'true'
    task_eager_propagates = True
    
    # Redis-specific optimizations
    broker_transport_options = {
        'priority_steps': list(range(11)),  # Support priorities 0-10
        'sep': ':',
        'queue_order_strategy': 'priority',
        'visibility_timeout': 3600,  # 1 hour
        'fanout_prefix': True,
        'fanout_patterns': True
    }
    
    # Result backend transport options
    result_backend_transport_options = {
        'retry_policy': {
            'timeout': 5.0
        }
    }


def get_celery_config():
    """Get Celery configuration instance"""
    return CeleryConfig()


def configure_celery_app(celery_app, flask_app=None):
    """
    Configure Celery app with enhanced settings
    
    Args:
        celery_app: Celery application instance
        flask_app: Flask application instance (optional)
    """
    config = get_celery_config()
    celery_app.config_from_object(config)
    
    if flask_app:
        # Update task base to work with Flask app context
        class ContextTask(celery_app.Task):
            """Make celery tasks work with Flask app context."""
            def __call__(self, *args, **kwargs):
                with flask_app.app_context():
                    return self.run(*args, **kwargs)
        
        celery_app.Task = ContextTask
    
    return celery_app


def get_worker_startup_commands():
    """
    Get recommended worker startup commands for different queue priorities
    
    Returns:
        dict: Dictionary of worker commands for different priorities
    """
    return {
        'critical_worker': 'celery -A backend.app.celery worker -Q critical_priority -c 2 --loglevel=info --prefetch-multiplier=1',
        'high_worker': 'celery -A backend.app.celery worker -Q high_priority -c 3 --loglevel=info --prefetch-multiplier=1',
        'normal_worker': 'celery -A backend.app.celery worker -Q normal_priority -c 4 --loglevel=info --prefetch-multiplier=2',
        'low_worker': 'celery -A backend.app.celery worker -Q low_priority -c 2 --loglevel=info --prefetch-multiplier=3',
        'all_queues': 'celery -A backend.app.celery worker -Q critical_priority,high_priority,normal_priority,low_priority -c 4 --loglevel=info'
    }


def get_monitoring_commands():
    """
    Get monitoring commands for Celery
    
    Returns:
        dict: Dictionary of monitoring commands
    """
    return {
        'flower': 'celery -A backend.app.celery flower --port=5555',
        'monitor': 'celery -A backend.app.celery monitor',
        'events': 'celery -A backend.app.celery events',
        'inspect_active': 'celery -A backend.app.celery inspect active',
        'inspect_stats': 'celery -A backend.app.celery inspect stats',
        'inspect_reserved': 'celery -A backend.app.celery inspect reserved'
    }


# Environment-specific configurations
class DevelopmentCeleryConfig(CeleryConfig):
    """Development-specific Celery configuration"""
    task_always_eager = os.getenv('CELERY_TASK_ALWAYS_EAGER', 'false').lower() == 'true'
    worker_concurrency = 2  # Lower concurrency for development
    task_time_limit = 300  # 5 minutes for development
    task_soft_time_limit = 240  # 4 minutes for development


class ProductionCeleryConfig(CeleryConfig):
    """Production-specific Celery configuration"""
    worker_concurrency = int(os.getenv('CELERY_WORKER_CONCURRENCY', '8'))  # Higher for production
    broker_pool_limit = int(os.getenv('CELERY_BROKER_POOL_LIMIT', '20'))
    result_cache_max = int(os.getenv('CELERY_RESULT_CACHE_MAX', '50000'))
    
    # Production-specific Redis optimizations
    broker_transport_options = {
        **CeleryConfig.broker_transport_options,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPIDLE': 1,
            'TCP_KEEPINTVL': 3,
            'TCP_KEEPCNT': 5,
        }
    }


def get_environment_config(environment='development'):
    """
    Get environment-specific Celery configuration
    
    Args:
        environment: Environment name (development, production, testing)
        
    Returns:
        Celery configuration class
    """
    if environment == 'production':
        return ProductionCeleryConfig()
    elif environment == 'development':
        return DevelopmentCeleryConfig()
    else:
        return CeleryConfig()