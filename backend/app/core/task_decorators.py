"""
Enhanced Task Decorators for Celery Performance Optimization
Provides decorators for retry strategies, priority handling, and resource management
"""

import functools
import time
import random
from typing import Callable, Any, Optional, Dict, List
from celery import shared_task
from celery.exceptions import Retry
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def enhanced_task(
    priority: int = 5,
    queue: str = 'normal_priority',
    max_retries: int = 3,
    retry_delay: int = 60,
    retry_backoff: bool = True,
    retry_jitter: bool = True,
    time_limit: int = 1800,
    soft_time_limit: int = 1500,
    **celery_kwargs
):
    """
    Enhanced task decorator with optimized retry strategies and resource management
    
    Args:
        priority: Task priority (1-10, higher is more important)
        queue: Queue name for task routing
        max_retries: Maximum number of retry attempts
        retry_delay: Initial retry delay in seconds
        retry_backoff: Enable exponential backoff
        retry_jitter: Add randomness to retry delays
        time_limit: Hard time limit in seconds
        soft_time_limit: Soft time limit in seconds
        **celery_kwargs: Additional Celery task arguments
    """
    def decorator(func: Callable) -> Callable:
        @shared_task(
            bind=True,
            max_retries=max_retries,
            default_retry_delay=retry_delay,
            time_limit=time_limit,
            soft_time_limit=soft_time_limit,
            **celery_kwargs
        )
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                # Log task start
                logger.info(f"Starting task {func.__name__} with priority {priority} on queue {queue}")
                
                # Execute the actual task
                result = func(*args, **kwargs)
                
                # Log successful completion
                logger.info(f"Task {func.__name__} completed successfully")
                return result
                
            except Exception as exc:
                # Calculate retry delay with exponential backoff and jitter
                retry_count = self.request.retries
                
                if retry_count < max_retries:
                    if retry_backoff:
                        # Exponential backoff: delay * (2 ^ retry_count)
                        delay = retry_delay * (2 ** retry_count)
                    else:
                        delay = retry_delay
                    
                    if retry_jitter:
                        # Add jitter: ±25% randomness
                        jitter = delay * 0.25
                        delay = delay + random.uniform(-jitter, jitter)
                    
                    # Cap the delay at a maximum value
                    delay = min(delay, 600)  # Max 10 minutes
                    
                    logger.warning(
                        f"Task {func.__name__} failed (attempt {retry_count + 1}/{max_retries}). "
                        f"Retrying in {delay:.1f} seconds. Error: {exc}"
                    )
                    
                    # Retry with calculated delay
                    raise self.retry(exc=exc, countdown=delay)
                else:
                    logger.error(
                        f"Task {func.__name__} failed permanently after {max_retries} attempts. "
                        f"Final error: {exc}"
                    )
                    raise exc
        
        # Set task routing information
        wrapper.apply_async = functools.partial(
            wrapper.apply_async,
            queue=queue,
            priority=priority
        )
        
        return wrapper
    return decorator


def critical_task(**kwargs):
    """Decorator for critical priority tasks"""
    defaults = {
        'priority': 10,
        'queue': 'critical_priority',
        'max_retries': 5,
        'retry_delay': 30,
        'time_limit': 3600,  # 1 hour for critical tasks
        'soft_time_limit': 3300,
    }
    # Merge defaults with provided kwargs, giving precedence to kwargs
    merged_kwargs = {**defaults, **kwargs}
    return enhanced_task(**merged_kwargs)


def high_priority_task(**kwargs):
    """Decorator for high priority tasks"""
    defaults = {
        'priority': 7,
        'queue': 'high_priority',
        'max_retries': 4,
        'retry_delay': 45,
    }
    # Merge defaults with provided kwargs, giving precedence to kwargs
    merged_kwargs = {**defaults, **kwargs}
    return enhanced_task(**merged_kwargs)


def normal_task(**kwargs):
    """Decorator for normal priority tasks"""
    defaults = {
        'priority': 5,
        'queue': 'normal_priority',
    }
    # Merge defaults with provided kwargs, giving precedence to kwargs
    merged_kwargs = {**defaults, **kwargs}
    return enhanced_task(**merged_kwargs)


def low_priority_task(**kwargs):
    """Decorator for low priority tasks"""
    return enhanced_task(
        priority=2,
        queue='low_priority',
        max_retries=2,
        retry_delay=120,
        time_limit=3600,  # Allow longer time for low priority tasks
        soft_time_limit=3300,
        **kwargs
    )


