#!/usr/bin/env python3
"""
Production WSGI application for the Flask backend.
This file is used by Gunicorn, uWSGI, or other WSGI servers.
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging early to see startup issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wsgi')

try:
    logger.info("🚀 Starting WSGI application initialization...")
    from app import create_app
    
    logger.info("📦 Creating Flask application...")
    # Create the application instance
    # create_app expects a config dict/object or None, not a string
    application = create_app()
    logger.info("✅ Flask application created successfully")
    
except Exception as e:
    logger.exception(f"❌ Failed to create application: {e}")
    # Exit gracefully to prevent container from hanging
    sys.exit(1)

if __name__ == '__main__':
    # For development only - use gunicorn in production
    application.run(host='0.0.0.0', port=5000)
