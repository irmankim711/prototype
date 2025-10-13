/* eslint-disable @typescript-eslint/no-explicit-any */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryCondition: (error: AxiosError) => boolean;
}

interface RequestQueueItem {
  config: AxiosRequestConfig;
  resolve: (value: any) => void;
  reject: (reason: any) => void;
  retryCount: number;
  abortController: AbortController;
}

export class StabilizedApiService {
  private client: AxiosInstance;
  private retryConfig: RetryConfig;
  private requestQueue: Map<string, RequestQueueItem> = new Map();
  private activeRequests: Map<string, AbortController> = new Map();

  constructor(retryConfig?: Partial<RetryConfig>) {
    this.retryConfig = {
      maxRetries: 2, // Reduced from 3 to prevent excessive retries
      baseDelay: 1000,
      maxDelay: 10000, // Cap at 10 seconds
      backoffMultiplier: 2,
      retryCondition: (error: AxiosError) => {
        // Only retry on specific network/server errors
        if (error.code === 'ECONNABORTED') return false; // Don't retry timeouts
        if (error.response?.status && error.response.status < 500) return false; // Don't retry client errors
        return (
          !error.response ||
          (error.response.status >= 500 && error.response.status < 600) ||
          error.response.status === 429 ||
          error.code === 'ERR_NETWORK'
        );
      },
      ...retryConfig,
    };

    this.client = this.createApiClient();
    this.setupInterceptors();
  }

  private createApiClient(): AxiosInstance {
    const instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return instance;
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: any) => {
        // Add authentication token if available
        const token = localStorage.getItem('token');
        if (token && !config.headers.Authorization) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Create unique request ID for tracking
        const requestId = this.generateRequestId(config);
        config.requestId = requestId;

        // Add request timestamp
        config.metadata = { startTime: Date.now() };

        return config;
      },
      (error: any) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        const duration = Date.now() - (response.config as any).metadata?.startTime || 0;
        const requestId = (response.config as any).requestId;

        // Clean up tracking
        if (requestId) {
          this.activeRequests.delete(requestId);
        }

        console.log(`✅ API Success: ${response.status} ${response.config.url} (${duration}ms)`);
        return response;
      },
      (error: AxiosError) => {
        return this.handleResponseError(error);
      }
    );
  }

  private generateRequestId(config: any): string {
    const url = config.url || '';
    const method = config.method || 'GET';
    const timestamp = Date.now();
    return `${method.toUpperCase()}-${url.replace(/[^a-zA-Z0-9]/g, '_')}-${timestamp}`;
  }

  private async handleResponseError(error: AxiosError): Promise<never> {
    const config = error.config as any;
    const requestId = config?.requestId;

    // Clean up tracking
    if (requestId) {
      this.activeRequests.delete(requestId);
    }

    // Don't retry if request was cancelled
    if (error.code === 'ERR_CANCELED') {
      console.log('🚫 Request cancelled:', config?.url);
      return Promise.reject(error);
    }

    // Initialize retry count
    if (!config.retryCount) {
      config.retryCount = 0;
    }

    // Check if we should retry
    const shouldRetry =
      config.retryCount < this.retryConfig.maxRetries &&
      this.retryConfig.retryCondition(error) &&
      !config.__isRetry; // Prevent infinite retry loops

    if (shouldRetry) {
      config.retryCount++;
      config.__isRetry = true;

      // Calculate delay with exponential backoff + jitter
      const baseDelay = this.retryConfig.baseDelay * Math.pow(this.retryConfig.backoffMultiplier, config.retryCount - 1);
      const jitter = Math.random() * 0.1 * baseDelay; // Add 10% jitter
      const delay = Math.min(baseDelay + jitter, this.retryConfig.maxDelay);

      console.warn(`🔄 Retrying request (${config.retryCount}/${this.retryConfig.maxRetries}) after ${Math.round(delay)}ms: ${config.url}`);

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay));

      // Create new abort controller for retry
      const newAbortController = new AbortController();
      config.signal = newAbortController.signal;

      if (requestId) {
        this.activeRequests.set(requestId, newAbortController);
      }

      // Retry the request
      return this.client.request(config);
    }

    // Log error details for debugging
    this.logError(error);

    return Promise.reject(error);
  }

  private logError(error: AxiosError) {
    const config = error.config as any;
    const retryCount = config?.retryCount || 0;

    console.error(`🚨 API Error after ${retryCount} retries:`, {
      url: config?.url,
      method: config?.method?.toUpperCase(),
      status: error.response?.status,
      statusText: error.response?.statusText,
      message: error.message,
      code: error.code,
      retryCount,
    });
  }

  // Public method to cancel all pending requests
  public cancelAllRequests(reason = 'Component unmounted or route changed') {
    console.log(`🚫 Cancelling ${this.activeRequests.size} active requests: ${reason}`);

    this.activeRequests.forEach((controller, requestId) => {
      try {
        controller.abort();
      } catch (err) {
        console.warn(`Failed to abort request ${requestId}:`, err);
      }
    });

    this.activeRequests.clear();
    this.requestQueue.clear();
  }

  // Public method to cancel specific request
  public cancelRequest(requestId: string) {
    const controller = this.activeRequests.get(requestId);
    if (controller) {
      controller.abort();
      this.activeRequests.delete(requestId);
      console.log(`🚫 Cancelled request: ${requestId}`);
    }
  }

  // Enhanced request methods with built-in cancellation
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    const abortController = new AbortController();
    const enhancedConfig = {
      ...config,
      signal: abortController.signal,
    };

    const requestId = this.generateRequestId({ url, method: 'GET', ...enhancedConfig });
    this.activeRequests.set(requestId, abortController);

    try {
      return await this.client.get<T>(url, enhancedConfig);
    } catch (error) {
      this.activeRequests.delete(requestId);
      throw error;
    }
  }

  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    const abortController = new AbortController();
    const enhancedConfig = {
      ...config,
      signal: abortController.signal,
    };

    const requestId = this.generateRequestId({ url, method: 'POST', ...enhancedConfig });
    this.activeRequests.set(requestId, abortController);

    try {
      return await this.client.post<T>(url, data, enhancedConfig);
    } catch (error) {
      this.activeRequests.delete(requestId);
      throw error;
    }
  }

  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    const abortController = new AbortController();
    const enhancedConfig = {
      ...config,
      signal: abortController.signal,
    };

    const requestId = this.generateRequestId({ url, method: 'PUT', ...enhancedConfig });
    this.activeRequests.set(requestId, abortController);

    try {
      return await this.client.put<T>(url, data, enhancedConfig);
    } catch (error) {
      this.activeRequests.delete(requestId);
      throw error;
    }
  }

  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    const abortController = new AbortController();
    const enhancedConfig = {
      ...config,
      signal: abortController.signal,
    };

    const requestId = this.generateRequestId({ url, method: 'DELETE', ...enhancedConfig });
    this.activeRequests.set(requestId, abortController);

    try {
      return await this.client.delete<T>(url, enhancedConfig);
    } catch (error) {
      this.activeRequests.delete(requestId);
      throw error;
    }
  }

  // Get status information
  public getStatus() {
    return {
      activeRequests: this.activeRequests.size,
      queuedRequests: this.requestQueue.size,
      retryConfig: this.retryConfig,
    };
  }
}

// Create and export singleton instance
export const stabilizedApi = new StabilizedApiService();

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    stabilizedApi.cancelAllRequests('Page unloading');
  });

  window.addEventListener('pagehide', () => {
    stabilizedApi.cancelAllRequests('Page hidden');
  });
}

export default stabilizedApi;