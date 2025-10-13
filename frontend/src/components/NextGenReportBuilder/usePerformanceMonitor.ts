/**
 * Performance Monitoring Hook for NextGen Report Builder
 * Tracks performance metrics and provides optimization insights
 */

import { useEffect, useRef, useCallback } from 'react';

interface PerformanceMetrics {
  renderTime: number;
  memoryUsage?: number;
  interactionTime: number;
  dataLoadTime: number;
  chartGenerationTime: number;
}

interface PerformanceThresholds {
  renderTime: number; // ms
  interactionTime: number; // ms
  dataLoadTime: number; // ms
  chartGenerationTime: number; // ms
}

const DEFAULT_THRESHOLDS: PerformanceThresholds = {
  renderTime: 100,
  interactionTime: 50,
  dataLoadTime: 1000,
  chartGenerationTime: 2000
};

export const usePerformanceMonitor = (
  componentName: string,
  thresholds: Partial<PerformanceThresholds> = {}
) => {
  const metricsRef = useRef<PerformanceMetrics>({
    renderTime: 0,
    interactionTime: 0,
    dataLoadTime: 0,
    chartGenerationTime: 0
  });
  
  const renderStartTime = useRef<number>(0);
  const interactionStartTime = useRef<number>(0);
  
  const finalThresholds = { ...DEFAULT_THRESHOLDS, ...thresholds };

  // Track render performance
  useEffect(() => {
    renderStartTime.current = performance.now();
    
    return () => {
      const renderTime = performance.now() - renderStartTime.current;
      metricsRef.current.renderTime = renderTime;
      
      if (renderTime > finalThresholds.renderTime) {
        // Log performance warning in development
        if (process.env.NODE_ENV === 'development') {
          console.warn(
            `[Performance] ${componentName} render time (${renderTime.toFixed(2)}ms) exceeds threshold (${finalThresholds.renderTime}ms)`
          );
        }
        
        // In production, send to performance monitoring service
        if (process.env.NODE_ENV === 'production') {
          // This would send to performance monitoring service
          // e.g., New Relic, DataDog, or custom analytics
        }
      }
    };
  });

  // Track interaction performance
  const trackInteraction = useCallback((interactionName: string, fn: () => void | Promise<void>) => {
    interactionStartTime.current = performance.now();
    
    try {
      const result = fn();
      
      if (result instanceof Promise) {
        return result.finally(() => {
          const interactionTime = performance.now() - interactionStartTime.current;
          metricsRef.current.interactionTime = interactionTime;
          
          if (interactionTime > finalThresholds.interactionTime) {
            if (process.env.NODE_ENV === 'development') {
              console.warn(
                `[Performance] ${componentName} interaction '${interactionName}' time (${interactionTime.toFixed(2)}ms) exceeds threshold (${finalThresholds.interactionTime}ms)`
              );
            }
          }
        });
      } else {
        const interactionTime = performance.now() - interactionStartTime.current;
        metricsRef.current.interactionTime = interactionTime;
        
        if (interactionTime > finalThresholds.interactionTime) {
          if (process.env.NODE_ENV === 'development') {
            console.warn(
              `[Performance] ${componentName} interaction '${interactionName}' time (${interactionTime.toFixed(2)}ms) exceeds threshold (${finalThresholds.interactionTime}ms)`
            );
          }
        }
        
        return result;
      }
    } catch (error) {
      const interactionTime = performance.now() - interactionStartTime.current;
      metricsRef.current.interactionTime = interactionTime;
      throw error;
    }
  }, [componentName, finalThresholds.interactionTime]);

  // Track data loading performance
  const trackDataLoad = useCallback(async <T>(dataLoadFn: () => Promise<T>): Promise<T> => {
    const startTime = performance.now();
    
    try {
      const result = await dataLoadFn();
      const dataLoadTime = performance.now() - startTime;
      metricsRef.current.dataLoadTime = dataLoadTime;
      
      if (dataLoadTime > finalThresholds.dataLoadTime) {
        if (process.env.NODE_ENV === 'development') {
          console.warn(
            `[Performance] ${componentName} data load time (${dataLoadTime.toFixed(2)}ms) exceeds threshold (${finalThresholds.dataLoadTime}ms)`
          );
        }
      }
      
      return result;
    } catch (error) {
      const dataLoadTime = performance.now() - startTime;
      metricsRef.current.dataLoadTime = dataLoadTime;
      throw error;
    }
  }, [componentName, finalThresholds.dataLoadTime]);

  // Track chart generation performance
  const trackChartGeneration = useCallback(async <T>(chartGenFn: () => Promise<T>): Promise<T> => {
    const startTime = performance.now();
    
    try {
      const result = await chartGenFn();
      const chartGenerationTime = performance.now() - startTime;
      metricsRef.current.chartGenerationTime = chartGenerationTime;
      
      if (chartGenerationTime > finalThresholds.chartGenerationTime) {
        if (process.env.NODE_ENV === 'development') {
          console.warn(
            `[Performance] ${componentName} chart generation time (${chartGenerationTime.toFixed(2)}ms) exceeds threshold (${finalThresholds.chartGenerationTime}ms)`
          );
        }
      }
      
      return result;
    } catch (error) {
      const chartGenerationTime = performance.now() - startTime;
      metricsRef.current.chartGenerationTime = chartGenerationTime;
      throw error;
    }
  }, [componentName, finalThresholds.chartGenerationTime]);

  // Get current metrics
  const getMetrics = useCallback((): PerformanceMetrics => {
    return { ...metricsRef.current };
  }, []);

  // Reset metrics
  const resetMetrics = useCallback(() => {
    metricsRef.current = {
      renderTime: 0,
      interactionTime: 0,
      dataLoadTime: 0,
      chartGenerationTime: 0
    };
  }, []);

  // Get performance insights
  const getPerformanceInsights = useCallback(() => {
    const metrics = metricsRef.current;
    const insights: string[] = [];
    
    if (metrics.renderTime > finalThresholds.renderTime) {
      insights.push(`Consider optimizing render performance (${metrics.renderTime.toFixed(2)}ms)`);
    }
    
    if (metrics.interactionTime > finalThresholds.interactionTime) {
      insights.push(`Consider optimizing interaction performance (${metrics.interactionTime.toFixed(2)}ms)`);
    }
    
    if (metrics.dataLoadTime > finalThresholds.dataLoadTime) {
      insights.push(`Consider implementing data caching or pagination (${metrics.dataLoadTime.toFixed(2)}ms)`);
    }
    
    if (metrics.chartGenerationTime > finalThresholds.chartGenerationTime) {
      insights.push(`Consider optimizing chart generation or implementing progressive loading (${metrics.chartGenerationTime.toFixed(2)}ms)`);
    }
    
    return insights;
  }, [finalThresholds]);

  return {
    trackInteraction,
    trackDataLoad,
    trackChartGeneration,
    getMetrics,
    resetMetrics,
    getPerformanceInsights
  };
};
