/**
 * Touch Gesture Hooks and Components
 * Advanced touch interaction system for mobile devices
 */

import { useState, useRef, useEffect, useCallback } from "react";

// Touch gesture types
export interface TouchGestureOptions {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  onPinch?: (scale: number) => void;
  onTap?: () => void;
  onDoubleTap?: () => void;
  onLongPress?: () => void;
  threshold?: number;
  longPressDelay?: number;
}

interface TouchPoint {
  x: number;
  y: number;
  timestamp: number;
}

// Touch gesture hook
export const useTouchGestures = (options: TouchGestureOptions) => {
  const elementRef = useRef<HTMLElement>(null);
  const [touchStart, setTouchStart] = useState<TouchPoint | null>(null);
  const [lastTap, setLastTap] = useState<number>(0);
  const [longPressTimer, setLongPressTimer] = useState<NodeJS.Timeout | null>(null);
  const [initialDistance, setInitialDistance] = useState<number>(0);

  const {
    threshold = 50,
    longPressDelay = 500,
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    onPinch,
    onTap,
    onDoubleTap,
    onLongPress
  } = options;

  // Calculate distance between two touch points
  const getDistance = useCallback((touch1: Touch, touch2: Touch): number => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }, []);

  // Handle touch start
  const handleTouchStart = useCallback((e: TouchEvent) => {
    const touch = e.touches[0];
    const now = Date.now();
    
    if (e.touches.length === 1) {
      setTouchStart({
        x: touch.clientX,
        y: touch.clientY,
        timestamp: now
      });

      // Start long press timer
      if (onLongPress) {
        const timer = setTimeout(() => {
          onLongPress();
          // Haptic feedback for long press
          if ('vibrate' in navigator) {
            navigator.vibrate([100, 50, 100]);
          }
        }, longPressDelay);
        setLongPressTimer(timer);
      }
    } else if (e.touches.length === 2 && onPinch) {
      // Start pinch gesture
      const distance = getDistance(e.touches[0], e.touches[1]);
      setInitialDistance(distance);
      
      // Clear single touch data
      setTouchStart(null);
      if (longPressTimer) {
        clearTimeout(longPressTimer);
        setLongPressTimer(null);
      }
    }
  }, [onLongPress, onPinch, longPressDelay, getDistance, longPressTimer]);

  // Handle touch move
  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (e.touches.length === 2 && onPinch && initialDistance > 0) {
      // Handle pinch gesture
      e.preventDefault();
      const currentDistance = getDistance(e.touches[0], e.touches[1]);
      const scale = currentDistance / initialDistance;
      onPinch(scale);
    } else if (touchStart && longPressTimer) {
      // Cancel long press if finger moves too much
      const touch = e.touches[0];
      const deltaX = Math.abs(touch.clientX - touchStart.x);
      const deltaY = Math.abs(touch.clientY - touchStart.y);
      
      if (deltaX > 10 || deltaY > 10) {
        clearTimeout(longPressTimer);
        setLongPressTimer(null);
      }
    }
  }, [onPinch, initialDistance, getDistance, touchStart, longPressTimer]);

  // Handle touch end
  const handleTouchEnd = useCallback((e: TouchEvent) => {
    // Clear long press timer
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }

    if (!touchStart || e.changedTouches.length !== 1) {
      setTouchStart(null);
      setInitialDistance(0);
      return;
    }

    const touchEnd = e.changedTouches[0];
    const deltaX = touchEnd.clientX - touchStart.x;
    const deltaY = touchEnd.clientY - touchStart.y;
    const deltaTime = Date.now() - touchStart.timestamp;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    // Check for swipe gestures
    if (distance > threshold && deltaTime < 500) {
      if (Math.abs(deltaX) > Math.abs(deltaY)) {
        // Horizontal swipe
        if (deltaX > 0) {
          onSwipeRight?.();
        } else {
          onSwipeLeft?.();
        }
      } else {
        // Vertical swipe
        if (deltaY > 0) {
          onSwipeDown?.();
        } else {
          onSwipeUp?.();
        }
      }
      
      // Haptic feedback for swipe
      if ('vibrate' in navigator) {
        navigator.vibrate(50);
      }
    } else if (distance < 10 && deltaTime < 500) {
      // Tap gesture
      const now = Date.now();
      const timeDiff = now - lastTap;
      
      if (timeDiff < 300 && onDoubleTap) {
        // Double tap
        onDoubleTap();
        setLastTap(0);
        
        // Haptic feedback for double tap
        if ('vibrate' in navigator) {
          navigator.vibrate([50, 100, 50]);
        }
      } else if (onTap) {
        // Single tap (delayed to detect double tap)
        setTimeout(() => {
          const currentTime = Date.now();
          if (currentTime - now > 300) {
            onTap();
            
            // Haptic feedback for tap
            if ('vibrate' in navigator) {
              navigator.vibrate(30);
            }
          }
        }, 300);
        setLastTap(now);
      }
    }

    setTouchStart(null);
    setInitialDistance(0);
  }, [touchStart, threshold, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, onTap, onDoubleTap, lastTap, longPressTimer]);

  // Attach event listeners
  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // Add passive: false to prevent scrolling during gestures
    const options = { passive: false };
    
    element.addEventListener('touchstart', handleTouchStart, options);
    element.addEventListener('touchmove', handleTouchMove, options);
    element.addEventListener('touchend', handleTouchEnd, options);

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
      element.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return elementRef;
};

