import axios from 'axios';
import type { AxiosInstance } from 'axios';
import { jwtDecode } from 'jwt-decode';
import { environmentConfig } from '../config/environment';
import type {
  IApiService,
  ApiConfig,
  EnvironmentConfig,
  JwtPayload,
  ApiError,
  RequestConfig,
  RetryConfig,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RefreshTokenResponse,
  User,
  LoadingState
} from '../types/api.types';

// Default configuration from environment
const DEFAULT_CONFIG: ApiConfig = {
  baseURL: environmentConfig.api.baseUrl,
  timeout: environmentConfig.api.timeout,
  retryAttempts: environmentConfig.api.retry.maxAttempts,
  retryDelay: environmentConfig.api.retry.delay,
  maxRetryDelay: environmentConfig.api.retry.maxDelay,
};

// Environment-specific configurations
const ENVIRONMENT_CONFIG: EnvironmentConfig = {
  development: {
    ...DEFAULT_CONFIG,
    baseURL: environmentConfig.isDevelopment ? 'http://localhost:5000' : environmentConfig.api.baseUrl,
    timeout: environmentConfig.api.timeout,
  },
  production: {
    ...DEFAULT_CONFIG,
    baseURL: environmentConfig.api.baseUrl,
    timeout: environmentConfig.api.timeout,
    retryAttempts: environmentConfig.api.retry.maxAttempts,
  },
  staging: {
    ...DEFAULT_CONFIG,
    baseURL: environmentConfig.api.baseUrl,
    timeout: environmentConfig.api.timeout,
    retryAttempts: environmentConfig.api.retry.maxAttempts,
  },
  test: {
    ...DEFAULT_CONFIG,
    baseURL: environmentConfig.api.baseUrl,
    timeout: 10000,
    retryAttempts: 1,
  },
};

// Default retry configuration from environment
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: environmentConfig.api.retry.maxAttempts,
  baseDelay: environmentConfig.api.retry.delay,
  maxDelay: environmentConfig.api.retry.maxDelay,
  backoffMultiplier: 2,
  retryableStatusCodes: [408, 429, 500, 502, 503, 504],
};

// Storage keys
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'accessToken',
  REFRESH_TOKEN: 'refreshToken',
  TOKEN_EXPIRY: 'tokenExpiry',
  USER_DATA: 'userData',
} as const;

