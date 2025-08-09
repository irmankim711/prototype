"""
Celery Flower Configuration for Task Monitoring
Production-ready monitoring setup for the AI reporting platform
"""

import os
from celery import Celery
from flask import Flask
from flower import Flower
from flower.urls import urlpatterns
from flower.command import FlowerCommand


class EnhancedFlowerConfig:
    """Enhanced Flower configuration for production monitoring"""
    
    # Basic settings
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Authentication settings
    basic_auth = [f"{os.getenv('FLOWER_USER', 'admin')}:{os.getenv('FLOWER_PASSWORD', 'admin123')}"]
    
    # Security settings
    port = int(os.getenv('FLOWER_PORT', 5555))
    address = os.getenv('FLOWER_ADDRESS', '0.0.0.0')
    url_prefix = os.getenv('FLOWER_URL_PREFIX', '/flower')
    
    # Database settings for persistent data
    db = os.getenv('FLOWER_DB', 'flower.db')
    persistent = True
    
    # Task monitoring settings
    max_tasks = 10000
    auto_refresh = True
    
    # Dashboard customization
    natural_time = True
    enable_events = True
    
    @classmethod
    def get_flower_settings(cls):
        """Get Flower settings as dictionary"""
        return {
            'broker_url': cls.broker_url,
            'result_backend': cls.result_backend,
            'basic_auth': cls.basic_auth,
            'port': cls.port,
            'address': cls.address,
            'url_prefix': cls.url_prefix,
            'db': cls.db,
            'persistent': cls.persistent,
            'max_tasks': cls.max_tasks,
            'auto_refresh': cls.auto_refresh,
            'natural_time': cls.natural_time,
            'enable_events': cls.enable_events,
        }


def create_flower_app():
    """Create and configure Flower monitoring application"""
    
    # Create Celery app instance
    celery_app = Celery('app')
    celery_app.config_from_object('app.celery_enhanced:CeleryConfig')
    
    # Configure Flower
    flower_config = EnhancedFlowerConfig.get_flower_settings()
    
    class CustomFlowerCommand(FlowerCommand):
        """Custom Flower command with enhanced configuration"""
        
        def handle(self, *args, **options):
            # Apply custom configuration
            for key, value in flower_config.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            
            super().handle(*args, **options)
    
    return CustomFlowerCommand()


def setup_flower_monitoring():
    """Set up Flower monitoring with custom metrics"""
    
    from flower.views import BaseHandler
    import tornado.web
    import json
    import redis
    
    class CustomMetricsHandler(BaseHandler):
        """Custom metrics endpoint for enhanced monitoring"""
        
        def get(self):
            """Return custom metrics in JSON format"""
            try:
                redis_client = redis.from_url(
                    os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                )
                
                # Get latest metrics
                latest_metrics = redis_client.get('celery_metrics:latest')
                if latest_metrics:
                    metrics = json.loads(latest_metrics)
                else:
                    metrics = {'error': 'No metrics available'}
                
                # Get queue health status
                queue_health = {}
                for queue_name in ['default', 'reports', 'ai', 'exports', 'emails']:
                    try:
                        queue_length = redis_client.llen(f"celery.{queue_name}")
                        queue_health[queue_name] = {
                            'length': queue_length,
                            'status': 'healthy' if queue_length < 100 else 'warning'
                        }
                    except Exception:
                        queue_health[queue_name] = {'status': 'error'}
                
                metrics['queue_health'] = queue_health
                
                self.set_header('Content-Type', 'application/json')
                self.write(json.dumps(metrics, indent=2))
                
            except Exception as e:
                self.set_status(500)
                self.write({'error': str(e)})
    
    class TaskProgressHandler(BaseHandler):
        """Handler for task progress tracking"""
        
        def get(self, task_id):
            """Get progress for specific task"""
            try:
                redis_client = redis.from_url(
                    os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                )
                
                progress_data = redis_client.get(f"task_progress:{task_id}")
                if progress_data:
                    progress = json.loads(progress_data)
                    self.write(progress)
                else:
                    self.set_status(404)
                    self.write({'error': 'Task progress not found'})
                
            except Exception as e:
                self.set_status(500)
                self.write({'error': str(e)})
    
    class HealthCheckHandler(BaseHandler):
        """Health check endpoint for monitoring systems"""
        
        def get(self):
            """Return health status of the entire system"""
            try:
                from ..tasks.enhanced_tasks import health_check
                
                # Run health check task
                health_result = health_check.delay()
                health_data = health_result.get(timeout=30)
                
                self.set_header('Content-Type', 'application/json')
                self.write(json.dumps(health_data, indent=2))
                
            except Exception as e:
                self.set_status(500)
                self.write({'error': str(e)})
    
    # Add custom handlers to Flower URL patterns
    custom_handlers = [
        (r"/api/metrics", CustomMetricsHandler),
        (r"/api/tasks/([^/]+)/progress", TaskProgressHandler),
        (r"/api/health", HealthCheckHandler),
    ]
    
    return custom_handlers