def batch_task(
    batch_size: int = 10,
    batch_timeout: int = 300,
    **task_kwargs
):
    """
    Decorator for batch processing tasks
    
    Args:
        batch_size: Number of items to process in each batch
        batch_timeout: Timeout for batch processing in seconds
        **task_kwargs: Additional task decorator arguments
    """
    def decorator(func: Callable) -> Callable:
        @enhanced_task(**task_kwargs)
        @functools.wraps(func)
        def wrapper(items: List[Any], *args, **kwargs):
            """Process items in batches"""
            results = []
            total_items = len(items)
            
            logger.info(f"Processing {total_items} items in batches of {batch_size}")
            
            for i in range(0, total_items, batch_size):
                batch = items[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_items + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
                
                try:
                    # Process batch with timeout
                    start_time = time.time()
                    batch_result = func(batch, *args, **kwargs)
                    processing_time = time.time() - start_time
                    
                    results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
                    
                    logger.info(f"Batch {batch_num} completed in {processing_time:.2f}s")
                    
                    # Check if we're approaching timeout
                    if processing_time > batch_timeout:
                        logger.warning(f"Batch processing time ({processing_time:.2f}s) exceeded timeout ({batch_timeout}s)")
                        
                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    # Continue with next batch instead of failing entire task
                    results.append({'error': str(e), 'batch': batch_num})
            
            return {
                'total_items': total_items,
                'total_batches': total_batches,
                'results': results,
                'success_count': len([r for r in results if not isinstance(r, dict) or 'error' not in r])
            }
        
        return wrapper
    return decorator


def memory_optimized_task(
    max_memory_mb: int = 200,
    **task_kwargs
):
    """
    Decorator for memory-optimized tasks
    
    Args:
        max_memory_mb: Maximum memory usage in MB before warning
        **task_kwargs: Additional task decorator arguments
    """
    def decorator(func: Callable) -> Callable:
        @enhanced_task(**task_kwargs)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            logger.info(f"Task {func.__name__} starting with {initial_memory:.1f}MB memory usage")
            
            try:
                result = func(*args, **kwargs)
                
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory
                
                logger.info(
                    f"Task {func.__name__} completed. "
                    f"Memory: {final_memory:.1f}MB (+{memory_increase:.1f}MB)"
                )
                
                if final_memory > max_memory_mb:
                    logger.warning(
                        f"Task {func.__name__} exceeded memory limit: "
                        f"{final_memory:.1f}MB > {max_memory_mb}MB"
                    )
                
                return result
                
            except Exception as e:
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                logger.error(
                    f"Task {func.__name__} failed with {final_memory:.1f}MB memory usage. Error: {e}"
                )
                raise
        
        return wrapper
    return decorator


def progress_tracking_task(
    progress_key_prefix: str = 'task_progress',
    **task_kwargs
):
    """
    Decorator for tasks with progress tracking
    
    Args:
        progress_key_prefix: Redis key prefix for progress tracking
        **task_kwargs: Additional task decorator arguments
    """
    def decorator(func: Callable) -> Callable:
        @enhanced_task(**task_kwargs)
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            from ..core.cache import get_redis_client
            
            task_id = self.request.id
            progress_key = f"{progress_key_prefix}:{task_id}"
            redis_client = get_redis_client()
            
            def update_progress(current: int, total: int, message: str = ""):
                """Update task progress"""
                progress_data = {
                    'current': current,
                    'total': total,
                    'percentage': (current / total * 100) if total > 0 else 0,
                    'message': message,
                    'timestamp': time.time()
                }
                
                redis_client.setex(
                    progress_key,
                    3600,  # Expire after 1 hour
                    str(progress_data)
                )
                
                # Update Celery task state
                self.update_state(
                    state='PROGRESS',
                    meta=progress_data
                )
            
            # Add progress callback to kwargs
            kwargs['update_progress'] = update_progress
            
            try:
                # Initialize progress
                update_progress(0, 100, "Task started")
                
                result = func(*args, **kwargs)
                
                # Mark as completed
                update_progress(100, 100, "Task completed")
                
                return result
                
            except Exception as e:
                # Mark as failed
                update_progress(-1, 100, f"Task failed: {str(e)}")
                raise
            finally:
                # Clean up progress key after some time
                redis_client.expire(progress_key, 300)  # Keep for 5 minutes after completion
        
        return wrapper
    return decorator


def rate_limited_task(
    rate_limit: str = "10/m",  # 10 per minute
    **task_kwargs
):
    """
    Decorator for rate-limited tasks
    
    Args:
        rate_limit: Rate limit string (e.g., "10/m", "100/h")
        **task_kwargs: Additional task decorator arguments
    """
    def decorator(func: Callable) -> Callable:
        @enhanced_task(rate_limit=rate_limit, **task_kwargs)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Utility functions for task management

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get comprehensive task status including progress
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Dictionary with task status information
    """
    from celery.result import AsyncResult
    from ..core.cache import get_redis_client
    
    result = AsyncResult(task_id)
    redis_client = get_redis_client()
    
    status = {
        'task_id': task_id,
        'state': result.state,
        'result': result.result,
        'traceback': result.traceback,
        'progress': None
    }
    
    # Try to get progress information
    progress_key = f"task_progress:{task_id}"
    progress_data = redis_client.get(progress_key)
    if progress_data:
        try:
            status['progress'] = eval(progress_data.decode())
        except:
            pass
    
    return status


def cancel_task(task_id: str) -> bool:
    """
    Cancel a running task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        True if task was cancelled successfully
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    result.revoke(terminate=True)
    
    logger.info(f"Task {task_id} cancelled")
    return True


def get_queue_stats() -> Dict[str, Any]:
    """
    Get statistics for all queues
    
    Returns:
        Dictionary with queue statistics
    """
    from celery import current_app
    
    inspect = current_app.control.inspect()
    
    return {
        'active': inspect.active(),
        'reserved': inspect.reserved(),
        'stats': inspect.stats(),
        'registered': inspect.registered()
    }