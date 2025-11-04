/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Token Management Utilities
 * 
 * This file provides utility functions for JWT token management,
 * including validation, expiration checking, and secure handling.
 */

export interface TokenPayload {
  sub?: string | number;
  
user_id?: string | number;
  
email?: string;
  
username?: string;
  
role?: string;
  
exp: number;
  
iat: number;
  
token_type?: string;
  [key: string]: any;
}

export interface TokenInfo {
  token: string;
  
expiresAt: number;
  
issuedAt: number;
  
timeUntilExpiration: number | null;
}

/**
 * Decode JWT token without verification
 * Note: This is for client-side use only, not for security validation
 */
export const decodeJWT = (token: string): TokenPayload | null => {
  try {
    if (!token || typeof token !== 'string') {
      return null;
    }

    const parts = token.split('.');
    
if (parts.length !== 3) {
      console.error('Invalid JWT format');
      
return null;
    }

    const payload = parts[1];
    
const decoded = JSON.parse(atob(payload));

return decoded;
  } catch (error) {
    console.error('Failed to decode JWT token:', error);
    
return null;
  }
};

/**
 * Check if a JWT token is expired
 */
export const isTokenExpired = (token: string): boolean => {
  try {
    const decoded = decodeJWT(token);
    
if (!decoded || !decoded.exp) return true;

const currentTime = Math.floor(Date.now() / 1000);
    
return decoded.exp <= currentTime;
  } catch (error) {
    console.error('Error checking token expiration:', error);
    
return true;
  }
};

/**
 * Get token expiration time in milliseconds
 */
export const getTokenExpirationTime = (token: string): number | null => {
  try {
    const decoded = decodeJWT(token);
    
return decoded?.exp ? decoded.exp * 1000 : null; // Convert to milliseconds
  } catch (error) {
    console.error('Error getting token expiration time:', error);
    
return null;
  }
};

/**
 * Get token issued time in milliseconds
 */
export const getTokenIssuedTime = (token: string): number | null => {
  try {
    const decoded = decodeJWT(token);
    
return decoded?.iat ? decoded.iat * 1000 : null; // Convert to milliseconds
  } catch (error) {
    console.error('Error getting token issued time:', error);
    
return null;
  }
};

/**
 * Calculate time until token expiration in seconds
 */
export const calculateTimeUntilExpiration = (token: string): number | null => {
  const expirationTime = getTokenExpirationTime(token);
  
if (!expirationTime) return null;

const currentTime = Date.now();
  
const timeUntilExpiration = Math.floor((expirationTime - currentTime) / 1000);

return timeUntilExpiration > 0 ? timeUntilExpiration : null;
};

/**
 * Check if token should be refreshed soon (within specified threshold)
 */
export const shouldRefreshToken = (token: string, thresholdMinutes: number = 5): boolean => {
  const timeUntilExpiration = calculateTimeUntilExpiration(token);
  
if (!timeUntilExpiration) return true;

const thresholdSeconds = thresholdMinutes * 60;
  
return timeUntilExpiration <= thresholdSeconds;
};

/**
 * Get comprehensive token information
 */
export const getTokenInfo = (token: string): TokenInfo | null => {
  try {
    const decoded = decodeJWT(token);
    
if (!decoded) return null;

const expiresAt = getTokenExpirationTime(token) || 0;
    
const issuedAt = getTokenIssuedTime(token) || 0;
    
const timeUntilExpiration = calculateTimeUntilExpiration(token);

return {
      token,
      expiresAt,
      issuedAt,
      timeUntilExpiration
    };
  } catch (error) {
    console.error('Error getting token info:', error);
    
return null;
  }
};

/**
 * Format time until expiration for display
 */
