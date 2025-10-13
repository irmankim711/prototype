/**
 * Performance Optimization Utilities
 * Separated utilities to fix React Fast Refresh issues
 */

// Types for performance monitoring
interface PerformanceMetrics {
  loadTime: number;
  renderTime: number;
  interactionTime: number;
  memoryUsage: number;
  networkType: string;
  deviceType: "mobile" | "tablet" | "desktop";
}

// Extended performance interfaces for type safety
interface ExtendedPerformance extends Performance {
  memory?: {
    usedJSHeapSize: number;
    totalJSHeapSize: number;
    jsHeapSizeLimit: number;
  };
}

interface ExtendedNavigator extends Navigator {
  connection?: {
    effectiveType: string;
    downlink: number;
    rtt: number;
  };
}

interface ExtendedWindow extends Window {
  gc?: () => void;
}

// Web Vitals metric interface
interface WebVitalMetric {
  name: string;
  value: number;
  rating: "good" | "needs-improvement" | "poor";
  delta: number;
  id: string;
}

// Module import interface for lazy routes
interface LazyRouteModule {
  default: React.ComponentType<Record<string, unknown>>;
}

// Device Type Detection
export const getDeviceType = (): "mobile" | "tablet" | "desktop" => {
  const width = window.innerWidth;
  if (width < 768) return "mobile";
  if (width < 1024) return "tablet";
  return "desktop";
};

// Bundle Size Analyzer
export const BundleAnalyzer = {
  // Measure bundle load time
  measureBundleLoad: (): Promise<number> => {
    return new Promise((resolve: any) => {
      const startTime = performance.now();

      const observer = new PerformanceObserver((list: any) => {
        const entries = list.getEntries();
        const bundleEntry = entries.find(
          (entry: any) =>
            entry.name.includes("bundle") || entry.name.includes("chunk")
        ) as PerformanceResourceTiming;

        if (bundleEntry && bundleEntry.responseEnd) {
          const loadTime = bundleEntry.responseEnd - bundleEntry.startTime;
          resolve(loadTime);
          observer.disconnect();
        }
      });

      observer.observe({ entryTypes: ["resource"] });

      // Fallback timeout
      setTimeout(() => {
        const endTime = performance.now();
        resolve(endTime - startTime);
        observer.disconnect();
      }, 5000);
    });
  },

  // Get bundle size information
  getBundleInfo: async (): Promise<{
    totalSize: number;
    gzippedSize: number;
    chunkCount: number;
  }> => {
    try {
      const response = await fetch("/api/bundle-info");
      if (!response.ok) {
        throw Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.warn("Bundle info not available:", error);
      return { totalSize: 0, gzippedSize: 0, chunkCount: 0 };
    }
  },
};

// Resource Prefetching
export const ResourcePrefetcher = {
  // Prefetch critical resources
  prefetchCritical: (urls: string[]) => {
    urls.forEach((url: any) => {
      const link = document.createElement("link");
      link.rel = "prefetch";
      link.href = url;
      document.head.appendChild(link);
    });
  },

  // Preload immediate resources
  preloadImmediate: (
    url: string,
    type: "script" | "style" | "image" | "font"
  ) => {
    const link = document.createElement("link");
    link.rel = "preload";
    link.href = url;
    link.as = type;
    if (type === "font") {
      link.crossOrigin = "anonymous";
    }
    document.head.appendChild(link);
  },

  // DNS prefetch for external domains
  dnsPrefetch: (domains: string[]) => {
    domains.forEach((domain: any) => {
      const link = document.createElement("link");
      link.rel = "dns-prefetch";
      link.href = `//${domain}`;
      document.head.appendChild(link);
    });
  },
};

// Memory Management
export const MemoryManager = {
  // Clear unused resources
  clearUnusedResources: async (): Promise<void> => {
    try {
      // Clear old caches
      if ("caches" in window) {
        const names = await caches.keys();
        const deletePromises = names
          .filter((name: any) => name.includes("old") || name.includes("unused"))
          .map((name: any) => caches.delete(name));
        await Promise.all(deletePromises);
      }

      // Clear old IndexedDB data
      if ("indexedDB" in window) {
        console.log("IndexedDB cleanup would go here");
      }

      // Force garbage collection if available
      const extendedWindow = window as ExtendedWindow;
      if (extendedWindow.gc) {
        extendedWindow.gc();
      }
    } catch (error) {
      console.error("Error clearing unused resources:", error);
    }
  },

  // Monitor memory usage
  getMemoryInfo: (): {
    used: number;
    total: number;
    limit: number;
  } => {
    const extendedPerformance = performance as ExtendedPerformance;
    const memory = extendedPerformance.memory;
    if (memory) {
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
      };
    }
    return { used: 0, total: 0, limit: 0 };
  },

  // Check if memory usage is high
  isMemoryHigh: (threshold = 0.8): boolean => {
    const memory = MemoryManager.getMemoryInfo();
    if (memory.total === 0) return false;
    return memory.used / memory.total > threshold;
  },
};

