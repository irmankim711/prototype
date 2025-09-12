import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { toast } from 'react-hot-toast';
import type { ToastOptions } from 'react-hot-toast';

// Error types
export interface ApiError {
  id: string;
  message: string;
  status?: number;
  endpoint?: string;
  timestamp: Date;
  retryCount: number;
  maxRetries: number;
  isRetrying: boolean;
  errorType: 'api' | 'network' | 'validation' | 'auth' | 'unknown';
  context?: Record<string, any>;
}

export interface NetworkStatus {
  isOnline: boolean;
  lastChecked: Date;
  connectionType?: 'wifi' | 'cellular' | 'ethernet' | 'unknown';
}

export interface ErrorState {
  errors: ApiError[];
  networkStatus: NetworkStatus;
  globalErrorCount: number;
  isRetrying: boolean;
}

// Action types
export type ErrorAction =
  | { type: 'ADD_ERROR'; payload: Omit<ApiError, 'id' | 'timestamp' | 'retryCount' | 'isRetrying'> }
  | { type: 'REMOVE_ERROR'; payload: string }
  | { type: 'UPDATE_ERROR'; payload: { id: string; updates: Partial<ApiError> } }
  | { type: 'CLEAR_ALL_ERRORS' }
  | { type: 'SET_RETRYING'; payload: { id: string; isRetrying: boolean } }
  | { type: 'INCREMENT_RETRY_COUNT'; payload: string }
  | { type: 'SET_NETWORK_STATUS'; payload: Partial<NetworkStatus> }
  | { type: 'RESET_ERROR_COUNT'; payload: string };

// Initial state
const initialState: ErrorState = {
  errors: [],
  networkStatus: {
    isOnline: navigator.onLine,
    lastChecked: new Date(),
    connectionType: 'unknown',
  },
  globalErrorCount: 0,
  isRetrying: false,
};

// Error reducer
function errorReducer(state: ErrorState, action: ErrorAction): ErrorState {
  switch (action.type) {
    case 'ADD_ERROR': {
      const newError: ApiError = {
        ...action.payload,
        id: crypto.randomUUID(),
        timestamp: new Date(),
        retryCount: 0,
        isRetrying: false,
      };
      
      return {
        ...state,
        errors: [...state.errors, newError],
        globalErrorCount: state.globalErrorCount + 1,
      };
    }
    
    case 'REMOVE_ERROR': {
      return {
        ...state,
        errors: state.errors.filter(error => error.id !== action.payload),
        globalErrorCount: Math.max(0, state.globalErrorCount - 1),
      };
    }
    
    case 'UPDATE_ERROR': {
      return {
        ...state,
        errors: state.errors.map(error =>
          error.id === action.payload.id
            ? { ...error, ...action.payload.updates }
            : error
        ),
      };
    }
    
    case 'CLEAR_ALL_ERRORS': {
      return {
        ...state,
        errors: [],
        globalErrorCount: 0,
      };
    }
    
    case 'SET_RETRYING': {
      return {
        ...state,
        errors: state.errors.map(error =>
          error.id === action.payload.id
            ? { ...error, isRetrying: action.payload.isRetrying }
            : error
        ),
        isRetrying: action.payload.isRetrying,
      };
    }
    
    case 'INCREMENT_RETRY_COUNT': {
      return {
        ...state,
        errors: state.errors.map(error =>
          error.id === action.payload
            ? { ...error, retryCount: error.retryCount + 1 }
            : error
        ),
      };
    }
    
    case 'SET_NETWORK_STATUS': {
      return {
        ...state,
        networkStatus: {
          ...state.networkStatus,
          ...action.payload,
          lastChecked: new Date(),
        },
      };
    }
    
    case 'RESET_ERROR_COUNT': {
      return {
        ...state,
        errors: state.errors.map(error =>
          error.id === action.payload
            ? { ...error, retryCount: 0 }
            : error
        ),
      };
    }
    
    default:
      return state;
  }
}