// Pull-to-refresh hook
export interface PullToRefreshOptions {
  onRefresh: () => Promise<void>;
  threshold?: number;
  resistance?: number;
  enabled?: boolean;
}

export const usePullToRefresh = (options: PullToRefreshOptions) => {
  const [isPulling, setIsPulling] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const touchStartY = useRef<number>(0);
  const scrollElement = useRef<HTMLElement | null>(null);

  const {
    onRefresh,
    threshold = 80,
    resistance = 2.5,
    enabled = true
  } = options;

  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (!enabled || isRefreshing) return;
    
    touchStartY.current = e.touches[0].clientY;
  }, [enabled, isRefreshing]);

  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (!enabled || isRefreshing || !scrollElement.current) return;

    const currentY = e.touches[0].clientY;
    const deltaY = currentY - touchStartY.current;
    const scrollTop = scrollElement.current.scrollTop;

    // Only trigger pull-to-refresh at the top of the scroll
    if (scrollTop === 0 && deltaY > 0) {
      e.preventDefault();
      setIsPulling(true);
      
      const distance = Math.min(deltaY / resistance, threshold * 1.5);
      setPullDistance(distance);
    }
  }, [enabled, isRefreshing, threshold, resistance]);

  const handleTouchEnd = useCallback(async () => {
    if (!enabled || isRefreshing || !isPulling) return;

    setIsPulling(false);

    if (pullDistance >= threshold) {
      setIsRefreshing(true);
      setPullDistance(threshold);
      
      // Haptic feedback
      if ('vibrate' in navigator) {
        navigator.vibrate(100);
      }

      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
        setPullDistance(0);
      }
    } else {
      setPullDistance(0);
    }
  }, [enabled, isRefreshing, isPulling, pullDistance, threshold, onRefresh]);

  const containerRef = useCallback((node: HTMLElement | null) => {
    if (node) {
      scrollElement.current = node;
      node.addEventListener('touchstart', handleTouchStart, { passive: false });
      node.addEventListener('touchmove', handleTouchMove, { passive: false });
      node.addEventListener('touchend', handleTouchEnd, { passive: false });
    }

    return () => {
      if (scrollElement.current) {
        scrollElement.current.removeEventListener('touchstart', handleTouchStart);
        scrollElement.current.removeEventListener('touchmove', handleTouchMove);
        scrollElement.current.removeEventListener('touchend', handleTouchEnd);
      }
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return {
    containerRef,
    isPulling,
    isRefreshing,
    pullDistance,
    shouldShowIndicator: pullDistance > 0 || isRefreshing
  };
};

// Device orientation hook
export const useDeviceOrientation = () => {
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    // Check if orientation API is supported
    if (typeof window !== 'undefined' && 'screen' in window && 'orientation' in window.screen) {
      setIsSupported(true);
      
      const updateOrientation = () => {
        const angle = (window.screen.orientation as any)?.angle || window.orientation || 0;
        setOrientation(Math.abs(angle) === 90 ? 'landscape' : 'portrait');
      };

      updateOrientation();
      
      window.addEventListener('orientationchange', updateOrientation);
      return () => window.removeEventListener('orientationchange', updateOrientation);
    } else {
      // Fallback to window dimensions
      const updateOrientation = () => {
        setOrientation(window.innerWidth > window.innerHeight ? 'landscape' : 'portrait');
      };

      updateOrientation();
      
      window.addEventListener('resize', updateOrientation);
      return () => window.removeEventListener('resize', updateOrientation);
    }
  }, []);

  return { orientation, isSupported };
};

