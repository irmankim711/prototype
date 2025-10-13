# Environment Configuration Setup

This document explains how to set up and use the environment configuration system for the React frontend.

## Overview

The environment configuration system provides:
- Type-safe access to environment variables
- Environment-specific configurations
- Validation of required variables
- Centralized configuration management

## File Structure

```
frontend/
├── env.development              # Development environment variables
├── env.production.template      # Production environment template
├── src/
│   └── config/
│       └── environment.ts      # Environment configuration and validation
└── ENVIRONMENT_SETUP_README.md  # This file
```

## Environment Files

### Development Environment (`env.development`)

Contains development-specific variables:
- Local API endpoints
- Development feature flags
- Debug mode enabled
- Development OAuth credentials

### Production Environment Template (`env.production.template`)

Template for production environment:
- Production API endpoints
- Production OAuth credentials
- Security features enabled
- Performance monitoring enabled

## Setup Instructions

### 1. Development Setup

1. Copy `env.development` to `.env.development`:
   ```bash
   cp env.development .env.development
   ```

2. Update the values in `.env.development` with your actual development credentials:
   ```bash
   # API Configuration
   VITE_API_URL=http://localhost:5000
   
   # OAuth Configuration
   VITE_GOOGLE_CLIENT_ID=your-actual-google-client-id
   VITE_MICROSOFT_CLIENT_ID=your-actual-microsoft-client-id
   ```

### 2. Production Setup

1. Copy `env.production.template` to `.env.production`:
   ```bash
   cp env.production.template .env.production
   ```

2. Update the values in `.env.production` with your production credentials:
   ```bash
   # API Configuration
   VITE_API_URL=https://api.yourdomain.com
   
   # OAuth Configuration
   VITE_GOOGLE_CLIENT_ID=your-production-google-client-id
   VITE_MICROSOFT_CLIENT_ID=your-production-microsoft-client-id
   
   # External Services
   VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
   VITE_GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX-X
   ```

### 3. Environment-Specific Builds

The build system automatically detects the environment:

```bash
# Development build
npm run build:dev

# Production build
npm run build:prod

# Staging build
npm run build:staging
```

## Environment Variables

### Required Variables

These variables must be set in all environments:

```bash
VITE_API_URL=           # Backend API endpoint
VITE_GOOGLE_CLIENT_ID=  # Google OAuth client ID
VITE_MICROSOFT_CLIENT_ID= # Microsoft OAuth client ID
VITE_APP_NAME=          # Application name
VITE_APP_VERSION=       # Application version
VITE_ENVIRONMENT=       # Environment (development/staging/production/test)
```

### Optional Variables

These variables have default values but can be customized:

```bash
# API Configuration
VITE_API_TIMEOUT=30000
VITE_MAX_RETRY_ATTEMPTS=3
VITE_RETRY_DELAY=1000
VITE_MAX_RETRY_DELAY=10000

# Feature Flags
VITE_ENABLE_AI_FEATURES=true
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_PWA=false
VITE_ENABLE_DEBUG_MODE=true

# Development Tools
VITE_ENABLE_HOT_RELOAD=true
VITE_ENABLE_SOURCE_MAPS=true
VITE_ENABLE_PERFORMANCE_MONITORING=false
```

## Usage in Code

### 1. Import Environment Configuration

```typescript
import { environmentConfig, environmentUtils } from '../config/environment';
```

### 2. Access Environment Variables

```typescript
// API Configuration
const apiUrl = environmentConfig.api.baseUrl;
const timeout = environmentConfig.api.timeout;

// Feature Flags
if (environmentConfig.features.ai) {
  // AI features are enabled
}

// OAuth Configuration
const googleClientId = environmentConfig.oauth.google.clientId;
```

### 3. Environment Checks

```typescript
// Check current environment
if (environmentUtils.isDev()) {
  console.log('Running in development mode');
}

if (environmentUtils.isProd()) {
  console.log('Running in production mode');
}

// Check feature availability
if (environmentUtils.isFeatureEnabled('ai')) {
  // AI features are available
}
```

### 4. API Service Integration

The API service automatically uses environment configuration:

```typescript
import apiService from '../services/apiService';

// The service automatically uses VITE_API_URL
const users = await apiService.get('/users');
```

## Validation

### Automatic Validation

Environment variables are automatically validated:
- Required variables must be present
- API URLs must have valid format
- Environment values must be valid
- Numeric values must be valid numbers

### Manual Validation

You can manually validate the environment:

```typescript
import { environmentUtils } from '../config/environment';

const isValid = environmentUtils.validate();
if (!isValid) {
  console.error('Environment validation failed');
}
```

## Security Considerations

### 1. Never Commit Sensitive Data

- `.env.production` should be in `.gitignore`
- Only commit template files
- Use environment-specific credentials

### 2. OAuth Credentials

- Use different client IDs for each environment
- Never expose production credentials in development
- Rotate credentials regularly

### 3. API Endpoints

- Use HTTPS in production
- Validate API URLs
- Use environment-specific endpoints

## Troubleshooting

### Common Issues

1. **Environment Variable Not Found**
   ```
   Error: Environment variable VITE_API_URL is required but not set
   ```
   Solution: Check that the variable is set in your `.env` file

2. **Invalid API URL Format**
   ```
   Error: Invalid API URL format: localhost:5000
   ```
   Solution: Ensure URLs start with `http://` or `https://`

3. **Invalid Environment Value**
   ```
   Error: Invalid environment value: dev
   ```
   Solution: Use one of: `development`, `staging`, `production`, `test`

### Debug Mode

Enable debug mode to see environment configuration:

```typescript
if (environmentConfig.features.debug) {
  console.log('Environment Config:', environmentConfig);
  console.log('Environment Utils:', environmentUtils);
}
```

## Best Practices

### 1. Environment-Specific Configs

- Use different configurations for each environment
- Never hardcode URLs or credentials
- Use feature flags for environment-specific features

### 2. Validation

- Always validate environment on startup
- Provide meaningful error messages
- Use TypeScript for type safety

### 3. Documentation

- Keep environment files up to date
- Document all environment variables
- Provide examples for each environment

### 4. Security

- Use environment-specific credentials
- Never expose production credentials
- Validate all environment variables

## Examples

### Development Environment

```bash
# .env.development
VITE_API_URL=http://localhost:5000
VITE_GOOGLE_CLIENT_ID=dev-client-id.apps.googleusercontent.com
VITE_MICROSOFT_CLIENT_ID=dev-microsoft-client-id
VITE_ENVIRONMENT=development
VITE_ENABLE_DEBUG_MODE=true
```

### Production Environment

```bash
# .env.production
VITE_API_URL=https://api.yourdomain.com
VITE_GOOGLE_CLIENT_ID=prod-client-id.apps.googleusercontent.com
VITE_MICROSOFT_CLIENT_ID=prod-microsoft-client-id
VITE_ENVIRONMENT=production
VITE_ENABLE_DEBUG_MODE=false
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

## Support

For questions or issues with environment configuration:

1. Check this documentation first
2. Verify environment variables are set correctly
3. Check console for validation errors
4. Review the environment configuration file
5. Contact the development team for complex issues
