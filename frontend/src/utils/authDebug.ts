/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Authentication Debug Utilities
 * Comprehensive debugging tools for JWT authentication issues
 */

import {
  decodeJWT,
  isTokenExpired,
  calculateTimeUntilExpiration,
  clearAllAuthData,
  logTokenInfo
} from './tokenUtils';

interface AuthDebugInfo {
  hasAccessToken: boolean;
  
hasRefreshToken: boolean;
  
tokenValid: boolean;
  
tokenExpired: boolean;
  
tokenFormat: 'valid' | 'invalid' | 'missing';
  
expirationInfo: {
    expiresAt: string | null;
    
timeUntilExpiration: number | null,
    
isExpired: boolean,
  };
  
userInfo: {
    userId: string | number | null;
    
email: string | null,
    
role: string | null,
  };
  
cookieInfo: {
    hasCookies: boolean,
    
cookieNames: string[],
  };
  
recommendations: string[];
}

/**
 * Get comprehensive authentication debug information
 */
export function getAuthDebugInfo(): AuthDebugInfo {
  const accessToken = localStorage.getItem('accessToken');
  
const refreshToken = localStorage.getItem('refreshToken');

const debugInfo: AuthDebugInfo = {
    hasAccessToken: !!accessToken,
    hasRefreshToken: !!refreshToken,
    tokenValid: false,
    tokenExpired: false,
    tokenFormat: 'missing',
    expirationInfo: {
      expiresAt: null,
      timeUntilExpiration: null,
      isExpired: false
    },
    userInfo: {
      userId: null,
      email: null,
      role: null
    },
    cookieInfo: {
      hasCookies: document.cookie.length > 0,
      cookieNames: document.cookie.split(',').map(c => c.split('=')[0].trim()).filter(Boolean)
    },
    recommendations: []
  };

  // Analyze access token
  if (accessToken) {
    try {
      const payload = decodeJWT(accessToken);

if (payload) {
        debugInfo.tokenFormat = 'valid';
        
debugInfo.tokenValid = true;
        
debugInfo.tokenExpired = isTokenExpired(accessToken);
        
        // Expiration info
        if (payload.exp) {
          const expirationTime = new Date(payload.exp * 1000);
          
debugInfo.expirationInfo.expiresAt = expirationTime.toLocaleString();
          
debugInfo.expirationInfo.timeUntilExpiration = calculateTimeUntilExpiration(accessToken);
          
debugInfo.expirationInfo.isExpired = debugInfo.tokenExpired;
        }
        
        // User info
        debugInfo.userInfo.userId = payload.sub || payload.user_id || null;
        
debugInfo.userInfo.email = payload.email || null;
        
debugInfo.userInfo.role = payload.role || null;
      } else {
        debugInfo.tokenFormat = 'invalid';
        
debugInfo.recommendations.push('Access token has invalid format - clear and re-login');
      }
    } catch (error) {
      debugInfo.tokenFormat = 'invalid';
      
debugInfo.recommendations.push('Access token decode error - clear and re-login');
    }
  } else {
    debugInfo.recommendations.push('No access token found - user needs to login');
  }

  // Generate recommendations
  if (debugInfo.tokenExpired) {
    if (debugInfo.hasRefreshToken) {
      debugInfo.recommendations.push('Token expired but refresh token available - attempt token refresh');
    } else {
      debugInfo.recommendations.push('Token expired and no refresh token - user must re-login');
    }
  }

  if (!debugInfo.hasAccessToken && !debugInfo.hasRefreshToken) {
    debugInfo.recommendations.push('No authentication tokens found - user must login');
  }

  if (debugInfo.tokenFormat === 'invalid') {
    debugInfo.recommendations.push('Clear all authentication data and retry login');
  }

  return debugInfo;
}

/**
 * Log comprehensive authentication debug information
 */