export const formatTimeUntilExpiration = (seconds: number): string => {
  if (seconds <= 0) return 'Expired';

const hours = Math.floor(seconds / 3600);
  
const minutes = Math.floor((seconds % 3600) / 60);
  
const remainingSeconds = seconds % 60;

if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${remainingSeconds}s`;
  }
};

/**
 * Validate token format and basic structure
 */
export const isValidTokenFormat = (token: string): boolean => {
  try {
    if (!token || typeof token !== 'string') return false;

const parts = token.split('.');
    
if (parts.length !== 3) return false;
    
    // Check if payload can be decoded
    const decoded = decodeJWT(token);
    
if (!decoded) return false;
    
    // Check for required fields
    if (!decoded.exp || !decoded.iat) return false;

return true;
  } catch {
    return false;
  }
};

/**
 * Get user ID from token
 */
export const getUserIdFromToken = (token: string): string | number | null => {
  try {
    const decoded = decodeJWT(token);
    
if (!decoded) return null;
    
    // Try different possible user ID fields
    return decoded.sub || decoded.user_id || null;
  } catch (error) {
    console.error('Error getting user ID from token:', error);
    
return null;
  }
};

/**
 * Get user role from token
 */
export const getUserRoleFromToken = (token: string): string | null => {
  try {
    const decoded = decodeJWT(token);
    
return decoded?.role || null;
  } catch (error) {
    console.error('Error getting user role from token:', error);
    
return null;
  }
};

/**
 * Check if token has specific claim/field
 */
export const hasTokenClaim = (token: string, claim: string): boolean => {
  try {
    const decoded = decodeJWT(token);

return decoded ? Object.prototype.hasOwnProperty.call(decoded, claim) : false;
  } catch {
    return false;
  }
};

/**
 * Get token claim value
 */
export const getTokenClaim = (token: string, claim: string): any => {
  try {
    const decoded = decodeJWT(token);
    
return decoded?.[claim] || null;
  } catch (error) {
    console.error(`Error getting token claim '${claim}':`, error);
    
return null;
  }
};

/**
 * Clear all authentication-related data from localStorage
 * CRITICAL FIX: Also clears Firebase SDK's internal auth state keys
 */
export const clearAllAuthData = (): void => {
  // Standard auth keys
  const authKeys = [
    'accessToken',
    'refreshToken',
    'tokenExpiry',
    'userData',
    'devBypassEnabled',
    'devUser',
    'token',
    'quickAccessToken',
    'firebaseToken'  // Custom Firebase token storage
  ];

  authKeys.forEach(key => {
    localStorage.removeItem(key);
  });

  // CRITICAL: Clear Firebase SDK's internal auth state keys
  // Firebase stores auth state with pattern: firebase:authUser:[apiKey]:[authDomain]
  const firebaseKeysToRemove: string[] = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && (
      key.startsWith('firebase:authUser') ||
      key.startsWith('firebase:host') ||
      key.startsWith('firebase:')
    )) {
      firebaseKeysToRemove.push(key);
    }
  }

  // Remove Firebase keys (done separately to avoid iteration issues)
  firebaseKeysToRemove.forEach(key => {
    localStorage.removeItem(key);
    console.log(`🧹 Removed Firebase SDK key: ${key}`);
  });

  console.log('🧹 All authentication data cleared (including Firebase SDK internal state)');
};

/**
 * Get all stored authentication keys
 */
export const getStoredAuthKeys = (): string[] => {
  const authKeys = [
    'accessToken',
    'refreshToken',
    'tokenExpiry',
    'userData',
    'devBypassEnabled',
    'devUser',
    'token',
    'quickAccessToken',
    'firebaseToken'
  ];

return authKeys.filter(key => localStorage.getItem(key) !== null);
};

/**
 * Check if any authentication data exists
 */
export const hasStoredAuthData = (): boolean => {
  return getStoredAuthKeys().length > 0;
};

/**
 * Log token information for debugging (development only)
 */
export const logTokenInfo = (token: string, label: string = 'Token'): void => {
  if (process.env.NODE_ENV === 'development') {
    const info = getTokenInfo(token);
    
if (info) {
      console.log(`🔍 ${label} Info:`, {
        expiresIn: formatTimeUntilExpiration(info.timeUntilExpiration || 0),
        issuedAt: new Date(info.issuedAt).toISOString(),
        expiresAt: new Date(info.expiresAt).toISOString(),
        shouldRefresh: shouldRefreshToken(token),
        userId: getUserIdFromToken(token),
        role: getUserRoleFromToken(token)
      });
    }
  }
};
