"""
Enhanced Celery Configuration with Retry Logic and Monitoring
Production-ready task queue configuration for the AI reporting platform
"""

from datetime import timedelta
import os
from kombu import Queue, Exchange

class CeleryConfig:
    """Enhanced Celery configuration for production environments"""
    
    # Broker settings
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Serialization
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    
    # Timezone
    timezone = 'UTC'
    enable_utc = True
    
    # Task routing and queues
    task_default_queue = 'default'
    task_queues = (
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('reports', Exchange('reports'), routing_key='reports'),
        Queue('ai', Exchange('ai'), routing_key='ai'),
        Queue('exports', Exchange('exports'), routing_key='exports'),
        Queue('emails', Exchange('emails'), routing_key='emails'),
        Queue('high_priority', Exchange('high_priority'), routing_key='high_priority'),
    )
    
    task_routes = {
        'app.tasks.report_tasks.generate_report_task': {'queue': 'reports'},
        'app.tasks.ai_tasks.*': {'queue': 'ai'},
        'app.tasks.export_tasks.*': {'queue': 'exports'},
        'app.tasks.email_tasks.*': {'queue': 'emails'},
        'app.tasks.urgent_tasks.*': {'queue': 'high_priority'},
    }
    
    # Retry configuration
    task_default_retry_delay = 60  # 1 minute
    task_max_retries = 3
    task_retry_jitter = True  # Add randomization to retry delays
    
    # Worker configuration
    worker_prefetch_multiplier = 1  # Prevent worker overload
    task_acks_late = True  # Acknowledge after task completion
    worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks
    worker_max_memory_per_child = 200000  # 200MB memory limit
    
    # Task execution
    task_time_limit = 30 * 60  # 30 minutes hard limit
    task_soft_time_limit = 25 * 60  # 25 minutes soft limit
    task_compression = 'gzip'
    
    # Result backend configuration
    result_expires = 3600  # Results expire after 1 hour
    result_persistent = True
    
    # Monitoring
    task_send_sent_event = True
    task_track_started = True
    
    # Security
    worker_hijack_root_logger = False
    worker_log_color = False
    
    # Beat scheduler configuration
    beat_schedule = {
        'cleanup-old-results': {
            'task': 'app.tasks.maintenance_tasks.cleanup_old_results',
            'schedule': timedelta(hours=1),
        },
        'health-check': {
            'task': 'app.tasks.maintenance_tasks.health_check',
            'schedule': timedelta(minutes=5),
        },
        'report-queue-metrics': {
            'task': 'app.tasks.monitoring_tasks.collect_queue_metrics',
            'schedule': timedelta(minutes=1),
        },
    }


# Retry decorators for different task types
def with_retry(max_retries=3, countdown=60, backoff=True):
    """
    Decorator for tasks with exponential backoff retry logic
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as exc:
                if self.request.retries < max_retries:
                    # Exponential backoff calculation
                    retry_countdown = countdown
                    if backoff:
                        retry_countdown = countdown * (2 ** self.request.retries)
                    
                    # Add jitter to prevent thundering herd
                    import random
                    jitter = random.uniform(0.1, 0.3) * retry_countdown
                    retry_countdown += jitter
                    
                    raise self.retry(
                        exc=exc,
                        countdown=retry_countdown,
                        max_retries=max_retries
                    )
                else:
                    # Log final failure
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(
                        f"Task {func.__name__} failed after {max_retries} retries: {exc}",
                        extra={'task_id': self.request.id, 'args': args, 'kwargs': kwargs}
                    )
                    raise exc
        
        return wrapper
    return decorator


# Circuit breaker pattern for external services
class CircuitBreaker:
    """Circuit breaker for external API calls"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func):
        from functools import wraps
        import time
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                return result
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
                
                raise e
        
        return wrapper


