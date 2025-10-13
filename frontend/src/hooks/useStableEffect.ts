import { useEffect, useRef, useState } from 'react';

/**
 * Custom hook that prevents useEffect from running twice in React Strict Mode
 * This helps prevent cascading API calls that can freeze the website
 */
export function useStableEffect(
  effect: React.EffectCallback,
  deps?: React.DependencyList
) {
  const isFirstRun = useRef(true);
  const hasRunRef = useRef(false);

  useEffect(() => {
    // In development with Strict Mode, useEffect runs twice
    // This prevents the double execution
    if (process.env.NODE_ENV === 'development') {
      if (isFirstRun.current) {
        isFirstRun.current = false;
        hasRunRef.current = true;
        return effect();
      } else if (!hasRunRef.current) {
        hasRunRef.current = true;
        return effect();
      }
      // Skip second run in development
      return;
    }

    // In production, run normally
    return effect();
  }, deps);
}

/**
 * Hook that prevents API calls from running multiple times
 * Includes automatic cleanup and request cancellation
 */
export function useStableApiEffect(
  effect: () => Promise<void> | (() => void),
  deps?: React.DependencyList
) {
  const abortControllerRef = useRef<AbortController | null>(null);
  const isCleanedUpRef = useRef(false);

  useStableEffect(() => {
    isCleanedUpRef.current = false;

    // Create new AbortController for this effect
    abortControllerRef.current = new AbortController();

    const runEffect = async () => {
      try {
        if (!isCleanedUpRef.current) {
          await effect();
        }
      } catch (error) {
        if (!isCleanedUpRef.current && error.name !== 'AbortError') {
          console.error('API effect error:', error);
        }
      }
    };

    runEffect();

    // Cleanup function
    return () => {
      isCleanedUpRef.current = true;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, deps);

  // Return abort controller for manual cancellation
  return abortControllerRef.current;
}

/**
 * Hook for data fetching that prevents duplicate requests
 * Includes loading state and error handling
 */
export function useStableDataFetch<T>(
  fetchFn: (signal: AbortSignal) => Promise<T>,
  deps?: React.DependencyList
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);
  const mountedRef = useRef(true);

  useStableApiEffect(() => {
    let isCancelled = false;
    setLoading(true);
    setError(null);

    const abortController = new AbortController();

    const fetchData = async () => {
      try {
        const result = await fetchFn(abortController.signal);
        if (!isCancelled && mountedRef.current) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (!isCancelled && mountedRef.current && err.name !== 'AbortError') {
          setError(err instanceof Error ? err : new Error('Unknown error'));
          setData(null);
        }
      } finally {
        if (!isCancelled && mountedRef.current) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isCancelled = true;
      abortController.abort();
    };
  }, deps);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return { data, loading, error };
}