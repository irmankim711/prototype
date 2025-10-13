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
    
    # Enable CORS for development
    CORS(app, origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174', 'http://127.0.0.1:3000', 'http://127.0.0.1:5173', 'http://127.0.0.1:5174'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'x-request-id', 'X-Request-ID'])
    
    # Load configuration
    if config:
        app.config.from_mapping(config)
    else:
        # Default configuration
        app.config.from_object('app.config.DevelopmentConfig')
    
    # Initialize extensions
    init_extensions(app)
    
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