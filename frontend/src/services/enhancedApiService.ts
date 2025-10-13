import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { useError } from '../context/ErrorContext';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Enhanced axios instance with retry logic and better error handling
const createApiClient = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return instance;
};

// Retry configuration
interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryCondition: (error: AxiosError) => boolean;
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  retryCondition: (error: AxiosError) => {
    // Retry on network errors, 5xx server errors, and 429 rate limit errors
    return (
      !error.response ||
      (error.response.status >= 500 && error.response.status < 600) ||
      error.response.status === 429 ||
      error.code === 'ECONNABORTED' ||
      error.code === 'ERR_NETWORK'
    );
  },
};

// Enhanced API service class
export class EnhancedApiService {
  private client: AxiosInstance;
  private retryConfig: RetryConfig;
  private errorContext: ReturnType<typeof useError> | null = null;

  constructor(retryConfig: Partial<RetryConfig> = {}) {
    this.client = createApiClient();
    this.retryConfig = { ...defaultRetryConfig, ...retryConfig };
    this.setupInterceptors();
  }

  // Set error context (called from React components)
  setErrorContext(context: ReturnType<typeof useError>) {
    this.errorContext = context;
  }

  // Setup request and response interceptors
  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add authentication token if available
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request timestamp for tracking
        (config as any).metadata = { startTime: Date.now() };

