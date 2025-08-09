# Enhanced Celery Task Management System
# Production-ready background task processing with monitoring

# Install enhanced dependencies
pip install flower==2.0.1
pip install redis-py-cluster==2.1.3
pip install prometheus-client==0.19.0
pip install sentry-sdk==1.38.0

# Flower monitoring service
celery -A app.celery flower --port=5555 --basic_auth=admin:admin123

# Enhanced worker with monitoring
celery -A app.celery worker --loglevel=info --concurrency=4 --queues=default,reports,ai,exports,emails --hostname=worker1@%h

# Beat scheduler with enhanced tasks
celery -A app.celery beat --loglevel=info --schedule=/tmp/celerybeat-schedule

# Multi-queue worker configuration
celery multi start worker1 worker2 worker3 \
  -A app.celery \
  --pidfile=/var/run/celery/%n.pid \
  --logfile=/var/log/celery/%n.log \
  --loglevel=INFO \
  -Q:worker1 high_priority,default \
  -Q:worker2 reports,ai \
  -Q:worker3 exports,emails

# Production monitoring commands
celery -A app.celery inspect active
celery -A app.celery inspect registered
celery -A app.celery inspect stats
celery -A app.celery control shutdown

# Queue length monitoring
celery -A app.celery inspect active_queues
celery -A app.celery control add_consumer default -d worker1@hostname

# Performance monitoring
celery -A app.celery events
celery -A app.celery monitor

# Emergency commands
celery -A app.celery purge  # Clear all tasks
celery -A app.celery control cancel_consumer default -d worker1@hostname
celery -A app.celery control pool_restart -d worker1@hostname
