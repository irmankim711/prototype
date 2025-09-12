#!/usr/bin/env python3
"""
Configuration Validation Script

This script validates the environment configuration to ensure all required
variables are set and have appropriate values for the current environment.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def load_environment_file(env_file):
    """Load environment variables from a file"""
    if Path(env_file).exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
        return True
    else:
        print(f"⚠️  Environment file {env_file} not found")
        return False

def validate_required_variables(environment):
    """Validate required environment variables for the given environment"""
    errors = []
    warnings = []
    
    # Core required variables for all environments
    core_vars = {
        'FLASK_ENV': 'Flask environment',
        'ENVIRONMENT': 'Application environment',
    }
    
    # Production-specific required variables
    production_vars = {
        'SECRET_KEY': 'Secret key',
        'JWT_SECRET_KEY': 'JWT secret key',
        'DATABASE_URL': 'Database URL',
        'CORS_ORIGINS': 'CORS origins',
    }
    
    # Check core variables
    for var, description in core_vars.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing {description}: {var}")
        elif environment == 'production' and value == 'development':
            warnings.append(f"Warning: {var} is set to 'development' in production environment")
    
    # Check production variables
    if environment == 'production':
        for var, description in production_vars.items():
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing {description}: {var}")
            elif var in ['SECRET_KEY', 'JWT_SECRET_KEY'] and value.startswith(('dev-', 'jwt-')):
                errors.append(f"Production {description} cannot use default value: {var}")
            elif var == 'CORS_ORIGINS' and value == '*':
                warnings.append(f"Warning: {var} is set to '*' in production (security risk)")
    
    return errors, warnings

def validate_database_config():
    """Validate database configuration"""
    errors = []
    warnings = []
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return errors, warnings
    
    # Check database URL format
    if not database_url.startswith(('sqlite:///', 'postgresql://', 'mysql://')):
        errors.append("Invalid DATABASE_URL format. Must start with sqlite:///, postgresql://, or mysql://")
    
    # Check connection pool settings
    pool_size = os.getenv('DB_POOL_SIZE', '10')
    try:
        pool_size_int = int(pool_size)
        if pool_size_int < 1 or pool_size_int > 100:
            warnings.append(f"DB_POOL_SIZE ({pool_size}) should be between 1 and 100")
    except ValueError:
        errors.append(f"Invalid DB_POOL_SIZE: {pool_size}")
    
    return errors, warnings

def validate_cors_config():
    """Validate CORS configuration"""
    errors = []
    warnings = []
    
    cors_origins = os.getenv('CORS_ORIGINS')
    if not cors_origins:
        return errors, warnings
    
    # Check if origins are properly formatted
    origins = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    if not origins:
        errors.append("CORS_ORIGINS is empty or contains only whitespace")
    
    # Check for wildcard in production
    environment = os.getenv('ENVIRONMENT', 'development')
    if environment == 'production' and '*' in origins:
        warnings.append("Warning: CORS_ORIGINS contains wildcard (*) in production environment")
    
    # Validate URL format
    for origin in origins:
        if origin != '*' and not (origin.startswith('http://') or origin.startswith('https://')):
            warnings.append(f"Warning: CORS origin may not be properly formatted: {origin}")
    
    return errors, warnings

def validate_security_config():
    """Validate security configuration"""
    errors = []
    warnings = []
    
    # Check secret key strength
    secret_key = os.getenv('SECRET_KEY', '')
    if secret_key and len(secret_key) < 32:
        warnings.append("SECRET_KEY should be at least 32 characters long for production")
    
    jwt_secret_key = os.getenv('JWT_SECRET_KEY', '')
    if jwt_secret_key and len(jwt_secret_key) < 32:
        warnings.append("JWT_SECRET_KEY should be at least 32 characters long for production")
    
    # Check JWT expiration times
    access_expires = os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600')
    try:
        access_expires_int = int(access_expires)
        if access_expires_int < 300:  # 5 minutes
            warnings.append("JWT_ACCESS_TOKEN_EXPIRES is very short (< 5 minutes)")
        elif access_expires_int > 86400:  # 24 hours
            warnings.append("JWT_ACCESS_TOKEN_EXPIRES is very long (> 24 hours)")
    except ValueError:
        errors.append(f"Invalid JWT_ACCESS_TOKEN_EXPIRES: {access_expires}")
    
    return errors, warnings

def validate_redis_config():
    """Validate Redis configuration"""
    errors = []
    warnings = []
    
    redis_url = os.getenv('REDIS_URL', '')
    if redis_url and not redis_url.startswith('redis://'):
        errors.append("Invalid REDIS_URL format. Must start with redis://")
    
    celery_broker = os.getenv('CELERY_BROKER_URL', '')
    if celery_broker and not celery_broker.startswith('redis://'):
        warnings.append("CELERY_BROKER_URL should use Redis for production")
    
    return errors, warnings

def main():
    """Main validation function"""
    print("🔍 Flask Application Configuration Validator")
    print("=" * 50)
    
    # Determine which environment file to load
    env_file = None
    if len(sys.argv) > 1:
        env_file = sys.argv[1]
    else:
        # Try to auto-detect environment file
        environment = os.getenv('FLASK_ENV', 'development')
        if environment == 'production':
            env_file = '.env.production'
        else:
            env_file = '.env.development'
    
    # Load environment file if specified
    if env_file:
        load_environment_file(env_file)
    
    # Get current environment
    environment = os.getenv('ENVIRONMENT', os.getenv('FLASK_ENV', 'development'))
    print(f"🌍 Validating configuration for environment: {environment}")
    print()
    
    # Run validations
    all_errors = []
    all_warnings = []
    
    # Validate required variables
    errors, warnings = validate_required_variables(environment)
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    # Validate database configuration
    errors, warnings = validate_database_config()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    # Validate CORS configuration
    errors, warnings = validate_cors_config()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    # Validate security configuration
    errors, warnings = validate_security_config()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    # Validate Redis configuration
    errors, warnings = validate_redis_config()
    all_errors.extend(errors)
    all_warnings.extend(warnings)
    
    # Display results
    if all_warnings:
        print("⚠️  Warnings:")
        for warning in all_warnings:
            print(f"   • {warning}")
        print()
    
    if all_errors:
        print("❌ Errors:")
        for error in all_errors:
            print(f"   • {error}")
        print()
        print("Configuration validation failed! Please fix the errors above.")
        return 1
    
    if all_warnings:
        print("⚠️  Configuration has warnings but will work. Consider addressing them for production.")
        return 0
    
    print("✅ Configuration validation passed!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
