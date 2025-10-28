/**
 * Rate Limit Alert Component
 * Displays user-friendly messages when rate limiting is active
 */

import React, { useState, useEffect } from 'react';

interface RateLimitAlertProps {
  isLocked: boolean;
  lockoutTimeRemaining: number; // in seconds
  remainingAttempts: number;
  warningMessage?: string | null;
  onResetPassword?: () => void;
  onGoogleSignIn?: () => void;
  className?: string;
}

export const RateLimitAlert: React.FC<RateLimitAlertProps> = ({
  isLocked,
  lockoutTimeRemaining,
  remainingAttempts,
  warningMessage,
  onResetPassword,
  onGoogleSignIn,
  className = '',
}) => {
  const [timeRemaining, setTimeRemaining] = useState(lockoutTimeRemaining);

  // Update countdown timer
  useEffect(() => {
    setTimeRemaining(lockoutTimeRemaining);

    if (lockoutTimeRemaining <= 0) return;

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [lockoutTimeRemaining]);

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;

    if (minutes > 0) {
      return `${minutes} minute${minutes === 1 ? '' : 's'}${secs > 0 ? ` ${secs} second${secs === 1 ? '' : 's'}` : ''}`;
    }
    return `${secs} second${secs === 1 ? '' : 's'}`;
  };

  if (isLocked) {
    return (
      <div
        className={`bg-red-50 border-l-4 border-red-500 p-4 rounded-md ${className}`}
        role="alert"
      >
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-red-400"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium text-red-800">
              Account Temporarily Locked
            </h3>
            <div className="mt-2 text-sm text-red-700">
              <p>
                Too many failed login attempts. For security, this account is
                temporarily locked.
              </p>
              {timeRemaining > 0 && (
                <p className="mt-2 font-semibold">
                  Time remaining: {formatTime(timeRemaining)}
                </p>
              )}
              <div className="mt-4">
                <p className="font-medium">What you can do:</p>
                <ul className="list-disc list-inside mt-2 space-y-1">
                  <li>Wait for the lockout period to end</li>
                  {onResetPassword && (
                    <li>
                      <button
                        onClick={onResetPassword}
                        className="text-red-800 underline hover:text-red-900 font-medium"
                      >
                        Reset your password
                      </button>{' '}
                      to regain access immediately
                    </li>
                  )}
                  {onGoogleSignIn && (
                    <li>
                      <button
                        onClick={onGoogleSignIn}
                        className="text-red-800 underline hover:text-red-900 font-medium"
                      >
                        Sign in with Google
                      </button>{' '}
                      instead
                    </li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (warningMessage && remainingAttempts <= 2) {
    return (
      <div
        className={`bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-md ${className}`}
        role="alert"
      >
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-yellow-400"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              <span className="font-medium">Warning:</span> {warningMessage}
            </p>
            {onResetPassword && (
              <p className="mt-2 text-sm text-yellow-700">
                Forgot your password?{' '}
                <button
                  onClick={onResetPassword}
                  className="text-yellow-800 underline hover:text-yellow-900 font-medium"
                >
                  Reset it here
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default RateLimitAlert;
