# API Service Layer Documentation

## Overview

This document describes the comprehensive API service layer that replaces the hardcoded localhost URLs with a robust, environment-based configuration system.

## Features

### ✅ Implemented Requirements

1. **ApiService Class with TypeScript Interfaces** - Complete implementation with proper typing
2. **Environment-based API URL Configuration** - Supports development, staging, production, and test environments
3. **JWT Token Management** - Get, set, refresh, clear, and expiry checking
4. **Request/Response Interceptors** - Automatic authentication and error handling
5. **Proper Error Handling** - User-friendly error messages with standardized error types
6. **Retry Logic with Exponential Backoff** - Configurable retry for failed requests
7. **Request Timeout Configuration** - Environment-specific timeout settings
8. **Typed Interfaces** - Complete TypeScript interfaces for all API responses
9. **Loading States Management** - Track loading states for individual requests

## Architecture

### File Structure

```
frontend/src/
├── services/
│   ├── apiService.ts          # Main ApiService class
│   └── api.ts                 # Updated legacy API functions
└── types/
    └── api.types.ts           # Complete type definitions
```

### Core Components

#### 1. ApiService Class (`apiService.ts`)

The main service class that handles:
- HTTP requests with automatic retry logic
- JWT token management and refresh
- Request/response interceptors
- Loading state management
- Environment-based configuration

#### 2. Type Definitions (`api.types.ts`)

Comprehensive TypeScript interfaces for:
- API configuration and environment settings
- JWT tokens and authentication
- Request/response types
- Error handling
- Loading states
- All domain models (User, Report, Form, etc.)

#### 3. Legacy API Functions (`api.ts`)

Updated to use the new ApiService while maintaining backward compatibility.

## Usage Examples

### Basic Usage

```typescript
import apiService from '../services/apiService';

// GET request
const users = await apiService.get<User[]>('/users');

// POST request
const newUser = await apiService.post<User>('/users', userData);

// PUT request
const updatedUser = await apiService.put<User>(`/users/${id}`, updateData);

// DELETE request
await apiService.delete(`/users/${id}`);
```

### Authentication

```typescript
// Login
const loginResponse = await apiService.login({
  email: 'user@example.com',
  password: 'password123'
});

// Check authentication status
if (apiService.isAuthenticated()) {
  // User is logged in
}

// Get current user
const user = await apiService.getCurrentUser();

// Logout
await apiService.logout();
```

### Configuration

```typescript
// Set custom base URL
apiService.setBaseURL('https://api.example.com');

// Set custom timeout
apiService.setRequestTimeout(60000);

// Get current configuration
const baseURL = apiService.getBaseURL();
```

### Error Handling

```typescript
try {
  const data = await apiService.get('/protected-endpoint');
} catch (error) {
  if (error.code === 'AUTHENTICATION_REQUIRED') {
    // Handle authentication error
  } else if (error.code === 'TOKEN_REFRESH_FAILED') {
    // Handle token refresh failure
  } else {
    // Handle other errors
    console.error('API Error:', error.message);
  }
}
```

### Loading States

```typescript
// Get loading state for a specific request
const loadingState = apiService.getLoadingState('request-id');

if (loadingState?.isLoading) {
  // Show loading indicator
}

if (loadingState?.error) {
  // Show error message
}

// Clear loading state when done
apiService.clearLoadingState('request-id');
```

## Environment Configuration

### Environment Variables

Create a `.env` file in the frontend directory:

```bash
# Development
REACT_APP_API_URL=http://localhost:5000
REACT_APP_ENVIRONMENT=development

# Production
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENVIRONMENT=production

# Staging
REACT_APP_STAGING_API_URL=https://staging-api.yourdomain.com
REACT_APP_ENVIRONMENT=staging
```

### Environment-Specific Settings

The ApiService automatically configures:
- **Development**: 30s timeout, 3 retry attempts
- **Production**: 60s timeout, 5 retry attempts  
- **Staging**: 45s timeout, 4 retry attempts
- **Test**: 10s timeout, 1 retry attempt

## Retry Logic

### Configuration

```typescript
const retryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,        // 1 second
  maxDelay: 10000,        // 10 seconds
  backoffMultiplier: 2,   // Exponential backoff
  retryableStatusCodes: [408, 429, 500, 502, 503, 504]
};
```

