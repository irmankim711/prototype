from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
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
from datetime import datetime

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
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days
    
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
    
    # CORS Configuration
    cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS(app, 
          resources={r"/*": {"origins": cors_origins}}, 
          supports_credentials=True,
          methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)
    limiter.init_app(app)
    
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
        if sentry_dsn:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration()],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
                environment=config_name
            )
    
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
    """Register application blueprints"""
    from .routes import api, dashboard_bp, users_bp, forms_bp, files_bp
    from .auth import auth_bp
    from .routes.mvp import mvp
    
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(forms_bp, url_prefix='/api/forms')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(auth_bp)
    app.register_blueprint(mvp, url_prefix='/mvp')