        return config;
      },
      (error) => {
        this.handleError(error, 'request');
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log successful responses
        const duration = Date.now() - ((response.config as any).metadata?.startTime || Date.now());
        console.log(`✅ API Response: ${response.status} ${response.config.url} (${duration}ms)`);
        return response;
      },
      async (error: AxiosError) => {
        return this.handleResponseError(error);
      }
    );
  }

  // Handle response errors with retry logic
  private async handleResponseError(error: AxiosError): Promise<never> {
    const config = error.config as any;
    
    // Initialize retry count if not present
    if (!config.retryCount) {
      config.retryCount = 0;
    }

    // Check if we should retry this request
    if (
      config.retryCount < this.retryConfig.maxRetries &&
      this.retryConfig.retryCondition(error)
    ) {
      config.retryCount++;
      
      // Calculate delay with exponential backoff
      const delay = this.retryConfig.retryDelay * Math.pow(2, config.retryCount - 1);
      
      console.log(`🔄 Retrying request (${config.retryCount}/${this.retryConfig.maxRetries}) in ${delay}ms`);
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Retry the request
      return this.client.request(config);
    }

    // No more retries, handle the error
    this.handleError(error, 'response');
    return Promise.reject(error);
  }

  // Handle errors and add them to the error context
  private handleError(error: AxiosError, source: 'request' | 'response') {
    if (!this.errorContext) {
      console.error('Error context not available');
      return;
    }

    const errorType = this.getErrorType(error);
    const message = this.getErrorMessage(error);
    const endpoint = error.config?.url || 'unknown';
    const status = error.response?.status;

    // Add error to context
    this.errorContext.addError({
      message,
      status,
      endpoint,
      errorType,
      maxRetries: this.retryConfig.maxRetries,
      context: {
        source,
        method: error.config?.method?.toUpperCase(),
        timestamp: new Date().toISOString(),
        retryCount: (error.config as any)?.retryCount || 0,
      },
    });

    // Log error details
    console.error(`🚨 API Error (${errorType}):`, {
      message,
      status,
      endpoint,
      source,
      retryCount: (error.config as any)?.retryCount || 0,
    });
  }

  // Determine error type based on the error
  private getErrorType(error: AxiosError): 'api' | 'network' | 'validation' | 'auth' | 'file_upload' | 'content_type' | 'unknown' {
    if (!error.response) {
      return 'network';
    }

    const status = error.response.status;
    const data = error.response.data as any;

    if (status === 401 || status === 403) {
      return 'auth';
    }

    if (status === 400) {
      // Check specific error codes for better categorization
      if (data?.code === 'FILE_UPLOAD_ERROR') {
        return 'file_upload';
      }
      if (data?.code === 'INVALID_CONTENT_TYPE') {
        return 'content_type';
      }
      if (data?.code === 'VALIDATION_ERROR' || data?.code === 'BAD_REQUEST') {
        return 'validation';
      }
      return 'validation'; // Default for 400 errors
    }

    if (status === 422) {
      return 'validation';
    }

    if (status >= 500) {
      return 'api';
    }

    return 'unknown';
  }

  // Get user-friendly error message
  private getErrorMessage(error: AxiosError): string {
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        return 'Request timeout. The server took too long to respond.';
      }
      if (error.code === 'ERR_NETWORK') {
        return 'Network error. Please check your internet connection.';
      }
      return 'Network error occurred.';
    }

    const status = error.response.status;
    const data = error.response.data as any;

    // Try to get error message from response with enhanced handling
    if (data?.message) {
      // Check if there are suggestions available
      if (data?.details?.suggestion) {
        return `${data.message}. ${data.details.suggestion}`;
      }
      return data.message;
    }

    if (data?.error) {
      return typeof data.error === 'string' ? data.error : 'An error occurred.';
    }

    // Enhanced status-based messages with specific handling for 400 errors
    switch (status) {
      case 400:
        // Provide specific messages based on error code
        if (data?.code === 'VALIDATION_ERROR') {
          const errorCount = data?.details?.total_errors || 0;
          return `Validation failed${errorCount > 0 ? ` (${errorCount} errors)` : ''}. Please check your input and try again.`;
        }
        if (data?.code === 'FILE_UPLOAD_ERROR') {
          const allowedTypes = data?.details?.allowed_file_types;
          const maxSize = data?.details?.max_file_size_mb;
          let message = 'File upload error.';
          if (allowedTypes) {
            message += ` Allowed types: ${allowedTypes.join(', ')}.`;
          }
          if (maxSize) {
            message += ` Maximum size: ${maxSize}MB.`;
          }
          return message;
        }
        if (data?.code === 'INVALID_CONTENT_TYPE') {
          return `Invalid content type. Expected: ${data?.details?.expected_content_type || 'application/json'}.`;
        }
        if (data?.code === 'BAD_REQUEST') {
          const missingFields = data?.details?.missing_fields;
          const invalidFields = data?.details?.invalid_fields;
          if (missingFields?.length > 0) {
            return `Missing required fields: ${missingFields.join(', ')}.`;
          }
          if (invalidFields && Object.keys(invalidFields).length > 0) {
            const fields = Object.keys(invalidFields).join(', ');
            return `Invalid field format for: ${fields}.`;
          }
        }
        return 'Bad request. Please check your input and try again.';

      case 401:
        return 'Authentication required. Please log in again.';
      case 403:
        return 'Access denied. You don\'t have permission for this action.';
      case 404:
        return 'Resource not found.';
      case 422:
        return 'Validation error. Please check your input.';
      case 429:
        return 'Too many requests. Please wait before trying again.';
      case 500:
        return 'Internal server error. Please try again later.';
      case 502:
        return 'Bad gateway. The server is temporarily unavailable.';
      case 503:
        return 'Service unavailable. Please try again later.';
      case 504:
        return 'Gateway timeout. The server is taking too long to respond.';
      default:
        return `Request failed with status ${status}.`;
    }
  }

  // Generic request method with error handling
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.client.request<T>(config);
      return response.data;
    } catch (error) {
      // Error is already handled by interceptors
      throw error;
    }
  }

  // GET request
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'GET', url });
  }

  // POST request
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  }

  // PUT request
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  }

  // PATCH request
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'PATCH', url, data });
  }

  // DELETE request
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  }

  // Upload file with progress tracking
  async uploadFile<T = any>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<T>({
      ...config,
      method: 'POST',
      url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers,
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  }

  // Download file
  async downloadFile(url: string, filename?: string, config?: AxiosRequestConfig): Promise<void> {
    try {
      const response = await this.client.request({
        ...config,
        method: 'GET',
        url,
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename || 'download';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      this.handleError(error as AxiosError, 'response');
      throw error;
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.client.get('/health', { timeout: 5000 });
      return true;
    } catch (error) {
      return false;
    }
  }

  // Get network status
  async getNetworkStatus(): Promise<{
    isOnline: boolean;
    latency: number;
    connectionType?: string;
  }> {
    const startTime = Date.now();
    
    try {
      await this.healthCheck();
      const latency = Date.now() - startTime;
      
      return {
        isOnline: true,
        latency,
        connectionType: this.getConnectionType(),
      };
    } catch (error) {
      return {
        isOnline: false,
        latency: -1,
        connectionType: this.getConnectionType(),
      };
    }
  }

  // Get connection type
  private getConnectionType(): string | undefined {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      if (connection) {
        return connection.effectiveType || connection.type;
      }
    }
    return undefined;
  }

  // Update retry configuration
  updateRetryConfig(config: Partial<RetryConfig>) {
    this.retryConfig = { ...this.retryConfig, ...config };
  }

  // Get current retry configuration
  getRetryConfig(): RetryConfig {
    return { ...this.retryConfig };
  }

  // Extract detailed error information for debugging and user feedback
  getDetailedErrorInfo(error: AxiosError): {
    requestId?: string;
    errorCode?: string;
    fieldErrors?: Record<string, any>;
    suggestions?: string[];
    debugInfo?: any;
  } {
    const data = error.response?.data as any;

    return {
      requestId: data?.request_id,
      errorCode: data?.code,
      fieldErrors: data?.details?.field_errors,
      suggestions: data?.details?.suggestions ? [data.details.suggestions] : undefined,
      debugInfo: data?.debug_info,
    };
  }

  // Validate request before sending (client-side pre-validation)
  validateRequest(config: AxiosRequestConfig): string[] {
    const errors: string[] = [];

    // Check for common issues
    if (config.method?.toUpperCase() === 'POST' && !config.data && !config.headers?.['Content-Type']?.includes('multipart')) {
      errors.push('POST request without data');
    }

    if (config.headers?.['Content-Type'] === 'application/json' && config.data && typeof config.data !== 'object') {
      errors.push('JSON Content-Type with non-object data');
    }

    // Check for file uploads
    if (config.data instanceof FormData) {
      if (!config.headers?.['Content-Type']?.includes('multipart') && !config.headers?.['Content-Type']?.includes('form-data')) {
        // FormData should automatically set the correct content type
        delete config.headers?.['Content-Type'];
      }
    }

    return errors;
  }

  // Enhanced request method with pre-validation
  async validatedRequest<T = any>(config: AxiosRequestConfig): Promise<T> {
    // Pre-validate request
    const validationErrors = this.validateRequest(config);
    if (validationErrors.length > 0) {
      console.warn('Request validation warnings:', validationErrors);
    }

    return this.request<T>(config);
  }
}

// Create singleton instance
export const enhancedApiService = new EnhancedApiService();

// React hook for using the enhanced API service with error context
export const useEnhancedApi = () => {
  const errorContext = useError();
  
  // Set error context in the service
  enhancedApiService.setErrorContext(errorContext);
  
  return {
    api: enhancedApiService,
    errorContext,
  };
};

export default enhancedApiService;
