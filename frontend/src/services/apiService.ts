import axios from 'axios';
import type { AxiosInstance } from 'axios';
import { jwtDecode } from 'jwt-decode';
import { environmentConfig } from '../config/environment';
import { auth } from '../config/firebase';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';
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
  FIREBASE_TOKEN: 'firebaseToken',
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
   * Obtain a fresh Firebase ID token from the Firebase SDK.
   * If forceRefresh is true, Firebase will mint a new token even if the current one is valid.
   */
  private async getFreshFirebaseIdToken(forceRefresh = true): Promise<string | null> {
    try {
      const user = auth?.currentUser;
      if (!user) return null;
      const newToken = await user.getIdToken(forceRefresh);
      // Persist for downstream usage
      localStorage.setItem(STORAGE_KEYS.FIREBASE_TOKEN, newToken);
      this.setAuthToken(newToken);
      return newToken;
    } catch (e) {
      console.warn('Failed to obtain fresh Firebase ID token:', e);
      return null;
    }
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
    // Request interceptors - async for token refresh
    this.axiosInstance.interceptors.request.use(
      (config) => this.handleRequest(config),
      this.handleRequestError.bind(this)
    );

    this.authAxiosInstance.interceptors.request.use(
      (config) => this.handleRequest(config),
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
  private async handleRequest(config: any): Promise<any> {
    // Check if token is expired and refresh if needed BEFORE making the request
    if (this.isTokenExpired() && auth?.currentUser) {
      try {
        console.log('Token expired, refreshing before request...');
        const freshToken = await this.getFreshFirebaseIdToken(true);
        if (freshToken) {
          console.log('Token refreshed successfully');
        }
      } catch (error) {
        console.warn('Failed to refresh token before request:', error);
      }
    }

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
    // CRITICAL FIX: Store token in single location (firebaseToken) for consistency
    localStorage.setItem(STORAGE_KEYS.FIREBASE_TOKEN, token);

    // Also store in ACCESS_TOKEN for backward compatibility (will be removed in migration)
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
    // Clear all auth-related data from localStorage
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.TOKEN_EXPIRY);
    localStorage.removeItem(STORAGE_KEYS.USER_DATA);
    localStorage.removeItem(STORAGE_KEYS.FIREBASE_TOKEN);

    // Also clear any other potential auth keys
    localStorage.removeItem('firebaseToken'); // Legacy key

    // Sign out from Firebase to clear Firebase's own auth state
    signOut(auth).catch((error) => {
      console.warn('Firebase signOut error:', error);
    });
  }

  public setRequestTimeout(timeout: number): void {
    this.currentConfig.timeout = timeout;
    this.axiosInstance.defaults.timeout = timeout;
    this.authAxiosInstance.defaults.timeout = timeout;
  }

  // Authentication Methods
  public async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      // Firebase-based login flow: ensure we have a fresh Firebase ID token
      let firebaseToken = localStorage.getItem(STORAGE_KEYS.FIREBASE_TOKEN);
      if (!firebaseToken) {
        // If no token in storage, try signing in with Firebase using provided credentials
        if (credentials?.email && credentials?.password) {
          try {
            await signInWithEmailAndPassword(auth, credentials.email, credentials.password);
          } catch (e: any) {
            console.error('Firebase sign-in error:', e);
            const errorCode = e?.code || 'unknown';
            const errorMessage = e?.message || 'Unknown error';

            // Provide user-friendly error messages based on Firebase error codes
            if (errorCode === 'auth/user-not-found') {
              throw new Error('No account found with this email. Please register first.');
            } else if (errorCode === 'auth/wrong-password') {
              throw new Error('Incorrect password. Please try again.');
            } else if (errorCode === 'auth/invalid-email') {
              throw new Error('Invalid email format.');
            } else if (errorCode === 'auth/user-disabled') {
              throw new Error('This account has been disabled.');
            } else if (errorCode === 'auth/too-many-requests') {
              throw new Error(
                'Too many failed login attempts. This account is temporarily locked for security. ' +
                'Please wait 15-30 minutes and try again, or reset your password using the "Forgot Password" link. ' +
                'You can also try signing in with Google if available.'
              );
            } else if (errorCode === 'auth/network-request-failed') {
              throw new Error('Network error. Please check your internet connection.');
            } else {
              throw new Error(`Firebase sign-in failed: ${errorMessage} (${errorCode})`);
            }
          }
        }
        // After sign-in (or if already signed in), obtain an ID token
        firebaseToken = await this.getFreshFirebaseIdToken(true) || null;
      }
      if (!firebaseToken) {
        throw new Error('Missing Firebase ID token. Please sign in with Firebase first.');
      }

      // Sync user with backend using Firebase token
      let syncResponse;
      try {
        syncResponse = await this.authAxiosInstance.post(
          '/auth/firebase-sync',
          {},
          { headers: { Authorization: `Bearer ${firebaseToken}` } }
        );
      } catch (e: any) {
        // If unauthorized, force refresh the Firebase token and retry once
        if (e?.response?.status === 401) {
          const refreshed = await this.getFreshFirebaseIdToken(true);
          if (!refreshed) throw e;
          firebaseToken = refreshed;
          syncResponse = await this.authAxiosInstance.post(
            '/auth/firebase-sync',
            {},
            { headers: { Authorization: `Bearer ${firebaseToken}` } }
          );
        } else {
          throw e;
        }
      }

      // Persist the Firebase token as our access token for subsequent requests
      this.setAuthToken(firebaseToken);

      // Persist user data if provided
      if (syncResponse?.data?.user) {
        localStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(syncResponse.data.user));
      }

      // Shape a LoginResponse-compatible object for callers
      let expiresIn = 3600;
      try {
        const decoded = jwtDecode<JwtPayload>(firebaseToken);
        if (decoded?.exp) {
          expiresIn = Math.max(0, Math.floor(decoded.exp * 1000 - Date.now()) / 1000);
        }
      } catch (_) {
        // ignore decode errors, fallback to default expiresIn
      }

      return {
        access_token: firebaseToken,
        user: syncResponse?.data?.user,
        expires_in: expiresIn,
      } as LoginResponse;
    } catch (error: any) {
      throw this.createApiError(error, 'LOGIN_FAILED');
    }
  }

  public async register(userData: RegisterRequest): Promise<LoginResponse> {
    try {
      // Step 1: Create Firebase account
      if (!userData.email || !userData.password) {
        throw new Error('Email and password are required for registration');
      }

      let firebaseUser;
      try {
        const userCredential = await createUserWithEmailAndPassword(
          auth,
          userData.email,
          userData.password
        );
        firebaseUser = userCredential.user;
      } catch (e: any) {
        console.error('Firebase registration error:', e);
        const errorCode = e?.code || 'unknown';
        const errorMessage = e?.message || 'Unknown error';

        // Provide user-friendly error messages based on Firebase error codes
        if (errorCode === 'auth/email-already-in-use') {
          throw new Error('An account with this email already exists. Please login instead.');
        } else if (errorCode === 'auth/invalid-email') {
          throw new Error('Invalid email format.');
        } else if (errorCode === 'auth/weak-password') {
          throw new Error('Password is too weak. Please use at least 6 characters.');
        } else if (errorCode === 'auth/operation-not-allowed') {
          throw new Error('Email/password registration is not enabled. Please contact support.');
        } else {
          throw new Error(`Registration failed: ${errorMessage} (${errorCode})`);
        }
      }

      // Step 2: Get Firebase ID token
      const firebaseToken = await firebaseUser.getIdToken();

      // Step 3: Sync with backend
      const syncResponse = await this.authAxiosInstance.post(
        '/auth/firebase-sync',
        {
          firstName: userData.first_name,
          lastName: userData.last_name
        },
        { headers: { Authorization: `Bearer ${firebaseToken}` } }
      );

      // Step 4: Store auth token
      this.setAuthToken(firebaseToken);

      // Step 5: Return user data
      return {
        user: syncResponse.data.user,
        access_token: firebaseToken,
        refresh_token: undefined,
        expires_in: 3600
      };
    } catch (error: any) {
      // If it's already a formatted error message, rethrow it
      if (error.message && !error.response) {
        throw error;
      }
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
    // Firebase-only refresh: ask Firebase SDK for a new ID token, then re-sync with backend
    try {
      console.log('🔄 [refreshToken] Starting token refresh process...');

      let firebaseToken = await this.getFreshFirebaseIdToken(true);
      if (!firebaseToken) {
        // Fallback: try existing stored token if available
        firebaseToken = localStorage.getItem(STORAGE_KEYS.FIREBASE_TOKEN);
      }
      if (!firebaseToken) {
        this.clearAuthToken();
        throw new Error('No Firebase ID token available');
      }

      console.log('✅ [refreshToken] Firebase token obtained, syncing with backend...');

      // CRITICAL FIX: Sync with backend is now REQUIRED, not optional
      // If backend doesn't accept the token, the refresh should fail
      try {
        await this.authAxiosInstance.post(
          '/api/auth/verify-token',
          {},
          {
            headers: { Authorization: `Bearer ${firebaseToken}` },
            timeout: 10000 // 10 second timeout
          }
        );
        console.log('✅ [refreshToken] Backend sync successful');
      } catch (syncError: any) {
        console.error('❌ [refreshToken] Backend sync failed:', syncError);

        // If backend rejects token with 401, this is a critical failure
        if (syncError.response?.status === 401) {
          console.error('🔒 [refreshToken] Backend rejected token - clearing auth and forcing re-login');
          this.clearAuthToken();
          throw new Error('Token rejected by backend - please log in again');
        }

        // For 5xx errors or timeouts, allow offline operation but log warning
        if (syncError.response?.status >= 500) {
          console.warn('⚠️ [refreshToken] Backend server error - allowing offline operation');
        } else if (syncError.code === 'ECONNABORTED' || syncError.message?.includes('timeout')) {
          console.warn('⚠️ [refreshToken] Backend timeout - allowing offline operation');
        } else {
          // For other errors, fail the refresh to be safe
          console.error('❌ [refreshToken] Unknown sync error - failing refresh for safety');
          this.clearAuthToken();
          throw new Error('Token refresh failed - backend sync error');
        }
      }

      // Keep using the Firebase token as our access token
      this.setAuthToken(firebaseToken);

      let expiresIn = 3600;
      try {
        const decoded = jwtDecode<JwtPayload>(firebaseToken);
        if (decoded?.exp) {
          expiresIn = Math.max(0, Math.floor((decoded.exp * 1000 - Date.now()) / 1000));
        }
      } catch (_) {
        // ignore decode errors
      }

      console.log(`✅ [refreshToken] Token refresh completed successfully (expires in ${expiresIn}s)`);

      return {
        access_token: firebaseToken,
        expires_in: expiresIn,
      } as RefreshTokenResponse;
    } catch (error: any) {
      console.error('❌ [refreshToken] Token refresh failed:', error);
      this.clearAuthToken();
      throw this.createApiError(error, 'TOKEN_REFRESH_FAILED');
    }
  }

  public async getCurrentUser(): Promise<User> {
    try {
      const { data } = await this.authAxiosInstance.get('/api/users/profile');
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
    // CRITICAL FIX: Use single source of truth for token storage
    // Priority: firebaseToken (primary) -> accessToken (legacy fallback)
    const firebaseToken = localStorage.getItem(STORAGE_KEYS.FIREBASE_TOKEN);
    if (firebaseToken) {
      return firebaseToken;
    }

    // Fallback to legacy accessToken if exists, but migrate it
    const legacyToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (legacyToken) {
      // Migrate legacy token to new storage key
      localStorage.setItem(STORAGE_KEYS.FIREBASE_TOKEN, legacyToken);
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      console.log('🔄 Migrated legacy access token to firebaseToken storage');
      return legacyToken;
    }

    return null;
  }

  public getTokenExpiry(): number | null {
    const expiry = localStorage.getItem(STORAGE_KEYS.TOKEN_EXPIRY);
    return expiry ? parseInt(expiry, 10) : null;
  }

  public isTokenExpired(): boolean {
    const expiry = this.getTokenExpiry();
    if (!expiry) return true;

    // Add 1 minute buffer before expiry (reduced from 5 minutes to prevent premature expiration)
    return Date.now() >= (expiry - 1 * 60 * 1000);
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
