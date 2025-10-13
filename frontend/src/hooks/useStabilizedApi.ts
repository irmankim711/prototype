import { useEffect, useRef } from 'react';
import { stabilizedApi, StabilizedApiService } from '../services/stabilizedApiService';

/**
 * Hook that provides access to the stabilized API service
 * Automatically handles cleanup on component unmount
 */
export function useStabilizedApi(): StabilizedApiService {
  const componentIdRef = useRef<string>(`component-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);

  useEffect(() => {
    // Cleanup function to cancel requests when component unmounts
    return () => {
      console.log(`🧹 Cleaning up API requests for component: ${componentIdRef.current}`);
      stabilizedApi.cancelAllRequests(`Component unmounted: ${componentIdRef.current}`);
    };
  }, []);

  return stabilizedApi;
}

/**
 * Hook to cancel API requests when navigating away from a page
 */
export function useApiCleanupOnRouteChange() {
  useEffect(() => {
    const handleRouteChange = () => {
      stabilizedApi.cancelAllRequests('Route change detected');
    };

    // Listen for route changes (works with React Router)
    const handlePopState = () => {
      handleRouteChange();
    };

    window.addEventListener('popstate', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      handleRouteChange();
    };
  }, []);
}

/**
 * Development-only hook to monitor API performance
 */
export function useApiPerformanceMonitor() {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;

    const interval = setInterval(() => {
      const status = stabilizedApi.getStatus();
      if (status.activeRequests > 0) {
        console.log(`📊 API Status: ${status.activeRequests} active requests, ${status.queuedRequests} queued`);
      }
    }, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, []);
}

/**
 * Hook for critical error detection that might cause website freezing
 */
export function useApiErrorDetection(onCriticalError?: (error: Error) => void) {
  useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const error = event.reason;

      // Check for cascading API failures
      if (
        error?.message?.includes('Network Error') ||
        error?.code === 'ERR_NETWORK' ||
        error?.message?.includes('timeout')
      ) {
        console.error('🚨 Critical API error detected - potential website freeze risk:', error);

        // Cancel all pending requests to prevent cascading failures
        stabilizedApi.cancelAllRequests('Critical error detected - preventing cascade');

        if (onCriticalError) {
          onCriticalError(error instanceof Error ? error : new Error(String(error)));
        }
      }
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, [onCriticalError]);
}