from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery
import os
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import text, inspect, MetaData, Table
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timedelta

# Import error handling system
from .core.error_handlers import register_error_handlers, configure_sentry

# Import configuration
from .core.config import get_settings, get_cors_config
from .core.db_config import get_sqlalchemy_config

# Import enhanced environment loader
from .core.env_loader import load_environment, get_environment_info, force_development_mode

# Load environment variables BEFORE any other configuration
print("🚀 Loading environment variables...")
try:
    load_environment()
    print("✅ Environment variables loaded successfully")
except Exception as e:
    print(f"⚠️ Environment loading had issues: {e}")
    print("🔄 Continuing with default environment settings...")

# Override environment for development if needed
if os.getenv('FLASK_ENV') == 'production' and os.getenv('FORCE_DEVELOPMENT', 'false').lower() == 'true':
    os.environ['FLASK_ENV'] = 'development'
    print("INFO: Forced development mode via FORCE_DEVELOPMENT=true")

# Debug: Show current environment state
try:
    env_info = get_environment_info()
    print(f"🎯 Current FLASK_ENV: {env_info['current_environment']}")
    print(f"🐛 Current DEBUG: {env_info['debug_mode']}")
    print(f"📁 Environment files loaded: {len(env_info['loaded_files'])}")
except Exception as e:
    print(f"⚠️ Could not get environment info: {e}")
    print(f"🎯 Current FLASK_ENV: {os.getenv('FLASK_ENV', 'NOT_SET')}")
    print(f"🐛 Current DEBUG: {os.getenv('DEBUG', 'NOT_SET')}")

