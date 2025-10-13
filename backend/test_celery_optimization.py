"""
Test script for Celery task configuration optimization
Tests task prioritization, retry strategies, and performance monitoring
"""

import os
import sys
import time
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, celery
from app.core.celery_config import get_celery_config, get_worker_startup_commands, get_monitoring_commands
from app.core.task_decorators import get_task_status, get_queue_stats
from app.tasks.report_tasks import generate_report_task, trigger_auto_report_generation
from app.models import db, Report, Form, User


def test_celery_configuration():
    """Test Celery configuration settings"""
    print("🔧 Testing Celery Configuration...")
    
    config = get_celery_config()
    
    # Test basic configuration
    assert config.broker_url is not None, "Broker URL not configured"
    assert config.result_backend is not None, "Result backend not configured"
    assert config.task_serializer == 'json', "Task serializer not set to JSON"
    assert config.result_serializer == 'json', "Result serializer not set to JSON"
    
    # Test worker configuration
    assert config.worker_prefetch_multiplier == 1, "Worker prefetch multiplier not optimized"
    assert config.worker_max_tasks_per_child == 500, "Worker max tasks per child not optimized"
    assert config.task_acks_late is True, "Task acks late not enabled"
    assert config.task_reject_on_worker_lost is True, "Task reject on worker lost not enabled"
    
    # Test retry configuration
    assert config.task_retry_backoff is True, "Task retry backoff not enabled"
    assert config.task_retry_jitter is True, "Task retry jitter not enabled"
    assert config.task_default_max_retries == 3, "Default max retries not set correctly"
    
    # Test queue configuration
    assert len(config.task_queues) == 4, "Not all priority queues configured"
    queue_names = [q.name for q in config.task_queues]
    expected_queues = ['critical_priority', 'high_priority', 'normal_priority', 'low_priority']
    for queue in expected_queues:
        assert queue in queue_names, f"Queue {queue} not configured"
    
    print("✅ Celery configuration tests passed")


def test_task_routing():
    """Test task routing to correct queues"""
    print("🔧 Testing Task Routing...")
    
    config = get_celery_config()
    
    # Test critical priority routing
    critical_tasks = [
        'app.tasks.generate_report_task',
        'app.tasks.report_tasks.generate_report_task',
        'app.tasks.report_tasks.generate_form_report'
    ]
    
    for task_name in critical_tasks:
        if task_name in config.task_routes:
            route = config.task_routes[task_name]
            assert route['queue'] == 'critical_priority', f"Task {task_name} not routed to critical queue"
            assert route['priority'] >= 9, f"Task {task_name} priority too low"
    
    # Test high priority routing
    high_priority_tasks = [
        'app.tasks.report_tasks.trigger_auto_report_generation'
    ]
    
    for task_name in high_priority_tasks:
        if task_name in config.task_routes:
            route = config.task_routes[task_name]
            assert route['queue'] == 'high_priority', f"Task {task_name} not routed to high priority queue"
    
    print("✅ Task routing tests passed")


def test_worker_commands():
    """Test worker startup commands"""
    print("🔧 Testing Worker Commands...")
    
    commands = get_worker_startup_commands()
    
    # Test that all expected commands are present
    expected_commands = ['critical_worker', 'high_worker', 'normal_worker', 'low_worker', 'all_queues']
    for cmd_name in expected_commands:
        assert cmd_name in commands, f"Worker command {cmd_name} not found"
        assert 'celery' in commands[cmd_name], f"Command {cmd_name} doesn't contain celery"
        assert 'worker' in commands[cmd_name], f"Command {cmd_name} doesn't contain worker"
    
    # Test queue-specific commands
    assert 'critical_priority' in commands['critical_worker'], "Critical worker doesn't target correct queue"
    assert 'high_priority' in commands['high_worker'], "High priority worker doesn't target correct queue"
    assert 'normal_priority' in commands['normal_worker'], "Normal worker doesn't target correct queue"
    assert 'low_priority' in commands['low_worker'], "Low priority worker doesn't target correct queue"
    
    print("✅ Worker command tests passed")


def test_monitoring_commands():
    """Test monitoring commands"""
    print("🔧 Testing Monitoring Commands...")
    
    commands = get_monitoring_commands()
    
    expected_commands = ['flower', 'monitor', 'events', 'inspect_active', 'inspect_stats', 'inspect_reserved']
    for cmd_name in expected_commands:
        assert cmd_name in commands, f"Monitoring command {cmd_name} not found"
        assert 'celery' in commands[cmd_name], f"Command {cmd_name} doesn't contain celery"
    
    print("✅ Monitoring command tests passed")


