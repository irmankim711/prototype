from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from celery import Celery
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from sqlalchemy import text, inspect, MetaData, Table
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, timedelta

load_dotenv()

db = SQLAlchemy()
celery = Celery(__name__)
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration based on environment
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Configuration
    app.config['ENV'] = config_name
    app.config['DEBUG'] = config_name == 'development'
    app.config['TESTING'] = config_name == 'testing'
    
    # Security Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))  # 1 hour
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))  # 30 days
    app.config['JWT_ALGORITHM'] = 'HS256'  # Explicitly set algorithm
    app.config['JWT_DECODE_ALGORITHMS'] = ['HS256']  # Allowed algorithms for decoding
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'msg'  # Consistent error message key
    # JWT Cookie configuration
    app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/api/auth/refresh'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # For development only! Enable and handle CSRF in production.
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token_cookie'
    app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token_cookie'
    
    # Database Configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', 20)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 20))
    }
    
    # CORS Configuration - Enhanced for preflight handling
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://localhost:5174"],
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                 "expose_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True
             }
         },
         supports_credentials=True)
    
    # Add explicit OPTIONS handling for preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization,X-Requested-With")
            response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            return response
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)
    limiter.init_app(app)
    
    # JWT User Identity Loader - Critical for resolving 422 errors
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """Convert user object to identity for JWT token with enhanced validation."""
        try:
            # Handle different input types
            if isinstance(user, str):
                # If it's already a string, validate and return
                if user == 'bypass-user':
                    return user
                # Try to convert to int and back to string to validate
                try:
                    int(user)
                    return user
                except ValueError:
                    app.logger.error(f"Invalid string identity: {user}")
                    return None
            elif isinstance(user, int):
                return str(user)
            elif hasattr(user, 'id'):
                # User object with id attribute
                return str(user.id)
            else:
                app.logger.error(f"Invalid user type for identity: {type(user)} - {user}")
                return None
        except Exception as e:
            app.logger.error(f"Identity lookup failed: {e}")
            return None
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Load user from JWT token data with enhanced error handling."""
        from .models import User
        identity = jwt_data["sub"]
        
        # Handle bypass user for development
        if identity == 'bypass-user':
            return None  # Bypass user doesn't need database lookup
        
        try:
            # Ensure identity is a string and try to convert to int
            if isinstance(identity, str):
                user_id = int(identity)
            elif isinstance(identity, int):
                user_id = identity
            else:
                app.logger.error(f"Invalid identity type: {type(identity)} - {identity}")
                return None
            
            # Look up user in database
            user = User.query.get(user_id)
            if user and user.is_active:
                return user
            elif user and not user.is_active:
                app.logger.warning(f"Inactive user attempted access: {user_id}")
                return None
            else:
                app.logger.warning(f"User not found: {user_id}")
                return None
                
        except (ValueError, TypeError) as e:
            app.logger.error(f"User lookup failed - Invalid identity format: {identity} - Error: {e}")
            return None
        except Exception as e:
            app.logger.error(f"User lookup failed - Database error: {e}")
            return None
    
    # JWT Error Handlers - Critical for resolving 422 errors
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired tokens."""
        return jsonify({
            'error': 'token_expired',
            'message': 'The token has expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        """Handle invalid tokens."""
        return jsonify({
            'error': 'invalid_token',
            'message': 'Token validation failed',
            'details': error_string
        }), 422
    
    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        """Handle missing tokens."""
        return jsonify({
            'error': 'missing_token',
            'message': 'Authentication token is required',
            'details': error_string
        }), 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        """Handle non-fresh tokens when fresh token is required."""
        return jsonify({
            'error': 'fresh_token_required',
            'message': 'A fresh token is required'
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked tokens."""
        return jsonify({
            'error': 'token_revoked',
            'message': 'The token has been revoked'
        }), 401
    
    @jwt.token_verification_failed_loader
    def token_verification_failed_callback(jwt_header, jwt_payload):
        """Handle token verification failures."""
        return jsonify({
            'error': 'token_verification_failed',
            'message': 'Token verification failed'
        }), 422
    
    @jwt.decode_key_loader
    def decode_key_callback(jwt_header, jwt_payload):
        """Provide the key for decoding JWT tokens."""
        return app.config['JWT_SECRET_KEY']
    
    # Celery configuration
    celery.conf.update(
        broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000
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
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': config_name,
            'database': db_status
        }), 200 if db_status == 'healthy' else 503
    
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
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        return response
    
    # Request logging middleware
    @app.before_request
    def log_request_info():
        app.logger.info(f'{request.method} {request.path} - {request.remote_addr}')
    
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

def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({'error': 'File too large'}), 413
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return jsonify({'error': 'Rate limit exceeded'}), 429

def register_blueprints(app):
    """Register Flask blueprints."""
    from .auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.analytics import analytics_bp
    from .routes.users import users_bp
    from .routes.forms import forms_bp
    from .routes.admin_forms import admin_forms_bp
    from .routes.files import files_bp
    from .routes.mvp import mvp
    from .routes.api import api
    from .routes.quick_auth import quick_auth_bp
    from .routes.ai_reports import ai_reports_bp
    from .public_routes import public_bp
    from .routes.public_forms import public_forms_bp
    from .routes.google_forms_routes import google_forms_bp
    from .routes.production_routes import production_bp  # NEW: Production routes
    from .routes.enhanced_report_routes import enhanced_report_bp  # NEW: Enhanced Report Builder
    from .routes.reports_export import reports_export_bp  # NEW: Unified reports export
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp)  # Dashboard already has url_prefix='/api/dashboard'
    app.register_blueprint(analytics_bp)  # Analytics already has url_prefix='/api/analytics'
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(forms_bp, url_prefix='/api/forms')
    app.register_blueprint(admin_forms_bp, url_prefix='/api/admin/forms')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(mvp, url_prefix='/api/mvp')
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(quick_auth_bp, url_prefix='/api/quick-auth')
    app.register_blueprint(ai_reports_bp, url_prefix='/api')
    app.register_blueprint(public_bp, url_prefix='/api/public')
    app.register_blueprint(public_forms_bp, url_prefix='/api/public-forms')
    app.register_blueprint(google_forms_bp)  # Already has url_prefix='/api/google-forms'
    app.register_blueprint(production_bp)  # NEW: Production routes with /api/production prefix
    app.register_blueprint(enhanced_report_bp)  # NEW: Enhanced Report Builder with /api/enhanced-report prefix
    app.register_blueprint(reports_export_bp)  # NEW: Unified export endpoints under /api/reports

def main():
    app = create_app()
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()