// Error context interface
interface ErrorContextType {
  state: ErrorState;
  addError: (error: Omit<ApiError, 'id' | 'timestamp' | 'retryCount' | 'isRetrying'>) => string;
  removeError: (id: string) => void;
  clearAllErrors: () => void;
  retryError: (id: string) => Promise<void>;
  retryAllErrors: () => Promise<void>;
  isOnline: boolean;
  checkNetworkStatus: () => Promise<void>;
  getErrorsByType: (type: ApiError['errorType']) => ApiError[];
  getErrorsByEndpoint: (endpoint: string) => ApiError[];
}

// Create context
const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

// Error context provider
interface ErrorProviderProps {
  children: ReactNode;
  maxRetries?: number;
  retryDelay?: number;
  toastOptions?: ToastOptions;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({
  children,
  retryDelay = 2000,
  toastOptions = {},
}) => {
  const [state, dispatch] = useReducer(errorReducer, initialState);

  // Network status checking
  const checkNetworkStatus = useCallback(async (): Promise<void> => {
    try {
      // Temporarily disabled health check since backend is not running
      // const response = await fetch('/api/health', { 
      //   method: 'HEAD',
      //   cache: 'no-cache',
      //   signal: AbortSignal.timeout(5000)
      // });
      
      // const isOnline = response.ok;
      const isOnline = navigator.onLine; // Use browser's online status instead
      const connectionType = getConnectionType();
      
      dispatch({
        type: 'SET_NETWORK_STATUS',
        payload: { isOnline, connectionType }
      });
    } catch (error) {
      const isOnline = navigator.onLine;
      const connectionType = getConnectionType();
      
      dispatch({
        type: 'SET_NETWORK_STATUS',
        payload: { isOnline, connectionType }
      });
    }
  }, []);

  // Get connection type
  const getConnectionType = (): NetworkStatus['connectionType'] => {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      if (connection) {
        switch (connection.effectiveType) {
          case 'slow-2g':
          case '2g':
          case '3g':
            return 'cellular';
          case '4g':
            return 'wifi';
          default:
            return 'unknown';
        }
      }
    }
    return 'unknown';
  };

  // Add error with toast notification
  const addError = useCallback((error: Omit<ApiError, 'id' | 'timestamp' | 'retryCount' | 'isRetrying'>) => {
    const errorId = crypto.randomUUID();
    
    dispatch({
      type: 'ADD_ERROR',
      payload: error,
    });

    // Show toast notification
    const toastMessage = getToastMessage(error);
    const toastType = getToastType(error.errorType);
    
    if (toastType === 'error') {
      toast.error(toastMessage, {
        duration: 5000,
        position: 'top-right',
        ...toastOptions,
      });
    } else if (toastType === 'warning') {
      toast(toastMessage, {
        duration: 5000,
        position: 'top-right',
        icon: '⚠️',
        ...toastOptions,
      });
    } else {
      toast.success(toastMessage, {
        duration: 5000,
        position: 'top-right',
        ...toastOptions,
      });
    }

    return errorId;
  }, [toastOptions]);

  // Get toast message based on error type
  const getToastMessage = (error: Omit<ApiError, 'id' | 'timestamp' | 'retryCount' | 'isRetrying'>): string => {
    switch (error.errorType) {
      case 'api':
        return `API Error: ${error.message}`;
      case 'network':
        return `Network Error: ${error.message}`;
      case 'validation':
        return `Validation Error: ${error.message}`;
      case 'auth':
        return `Authentication Error: ${error.message}`;
      default:
        return error.message;
    }
  };

  // Get toast type based on error type
  const getToastType = (errorType: ApiError['errorType']): 'error' | 'warning' | 'success' => {
    switch (errorType) {
      case 'auth':
        return 'warning';
      case 'validation':
        return 'success';
      default:
        return 'error';
    }
  };

