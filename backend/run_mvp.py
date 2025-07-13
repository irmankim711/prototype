#!/usr/bin/env python3
"""
Simple Flask app runner for MVP testing
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

if __name__ == "__main__":
    print("🚀 Starting StratoSys MVP Development Server")
    print("=" * 50)
    print("📊 Dashboard API: http://localhost:5000/api/dashboard/stats")
    print("👤 User Profile API: http://localhost:5000/api/users/profile")
    print("📝 Forms API: http://localhost:5000/api/forms/")
    print("📄 Reports API: http://localhost:5000/api/reports")
    print("📁 Files API: http://localhost:5000/api/files/")
    print("🔐 Auth API: http://localhost:5000/auth/login")
    print("🧪 Database Test: http://localhost:5000/test-db")
    print("=" * 50)
    
    try:
        app = create_app()
        print("✅ Flask app created successfully!")
        print("🎯 Ready for MVP testing!")
        print()
        
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False  # Disable reloader to avoid issues
        )
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        import traceback
        traceback.print_exc()
