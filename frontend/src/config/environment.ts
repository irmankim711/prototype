/**
 * Environment Configuration
 * This file provides typed access to environment variables and validates their presence
 */

// Environment variable types
interface EnvironmentVariables {
  // API Configuration
  VITE_API_URL: string;
  VITE_API_TIMEOUT: number;
  VITE_MAX_RETRY_ATTEMPTS: number;
  VITE_RETRY_DELAY: number;
  VITE_MAX_RETRY_DELAY: number;

  // OAuth Configuration
  VITE_GOOGLE_CLIENT_ID?: string;
  VITE_MICROSOFT_CLIENT_ID?: string;

  // Feature Flags
  VITE_ENABLE_AI_FEATURES: boolean;
  VITE_ENABLE_ANALYTICS: boolean;
  VITE_ENABLE_PWA: boolean;
  VITE_ENABLE_DEBUG_MODE: boolean;
  VITE_ENABLE_AUTH_BYPASS: boolean;

  // Application Configuration
  VITE_APP_NAME?: string;
  VITE_APP_VERSION?: string;
  VITE_ENVIRONMENT: 'development' | 'staging' | 'production' | 'test';

  // Development Authentication Bypass
  VITE_DEV_USER_ID: string;
  VITE_DEV_USER_EMAIL: string;
  VITE_DEV_USER_ROLE: string;

  // External Services
  VITE_SENTRY_DSN?: string;
  VITE_GOOGLE_ANALYTICS_ID?: string;
  VITE_MIXPANEL_TOKEN?: string;

  // Development Tools
  VITE_ENABLE_HOT_RELOAD: boolean;
  VITE_ENABLE_SOURCE_MAPS: boolean;
  VITE_ENABLE_PERFORMANCE_MONITORING: boolean;

  // Security
  VITE_ENABLE_HTTPS_ONLY: boolean;
  VITE_ENABLE_CONTENT_SECURITY_POLICY: boolean;
  VITE_ENABLE_HSTS: boolean;
}

/**
 * Get environment variable with type conversion
 */
function getEnvVar<T>(key: keyof EnvironmentVariables, defaultValue?: T): T {
  const value = import.meta.env[key];
  
  if (value === undefined) {
    if (defaultValue !== undefined) {
      return defaultValue;
    }
    throw new Error(`Environment variable ${key} is required but not set`);
  }

  // Type conversion based on expected type
  if (typeof defaultValue === 'boolean') {
    return (value === 'true' || value === '1') as T;
  }
  
  if (typeof defaultValue === 'number') {
    const num = parseInt(value, 10);
    if (isNaN(num)) {
      throw new Error(`Environment variable ${key} must be a valid number, got: ${value}`);
    }
    return num as T;
  }

  return value as T;
}

/**
 * Get optional environment variable (can return undefined)
 */
function getOptionalEnvVar<T>(key: keyof EnvironmentVariables): T | undefined {
  const value = import.meta.env[key];
  
  if (value === undefined || value === '') {
    return undefined;
  }

  // Type conversion based on expected type
  if (typeof value === 'string') {
    if (value === 'true' || value === 'false') {
      return (value === 'true') as T;
    }
    if (!isNaN(Number(value))) {
      return Number(value) as T;
    }
    return value as T;
  }

  return value as T;
}

/**
 * Validate required environment variables
 */
function validateEnvironment(): void {
  const requiredVars: (keyof EnvironmentVariables)[] = [
    'VITE_API_URL',
    'VITE_ENVIRONMENT'
  ];

  for (const varName of requiredVars) {
    if (!import.meta.env[varName]) {
      throw new Error(`Required environment variable ${varName} is not set`);
    }
  }

  // Validate API URL format
  const apiUrl = import.meta.env.VITE_API_URL;
  if (apiUrl && !/^https?:\/\/.+/.test(apiUrl)) {
    throw new Error(`Invalid API URL format: ${apiUrl}. Must start with http:// or https://`);
  }

  // Validate environment value
  const env = import.meta.env.VITE_ENVIRONMENT;
  if (env && !['development', 'staging', 'production', 'test'].includes(env)) {
    throw new Error(`Invalid environment value: ${env}. Must be one of: development, staging, production, test`);
  }
}

/**
 * Environment configuration object
 */
