// Enhanced Dashboard Type Definitions

declare module "*.css" {
  const content: Record<string, string>;
  export default content;
}

interface Window {
  // Enhanced dashboard globals
  __DASHBOARD_DEBUG__?: boolean;
  __PERFORMANCE_OBSERVER__?: PerformanceObserver;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  gtag?: (...args: any[]) => void;
}

// Chart.js module augmentation
declare module "chart.js" {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  interface TooltipModel {
    // Add any custom tooltip properties when needed
  }
}

// Lodash module augmentation
declare module "lodash" {
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  interface LoDashStatic {
    // Add any custom lodash methods when needed
  }
}
