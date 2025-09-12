#!/usr/bin/env python3
"""
Enhanced Flask Application Runner
Ensures proper environment loading before application startup
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Import and load environment BEFORE creating app
from app.core.env_loader import load_environment, get_environment_info, force_development_mode

def main():
    """Main application entry point with enhanced environment loading and error handling"""
    try:
        print("🚀 Starting Flask application...")
        
        # Load environment variables first
        print("📁 Loading environment variables...")
        success = load_environment()
        
        if not success:
            print("⚠️ Environment loading had issues, but continuing...")
        
        # Show environment information
        env_info = get_environment_info()
        print(f"🎯 Environment: {env_info['current_environment']}")
        print(f"🐛 Debug Mode: {env_info['debug_mode']}")
        print(f"📁 Files Loaded: {len(env_info['loaded_files'])}")
        
        # Force development mode if needed
        if env_info['current_environment'] != 'development':
            print("🔧 Forcing development mode for local development...")
            force_development_mode()
            
    except Exception as e:
        print(f"❌ Environment Setup Error: {e}")
        import traceback
        print("📋 Full Traceback:")
        traceback.print_exc()
        sys.exit(1)
    
    # Now create and run the app with proper error handling
    try:
        from app import create_app
        print("📦 Creating Flask application...")
        app = create_app()
        print("✅ Flask application created successfully")
        
        # Get configuration from environment
        debug = os.getenv('DEBUG', 'false').lower() == 'true'
        port = int(os.getenv('APP_PORT', '5000'))
        host = os.getenv('APP_HOST', '0.0.0.0')
        
        print(f"🌐 Starting server on {host}:{port}")
        print(f"🐛 Debug mode: {debug}")
        print("=" * 50)
        print("🚀 Server is starting...")
        print("=" * 50)
        
        # Enable threaded mode and error propagation
        app.run(
            debug=debug, 
            port=port, 
            host=host,
            threaded=True,
            use_reloader=debug,
            use_debugger=debug
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 This usually means there's an issue with your app module or dependencies")
        print("🔍 Check your __init__.py file in the app directory")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Application Error: {e}")
        print(f"🔍 Error Type: {type(e).__name__}")
        
        # Print full traceback in debug mode
        if debug:
            import traceback
            print("📋 Full Traceback:")
            traceback.print_exc()
        
        print("💡 Try running with DEBUG=true to see more details")
        sys.exit(1)

if __name__ == '__main__':
    main()

