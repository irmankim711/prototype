/**
 * Performance Optimization Components
 * React components for lazy loading, performance monitoring, and optimization
 */

import React from "react";
import { Suspense, useState, useEffect, useCallback } from "react";
import { MobileSkeleton } from "./MobileComponents";
import type { PerformanceMetrics, WebVitalMetric } from "./performanceUtils";
import {
  BundleAnalyzer,
  ResourcePrefetcher,
  MemoryManager,
  NetworkOptimizer,
  MetricsReporter,
  getDeviceType,
} from "./performanceUtils";
import { useLazyLoading, usePerformanceMonitor } from "./performanceHooks";
import { createLazyRoute } from "./routeUtils";

// Component-specific interfaces
interface LazyComponentProps {
  children: React.ReactNode;
  fallback?: React.ComponentType;
  threshold?: number;
  rootMargin?: string;
}

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholder?: string;
  onLoad?: () => void;
  onError?: () => void;
}

// Lazy Component Wrapper
export const LazyComponent: React.FC<LazyComponentProps> = ({
  children,
  fallback: Fallback = MobileSkeleton,
  threshold = 0.1,
  rootMargin = "50px",
}) => {
  const { elementRef, isVisible } = useLazyLoading(threshold, rootMargin);

  return (
    <div ref={elementRef} className="lazy-component">
      {isVisible ? (
        <Suspense fallback={<Fallback />}>{children}</Suspense>
      ) : (
        <Fallback />
      )}
    </div>
  );
};

// Image Lazy Loading Component
export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className,
  placeholder,
  onLoad,
  onError,
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const { elementRef, isVisible } = useLazyLoading();

  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    onLoad?.();
  }, [onLoad]);

  const handleError = useCallback(() => {
    setHasError(true);
    onError?.();
  }, [onError]);

  return (
    <div ref={elementRef} className={`lazy-image-container ${className || ""}`}>
      {isVisible && !hasError && (
        <img
          src={src}
          alt={alt}
          onLoad={handleLoad}
          onError={handleError}
          className={`lazy-image ${isLoaded ? "loaded" : "loading"}`}
          loading="lazy"
          decoding="async"
        />
      )}
      {(!isVisible || !isLoaded) && !hasError && (
        <div className="lazy-image-placeholder">
          {placeholder ? (
            <img src={placeholder} alt={alt} className="placeholder-image" />
          ) : (
            <div className="placeholder-skeleton" />
          )}
        </div>
      )}
      {hasError && (
        <div className="lazy-image-error">
          <span>Image failed to load</span>
        </div>
      )}
    </div>
  );
};

// Performance Provider Component
export const PerformanceProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { startMonitoring, metrics } = usePerformanceMonitor();

  useEffect(() => {
    // Start monitoring on mount
    startMonitoring();

    // Prefetch critical resources
    ResourcePrefetcher.prefetchCritical([
      "/api/dashboard",
      "/api/reports",
      "/static/css/main.css",
    ]);

    // DNS prefetch external domains
    ResourcePrefetcher.dnsPrefetch(["api.example.com", "cdn.example.com"]);

    // Monitor memory usage
    const memoryInterval = setInterval(() => {
      if (MemoryManager.isMemoryHigh()) {
        console.warn("High memory usage detected");
        MemoryManager.clearUnusedResources();
      }
    }, 30000);

    return () => {
      clearInterval(memoryInterval);
    };
  }, [startMonitoring]);

  useEffect(() => {
    if (metrics) {
      MetricsReporter.sendMetrics(metrics);
    }
  }, [metrics]);

  return <>{children}</>;
};

// Export utilities for external use
export {
  BundleAnalyzer,
  ResourcePrefetcher,
  MemoryManager,
  NetworkOptimizer,
  MetricsReporter,
  getDeviceType,
  createLazyRoute,
  useLazyLoading,
  usePerformanceMonitor,
};

export type { PerformanceMetrics, WebVitalMetric };

export default PerformanceProvider;