def create_monitoring_dashboard():
    """Create enhanced monitoring dashboard HTML"""
    
    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Reporting Platform - Task Monitoring</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .dashboard {
                max-width: 1200px;
                margin: 0 auto;
            }
            .card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }
            .metric-card {
                text-align: center;
                padding: 15px;
                border-left: 4px solid #007bff;
            }
            .metric-value {
                font-size: 2rem;
                font-weight: bold;
                color: #007bff;
            }
            .metric-label {
                color: #666;
                margin-top: 5px;
            }
            .status-healthy { border-left-color: #28a745; }
            .status-warning { border-left-color: #ffc107; }
            .status-error { border-left-color: #dc3545; }
            .chart-container {
                position: relative;
                height: 300px;
                margin: 20px 0;
            }
            .refresh-btn {
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <div class="card">
                <h1>🚀 AI Reporting Platform - Task Monitoring</h1>
                <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Data</button>
                <span id="last-updated"></span>
            </div>
            
            <div class="card">
                <h2>📊 Queue Metrics</h2>
                <div class="metrics-grid" id="queue-metrics">
                    <!-- Queue metrics will be populated here -->
                </div>
            </div>
            
            <div class="card">
                <h2>👥 Worker Status</h2>
                <div id="worker-status">
                    <!-- Worker status will be populated here -->
                </div>
            </div>
            
            <div class="card">
                <h2>📈 Task Throughput</h2>
                <div class="chart-container">
                    <canvas id="throughput-chart"></canvas>
                </div>
            </div>
            
            <div class="card">
                <h2>🏥 System Health</h2>
                <div id="health-status">
                    <!-- Health status will be populated here -->
                </div>
            </div>
        </div>
        
        <script>
            let throughputChart;
            
            async function fetchMetrics() {
                try {
                    const response = await fetch('/api/metrics');
                    return await response.json();
                } catch (error) {
                    console.error('Failed to fetch metrics:', error);
                    return null;
                }
            }
            
            async function fetchHealth() {
                try {
                    const response = await fetch('/api/health');
                    return await response.json();
                } catch (error) {
                    console.error('Failed to fetch health:', error);
                    return null;
                }
            }
            
            function updateQueueMetrics(metrics) {
                const container = document.getElementById('queue-metrics');
                container.innerHTML = '';
                
                if (metrics && metrics.queue_health) {
                    Object.entries(metrics.queue_health).forEach(([queue, data]) => {
                        const statusClass = `status-${data.status}`;
                        container.innerHTML += `
                            <div class="metric-card ${statusClass}">
                                <div class="metric-value">${data.length || 0}</div>
                                <div class="metric-label">${queue} Queue</div>
                            </div>
                        `;
                    });
                }
            }
            
            function updateWorkerStatus(metrics) {
                const container = document.getElementById('worker-status');
                
                if (metrics && metrics.workers) {
                    let html = '<div class="metrics-grid">';
                    Object.entries(metrics.workers).forEach(([worker, data]) => {
                        html += `
                            <div class="metric-card status-healthy">
                                <div class="metric-value">${data.active || 0}</div>
                                <div class="metric-label">${worker}<br>Active Tasks</div>
                            </div>
                        `;
                    });
                    html += '</div>';
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<p>No worker data available</p>';
                }
            }
            
            function updateHealthStatus(health) {
                const container = document.getElementById('health-status');
                
                if (health) {
                    let html = '<div class="metrics-grid">';
                    
                    // Database status
                    const dbStatus = health.database === 'healthy' ? 'healthy' : 'error';
                    html += `
                        <div class="metric-card status-${dbStatus}">
                            <div class="metric-value">🗄️</div>
                            <div class="metric-label">Database<br>${health.database}</div>
                        </div>
                    `;
                    
                    // Redis status
                    const redisStatus = health.redis === 'healthy' ? 'healthy' : 'error';
                    html += `
                        <div class="metric-card status-${redisStatus}">
                            <div class="metric-value">🔴</div>
                            <div class="metric-label">Redis<br>${health.redis}</div>
                        </div>
                    `;
                    
                    // AI Service status
                    const aiStatus = health.ai_service === 'healthy' ? 'healthy' : 'error';
                    html += `
                        <div class="metric-card status-${aiStatus}">
                            <div class="metric-value">🤖</div>
                            <div class="metric-label">AI Service<br>${health.ai_service}</div>
                        </div>
                    `;
                    
                    html += '</div>';
                    container.innerHTML = html;
                } else {
                    container.innerHTML = '<p>Health check failed</p>';
                }
            }
            
            function initThroughputChart() {
                const ctx = document.getElementById('throughput-chart').getContext('2d');
                throughputChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Tasks Completed',
                            data: [],
                            borderColor: '#007bff',
                            backgroundColor: 'rgba(0, 123, 255, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
            
            async function refreshData() {
                const metrics = await fetchMetrics();
                const health = await fetchHealth();
                
                updateQueueMetrics(metrics);
                updateWorkerStatus(metrics);
                updateHealthStatus(health);
                
                document.getElementById('last-updated').textContent = 
                    `Last updated: ${new Date().toLocaleTimeString()}`;
            }
            
            // Initialize dashboard
            initThroughputChart();
            refreshData();
            
            // Auto-refresh every 30 seconds
            setInterval(refreshData, 30000);
        </script>
    </body>
    </html>
    """
    
    return dashboard_html


if __name__ == "__main__":
    # Start Flower with enhanced configuration
    flower_app = create_flower_app()
    flower_app.execute_from_commandline([
        'flower',
        '--basic_auth=admin:admin123',
        '--port=5555',
        '--url_prefix=/flower'
    ])
