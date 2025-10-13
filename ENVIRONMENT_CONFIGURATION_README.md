# Environment Configuration Guide

This document explains how to configure the Flask application using environment variables instead of hardcoded values.

## Overview

The application has been updated to use environment variables for all configuration settings, eliminating hardcoded values and providing better security and flexibility across different environments.

## Quick Start

### 1. Development Environment

Copy the development template and customize as needed:

```bash
cp development.env .env.development
```

### 2. Production Environment

Copy the production template and fill in your actual values:

```bash
cp env.production.template .env.production
```

**⚠️ IMPORTANT: Never commit `.env.production` to version control!**

## Environment Variables Reference

### Core Environment Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FLASK_ENV` | Flask environment (development/production/testing) | development | No |
| `ENVIRONMENT` | Application environment | development | No |
| `DEBUG` | Enable debug mode | false | No |
| `TESTING` | Enable testing mode | false | No |

### Security Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key | dev-secret-key-change-in-production | **Yes** (production) |
| `JWT_SECRET_KEY` | JWT signing secret | jwt-secret-key-change-in-production | **Yes** (production) |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access token expiration (seconds) | 3600 | No |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh token expiration (seconds) | 2592000 | No |
| `JWT_COOKIE_CSRF_PROTECT` | Enable CSRF protection for JWT cookies | false | No |
| `JWT_ACCESS_COOKIE_NAME` | Access token cookie name | access_token_cookie | No |
| `JWT_REFRESH_COOKIE_NAME` | Refresh token cookie name | refresh_token_cookie | No |

### Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | sqlite:///app.db | **Yes** (production) |
| `DB_POOL_SIZE` | Connection pool size | 10 | No |
| `DB_POOL_TIMEOUT` | Connection timeout (seconds) | 20 | No |
| `DB_POOL_RECYCLE` | Connection recycle time (seconds) | 3600 | No |
| `DB_MAX_OVERFLOW` | Maximum overflow connections | 20 | No |

### Redis Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 | No |
| `REDIS_MAX_CONNECTIONS` | Maximum Redis connections | 20 | No |
| `REDIS_RETRY_ON_TIMEOUT` | Retry on timeout | true | No |
| `REDIS_HEALTH_CHECK_INTERVAL` | Health check interval (seconds) | 30 | No |

### CORS Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CORS_ORIGINS` | Allowed origins (comma-separated) | localhost URLs (dev) | **Yes** (production) |
| `CORS_METHODS` | Allowed HTTP methods | GET,POST,PUT,DELETE,OPTIONS | No |
| `CORS_ALLOW_HEADERS` | Allowed headers | Content-Type,Authorization,X-Requested-With | No |
| `CORS_EXPOSE_HEADERS` | Exposed headers | Content-Type,Authorization | No |
| `CORS_SUPPORTS_CREDENTIALS` | Support credentials | true | No |
| `CORS_MAX_AGE` | Preflight cache time (seconds) | 3600 | No |

### Celery Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CELERY_BROKER_URL` | Celery broker URL | redis://localhost:6379/0 | No |
| `CELERY_RESULT_BACKEND` | Celery result backend | redis://localhost:6379/0 | No |
| `CELERY_TASK_SERIALIZER` | Task serializer | json | No |
| `CELERY_RESULT_SERIALIZER` | Result serializer | json | No |
| `CELERY_TIMEZONE` | Celery timezone | UTC | No |
| `CELERY_TASK_TIME_LIMIT` | Task time limit (seconds) | 1800 | No |
| `CELERY_TASK_SOFT_TIME_LIMIT` | Soft time limit (seconds) | 1500 | No |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | Worker prefetch multiplier | 1 | No |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | Max tasks per worker | 1000 | No |

### Security Headers

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `STRICT_TRANSPORT_SECURITY` | Enable HSTS | false | No |
| `HSTS_MAX_AGE` | HSTS max age | max-age=31536000; includeSubDomains | No |
| `CONTENT_SECURITY_POLICY` | Enable CSP | false | No |
| `CSP_POLICY` | CSP policy string | default-src 'self'... | No |

### File Upload

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_CONTENT_LENGTH` | Maximum file size (bytes) | 16777216 (16MB) | No |
| `UPLOAD_FOLDER` | Upload directory | uploads | No |
| `ALLOWED_EXTENSIONS` | Allowed file extensions | txt,pdf,png,jpg,jpeg,gif,xlsx,csv | No |

### Monitoring and Logging

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SENTRY_DSN` | Sentry DSN for error monitoring | None | No |
| `LOG_LEVEL` | Log level | INFO | No |
| `APP_VERSION` | Application version | 1.0.0 | No |

## Environment-Specific Configuration

### Development Environment

The development environment automatically sets:
- Debug mode enabled
- SQLite database
- Localhost CORS origins
- Development secret keys
- Detailed logging

### Production Environment

The production environment requires:
- Explicit `SECRET_KEY` and `JWT_SECRET_KEY`
- Production database URL
- Explicit CORS origins
- Security headers enabled
- Proper monitoring configuration

## Configuration Validation

The application automatically validates configuration on startup:

1. **Production Environment Checks:**
   - Required secret keys are set and not default values
   - Database URL is properly formatted
   - CORS origins are explicitly configured

2. **Environment Variable Validation:**
   - Database URL format validation
   - Redis URL format validation
   - OAuth configuration validation

## Error Handling

If configuration validation fails, the application will:
1. Log detailed error messages
2. Raise a `ValueError` with specific issues
3. Prevent startup until issues are resolved

## Best Practices

### 1. Security
- Generate unique secret keys for each deployment
- Use strong, random passwords
- Never commit production credentials to version control

### 2. Environment Management
- Use separate environment files for different environments
- Validate configuration in staging before production
- Document all required variables

### 3. CORS Configuration
- In production, explicitly list allowed origins
- Avoid using wildcard (*) in production
- Test CORS configuration thoroughly

### 4. Database Configuration
- Use connection pooling for production databases
- Set appropriate timeouts and pool sizes
- Monitor database connection health

## Troubleshooting

### Common Issues

1. **Configuration Validation Failed**
   - Check that all required environment variables are set
   - Verify secret keys are not default values in production
   - Ensure CORS origins are properly configured

2. **CORS Errors**
   - Verify `CORS_ORIGINS` includes your frontend domain
   - Check that `CORS_SUPPORTS_CREDENTIALS` is set correctly
   - Ensure preflight requests are handled properly

3. **Database Connection Issues**
   - Verify `DATABASE_URL` format and credentials
   - Check database server accessibility
   - Validate connection pool settings

### Debug Mode

Enable debug mode to see detailed configuration information:

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## Migration from Hardcoded Values

If you're migrating from the previous hardcoded configuration:

1. Copy the appropriate environment template
2. Fill in your actual values
3. Remove any hardcoded configuration from your code
4. Test the application with the new configuration
5. Update your deployment scripts to use environment variables

## Support

For configuration issues:
1. Check the application logs for validation errors
2. Verify all required environment variables are set
3. Test configuration in a development environment first
4. Review the configuration validation output

## Security Notes

- **Never** use default secret keys in production
- **Always** validate configuration before deployment
- **Regularly** rotate production credentials
- **Monitor** application logs for configuration issues
- **Test** security headers and CORS in staging