export function logAuthDebugInfo(): AuthDebugInfo {
  const debugInfo = getAuthDebugInfo();

console.group('🔐 Authentication Debug Information');

console.log('📊 Token Status:', {
    hasAccessToken: debugInfo.hasAccessToken,
    hasRefreshToken: debugInfo.hasRefreshToken,
    tokenValid: debugInfo.tokenValid,
    tokenExpired: debugInfo.tokenExpired,
    tokenFormat: debugInfo.tokenFormat
  });

if (debugInfo.expirationInfo.expiresAt) {
    console.log('⏰ Expiration Info:', debugInfo.expirationInfo);
  }

  if (debugInfo.userInfo.userId) {
    console.log('👤 User Info:', debugInfo.userInfo);
  }

  console.log('🍪 Cookie Info:', debugInfo.cookieInfo);

if (debugInfo.recommendations.length > 0) {
    console.log('💡 Recommendations:');
    
debugInfo.recommendations.forEach((rec, index) => {
      console.log(`  ${index + 1}. ${rec}`);
    });
  }

  console.groupEnd();

return debugInfo;
}

/**
 * Test authentication with backend
 */
export async function testAuthWithBackend(apiUrl: string = 'http://localhost:5001'): Promise<{
  success: boolean;
  
error?: string;
  
status?: number;
  
response?: any;
}> {
  const accessToken = localStorage.getItem('accessToken');

if (!accessToken) {
    return { 
      success: false, 
      error: 'No access token available' 
    };
  }

  try {
    const response = await fetch(`${apiUrl}/api/v1/nextgen/data-sources`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });

const responseText = await response.text();
    
let responseData;

try {
      responseData = JSON.parse(responseText);
    } catch {
      responseData = { raw_response: responseText };
    }

    if (response.ok) {
      return { 
        success: true, 
        status: response.status,
        response: responseData 
      };
    } else {
      return { 
        success: false, 
        error: `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        response: responseData 
      };
    }
  } catch (error: any) {
    return { 
      success: false, 
      error: `Network error: ${error.message}` 
    };
  }
}

/**
 * Attempt to refresh authentication token
 */
export async function attemptTokenRefresh(apiUrl: string = 'http://localhost:5001'): Promise<{
  success: boolean;
  
error?: string;
  
newToken?: string;
}> {
  const refreshToken = localStorage.getItem('refreshToken');

if (!refreshToken) {
    return { 
      success: false, 
      error: 'No refresh token available' 
    };
  }

  try {
    console.log('🔄 Attempting token refresh...');

const response = await fetch(`${apiUrl}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refreshToken}`
      },
      credentials: 'include'
    });

const data = await response.json();

if (response.ok && data.access_token) {
      localStorage.setItem('accessToken', data.access_token);

if (data.refresh_token) {
        localStorage.setItem('refreshToken', data.refresh_token);
      }

      console.log('✅ Token refresh successful');
      
logTokenInfo(data.access_token, 'Refreshed Token');

return { 
        success: true, 
        newToken: data.access_token 
      };
    } else {
      console.error('❌ Token refresh failed:', data);
      
return { 
        success: false, 
        error: data.message || 'Token refresh failed' 
      };
    }
  } catch (error: any) {
    console.error('❌ Token refresh network error:', error);
    
return { 
      success: false, 
      error: `Network error: ${error.message}` 
    };
  }
}

/**
 * Comprehensive authentication fix attempt
 */
export async function fixAuthenticationIssues(apiUrl: string = 'http://localhost:5001'): Promise<{
  success: boolean;
  
action: string;
  
message: string;
  
debugInfo?: AuthDebugInfo;
}> {
  console.log('🔧 Starting comprehensive authentication fix...');

const debugInfo = logAuthDebugInfo();
  
  // Step 1: If no tokens at all, user must login
  if (!debugInfo.hasAccessToken && !debugInfo.hasRefreshToken) {
    return {
      success: false,
      action: 'login_required',
      message: 'No authentication tokens found. User must login.',
      debugInfo
    };
  }
  
  // Step 2: If token is invalid format, clear and require login
  if (debugInfo.tokenFormat === 'invalid') {
    clearAllAuthData();
    
return {
      success: false,
      action: 'cleared_invalid_tokens',
      message: 'Invalid token format detected. Cleared authentication data. User must re-login.',
      debugInfo
    };
  }
  
  // Step 3: If token is expired, attempt refresh
  if (debugInfo.tokenExpired && debugInfo.hasRefreshToken) {
    const refreshResult = await attemptTokenRefresh(apiUrl);

if (refreshResult.success) {
      return {
        success: true,
        action: 'token_refreshed',
        message: 'Successfully refreshed authentication token.',
        debugInfo
      };
    } else {
      // Refresh failed, clear tokens and require login
      clearAllAuthData();
      
return {
        success: false,
        action: 'refresh_failed_cleared',
        message: `Token refresh failed: ${refreshResult.error}. Cleared authentication data. User must re-login.`,
        debugInfo
      };
    }
  }
  
  // Step 4: If token appears valid, test with backend
  if (debugInfo.tokenValid && !debugInfo.tokenExpired) {
    const testResult = await testAuthWithBackend(apiUrl);

if (testResult.success) {
      return {
        success: true,
        action: 'auth_valid',
        message: 'Authentication is working correctly.',
        debugInfo
      };
    } else {
      // Backend rejected valid-looking token
      if (testResult.status === 401) {
        // Try refresh if available
        if (debugInfo.hasRefreshToken) {
          const refreshResult = await attemptTokenRefresh(apiUrl);
          
if (refreshResult.success) {
            return {
              success: true,
              action: 'token_refreshed_after_401',
              message: 'Backend rejected token but refresh was successful.',
              debugInfo
            };
          }
        }
        
        // No refresh available or refresh failed, clear and require login
        clearAllAuthData();
        
return {
          success: false,
          action: 'backend_rejected_cleared',
          message: `Backend rejected authentication (${testResult.error}). Cleared authentication data. User must re-login.`,
          debugInfo
        };
      } else {
        return {
          success: false,
          action: 'backend_error',
          message: `Backend error: ${testResult.error}. Authentication tokens appear valid.`,
          debugInfo
        };
      }
    }
  }
  
  // Fallback - unclear state
  return {
    success: false,
    action: 'unclear_state',
    message: 'Authentication state unclear. Recommend clearing tokens and re-login.',
    debugInfo
  };
}

/**
 * Quick auth status check for UI
 */
export function getQuickAuthStatus(): {
  isAuthenticated: boolean;
  
needsRefresh: boolean;
  
needsLogin: boolean;
  
tokenExpired: boolean;
  
status: 'valid' | 'expired' | 'missing' | 'invalid',
} {
  const debugInfo = getAuthDebugInfo();

return {
    isAuthenticated: debugInfo.tokenValid && !debugInfo.tokenExpired,
    needsRefresh: debugInfo.tokenExpired && debugInfo.hasRefreshToken,
    needsLogin: !debugInfo.hasAccessToken || (debugInfo.tokenExpired && !debugInfo.hasRefreshToken),
    tokenExpired: debugInfo.tokenExpired,
    status: !debugInfo.hasAccessToken ? 'missing' 
            : debugInfo.tokenFormat === 'invalid' ? 'invalid'
            : debugInfo.tokenExpired ? 'expired' 
            : 'valid'
  };
}

// Make functions available globally for debugging in console
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
  (window as any).authDebug = {
    getAuthDebugInfo,
    logAuthDebugInfo,
    testAuthWithBackend,
    attemptTokenRefresh,
    fixAuthenticationIssues,
    getQuickAuthStatus,
    clearAllAuthData
  };

console.log('🔧 Auth debug utilities available at window.authDebug');
}
