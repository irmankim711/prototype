"""
Task Progress and Monitoring API Endpoints
Real-time task tracking and monitoring for the AI reporting platform
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import redis
import json
from datetime import datetime
from typing import Dict, Any, Optional

from ..models import User, db
from ..celery_enhanced import get_redis_client
from ..tasks.enhanced_tasks import get_progress_tracker, get_task_metrics

# Create blueprint
task_monitoring_bp = Blueprint('task_monitoring', __name__, url_prefix='/api/tasks')


@task_monitoring_bp.route('/progress/<task_id>', methods=['GET'])
@jwt_required()
def get_task_progress(task_id: str):
    """
    Get progress information for a specific task
    """
    try:
        progress_tracker = get_progress_tracker()
        progress_data = progress_tracker.get_progress(task_id)
        
        if not progress_data:
            return jsonify({
                'error': 'Task progress not found',
                'task_id': task_id
            }), 404
        
        # Add task metadata if available
        metrics = get_task_metrics()
        task_metrics = metrics.redis.get(f"task_metrics:{task_id}")
        
        if task_metrics:
            task_info = json.loads(task_metrics)
            progress_data.update({
                'task_name': task_info.get('task_name'),
                'queue_name': task_info.get('queue_name'),
                'start_time': task_info.get('start_time'),
                'duration': task_info.get('duration'),
                'status': task_info.get('status')
            })
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'progress': progress_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting task progress: {e}")
        return jsonify({
            'error': 'Failed to get task progress',
            'details': str(e)
        }), 500


@task_monitoring_bp.route('/status/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id: str):
    """
    Get comprehensive status information for a task
    """
    try:
        from celery.result import AsyncResult
        
        # Get Celery task result
        task_result = AsyncResult(task_id)
        
        status_data = {
            'task_id': task_id,
            'state': task_result.state,
            'successful': task_result.successful(),
            'failed': task_result.failed(),
            'ready': task_result.ready(),
            'result': None,
            'traceback': None,
            'info': None
        }
        
        # Add result information based on state
        if task_result.ready():
            if task_result.successful():
                status_data['result'] = task_result.result
            elif task_result.failed():
                status_data['traceback'] = task_result.traceback
                status_data['result'] = str(task_result.info)
        else:
            status_data['info'] = task_result.info
        
        # Add progress information
        progress_tracker = get_progress_tracker()
        progress_data = progress_tracker.get_progress(task_id)
        
        if progress_data:
            status_data['progress'] = progress_data
        
        return jsonify({
            'success': True,
            'status': status_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting task status: {e}")
        return jsonify({
            'error': 'Failed to get task status',
            'details': str(e)
        }), 500


@task_monitoring_bp.route('/cancel/<task_id>', methods=['POST'])
@jwt_required()
def cancel_task(task_id: str):
    """
    Cancel a running task
    """
    try:
        from celery import current_app as celery_app
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Revoke the task
        celery_app.control.revoke(task_id, terminate=True)
        
        # Update progress to cancelled
        progress_tracker = get_progress_tracker()
        progress_tracker.update_progress(
            task_id, 
            -2, 
            f"Task cancelled by user {user.email}",
            {'cancelled_by': user_id, 'cancelled_at': datetime.utcnow().isoformat()}
        )
        
        current_app.logger.info(f"Task {task_id} cancelled by user {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Task cancelled successfully',
            'task_id': task_id
        })
        
    except Exception as e:
        current_app.logger.error(f"Error cancelling task: {e}")
        return jsonify({
            'error': 'Failed to cancel task',
            'details': str(e)
        }), 500


@task_monitoring_bp.route('/list', methods=['GET'])
@jwt_required()
def list_user_tasks():
    """
    List tasks for the current user
    """
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status', None)
        
        # Get user's tasks from Redis metrics
        redis_client = get_redis_client()
        task_keys = list(redis_client.scan_iter(match="task_metrics:*"))
        
        user_tasks = []
        
        for key in task_keys:
            try:
                task_data = redis_client.get(key)
                if task_data:
                    task_info = json.loads(task_data)
                    
                    # Check if task belongs to user (you might need to store user_id in task metadata)
                    # For now, we'll return all tasks (in production, filter by user)
                    
                    if status_filter and task_info.get('status') != status_filter.upper():
                        continue
                    
                    # Get progress data
                    task_id = key.split(':')[1]
                    progress_data = redis_client.get(f"task_progress:{task_id}")
                    
                    if progress_data:
                        progress_info = json.loads(progress_data)
                        task_info['progress'] = progress_info['progress']
                        task_info['message'] = progress_info['message']
                    
                    user_tasks.append(task_info)
                    
            except Exception:
                continue
        
        # Sort by start time (newest first)
        user_tasks.sort(key=lambda x: x.get('start_time', 0), reverse=True)
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_tasks = user_tasks[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'tasks': paginated_tasks,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': len(user_tasks),
                'pages': (len(user_tasks) + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing user tasks: {e}")
        return jsonify({
            'error': 'Failed to list tasks',
            'details': str(e)
        }), 500


@task_monitoring_bp.route('/queues/status', methods=['GET'])
@jwt_required()
def get_queue_status():
    """
    Get status of all task queues
    """
    try:
        from celery import current_app as celery_app
        
        queue_status = {}
        
        # Get queue lengths
        with celery_app.connection() as conn:
            for queue_name in ['default', 'reports', 'ai', 'exports', 'emails', 'high_priority']:
                try:
                    queue_length = conn.default_channel.queue_declare(
                        queue=queue_name, passive=True
                    ).method.message_count
                    
                    queue_status[queue_name] = {
                        'length': queue_length,
                        'status': 'healthy' if queue_length < 100 else 'warning' if queue_length < 500 else 'critical'
                    }
                except Exception as e:
                    queue_status[queue_name] = {
                        'length': -1,
                        'status': 'error',
                        'error': str(e)
                    }
        
        return jsonify({
            'success': True,
            'queues': queue_status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting queue status: {e}")
        return jsonify({
            'error': 'Failed to get queue status',
            'details': str(e)
        }), 500


@task_monitoring_bp.route('/workers/status', methods=['GET'])
@jwt_required()
def get_workers_status():
    """
    Get status of all Celery workers
    """
    try:
        from celery import current_app as celery_app
        
        inspect = celery_app.control.inspect()
        
        workers_data = {
            'active': inspect.active() or {},
            'registered': inspect.registered() or {},
            'stats': inspect.stats() or {},
            'reserved': inspect.reserved() or {}
        }
        
        # Process worker information
        workers_status = {}
        
        for worker_name in workers_data['stats'].keys():
            worker_stats = workers_data['stats'][worker_name]
            active_tasks = workers_data['active'].get(worker_name, [])
            
            workers_status[worker_name] = {
                'status': 'online',
                'total_processed': worker_stats.get('total', 0),
                'active_tasks': len(active_tasks),
                'registered_tasks': len(workers_data['registered'].get(worker_name, [])),
                'load_avg': worker_stats.get('rusage', {}).get('utime', 0),
                'memory_usage': worker_stats.get('rusage', {}).get('maxrss', 0),
                'active_task_details': [
                    {
                        'id': task['id'],
                        'name': task['name'],
                        'started': task.get('time_start'),
                        'args': task.get('args', []),
                        'kwargs': task.get('kwargs', {})
                    }
                    for task in active_tasks
                ]
            }
        
        return jsonify({
            'success': True,
            'workers': workers_status,
            'total_workers': len(workers_status),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting workers status: {e}")
        return jsonify({
            'error': 'Failed to get workers status',
            'details': str(e)
        }), 500


@task_monitoring_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_system_metrics():
    """
    Get comprehensive system metrics
    """
    try:
        redis_client = get_redis_client()
        
        # Get latest metrics
        latest_metrics = redis_client.get('celery_metrics:latest')
        if latest_metrics:
            metrics = json.loads(latest_metrics)
        else:
            metrics = {'error': 'No metrics available'}
        
        # Get historical metrics
        historical_data = redis_client.lrange('celery_metrics:history', 0, 24)  # Last 24 data points
        historical_metrics = []
        
        for data in historical_data:
            try:
                historical_metrics.append(json.loads(data))
            except:
                continue
        
        # Calculate trend data
        trend_data = {
            'task_completion_rate': [],
            'queue_lengths': [],
            'worker_utilization': []
        }
        
        for metric in historical_metrics[-12:]:  # Last 12 data points
            # Calculate completion rate trend (simplified)
            total_processed = sum(
                worker.get('processed', 0) 
                for worker in metric.get('workers', {}).values()
            )
            trend_data['task_completion_rate'].append(total_processed)
            
            # Queue lengths trend
            total_queue_length = sum(metric.get('queues', {}).values())
            trend_data['queue_lengths'].append(total_queue_length)
            
            # Worker utilization (active tasks / total workers)
            total_active = sum(
                worker.get('active', 0) 
                for worker in metric.get('workers', {}).values()
            )
            total_workers = len(metric.get('workers', {}))
            utilization = (total_active / total_workers * 100) if total_workers > 0 else 0
            trend_data['worker_utilization'].append(utilization)
        
        return jsonify({
            'success': True,
            'current_metrics': metrics,
            'historical_metrics': historical_metrics,
            'trends': trend_data,
            'summary': {
                'total_workers': len(metrics.get('workers', {})),
                'total_queues': len(metrics.get('queues', {})),
                'total_active_tasks': sum(
                    worker.get('active', 0) 
                    for worker in metrics.get('workers', {}).values()
                ),
                'total_queue_length': sum(metrics.get('queues', {}).values()),
                'system_health': 'healthy' if sum(metrics.get('queues', {}).values()) < 1000 else 'warning'
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting system metrics: {e}")
        return jsonify({
            'error': 'Failed to get system metrics',
            'details': str(e)
        }), 500


@task_monitoring_bp.route('/health', methods=['GET'])
def system_health_check():
    """
    Public health check endpoint for monitoring systems
    """
    try:
        from ..tasks.enhanced_tasks import health_check
        
        # Run health check
        health_result = health_check.delay()
        health_data = health_result.get(timeout=30)
        
        # Determine overall health status
        overall_status = 'healthy'
        
        if health_data.get('database') != 'healthy':
            overall_status = 'unhealthy'
        elif health_data.get('redis') != 'healthy':
            overall_status = 'degraded'
        elif health_data.get('ai_service') != 'healthy':
            overall_status = 'degraded'
        
        # Add system uptime and version info
        health_data.update({
            'overall_status': overall_status,
            'version': current_app.config.get('APP_VERSION', '1.0.0'),
            'environment': current_app.config.get('ENV', 'development'),
            'uptime': 'N/A'  # Could implement actual uptime tracking
        })
        
        status_code = 200 if overall_status == 'healthy' else 503
        
        return jsonify(health_data), status_code
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'overall_status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503


@task_monitoring_bp.route('/restart-worker', methods=['POST'])
@jwt_required()
def restart_worker():
    """
    Restart a specific worker (admin only)
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Check if user is admin (implement your admin check logic)
        if not user or not getattr(user, 'is_admin', False):
            return jsonify({'error': 'Admin access required'}), 403
        
        worker_name = request.json.get('worker_name')
        if not worker_name:
            return jsonify({'error': 'Worker name is required'}), 400
        
        from celery import current_app as celery_app
        
        # Restart worker
        celery_app.control.pool_restart([worker_name])
        
        current_app.logger.info(f"Worker {worker_name} restarted by admin {user.email}")
        
        return jsonify({
            'success': True,
            'message': f'Worker {worker_name} restart initiated',
            'worker_name': worker_name
        })
        
    except Exception as e:
        current_app.logger.error(f"Error restarting worker: {e}")
        return jsonify({
            'error': 'Failed to restart worker',
            'details': str(e)
        }), 500


# WebSocket support for real-time updates (optional)
@task_monitoring_bp.route('/subscribe/<task_id>', methods=['GET'])
@jwt_required()
def subscribe_to_task_updates(task_id: str):
    """
    Subscribe to real-time task updates via Server-Sent Events
    """
    import time
    
    def generate_updates():
        """Generate real-time task updates"""
        progress_tracker = get_progress_tracker()
        last_progress = None
        
        while True:
            try:
                current_progress = progress_tracker.get_progress(task_id)
                
                if current_progress and current_progress != last_progress:
                    yield f"data: {json.dumps(current_progress)}\n\n"
                    last_progress = current_progress
                    
                    # Stop if task is completed or failed
                    if current_progress.get('progress', 0) in [100, -1, -2]:
                        break
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return current_app.response_class(
        generate_updates(),
        mimetype='text/plain',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )


# Error handlers
@task_monitoring_bp.errorhandler(404)
def task_not_found(error):
    return jsonify({
        'error': 'Task not found',
        'message': 'The requested task does not exist or has expired'
    }), 404


@task_monitoring_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred while processing your request'
    }), 500
