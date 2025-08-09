/**
 * Route Utilities
 * Lazy route creation utilities separated for React Fast Refresh
 */

import { lazy } from "react";
import type { LazyRouteModule } from "./performanceUtils";

// Code Splitting Utilities
export const createLazyRoute = (importFn: () => Promise<LazyRouteModule>) => {
  return lazy(() =>
    importFn().catch((error: any) => {
      console.error("Failed to load route:", error);
      return {
        default: () =>
          React.createElement(
            "div",
            { className: "route-error" },
            React.createElement("h2", null, "Failed to load page"),
            React.createElement(
              "p",
              null,
              "Please check your connection and try again."
            ),
            React.createElement(
              "button",
              { onClick: () => window.location.reload() },
              "Retry"
            )
          ),
      };
    })
  );
};
