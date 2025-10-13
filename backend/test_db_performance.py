#!/usr/bin/env python3
"""
Database Performance Testing Script
Tests the implemented database performance optimizations.
"""

import time
import statistics
from app import create_app, db
from app.models import Form, FormSubmission, Report, User
from app.core.query_optimizer import QueryOptimizer, time_query
from app.core.performance_monitor import QueryTimer, performance_monitor
from app.core.db_health import db_health_monitor, with_db_retry
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePerformanceTest:
    """Test database performance optimizations."""
    
    def __init__(self):
        self.app = create_app()
        self.test_results = {}
        
    def setup_test_data(self):
        """Setup test data for performance testing."""
        with self.app.app_context():
            try:
                # Check if test data already exists
                test_user = User.query.filter_by(email='test_performance@example.com').first()
                if test_user:
                    logger.info("Test data already exists, skipping setup")
                    return test_user.id
                
                # Create test user
                test_user = User(
                    email='test_performance@example.com',
                    password_hash='test_hash',
                    first_name='Test',
                    last_name='User'
                )
                db.session.add(test_user)
                db.session.flush()
                
                # Create test forms
                for i in range(10):
                    form = Form(
                        title=f'Performance Test Form {i}',
                        description=f'Test form {i} for performance testing',
                        creator_id=test_user.id,
                        schema={'fields': [{'type': 'text', 'name': f'field_{i}'}]},
                        is_active=True,
                        is_public=i % 2 == 0  # Make every other form public
                    )
                    db.session.add(form)
                
                db.session.commit()
                logger.info(f"Created test data with user ID: {test_user.id}")
                return test_user.id
                
            except Exception as e:
                logger.error(f"Error setting up test data: {str(e)}")
                db.session.rollback()
                return None
    
    def test_index_performance(self):
        """Test database index performance."""
        logger.info("Testing database index performance...")
        
        with self.app.app_context():
            times = []
            
            # Test form queries by creator_id (should use index)
            for _ in range(10):
                start_time = time.time()
                forms = Form.query.filter(Form.creator_id == 1).all()
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            self.test_results['index_query_avg_time'] = avg_time
            logger.info(f"Average indexed query time: {avg_time:.4f}s")
            
            # Test form queries by is_active (should use index)
            times = []
            for _ in range(10):
                start_time = time.time()
                forms = Form.query.filter(Form.is_active == True).all()
                end_time = time.time()
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            self.test_results['boolean_index_avg_time'] = avg_time
            logger.info(f"Average boolean index query time: {avg_time:.4f}s")
    
    def test_optimized_queries(self):
        """Test optimized query patterns."""
        logger.info("Testing optimized query patterns...")
        
        with self.app.app_context():
            user_id = 1  # Assuming test user exists
            
            # Test optimized user forms query
            start_time = time.time()
            forms = QueryOptimizer.get_user_forms_optimized(user_id)
            end_time = time.time()
            
            optimized_time = end_time - start_time
            self.test_results['optimized_user_forms_time'] = optimized_time
            logger.info(f"Optimized user forms query time: {optimized_time:.4f}s")
            
            # Test optimized form with submissions
            if forms:
                start_time = time.time()
                form_with_subs = QueryOptimizer.get_form_with_submissions(forms[0].id, user_id)
                end_time = time.time()
                
                optimized_time = end_time - start_time
                self.test_results['optimized_form_with_subs_time'] = optimized_time
                logger.info(f"Optimized form with submissions query time: {optimized_time:.4f}s")
    
    def test_connection_pool_health(self):
        """Test database connection pool health."""
        logger.info("Testing database connection pool health...")
        
        with self.app.app_context():
            # Get connection pool metrics
            metrics = db_health_monitor.get_connection_pool_metrics()
            
            if metrics:
                self.test_results['connection_pool_metrics'] = metrics
                logger.info(f"Connection pool metrics: {metrics}")
                
                # Test connection health
                health_status = db_health_monitor.check_database_health()
                self.test_results['db_health_status'] = health_status
                logger.info(f"Database health status: {'Healthy' if health_status else 'Unhealthy'}")
            else:
                logger.warning("Could not retrieve connection pool metrics")
    
    @with_db_retry(max_retries=3)
    def test_retry_mechanism(self):
        """Test database retry mechanism."""
        logger.info("Testing database retry mechanism...")
        
        with self.app.app_context():
            try:
                # This should succeed normally
                forms = Form.query.limit(5).all()
                self.test_results['retry_test_success'] = True
                logger.info(f"Retry mechanism test passed - retrieved {len(forms)} forms")
                
            except Exception as e:
                self.test_results['retry_test_success'] = False
                logger.error(f"Retry mechanism test failed: {str(e)}")
    
    def test_query_timing_decorator(self):
        """Test query timing decorator."""
        logger.info("Testing query timing decorator...")
        
        @time_query
        def timed_query():
            with self.app.app_context():
                return Form.query.all()
        
        start_time = time.time()
        forms = timed_query()
        end_time = time.time()
        
        total_time = end_time - start_time
        self.test_results['timed_query_duration'] = total_time
        logger.info(f"Timed query completed in {total_time:.4f}s, found {len(forms)} forms")
    
    def test_bulk_operations(self):
        """Test bulk operation performance."""
        logger.info("Testing bulk operations...")
        
        with self.app.app_context():
            # Test bulk view count update
            form_ids = [f.id for f in Form.query.limit(5).all()]
            
            if form_ids:
                start_time = time.time()
                QueryOptimizer.bulk_update_form_view_counts(form_ids)
                end_time = time.time()
                
                bulk_time = end_time - start_time
                self.test_results['bulk_update_time'] = bulk_time
                logger.info(f"Bulk update of {len(form_ids)} forms took {bulk_time:.4f}s")
    
    def run_all_tests(self):
        """Run all performance tests."""
        logger.info("Starting database performance tests...")
        
        # Setup test data
        user_id = self.setup_test_data()
        if not user_id:
            logger.error("Failed to setup test data, aborting tests")
            return
        
        # Run individual tests
        try:
            self.test_index_performance()
            self.test_optimized_queries()
            self.test_connection_pool_health()
            self.test_retry_mechanism()
            self.test_query_timing_decorator()
            self.test_bulk_operations()
            
        except Exception as e:
            logger.error(f"Error during performance tests: {str(e)}")
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary."""
        logger.info("\n" + "="*50)
        logger.info("DATABASE PERFORMANCE TEST SUMMARY")
        logger.info("="*50)
        
        for test_name, result in self.test_results.items():
            if isinstance(result, float):
                logger.info(f"{test_name}: {result:.4f}s")
            elif isinstance(result, dict):
                logger.info(f"{test_name}: {result}")
            else:
                logger.info(f"{test_name}: {result}")
        
        logger.info("="*50)
        
        # Performance recommendations
        self.print_recommendations()
    
    def print_recommendations(self):
        """Print performance recommendations based on test results."""
        logger.info("\nPERFORMANCE RECOMMENDATIONS:")
        
        # Check query times
        if 'index_query_avg_time' in self.test_results:
            if self.test_results['index_query_avg_time'] > 0.1:
                logger.warning("- Index queries are slower than expected (>0.1s)")
            else:
                logger.info("- Index query performance is good")
        
        # Check connection pool utilization
        if 'connection_pool_metrics' in self.test_results:
            metrics = self.test_results['connection_pool_metrics']
            if metrics['pool_utilization'] > 80:
                logger.warning("- High connection pool utilization, consider increasing pool size")
            elif metrics['pool_utilization'] < 20:
                logger.info("- Low connection pool utilization, current settings are adequate")
        
        logger.info("Performance testing completed!")

if __name__ == '__main__':
    test_runner = DatabasePerformanceTest()
    test_runner.run_all_tests()