# Task progress tracking
class TaskProgressTracker:
    """Track and store task progress in Redis"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def update_progress(self, task_id, progress, message=None, metadata=None):
        """Update task progress"""
        progress_data = {
            'progress': progress,
            'message': message,
            'metadata': metadata or {},
            'updated_at': time.time()
        }
        
        self.redis.setex(
            f"task_progress:{task_id}",
            3600,  # Expire after 1 hour
            json.dumps(progress_data)
        )
    
    def get_progress(self, task_id):
        """Get task progress"""
        data = self.redis.get(f"task_progress:{task_id}")
        if data:
            return json.loads(data)
        return None
    
    def clear_progress(self, task_id):
        """Clear task progress"""
        self.redis.delete(f"task_progress:{task_id}")


# Task metrics collection
class TaskMetrics:
    """Collect and store task execution metrics"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def record_task_start(self, task_id, task_name, queue_name):
        """Record task start time"""
        metrics = {
            'task_id': task_id,
            'task_name': task_name,
            'queue_name': queue_name,
            'start_time': time.time(),
            'status': 'STARTED'
        }
        
        self.redis.setex(
            f"task_metrics:{task_id}",
            86400,  # 24 hours
            json.dumps(metrics)
        )
    
    def record_task_completion(self, task_id, success=True, error=None):
        """Record task completion"""
        metrics_data = self.redis.get(f"task_metrics:{task_id}")
        if metrics_data:
            metrics = json.loads(metrics_data)
            metrics.update({
                'end_time': time.time(),
                'duration': time.time() - metrics['start_time'],
                'status': 'SUCCESS' if success else 'FAILURE',
                'error': str(error) if error else None
            })
            
            self.redis.setex(
                f"task_metrics:{task_id}",
                86400,
                json.dumps(metrics)
            )
    
    def get_queue_metrics(self, queue_name, hours=24):
        """Get aggregated metrics for a queue"""
        # Implementation for queue metrics aggregation
        # This would typically involve scanning Redis keys and aggregating data
        pass


# Dead letter queue handler
def setup_dead_letter_queues(celery_app):
    """Set up dead letter queues for failed tasks"""
    
    @celery_app.task(bind=True)
    def handle_dead_letter(self, task_id, task_name, args, kwargs, exc_info):
        """Handle tasks that have exhausted all retries"""
        import logging
        logger = logging.getLogger(__name__)
        
        dead_letter_data = {
            'task_id': task_id,
            'task_name': task_name,
            'args': args,
            'kwargs': kwargs,
            'exc_info': exc_info,
            'failed_at': time.time()
        }
        
        # Store in dead letter queue
        self.redis.lpush('dead_letter_queue', json.dumps(dead_letter_data))
        
        # Log the failure
        logger.error(
            f"Task {task_name} ({task_id}) moved to dead letter queue",
            extra=dead_letter_data
        )
        
        # Optionally send alert to administrators
        # send_admin_alert(f"Task failure: {task_name}", dead_letter_data)


# Health check utilities
def get_celery_health_status(celery_app):
    """Get comprehensive health status of Celery workers and queues"""
    
    from celery import current_app
    
    health_data = {
        'timestamp': time.time(),
        'workers': {},
        'queues': {},
        'broker_status': 'unknown'
    }
    
    try:
        # Check worker status
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            for worker_name, worker_stats in stats.items():
                health_data['workers'][worker_name] = {
                    'status': 'active',
                    'processed_tasks': worker_stats.get('total', 0),
                    'active_tasks': len(inspect.active().get(worker_name, [])),
                    'load_avg': worker_stats.get('rusage', {}).get('utime', 0)
                }
        
        # Check queue lengths
        with current_app.connection() as conn:
            for queue_name in ['default', 'reports', 'ai', 'exports', 'emails']:
                try:
                    queue_length = conn.default_channel.queue_declare(
                        queue=queue_name, passive=True
                    ).method.message_count
                    health_data['queues'][queue_name] = {
                        'length': queue_length,
                        'status': 'healthy' if queue_length < 1000 else 'warning'
                    }
                except Exception as e:
                    health_data['queues'][queue_name] = {
                        'length': -1,
                        'status': 'error',
                        'error': str(e)
                    }
        
        health_data['broker_status'] = 'healthy'
        
    except Exception as e:
        health_data['broker_status'] = 'error'
        health_data['error'] = str(e)
    
    return health_data


if __name__ == "__main__":
    import json
    import time
    
    # Example usage and testing
    config = CeleryConfig()
    print("Celery configuration loaded successfully")
    print(f"Broker URL: {config.broker_url}")
    print(f"Task queues: {[q.name for q in config.task_queues]}")
