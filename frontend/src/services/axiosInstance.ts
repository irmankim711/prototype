import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

// Create axios instance with proper configuration
const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Essential for cookies
  timeout: 10000,
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

// Request interceptor to add auth token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors and token refresh
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If we're already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return axiosInstance(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        console.log("Attempting to refresh token...");

        // Make refresh request with credentials
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        );

        const { access_token } = refreshResponse.data;

        if (access_token) {
          console.log("Token refreshed successfully");
          localStorage.setItem("accessToken", access_token);

          // Update the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;

          // Process queued requests
          processQueue(null, access_token);

          // Retry the original request
          return axiosInstance(originalRequest);
        } else {
          throw new Error("No access token received");
        }
      } catch (refreshError) {
        console.log("Token refresh failed:", refreshError);

        // Clear stored tokens
        localStorage.removeItem("accessToken");

        // Process queued requests with error
        processQueue(refreshError, null);

        // Only redirect to login if this is an auth error, not a network error
        if (
          refreshError.response?.status === 401 ||
          refreshError.response?.status === 403
        ) {
          console.log("Authentication failed - redirecting to login");
          // In development, we might want to avoid auto-redirect for debugging
          // Uncomment the next line for production:
          // window.location.href = '/';
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
