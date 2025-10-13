#!/bin/bash

# 📊 Production Monitoring Setup Script
# Configures comprehensive monitoring for the form automation platform

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_ROOT/monitoring"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

main() {
    log "📊 Setting up production monitoring..."
    
    create_monitoring_structure
    setup_prometheus_config
    setup_grafana_dashboards
    setup_alertmanager
    configure_sentry_monitoring
    setup_health_checks
    create_monitoring_docker_compose
    
    success "🎯 Monitoring setup completed!"
    display_monitoring_summary
}

create_monitoring_structure() {
    log "📁 Creating monitoring directory structure..."
    
    mkdir -p "$MONITORING_DIR"/{prometheus,grafana/dashboards,grafana/provisioning/{dashboards,datasources},alertmanager,health-checks}
    
    success "Directory structure created"
}

setup_prometheus_config() {
    log "🔍 Setting up Prometheus configuration..."
    
    cat > "$MONITORING_DIR/prometheus/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Flask application metrics
  - job_name: 'flask-app'
    static_configs:
      - targets: ['api:5000']
    metrics_path: /metrics
    scrape_interval: 10s
    scrape_timeout: 5s

  # PostgreSQL metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis_exporter:9121']

  # Nginx metrics
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx_exporter:9113']

  # Node/System metrics
  - job_name: 'node'
    static_configs:
      - targets: ['node_exporter:9100']

  # Celery metrics
  - job_name: 'celery'
    static_configs:
      - targets: ['celery_exporter:9540']

  # Docker metrics
  - job_name: 'docker'
    static_configs:
      - targets: ['cadvisor:8080']
EOF

    # Create alerting rules
    cat > "$MONITORING_DIR/prometheus/alert_rules.yml" << 'EOF'
groups:
- name: form_automation_alerts
  rules:
  # High response time
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m])) > 2
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }}s"

  # High error rate
  - alert: HighErrorRate
    expr: rate(flask_http_request_exceptions_total[5m]) > 0.1
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors/second"

  # Database connection issues
  - alert: DatabaseDown
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database is down"
      description: "PostgreSQL database is not responding"

  # Redis connection issues
  - alert: RedisDown
    expr: up{job="redis"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Redis is down"
      description: "Redis cache is not responding"

  # High CPU usage
  - alert: HighCPUUsage
    expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage"
      description: "CPU usage is {{ $value }}%"

  # High memory usage
  - alert: HighMemoryUsage
    expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is {{ $value }}%"

  # Disk space running low
  - alert: DiskSpaceLow
    expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 90
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Disk space running low"
      description: "Disk usage is {{ $value }}%"

  # Celery queue backup
  - alert: CeleryQueueBackup
    expr: celery_tasks_pending > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Celery queue backup"
      description: "{{ $value }} tasks pending in Celery queue"
EOF

    success "Prometheus configuration created"
}

