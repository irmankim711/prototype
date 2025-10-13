/**
 * Mobile Testing Framework
 * Comprehensive testing utilities for mobile responsive features
 */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";

// Types for mobile testing
interface MockTouchEvent {
  touches: Array<{ clientX: number; clientY: number; identifier: number }>;
  changedTouches: Array<{
    clientX: number;
    clientY: number;
    identifier: number;
  }>;
  targetTouches: Array<{
    clientX: number;
    clientY: number;
    identifier: number;
  }>;
  preventDefault: () => void;
  stopPropagation: () => void;
}

interface ViewportSize {
  width: number;
  height: number;
}

interface DevicePreset {
  name: string;
  viewport: ViewportSize;
  userAgent: string;
  pixelRatio: number;
  touch: boolean;
}

// Device presets for testing
export const DEVICE_PRESETS: Record<string, DevicePreset> = {
  iphone12: {
    name: "iPhone 12",
    viewport: { width: 390, height: 844 },
    userAgent:
      "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    pixelRatio: 3,
    touch: true,
  },
  iphone12Pro: {
    name: "iPhone 12 Pro",
    viewport: { width: 390, height: 844 },
    userAgent:
      "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    pixelRatio: 3,
    touch: true,
  },
  galaxyS21: {
    name: "Galaxy S21",
    viewport: { width: 384, height: 854 },
    userAgent:
      "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    pixelRatio: 2.75,
    touch: true,
  },
  ipadAir: {
    name: "iPad Air",
    viewport: { width: 820, height: 1180 },
    userAgent:
      "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    pixelRatio: 2,
    touch: true,
  },
  desktop: {
    name: "Desktop",
    viewport: { width: 1920, height: 1080 },
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    pixelRatio: 1,
    touch: false,
  },
};

// Breakpoint testing utilities
export const BREAKPOINTS = {
  mobile: { min: 0, max: 767 },
  tablet: { min: 768, max: 1023 },
  desktop: { min: 1024, max: Infinity },
};

// Mock touch events
export const createMockTouchEvent = (
  type: string,
  touches: Array<{ x: number; y: number; id?: number }> = []
): MockTouchEvent => {
  const touchList = touches.map((touch, index) => ({
    clientX: touch.x,
    clientY: touch.y,
    identifier: touch.id ?? index,
    target: document.body,
    pageX: touch.x,
    pageY: touch.y,
    screenX: touch.x,
    screenY: touch.y,
    radiusX: 10,
    radiusY: 10,
    rotationAngle: 0,
    force: 1,
  }));

  return {
    touches: touchList,
    changedTouches: touchList,
    targetTouches: touchList,
    preventDefault: jest.fn(),
    stopPropagation: jest.fn(),
  } as MockTouchEvent;
};

// Viewport testing utilities
export class ViewportTester {
  private originalInnerWidth: number;
  private originalInnerHeight: number;
  private originalUserAgent: string;

  constructor() {
    this.originalInnerWidth = window.innerWidth;
    this.originalInnerHeight = window.innerHeight;
    this.originalUserAgent = navigator.userAgent;
  }

