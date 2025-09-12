import { useState, useCallback, useRef } from 'react';
import apiService from '../services/apiService';
import type { LoadingState, ApiError, RequestConfig } from '../types/api.types';

/**
 * React hook for using the API service with built-in loading states and error handling
 */
export function useApi() {
  const [loadingStates, setLoadingStates] = useState<Map<string, LoadingState>>(new Map());
  const requestIdRef = useRef<string>('');

  /**
   * Generate a unique request ID for tracking
   */
  const generateRequestId = useCallback(() => {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  /**
   * Update loading state for a specific request
   */
  const updateLoadingState = useCallback((requestId: string, updates: Partial<LoadingState>) => {
    setLoadingStates(prev => {
      const newMap = new Map(prev);
      const current = newMap.get(requestId) || {
        isLoading: false,
        error: null,
        retryCount: 0,
        lastUpdated: null,
      };
      newMap.set(requestId, { ...current, ...updates });
      return newMap;
    });
  }, []);

  /**
   * Clear loading state for a specific request
   */
  const clearLoadingState = useCallback((requestId: string) => {
    setLoadingStates(prev => {
      const newMap = new Map(prev);
      newMap.delete(requestId);
      return newMap;
    });
  }, []);

  /**
   * GET request with loading state management
   */
  const get = useCallback(async <T>(
    url: string, 
    config?: RequestConfig
  ): Promise<T> => {
    const requestId = generateRequestId();
    requestIdRef.current = requestId;
    
    updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await apiService.get<T>(url, config);
      updateLoadingState(requestId, { 
        isLoading: false, 
        lastUpdated: new Date().toISOString() 
      });
      return result;
    } catch (error: any) {
      const apiError = error as ApiError;
      updateLoadingState(requestId, { 
        isLoading: false, 
        error: apiError,
        retryCount: (loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }, [generateRequestId, updateLoadingState, loadingStates]);

  /**
   * POST request with loading state management
   */
  const post = useCallback(async <T>(
    url: string, 
    data?: any, 
    config?: RequestConfig
  ): Promise<T> => {
    const requestId = generateRequestId();
    requestIdRef.current = requestId;
    
    updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await apiService.post<T>(url, data, config);
      updateLoadingState(requestId, { 
        isLoading: false, 
        lastUpdated: new Date().toISOString() 
      });
      return result;
    } catch (error: any) {
      const apiError = error as ApiError;
      updateLoadingState(requestId, { 
        isLoading: false, 
        error: apiError,
        retryCount: (loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }, [generateRequestId, updateLoadingState, loadingStates]);

  /**
   * PUT request with loading state management
   */
  const put = useCallback(async <T>(
    url: string, 
    data?: any, 
    config?: RequestConfig
  ): Promise<T> => {
    const requestId = generateRequestId();
    requestIdRef.current = requestId;
    
    updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await apiService.put<T>(url, data, config);
      updateLoadingState(requestId, { 
        isLoading: false, 
        lastUpdated: new Date().toISOString() 
      });
      return result;
    } catch (error: any) {
      const apiError = error as ApiError;
      updateLoadingState(requestId, { 
        isLoading: false, 
        error: apiError,
        retryCount: (loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }, [generateRequestId, updateLoadingState, loadingStates]);

  /**
   * PATCH request with loading state management
   */
  const patch = useCallback(async <T>(
    url: string, 
    data?: any, 
    config?: RequestConfig
  ): Promise<T> => {
    const requestId = generateRequestId();
    requestIdRef.current = requestId;
    
    updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await apiService.patch<T>(url, data, config);
      updateLoadingState(requestId, { 
        isLoading: false, 
        lastUpdated: new Date().toISOString() 
      });
      return result;
    } catch (error: any) {
      const apiError = error as ApiError;
      updateLoadingState(requestId, { 
        isLoading: false, 
        error: apiError,
        retryCount: (loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }, [generateRequestId, updateLoadingState, loadingStates]);

  /**
   * DELETE request with loading state management
   */
  const del = useCallback(async <T>(
    url: string, 
    config?: RequestConfig
  ): Promise<T> => {
    const requestId = generateRequestId();
    requestIdRef.current = requestId;
    
    updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await apiService.delete<T>(url, config);
      updateLoadingState(requestId, { 
        isLoading: false, 
        lastUpdated: new Date().toISOString() 
      });
      return result;
    } catch (error: any) {
      const apiError = error as ApiError;
      updateLoadingState(requestId, { 
        isLoading: false, 
        error: apiError,
        retryCount: (loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }, [generateRequestId, updateLoadingState, loadingStates]);

  /**
   * Get current loading state
   */
  const getCurrentLoadingState = useCallback((): LoadingState | undefined => {
    return loadingStates.get(requestIdRef.current);
  }, [loadingStates]);

  /**
   * Check if any request is currently loading
   */
  const isLoading = useCallback((): boolean => {
    return Array.from(loadingStates.values()).some(state => state.isLoading);
  }, [loadingStates]);

  /**
   * Get current error
   */
  const getCurrentError = useCallback((): ApiError | null => {
    const currentState = loadingStates.get(requestIdRef.current);
    return currentState?.error || null;
  }, [loadingStates]);

  /**
   * Clear current error
   */
  const clearError = useCallback(() => {
    if (requestIdRef.current) {
      updateLoadingState(requestIdRef.current, { error: null });
    }
  }, [updateLoadingState]);

  /**
   * Retry the last failed request
   */
  const retry = useCallback(async <T>(): Promise<T | undefined> => {
    const currentState = loadingStates.get(requestIdRef.current);
    if (currentState?.error && requestIdRef.current) {
      // Clear error and retry
      updateLoadingState(requestIdRef.current, { error: null });
      // Note: This is a simplified retry - in practice you'd want to store the last request details
      return undefined;
    }
    return undefined;
  }, [loadingStates, updateLoadingState]);

  return {
    // API methods
    get,
    post,
    put,
    patch,
    delete: del,
    
    // Loading state management
    getCurrentLoadingState,
    isLoading,
    getCurrentError,
    clearError,
    retry,
    
    // Utility methods
    updateLoadingState,
    clearLoadingState,
    
    // Direct access to apiService for advanced use cases
    apiService,
  };
}

/**
 * Specialized hook for data fetching with automatic state management
 */
export function useApiData<T>(
  url: string,
  config?: RequestConfig
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const { get } = useApi();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await get<T>(url, config);
      setData(result);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [get, url, config]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  const mutate = useCallback((newData: T) => {
    setData(newData);
  }, []);

  return {
    data,
    loading,
    error,
    refetch,
    mutate,
  };
}

/**
 * Hook for mutations (POST, PUT, PATCH, DELETE) with loading states
 */
export function useApiMutation<T, V = any>() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const { post, put, patch, delete: del } = useApi();

  const mutate = useCallback(async (
    method: 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    url: string,
    data?: V,
    config?: RequestConfig
  ): Promise<T> => {
    setLoading(true);
    setError(null);
    
    try {
      let result: T;
      
      switch (method) {
        case 'POST':
          result = await post<T>(url, data, config);
          break;
        case 'PUT':
          result = await put<T>(url, data, config);
          break;
        case 'PATCH':
          result = await patch<T>(url, data, config);
          break;
        case 'DELETE':
          result = await del<T>(url, config);
          break;
        default:
          throw new Error(`Unsupported HTTP method: ${method}`);
      }
      
      return result;
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [post, put, patch, del]);

  const reset = useCallback(() => {
    setError(null);
  }, []);

  return {
    mutate,
    loading,
    error,
    reset,
  };
}

export default useApi;
