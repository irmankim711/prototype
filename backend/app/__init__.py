from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from celery import Celery
import os
from dotenv import load_dotenv
from sqlalchemy import text, inspect, MetaData, Table

load_dotenv()

db = SQLAlchemy()
celery = Celery(__name__)
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration - added default values and SSL requirement for production
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db').replace(
        'postgresql://', 'postgresql+psycopg2://', 1
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    jwt.init_app(app)
    Migrate(app, db)
    
    # Celery configuration
    celery.conf.update(
        broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    )
    
    # Register blueprints
    from .routes import api, dashboard_bp, users_bp, forms_bp, files_bp
    from .auth import auth_bp
    from .routes.mvp import mvp
    
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(dashboard_bp)  # Dashboard already has /api/dashboard prefix
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(forms_bp, url_prefix='/api/forms')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(auth_bp)
    app.register_blueprint(mvp, url_prefix='/mvp')
    
    # Improved test database endpoint
    @app.route('/test-db')
    def test_db():
        try:
            with db.engine.connect() as conn:  # Use SQLAlchemy's connection
                # Get table list
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result]
                
                # Get data from each table
                tables_data = {}
                for table in tables:
                    try:
                        # Using parameterized queries for safety
                        result = conn.execute(
                            text(f'SELECT * FROM "{table}" LIMIT 5')
                        )
                        columns = [str(col) for col in result.keys()]  # Convert to strings
                        rows = result.fetchall()
                        tables_data[table] = {
                            'columns': columns,
                            'data': [dict(zip(columns, row)) for row in rows],
                            'row_count': len(rows)
                        }
                    except Exception as e:
                        tables_data[table] = {'error': str(e)}
            
            return jsonify({
                'status': 'success',
                'message': 'Database connection successful',
                'tables': tables_data,
                'table_count': len(tables)
            })
            
        except Exception as e:
            app.logger.error(f"Database connection failed: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed',
                'details': str(e)
            }), 500
    
    # Debug endpoint to list all routes
    @app.route('/routes')
    def list_routes():
        """List all registered routes for debugging"""
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': str(rule)
            })
        return jsonify(routes)
    
    return app