### Retryable Status Codes

- `408` - Request Timeout
- `429` - Too Many Requests
- `500` - Internal Server Error
- `502` - Bad Gateway
- `503` - Service Unavailable
- `504` - Gateway Timeout

## Error Handling

### Standardized Error Types

```typescript
interface ApiError {
  message: string;           // User-friendly message
  code: string;              // Error code for programmatic handling
  status: number;            // HTTP status code
  details?: Record<string, any>; // Additional error details
  timestamp: string;         // When the error occurred
  requestId?: string;        // Request ID for tracking
}
```

### User-Friendly Messages

The service automatically converts technical error messages to user-friendly ones:

- `400` → "Invalid request. Please check your input and try again."
- `401` → "Authentication required. Please log in again."
- `403` → "Access denied. You don't have permission to perform this action."
- `404` → "The requested resource was not found."
- `500` → "Server error. Please try again later."

## Migration Guide

### From Old API Functions

**Before:**
```typescript
import { api } from '../services/api';

const { data } = await api.get('/users');
return data;
```

**After:**
```typescript
import apiService from '../services/apiService';

const users = await apiService.get<User[]>('/users');
return users;
```

### Benefits of Migration

1. **Type Safety**: Full TypeScript support with generic types
2. **Error Handling**: Standardized error handling with user-friendly messages
3. **Retry Logic**: Automatic retry for failed requests
4. **Token Management**: Automatic JWT refresh and management
5. **Loading States**: Built-in loading state management
6. **Environment Support**: Easy configuration for different environments

## Testing

### Unit Tests

```typescript
import { ApiService } from '../services/apiService';

describe('ApiService', () => {
  let apiService: ApiService;

  beforeEach(() => {
    apiService = new ApiService('test');
  });

  it('should handle authentication correctly', async () => {
    // Test implementation
  });
});
```

### Mocking

```typescript
// Mock the ApiService for testing
jest.mock('../services/apiService', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    login: jest.fn(),
    // ... other methods
  }
}));
```

## Performance Considerations

### Request Deduplication

The service automatically handles duplicate requests and prevents unnecessary API calls.

### Caching

Consider implementing caching for frequently accessed data:

```typescript
// Example caching implementation
const cache = new Map<string, { data: any; timestamp: number }>();

const getCachedData = async (key: string, ttl: number = 5 * 60 * 1000) => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data;
  }
  
  const data = await apiService.get(key);
  cache.set(key, { data, timestamp: Date.now() });
  return data;
};
```

## Security Features

### JWT Token Security

- Automatic token refresh before expiry
- Secure token storage in localStorage
- Token validation and expiry checking
- Automatic logout on token refresh failure

### Request Security

- Automatic Authorization header injection
- Request ID tracking for audit logs
- CSRF protection with withCredentials
- Secure error handling (no sensitive data exposure)

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure backend allows requests from frontend origin
2. **Token Refresh Loops**: Check refresh token endpoint implementation
3. **Timeout Issues**: Adjust timeout settings for slow networks
4. **Retry Failures**: Verify retryable status codes configuration

### Debug Mode

Enable debug logging:

```typescript
// In development, you can enable debug mode
if (process.env.NODE_ENV === 'development') {
  console.log('API Service Debug:', {
    baseURL: apiService.getBaseURL(),
    isAuthenticated: apiService.isAuthenticated(),
    tokenExpiry: apiService.getTokenExpiry()
  });
}
```

## Future Enhancements

### Planned Features

1. **Request/Response Caching**: Redis-like caching for API responses
2. **Request Queuing**: Queue management for rate-limited APIs
3. **WebSocket Support**: Real-time communication capabilities
4. **Offline Support**: Offline request queuing and sync
5. **Performance Monitoring**: Request timing and performance metrics

### Contributing

When adding new features to the API service:

1. Update the `IApiService` interface
2. Add corresponding types to `api.types.ts`
3. Implement the feature in the `ApiService` class
4. Add comprehensive tests
5. Update this documentation

## Support

For questions or issues with the API service:

1. Check this documentation first
2. Review the TypeScript interfaces for type information
3. Check the console for error details
4. Review the network tab for request/response details
5. Contact the development team for complex issues
