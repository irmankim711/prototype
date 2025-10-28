/**
 * Custom hook for client-side login rate limiting
 * Prevents excessive login attempts before Firebase rate limiting kicks in
 */

import { useState, useCallback, useEffect } from 'react';

interface RateLimitState {
  attempts: number;
  lastAttemptTime: number;
  isLocked: boolean;
  lockoutEndsAt: number | null;
}

interface UseLoginRateLimitReturn {
  canAttemptLogin: boolean;
  remainingAttempts: number;
  lockoutTimeRemaining: number; // in seconds
  recordAttempt: (success: boolean) => void;
  reset: () => void;
  getErrorMessage: () => string | null;
}

const STORAGE_KEY = 'login_rate_limit';
const MAX_ATTEMPTS = 5;
const LOCKOUT_DURATION_MS = 5 * 60 * 1000; // 5 minutes
const ATTEMPT_WINDOW_MS = 15 * 60 * 1000; // 15 minutes - reset counter after this period

export function useLoginRateLimit(): UseLoginRateLimitReturn {
  const [state, setState] = useState<RateLimitState>(() => {
    // Load state from localStorage on mount
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed: RateLimitState = JSON.parse(stored);
        const now = Date.now();

        // Check if lockout has expired
        if (parsed.isLocked && parsed.lockoutEndsAt && now >= parsed.lockoutEndsAt) {
          return {
            attempts: 0,
            lastAttemptTime: 0,
            isLocked: false,
            lockoutEndsAt: null,
          };
        }

        // Check if attempt window has passed (reset counter)
        if (!parsed.isLocked && parsed.lastAttemptTime && (now - parsed.lastAttemptTime) > ATTEMPT_WINDOW_MS) {
          return {
            attempts: 0,
            lastAttemptTime: 0,
            isLocked: false,
            lockoutEndsAt: null,
          };
        }

        return parsed;
      } catch (error) {
        console.error('Failed to parse rate limit state:', error);
      }
    }

    return {
      attempts: 0,
      lastAttemptTime: 0,
      isLocked: false,
      lockoutEndsAt: null,
    };
  });

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  // Auto-update lockout status
  useEffect(() => {
    if (!state.isLocked || !state.lockoutEndsAt) return;

    const now = Date.now();
    const timeRemaining = state.lockoutEndsAt - now;

    if (timeRemaining <= 0) {
      setState({
        attempts: 0,
        lastAttemptTime: 0,
        isLocked: false,
        lockoutEndsAt: null,
      });
      return;
    }

    // Set a timeout to unlock when the lockout period ends
    const timeoutId = setTimeout(() => {
      setState({
        attempts: 0,
        lastAttemptTime: 0,
        isLocked: false,
        lockoutEndsAt: null,
      });
    }, timeRemaining);

    return () => clearTimeout(timeoutId);
  }, [state.isLocked, state.lockoutEndsAt]);

  const recordAttempt = useCallback((success: boolean) => {
    const now = Date.now();

    setState((prevState) => {
      // If locked, don't update
      if (prevState.isLocked) {
        return prevState;
      }

      // If successful, reset everything
      if (success) {
        return {
          attempts: 0,
          lastAttemptTime: 0,
          isLocked: false,
          lockoutEndsAt: null,
        };
      }

      // Failed attempt
      const newAttempts = prevState.attempts + 1;

      // Check if we've hit the limit
      if (newAttempts >= MAX_ATTEMPTS) {
        const lockoutEndsAt = now + LOCKOUT_DURATION_MS;

        // Log security event
        console.warn('[SECURITY] Client-side rate limit triggered', {
          attempts: newAttempts,
          lockoutDuration: LOCKOUT_DURATION_MS / 1000 / 60,
          timestamp: new Date().toISOString(),
        });

        return {
          attempts: newAttempts,
          lastAttemptTime: now,
          isLocked: true,
          lockoutEndsAt,
        };
      }

      return {
        attempts: newAttempts,
        lastAttemptTime: now,
        isLocked: false,
        lockoutEndsAt: null,
      };
    });
  }, []);

  const reset = useCallback(() => {
    setState({
      attempts: 0,
      lastAttemptTime: 0,
      isLocked: false,
      lockoutEndsAt: null,
    });
  }, []);

  const getLockoutTimeRemaining = useCallback((): number => {
    if (!state.isLocked || !state.lockoutEndsAt) return 0;
    const remaining = Math.max(0, state.lockoutEndsAt - Date.now());
    return Math.ceil(remaining / 1000); // Convert to seconds
  }, [state.isLocked, state.lockoutEndsAt]);

  const getErrorMessage = useCallback((): string | null => {
    if (!state.isLocked) {
      // Show warning as they approach the limit
      if (state.attempts >= MAX_ATTEMPTS - 2 && state.attempts < MAX_ATTEMPTS) {
        const remaining = MAX_ATTEMPTS - state.attempts;
        return `Warning: ${remaining} attempt${remaining === 1 ? '' : 's'} remaining before temporary lockout.`;
      }
      return null;
    }

    const timeRemaining = getLockoutTimeRemaining();
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;

    if (minutes > 0) {
      return `Too many failed login attempts. Please wait ${minutes} minute${minutes === 1 ? '' : 's'} ${seconds > 0 ? `and ${seconds} second${seconds === 1 ? '' : 's'}` : ''} before trying again.`;
    } else {
      return `Too many failed login attempts. Please wait ${seconds} second${seconds === 1 ? '' : 's'} before trying again.`;
    }
  }, [state.isLocked, state.attempts, getLockoutTimeRemaining]);

  return {
    canAttemptLogin: !state.isLocked,
    remainingAttempts: Math.max(0, MAX_ATTEMPTS - state.attempts),
    lockoutTimeRemaining: getLockoutTimeRemaining(),
    recordAttempt,
    reset,
    getErrorMessage,
  };
}
