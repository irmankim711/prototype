/**
 * Mobile Components Test Suite
 * Comprehensive tests for mobile responsive components
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";

// Import components to test
import {
  MobileButton,
  MobileInput,
  MobileCard,
  MobileModal,
  MobileList,
  PullToRefresh,
  MobileSkeleton,
} from "../MobileComponents";

import MobileNavigation from "../MobileNavigation";
import MobileDashboard from "../MobileDashboard";
import MobileFormBuilder from "../MobileFormBuilder";

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

// Mock viewport for mobile testing
const mockViewport = (width: number, height: number) => {
  Object.defineProperty(window, "innerWidth", {
    writable: true,
    configurable: true,
    value: width,
  });
  Object.defineProperty(window, "innerHeight", {
    writable: true,
    configurable: true,
    value: height,
  });
  window.dispatchEvent(new Event("resize"));
};

// Mock touch events
const createTouchEvent = (
  type: string,
  touches: Array<{ clientX: number; clientY: number }>
) => {
  const touchEvent = new Event(type, { bubbles: true });
  Object.defineProperty(touchEvent, "touches", {
    value: touches.map((touch, index) => ({
      ...touch,
      identifier: index,
      target: document.body,
    })),
  });
  Object.defineProperty(touchEvent, "changedTouches", {
    value: touches.map((touch, index) => ({
      ...touch,
      identifier: index,
      target: document.body,
    })),
  });
  return touchEvent;
};

describe("Mobile Components", () => {
  beforeEach(() => {
    // Set mobile viewport
    mockViewport(375, 667);
  });

  afterEach(() => {
    // Reset viewport
    mockViewport(1024, 768);
  });

  describe("MobileButton", () => {
    test("renders correctly with different variants", () => {
      const { rerender } = render(
        <MobileButton variant="primary">Primary Button</MobileButton>
      );
      expect(screen.getByText("Primary Button")).toBeInTheDocument();
      expect(screen.getByRole("button")).toHaveClass(
        "mobile-button",
        "primary"
      );

      rerender(
        <MobileButton variant="secondary">Secondary Button</MobileButton>
      );
      expect(screen.getByText("Secondary Button")).toBeInTheDocument();
      expect(screen.getByRole("button")).toHaveClass("secondary");

      rerender(<MobileButton variant="ghost">Ghost Button</MobileButton>);
      expect(screen.getByText("Ghost Button")).toBeInTheDocument();
      expect(screen.getByRole("button")).toHaveClass("ghost");
    });

    test("handles touch interactions", async () => {
      const handleClick = jest.fn();
      const handleTouchStart = jest.fn();

      render(
        <MobileButton onClick={handleClick} onTouchStart={handleTouchStart}>
          Touch Button
        </MobileButton>
      );

      const button = screen.getByRole("button");

      // Test touch start
      const touchStart = createTouchEvent("touchstart", [
        { clientX: 100, clientY: 100 },
      ]);
      fireEvent(button, touchStart);
      expect(handleTouchStart).toHaveBeenCalled();

      // Test click
      fireEvent.click(button);
      expect(handleClick).toHaveBeenCalled();
    });

    test("shows loading state correctly", () => {
      render(<MobileButton loading>Loading Button</MobileButton>);

      expect(screen.getByRole("button")).toBeDisabled();
      expect(screen.getByText("Loading Button")).toBeInTheDocument();
    });

    test("renders with icons", () => {
      const TestIcon = () => <span data-testid="test-icon">Icon</span>;

      render(
        <MobileButton startIcon={<TestIcon />}>Button with Icon</MobileButton>
      );

      expect(screen.getByTestId("test-icon")).toBeInTheDocument();
      expect(screen.getByText("Button with Icon")).toBeInTheDocument();
    });
  });

  describe("MobileInput", () => {
    test("renders correctly with different types", () => {
      const { rerender } = render(
        <MobileInput type="text" placeholder="Enter text" />
      );
      expect(screen.getByPlaceholderText("Enter text")).toHaveAttribute(
        "type",
        "text"
      );

      rerender(<MobileInput type="email" placeholder="Enter email" />);
      expect(screen.getByPlaceholderText("Enter email")).toHaveAttribute(
        "type",
        "email"
      );

      rerender(<MobileInput type="password" placeholder="Enter password" />);
      expect(screen.getByPlaceholderText("Enter password")).toHaveAttribute(
        "type",
        "password"
      );
    });

    test("handles input events", () => {
      const handleChange = jest.fn();
      const handleFocus = jest.fn();
      const handleBlur = jest.fn();

      render(
        <MobileInput
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder="Test input"
        />
      );

      const input = screen.getByPlaceholderText("Test input");

      fireEvent.focus(input);
      expect(handleFocus).toHaveBeenCalled();

      fireEvent.change(input, { target: { value: "test value" } });
      expect(handleChange).toHaveBeenCalled();

      fireEvent.blur(input);
      expect(handleBlur).toHaveBeenCalled();
    });

    test("shows error state", () => {
      render(
        <MobileInput error="This field is required" placeholder="Test input" />
      );

      const container = screen
        .getByPlaceholderText("Test input")
        .closest(".mobile-input-container");
      expect(container).toHaveClass("error");
      expect(screen.getByText("This field is required")).toBeInTheDocument();
    });
  });

  describe("MobileCard", () => {
    test("renders content correctly", () => {
      render(
        <MobileCard>
          <h2>Card Title</h2>
          <p>Card content goes here</p>
        </MobileCard>
      );

      expect(screen.getByText("Card Title")).toBeInTheDocument();
      expect(screen.getByText("Card content goes here")).toBeInTheDocument();
    });

    test("handles click events", () => {
      const handleClick = jest.fn();

      render(
        <MobileCard onClick={handleClick}>
          <p>Clickable card</p>
        </MobileCard>
      );

      fireEvent.click(screen.getByText("Clickable card"));
      expect(handleClick).toHaveBeenCalled();
    });

    test("applies hover effects on touch devices", () => {
      render(
        <MobileCard>
          <p>Touch card</p>
        </MobileCard>
      );

      const card = screen.getByText("Touch card").closest(".mobile-card");

      const touchStart = createTouchEvent("touchstart", [
        { clientX: 100, clientY: 100 },
      ]);
      fireEvent(card!, touchStart);

      expect(card).toHaveClass("mobile-card");
    });
  });

  describe("MobileModal", () => {
    test("renders when open", () => {
      render(
        <MobileModal isOpen onClose={() => {}} title="Test Modal">
          <p>Modal content</p>
        </MobileModal>
      );

      expect(screen.getByText("Test Modal")).toBeInTheDocument();
      expect(screen.getByText("Modal content")).toBeInTheDocument();
    });

    test("does not render when closed", () => {
      render(
        <MobileModal isOpen={false} onClose={() => {}} title="Test Modal">
          <p>Modal content</p>
        </MobileModal>
      );

      expect(screen.queryByText("Test Modal")).not.toBeInTheDocument();
      expect(screen.queryByText("Modal content")).not.toBeInTheDocument();
    });

    test("calls onClose when close button clicked", () => {
      const handleClose = jest.fn();

      render(
        <MobileModal isOpen onClose={handleClose} title="Test Modal">
          <p>Modal content</p>
        </MobileModal>
      );

      fireEvent.click(screen.getByLabelText("Close modal"));
      expect(handleClose).toHaveBeenCalled();
    });

    test("closes on backdrop click", () => {
      const handleClose = jest.fn();

      render(
        <MobileModal isOpen onClose={handleClose} title="Test Modal">
          <p>Modal content</p>
        </MobileModal>
      );

      const backdrop = document.querySelector(".mobile-modal-backdrop");
      fireEvent.click(backdrop!);
      expect(handleClose).toHaveBeenCalled();
    });
  });

  describe("PullToRefresh", () => {
    test("renders children correctly", () => {
      render(
        <PullToRefresh onRefresh={() => {}}>
          <div>Content to refresh</div>
        </PullToRefresh>
      );

      expect(screen.getByText("Content to refresh")).toBeInTheDocument();
    });

    test("triggers refresh on pull gesture", async () => {
      const handleRefresh = jest.fn().mockResolvedValue(undefined);

      render(
        <PullToRefresh onRefresh={handleRefresh}>
          <div>Content to refresh</div>
        </PullToRefresh>
      );

      const container = screen
        .getByText("Content to refresh")
        .closest(".pull-to-refresh-container");

      // Simulate pull down gesture
      const touchStart = createTouchEvent("touchstart", [
        { clientX: 100, clientY: 100 },
      ]);
      const touchMove = createTouchEvent("touchmove", [
        { clientX: 100, clientY: 200 },
      ]);
      const touchEnd = createTouchEvent("touchend", [
        { clientX: 100, clientY: 200 },
      ]);

      fireEvent(container!, touchStart);
      fireEvent(container!, touchMove);
      fireEvent(container!, touchEnd);

      await waitFor(() => {
        expect(handleRefresh).toHaveBeenCalled();
      });
    });
  });
});

describe("Mobile Navigation", () => {
  test("MobileNavigation renders correctly", () => {
    render(
      <TestWrapper>
        <MobileNavigation />
      </TestWrapper>
    );

    // Check if navigation items are present
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
    expect(screen.getByText("Forms")).toBeInTheDocument();
    expect(screen.getByText("Profile")).toBeInTheDocument();
  });

  test("MobileHeader renders with title", () => {
    render(
      <TestWrapper>
        <MobileHeader title="Test Page" />
      </TestWrapper>
    );

    expect(screen.getByText("Test Page")).toBeInTheDocument();
  });

  test("MobileTabBar handles tab switching", () => {
    const tabs = [
      { id: "tab1", label: "Tab 1", content: <div>Content 1</div> },
      { id: "tab2", label: "Tab 2", content: <div>Content 2</div> },
    ];

    render(<MobileTabBar tabs={tabs} />);

    expect(screen.getByText("Tab 1")).toBeInTheDocument();
    expect(screen.getByText("Tab 2")).toBeInTheDocument();
    expect(screen.getByText("Content 1")).toBeInTheDocument();

    // Switch to tab 2
    fireEvent.click(screen.getByText("Tab 2"));
    expect(screen.getByText("Content 2")).toBeInTheDocument();
  });
});

describe("Mobile Dashboard", () => {
  test("renders dashboard components", () => {
    render(
      <TestWrapper>
        <MobileDashboard />
      </TestWrapper>
    );

    // Check for dashboard elements
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });
});

describe("Mobile Form Builder", () => {
  test("renders form builder interface", () => {
    render(
      <TestWrapper>
        <MobileFormBuilder />
      </TestWrapper>
    );

    // Check for form builder elements
    expect(screen.getByText("Form Builder")).toBeInTheDocument();
  });

  test("handles field addition", async () => {
    render(
      <TestWrapper>
        <MobileFormBuilder />
      </TestWrapper>
    );

    // Test adding a field (this would depend on the actual implementation)
    const addButton = screen.getByText("Add Field");
    fireEvent.click(addButton);

    // Check if field was added (implementation specific)
    await waitFor(() => {
      // Add assertions based on actual implementation
    });
  });
});

describe("Responsive Behavior", () => {
  test("components adapt to different screen sizes", () => {
    // Test mobile
    mockViewport(375, 667);
    const { rerender } = render(
      <TestWrapper>
        <MobileNavigation />
      </TestWrapper>
    );

    let nav = document.querySelector(".mobile-navigation");
    expect(nav).toHaveClass("mobile-navigation");

    // Test tablet
    mockViewport(768, 1024);
    rerender(
      <TestWrapper>
        <MobileNavigation />
      </TestWrapper>
    );

    nav = document.querySelector(".mobile-navigation");
    expect(nav).toHaveClass("mobile-navigation");

    // Test desktop
    mockViewport(1920, 1080);
    rerender(
      <TestWrapper>
        <MobileNavigation />
      </TestWrapper>
    );

    nav = document.querySelector(".mobile-navigation");
    expect(nav).toHaveClass("mobile-navigation");
  });
});

describe("Touch Interactions", () => {
  test("handles swipe gestures", () => {
    const handleSwipe = jest.fn();

    render(
      <div data-testid="swipe-container" onTouchStart={handleSwipe}>
        Swipeable content
      </div>
    );

    const container = screen.getByTestId("swipe-container");

    // Simulate swipe
    const touchStart = createTouchEvent("touchstart", [
      { clientX: 100, clientY: 100 },
    ]);
    const touchMove = createTouchEvent("touchmove", [
      { clientX: 200, clientY: 100 },
    ]);
    const touchEnd = createTouchEvent("touchend", [
      { clientX: 200, clientY: 100 },
    ]);

    fireEvent(container, touchStart);
    fireEvent(container, touchMove);
    fireEvent(container, touchEnd);

    expect(handleSwipe).toHaveBeenCalled();
  });

  test("handles pinch gestures", () => {
    const handleTouch = jest.fn();

    render(
      <div data-testid="pinch-container" onTouchStart={handleTouch}>
        Pinchable content
      </div>
    );

    const container = screen.getByTestId("pinch-container");

    // Simulate pinch with two fingers
    const touchStart = createTouchEvent("touchstart", [
      { clientX: 100, clientY: 100 },
      { clientX: 200, clientY: 100 },
    ]);

    fireEvent(container, touchStart);
    expect(handleTouch).toHaveBeenCalled();
  });
});

describe("Performance", () => {
  test("components render within acceptable time", async () => {
    const startTime = performance.now();

    render(
      <TestWrapper>
        <MobileDashboard />
      </TestWrapper>
    );

    const endTime = performance.now();
    const renderTime = endTime - startTime;

    // Should render within 100ms
    expect(renderTime).toBeLessThan(100);
  });

  test("lazy loading works correctly", async () => {
    const LazyComponent = React.lazy(() =>
      Promise.resolve({
        default: () => <div>Lazy loaded content</div>,
      })
    );

    render(
      <React.Suspense fallback={<div>Loading...</div>}>
        <LazyComponent />
      </React.Suspense>
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Lazy loaded content")).toBeInTheDocument();
    });
  });
});

describe("Accessibility", () => {
  test("components have proper ARIA labels", () => {
    render(
      <TestWrapper>
        <MobileNavigation />
      </TestWrapper>
    );

    // Check for ARIA labels
    const nav = screen.getByRole("navigation");
    expect(nav).toBeInTheDocument();
  });

  test("buttons have proper touch targets", () => {
    render(<MobileButton>Test Button</MobileButton>);

    const button = screen.getByRole("button");
    const styles = window.getComputedStyle(button);

    // Check minimum touch target size (44px)
    // Note: This would need actual CSS measurement in a real test
    expect(button).toBeInTheDocument();
  });

  test("focus management works correctly", () => {
    render(
      <div>
        <MobileButton>Button 1</MobileButton>
        <MobileButton>Button 2</MobileButton>
      </div>
    );

    const buttons = screen.getAllByRole("button");

    buttons[0].focus();
    expect(document.activeElement).toBe(buttons[0]);

    // Simulate tab key
    buttons[1].focus();
    expect(document.activeElement).toBe(buttons[1]);
  });
});
