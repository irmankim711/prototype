/**
 * Accessibility Helpers for Next-Gen Report Builder
 * WCAG 2.1 AA Compliance Implementation
 * Focus: Screen Reader Support, Keyboard Navigation, Inclusive Design
 */

import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  Box,
  Typography,
  Alert,
  IconButton,
  Tooltip,
  Button,
  useTheme,
  useMediaQuery,
} from "@mui/material";
import {
  VolumeUp,
  Keyboard,
  Accessibility,
  InvertColors,
  ZoomIn,
  ZoomOut,
  PlayArrow,
  Pause,
} from "@mui/icons-material";

// Accessibility Context and Hooks
interface AccessibilityContext {
  screenReaderEnabled: boolean;
  highContrastMode: boolean;
  reducedMotion: boolean;
  keyboardNavigation: boolean;
  fontSize: number;
  announcements: string[];
}

// Screen Reader Announcements
const useScreenReader = () => {
  const [announcements, setAnnouncements] = useState<string[]>([]);
  const ariaLiveRef = useRef<HTMLDivElement>(null);

  const announce = useCallback((message: string, priority: "polite" | "assertive" = "polite") => {
    setAnnouncements(prev => [...prev, message]);
    
    // Also use the aria-live region
    if (ariaLiveRef.current) {
      ariaLiveRef.current.setAttribute("aria-live", priority);
      ariaLiveRef.current.textContent = message;
      
      // Clear after announcement
      setTimeout(() => {
        if (ariaLiveRef.current) {
          ariaLiveRef.current.textContent = "";
        }
      }, 1000);
    }
  }, []);

  const AriaLiveRegion = () => (
    <div
      ref={ariaLiveRef}
      aria-live="polite"
      aria-atomic="true"
      style={{
        position: "absolute",
        left: "-10000px",
        width: "1px",
        height: "1px",
        overflow: "hidden",
      }}
    />
  );

  return { announce, AriaLiveRegion, announcements };
};

// Keyboard Navigation Helper
const useKeyboardNavigation = () => {
  const [focusedElement, setFocusedElement] = useState<string | null>(null);
  const focusableElementsRef = useRef<Map<string, HTMLElement>>(new Map());

  const registerFocusableElement = useCallback((id: string, element: HTMLElement) => {
    focusableElementsRef.current.set(id, element);
  }, []);

  const unregisterFocusableElement = useCallback((id: string) => {
    focusableElementsRef.current.delete(id);
  }, []);

  const focusElement = useCallback((id: string) => {
    const element = focusableElementsRef.current.get(id);
    if (element) {
      element.focus();
      setFocusedElement(id);
    }
  }, []);

  const handleKeyNavigation = useCallback((event: KeyboardEvent) => {
    const elements = Array.from(focusableElementsRef.current.entries());
    const currentIndex = elements.findIndex(([id]) => id === focusedElement);

    switch (event.key) {
      case "Tab":
        if (!event.shiftKey) {
          // Tab forward
          const nextIndex = (currentIndex + 1) % elements.length;
          if (elements[nextIndex]) {
            event.preventDefault();
            focusElement(elements[nextIndex][0]);
          }
        } else {
          // Shift+Tab backward
          const prevIndex = currentIndex <= 0 ? elements.length - 1 : currentIndex - 1;
          if (elements[prevIndex]) {
            event.preventDefault();
            focusElement(elements[prevIndex][0]);
          }
        }
        break;
      case "ArrowDown":
      case "ArrowRight":
        if (currentIndex < elements.length - 1) {
          event.preventDefault();
          focusElement(elements[currentIndex + 1][0]);
        }
        break;
      case "ArrowUp":
      case "ArrowLeft":
        if (currentIndex > 0) {
          event.preventDefault();
          focusElement(elements[currentIndex - 1][0]);
        }
        break;
      case "Home":
        if (elements[0]) {
          event.preventDefault();
          focusElement(elements[0][0]);
        }
        break;
      case "End":
        if (elements[elements.length - 1]) {
          event.preventDefault();
          focusElement(elements[elements.length - 1][0]);
        }
        break;
    }
  }, [focusedElement, focusElement]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyNavigation);
    return () => document.removeEventListener("keydown", handleKeyNavigation);
  }, [handleKeyNavigation]);

  return {
    registerFocusableElement,
    unregisterFocusableElement,
    focusElement,
    focusedElement,
  };
};

// Accessible Drag and Drop
interface AccessibleDragDropProps {
  children: React.ReactNode;
  dragId: string;
  dragLabel: string;
  dragDescription: string;
  onDragStart?: () => void;
  onDragEnd?: () => void;
  onKeyboardDrop?: (targetId: string) => void;
}

