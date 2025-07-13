#!/usr/bin/env python3
"""
Development server startup script for StratoSys MVP
"""

from app import create_app
import os

if __name__ == "__main__":
    app = create_app()
    
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
    print("Ready for MVP testing! 🎯")
    print()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
