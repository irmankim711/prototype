/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * CSRF Token Input Component
 * 
 * This component automatically includes CSRF tokens in forms for protection against CSRF attacks.
 * It can be used as a hidden input in any form component.
 */

import React from 'react';

import { useCSRF } from "../hooks/useCSRF";

interface CSRFTokenInputProps {
  /**
   * Whether to show a loading indicator while the token is being fetched
   */
  showLoading?: boolean;
  
  /**
   * Custom CSS class for the component
   */
  className?: string;
  
  /**
   * Whether to show error messages if token loading fails
   */
  showErrors?: boolean;
  
  /**
   * Custom error message component
   */
  errorComponent?: React.ComponentType<{ error: string }>;
}

/**
 * Default error component
 */
const DefaultErrorComponent: React.FC<{ error: string }> = ({ error }) => (
  <div className="text-red-500 text-sm mt-1">
    ⚠️ CSRF protection error: {error}
  </div>
);

/**
 * CSRF Token Input Component
 */
const CSRFTokenInput: React.FC<CSRFTokenInputProps> = ({
  showLoading = false,
  className = '',
  showErrors = false,
  errorComponent: ErrorComponent = DefaultErrorComponent,
}) => {
  const { csrfToken, isLoading, error, refreshToken } = useCSRF();

  // If no token is available, try to refresh it
  React.useEffect(() => {
    if (!csrfToken && !isLoading) {
      refreshToken();
    }
  }, [csrfToken, isLoading, refreshToken]);

  // Show loading indicator if requested
  if (showLoading && isLoading) {
    return (
      <div className={`text-gray-500 text-sm ${className}`}>
        🔄 Loading CSRF protection...
      </div>
    );
  }

  // Show error if requested and there's an error
  if (showErrors && error) {
    return <ErrorComponent error={error} />;
  }

  // If we have a token, render the hidden input
  if (csrfToken) {
    return (
      <input
        type="hidden"
        name="csrf_token"
        value={csrfToken}
        className={className}
        data-testid="csrf-token-input"
      />
    );
  }

  // If no token and not loading, show a warning
  if (!isLoading && !csrfToken) {
    return (
      <div className={`text-yellow-500 text-sm ${className}`}>
        ⚠️ CSRF protection not available
      </div>
    );
  }

  // Default case: render nothing
  return null;
};

/**
 * Higher-order component that wraps a form component with CSRF protection
 */
export function withCSRFProtection<P extends object>(
  WrappedComponent: React.ComponentType<P>
): React.ComponentType<P> {
  return React.forwardRef<HTMLElement, P>((props, ref) => {
    const { csrfToken, isLoading, error } = useCSRF();

    // If CSRF token is not available, show loading or error
    if (isLoading) {
      return (
        <div className="flex items-center justify-center p-4">
          <div className="text-gray-500">🔄 Loading security protection...</div>
        </div>
      );
    }

    if (error || !csrfToken) {
      return (
        <div className="flex items-center justify-center p-4">
          <div className="text-red-500">
            ❌ Security protection unavailable. Please refresh the page.
          </div>
        </div>
      );
    }

    // Render the wrapped component with CSRF token available
    return (
      <>
        <CSRFTokenInput />
        <WrappedComponent {...props} ref={ref} />
      </>
    );
  });
}

/**
 * Hook that provides CSRF token for use in custom form handling
 */
const useCSRFFormData = () => {
  const { csrfToken, getTokenFormData } = useCSRF();

const addCSRFToken = React.useCallback(
    (formData: FormData | Record<string, any>) => {
      if (!csrfToken) {
        throw Error('CSRF token not available');
      }

      if (formData instanceof FormData) {
        formData.append('csrf_token', csrfToken);
      } else {
        formData.csrf_token = csrfToken;
      }

      return formData;
    },
    [csrfToken]
  );

const createFormDataWithCSRF = React.useCallback(
    (data: Record<string, any>) => {
      const formData = new FormData();
      
      // Add all data
      Object.entries(data).forEach(([key, value]) => {
        formData.append(key, value);
      });
      
      // Add CSRF token
      if (csrfToken) {
        formData.append('csrf_token', csrfToken);
      }
      
      return formData;
    },
    [csrfToken]
  );

return {
    csrfToken,
    addCSRFToken,
    createFormDataWithCSRF,
    getTokenFormData,
  };
};

export default CSRFTokenInput;