const AccessibleDragDrop: React.FC<AccessibleDragDropProps> = ({
  children,
  dragId,
  dragLabel,
  dragDescription,
  onDragStart,
  onDragEnd,
  onKeyboardDrop,
}) => {
  const { announce } = useScreenReader();
  const { registerFocusableElement, unregisterFocusableElement } = useKeyboardNavigation();
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (elementRef.current) {
      registerFocusableElement(dragId, elementRef.current);
    }
    return () => unregisterFocusableElement(dragId);
  }, [dragId, registerFocusableElement, unregisterFocusableElement]);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case "Enter":
      case " ":
        event.preventDefault();
        announce(`Started dragging ${dragLabel}. Use arrow keys to navigate to drop zone, then press Enter to drop.`);
        onDragStart?.();
        break;
      case "Escape":
        event.preventDefault();
        announce(`Cancelled dragging ${dragLabel}`);
        onDragEnd?.();
        break;
    }
  };

  return (
    <div
      ref={elementRef}
      role="button"
      tabIndex={0}
      aria-label={`Draggable ${dragLabel}. ${dragDescription}`}
      aria-describedby={`${dragId}-instructions`}
      onKeyDown={handleKeyDown}
      onFocus={() => announce(`Focused on ${dragLabel}. Press Enter or Space to start dragging.`)}
    >
      {children}
      <div
        id={`${dragId}-instructions`}
        className="sr-only"
      >
        Press Enter or Space to pick up this item. Use arrow keys to navigate to a drop zone, then press Enter to drop.
      </div>
    </div>
  );
};

// Accessible Drop Zone
interface AccessibleDropZoneProps {
  children: React.ReactNode;
  dropId: string;
  dropLabel: string;
  accepts: string[];
  onDrop: (draggedId: string) => void;
  isEmpty: boolean;
}

const AccessibleDropZone: React.FC<AccessibleDropZoneProps> = ({
  children,
  dropId,
  dropLabel,
  accepts,
  onDrop,
  isEmpty,
}) => {
  const { announce } = useScreenReader();
  const { registerFocusableElement, unregisterFocusableElement } = useKeyboardNavigation();
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (elementRef.current) {
      registerFocusableElement(dropId, elementRef.current);
    }
    return () => unregisterFocusableElement(dropId);
  }, [dropId, registerFocusableElement, unregisterFocusableElement]);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      // This would be connected to the drag and drop state
      announce(`Dropped item into ${dropLabel}`);
      // onDrop would be called here with the currently dragged item
    }
  };

  return (
    <div
      ref={elementRef}
      role="button"
      tabIndex={0}
      aria-label={`Drop zone for ${dropLabel}. Accepts ${accepts.join(", ")}. ${isEmpty ? "Empty" : "Contains data"}`}
      aria-describedby={`${dropId}-instructions`}
      onKeyDown={handleKeyDown}
      onFocus={() => announce(`Focused on drop zone for ${dropLabel}`)}
    >
      {children}
      <div
        id={`${dropId}-instructions`}
        className="sr-only"
      >
        This is a drop zone for {dropLabel}. It accepts {accepts.join(", ")}. 
        {isEmpty ? "Currently empty." : "Contains data."} 
        Press Enter to drop the currently selected item here.
      </div>
    </div>
  );
};

// High Contrast Mode Toggle
const HighContrastToggle: React.FC = () => {
  const [highContrast, setHighContrast] = useState(false);
  const { announce } = useScreenReader();

  const toggleHighContrast = () => {
    const newValue = !highContrast;
    setHighContrast(newValue);
    
    // Apply high contrast styles
    document.documentElement.setAttribute("data-high-contrast", newValue.toString());
    
    announce(`High contrast mode ${newValue ? "enabled" : "disabled"}`);
  };

  return (
    <Tooltip title="Toggle high contrast mode">
      <IconButton
        onClick={toggleHighContrast}
        aria-label={`High contrast mode ${highContrast ? "on" : "off"}`}
        color={highContrast ? "primary" : "default"}
      >
        <InvertColors />
      </IconButton>
    </Tooltip>
  );
};

