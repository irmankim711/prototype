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

def create_app(config=None):
    """
    Application factory function that creates and configures the Flask app

    Args:
        config: Configuration object or dictionary (optional)

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Enable CORS for development and production
    CORS(app,
         origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174',
                  'http://127.0.0.1:3000', 'http://127.0.0.1:5173', 'http://127.0.0.1:5174',
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

    # ============================================================================
    # 🔥 CRITICAL SECURITY FIX: Clear request context to prevent data leakage
    # ============================================================================
    @app.before_request
    def clear_auth_context():
        """
        Clear authentication context before each request to prevent user data leakage.

        SECURITY: This prevents Flask's g object from leaking between requests
        in multi-threaded or async environments, ensuring User A cannot see User B's data.
        """
        from app.middleware.firebase_auth import clear_request_context
        clear_request_context()

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

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    return app

def init_extensions(app):
    """Initialize Flask extensions"""
    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models after db is initialized to avoid circular imports
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()