// Screen wake lock hook (prevent screen from sleeping)
export const useWakeLock = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [isActive, setIsActive] = useState(false);
  const wakeLockRef = useRef<any>(null);

  useEffect(() => {
    setIsSupported('wakeLock' in navigator);
  }, []);

  const requestWakeLock = useCallback(async () => {
    if (!isSupported || isActive) return false;

    try {
      wakeLockRef.current = await (navigator as any).wakeLock.request('screen');
      setIsActive(true);
      
      wakeLockRef.current.addEventListener('release', () => {
        setIsActive(false);
      });
      
      return true;
    } catch (error) {
      console.warn('Failed to request wake lock:', error);
      return false;
    }
  }, [isSupported, isActive]);

  const releaseWakeLock = useCallback(async () => {
    if (!wakeLockRef.current) return;

    try {
      await wakeLockRef.current.release();
      wakeLockRef.current = null;
      setIsActive(false);
    } catch (error) {
      console.warn('Failed to release wake lock:', error);
    }
  }, []);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (wakeLockRef.current) {
        wakeLockRef.current.release();
      }
    };
  }, []);

  return {
    isSupported,
    isActive,
    requestWakeLock,
    releaseWakeLock
  };
};

// Network status hook
export const useNetworkStatus = () => {
  const [isOnline, setIsOnline] = useState(true);
  const [connectionType, setConnectionType] = useState<string>('unknown');
  const [isSlowConnection, setIsSlowConnection] = useState(false);

  useEffect(() => {
    // Initialize with current status
    setIsOnline(navigator.onLine);

    // Check connection type if available
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    
    if (connection) {
      setConnectionType(connection.effectiveType || 'unknown');
      setIsSlowConnection(connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g');
      
      const handleConnectionChange = () => {
        setConnectionType(connection.effectiveType || 'unknown');
        setIsSlowConnection(connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g');
      };
      
      connection.addEventListener('change', handleConnectionChange);
      
      return () => {
        connection.removeEventListener('change', handleConnectionChange);
      };
    }

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return {
    isOnline,
    connectionType,
    isSlowConnection
  };
};

// Viewport hook for responsive design
export const useViewport = () => {
  const [viewport, setViewport] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
    isMobile: typeof window !== 'undefined' ? window.innerWidth < 768 : false,
    isTablet: typeof window !== 'undefined' ? window.innerWidth >= 768 && window.innerWidth < 1024 : false,
    isDesktop: typeof window !== 'undefined' ? window.innerWidth >= 1024 : false
  });

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      setViewport({
        width,
        height,
        isMobile: width < 768,
        isTablet: width >= 768 && width < 1024,
        isDesktop: width >= 1024
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return viewport;
};

// Safe area insets hook for devices with notches
export const useSafeAreaInsets = () => {
  const [insets, setInsets] = useState({
    top: 0,
    right: 0,
    bottom: 0,
    left: 0
  });

  useEffect(() => {
    const updateInsets = () => {
      const computedStyle = getComputedStyle(document.documentElement);
      
      setInsets({
        top: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-top)') || '0', 10),
        right: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-right)') || '0', 10),
        bottom: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-bottom)') || '0', 10),
        left: parseInt(computedStyle.getPropertyValue('env(safe-area-inset-left)') || '0', 10)
      });
    };

    updateInsets();
    
    // Update on orientation change
    window.addEventListener('orientationchange', updateInsets);
    return () => window.removeEventListener('orientationchange', updateInsets);
  }, []);

  return insets;
};
