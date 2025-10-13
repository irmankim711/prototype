#!/usr/bin/env python3
"""
Secure Production Key Generation Script
======================================

This script generates cryptographically secure secret keys for production deployment.
It creates SECRET_KEY and JWT_SECRET_KEY using the secrets module for maximum security.

Usage:
    python scripts/generate_production_keys.py

Output:
    - Generates secure keys and displays them
    - Creates .env.production file with generated keys
    - Creates .env.production.template for future deployments
"""

import secrets
import string
import os
import sys
from pathlib import Path
from datetime import datetime

def generate_secure_key(length=32):
    """
    Generate a cryptographically secure random key.
    
    Args:
        length (int): Length of the key in bytes
        
    Returns:
        str: URL-safe base64 encoded key
    """
    # Generate random bytes
    random_bytes = secrets.token_bytes(length)
    
    # Convert to URL-safe base64
    import base64
    key = base64.urlsafe_b64encode(random_bytes).decode('ascii')
    
    # Remove padding characters for cleaner URLs
    key = key.rstrip('=')
    
    return key

def generate_jwt_secret():
    """
    Generate a secure JWT secret key.
    
    Returns:
        str: 32-byte URL-safe JWT secret
    """
    return generate_secure_key(32)

def generate_flask_secret():
    """
    Generate a secure Flask secret key.
    
    Returns:
        str: 32-byte URL-safe Flask secret
    """
    return generate_secure_key(32)

def create_env_production(secret_key, jwt_secret):
    """
    Create .env.production file with generated keys.
    
    Args:
        secret_key (str): Generated Flask secret key
        jwt_secret (str): Generated JWT secret key
    """
    env_content = f"""# Production Environment Configuration
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
# WARNING: Keep this file secure and never commit it to version control!

# =============================================================================
# SECURITY KEYS (GENERATED AUTOMATICALLY - DO NOT MODIFY MANUALLY)
# =============================================================================
SECRET_KEY={secret_key}
JWT_SECRET_KEY={jwt_secret}

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================
FLASK_ENV=production
ENVIRONMENT=production
DEBUG=false
TESTING=false

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# PostgreSQL Database URL (replace with your actual database credentials)
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Database Connection Pool Settings
DB_POOL_SIZE=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=30

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
# Redis URL for Celery broker and result backend
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Redis Connection Settings
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# =============================================================================
# JWT CONFIGURATION
# =============================================================================
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
JWT_ALGORITHM=HS256

# =============================================================================
# CORS AND SECURITY
# =============================================================================
# Allowed origins for CORS (replace with your actual domains)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security headers
SECURE_HEADERS=true
STRICT_TRANSPORT_SECURITY=true
CONTENT_SECURITY_POLICY=true

# =============================================================================
# MONITORING AND LOGGING
# =============================================================================
# Sentry DSN for error monitoring (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Log level
LOG_LEVEL=INFO

# Application version
APP_VERSION=1.0.0

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
# SMTP settings for email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# =============================================================================
# FILE STORAGE
# =============================================================================
# File upload settings
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=txt,pdf,png,jpg,jpeg,gif,doc,docx,xls,xlsx

# =============================================================================
# RATE LIMITING
# =============================================================================
# Rate limiting configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=200 per day, 50 per hour
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================
# Celery worker settings
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500

# =============================================================================
# EXTERNAL SERVICES
# =============================================================================
# Google Forms API (if using)
GOOGLE_FORMS_API_KEY=your-google-api-key
GOOGLE_FORMS_CLIENT_ID=your-google-client-id
GOOGLE_FORMS_CLIENT_SECRET=your-google-client-secret

# =============================================================================
# BACKUP AND MAINTENANCE
# =============================================================================
# Backup settings
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_STORAGE_PATH=/backups

# Maintenance mode
MAINTENANCE_MODE=false
MAINTENANCE_MESSAGE=System is under maintenance. Please try again later.
"""
    
    # Create .env.production file
    env_file = Path('.env.production')
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created {env_file}")
    return env_content