export const env: EnvironmentVariables = {
  // API Configuration
  VITE_API_URL: getEnvVar('VITE_API_URL', 'http://localhost:5000'),
  VITE_API_TIMEOUT: getEnvVar('VITE_API_TIMEOUT', 30000),
  VITE_MAX_RETRY_ATTEMPTS: getEnvVar('VITE_MAX_RETRY_ATTEMPTS', 3),
  VITE_RETRY_DELAY: getEnvVar('VITE_RETRY_DELAY', 1000),
  VITE_MAX_RETRY_DELAY: getEnvVar('VITE_MAX_RETRY_DELAY', 10000),

  // OAuth Configuration
  VITE_GOOGLE_CLIENT_ID: getOptionalEnvVar('VITE_GOOGLE_CLIENT_ID'),
  VITE_MICROSOFT_CLIENT_ID: getOptionalEnvVar('VITE_MICROSOFT_CLIENT_ID'),

  // Feature Flags
  VITE_ENABLE_AI_FEATURES: getEnvVar('VITE_ENABLE_AI_FEATURES', true),
  VITE_ENABLE_ANALYTICS: getEnvVar('VITE_ENABLE_ANALYTICS', false),
  VITE_ENABLE_PWA: getEnvVar('VITE_ENABLE_PWA', false),
  VITE_ENABLE_DEBUG_MODE: getEnvVar('VITE_ENABLE_DEBUG_MODE', true),
  VITE_ENABLE_AUTH_BYPASS: getEnvVar('VITE_ENABLE_AUTH_BYPASS', false),

  // Application Configuration
  VITE_APP_NAME: getEnvVar('VITE_APP_NAME', 'Excel Report Automation'),
  VITE_APP_VERSION: getOptionalEnvVar('VITE_APP_VERSION') || '1.0.0',
  VITE_ENVIRONMENT: getEnvVar('VITE_ENVIRONMENT', 'development'),

  // Development Authentication Bypass
  VITE_DEV_USER_ID: getEnvVar('VITE_DEV_USER_ID', '1234567890'),
  VITE_DEV_USER_EMAIL: getEnvVar('VITE_DEV_USER_EMAIL', 'dev@example.com'),
  VITE_DEV_USER_ROLE: getEnvVar('VITE_DEV_USER_ROLE', 'admin'),

  // External Services
  VITE_SENTRY_DSN: getOptionalEnvVar('VITE_SENTRY_DSN'),
  VITE_GOOGLE_ANALYTICS_ID: getOptionalEnvVar('VITE_GOOGLE_ANALYTICS_ID'),
  VITE_MIXPANEL_TOKEN: getOptionalEnvVar('VITE_MIXPANEL_TOKEN'),

  // Development Tools
  VITE_ENABLE_HOT_RELOAD: getEnvVar('VITE_ENABLE_HOT_RELOAD', true),
  VITE_ENABLE_SOURCE_MAPS: getEnvVar('VITE_ENABLE_SOURCE_MAPS', true),
  VITE_ENABLE_PERFORMANCE_MONITORING: getEnvVar('VITE_ENABLE_PERFORMANCE_MONITORING', false),

  // Security
  VITE_ENABLE_HTTPS_ONLY: getEnvVar('VITE_ENABLE_HTTPS_ONLY', false),
  VITE_ENABLE_CONTENT_SECURITY_POLICY: getEnvVar('VITE_ENABLE_CONTENT_SECURITY_POLICY', false),
  VITE_ENABLE_HSTS: getEnvVar('VITE_ENABLE_HSTS', false),
};

/**
 * Environment-specific configuration
 */
export const environmentConfig = {
  isDevelopment: env.VITE_ENVIRONMENT === 'development',
  isStaging: env.VITE_ENVIRONMENT === 'staging',
  isProduction: env.VITE_ENVIRONMENT === 'production',
  isTest: env.VITE_ENVIRONMENT === 'test',

  // API Configuration
  api: {
    baseUrl: env.VITE_API_URL,
    timeout: env.VITE_API_TIMEOUT,
    retry: {
      maxAttempts: env.VITE_MAX_RETRY_ATTEMPTS,
      delay: env.VITE_RETRY_DELAY,
      maxDelay: env.VITE_MAX_RETRY_DELAY,
    },
  },

  // OAuth Configuration
  oauth: {
    google: {
      clientId: env.VITE_GOOGLE_CLIENT_ID,
    },
    microsoft: {
      clientId: env.VITE_MICROSOFT_CLIENT_ID,
    },
  },

  // Feature Configuration
  features: {
    ai: env.VITE_ENABLE_AI_FEATURES,
    analytics: env.VITE_ENABLE_ANALYTICS,
    pwa: env.VITE_ENABLE_PWA,
    debug: env.VITE_ENABLE_DEBUG_MODE,
    authBypass: env.VITE_ENABLE_AUTH_BYPASS,
  },

  // Development Authentication Configuration
  devAuth: {
    userId: env.VITE_DEV_USER_ID,
    userEmail: env.VITE_DEV_USER_EMAIL,
    userRole: env.VITE_DEV_USER_ROLE,
  },

  // Application Configuration
  app: {
    name: env.VITE_APP_NAME,
    version: env.VITE_APP_VERSION,
    environment: env.VITE_ENVIRONMENT,
  },

  // Development Configuration
  development: {
    hotReload: env.VITE_ENABLE_HOT_RELOAD,
    sourceMaps: env.VITE_ENABLE_SOURCE_MAPS,
    performanceMonitoring: env.VITE_ENABLE_PERFORMANCE_MONITORING,
  },

  // Security Configuration
  security: {
    httpsOnly: env.VITE_ENABLE_HTTPS_ONLY,
    contentSecurityPolicy: env.VITE_ENABLE_CONTENT_SECURITY_POLICY,
    hsts: env.VITE_ENABLE_HSTS,
  },
};

/**
 * Utility functions
 */
export const environmentUtils = {
  /**
   * Check if running in development mode
   */
  isDev: () => env.VITE_ENVIRONMENT === 'development',

  /**
   * Check if running in production mode
   */
  isProd: () => env.VITE_ENVIRONMENT === 'production',

  /**
   * Check if running in staging mode
   */
  isStaging: () => env.VITE_ENVIRONMENT === 'staging',

  /**
   * Check if running in test mode
   */
  isTest: () => env.VITE_ENVIRONMENT === 'test',

  /**
   * Get environment-specific API configuration
   */
  getApiConfig: () => environmentConfig.api,

  /**
   * Get feature flags
   */
  getFeatures: () => environmentConfig.features,

  /**
   * Check if a feature is enabled
   */
  isFeatureEnabled: (feature: keyof typeof environmentConfig.features) => 
    environmentConfig.features[feature],

  /**
   * Get OAuth configuration
   */
  getOAuthConfig: () => environmentConfig.oauth,

  /**
   * Validate environment on startup
   */
  validate: () => {
    try {
      validateEnvironment();
      return true;
    } catch (error) {
      console.error('Environment validation failed:', error);
      return false;
    }
  },
};

// Validate environment on module load
if (typeof window !== 'undefined') {
  // Only validate in browser environment
  environmentUtils.validate();
}

export default environmentConfig;
