/**
 * Performance Optimization Test Suite
 * Tests for performance utilities, hooks, and components
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

// Import components and utilities to test
import {
  PerformanceProvider,
  LazyComponent,
  LazyImage,
} from "../PerformanceOptimizer";
import { useLazyLoading, usePerformanceMonitor } from "../performanceHooks";
import {
  BundleAnalyzer,
  ResourcePrefetcher,
  MemoryManager,
  NetworkOptimizer,
  MetricsReporter,
  getDeviceType,
} from "../performanceUtils";
import { createLazyRoute } from "../routeUtils";

// Mock APIs that aren't available in test environment
global.IntersectionObserver = jest.fn().mockImplementation((callback) => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

global.PerformanceObserver = jest.fn().mockImplementation((callback) => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock performance API
Object.defineProperty(global, "performance", {
  value: {
    now: jest.fn(() => Date.now()),
    getEntries: jest.fn(() => []),
    memory: {
      usedJSHeapSize: 1000000,
      totalJSHeapSize: 2000000,
      jsHeapSizeLimit: 4000000,
    },
  },
  writable: true,
});

// Mock navigator
Object.defineProperty(global, "navigator", {
  value: {
    ...global.navigator,
    connection: {
      effectiveType: "4g",
      downlink: 10,
      rtt: 50,
    },
  },
  writable: true,
});

// Test component for hooks
const TestComponent: React.FC<{ threshold?: number; rootMargin?: string }> = ({
  threshold,
  rootMargin,
}) => {
  const { elementRef, isVisible, hasLoaded } = useLazyLoading(
    threshold,
    rootMargin
  );
  const { metrics, startMonitoring, isMonitoring } = usePerformanceMonitor();

  return (
    <div>
      <div ref={elementRef} data-testid="lazy-element">
        Lazy Element
      </div>
      <div data-testid="visibility">{isVisible ? "visible" : "hidden"}</div>
      <div data-testid="loaded">{hasLoaded ? "loaded" : "not-loaded"}</div>
      <button onClick={startMonitoring} data-testid="start-monitoring">
        Start Monitoring
      </button>
      <div data-testid="monitoring">
        {isMonitoring ? "monitoring" : "not-monitoring"}
      </div>
      {metrics && <div data-testid="metrics">{JSON.stringify(metrics)}</div>}
    </div>
  );
};

describe("Performance Optimization Utilities", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset window dimensions
    Object.defineProperty(window, "innerWidth", {
      value: 1024,
      writable: true,
    });
    Object.defineProperty(window, "innerHeight", {
      value: 768,
      writable: true,
    });
  });

  describe("Device Type Detection", () => {
    test("should detect mobile device", () => {
      Object.defineProperty(window, "innerWidth", {
        value: 375,
        writable: true,
      });
      expect(getDeviceType()).toBe("mobile");
    });

    test("should detect tablet device", () => {
      Object.defineProperty(window, "innerWidth", {
        value: 768,
        writable: true,
      });
      expect(getDeviceType()).toBe("tablet");
    });

    test("should detect desktop device", () => {
      Object.defineProperty(window, "innerWidth", {
        value: 1440,
        writable: true,
      });
      expect(getDeviceType()).toBe("desktop");
    });
  });

  describe("useLazyLoading Hook", () => {
    test("should initialize with default values", () => {
      render(<TestComponent />);

      expect(screen.getByTestId("visibility")).toHaveTextContent("hidden");
      expect(screen.getByTestId("loaded")).toHaveTextContent("not-loaded");
    });

    test("should accept custom threshold and rootMargin", () => {
      render(<TestComponent threshold={0.5} rootMargin="100px" />);

      // Verify the hook doesn't crash with custom parameters
      expect(screen.getByTestId("lazy-element")).toBeInTheDocument();
    });
  });

  describe("usePerformanceMonitor Hook", () => {
    test("should initialize monitoring state", () => {
      render(<TestComponent />);

      expect(screen.getByTestId("monitoring")).toHaveTextContent(
        "not-monitoring"
      );
    });

    test("should start monitoring when button is clicked", async () => {
      render(<TestComponent />);

      const startButton = screen.getByTestId("start-monitoring");
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(screen.getByTestId("monitoring")).toHaveTextContent(
          "monitoring"
        );
      });
    });
  });

  describe("LazyComponent", () => {
    const TestChild = () => <div data-testid="lazy-child">Lazy Content</div>;

    test("should render fallback initially", () => {
      render(
        <LazyComponent>
          <TestChild />
        </LazyComponent>
      );

      // Should show skeleton loader initially
      expect(screen.queryByTestId("lazy-child")).not.toBeInTheDocument();
    });

    test("should accept custom fallback component", () => {
      const CustomFallback = () => (
        <div data-testid="custom-fallback">Loading...</div>
      );

      render(
        <LazyComponent fallback={CustomFallback}>
          <TestChild />
        </LazyComponent>
      );

      expect(screen.getByTestId("custom-fallback")).toBeInTheDocument();
    });
  });

  describe("LazyImage", () => {
    test("should render placeholder initially", () => {
      render(
        <LazyImage
          src="https://example.com/image.jpg"
          alt="Test image"
          placeholder="https://example.com/placeholder.jpg"
        />
      );

      const placeholder = screen.getByAltText("Test image");
      expect(placeholder).toHaveClass("placeholder-image");
    });

    test("should handle loading callbacks", () => {
      const onLoad = jest.fn();
      const onError = jest.fn();

      render(
        <LazyImage
          src="https://example.com/image.jpg"
          alt="Test image"
          onLoad={onLoad}
          onError={onError}
        />
      );

      expect(onLoad).not.toHaveBeenCalled();
      expect(onError).not.toHaveBeenCalled();
    });
  });

  describe("BundleAnalyzer", () => {
    test("should measure bundle load time", async () => {
      const mockPromise = BundleAnalyzer.measureBundleLoad();
      expect(mockPromise).toBeInstanceOf(Promise);

      const loadTime = await mockPromise;
      expect(typeof loadTime).toBe("number");
      expect(loadTime).toBeGreaterThanOrEqual(0);
    });

    test("should get bundle info", async () => {
      // Mock fetch for bundle info
      global.fetch = jest.fn().mockRejectedValue(new Error("Not found"));

      const bundleInfo = await BundleAnalyzer.getBundleInfo();
      expect(bundleInfo).toEqual({
        totalSize: 0,
        gzippedSize: 0,
        chunkCount: 0,
      });
    });
  });

  describe("ResourcePrefetcher", () => {
    beforeEach(() => {
      document.head.innerHTML = "";
    });

    test("should prefetch critical resources", () => {
      const urls = ["/api/data", "/static/styles.css"];
      ResourcePrefetcher.prefetchCritical(urls);

      const links = document.head.querySelectorAll('link[rel="prefetch"]');
      expect(links).toHaveLength(2);
      expect(links[0]).toHaveAttribute("href", "/api/data");
      expect(links[1]).toHaveAttribute("href", "/static/styles.css");
    });

    test("should preload immediate resources", () => {
      ResourcePrefetcher.preloadImmediate("/static/main.js", "script");

      const link = document.head.querySelector('link[rel="preload"]');
      expect(link).toHaveAttribute("href", "/static/main.js");
      expect(link).toHaveAttribute("as", "script");
    });

    test("should DNS prefetch domains", () => {
      const domains = ["api.example.com", "cdn.example.com"];
      ResourcePrefetcher.dnsPrefetch(domains);

      const links = document.head.querySelectorAll('link[rel="dns-prefetch"]');
      expect(links).toHaveLength(2);
      expect(links[0]).toHaveAttribute("href", "//api.example.com");
      expect(links[1]).toHaveAttribute("href", "//cdn.example.com");
    });
  });

  describe("MemoryManager", () => {
    test("should get memory info", () => {
      const memoryInfo = MemoryManager.getMemoryInfo();

      expect(memoryInfo).toHaveProperty("used");
      expect(memoryInfo).toHaveProperty("total");
      expect(memoryInfo).toHaveProperty("limit");
      expect(typeof memoryInfo.used).toBe("number");
      expect(typeof memoryInfo.total).toBe("number");
      expect(typeof memoryInfo.limit).toBe("number");
    });

    test("should detect high memory usage", () => {
      const isHigh = MemoryManager.isMemoryHigh(0.5);
      expect(typeof isHigh).toBe("boolean");
    });

    test("should clear unused resources", async () => {
      // Mock caches API
      global.caches = {
        keys: jest.fn().mockResolvedValue(["old-cache", "current-cache"]),
        delete: jest.fn().mockResolvedValue(true),
      };

      await expect(MemoryManager.clearUnusedResources()).resolves.not.toThrow();
    });
  });

  describe("NetworkOptimizer", () => {
    test("should compress requests", async () => {
      const data = { test: "data", array: [1, 2, 3] };
      const compressed = await NetworkOptimizer.compressRequest(data);

      // Should fallback to JSON string if compression not available
      expect(typeof compressed).toBe("string");
    });

    test("should batch requests", async () => {
      const requests = [
        () => Promise.resolve("result1"),
        () => Promise.resolve("result2"),
        () => Promise.resolve("result3"),
      ];

      const results = await NetworkOptimizer.batchRequests(requests, 2, 0);
      expect(results).toEqual(["result1", "result2", "result3"]);
    });

    test("should retry failed requests", async () => {
      let attemptCount = 0;
      const failingRequest = () => {
        attemptCount++;
        if (attemptCount < 3) {
          return Promise.reject(new Error("Request failed"));
        }
        return Promise.resolve("success");
      };

      const result = await NetworkOptimizer.retryRequest(failingRequest, 3, 10);
      expect(result).toBe("success");
      expect(attemptCount).toBe(3);
    });
  });

  describe("MetricsReporter", () => {
    test("should send metrics to analytics", async () => {
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      });

      const metrics = {
        loadTime: 1000,
        renderTime: 500,
        interactionTime: 100,
        memoryUsage: 1000000,
        networkType: "4g",
        deviceType: "desktop" as const,
      };

      await expect(MetricsReporter.sendMetrics(metrics)).resolves.not.toThrow();
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/analytics/performance",
        expect.any(Object)
      );
    });

    test("should handle failed metrics sending", async () => {
      global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

      const metrics = {
        loadTime: 1000,
        renderTime: 500,
        interactionTime: 100,
        memoryUsage: 1000000,
        networkType: "4g",
        deviceType: "desktop" as const,
      };

      // Should not throw but log errors
      await expect(
        MetricsReporter.sendMetrics(metrics, 1)
      ).resolves.not.toThrow();
    });
  });

  describe("createLazyRoute", () => {
    test("should create lazy route component", () => {
      const mockImport = () =>
        Promise.resolve({
          default: () => <div data-testid="route-component">Route Content</div>,
        });

      const LazyRoute = createLazyRoute(mockImport);
      expect(LazyRoute).toBeDefined();
      expect(typeof LazyRoute).toBe("object");
    });

    test("should handle failed route imports", () => {
      const mockFailingImport = () =>
        Promise.reject(new Error("Import failed"));

      const LazyRoute = createLazyRoute(mockFailingImport);
      expect(LazyRoute).toBeDefined();
    });
  });

  describe("PerformanceProvider", () => {
    test("should render children", () => {
      render(
        <PerformanceProvider>
          <div data-testid="test-child">Test Content</div>
        </PerformanceProvider>
      );

      expect(screen.getByTestId("test-child")).toBeInTheDocument();
    });

    test("should initialize performance monitoring", () => {
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      render(
        <PerformanceProvider>
          <div>Test Content</div>
        </PerformanceProvider>
      );

      // Should not throw during initialization
      expect(screen.getByText("Test Content")).toBeInTheDocument();

      consoleSpy.mockRestore();
    });
  });
});

// Test error logging and monitoring
describe("Error Logging and Monitoring", () => {
  test("should log performance monitoring errors", () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    // Mock PerformanceObserver to throw an error
    const mockObserver = jest.fn().mockImplementation(() => {
      throw new Error("Observer error");
    });
    global.PerformanceObserver = mockObserver;

    render(<TestComponent />);

    const startButton = screen.getByTestId("start-monitoring");
    fireEvent.click(startButton);

    // Should handle errors gracefully
    expect(screen.getByTestId("test-child")).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  test("should log bundle analyzer errors", async () => {
    const consoleSpy = jest.spyOn(console, "warn").mockImplementation();

    // Mock fetch to fail
    global.fetch = jest.fn().mockRejectedValue(new Error("Network error"));

    const bundleInfo = await BundleAnalyzer.getBundleInfo();
    expect(bundleInfo).toEqual({
      totalSize: 0,
      gzippedSize: 0,
      chunkCount: 0,
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      "Bundle info not available:",
      expect.any(Error)
    );

    consoleSpy.mockRestore();
  });
});

// Performance assertions
describe("Performance Assertions", () => {
  test("performance utilities should complete within acceptable time", async () => {
    const startTime = performance.now();

    // Test multiple utilities
    const deviceType = getDeviceType();
    const memoryInfo = MemoryManager.getMemoryInfo();
    await MemoryManager.clearUnusedResources();

    const endTime = performance.now();
    const executionTime = endTime - startTime;

    // Should complete within 100ms
    expect(executionTime).toBeLessThan(100);
    expect(deviceType).toBeDefined();
    expect(memoryInfo).toBeDefined();
  });

  test("network optimizer should handle large batches efficiently", async () => {
    const requests = Array.from(
      { length: 100 },
      (_, i) => () => Promise.resolve(`result${i}`)
    );

    const startTime = performance.now();
    const results = await NetworkOptimizer.batchRequests(requests, 10, 0);
    const endTime = performance.now();

    expect(results).toHaveLength(100);
    expect(endTime - startTime).toBeLessThan(1000); // Should complete within 1 second
  });
});