def create_env_template():
    """
    Create .env.production.template file for future deployments.
    """
    template_content = """# Production Environment Template
# Copy this file to .env.production and fill in your actual values
# Generated on: {datetime}

# =============================================================================
# SECURITY KEYS (GENERATE NEW KEYS FOR EACH DEPLOYMENT)
# =============================================================================
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================
FLASK_ENV=production
ENVIRONMENT=production
DEBUG=false
TESTING=false

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
# PostgreSQL Database URL
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Database Connection Pool Settings
DB_POOL_SIZE=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
DB_MAX_OVERFLOW=30

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================
# Redis URL for Celery broker and result backend
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Redis Connection Settings
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# =============================================================================
# JWT CONFIGURATION
# =============================================================================
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
JWT_ALGORITHM=HS256

# =============================================================================
# CORS AND SECURITY
# =============================================================================
# Allowed origins for CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Security headers
SECURE_HEADERS=true
STRICT_TRANSPORT_SECURITY=true
CONTENT_SECURITY_POLICY=true

# =============================================================================
# MONITORING AND LOGGING
# =============================================================================
# Sentry DSN for error monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id

# Log level
LOG_LEVEL=INFO

# Application version
APP_VERSION=1.0.0

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================
# SMTP settings for email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# =============================================================================
# FILE STORAGE
# =============================================================================
# File upload settings
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=uploads
ALLOWED_EXTENSIONS=txt,pdf,png,jpg,jpeg,gif,doc,docx,xls,xlsx

# =============================================================================
# RATE LIMITING
# =============================================================================
# Rate limiting configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=200 per day, 50 per hour
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================
# Celery worker settings
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500

# =============================================================================
# EXTERNAL SERVICES
# =============================================================================
# Google Forms API (if using)
GOOGLE_FORMS_API_KEY=your-google-api-key
GOOGLE_FORMS_CLIENT_ID=your-google-client-id
GOOGLE_FORMS_CLIENT_SECRET=your-google-client-secret

# =============================================================================
# BACKUP AND MAINTENANCE
# =============================================================================
# Backup settings
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
BACKUP_STORAGE_PATH=/backups

# Maintenance mode
MAINTENANCE_MODE=false
MAINTENANCE_MESSAGE=System is under maintenance. Please try again later.
"""
    
    # Create .env.production.template file
    template_file = Path('.env.production.template')
    with open(template_file, 'w') as f:
        f.write(template_content.format(datetime=datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')))
    
    print(f"✅ Created {template_file}")

def main():
    """Main function to generate production keys and environment files."""
    print("🔐 Secure Production Key Generation")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path('backend').exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   Expected to find 'backend' directory")
        sys.exit(1)
    
    # Generate secure keys
    print("\n🔑 Generating cryptographically secure keys...")
    flask_secret = generate_flask_secret()
    jwt_secret = generate_jwt_secret()
    
    print(f"✅ Flask SECRET_KEY: {flask_secret}")
    print(f"✅ JWT_SECRET_KEY: {jwt_secret}")
    
    # Create environment files
    print("\n📝 Creating environment configuration files...")
    create_env_production(flask_secret, jwt_secret)
    create_env_template()
    
    # Security recommendations
    print("\n🔒 Security Recommendations:")
    print("   1. Keep .env.production secure and never commit it to version control")
    print("   2. Use different keys for each environment (staging, production)")
    print("   3. Rotate keys periodically (recommended: every 90 days)")
    print("   4. Use strong passwords for database and Redis connections")
    print("   5. Enable HTTPS in production")
    print("   6. Configure proper firewall rules")
    print("   7. Monitor logs for suspicious activity")
    
    # Next steps
    print("\n📋 Next Steps:")
    print("   1. Review and customize .env.production with your actual values")
    print("   2. Update database credentials and connection strings")
    print("   3. Configure Redis connection details")
    print("   4. Set up monitoring (Sentry, etc.)")
    print("   5. Test the configuration in a staging environment")
    print("   6. Deploy to production")
    
    print("\n🎉 Production key generation complete!")
    print("   Files created:")
    print("   - .env.production (with generated keys)")
    print("   - .env.production.template (for future deployments)")

if __name__ == "__main__":
    main()
