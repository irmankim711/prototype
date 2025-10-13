#!/usr/bin/env python3
"""
Quick template initialization script
Run this to sync filesystem templates to database
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sync_templates_to_db import main

if __name__ == '__main__':
    print("🚀 Initializing templates...")
    main()