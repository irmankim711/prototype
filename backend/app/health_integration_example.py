"""
Health Check System Integration Example

This file shows how to integrate the comprehensive health check and monitoring system
into your main Flask application.
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import redis

# Import health check and monitoring components
from .core.health_checks import (
    HealthCheckRegistry,
    DatabaseHealthCheck,
    RedisHealthCheck,
    ExternalAPIHealthCheck,
    SystemResourceHealthCheck
)
from .core.monitoring import CorrelationIDMiddleware, performance_monitor
from .core.graceful_shutdown import register_common_shutdown_hooks
from .routes.health import health_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application with health checks."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize extensions
    db = SQLAlchemy(app)
    jwt = JWTManager(app)
    
    # Initialize Redis client
    try:
        redis_client = redis.from_url(
            app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        )
        redis_client.ping()  # Test connection
        logger.info("✅ Redis connected successfully")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        redis_client = None
    
    # Initialize health check system
    initialize_health_checks(app, db, redis_client)
    
    # Initialize monitoring system
    initialize_monitoring(app)
    
    # Initialize graceful shutdown
    initialize_graceful_shutdown(app, db, redis_client)
    
    # Register blueprints
    register_blueprints(app)
    
    return app

def initialize_health_checks(app, db, redis_client):
    """Initialize the health check system."""
    logger.info("🔧 Initializing health check system...")
    
    # Create health check registry
    registry = HealthCheckRegistry()
    app.health_check_registry = registry
    
    # Register database health check
    try:
        db_check = DatabaseHealthCheck(db.session)
        registry.register_check(db_check)
        logger.info("✅ Database health check registered")
    except Exception as e:
        logger.error(f"❌ Failed to register database health check: {e}")
    
    # Register Redis health check
    if redis_client:
        try:
            redis_check = RedisHealthCheck(redis_client)
            registry.register_check(redis_check)
            logger.info("✅ Redis health check registered")
        except Exception as e:
            logger.error(f"❌ Failed to register Redis health check: {e}")
    else:
        logger.warning("⚠️ Redis health check not registered (Redis unavailable)")
    
    # Register external API health checks
    external_apis = [
        ("google", "https://www.google.com", 10),
        ("microsoft", "https://www.microsoft.com", 10),
        ("openai", "https://api.openai.com", 15),
    ]
    
    for name, url, timeout in external_apis:
        try:
            api_check = ExternalAPIHealthCheck(name, url, timeout)
            registry.register_check(api_check)
            logger.info(f"✅ {name.capitalize()} API health check registered")
        except Exception as e:
            logger.error(f"❌ Failed to register {name} API health check: {e}")
    
    # Register system resources health check
    try:
        system_check = SystemResourceHealthCheck()
        registry.register_check(system_check)
        logger.info("✅ System resources health check registered")
    except Exception as e:
        logger.error(f"❌ Failed to register system resources health check: {e}")
    
    logger.info(f"✅ Health check system initialized with {len(registry.checks)} checks")

def initialize_monitoring(app):
    """Initialize the monitoring system."""
    logger.info("🔧 Initializing monitoring system...")
    
    try:
        # Add correlation ID middleware
        correlation_middleware = CorrelationIDMiddleware(app)
        logger.info("✅ Correlation ID middleware initialized")
        
        # Initialize performance monitoring
        app.performance_monitor = performance_monitor
        logger.info("✅ Performance monitoring initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize monitoring system: {e}")

def initialize_graceful_shutdown(app, db, redis_client):
    """Initialize graceful shutdown system."""
    logger.info("🔧 Initializing graceful shutdown system...")
    
    try:
        # Register common shutdown hooks
        register_common_shutdown_hooks(app, db, redis_client)
        logger.info("✅ Graceful shutdown system initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize graceful shutdown: {e}")

def register_blueprints(app):
    """Register application blueprints."""
    logger.info("🔧 Registering blueprints...")
    
    # Register health check blueprint
    try:
        app.register_blueprint(health_bp, url_prefix='/api')
        logger.info("✅ Health check blueprint registered")
    except Exception as e:
        logger.error(f"❌ Failed to register health check blueprint: {e}")
    
    # Register other blueprints here
    # app.register_blueprint(auth_bp, url_prefix='/api/auth')
    # app.register_blueprint(users_bp, url_prefix='/api/users')
    # etc.

def run_health_check_demo():
    """Run a demonstration of the health check system."""
    logger.info("🚀 Running health check system demo...")
    
    app = create_app()
    
    with app.app_context():
        # Get health check registry
        registry = app.health_check_registry
        
        if not registry:
            logger.error("❌ Health check registry not available")
            return
        
        # Run a quick health check
        logger.info("🔍 Running health checks...")
        
        import asyncio
        
        # Create new event loop for health checks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(registry.run_all_checks())
            
            # Display results
            logger.info("📊 Health Check Results:")
            logger.info(f"Total checks: {len(results)}")
            
            for result in results:
                status_emoji = "✅" if result.status.value == "healthy" else "⚠️" if result.status.value == "degraded" else "❌"
                logger.info(f"{status_emoji} {result.name}: {result.status.value} - {result.message}")
            
            # Get overall status
            overall_status = registry.get_overall_status(results)
            summary = registry.get_summary(results)
            
            logger.info(f"🏥 Overall System Status: {overall_status.value}")
            logger.info(f"📈 Summary: {summary}")
            
        finally:
            loop.close()
        
        logger.info("✅ Health check demo completed")

if __name__ == "__main__":
    # Run the demo
    run_health_check_demo()
