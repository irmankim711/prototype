#!/usr/bin/env python3
"""
Celery Worker Startup Script
Simple script to start the Celery worker for the automated report system
"""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables if not already set
os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('CELERY_BROKER_URL', 'redis://localhost:6379/0')
os.environ.setdefault('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

if __name__ == '__main__':
    from app.celery_enhanced import celery
    
    print("🚀 Starting Celery Worker...")
    print(f"📡 Broker URL: {celery.conf.broker_url}")
    print(f"💾 Result Backend: {celery.conf.result_backend}")
    print(f"📋 Task Queues: {[q.name for q in celery.conf.task_queues]}")
    print("=" * 50)
    
    # Start the worker
    celery.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--queues=default,reports,exports,ai,emails,high_priority',
        '--hostname=worker1@%h'
    ])