  // Remove error
  const removeError = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_ERROR', payload: id });
  }, []);

  // Clear all errors
  const clearAllErrors = useCallback(() => {
    dispatch({ type: 'CLEAR_ALL_ERRORS' });
  }, []);

  // Retry specific error
  const retryError = useCallback(async (id: string) => {
    const error = state.errors.find(e => e.id === id);
    if (!error || error.retryCount >= error.maxRetries) {
      return;
    }

    dispatch({ type: 'SET_RETRYING', payload: { id, isRetrying: true } });

    try {
      // Wait for retry delay
      await new Promise(resolve => setTimeout(resolve, retryDelay * (error.retryCount + 1)));
      
      // Increment retry count
      dispatch({ type: 'INCREMENT_RETRY_COUNT', payload: id });
      
      // Here you would typically retry the actual API call
      // For now, we'll simulate a retry
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // If successful, remove the error
      dispatch({ type: 'REMOVE_ERROR', payload: id });
      
      toast.success('Request retried successfully!');
    } catch (retryError) {
      // If retry fails, update error state
      dispatch({
        type: 'UPDATE_ERROR',
        payload: {
          id,
          updates: {
            message: `Retry failed: ${(retryError as Error).message}`,
            isRetrying: false,
          },
        },
      });
      
      toast.error('Retry failed. Please try again manually.');
    } finally {
      dispatch({ type: 'SET_RETRYING', payload: { id, isRetrying: false } });
    }
  }, [state.errors, retryDelay]);

  // Retry all errors
  const retryAllErrors = useCallback(async () => {
    const retryableErrors = state.errors.filter(error => error.retryCount < error.maxRetries);
    
    if (retryableErrors.length === 0) {
      toast.success('No errors to retry');
      return;
    }

    dispatch({ type: 'SET_RETRYING', payload: { id: 'global', isRetrying: true } });

    try {
      // Retry all errors in parallel
      await Promise.allSettled(
        retryableErrors.map(error => retryError(error.id))
      );
      
      toast.success(`Retried ${retryableErrors.length} failed requests`);
    } catch (error) {
      toast.error('Some retries failed. Please check individual errors.');
    } finally {
      dispatch({ type: 'SET_RETRYING', payload: { id: 'global', isRetrying: false } });
    }
  }, [state.errors, retryError]);

  // Get errors by type
  const getErrorsByType = useCallback((type: ApiError['errorType']) => {
    return state.errors.filter(error => error.errorType === type);
  }, [state.errors]);

  // Get errors by endpoint
  const getErrorsByEndpoint = useCallback((endpoint: string) => {
    return state.errors.filter(error => error.endpoint === endpoint);
  }, [state.errors]);

  // Network event listeners
  useEffect(() => {
    const handleOnline = () => {
      dispatch({
        type: 'SET_NETWORK_STATUS',
        payload: { isOnline: true }
      });
      toast.success('Network connection restored');
    };

    const handleOffline = () => {
      dispatch({
        type: 'SET_NETWORK_STATUS',
        payload: { isOnline: false }
      });
      toast.error('Network connection lost');
    };

    // Check network status periodically
    const networkCheckInterval = setInterval(checkNetworkStatus, 30000);

    // Add event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial network check
    checkNetworkStatus();

    return () => {
      clearInterval(networkCheckInterval);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [checkNetworkStatus]);

  // Auto-retry logic for transient failures
  useEffect(() => {
    const autoRetryErrors = state.errors.filter(
      error => 
        error.errorType === 'network' && 
        error.retryCount < error.maxRetries && 
        !error.isRetrying
    );

    if (autoRetryErrors.length > 0 && state.networkStatus.isOnline) {
      autoRetryErrors.forEach(error => {
        setTimeout(() => retryError(error.id), retryDelay);
      });
    }
  }, [state.errors, state.networkStatus.isOnline, retryDelay, retryError]);

  const contextValue: ErrorContextType = {
    state,
    addError,
    removeError,
    clearAllErrors,
    retryError,
    retryAllErrors,
    isOnline: state.networkStatus.isOnline,
    checkNetworkStatus,
    getErrorsByType,
    getErrorsByEndpoint,
  };

  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
    </ErrorContext.Provider>
  );
};

// Custom hook to use error context
export const useError = (): ErrorContextType => {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
};

export default ErrorContext;