db = SQLAlchemy()
celery = Celery(__name__)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration based on environment
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Get centralized configuration
    settings = get_settings()
    
    # Configuration
    app.config['ENV'] = config_name
    app.config['DEBUG'] = settings.debug
    app.config['TESTING'] = settings.testing
    
    # Security Configuration - Use settings from config
    app.config['SECRET_KEY'] = settings.security.secret_key
    
    # Database Configuration - Use production-ready config
    db_config = get_sqlalchemy_config()
    app.config.update(db_config)
    
    # CORS Configuration - Use centralized config
    cors_config = get_cors_config()
    
    # Debug: Log CORS configuration
    print("🔧 CORS Configuration Debug:")
    print(f"   Origins: {cors_config.get('origins', [])}")
    print(f"   Methods: {cors_config.get('methods', [])}")
    print(f"   Allow Headers: {cors_config.get('allow_headers', [])}")
    print(f"   Supports Credentials: {cors_config.get('supports_credentials', False)}")
    
    # Apply CORS to all API routes including NextGen
    CORS(app, 
         resources={
             r"/api/*": cors_config,
             r"/api/v1/*": cors_config,  # Explicitly cover NextGen routes
             r"/v1/*": cors_config,  # Keep for backward compatibility
             r"/health*": cors_config,  # Add health check endpoints
             r"/auth/*": cors_config   # Add auth endpoints
         },
         supports_credentials=cors_config.get('supports_credentials', True))
    
    # Add explicit OPTIONS handling for preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            print(f"🔧 CORS Preflight Request:")
            print(f"   Origin: {request.headers.get('Origin')}")
            print(f"   Method: {request.headers.get('Access-Control-Request-Method')}")
            print(f"   Headers: {request.headers.get('Access-Control-Request-Headers')}")
            print(f"   Path: {request.path}")
            
            response = make_response()
            # Use configured CORS origins
            origin = request.headers.get('Origin')
            if origin and cors_config.get('origins'):
                if origin in cors_config['origins'] or '*' in cors_config['origins']:
                    response.headers.add("Access-Control-Allow-Origin", origin)
                    print(f"   ✅ Origin allowed: {origin}")
                else:
                    response.headers.add("Access-Control-Allow-Origin", cors_config['origins'][0])
                    print(f"   ⚠️ Origin not in allowlist, using first: {cors_config['origins'][0]}")
            else:
                response.headers.add("Access-Control-Allow-Origin", "*")
                print(f"   ⚠️ Using wildcard origin")
            
            response.headers.add('Access-Control-Allow-Headers', ",".join(cors_config.get('allow_headers', [])))
            response.headers.add('Access-Control-Allow-Methods', ",".join(cors_config.get('methods', [])))
            response.headers.add('Access-Control-Allow-Credentials', str(cors_config.get('supports_credentials', True)).lower())
            response.headers.add('Access-Control-Max-Age', str(cors_config.get('max_age', 3600)))
            print(f"   ✅ Preflight response headers set")
            return response
    
    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    limiter.init_app(app)

    # Initialize request tracking middleware
    from .middleware.request_tracking import request_tracker
    request_tracker.init_app(app)
    
    
    # Celery Configuration - Use environment variables
    app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer=os.getenv('CELERY_TASK_SERIALIZER', 'json'),
        result_serializer=os.getenv('CELERY_RESULT_SERIALIZER', 'json'),
        timezone=os.getenv('CELERY_TIMEZONE', 'UTC'),
        enable_utc=True,
        task_track_started=True,
        task_time_limit=int(os.getenv('CELERY_TASK_TIME_LIMIT', '1800')),  # 30 minutes
        task_soft_time_limit=int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '1500')),  # 25 minutes
        worker_prefetch_multiplier=int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', '1')),
        worker_max_tasks_per_child=int(os.getenv('CELERY_WORKER_MAX_TASKS_PER_CHILD', '1000'))
    )
    
    # Sentry Configuration for production
    if config_name == 'production':
        sentry_dsn = os.getenv('SENTRY_DSN')
        if sentry_dsn and sentry_dsn.strip() and sentry_dsn.startswith('https://'):
            try:
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[FlaskIntegration()],
                    traces_sample_rate=0.1,
                    profiles_sample_rate=0.1,
                    environment=config_name
                )
                app.logger.info("✅ Sentry monitoring enabled")
            except Exception as e:
                app.logger.warning(f"⚠️ Sentry initialization failed: {str(e)}")
        else:
            app.logger.info("ℹ️ Sentry monitoring disabled (no valid DSN provided)")
    
    # Enhanced logging configuration
    if app.config.get('ENV') == 'development':
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        app.logger.info('Starting app in development mode')
        
        @app.before_request
        def log_request_info():
            app.logger.debug(f'Request Headers: {request.headers}')
            app.logger.debug(f'Request Body: {request.get_data()}')
            
        @app.after_request
        def log_response_info(response):
            app.logger.debug(f'Response Status: {response.status}')
            app.logger.debug(f'Response Headers: {response.headers}')
            return response
    
    # Setup logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for load balancers and monitoring"""
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db_status = 'healthy'
        except Exception as e:
            app.logger.error(f"Database health check failed: {e}")
            db_status = 'unhealthy'
        
        return jsonify({
            'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': settings.app_version,
            'environment': config_name,
            'database': db_status
        }), 200 if db_status == 'healthy' else 503
    
    # Database health check endpoint
    @app.route('/health/database')
    def database_health_check():
        """Comprehensive database health check endpoint"""
        try:
            from .core.database import check_database_health
            health_result = check_database_health(force=True)
            
            return jsonify(health_result), 200 if health_result['status'] == 'healthy' else 503
            
        except Exception as e:
            app.logger.error(f"Database health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503
    
    # Request logging middleware
    @app.before_request
    def log_request():
        app.logger.debug(f"Incoming Request: {request.method} {request.path}")
        app.logger.debug(f"Headers: {dict(request.headers)}")
        app.logger.debug(f"Body: {request.get_data()}")

    @app.after_request
    def log_response(response):
        app.logger.debug(f"Outgoing Response: {response.status}")
        return response
    
    # Static file serving for previews
    from flask import send_from_directory
    
    @app.route('/static/previews/<filename>')
    def serve_preview(filename):
        """Serve HTML preview files"""
        try:
            import os
            preview_dir = os.path.join(os.getcwd(), 'static', 'previews')
            return send_from_directory(preview_dir, filename)
        except Exception as e:
            logger.error(f"Failed to serve preview file {filename}: {e}")
            return "Preview not found", 404
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Use environment variables for security headers
        if os.getenv('STRICT_TRANSPORT_SECURITY', 'false').lower() == 'true':
            response.headers['Strict-Transport-Security'] = os.getenv('HSTS_MAX_AGE', 'max-age=31536000; includeSubDomains')
        
        if os.getenv('CONTENT_SECURITY_POLICY', 'false').lower() == 'true':
            csp_policy = os.getenv('CSP_POLICY', "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';")
            response.headers['Content-Security-Policy'] = csp_policy
        
        return response
    
    # Request logging middleware
    @app.before_request
    def log_request_info():
        app.logger.info(f'{request.method} {request.path} - {request.remote_addr}')
    
    # Configure Sentry for error tracking
    configure_sentry(app)
    
    # Register comprehensive error handlers
    register_error_handlers(app)
    
    # Setup graceful shutdown
    setup_graceful_shutdown(app)
    
    # Proxy configuration for production
    if config_name == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    return app

def setup_logging(app):
    """Setup application logging"""
    if not app.debug and not app.testing:
        # Production logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/app.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')

def setup_graceful_shutdown(app):
    """Setup graceful shutdown for the application"""
    try:
        from .core.graceful_shutdown import register_common_shutdown_hooks
        from .core.database import db_manager
        
        # Register database shutdown hooks
        def cleanup_database():
            """Cleanup database connections on shutdown"""
            try:
                db_manager.graceful_shutdown()
                app.logger.info("Database connections cleaned up successfully")
            except Exception as e:
                app.logger.error(f"Database cleanup failed: {e}")
        
        # Register shutdown hooks
        register_common_shutdown_hooks(
            app=app,
            db=db_manager,
            redis_client=None,  # Will be set if Redis is configured
            celery_app=celery
        )
        
        # Register custom database cleanup hook
        from .core.graceful_shutdown import register_shutdown_hook
        register_shutdown_hook(
            name="database_cleanup",
            callback=cleanup_database,
            priority=1,
            timeout=30.0,
            critical=True
        )
        
        app.logger.info("✅ Graceful shutdown configured successfully")
        
    except Exception as e:
        app.logger.warning(f"⚠️ Graceful shutdown configuration failed: {e}")
        app.logger.warning("Application will continue without graceful shutdown")

# Old error handler function removed - now using comprehensive error handling system

def register_blueprints(app):
    """Register Flask blueprints with enhanced error handling and logging."""
    logger = app.logger
    
    # Auth blueprint removed - JWT authentication no longer needed
    
    try:
        from .api.v1.integrations import integrations_bp
        logger.info("✅ Integrations blueprint imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import integrations blueprint: {e}")
        raise
    
    try:
        from .public_routes import public_bp
        logger.info("✅ Public routes blueprint imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import public routes blueprint: {e}")
        raise
    
    # Register core blueprints
    app.register_blueprint(integrations_bp)  # Integrations API with /api/v1/integrations prefix
    app.register_blueprint(public_bp, url_prefix='/api/public')
    
    
    # Use the new route registration function
    try:
        from .routes import register_routes
        route_blueprints = register_routes()
        logger.info(f"🎯 Route registration completed with {len(route_blueprints)} modules")
        
        # Register all successfully imported route blueprints
        for name, blueprint in route_blueprints.items():
            try:
                if name == 'dashboard':
                    app.register_blueprint(blueprint)  # Already has url_prefix
                elif name == 'analytics':
                    app.register_blueprint(blueprint)  # Already has url_prefix
                elif name == 'users':
                    app.register_blueprint(blueprint, url_prefix='/api/users')
                elif name == 'forms':
                    app.register_blueprint(blueprint, url_prefix='/api/forms')
                elif name == 'admin_forms':
                    app.register_blueprint(blueprint, url_prefix='/api/admin/forms')
                elif name == 'files':
                    app.register_blueprint(blueprint, url_prefix='/api/files')
                elif name == 'mvp':
                    app.register_blueprint(blueprint, url_prefix='/api/mvp')
                elif name == 'api':
                    app.register_blueprint(blueprint, url_prefix='/api')
                elif name == 'quick_auth':
                    app.register_blueprint(blueprint, url_prefix='/api/quick-auth')
                elif name == 'ai_reports':
                    app.register_blueprint(blueprint, url_prefix='/api')
                elif name == 'reports':
                    app.register_blueprint(blueprint)  # Already has url_prefix /api/reports
                elif name == 'public_forms':
                    app.register_blueprint(blueprint, url_prefix='/api/public-forms')
                elif name == 'google_forms':
                    app.register_blueprint(blueprint)  # Already has url_prefix
                elif name == 'production':
                    app.register_blueprint(blueprint, url_prefix='/api/production')
                elif name == 'production_api':
                    app.register_blueprint(blueprint, url_prefix='/api/production')
                elif name == 'enhanced_report':
                    app.register_blueprint(blueprint, url_prefix='/api/enhanced-report')
                elif name == 'reports_export':
                    app.register_blueprint(blueprint, url_prefix='/api/reports/export')
                elif name == 'nextgen':
                    app.register_blueprint(blueprint, url_prefix='/api/v1/nextgen')
                elif name == 'excel_to_pdf':
                    app.register_blueprint(blueprint)  # Already has url_prefix
                elif name == 'templates_api':
                    app.register_blueprint(blueprint, url_prefix='/api/v1')

                logger.info(f"✅ Successfully registered {name} blueprint")
                
            except Exception as e:
                logger.error(f"❌ Failed to register {name} blueprint: {e}")
                # Continue with other blueprints instead of crashing
        
    except Exception as e:
        logger.error(f"❌ Route registration failed: {e}")
        # Fallback to basic route registration
        logger.warning("⚠️ Falling back to basic route registration")
        try:
            from .routes.dashboard import dashboard_bp
            from .routes.users import users_bp
            from .routes.files import files_bp
            from .routes.api import api
            from .routes.nextgen_report_builder import nextgen_bp
            from .routes.reports_api import reports_bp

            app.register_blueprint(dashboard_bp)
            app.register_blueprint(users_bp, url_prefix='/api/users')
            app.register_blueprint(files_bp, url_prefix='/api/files')
            app.register_blueprint(api, url_prefix='/api')
            app.register_blueprint(nextgen_bp, url_prefix='/api/v1/nextgen')
            app.register_blueprint(reports_bp)  # Already has url_prefix /api/reports

            logger.info("✅ Basic route registration completed")
        except Exception as fallback_error:
            logger.error(f"❌ Basic route registration also failed: {fallback_error}")
            raise
    
    # Excel-to-DOCX bridge blueprint is auto-registered via routes module loader
    # Removing duplicate registration to prevent conflicts
    
    logger.info("🎉 All blueprints registered successfully")

def main():
    app = create_app()
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()