// Network Optimization
export const NetworkOptimizer = {
  // Compress requests
  compressRequest: async (data: Record<string, unknown>): Promise<string> => {
    if ("CompressionStream" in window) {
      try {
        const stream = new CompressionStream("gzip");
        const writer = stream.writable.getWriter();
        const reader = stream.readable.getReader();

        await writer.write(new TextEncoder().encode(JSON.stringify(data)));
        await writer.close();

        const chunks: Uint8Array[] = [];
        let done = false;

        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) chunks.push(value);
        }

        const concatenated = new Uint8Array(
          chunks.reduce((acc, chunk) => acc + chunk.length, 0)
        );
        let offset = 0;
        for (const chunk of chunks) {
          concatenated.set(chunk, offset);
          offset += chunk.length;
        }

        return btoa(String.fromCharCode(...concatenated));
      } catch (error) {
        console.warn("Compression failed, falling back to JSON:", error);
        return JSON.stringify(data);
      }
    }

    return JSON.stringify(data);
  },

  // Batch requests
  batchRequests: function <T>(
    requests: (() => Promise<T>)[],
    batchSize = 5,
    delay = 100
  ): Promise<T[]> {
    return new Promise((resolve, reject) => {
      (async () => {
        const results: T[] = [];
        const errors: Error[] = [];

        for (let i = 0; i < requests.length; i += batchSize) {
          const batch = requests.slice(i, i + batchSize);

          try {
            const batchResults = await Promise.all(
              batch.map((request: any) => request())
            );
            results.push(...batchResults);
          } catch (error) {
            errors.push(error as Error);
          }

          // Delay between batches
          if (i + batchSize < requests.length) {
            await new Promise((resolveDelay: any) =>
              setTimeout(resolveDelay, delay)
            );
          }
        }

        if (errors.length > 0) {
          reject(errors);
        } else {
          resolve(results);
        }
      })().catch(reject);
    });
  },

  // Retry failed requests
  retryRequest: async function <T>(
    requestFn: () => Promise<T>,
    maxRetries = 3,
    backoffMs = 1000
  ): Promise<T> {
    let lastError: Error = new Error("Unknown error");

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error as Error;

        if (attempt === maxRetries) break;

        // Exponential backoff with jitter
        const jitter = Math.random() * 0.1 * backoffMs;
        const delay = backoffMs * Math.pow(2, attempt) + jitter;
        await new Promise((resolveDelay: any) => setTimeout(resolveDelay, delay));
      }
    }

    throw lastError;
  },
};

// Performance Metrics Reporter
export const MetricsReporter = {
  // Report Core Web Vitals
  reportWebVitals: (callback: (metric: WebVitalMetric) => void) => {
    try {
      import("web-vitals")
        .then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
          getCLS(callback);
          getFID(callback);
          getFCP(callback);
          getLCP(callback);
          getTTFB(callback);
        })
        .catch((error: any) => {
          console.warn("Web Vitals library not available:", error);
        });
    } catch (error) {
      console.warn("Web Vitals import failed:", error);
    }
  },

  // Send metrics to analytics
  sendMetrics: async (
    metrics: PerformanceMetrics,
    retries = 3
  ): Promise<void> => {
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const response = await fetch("/api/analytics/performance", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...metrics,
            timestamp: Date.now(),
            userAgent: navigator.userAgent,
            url: window.location.href,
          }),
        });

        if (!response.ok) {
          throw Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        console.log("Performance metrics sent successfully");
        return;
      } catch (error) {
        console.error(
          `Failed to send performance metrics (attempt ${attempt + 1}):`,
          error
        );

        if (attempt < retries - 1) {
          await new Promise((resolve: any) =>
            setTimeout(resolve, Math.pow(2, attempt) * 1000)
          );
        }
      }
    }

    console.error("All attempts to send performance metrics failed");
  },
};

// Export types
export type {
  PerformanceMetrics,
  WebVitalMetric,
  LazyRouteModule,
  ExtendedPerformance,
  ExtendedNavigator,
  ExtendedWindow,
};
