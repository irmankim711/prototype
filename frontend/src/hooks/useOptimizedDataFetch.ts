import { useState, useEffect, useRef, useCallback } from 'react';

interface UseOptimizedDataFetchOptions<T> {
  fetchFn: () => Promise<T>;
  cacheKey: string;
  cacheDuration?: number; // in milliseconds
  enabled?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

interface UseOptimizedDataFetchResult<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  clearCache: () => void;
}

// Global cache to prevent multiple components from fetching the same data
const globalCache = new Map<string, { data: any; timestamp: number; ttl: number }>();
const pendingRequests = new Map<string, Promise<any>>();

export function useOptimizedDataFetch<T>({
  fetchFn,
  cacheKey,
  cacheDuration = 5 * 60 * 1000, // 5 minutes default
  enabled = true,
  onSuccess,
  onError
}: UseOptimizedDataFetchOptions<T>): UseOptimizedDataFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check if we have valid cached data
  const getCachedData = useCallback((): T | null => {
    const cached = globalCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data as T;
    }
    globalCache.delete(cacheKey);
    return null;
  }, [cacheKey]);

  // Set cached data
  const setCachedData = useCallback((newData: T) => {
    globalCache.set(cacheKey, {
      data: newData,
      timestamp: Date.now(),
      ttl: cacheDuration
    });
  }, [cacheKey, cacheDuration]);

  // Fetch data with deduplication
  const fetchData = useCallback(async (): Promise<void> => {
    // Check cache first
    const cached = getCachedData();
    if (cached) {
      setData(cached);
      setError(null);
      return;
    }

    // Check if there's already a pending request
    if (pendingRequests.has(cacheKey)) {
      try {
        const result = await pendingRequests.get(cacheKey)!;
        setData(result);
        setError(null);
        onSuccess?.(result);
        return;
      } catch (err) {
        setError(err as Error);
        onError?.(err as Error);
        return;
      }
    }

    setIsLoading(true);
    setError(null);

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      // Create the promise and store it
      const promise = fetchFn();
      pendingRequests.set(cacheKey, promise);

      const result = await promise;
      
      // Only update state if the request wasn't aborted
      if (!abortControllerRef.current?.signal.aborted) {
        setData(result);
        setCachedData(result);
        onSuccess?.(result);
      }
    } catch (err) {
      if (!abortControllerRef.current?.signal.aborted) {
        const error = err as Error;
        setError(error);
        onError?.(error);
      }
    } finally {
      if (!abortControllerRef.current?.signal.aborted) {
        setIsLoading(false);
      }
      pendingRequests.delete(cacheKey);
    }
  }, [fetchFn, cacheKey, getCachedData, setCachedData, onSuccess, onError]);

  // Refetch function
  const refetch = useCallback(async (): Promise<void> => {
    // Clear cache to force fresh fetch
    globalCache.delete(cacheKey);
    await fetchData();
  }, [fetchData, cacheKey]);

  // Clear cache function
  const clearCache = useCallback((): void => {
    globalCache.delete(cacheKey);
    setData(null);
  }, [cacheKey]);

  // Effect to fetch data when enabled or dependencies change
  useEffect(() => {
    if (enabled) {
      fetchData();
    }

    // Cleanup function to abort pending requests
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [enabled, fetchData]);

  // Initialize with cached data if available
  useEffect(() => {
    const cached = getCachedData();
    if (cached && !data) {
      setData(cached);
    }
  }, [getCachedData, data]);

  return {
    data,
    isLoading,
    error,
    refetch,
    clearCache
  };
}
