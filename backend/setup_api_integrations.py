#!/usr/bin/env python3
"""
API Integration Setup Script
Meta DevOps Engineering Standards - Automated Setup

This script sets up the complete API integration environment:
- Google Sheets OAuth2 configuration
- Microsoft Graph OAuth2 configuration
- Required dependencies installation
- Database schema updates
- Security key generation
- Environment validation
"""

import os
import sys
import subprocess
import secrets
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message: str):
    """Print formatted header message"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")

def run_command(command: str, check: bool = True):
    """Run shell command with error handling"""
    try:
        result = subprocess.run(
            command.split(),
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        print_error(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return None

def check_prerequisites():
    """Check system prerequisites"""
    print_header("Checking Prerequisites")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major != 3 or python_version.minor < 8:
        print_error("Python 3.8+ is required")
        sys.exit(1)
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check Node.js
    try:
        result = run_command("node --version")
        if result:
            node_version = result.stdout.strip()
            print_success(f"Node.js {node_version}")
        else:
            print_error("Failed to get Node.js version")
    except:
        print_error("Node.js is not installed")
        sys.exit(1)
    
    # Check Redis
    try:
        result = run_command("redis-cli ping", check=False)
        if result and "PONG" in result.stdout:
            print_success("Redis server is running")
        else:
            print_warning("Redis server is not running")
            print_info("Start Redis server: redis-server")
    except:
        print_warning("Redis CLI not found - install Redis")
    
    # Check PostgreSQL
    try:
        result = run_command("psql --version")
        if result:
            pg_version = result.stdout.strip()
            print_success(f"PostgreSQL {pg_version}")
        else:
            print_warning("Failed to get PostgreSQL version")
    except:
        print_warning("PostgreSQL client not found")

def install_python_dependencies():
    """Install required Python packages"""
    print_header("Installing Python Dependencies")
    
    dependencies = [
        "google-api-python-client>=2.0.0",
        "google-auth>=2.0.0",
        "google-auth-oauthlib>=1.0.0",
        "msal>=1.20.0",
        "httpx>=0.24.0",
        "tenacity>=8.0.0",
        "cryptography>=3.4.0",
        "redis>=4.0.0",
        "pydantic>=1.10.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0"
    ]
    
    for package in dependencies:
        try:
            print_info(f"Installing {package}...")
            run_command(f"pip install {package}")
            print_success(f"Installed {package}")
        except Exception as e:
            print_error(f"Failed to install {package}: {e}")

def install_frontend_dependencies():
    """Install required frontend packages"""
    print_header("Installing Frontend Dependencies")
    
    os.chdir("../frontend")
    
    dependencies = [
        "@mui/material",
        "@mui/icons-material",
        "@emotion/react",
        "@emotion/styled",
        "axios",
        "react-router-dom"
    ]
    
    for package in dependencies:
        try:
            print_info(f"Installing {package}...")
            run_command(f"npm install {package}")
            print_success(f"Installed {package}")
        except Exception as e:
            print_error(f"Failed to install {package}: {e}")
    
    os.chdir("../backend")

def generate_security_keys():
    """Generate secure keys for encryption"""
    print_header("Generating Security Keys")
    
    # Generate encryption key (32 bytes for AES-256)
    encryption_key = secrets.token_hex(32)
    print_success("Generated TOKEN_ENCRYPTION_KEY")
    
    # Generate JWT secret
    jwt_secret = secrets.token_urlsafe(64)
    print_success("Generated JWT_SECRET_KEY")
    
    return {
        'TOKEN_ENCRYPTION_KEY': encryption_key,
        'JWT_SECRET_KEY': jwt_secret
    }

def setup_environment_file(security_keys: Dict[str, str]):
    """Setup environment configuration file"""
    print_header("Setting Up Environment Configuration")
    
    env_template = Path(".env.api_integrations")
    env_file = Path(".env")
    
    if env_template.exists():
        # Read template
        with open(env_template, 'r') as f:
            env_content = f.read()
        
        # Replace security keys
        env_content = env_content.replace(
            "your_32_character_encryption_key_here",
            security_keys['TOKEN_ENCRYPTION_KEY']
        )
        env_content = env_content.replace(
            "your_jwt_secret_key_here",
            security_keys['JWT_SECRET_KEY']
        )
        
        # Write to .env file
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print_success("Created .env file with security keys")
        print_warning("Please update OAuth2 credentials in .env file:")
        print_info("  - GOOGLE_CLIENT_ID")
        print_info("  - GOOGLE_CLIENT_SECRET")
        print_info("  - MICROSOFT_CLIENT_ID")
        print_info("  - MICROSOFT_CLIENT_SECRET")
        print_info("  - MICROSOFT_TENANT_ID")
    else:
        print_error("Environment template not found")

def setup_oauth_applications():
    """Provide instructions for OAuth application setup"""
    print_header("OAuth Application Setup Instructions")
    
    print_info("Google Cloud Console Setup:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing project")
    print("3. Enable Google Sheets API and Google Drive API")
    print("4. Go to Credentials > Create Credentials > OAuth 2.0 Client IDs")
    print("5. Set Application type to 'Web application'")
    print("6. Add authorized redirect URIs:")
    print("   - http://localhost:3000/auth/callback (development)")
    print("   - https://yourdomain.com/auth/callback (production)")
    print("7. Copy Client ID and Client Secret to .env file\n")
    
    print_info("Microsoft Azure App Registration:")
    print("1. Go to https://portal.azure.com/")
    print("2. Navigate to Azure Active Directory > App registrations")
    print("3. Click 'New registration'")
    print("4. Set name and redirect URI:")
    print("   - http://localhost:3000/auth/callback (development)")
    print("   - https://yourdomain.com/auth/callback (production)")
    print("5. Go to Certificates & secrets > New client secret")
    print("6. Go to API permissions > Add permission:")
    print("   - Microsoft Graph > Delegated permissions")
    print("   - Add Files.ReadWrite.All, Sites.ReadWrite.All, User.Read")
    print("7. Copy Application ID, Directory ID, and Client Secret to .env file\n")

def create_database_tables():
    """Create database tables for API integrations"""
    print_header("Setting Up Database Tables")
    
    sql_schema = """
    -- API Integration Tables
    CREATE TABLE IF NOT EXISTS api_integrations (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        service_type VARCHAR(50) NOT NULL,
        service_user_id VARCHAR(255),
        encrypted_refresh_token TEXT,
        status VARCHAR(20) DEFAULT 'connected',
        scopes TEXT[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_sync_at TIMESTAMP,
        UNIQUE(user_id, service_type)
    );
    
    CREATE TABLE IF NOT EXISTS integration_metrics (
        id SERIAL PRIMARY KEY,
        integration_id INTEGER NOT NULL REFERENCES api_integrations(id),
        metric_type VARCHAR(50) NOT NULL,
        metric_value INTEGER DEFAULT 0,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS integration_audit_log (
        id SERIAL PRIMARY KEY,
        integration_id INTEGER NOT NULL REFERENCES api_integrations(id),
        operation VARCHAR(100) NOT NULL,
        operation_data JSONB,
        success BOOLEAN DEFAULT true,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_api_integrations_user_service 
        ON api_integrations(user_id, service_type);
    CREATE INDEX IF NOT EXISTS idx_integration_metrics_integration_type 
        ON integration_metrics(integration_id, metric_type);
    CREATE INDEX IF NOT EXISTS idx_integration_audit_log_integration_created 
        ON integration_audit_log(integration_id, created_at);
    """
    
    try:
        # Save schema to file
        schema_file = Path("migrations/004_api_integrations.sql")
        schema_file.parent.mkdir(exist_ok=True)
        
        with open(schema_file, 'w') as f:
            f.write(sql_schema)
        
        print_success("Created database migration file")
        print_info("Run: python manage.py migrate to apply database changes")
        
    except Exception as e:
        print_error(f"Failed to create database schema: {e}")

def setup_testing_framework():
    """Setup testing framework for API integrations"""
    print_header("Setting Up Testing Framework")
    
    test_requirements = [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "httpx>=0.24.0",
        "pytest-mock>=3.10.0",
        "fakeredis>=2.10.0"
    ]
    
    for package in test_requirements:
        try:
            run_command(f"pip install {package}")
            print_success(f"Installed {package}")
        except Exception as e:
            print_error(f"Failed to install {package}: {e}")

def validate_setup():
    """Validate the complete setup"""
    print_header("Validating Setup")
    
    checks = [
        ("Environment file exists", Path(".env").exists()),
        ("Google API client installed", check_package("google-api-python-client")),
        ("Microsoft Graph library installed", check_package("msal")),
        ("Redis connection", check_redis_connection()),
        ("Database migration ready", Path("migrations/004_api_integrations.sql").exists())
    ]
    
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    if all_passed:
        print_success("All validation checks passed!")
    else:
        print_warning("Some checks failed - review the setup")

def check_package(package_name: str) -> bool:
    """Check if Python package is installed"""
    try:
        __import__(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False

def check_redis_connection() -> bool:
    """Check Redis connection"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        return True
    except:
        return False

def create_example_integration():
    """Create example integration code"""
    print_header("Creating Example Integration")
    
    example_code = '''"""
Example API Integration Usage
Run this script to test the Google Sheets integration
"""

import asyncio
from app.services.google_sheets_service import google_sheets_service

async def test_integration():
    """Test the API integration setup"""
    try:
        # Test Google Sheets service initialization
        metrics = google_sheets_service.get_metrics()
        print(f"Google Sheets service initialized: {metrics}")
        
        # Add more tests here
        print("✓ API Integration setup is working!")
        
    except Exception as e:
        print(f"✗ Setup test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration())
'''
    
    example_file = Path("test_api_integration.py")
    with open(example_file, 'w') as f:
        f.write(example_code)
    
    print_success("Created test_api_integration.py")
    print_info("Run: python test_api_integration.py to test the setup")

def main():
    """Main setup function"""
    print_header("Meta DevOps API Integration Setup")
    print_info("Setting up Google Sheets and Microsoft Graph integrations...")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Setup steps
        check_prerequisites()
        install_python_dependencies()
        install_frontend_dependencies()
        
        security_keys = generate_security_keys()
        setup_environment_file(security_keys)
        setup_oauth_applications()
        create_database_tables()
        setup_testing_framework()
        create_example_integration()
        
        validate_setup()
        
        print_header("Setup Complete!")
        print_success("API Integration Hub is ready!")
        print_info("Next steps:")
        print("1. Configure OAuth2 credentials in .env file")
        print("2. Run database migrations: python manage.py migrate")
        print("3. Start the development server: python main.py")
        print("4. Test integrations: python test_api_integration.py")
        
    except KeyboardInterrupt:
        print_error("Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
