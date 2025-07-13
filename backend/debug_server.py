#!/usr/bin/env python3
"""
Enhanced MVP Server with detailed debugging
"""

import os
import sys
from flask import Flask, request, jsonify

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Change to the correct directory
os.chdir(project_root)
print(f"📁 Working directory: {os.getcwd()}")

# Add current directory to Python path for imports
if '.' not in sys.path:
    sys.path.insert(0, '.')

def create_debug_app():
    """Create Flask app with enhanced debugging"""
    
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    
    # Database configuration
    app.config['SUPABASE_URL'] = 'https://qkyjzxihsopgopudmjin.supabase.co'
    app.config['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFreWp6eGloc29wZ29wdWRtamluIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTIwNDA3MSwiZXhwIjoyMDUwNzgwMDcxfQ.OXGbxOPUvOqZ5yMaKHy5jRTCM1h3KCpRXCqWwg7lHxY'
    
    # Initialize JWT
    from flask_jwt_extended import JWTManager
    jwt = JWTManager(app)
    
    # Request logging middleware
    @app.before_request
    def log_request():
        print(f"\n🔍 Request: {request.method} {request.path}")
        print(f"   Headers: {dict(request.headers)}")
        if request.json:
            print(f"   JSON: {request.json}")
    
    @app.after_request
    def log_response(response):
        print(f"✅ Response: {response.status_code}")
        return response
    
    # Test endpoint
    @app.route('/test-db')
    def test_db():
        try:
            from app.utils.db import get_db_connection
            
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                table_count = cursor.fetchone()[0]
            conn.close()
            
            return jsonify({
                'status': 'success',
                'message': 'Database connection successful',
                'table_count': table_count
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # Register blueprints with debugging
    try:
        print("🔧 Registering blueprints...")
        
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        print("✅ Auth blueprint registered")
        
        from app.routes.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        print("✅ API blueprint registered")
        
        from app.routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
        print("✅ Dashboard blueprint registered")
        
        from app.routes.users import users_bp
        app.register_blueprint(users_bp, url_prefix='/api/users')
        print("✅ Users blueprint registered")
        
        from app.routes.forms import forms_bp
        app.register_blueprint(forms_bp, url_prefix='/api/forms')
        print("✅ Forms blueprint registered")
        
        from app.routes.files import files_bp
        app.register_blueprint(files_bp, url_prefix='/api/files')
        print("✅ Files blueprint registered")
        
    except Exception as e:
        print(f"❌ Blueprint registration failed: {e}")
        raise
    
    # List all routes
    print("\n📋 All registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"   {rule.methods} {rule.rule} -> {rule.endpoint}")
    
    return app

if __name__ == '__main__':
    print("🚀 Starting StratoSys MVP Server with Enhanced Debugging...")
    
    app = create_debug_app()
    
    print("✅ App created successfully!")
    print("🌐 Starting server on http://127.0.0.1:5000")
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to prevent double initialization
    )