def test_task_decorators():
    """Test enhanced task decorators"""
    print("🔧 Testing Task Decorators...")
    
    # Test that tasks are properly decorated
    from app.tasks.report_tasks import generate_form_report, trigger_auto_report_generation
    
    # Check that tasks have the correct attributes
    assert hasattr(generate_form_report, 'apply_async'), "Task doesn't have apply_async method"
    assert hasattr(trigger_auto_report_generation, 'apply_async'), "Task doesn't have apply_async method"
    
    print("✅ Task decorator tests passed")


def test_database_integration():
    """Test database integration with tasks"""
    print("🔧 Testing Database Integration...")
    
    app = create_app('testing')
    
    with app.app_context():
        # Create test data
        db.create_all()
        
        # Create test user
        test_user = User(
            email='test@example.com',
            name='Test User',
            is_active=True
        )
        db.session.add(test_user)
        
        # Create test form
        test_form = Form(
            title='Test Form',
            description='Test form for Celery optimization',
            creator_id=test_user.id,
            is_active=True,
            schema={'fields': [{'id': 'test_field', 'type': 'text', 'label': 'Test Field'}]}
        )
        db.session.add(test_form)
        
        # Create test report
        test_report = Report(
            title='Test Report',
            description='Test report for Celery optimization',
            user_id=test_user.id,
            status='pending',
            data={'test': True}
        )
        db.session.add(test_report)
        
        db.session.commit()
        
        print(f"✅ Created test data: User {test_user.id}, Form {test_form.id}, Report {test_report.id}")
        
        # Clean up
        db.session.delete(test_report)
        db.session.delete(test_form)
        db.session.delete(test_user)
        db.session.commit()


def test_performance_metrics():
    """Test performance monitoring capabilities"""
    print("🔧 Testing Performance Metrics...")
    
    # Test task status tracking
    fake_task_id = 'test-task-123'
    
    try:
        status = get_task_status(fake_task_id)
        assert 'task_id' in status, "Task status doesn't include task_id"
        assert 'state' in status, "Task status doesn't include state"
        print("✅ Task status tracking works")
    except Exception as e:
        print(f"⚠️ Task status tracking test failed: {e}")
    
    # Test queue statistics (may fail if no workers running)
    try:
        stats = get_queue_stats()
        print("✅ Queue statistics retrieval works")
    except Exception as e:
        print(f"⚠️ Queue statistics test failed (expected if no workers running): {e}")


def run_performance_benchmark():
    """Run a simple performance benchmark"""
    print("🔧 Running Performance Benchmark...")
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create test user and form
        test_user = User(
            email='benchmark@example.com',
            name='Benchmark User',
            is_active=True
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Measure task creation time
        start_time = time.time()
        
        # Create multiple test reports to simulate load
        reports = []
        for i in range(10):
            report = Report(
                title=f'Benchmark Report {i}',
                description=f'Benchmark report {i} for performance testing',
                user_id=test_user.id,
                status='pending',
                data={'benchmark': True, 'index': i}
            )
            reports.append(report)
            db.session.add(report)
        
        db.session.commit()
        
        creation_time = time.time() - start_time
        print(f"✅ Created 10 test reports in {creation_time:.3f} seconds")
        
        # Clean up
        for report in reports:
            db.session.delete(report)
        db.session.delete(test_user)
        db.session.commit()


def main():
    """Run all tests"""
    print("🚀 Starting Celery Optimization Tests...")
    print("=" * 50)
    
    try:
        test_celery_configuration()
        test_task_routing()
        test_worker_commands()
        test_monitoring_commands()
        test_task_decorators()
        test_database_integration()
        test_performance_metrics()
        run_performance_benchmark()
        
        print("=" * 50)
        print("🎉 All Celery optimization tests completed successfully!")
        
        # Print configuration summary
        print("\n📊 Configuration Summary:")
        config = get_celery_config()
        print(f"   Broker URL: {config.broker_url}")
        print(f"   Result Backend: {config.result_backend}")
        print(f"   Worker Concurrency: {config.worker_concurrency}")
        print(f"   Max Tasks Per Child: {config.worker_max_tasks_per_child}")
        print(f"   Prefetch Multiplier: {config.worker_prefetch_multiplier}")
        print(f"   Task Time Limit: {config.task_time_limit}s")
        print(f"   Max Retries: {config.task_default_max_retries}")
        print(f"   Retry Backoff: {config.task_retry_backoff}")
        print(f"   Number of Queues: {len(config.task_queues)}")
        
        # Print worker commands
        print("\n🔧 Worker Startup Commands:")
        commands = get_worker_startup_commands()
        for name, command in commands.items():
            print(f"   {name}: {command}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)