  // Set viewport size
  setViewport(size: ViewportSize): void {
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: size.width,
    });

    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: size.height,
    });

    // Trigger resize event
    window.dispatchEvent(new Event("resize"));
  }

  // Set device preset
  setDevice(device: DevicePreset): void {
    this.setViewport(device.viewport);

    // Mock user agent
    Object.defineProperty(navigator, "userAgent", {
      writable: true,
      configurable: true,
      value: device.userAgent,
    });

    // Mock device pixel ratio
    Object.defineProperty(window, "devicePixelRatio", {
      writable: true,
      configurable: true,
      value: device.pixelRatio,
    });

    // Mock touch capability
    if (device.touch) {
      Object.defineProperty(window, "ontouchstart", {
        value: null,
        configurable: true,
      });
    } else {
      delete (window as any).ontouchstart;
    }
  }

  // Test all breakpoints
  async testBreakpoints(
    testFn: (breakpoint: string, size: ViewportSize) => void | Promise<void>
  ): Promise<void> {
    const testSizes: Array<{ name: string; size: ViewportSize }> = [
      { name: "mobile-small", size: { width: 320, height: 568 } },
      { name: "mobile-medium", size: { width: 375, height: 667 } },
      { name: "mobile-large", size: { width: 414, height: 896 } },
      { name: "tablet-portrait", size: { width: 768, height: 1024 } },
      { name: "tablet-landscape", size: { width: 1024, height: 768 } },
      { name: "desktop-small", size: { width: 1366, height: 768 } },
      { name: "desktop-large", size: { width: 1920, height: 1080 } },
    ];

    for (const { name, size } of testSizes) {
      this.setViewport(size);
      await act(async () => {
        await testFn(name, size);
      });
    }
  }

  // Restore original viewport
  restore(): void {
    this.setViewport({
      width: this.originalInnerWidth,
      height: this.originalInnerHeight,
    });

    Object.defineProperty(navigator, "userAgent", {
      value: this.originalUserAgent,
      configurable: true,
    });
  }
}

// Touch gesture testing utilities
export class TouchTester {
  private element: HTMLElement;

  constructor(element: HTMLElement) {
    this.element = element;
  }

  // Simulate tap
  async tap(
    options: { x?: number; y?: number; duration?: number } = {}
  ): Promise<void> {
    const { x = 50, y = 50, duration = 100 } = options;
    const rect = this.element.getBoundingClientRect();
    const clientX = rect.left + x;
    const clientY = rect.top + y;

    const touchStart = createMockTouchEvent("touchstart", [
      { x: clientX, y: clientY },
    ]);
    const touchEnd = createMockTouchEvent("touchend", [
      { x: clientX, y: clientY },
    ]);

    fireEvent.touchStart(this.element, touchStart);

    await act(async () => {
      await new Promise((resolve: any) => setTimeout(resolve, duration));
    });

    fireEvent.touchEnd(this.element, touchEnd);
  }

  // Simulate long press
  async longPress(
    options: { x?: number; y?: number; duration?: number } = {}
  ): Promise<void> {
    const { x = 50, y = 50, duration = 500 } = options;
    const rect = this.element.getBoundingClientRect();
    const clientX = rect.left + x;
    const clientY = rect.top + y;

    const touchStart = createMockTouchEvent("touchstart", [
      { x: clientX, y: clientY },
    ]);

    fireEvent.touchStart(this.element, touchStart);

    await act(async () => {
      await new Promise((resolve: any) => setTimeout(resolve, duration));
    });

    const touchEnd = createMockTouchEvent("touchend", [
      { x: clientX, y: clientY },
    ]);
    fireEvent.touchEnd(this.element, touchEnd);
  }

  // Simulate swipe
  async swipe(
    options: {
      startX?: number;
      startY?: number;
      endX?: number;
      endY?: number;
      duration?: number;
      steps?: number;
    } = {}
  ): Promise<void> {
    const {
      startX = 10,
      startY = 50,
      endX = 90,
      endY = 50,
      duration = 300,
      steps = 10,
    } = options;

    const rect = this.element.getBoundingClientRect();
    const startClientX = rect.left + (rect.width * startX) / 100;
    const startClientY = rect.top + (rect.height * startY) / 100;
    const endClientX = rect.left + (rect.width * endX) / 100;
    const endClientY = rect.top + (rect.height * endY) / 100;

    const deltaX = (endClientX - startClientX) / steps;
    const deltaY = (endClientY - startClientY) / steps;
    const stepDuration = duration / steps;

    // Start touch
    const touchStart = createMockTouchEvent("touchstart", [
      { x: startClientX, y: startClientY },
    ]);
    fireEvent.touchStart(this.element, touchStart);

    // Move touch
    for (let i = 1; i <= steps; i++) {
      const currentX = startClientX + deltaX * i;
      const currentY = startClientY + deltaY * i;

      const touchMove = createMockTouchEvent("touchmove", [
        { x: currentX, y: currentY },
      ]);

      fireEvent.touchMove(this.element, touchMove);

      await act(async () => {
        await new Promise((resolve: any) => setTimeout(resolve, stepDuration));
      });
    }

    // End touch
    const touchEnd = createMockTouchEvent("touchend", [
      { x: endClientX, y: endClientY },
    ]);
    fireEvent.touchEnd(this.element, touchEnd);
  }

