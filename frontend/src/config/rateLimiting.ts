/**
 * Rate Limiting Configuration
 * Centralized configuration for API rate limiting to prevent 429 errors
 */

export const RATE_LIMITING_CONFIG = {
  // Global rate limits
  global: {
    maxRequestsPerMinute: 30,
    maxRequestsPerSecond: 2,
    burstLimit: 5, // Allow burst of 5 requests before throttling
  },

  // Endpoint-specific rate limits
  endpoints: {
    '/v1/nextgen/data-sources': {
      maxRequestsPerMinute: 20,
      maxRequestsPerSecond: 1,
      burstLimit: 3,
      cacheDuration: 2 * 60 * 1000, // 2 minutes
    },
    '/v1/nextgen/templates': {
      maxRequestsPerMinute: 15,
      maxRequestsPerSecond: 1,
      burstLimit: 2,
      cacheDuration: 5 * 60 * 1000, // 5 minutes
    },
    '/v1/nextgen/charts/generate': {
      maxRequestsPerMinute: 10,
      maxRequestsPerSecond: 0.5, // 1 request every 2 seconds
      burstLimit: 1,
      cacheDuration: 0, // No caching for dynamic content
    },
    '/v1/nextgen/ai/suggestions': {
      maxRequestsPerMinute: 20,
      maxRequestsPerSecond: 1,
      burstLimit: 3,
      cacheDuration: 1 * 60 * 1000, // 1 minute
    },
  },

  // Retry configuration
  retry: {
    maxRetries: 3,
    baseDelay: 2000, // 2 seconds
    maxDelay: 30000, // 30 seconds
    backoffMultiplier: 3, // Exponential backoff multiplier
  },

  // Cache configuration
  cache: {
    defaultTTL: 5 * 60 * 1000, // 5 minutes
    maxCacheSize: 100, // Maximum number of cached items
    cleanupInterval: 10 * 60 * 1000, // Clean up every 10 minutes
  },

  // Development overrides
  development: {
    bypassRateLimiting: false, // Set to true to bypass rate limiting in dev
    logAllRequests: true,
    aggressiveCaching: true,
  },
};

// Helper function to get endpoint-specific config
export function getEndpointConfig(endpoint: string) {
  const config = RATE_LIMITING_CONFIG.endpoints[endpoint];
  if (config) {
    return {
      ...RATE_LIMITING_CONFIG.global,
      ...config,
    };
  }
  return RATE_LIMITING_CONFIG.global;
}

// Helper function to check if rate limiting should be bypassed
export function shouldBypassRateLimiting(): boolean {
  return process.env.NODE_ENV === 'development' && 
         RATE_LIMITING_CONFIG.development.bypassRateLimiting;
}

// Helper function to get cache duration for an endpoint
export function getCacheDuration(endpoint: string): number {
  const config = RATE_LIMITING_CONFIG.endpoints[endpoint];
  return config?.cacheDuration || RATE_LIMITING_CONFIG.cache.defaultTTL;
}
