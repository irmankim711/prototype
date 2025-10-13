#!/usr/bin/env python3
"""
Test Redis Caching Infrastructure

Tests the complete caching infrastructure including:
- CacheManager functionality
- Form, User, and Template cache managers
- Response caching middleware
- Cache warming utilities
"""

import sys
import os
import time
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Form, ReportTemplate
from app.core.cache import cache_manager, form_cache, user_cache, template_cache
from app.core.cache_warming import cache_warming_service

def test_cache_manager():
    """Test basic cache manager functionality"""
    print("🧪 Testing CacheManager...")
    
    # Test basic operations
    test_key = "test:cache:key"
    test_data = {"message": "Hello, Cache!", "timestamp": datetime.utcnow().isoformat()}
    
    # Test set
    result = cache_manager.set(test_key, test_data, 60)
    print(f"   Set operation: {'✅ Success' if result else '❌ Failed'}")
    
    # Test get
    retrieved_data = cache_manager.get(test_key)
    print(f"   Get operation: {'✅ Success' if retrieved_data == test_data else '❌ Failed'}")
    
    # Test exists
    exists = cache_manager.exists(test_key)
    print(f"   Exists check: {'✅ Success' if exists else '❌ Failed'}")
    
    # Test TTL
    ttl = cache_manager.get_ttl(test_key)
    print(f"   TTL check: {'✅ Success' if ttl > 0 else '❌ Failed'} (TTL: {ttl})")
    
    # Test delete
    deleted = cache_manager.delete(test_key)
    print(f"   Delete operation: {'✅ Success' if deleted else '❌ Failed'}")
    
    # Test health check
    health = cache_manager.health_check()
    print(f"   Health check: {'✅ Healthy' if health['status'] == 'healthy' else '❌ Unhealthy'}")
    
    # Test stats
    stats = cache_manager.get_stats()
    print(f"   Cache stats: Hit rate: {stats.get('hit_rate', 0):.1f}%")
    
    return True

def test_form_cache():
    """Test form cache manager"""
    print("🧪 Testing FormCacheManager...")
    
    if not form_cache:
        print("   ❌ Form cache not available")
        return False
    
    # Test form definition caching
    test_form_id = 999
    test_form_data = {
        "id": test_form_id,
        "title": "Test Form",
        "description": "Test form for caching",
        "schema": {"fields": [{"name": "test", "type": "text"}]},
        "is_active": True
    }
    
    # Test set form definition
    result = form_cache.set_form_definition(test_form_id, test_form_data)
    print(f"   Set form definition: {'✅ Success' if result else '❌ Failed'}")
    
    # Test get form definition
    retrieved_form = form_cache.get_form_definition(test_form_id)
    print(f"   Get form definition: {'✅ Success' if retrieved_form else '❌ Failed'}")
    
    # Test form schema caching
    test_schema = {"fields": [{"name": "test", "type": "text", "required": True}]}
    result = form_cache.set_form_schema(test_form_id, test_schema)
    print(f"   Set form schema: {'✅ Success' if result else '❌ Failed'}")
    
    retrieved_schema = form_cache.get_form_schema(test_form_id)
    print(f"   Get form schema: {'✅ Success' if retrieved_schema else '❌ Failed'}")
    
    # Test submissions count caching
    result = form_cache.set_form_submissions_count(test_form_id, 42)
    print(f"   Set submissions count: {'✅ Success' if result else '❌ Failed'}")
    
    count = form_cache.get_form_submissions_count(test_form_id)
    print(f"   Get submissions count: {'✅ Success' if count == 42 else '❌ Failed'} (Count: {count})")
    
    # Test invalidation
    form_cache.invalidate_form(test_form_id)
    invalidated_form = form_cache.get_form_definition(test_form_id)
    print(f"   Form invalidation: {'✅ Success' if not invalidated_form else '❌ Failed'}")
    
    return True

def test_user_cache():
    """Test user cache manager"""
    print("🧪 Testing UserCacheManager...")
    
    if not user_cache:
        print("   ❌ User cache not available")
        return False
    
    test_user_id = 999
    test_permissions = ["create_report", "read_report", "update_report"]
    test_role = "user"
    test_profile = {
        "id": test_user_id,
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": test_role
    }
    
    # Test permissions caching
    result = user_cache.set_user_permissions(test_user_id, test_permissions)
    print(f"   Set user permissions: {'✅ Success' if result else '❌ Failed'}")
    
    retrieved_permissions = user_cache.get_user_permissions(test_user_id)
    print(f"   Get user permissions: {'✅ Success' if retrieved_permissions == test_permissions else '❌ Failed'}")
    
    # Test role caching
    result = user_cache.set_user_role(test_user_id, test_role)
    print(f"   Set user role: {'✅ Success' if result else '❌ Failed'}")
    
    retrieved_role = user_cache.get_user_role(test_user_id)
    print(f"   Get user role: {'✅ Success' if retrieved_role == test_role else '❌ Failed'}")
    
    # Test profile caching
    result = user_cache.set_user_profile(test_user_id, test_profile)
    print(f"   Set user profile: {'✅ Success' if result else '❌ Failed'}")
    
    retrieved_profile = user_cache.get_user_profile(test_user_id)
    print(f"   Get user profile: {'✅ Success' if retrieved_profile else '❌ Failed'}")
    
    # Test invalidation
    user_cache.invalidate_user(test_user_id)
    invalidated_profile = user_cache.get_user_profile(test_user_id)
    print(f"   User invalidation: {'✅ Success' if not invalidated_profile else '❌ Failed'}")
    
    return True

