/**
 * CSRF Token Hook
 * 
 * This hook provides CSRF token management functionality for React components.
 */

import { useState, useEffect, useCallback } from 'react';
import csrfService from '../services/csrfService';

export interface UseCSRFReturn {
  csrfToken: string | null;
  isLoading: boolean;
  error: string | null;
  refreshToken: () => Promise<void>;
  clearToken: () => void;
  getTokenHeader: () => { [key: string]: string };
  getTokenFormData: () => { [key: string]: string };
}

export const useCSRF = (): UseCSRFReturn => {
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load the current CSRF token
   */
  const loadToken = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const token = await csrfService.getToken();
      setCsrfToken(token);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load CSRF token';
      setError(errorMessage);
      console.error('❌ Failed to load CSRF token:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Refresh the CSRF token
   */
  const refreshToken = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const token = await csrfService.refreshToken();
      setCsrfToken(token);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh CSRF token';
      setError(errorMessage);
      console.error('❌ Failed to refresh CSRF token:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Clear the CSRF token
   */
  const clearToken = useCallback(() => {
    csrfService.clearToken();
    setCsrfToken(null);
    setError(null);
  }, []);

  /**
   * Get CSRF token header
   */
  const getTokenHeader = useCallback(() => {
    return csrfService.getTokenHeader();
  }, []);

  /**
   * Get CSRF token form data
   */
  const getTokenFormData = useCallback(() => {
    return csrfService.getTokenFormData();
  }, []);

  // Load token on mount
  useEffect(() => {
    loadToken();
  }, [loadToken]);

  // Set up auto-refresh effect
  useEffect(() => {
    if (!csrfToken) return;

    const interval = setInterval(async () => {
      try {
        // Check if token needs refresh
        const shouldRefresh = await csrfService.ensureValidToken() !== csrfToken;
        if (shouldRefresh) {
          await refreshToken();
        }
      } catch (err) {
        console.warn('⚠️ Auto-refresh check failed:', err);
      }
    }, 60 * 1000); // Check every minute

    return () => clearInterval(interval);
  }, [csrfToken, refreshToken]);

  return {
    csrfToken,
    isLoading,
    error,
    refreshToken,
    clearToken,
    getTokenHeader,
    getTokenFormData,
  };
};

export default useCSRF;