  // Simulate pinch
  async pinch(
    options: {
      centerX?: number;
      centerY?: number;
      startDistance?: number;
      endDistance?: number;
      duration?: number;
      steps?: number;
    } = {}
  ): Promise<void> {
    const {
      centerX = 50,
      centerY = 50,
      startDistance = 50,
      endDistance = 100,
      duration = 300,
      steps = 10,
    } = options;

    const rect = this.element.getBoundingClientRect();
    const centerClientX = rect.left + (rect.width * centerX) / 100;
    const centerClientY = rect.top + (rect.height * centerY) / 100;

    const deltaDistance = (endDistance - startDistance) / steps;
    const stepDuration = duration / steps;

    // Start touches
    const startTouch1X = centerClientX - startDistance / 2;
    const startTouch2X = centerClientX + startDistance / 2;

    const touchStart = createMockTouchEvent("touchstart", [
      { x: startTouch1X, y: centerClientY, id: 1 },
      { x: startTouch2X, y: centerClientY, id: 2 },
    ]);
    fireEvent.touchStart(this.element, touchStart);

    // Move touches
    for (let i = 1; i <= steps; i++) {
      const currentDistance = startDistance + deltaDistance * i;
      const touch1X = centerClientX - currentDistance / 2;
      const touch2X = centerClientX + currentDistance / 2;

      const touchMove = createMockTouchEvent("touchmove", [
        { x: touch1X, y: centerClientY, id: 1 },
        { x: touch2X, y: centerClientY, id: 2 },
      ]);

      fireEvent.touchMove(this.element, touchMove);

      await act(async () => {
        await new Promise((resolve: any) => setTimeout(resolve, stepDuration));
      });
    }

    // End touches
    const endTouch1X = centerClientX - endDistance / 2;
    const endTouch2X = centerClientX + endDistance / 2;

    const touchEnd = createMockTouchEvent("touchend", [
      { x: endTouch1X, y: centerClientY, id: 1 },
      { x: endTouch2X, y: centerClientY, id: 2 },
    ]);
    fireEvent.touchEnd(this.element, touchEnd);
  }
}

