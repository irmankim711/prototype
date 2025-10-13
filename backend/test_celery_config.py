#!/usr/bin/env python3
"""
Test Celery Configuration
Simple script to test if the Celery configuration is working
"""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_celery_import():
    """Test if we can import the Celery app"""
    try:
        from app.celery_enhanced import celery
        print("✅ Successfully imported Celery app")
        return celery
    except Exception as e:
        print(f"❌ Failed to import Celery app: {e}")
        return None

def test_celery_config(celery_app):
    """Test Celery configuration"""
    if not celery_app:
        return False
    
    try:
        print(f"📡 Broker URL: {celery_app.conf.broker_url}")
        print(f"💾 Result Backend: {celery_app.conf.result_backend}")
        print(f"📋 Task Queues: {[q.name for q in celery_app.conf.task_queues]}")
        print(f"🔄 Task Serializer: {celery_app.conf.task_serializer}")
        print(f"⏰ Timezone: {celery_app.conf.timezone}")
        print("✅ Celery configuration looks good!")
        return True
    except Exception as e:
        print(f"❌ Failed to read Celery config: {e}")
        return False

def test_task_discovery(celery_app):
    """Test if tasks can be discovered"""
    if not celery_app:
        return False
    
    try:
        # Try to discover tasks
        celery_app.autodiscover_tasks(['app.tasks'])
        print("✅ Task discovery successful")
        return True
    except Exception as e:
        print(f"❌ Task discovery failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Celery Configuration...")
    print("=" * 50)
    
    # Test 1: Import
    celery_app = test_celery_import()
    
    # Test 2: Configuration
    if celery_app:
        test_celery_config(celery_app)
        test_task_discovery(celery_app)
    
    print("=" * 50)
    if celery_app:
        print("🎉 All tests passed! Celery is ready to use.")
    else:
        print("💥 Some tests failed. Please check the configuration.")

if __name__ == '__main__':
    main()