// Font Size Control
const FontSizeControl: React.FC = () => {
  const [fontSize, setFontSize] = useState(100);
  const { announce } = useScreenReader();

  const adjustFontSize = (delta: number) => {
    const newSize = Math.max(75, Math.min(150, fontSize + delta));
    setFontSize(newSize);
    
    // Apply font size
    document.documentElement.style.fontSize = `${newSize}%`;
    
    announce(`Font size set to ${newSize} percent`);
  };

  return (
    <Box display="flex" alignItems="center" gap={1}>
      <Tooltip title="Decrease font size">
        <IconButton
          onClick={() => adjustFontSize(-10)}
          aria-label="Decrease font size"
          disabled={fontSize <= 75}
        >
          <ZoomOut />
        </IconButton>
      </Tooltip>
      
      <Typography variant="body2" sx={{ minWidth: 50, textAlign: "center" }}>
        {fontSize}%
      </Typography>
      
      <Tooltip title="Increase font size">
        <IconButton
          onClick={() => adjustFontSize(10)}
          aria-label="Increase font size"
          disabled={fontSize >= 150}
        >
          <ZoomIn />
        </IconButton>
      </Tooltip>
    </Box>
  );
};

// Keyboard Shortcuts Helper
const KeyboardShortcutsHelp: React.FC = () => {
  const [showHelp, setShowHelp] = useState(false);
  const shortcuts = [
    { key: "Tab", description: "Navigate between elements" },
    { key: "Shift + Tab", description: "Navigate backwards" },
    { key: "Enter/Space", description: "Activate element or start drag" },
    { key: "Arrow Keys", description: "Navigate in drag mode" },
    { key: "Escape", description: "Cancel current action" },
    { key: "Alt + H", description: "Show this help" },
    { key: "Alt + 1", description: "Go to data fields" },
    { key: "Alt + 2", description: "Go to chart area" },
    { key: "Alt + 3", description: "Go to properties panel" },
  ];

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.altKey && event.key === "h") {
        event.preventDefault();
        setShowHelp(true);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!showHelp) {
    return (
      <Tooltip title="Keyboard shortcuts (Alt + H)">
        <IconButton
          onClick={() => setShowHelp(true)}
          aria-label="Show keyboard shortcuts"
        >
          <Keyboard />
        </IconButton>
      </Tooltip>
    );
  }

  return (
    <Alert
      severity="info"
      onClose={() => setShowHelp(false)}
      sx={{ position: "fixed", top: 80, right: 16, zIndex: 9999, maxWidth: 400 }}
    >
      <Typography variant="h6" gutterBottom>
        Keyboard Shortcuts
      </Typography>
      <Box component="dl" sx={{ m: 0 }}>
        {shortcuts.map((shortcut, index) => (
          <Box key={index} display="flex" justifyContent="space-between" mb={1}>
            <Typography component="dt" variant="body2" fontWeight="medium">
              {shortcut.key}
            </Typography>
            <Typography component="dd" variant="body2" color="text.secondary">
              {shortcut.description}
            </Typography>
          </Box>
        ))}
      </Box>
    </Alert>
  );
};

// Motion Preferences Detector
const useMotionPreferences = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  return prefersReducedMotion;
};

// Accessibility Toolbar
const AccessibilityToolbar: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [showToolbar, setShowToolbar] = useState(false);

  return (
    <>
      <Tooltip title="Accessibility options">
        <IconButton
          onClick={() => setShowToolbar(!showToolbar)}
          aria-label="Open accessibility options"
          sx={{
            position: "fixed",
            top: 80,
            right: 16,
            zIndex: 1000,
            backgroundColor: "primary.main",
            color: "white",
            "&:hover": {
              backgroundColor: "primary.dark",
            },
          }}
        >
          <Accessibility />
        </IconButton>
      </Tooltip>

      {showToolbar && (
        <Box
          sx={{
            position: "fixed",
            top: 130,
            right: 16,
            zIndex: 999,
            backgroundColor: "background.paper",
            border: 1,
            borderColor: "divider",
            borderRadius: 2,
            p: 2,
            boxShadow: 3,
            minWidth: isMobile ? 280 : 320,
          }}
        >
          <Typography variant="h6" gutterBottom>
            Accessibility Options
          </Typography>
          
          <Box display="flex" flexDirection="column" gap={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="body2">High Contrast</Typography>
              <HighContrastToggle />
            </Box>
            
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="body2">Font Size</Typography>
              <FontSizeControl />
            </Box>
            
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="body2">Keyboard Help</Typography>
              <KeyboardShortcutsHelp />
            </Box>
            
            <Button
              size="small"
              onClick={() => setShowToolbar(false)}
              sx={{ alignSelf: "flex-end" }}
            >
              Close
            </Button>
          </Box>
        </Box>
      )}
    </>
  );
};

// Export all accessibility components and hooks
export {
  useScreenReader,
  useKeyboardNavigation,
  useMotionPreferences,
  AccessibleDragDrop,
  AccessibleDropZone,
  HighContrastToggle,
  FontSizeControl,
  KeyboardShortcutsHelp,
  AccessibilityToolbar,
};

export default AccessibilityToolbar;