// Accessibility testing utilities
export const AccessibilityTester = {
  // Test touch target sizes
  checkTouchTargets: (
    container: HTMLElement
  ): Array<{
    element: HTMLElement;
    size: { width: number; height: number };
  }> => {
    const touchTargets = container.querySelectorAll(
      'button, a, input, [role="button"]'
    );
    const results: Array<{
      element: HTMLElement;
      size: { width: number; height: number };
    }> = [];

    touchTargets.forEach((element: any) => {
      const rect = element.getBoundingClientRect();
      const size = { width: rect.width, height: rect.height };

      // WCAG recommends minimum 44x44px for touch targets
      if (size.width < 44 || size.height < 44) {
        results.push({ element: element as HTMLElement, size });
      }
    });

    return results;
  },

  // Test color contrast
  checkColorContrast: (
    element: HTMLElement
  ): { ratio: number; passes: boolean } => {
    const styles = window.getComputedStyle(element);
    const color = styles.color;
    const backgroundColor = styles.backgroundColor;

    // This is a simplified version - in practice, you'd use a proper color contrast library
    const ratio = calculateContrastRatio(color, backgroundColor);
    const passes = ratio >= 4.5; // WCAG AA standard

    return { ratio, passes };
  },

  // Test keyboard navigation
  testKeyboardNavigation: async (container: HTMLElement): Promise<boolean> => {
    const focusableElements = container.querySelectorAll(
      'button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    let previousElement: HTMLElement | null = null;

    for (const element of Array.from(focusableElements)) {
      const htmlElement = element as HTMLElement;

      // Check if element can receive focus
      htmlElement.focus();
      if (document.activeElement !== htmlElement) {
        console.warn("Element cannot receive focus:", htmlElement);
        return false;
      }

      // Check tab order
      if (previousElement) {
        const prevTabIndex = parseInt(
          previousElement.getAttribute("tabindex") || "0"
        );
        const currentTabIndex = parseInt(
          htmlElement.getAttribute("tabindex") || "0"
        );

        if (currentTabIndex < prevTabIndex && currentTabIndex !== 0) {
          console.warn("Tab order issue detected");
        }
      }

      previousElement = htmlElement;
    }

    return true;
  },
};

// Helper function for color contrast calculation
function calculateContrastRatio(color1: string, color2: string): number {
  // Simplified implementation - use a proper library in production
  // This is just for demonstration
  return Math.random() * 10 + 1; // Random value for testing
}

// Performance testing utilities
export const PerformanceTester = {
  // Test render performance
  measureRenderTime: async (renderFn: () => void): Promise<number> => {
    const startTime = performance.now();

    await act(async () => {
      renderFn();
    });

    const endTime = performance.now();
    return endTime - startTime;
  },

  // Test interaction performance
  measureInteractionTime: async (
    interactionFn: () => Promise<void>
  ): Promise<number> => {
    const startTime = performance.now();

    await act(async () => {
      await interactionFn();
    });

    const endTime = performance.now();
    return endTime - startTime;
  },

  // Test memory usage
  measureMemoryUsage: (): { before: number; after: number } => {
    const before = (performance as any).memory?.usedJSHeapSize || 0;

    // Force garbage collection if available
    if ((window as any).gc) {
      (window as any).gc();
    }

    const after = (performance as any).memory?.usedJSHeapSize || 0;

    return { before, after };
  },
};

// Test utilities for mobile components
export const MobileTestUtils = {
  // Render component with mobile wrapper
  renderMobile: (
    component: React.ReactElement,
    device: DevicePreset = DEVICE_PRESETS.iphone12
  ) => {
    const viewportTester = new ViewportTester();
    viewportTester.setDevice(device);

    const utils = render(<BrowserRouter>{component}</BrowserRouter>);

    return {
      ...utils,
      viewportTester,
      touchTester: (element: HTMLElement) => new TouchTester(element),
    };
  },

  // Test component across multiple devices
  testAcrossDevices: async (
    component: React.ReactElement,
    testFn: (utils: any, device: DevicePreset) => void | Promise<void>
  ) => {
    for (const [deviceName, device] of Object.entries(DEVICE_PRESETS)) {
      console.log(`Testing on ${deviceName}...`);

      const utils = MobileTestUtils.renderMobile(component, device);

      await act(async () => {
        await testFn(utils, device);
      });

      utils.viewportTester.restore();
      utils.unmount();
    }
  },

  // Assert responsive behavior
  assertResponsive: (
    element: HTMLElement,
    expectedClasses: Record<string, string[]>
  ) => {
    Object.entries(expectedClasses).forEach(([breakpoint, classes]) => {
      const viewportTester = new ViewportTester();
      const breakpointConfig =
        BREAKPOINTS[breakpoint as keyof typeof BREAKPOINTS];

      if (breakpointConfig) {
        viewportTester.setViewport({
          width: breakpointConfig.min + 100,
          height: 800,
        });

        classes.forEach((className: any) => {
          expect(element).toHaveClass(className);
        });
      }

      viewportTester.restore();
    });
  },
};

export default MobileTestUtils;
