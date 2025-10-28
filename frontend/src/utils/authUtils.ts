/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Authentication utilities for robust token refresh and offline handling
 */

import { getAuth, onAuthStateChanged } from "firebase/auth";
// Use the actual Firebase auth instance instead of importing User type
import { auth } from "../config/firebase";

export interface AuthState {
  user: any; // Firebase user object - avoid type import issues
  isLoading: boolean;
  
error: string | null;
  
isOnline: boolean;
  
lastTokenRefresh: number | null;
}

export class AuthTokenManager {
  private static instance: AuthTokenManager;
  
private tokenRefreshPromise: Promise<string> | null = null;
  
private lastRefreshAttempt = 0;
  
private readonly REFRESH_COOLDOWN = 5000; // 5 seconds
  private readonly TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes before expiry
  
  private constructor() {}
  
  static getInstance(): AuthTokenManager {
    if (!AuthTokenManager.instance) {
      AuthTokenManager.instance = new AuthTokenManager();
    }
    return AuthTokenManager.instance;
  }
  
  /**
   * Get a fresh token with automatic refresh and error handling
   */
  async getValidToken(): Promise<string | null> {
    try {
      const currentUser = auth.currentUser;

if (!currentUser) {
        console.warn('🔐 No authenticated user found');
        
return null;
      }
      
      // Check if we're already refreshing
      if (this.tokenRefreshPromise) {
        console.log('🔄 Token refresh already in progress, waiting...');
        
return await this.tokenRefreshPromise;
      }
      
      // Check cooldown period
      const now = Date.now();
      
if (now - this.lastRefreshAttempt < this.REFRESH_COOLDOWN) {
        console.log('🕐 Token refresh in cooldown period, using cached token');
        
return await currentUser.getIdToken(false); // Use cached token
      }
      
      // Check if token needs refresh
      const tokenResult = await currentUser.getIdTokenResult(false);
      
const expirationTime = new Date(tokenResult.expirationTime).getTime();
      
const timeUntilExpiry = expirationTime - now;

if (timeUntilExpiry > this.TOKEN_REFRESH_THRESHOLD) {
        console.log(`✅ Token is still valid for ${Math.round(timeUntilExpiry / 1000 / 60)} minutes`);
        
return tokenResult.token;
      }
      
      // Refresh token
      console.log('🔄 Refreshing Firebase token...');
      
this.lastRefreshAttempt = now;

this.tokenRefreshPromise = currentUser.getIdToken(true);
      
const refreshedToken = await this.tokenRefreshPromise;

console.log('✅ Token refreshed successfully');
      
return refreshedToken;
      
    } catch (error: any) {
      console.error('❌ Token refresh failed:', error);
      
      // Handle offline errors
      if (error.code === 'auth/network-request-failed' || 
          error.message?.includes('network') ||
          error.message?.includes('offline')) {
        console.warn('🌐 Network error during token refresh, will retry when online');
        
        // Try to return cached token as fallback
        try {
          const currentUser = auth.currentUser;
          
if (currentUser) {
            const cachedToken = await currentUser.getIdToken(false);
            
console.log('🔄 Using cached token during network issues');
            
return cachedToken;
          }
        } catch (cachedError) {
          console.error('❌ Failed to get cached token:', cachedError);
        }
      }
      
      throw error;
    } finally {
      this.tokenRefreshPromise = null;
    }
  }
  
  /**
   * Handle network connectivity changes
   */
  setupNetworkHandling(): void {
    window.addEventListener('online', () => {
      console.log('🌐 Network connection restored, attempting token refresh...');
      
this.getValidToken().catch(error => {
        console.error('Failed to refresh token after network restoration:', error);
      });
    });

window.addEventListener('offline', () => {
      console.warn('🌐 Network connection lost, will use cached tokens');
    });
  }
  
  /**
   * Check if user is online
   */
  isOnline(): boolean {
    return navigator.onLine;
  }
}

/**
 * Enhanced axios interceptor for automatic token refresh
 */
export const createAuthInterceptor = () => {
  const tokenManager = AuthTokenManager.getInstance();

return async (config: any) => {
    try {
      const token = await tokenManager.getValidToken();

if (token) {
        config.headers = config.headers || {};
        
config.headers.Authorization = `Bearer ${token}`;
        
console.log('🔐 Added auth token to request:', config.url);
      } else {
        console.warn('⚠️ No valid token available for request:', config.url);
      }
      
      return config;
    } catch (error) {
      console.error('❌ Failed to add auth token to request:', error);
      
      // Continue with request without token for non-authenticated endpoints
      if (config.url?.includes('/health') || config.url?.includes('/public')) {
        return config;
      }
      
      throw error;
    }
  };
};