setup_grafana_dashboards() {
    log "📊 Setting up Grafana dashboards..."
    
    # Datasource provisioning
    cat > "$MONITORING_DIR/grafana/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Dashboard provisioning
    cat > "$MONITORING_DIR/grafana/provisioning/dashboards/dashboard.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'form-automation'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    # Main application dashboard
    cat > "$MONITORING_DIR/grafana/dashboards/application_dashboard.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Form Automation Platform",
    "tags": ["form-automation"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(flask_http_request_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(flask_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Seconds"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(flask_http_request_exceptions_total[5m])",
            "legendFormat": "Errors/sec"
          }
        ],
        "yAxes": [
          {
            "label": "Errors/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 8
        }
      },
      {
        "id": 4,
        "title": "Active Users",
        "type": "stat",
        "targets": [
          {
            "expr": "flask_sessions_active",
            "legendFormat": "Active Sessions"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 8
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF

    success "Grafana dashboards configured"
}

setup_alertmanager() {
    log "🚨 Setting up Alertmanager..."
    
    cat > "$MONITORING_DIR/alertmanager/alertmanager.yml" << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@yourdomain.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@yourdomain.com'
    subject: '[ALERT] {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK_URL'
    channel: '#alerts'
    title: 'Alert: {{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
EOF

    success "Alertmanager configured"
}

configure_sentry_monitoring() {
    log "🔍 Configuring Sentry monitoring..."
    
    cat > "$MONITORING_DIR/sentry_config.py" << 'EOF'
"""
Sentry Configuration for Production Monitoring
"""

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import os

def configure_sentry(app):
    """Configure Sentry for error tracking and performance monitoring"""
    
    sentry_dsn = os.getenv('SENTRY_DSN')
    if not sentry_dsn:
        app.logger.warning("Sentry DSN not configured")
        return
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FlaskIntegration(transaction_style='endpoint'),
            CeleryIntegration(),
            RedisIntegration(),
            SqlalchemyIntegration(),
        ],
        
        # Performance monitoring
        traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        profiles_sample_rate=float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
        
        # Environment configuration
        environment=os.getenv('FLASK_ENV', 'production'),
        release=os.getenv('APP_VERSION', 'unknown'),
        
        # Error filtering
        before_send=filter_errors,
        
        # Additional configuration
        attach_stacktrace=True,
        send_default_pii=False,
        max_breadcrumbs=50,
    )
    
    app.logger.info("Sentry monitoring configured")

def filter_errors(event, hint):
    """Filter out certain errors from being sent to Sentry"""
    
    # Don't send certain HTTP errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, (ConnectionError, TimeoutError)):
            return None
    
    # Filter out health check requests
    if event.get('request', {}).get('url', '').endswith('/health'):
        return None
    
    return event
EOF

    success "Sentry monitoring configured"
}

setup_health_checks() {
    log "🏥 Setting up health checks..."
    
    cat > "$MONITORING_DIR/health-checks/comprehensive_health_check.py" << 'EOF'
#!/usr/bin/env python3
"""
Comprehensive Health Check Script
Monitors all aspects of the form automation platform
"""

import requests
import psycopg2
import redis
import json
import time
import sys
from datetime import datetime
import os

class HealthChecker:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.checks = []
        
    def check_api_health(self):
        """Check API health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return {
                "name": "API Health",
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "details": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "name": "API Health",
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_database(self):
        """Check database connectivity"""
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'prototype'),
                user=os.getenv('DB_USER', 'prototype_user'),
                password=os.getenv('DB_PASSWORD', 'password')
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            return {
                "name": "Database",
                "status": "healthy"
            }
        except Exception as e:
            return {
                "name": "Database",
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_redis(self):
        """Check Redis connectivity"""
        try:
            r = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            r.ping()
            
            return {
                "name": "Redis",
                "status": "healthy",
                "info": r.info()
            }
        except Exception as e:
            return {
                "name": "Redis",
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_celery_workers(self):
        """Check Celery worker status"""
        try:
            response = requests.get(f"{self.base_url}/api/admin/celery/status", timeout=10)
            return {
                "name": "Celery Workers",
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            return {
                "name": "Celery Workers",
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_disk_space(self):
        """Check disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            usage_percent = (used / total) * 100
            
            return {
                "name": "Disk Space",
                "status": "healthy" if usage_percent < 90 else "unhealthy",
                "usage_percent": usage_percent,
                "free_gb": free // (1024**3)
            }
        except Exception as e:
            return {
                "name": "Disk Space",
                "status": "unhealthy",
                "error": str(e)
            }
    
    def run_all_checks(self):
        """Run all health checks"""
        checks = [
            self.check_api_health,
            self.check_database,
            self.check_redis,
            self.check_celery_workers,
            self.check_disk_space
        ]
        
        results = []
        for check in checks:
            result = check()
            results.append(result)
            print(f"✅ {result['name']}: {result['status']}")
        
        return results
    
    def generate_report(self):
        """Generate comprehensive health report"""
        results = self.run_all_checks()
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy" if all(r["status"] == "healthy" for r in results) else "unhealthy",
            "checks": results
        }
        
        return report

if __name__ == "__main__":
    checker = HealthChecker()
    report = checker.generate_report()
    
    print(json.dumps(report, indent=2))
    
    # Exit with error code if any check failed
    if report["overall_status"] == "unhealthy":
        sys.exit(1)
EOF

    chmod +x "$MONITORING_DIR/health-checks/comprehensive_health_check.py"
    
    success "Health checks configured"
}

create_monitoring_docker_compose() {
    log "🐳 Creating monitoring Docker Compose..."
    
    cat > "$MONITORING_DIR/docker-compose.monitoring.yml" << 'EOF'
version: '3.8'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    networks:
      - monitoring

  # Alertmanager
  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    networks:
      - monitoring

  # Node Exporter
  node_exporter:
    image: prom/node-exporter:latest
    container_name: node_exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring

  # PostgreSQL Exporter
  postgres_exporter:
    image: prometheuscommunity/postgres-exporter:latest
    container_name: postgres_exporter
    ports:
      - "9187:9187"
    environment:
      DATA_SOURCE_NAME: "postgresql://prototype_user:password@postgres:5432/prototype?sslmode=disable"
    networks:
      - monitoring

  # Redis Exporter
  redis_exporter:
    image: oliver006/redis_exporter:latest
    container_name: redis_exporter
    ports:
      - "9121:9121"
    environment:
      REDIS_ADDR: "redis://redis:6379"
    networks:
      - monitoring

  # cAdvisor for container metrics
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
EOF

    success "Monitoring Docker Compose created"
}

display_monitoring_summary() {
    cat << 'EOF'

📊 MONITORING SETUP COMPLETE
=============================

✅ Components Configured:
   - Prometheus (metrics collection)
   - Grafana (visualization)
   - Alertmanager (alerting)
   - Health checks (comprehensive monitoring)
   - Sentry integration (error tracking)

🚀 To Start Monitoring:
   cd monitoring
   docker-compose -f docker-compose.monitoring.yml up -d

📊 Access Points:
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090
   - Alertmanager: http://localhost:9093

🔧 Configuration Files:
   - monitoring/prometheus/prometheus.yml
   - monitoring/grafana/dashboards/
   - monitoring/alertmanager/alertmanager.yml

📈 Key Metrics Monitored:
   - Request rate and response time
   - Error rates and exceptions
   - Database and Redis performance
   - System resources (CPU, memory, disk)
   - Celery queue status
   - User sessions and activity

🚨 Alerts Configured:
   - High response time (>2s)
   - High error rate (>10%)
   - Service downtime
   - Resource exhaustion
   - Queue backups

🔧 Next Steps:
   1. Update Slack webhook URL in alertmanager.yml
   2. Configure email SMTP settings
   3. Set up Sentry DSN in production
   4. Customize dashboard thresholds
   5. Add business-specific metrics

EOF
}

# Execute main function
main "$@"
