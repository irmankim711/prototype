#!/usr/bin/env python3
"""
Simple startup script for the Flask backend
"""
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from app import create_app
    
    app = create_app()
    
    if __name__ == '__main__':
        print("🚀 Starting Enhanced Form Builder Backend...")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🐍 Python path: {sys.path[0]}")
        print("🌐 Server will be available at: http://localhost:5000")
        print("🛠️  Debug mode: ON")
        print("-" * 50)
        
        app.run(
            debug=True,
            port=5000,
            host='0.0.0.0',
            use_reloader=True
        )
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("💡 Make sure you're in the backend directory and all dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting server: {e}")
    sys.exit(1)
