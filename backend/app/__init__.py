"""
Flask application factory pattern implementation
"""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy



# Create extensions
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

# Simple rate limiter placeholder (for route compatibility)
class SimpleLimiter:
    def limit(self, rate_limit):
        def decorator(f):
            return f  # No-op for now
        return decorator

limiter = SimpleLimiter()

# Global flag to track if app initialization is complete
_app_initialized = False

def create_app(config=None):
    """
    Application factory function that creates and configures the Flask app

    Args:
        config: Configuration object or dictionary (optional)

    Returns:
        Configured Flask application instance
    """
    global _app_initialized
    
    app = Flask(__name__)

    # Enable CORS for development and production
    CORS(app,
         origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174',
                  'http://127.0.0.1:3000', 'http://127.0.0.1:5173', 'http://127.0.0.1:5174',
                  'https://www.stratosys.com.my',
                  'https://stratosys.com.my',
                  'https://stratosys-irmankim711s-projects.vercel.app',
                  'https://*.vercel.app'],  # Allow all Vercel preview deployments
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'x-request-id', 'X-Request-ID',
                        'Accept', 'Origin', 'X-CSRF-Token', 'X-Requested-With'],
         expose_headers=['Content-Length', 'X-JSON', 'X-Request-ID'],
         methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
         max_age=3600)  # Cache preflight requests for 1 hour

    # Load configuration
    if config:
        app.config.from_mapping(config)
    else:
        # Default configuration
        app.config.from_object('app.config.DevelopmentConfig')

    # Initialize extensions
    init_extensions(app)

    # Add global OPTIONS handler for preflight requests
    @app.before_request
    def handle_preflight():
        from flask import request, make_response
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", request.headers.get('Origin', '*'))
            response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
            response.headers.add("Access-Control-Allow-Headers",
                                 "Content-Type, Authorization, x-request-id, X-Request-ID, Accept, Origin, X-CSRF-Token, X-Requested-With")
            response.headers.add("Access-Control-Allow-Credentials", "true")
            response.headers.add("Access-Control-Max-Age", "3600")
            return response, 200

    # Add simple health check endpoint BEFORE registering other blueprints
    @app.route('/api/health', methods=['GET'])
    def simple_health():
        """Lightweight health check endpoint - always responds immediately"""
        return {'status': 'ok', 'message': 'Server is running'}, 200

    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint without /api prefix"""
        return {'status': 'ok', 'message': 'Server is running'}, 200

    @app.route('/api/ready', methods=['GET'])
    def readiness_check():
        """Readiness check endpoint - only returns ok after full initialization"""
        global _app_initialized
        if _app_initialized:
            return {'status': 'ok', 'message': 'Application is ready'}, 200
        else:
            return {'status': 'initializing', 'message': 'Application is starting up'}, 503

    # Register blueprints AFTER health check
    from app.routes import register_blueprints
    register_blueprints(app)
    
    # Mark as initialized after blueprints are registered
    _app_initialized = True
    app.logger.info("✅ Application initialization complete")

    return app

def init_extensions(app):
    """Initialize Flask extensions"""
    # Only initialize SQL database if DATABASE_URL is set
    # (Firestore is used as primary database, SQL is optional for legacy compatibility)
    database_url = app.config.get('SQLALCHEMY_DATABASE_URI')
    use_sql_db = database_url and database_url != 'sqlite:///:memory:' and not database_url.endswith('/app.db')

    if use_sql_db:
        app.logger.info(f"Initializing SQL database: {database_url[:20]}...")
        # Initialize database
        db.init_app(app)
        migrate.init_app(app, db)

        # Import models after db is initialized to avoid circular imports
        with app.app_context():
            try:
                from app import models  # noqa: F401
                db.create_all()
                app.logger.info("SQL database initialized successfully")
            except Exception as e:
                app.logger.warning(f"SQL database initialization failed (using Firestore only): {e}")
    else:
        app.logger.info("SQL database disabled - using Firestore only")
        # Configure a dummy database to prevent errors
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False