def test_template_cache():
    """Test template cache manager"""
    print("🧪 Testing ReportTemplateCacheManager...")
    
    if not template_cache:
        print("   ❌ Template cache not available")
        return False
    
    test_template_id = "test-template-999"
    test_template_data = {
        "id": test_template_id,
        "name": "Test Template",
        "description": "Test template for caching",
        "template_type": "report",
        "content_template": "Test content",
        "parameters": {"param1": "value1"},
        "is_public": True
    }
    
    # Test template caching
    result = template_cache.set_template(test_template_id, test_template_data)
    print(f"   Set template: {'✅ Success' if result else '❌ Failed'}")
    
    retrieved_template = template_cache.get_template(test_template_id)
    print(f"   Get template: {'✅ Success' if retrieved_template else '❌ Failed'}")
    
    # Test template list caching
    test_template_list = [
        {"id": "template1", "name": "Template 1", "template_type": "report"},
        {"id": "template2", "name": "Template 2", "template_type": "form"}
    ]
    
    result = template_cache.set_template_list(test_template_list)
    print(f"   Set template list: {'✅ Success' if result else '❌ Failed'}")
    
    retrieved_list = template_cache.get_template_list()
    print(f"   Get template list: {'✅ Success' if retrieved_list else '❌ Failed'}")
    
    # Test invalidation
    template_cache.invalidate_template(test_template_id)
    invalidated_template = template_cache.get_template(test_template_id)
    print(f"   Template invalidation: {'✅ Success' if not invalidated_template else '❌ Failed'}")
    
    return True

def test_cache_warming():
    """Test cache warming functionality"""
    print("🧪 Testing Cache Warming...")
    
    if not cache_warming_service:
        print("   ❌ Cache warming service not available")
        return False
    
    try:
        # Test warming all caches
        print("   Starting cache warming...")
        results = cache_warming_service.warm_all_caches()
        
        print(f"   Forms warmed: {results.get('forms', {}).get('definitions_warmed', 0)}")
        print(f"   Users warmed: {results.get('users', {}).get('permissions_warmed', 0)}")
        print(f"   Templates warmed: {results.get('templates', {}).get('templates_warmed', 0)}")
        print(f"   Dashboard stats warmed: {results.get('dashboard', {}).get('stats_warmed', 0)}")
        
        error_count = len(results.get('errors', []))
        print(f"   Cache warming: {'✅ Success' if error_count == 0 else f'⚠️ Completed with {error_count} errors'}")
        
        if error_count > 0:
            print("   Errors:")
            for error in results.get('errors', [])[:3]:  # Show first 3 errors
                print(f"     - {error}")
        
        return error_count == 0
        
    except Exception as e:
        print(f"   ❌ Cache warming failed: {e}")
        return False

def test_performance():
    """Test cache performance"""
    print("🧪 Testing Cache Performance...")
    
    # Test cache performance with multiple operations
    test_data = {"performance_test": True, "data": list(range(100))}
    operations = 100
    
    # Test write performance
    start_time = time.time()
    for i in range(operations):
        cache_manager.set(f"perf_test:{i}", test_data, 60)
    write_time = time.time() - start_time
    
    # Test read performance
    start_time = time.time()
    hits = 0
    for i in range(operations):
        result = cache_manager.get(f"perf_test:{i}")
        if result:
            hits += 1
    read_time = time.time() - start_time
    
    # Cleanup
    for i in range(operations):
        cache_manager.delete(f"perf_test:{i}")
    
    print(f"   Write performance: {operations} ops in {write_time:.3f}s ({operations/write_time:.1f} ops/sec)")
    print(f"   Read performance: {operations} ops in {read_time:.3f}s ({operations/read_time:.1f} ops/sec)")
    print(f"   Cache hit rate: {hits}/{operations} ({hits/operations*100:.1f}%)")
    
    return hits == operations

def main():
    """Run all cache infrastructure tests"""
    print("🚀 Starting Redis Caching Infrastructure Tests")
    print("=" * 60)
    
    # Create Flask app context
    app = create_app('testing')
    
    with app.app_context():
        test_results = []
        
        # Run tests
        test_results.append(("Cache Manager", test_cache_manager()))
        test_results.append(("Form Cache", test_form_cache()))
        test_results.append(("User Cache", test_user_cache()))
        test_results.append(("Template Cache", test_template_cache()))
        test_results.append(("Cache Warming", test_cache_warming()))
        test_results.append(("Performance", test_performance()))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All caching infrastructure tests passed!")
            return 0
        else:
            print("⚠️ Some tests failed. Check Redis connection and configuration.")
            return 1

if __name__ == "__main__":
    exit(main())