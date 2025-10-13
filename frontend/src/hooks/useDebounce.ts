/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Debounce hook for optimizing performance by delaying function execution
 * until after a specified delay has passed since the last invocation
 */

import { useRef, useCallback } from "react";

export const useDebounce = <T extends (...args: any[]) => void>(
  callback: T,
  delay: number
): T => {
  const timeoutRef = useRef<NodeJS.Timeout>();

const debouncedCallback = useCallback(
    (...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    },
    [callback, delay]
  ) as T;

return debouncedCallback;
};

export const useThrottle = <T extends (...args: any[]) => void>(
  callback: T,
  delay: number
): T => {
  const lastExecutedRef = useRef<number>(0);

const throttledCallback = useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      
if (now - lastExecutedRef.current >= delay) {
        lastExecutedRef.current = now;
        
callback(...args);
      }
    },
    [callback, delay]
  ) as T;

return throttledCallback;
};
