#!/usr/bin/env python3
"""
Production WSGI application for the Flask backend.
This file is used by Gunicorn, uWSGI, or other WSGI servers.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app import create_app

# Create the application instance
application = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    # For development only - use gunicorn in production
    application.run(host='0.0.0.0', port=5000)
