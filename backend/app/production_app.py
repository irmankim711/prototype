"""
Production Flask Application Setup - ZERO MOCK DATA
Main application file for production-ready form automation system
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.exceptions import HTTPException

# Production environment setup
def create_production_app(config_name='production'):
    """Create Flask application configured for production"""
    
    app = Flask(__name__)
    
    # ====================================================================
    # PRODUCTION CONFIGURATION - NO MOCK DATA
    # ====================================================================
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'postgresql://your_user:your_password@localhost/production_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 30,
    }
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'production-secret-key-change-this')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    
    # Production Security Settings
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'production-secret-change-this')
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # API Configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    
    # Production API Keys - REAL INTEGRATIONS ONLY
    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
    app.config['GOOGLE_REDIRECT_URI'] = os.getenv('GOOGLE_REDIRECT_URI')
    
    app.config['MICROSOFT_CLIENT_ID'] = os.getenv('MICROSOFT_CLIENT_ID')
    app.config['MICROSOFT_CLIENT_SECRET'] = os.getenv('MICROSOFT_CLIENT_SECRET')
    app.config['MICROSOFT_TENANT_ID'] = os.getenv('MICROSOFT_TENANT_ID')
    
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    
    # Production Feature Flags - DISABLE ALL MOCK DATA
    app.config['MOCK_MODE_DISABLED'] = os.getenv('MOCK_MODE_DISABLED', 'true').lower() == 'true'
    app.config['ENABLE_REAL_GOOGLE_FORMS'] = os.getenv('ENABLE_REAL_GOOGLE_FORMS', 'true').lower() == 'true'
    app.config['ENABLE_REAL_MICROSOFT_FORMS'] = os.getenv('ENABLE_REAL_MICROSOFT_FORMS', 'true').lower() == 'true'
    app.config['ENABLE_REAL_AI'] = os.getenv('ENABLE_REAL_AI', 'true').lower() == 'true'
    
    # Logging Configuration
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Production application startup')
    
    # ====================================================================
    # INITIALIZE EXTENSIONS
    # ====================================================================
    
    # Database
    from .models.production_models import db
    db.init_app(app)
    
    # Migrations
    migrate = Migrate(app, db)
    
    # JWT
    jwt = JWTManager(app)
    
    # CORS
    CORS(app, origins=[
        "http://localhost:3000",  # React development
        "https://your-production-domain.com"  # Production domain
    ])
    
    # ====================================================================
    # PRODUCTION ROUTE REGISTRATION - REAL ENDPOINTS ONLY
    # ====================================================================
    
    # Health check and system status
    from .routes.production_endpoints import production_api_bp
    app.register_blueprint(production_api_bp)
    
    # Real forms integration
    from .routes.production_forms_endpoints import production_forms_bp
    app.register_blueprint(production_forms_bp)
    
    # Real reports generation
    from .routes.production_reports_endpoints import production_reports_bp
    app.register_blueprint(production_reports_bp)
    
    # ====================================================================
    # ERROR HANDLERS
    # ====================================================================
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions"""
        return jsonify({
            'status': 'error',
            'message': e.name,
            'details': e.description,
            'code': e.code
        }), e.code
    
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        """Handle general exceptions"""
        app.logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'details': str(e) if app.debug else 'An unexpected error occurred'
        }), 500
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired JWT tokens"""
        return jsonify({
            'status': 'error',
            'message': 'Token has expired',
            'action_required': 'refresh_token'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid JWT tokens"""
        return jsonify({
            'status': 'error',
            'message': 'Invalid token',
            'action_required': 'authenticate'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing JWT tokens"""
        return jsonify({
            'status': 'error',
            'message': 'Authentication required',
            'action_required': 'provide_token'
        }), 401
    
    # ====================================================================
    # STARTUP VALIDATION
    # ====================================================================
    
    def validate_production_setup():
        """Validate that production setup is correct - NO MOCK DATA"""
        
        validation_errors = []
        
        # Check database connection
        try:
            with app.app_context():
                db.session.execute('SELECT 1')
                app.logger.info("✓ Database connection successful")
        except Exception as e:
            validation_errors.append(f"Database connection failed: {str(e)}")
        
        # Validate API keys are not placeholder values
        google_client_id = app.config.get('GOOGLE_CLIENT_ID')
        if not google_client_id or 'your_' in google_client_id.lower():
            validation_errors.append("Google Client ID not properly configured")
        
        microsoft_client_id = app.config.get('MICROSOFT_CLIENT_ID')
        if not microsoft_client_id or 'your_' in microsoft_client_id.lower():
            validation_errors.append("Microsoft Client ID not properly configured")
        
        openai_key = app.config.get('OPENAI_API_KEY')
        if not openai_key or 'your_' in openai_key.lower():
            validation_errors.append("OpenAI API key not properly configured")
        
        # Check mock mode is disabled
        if not app.config.get('MOCK_MODE_DISABLED'):
            validation_errors.append("Mock mode is still enabled - set MOCK_MODE_DISABLED=true")
        
        # Log validation results
        if validation_errors:
            app.logger.warning("Production setup warnings:")
            for error in validation_errors:
                app.logger.warning(f"  - {error}")
        else:
            app.logger.info("✓ Production setup validation passed")
            app.logger.info("✓ Mock data disabled - real API integrations active")
    
    # ====================================================================
    # MAIN APPLICATION ROUTES
    # ====================================================================
    
    @app.route('/')
    def home():
        """Main application home"""
        return jsonify({
            'application': 'Production Form Automation System',
            'version': '1.0.0',
            'status': 'production',
            'mock_data_disabled': True,
            'api_endpoints': {
                'health': '/api/production/health',
                'forms': '/api/production/forms',
                'reports': '/api/production/reports'
            },
            'features': {
                'real_google_forms': app.config.get('ENABLE_REAL_GOOGLE_FORMS'),
                'real_microsoft_forms': app.config.get('ENABLE_REAL_MICROSOFT_FORMS'),
                'real_ai_analysis': app.config.get('ENABLE_REAL_AI'),
                'mock_mode_disabled': app.config.get('MOCK_MODE_DISABLED')
            }
        })
    
    @app.route('/api/status')
    def api_status():
        """API status endpoint"""
        return jsonify({
            'status': 'operational',
            'environment': 'production',
            'mock_data': False,
            'real_apis_enabled': True,
            'timestamp': str(datetime.utcnow())
        })
    
    # ====================================================================
    # DATABASE INITIALIZATION
    # ====================================================================
    
    def init_production_database():
        """Initialize production database with real schema"""
        with app.app_context():
            try:
                # Import models to ensure they're registered
                from .models.production_models import (
                    User, UserOAuthToken, Program, FormAnalysis, 
                    Report, APILog, SystemConfiguration
                )
                
                # Create all tables
                db.create_all()
                
                # Create default system configurations
                default_configs = [
                    {
                        'key': 'PRODUCTION_MODE',
                        'value': 'true',
                        'value_type': 'boolean',
                        'description': 'System running in production mode'
                    },
                    {
                        'key': 'MOCK_DATA_DISABLED',
                        'value': 'true',
                        'value_type': 'boolean',
                        'description': 'All mock data disabled'
                    }
                ]
                
                for config_data in default_configs:
                    existing = SystemConfiguration.query.filter_by(key=config_data['key']).first()
                    if not existing:
                        config = SystemConfiguration(**config_data)
                        db.session.add(config)
                
                db.session.commit()
                app.logger.info("✓ Production database initialized successfully")
                
            except Exception as e:
                app.logger.error(f"Database initialization failed: {str(e)}")
                raise
    
    # Initialize database on first run
    if os.getenv('INIT_DATABASE', 'false').lower() == 'true':
        init_production_database()
    
    return app

# ====================================================================
# PRODUCTION APPLICATION FACTORY
# ====================================================================

def create_app():
    """Main application factory for production"""
    return create_production_app('production')

if __name__ == '__main__':
    # For development/testing only
    app = create_production_app()
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    )
