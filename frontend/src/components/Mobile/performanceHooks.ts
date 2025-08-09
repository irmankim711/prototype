/**
 * Performance Optimization Hooks
 * React hooks for lazy loading and performance monitoring
 */

import { useState, useEffect, useRef, useCallback } from "react";
import type {
  PerformanceMetrics,
  ExtendedPerformance,
  ExtendedNavigator,
} from "./performanceUtils";
import { getDeviceType } from "./performanceUtils";

// Lazy Loading Hook with Intersection Observer
export const useLazyLoading = (threshold = 0.1, rootMargin = "50px") => {
  const [isVisible, setIsVisible] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element || hasLoaded) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          setHasLoaded(true);
          observer.unobserve(element);
        }
      },
      { threshold, rootMargin }
    );

    observer.observe(element);

    return () => {
      if (element) observer.unobserve(element);
    };
  }, [threshold, rootMargin, hasLoaded]);

  return { elementRef, isVisible, hasLoaded };
};

// Performance Monitor Hook
export const usePerformanceMonitor = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  const startMonitoring = useCallback(() => {
    if (isMonitoring) return;

    setIsMonitoring(true);
    const startTime = performance.now();

    const observer = new PerformanceObserver((list: any) => {
      try {
        const entries = list.getEntries();
        const paintEntries = entries.filter(
          (entry: any) =>
            entry.entryType === "paint" || entry.entryType === "navigation"
        );

        if (paintEntries.length > 0) {
          const navigationEntry = paintEntries.find(
            (entry: any) => entry.entryType === "navigation"
          ) as PerformanceNavigationTiming;
          const paintEntry = paintEntries.find(
            (entry: any) => entry.name === "first-contentful-paint"
          );

          const loadTime =
            navigationEntry?.loadEventEnd - navigationEntry?.loadEventStart ||
            0;
          const renderTime = paintEntry?.startTime || 0;

          const extendedPerformance = performance as ExtendedPerformance;
          const extendedNavigator = navigator as ExtendedNavigator;

          setMetrics({
            loadTime,
            renderTime,
            interactionTime: performance.now() - startTime,
            memoryUsage: extendedPerformance.memory?.usedJSHeapSize || 0,
            networkType:
              extendedNavigator.connection?.effectiveType || "unknown",
            deviceType: getDeviceType(),
          });

          observer.disconnect();
          setIsMonitoring(false);
        }
      } catch (error) {
        console.error("Performance monitoring error:", error);
        observer.disconnect();
        setIsMonitoring(false);
      }
    });

    observer.observe({ entryTypes: ["paint", "navigation"] });

    setTimeout(() => {
      observer.disconnect();
      setIsMonitoring(false);
    }, 10000);
  }, [isMonitoring]);

  return { metrics, startMonitoring, isMonitoring };
};
