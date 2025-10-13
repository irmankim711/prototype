import axios from "axios";

/**
 * Enhanced Axios Instance with Token Refresh Interceptor
 * 
 * Features:
 * - Automatic token refresh on 401 responses
 * - Proper refresh token handling
 * - Comprehensive error handling and cleanup
 * - Request queuing during refresh
 * - Custom events for auth state changes
 * - Timeout protection for refresh requests
 * - Integration with AuthContext for better token management
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

// Debug: Log the API URL being used
console.log("🔗 Axios Base URL:", API_BASE_URL);
console.log("🔗 Environment Variables:", {
  VITE_API_URL: import.meta.env.VITE_API_URL,
  NODE_ENV: import.meta.env.NODE_ENV,
  DEV: import.meta.env.DEV
});

// Create axios instance with proper configuration
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Essential for cookies
  timeout: 30000, // 30 seconds timeout for better handling of slow API responses
});

// Track if we're currently refreshing to avoid multiple refresh calls
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (error?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });

  failedQueue = [];
};

/**
 * Clear all authentication-related data from localStorage
 */
const clearAllAuthData = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("tokenExpiry");
  localStorage.removeItem("userData");
  localStorage.removeItem("devBypassEnabled");
  localStorage.removeItem("devUser");
  
  // Clear any other potential token keys for backward compatibility
  localStorage.removeItem("token");
  localStorage.removeItem("quickAccessToken");
  
  console.log("🧹 All authentication data cleared from axios interceptor");
};

/**
 * Check if an error indicates permanent authentication failure
 */
const isPermanentAuthError = (error: any): boolean => {
  const status = error.response?.status;
  return status === 401 || status === 403 || status === 422;
};

/**
 * Check if a token is expired
 */
const isTokenExpired = (token: string): boolean => {
  try {
    const decoded = JSON.parse(atob(token.split(".")[1]));
    if (!decoded || !decoded.exp) return true;
    
    const currentTime = Math.floor(Date.now() / 1000);
    return decoded.exp <= currentTime;
  } catch (error) {
    console.error("Error checking token expiration:", error);
    return true;
  }
};

/**
 * Get token expiration time in milliseconds
 */
const getTokenExpirationTime = (token: string): number | null => {
  try {
    const decoded = JSON.parse(atob(token.split(".")[1]));
    return decoded?.exp ? decoded.exp * 1000 : null;
  } catch (error) {
    console.error("Error getting token expiration time:", error);
    return null;
  }
};

/**
 * Calculate time until token expiration in seconds
 */
const calculateTimeUntilExpiration = (token: string): number | null => {
  const expirationTime = getTokenExpirationTime(token);
  if (!expirationTime) return null;
  
  const currentTime = Date.now();
  const timeUntilExpiration = Math.floor((expirationTime - currentTime) / 1000);
  
  return timeUntilExpiration > 0 ? timeUntilExpiration : null;
};

/**
 * Check if token should be refreshed soon (within 5 minutes)
 */
const shouldRefreshToken = (token: string): boolean => {
  const timeUntilExpiration = calculateTimeUntilExpiration(token);
  if (!timeUntilExpiration) return true;
  
  const REFRESH_THRESHOLD = 5 * 60; // 5 minutes in seconds
  return timeUntilExpiration <= REFRESH_THRESHOLD;
};

// Request interceptor to add auth token and check expiration
axiosInstance.interceptors.request.use(
  (config: any) => {
    const token = localStorage.getItem("accessToken");
    
    if (token) {
      // Check if token is expired before making request
      if (isTokenExpired(token)) {
        console.warn("⚠️ Token expired, clearing and will attempt refresh on next 401");
        clearAllAuthData();
        return config; // Continue with request, let response interceptor handle 401
      }
      
      // Check if token should be refreshed soon
      if (shouldRefreshToken(token)) {
        console.log("🔄 Token expires soon, will refresh on next 401");
      }
      
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: any) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors and token refresh
axiosInstance.interceptors.response.use(
  (response: any) => {
    return response;
  },
  async (error: any) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      // Check if we have a refresh token before attempting refresh
      const refreshToken = localStorage.getItem("refreshToken");
      if (!refreshToken) {
        console.error("❌ No refresh token available - user must re-login");
        clearAllAuthData();
        
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('auth:token-expired', {
            detail: { reason: 'no_refresh_token' }
          }));
        }
        
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // If we're already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token: any) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return axiosInstance(originalRequest);
          })
          .catch((err: any) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        console.log("🔄 Attempting to refresh token...");

        // Get refresh token from localStorage
        const refreshToken = localStorage.getItem("refreshToken");
        if (!refreshToken) {
          throw new Error("No refresh token available");
        }

        // Make refresh request with refresh token in Authorization header
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/api/auth/refresh`,
          {},
          { 
            withCredentials: true,
            timeout: 10000, // 10 second timeout for refresh requests
            headers: {
              'Authorization': `Bearer ${refreshToken}`,
              'Content-Type': 'application/json'
            }
          }
        );

        const { access_token } = refreshResponse.data;

        if (access_token) {
          // Validate the new token
          if (isTokenExpired(access_token)) {
            throw new Error("Received expired token from refresh");
          }

          console.log("✅ Token refreshed successfully");
          localStorage.setItem("accessToken", access_token);

          // Update the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;

          // Process queued requests
          processQueue(null, access_token);

          // Retry the original request
          return axiosInstance(originalRequest);
        } else {
          throw new Error("No access token received from refresh response");
        }
      } catch (refreshError: any) {
        console.error("❌ Token refresh failed:", refreshError);

        // Clear all stored tokens on refresh failure
        clearAllAuthData();

        // Process queued requests with error
        processQueue(refreshError, null);

        // Determine if this is a permanent auth failure or temporary issue
        if (isPermanentAuthError(refreshError)) {
          console.error("❌ Permanent authentication failure - user must re-login");
          
          // Clear any remaining auth state
          if (typeof window !== 'undefined') {
            // Dispatch custom event for components to handle
            window.dispatchEvent(new CustomEvent('auth:token-expired', {
              detail: { 
                reason: 'refresh_failed', 
                error: refreshError.message || 'Unknown refresh error',
                status: refreshError.response?.status,
                data: refreshError.response?.data
              }
            }));
            
            // Optional: Redirect to login page
            // window.location.href = '/login';
          }
        } else {
          console.warn("⚠️ Temporary refresh failure - may retry on next request");
        }

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