export class ApiService implements IApiService {
  private axiosInstance: AxiosInstance;
  private authAxiosInstance: AxiosInstance;
  private currentConfig: ApiConfig;
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];
  private loadingStates = new Map<string, LoadingState>();

  constructor(environment?: keyof EnvironmentConfig) {
    // Use environment from config if not specified
    const env = environment || environmentConfig.app.environment as keyof EnvironmentConfig;
    this.currentConfig = ENVIRONMENT_CONFIG[env];
    this.initializeAxiosInstances();
    this.setupInterceptors();
  }

  /**
   * Initialize axios instances
   */
  private initializeAxiosInstances(): void {
    // Main API instance
    this.axiosInstance = axios.create({
      baseURL: this.currentConfig.baseURL,
      timeout: this.currentConfig.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    // Auth-specific instance
    this.authAxiosInstance = axios.create({
      baseURL: this.currentConfig.baseURL,
      timeout: this.currentConfig.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });
  }

  /**
   * Setup request and response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptors
    this.axiosInstance.interceptors.request.use(
      this.handleRequest.bind(this),
      this.handleRequestError.bind(this)
    );

    this.authAxiosInstance.interceptors.request.use(
      this.handleRequest.bind(this),
      this.handleRequestError.bind(this)
    );

    // Response interceptors
    this.axiosInstance.interceptors.response.use(
      this.handleResponse.bind(this),
      this.handleResponseError.bind(this)
    );

    this.authAxiosInstance.interceptors.response.use(
      this.handleResponse.bind(this),
      this.handleResponseError.bind(this)
    );
  }

  /**
   * Handle request interceptor
   */
  private handleRequest(config: any): any {
    const token = this.getAuthToken();
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      };
    }

    // Add request ID for tracking
    config.headers = {
      ...config.headers,
      'X-Request-ID': this.generateRequestId(),
    };

    return config;
  }

  /**
   * Handle request error
   */
  private handleRequestError(error: any): Promise<never> {
    return Promise.reject(this.createApiError(error, 'REQUEST_ERROR'));
  }

  /**
   * Handle response interceptor
   */
  private handleResponse(response: any): any {
    return response;
  }

  /**
   * Handle response error with retry logic and token refresh
   */
  private async handleResponseError(error: any): Promise<never> {
    const originalRequest = error.config as any;
    
    // Handle token refresh for 401 errors
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (this.isRefreshing) {
        // Wait for the refresh to complete
        return new Promise((resolve) => {
          this.refreshSubscribers.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(axios(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      this.isRefreshing = true;

      try {
        const newToken = await this.refreshToken();
        this.refreshSubscribers.forEach(callback => callback(newToken.access_token));
        this.refreshSubscribers = [];
        
        // Retry the original request
        originalRequest.headers.Authorization = `Bearer ${newToken.access_token}`;
        return axios(originalRequest);
      } catch (refreshError) {
        this.refreshSubscribers.forEach(callback => callback(''));
        this.refreshSubscribers = [];
        this.logout();
        return Promise.reject(this.createApiError(refreshError, 'TOKEN_REFRESH_FAILED'));
      } finally {
        this.isRefreshing = false;
      }
    }

    return Promise.reject(this.createApiError(error, 'RESPONSE_ERROR'));
  }

  /**
   * Create standardized API error
   */
  private createApiError(error: any, code: string): ApiError {
    const status = error.response?.status || 0;
    const message = error.response?.data?.message || error.message || 'An unexpected error occurred';
    
    return {
      message: this.getUserFriendlyMessage(status, message),
      code,
      status,
      details: error.response?.data?.details || {},
      timestamp: new Date().toISOString(),
      requestId: error.config?.headers?.['X-Request-ID'],
    };
  }

  /**
   * Get user-friendly error messages
   */
  private getUserFriendlyMessage(status: number, defaultMessage: string): string {
    const errorMessages: Record<number, string> = {
      400: 'Invalid request. Please check your input and try again.',
      401: 'Authentication required. Please log in again.',
      403: 'Access denied. You don\'t have permission to perform this action.',
      404: 'The requested resource was not found.',
      408: 'Request timeout. Please try again.',
      429: 'Too many requests. Please wait a moment and try again.',
      500: 'Server error. Please try again later.',
      502: 'Bad gateway. Please try again later.',
      503: 'Service unavailable. Please try again later.',
      504: 'Gateway timeout. Please try again later.',
    };

    return errorMessages[status] || defaultMessage;
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Implement retry logic with exponential backoff
   */
  private async executeWithRetry<T>(
    requestFn: () => Promise<T>,
    config?: RequestConfig
  ): Promise<T> {
    const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config?.retryConfig };
    let lastError: any;
    let delay = retryConfig.baseDelay;

    for (let attempt = 1; attempt <= retryConfig.maxAttempts; attempt++) {
      try {
        return await requestFn();
      } catch (error: any) {
        lastError = error;
        
        // Check if error is retryable
        if (!this.isRetryableError(error, retryConfig)) {
          throw error;
        }

        // Don't wait on the last attempt
        if (attempt < retryConfig.maxAttempts) {
          await this.sleep(delay);
          delay = Math.min(delay * retryConfig.backoffMultiplier, retryConfig.maxDelay);
        }
      }
    }

    throw lastError;
  }

  /**
   * Check if error is retryable
   */
  private isRetryableError(error: any, retryConfig: RetryConfig): boolean {
    const status = error.response?.status;
    return retryConfig.retryableStatusCodes.includes(status);
  }

  /**
   * Sleep utility for retry delays
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Update loading state for a specific request
   */
  private updateLoadingState(requestId: string, updates: Partial<LoadingState>): void {
    const current = this.loadingStates.get(requestId) || {
      isLoading: false,
      error: null,
      retryCount: 0,
      lastUpdated: null,
    };

    this.loadingStates.set(requestId, { ...current, ...updates });
  }

  // Configuration Methods
  public setBaseURL(url: string): void {
    this.currentConfig.baseURL = url;
    this.axiosInstance.defaults.baseURL = url;
    this.authAxiosInstance.defaults.baseURL = url;
  }

  public getBaseURL(): string {
    return this.currentConfig.baseURL;
  }

  public setAuthToken(token: string): void {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
    
    // Set token expiry
    try {
      const decoded = jwtDecode<JwtPayload>(token);
      const expiry = decoded.exp * 1000; // Convert to milliseconds
      localStorage.setItem(STORAGE_KEYS.TOKEN_EXPIRY, expiry.toString());
    } catch (error) {
      console.warn('Failed to decode JWT token:', error);
    }
  }

  public clearAuthToken(): void {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.TOKEN_EXPIRY);
    localStorage.removeItem(STORAGE_KEYS.USER_DATA);
  }

  public setRequestTimeout(timeout: number): void {
    this.currentConfig.timeout = timeout;
    this.axiosInstance.defaults.timeout = timeout;
    this.authAxiosInstance.defaults.timeout = timeout;
  }

  // Authentication Methods
  public async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const { data } = await this.authAxiosInstance.post('/api/auth/login', credentials);
      
      if (data.access_token) {
        this.setAuthToken(data.access_token);
        if (data.refresh_token) {
          localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
        }
        if (data.user) {
          localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));
        }
      }
      
      return data;
    } catch (error: any) {
      throw this.createApiError(error, 'LOGIN_FAILED');
    }
  }

  public async register(userData: RegisterRequest): Promise<LoginResponse> {
    try {
      const { data } = await this.authAxiosInstance.post('/api/auth/register', userData);
      
      if (data.access_token) {
        this.setAuthToken(data.access_token);
        if (data.refresh_token) {
          localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token);
        }
        if (data.user) {
          localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(data.user));
        }
      }
      
      return data;
    } catch (error: any) {
      throw this.createApiError(error, 'REGISTRATION_FAILED');
    }
  }

  public async logout(): Promise<void> {
    try {
      // Call logout endpoint if available
      if (this.isAuthenticated()) {
        await this.authAxiosInstance.post('/api/auth/logout');
      }
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      this.clearAuthToken();
    }
  }

  public async refreshToken(): Promise<RefreshTokenResponse> {
    const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const { data } = await this.authAxiosInstance.post('/api/auth/refresh', {
        refresh_token: refreshToken,
      });

      if (data.access_token) {
        this.setAuthToken(data.access_token);
      }

      return data;
    } catch (error: any) {
      this.clearAuthToken();
      throw this.createApiError(error, 'TOKEN_REFRESH_FAILED');
    }
  }

  public async getCurrentUser(): Promise<User> {
    try {
      const { data } = await this.authAxiosInstance.get('/api/auth/me');
      return data;
    } catch (error: any) {
      throw this.createApiError(error, 'GET_USER_FAILED');
    }
  }

  // HTTP Methods with retry logic
  public async get<T>(url: string, config?: RequestConfig): Promise<T> {
    const requestId = this.generateRequestId();
    this.updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await this.executeWithRetry(
        () => this.axiosInstance.get(url, this.buildAxiosConfig(config)),
        config
      );
      
      this.updateLoadingState(requestId, { isLoading: false, lastUpdated: new Date().toISOString() });
      return result.data;
    } catch (error: any) {
      this.updateLoadingState(requestId, { 
        isLoading: false, 
        error: this.createApiError(error, 'GET_REQUEST_FAILED'),
        retryCount: (this.loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }

  public async post<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    const requestId = this.generateRequestId();
    this.updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await this.executeWithRetry(
        () => this.axiosInstance.post(url, data, this.buildAxiosConfig(config)),
        config
      );
      
      this.updateLoadingState(requestId, { isLoading: false, lastUpdated: new Date().toISOString() });
      return result.data;
    } catch (error: any) {
      this.updateLoadingState(requestId, { 
        isLoading: false, 
        error: this.createApiError(error, 'POST_REQUEST_FAILED'),
        retryCount: (this.loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }

  public async put<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    const requestId = this.generateRequestId();
    this.updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await this.executeWithRetry(
        () => this.axiosInstance.put(url, data, this.buildAxiosConfig(config)),
        config
      );
      
      this.updateLoadingState(requestId, { isLoading: false, lastUpdated: new Date().toISOString() });
      return result.data;
    } catch (error: any) {
      this.updateLoadingState(requestId, { 
        isLoading: false, 
        error: this.createApiError(error, 'PUT_REQUEST_FAILED'),
        retryCount: (this.loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }

  public async patch<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    const requestId = this.generateRequestId();
    this.updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await this.executeWithRetry(
        () => this.axiosInstance.patch(url, data, this.buildAxiosConfig(config)),
        config
      );
      
      this.updateLoadingState(requestId, { isLoading: false, lastUpdated: new Date().toISOString() });
      return result.data;
    } catch (error: any) {
      this.updateLoadingState(requestId, { 
        isLoading: false, 
        error: this.createApiError(error, 'PATCH_REQUEST_FAILED'),
        retryCount: (this.loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }

  public async delete<T>(url: string, config?: RequestConfig): Promise<T> {
    const requestId = this.generateRequestId();
    this.updateLoadingState(requestId, { isLoading: true, error: null });

    try {
      const result = await this.executeWithRetry(
        () => this.axiosInstance.delete(url, this.buildAxiosConfig(config)),
        config
      );
      
      this.updateLoadingState(requestId, { isLoading: false, lastUpdated: new Date().toISOString() });
      return result.data;
    } catch (error: any) {
      this.updateLoadingState(requestId, { 
        isLoading: false, 
        error: this.createApiError(error, 'DELETE_REQUEST_FAILED'),
        retryCount: (this.loadingStates.get(requestId)?.retryCount || 0) + 1
      });
      throw error;
    }
  }

  /**
   * Build axios config from our RequestConfig
   */
  private buildAxiosConfig(config?: RequestConfig): any {
    const axiosConfig: any = {};

    if (config?.timeout) {
      axiosConfig.timeout = config.timeout;
    }

    if (config?.headers) {
      axiosConfig.headers = config.headers;
    }

    if (config?.params) {
      axiosConfig.params = config.params;
    }

    return axiosConfig;
  }

  // Utility Methods
  public isAuthenticated(): boolean {
    const token = this.getAuthToken();
    if (!token) return false;
    
    return !this.isTokenExpired();
  }

  public getAuthToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  }

  public getTokenExpiry(): number | null {
    const expiry = localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRY);
    return expiry ? parseInt(expiry, 10) : null;
  }

  public isTokenExpired(): boolean {
    const expiry = this.getTokenExpiry();
    if (!expiry) return true;
    
    // Add 5 minute buffer before expiry
    return Date.now() >= (expiry - 5 * 60 * 1000);
  }

  /**
   * Get loading state for a specific request
   */
  public getLoadingState(requestId: string): LoadingState | undefined {
    return this.loadingStates.get(requestId);
  }

  /**
   * Clear loading state for a specific request
   */
  public clearLoadingState(requestId: string): void {
    this.loadingStates.delete(requestId);
  }

  /**
   * Get all loading states
   */
  public getAllLoadingStates(): Map<string, LoadingState> {
    return new Map(this.loadingStates);
  }
}

// Create and export default instance
export const apiService = new ApiService();

// Export for use in other modules
export default apiService;
