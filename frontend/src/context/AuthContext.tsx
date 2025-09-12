import { createContext, useState, useEffect, useContext, useCallback } from "react";
import type { ReactNode } from "react";
import axiosInstance from "../services/axiosInstance";
import { setTokenGetter } from "../services/formBuilder";
import { environmentConfig } from "../config/environment";
import {
  decodeJWT,
  isTokenExpired as isTokenExpiredUtil,
  calculateTimeUntilExpiration,
  clearAllAuthData as clearAuthData,
  logTokenInfo
} from "../utils/tokenUtils";

interface User {
  id: number;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  role: string;
  organization_id?: number;
  avatar_url?: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  userProfile: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isDevelopmentBypass: boolean;
  tokenExpiresIn: number | null; // seconds until expiration
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    organizationName?: string;
  }) => Promise<void>;
  fetchUserProfile: () => Promise<void>;
  refreshUserProfile: () => Promise<void>;
  enableDevelopmentBypass: () => void;
  disableDevelopmentBypass: () => void;
  refreshToken: () => Promise<boolean>;
  isTokenExpired: () => boolean;
  clearAllAuthData: () => void;
}

export const AuthContext = createContext<AuthContextType>(
  {} as AuthContextType
);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [accessToken, setAccessToken] = useState<string | null>(() =>
    localStorage.getItem("accessToken")
  );
  const [isDevelopmentBypass, setIsDevelopmentBypass] = useState(false);
  const [tokenExpiresIn, setTokenExpiresIn] = useState<number | null>(null);

  // Check if development bypass is enabled
  const isDevBypassEnabled = environmentConfig.isDevelopment && 
    environmentConfig.features.authBypass;

  // Set up token getter for formBuilder service
  useEffect(() => {
    setTokenGetter(() => accessToken);
  }, [accessToken]);

  // Update token expiration countdown
  useEffect(() => {
    if (!accessToken || isDevelopmentBypass) {
      setTokenExpiresIn(null);
      return;
    }

    const updateExpiration = () => {
      const timeUntilExpiration = calculateTimeUntilExpiration(accessToken);
      setTokenExpiresIn(timeUntilExpiration);
    };

    // Update immediately
    updateExpiration();

    // Update every minute
    const interval = setInterval(updateExpiration, 60000);

    return () => clearInterval(interval);
  }, [accessToken, isDevelopmentBypass]);

  // Auto-refresh token before expiration (5 minutes before)
  useEffect(() => {
    if (!accessToken || isDevelopmentBypass || !tokenExpiresIn) return;

    const REFRESH_THRESHOLD = 5 * 60; // 5 minutes in seconds
    
    if (tokenExpiresIn <= REFRESH_THRESHOLD) {
      console.log("🔄 Token expires soon, auto-refreshing...");
      refreshToken().catch(error => {
        console.error("Auto-refresh failed:", error);
      });
    }
  }, [tokenExpiresIn, accessToken, isDevelopmentBypass]);

  // Use the configured axios instance
  const api = axiosInstance;

  // Clear all authentication data
  const clearAllAuthData = useCallback(() => {
    // Clear state
    setUser(null);
    setUserProfile(null);
    setAccessToken(null);
    setIsDevelopmentBypass(false);
    setTokenExpiresIn(null);

    // Clear localStorage using utility function
    clearAuthData();
  }, []);

  // Check if token is expired
  const isTokenExpired = useCallback((): boolean => {
    if (!accessToken || isDevelopmentBypass) return true;
    return isTokenExpiredUtil(accessToken);
  }, [accessToken, isDevelopmentBypass]);

  // Development authentication bypass
  const enableDevelopmentBypass = () => {
    if (!isDevBypassEnabled) {
      console.warn("Development bypass not enabled in this environment");
      return;
    }

    const devUser: User = {
      id: parseInt(environmentConfig.devAuth.userId),
      email: environmentConfig.devAuth.userEmail,
      username: environmentConfig.devAuth.userEmail.split('@')[0],
      role: environmentConfig.devAuth.userRole,
      is_active: true,
      first_name: "Development",
      last_name: "User",
      full_name: "Development User"
    };

    setUser(devUser);
    setUserProfile(devUser);
    setAccessToken("dev-bypass-token");
    setIsDevelopmentBypass(true);
    setTokenExpiresIn(null);
    
    // Store in localStorage for persistence
    localStorage.setItem("devBypassEnabled", "true");
    localStorage.setItem("devUser", JSON.stringify(devUser));
    
    console.log("🔓 Development authentication bypass enabled", devUser);
  };

  const disableDevelopmentBypass = () => {
    clearAllAuthData();
    console.log("🔒 Development authentication bypass disabled");
  };

  // Fetch user profile from backend
  const fetchUserProfile = async () => {
    if (isDevelopmentBypass) {
      console.log("Skipping profile fetch - development bypass active");
      return null;
    }

    try {
      const response = await api.get("/users/profile");
      const profileData = response.data;
      setUserProfile(profileData);
      console.log("User profile fetched successfully");
      return profileData;
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      // Don't throw error, just log it as this is optional
      return null;
    }
  };

  const refreshUserProfile = async () => {
    if (!accessToken || isDevelopmentBypass) return;
    await fetchUserProfile();
  };

  // Secure token refresh function
  const refreshToken = async (): Promise<boolean> => {
    if (isDevelopmentBypass) {
      console.log("Skipping token refresh - development bypass active");
      return false;
    }

    try {
      console.log("🔄 Attempting to refresh token...");
      
      const { data } = await api.post(
        "/auth/refresh",
        {},
        { 
          withCredentials: true,
          timeout: 10000 // 10 second timeout for refresh requests
        }
      );

      if (data.access_token) {
        // Validate the new token
        if (isTokenExpiredUtil(data.access_token)) {
          console.error("❌ Received expired token from refresh");
          throw new Error("Received expired token from refresh");
        }

        // Store the new token
        setAccessToken(data.access_token);
        localStorage.setItem("accessToken", data.access_token);

        // Decode and set user from new token
        const decoded = decodeJWT(data.access_token);
        if (decoded) {
          // Convert TokenPayload to User format
          const userData: User = {
            id: typeof decoded.sub === 'number' ? decoded.sub : parseInt(decoded.sub || '0'),
            email: decoded.email || '',
            username: decoded.username || '',
            role: decoded.role || '',
            is_active: true,
            first_name: decoded.first_name,
            last_name: decoded.last_name,
            full_name: decoded.full_name
          };
          setUser(userData);
        }

        // Update expiration tracking
        const timeUntilExpiration = calculateTimeUntilExpiration(data.access_token);
        setTokenExpiresIn(timeUntilExpiration);

        // Log token info for debugging
        logTokenInfo(data.access_token, "Refreshed Token");

        console.log("✅ Token refreshed successfully");
        return true;
      } else {
        throw new Error("No access token received from refresh response");
      }
    } catch (error: any) {
      console.error("❌ Token refresh failed:", error.message);
      
      // Clear stale data on refresh failure
      clearAllAuthData();
      
      // Dispatch custom event for components to handle
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth:token-expired', {
          detail: { reason: 'refresh_failed', error: error.message }
        }));
      }
      
      return false;
    }
  };

  async function login(email: string, password: string) {
    try {
      const { data } = await api.post(
        "/auth/login",
        { email, password },
        { withCredentials: true }
      );
      
      if (!data.access_token) {
        throw new Error("No access token received from login");
      }

      // Validate the received token
      if (isTokenExpiredUtil(data.access_token)) {
        throw new Error("Received expired token from login");
      }

      // Store the token
      setAccessToken(data.access_token);
      localStorage.setItem("accessToken", data.access_token);
      
      // Decode and set user
      const decoded = decodeJWT(data.access_token);
      if (decoded) {
        // Convert TokenPayload to User format
        const userData: User = {
          id: typeof decoded.sub === 'number' ? decoded.sub : parseInt(decoded.sub || '0'),
          email: decoded.email || '',
          username: decoded.username || '',
          role: decoded.role || '',
          is_active: true,
          first_name: decoded.first_name,
          last_name: decoded.last_name,
          full_name: decoded.full_name
        };
        setUser(userData);
      } else {
        throw new Error("Failed to decode user information from token");
      }

      // Update expiration tracking
      const timeUntilExpiration = calculateTimeUntilExpiration(data.access_token);
      setTokenExpiresIn(timeUntilExpiration);

      // Log token info for debugging
      logTokenInfo(data.access_token, "Login Token");

      // Fetch full user profile after successful login
      try {
        await fetchUserProfile();
      } catch (error) {
        console.log(
          "Could not fetch user profile after login, continuing anyway"
        );
      }

      console.log("✅ Login successful");
    } catch (error) {
      console.error("❌ Login failed:", error);
      throw error;
    }
  }

  async function register({
    email,
    password,
    organizationName,
  }: {
    email: string;
    password: string;
    organizationName?: string;
  }) {
    try {
      await api.post("/auth/register", { email, password, organizationName });
    } catch (error) {
      console.error("Registration failed:", error);
      throw error;
    }
  }

  async function logout() {
    try {
      if (!isDevelopmentBypass) {
        // Attempt to call logout endpoint
        await api.post("/api/auth/logout");
      }
    } catch (error) {
      console.warn("Logout API call failed, continuing with local cleanup:", error);
    } finally {
      // Always clear local data regardless of API call success
      clearAllAuthData();
      console.log("✅ Logout completed successfully");
    }
  }

  // Check if we likely have a refresh token (by checking if we've logged in before)
  const hasRefreshToken = () => {
    // Simple heuristic: if we have any auth-related data, we might have a refresh token
    return (
      localStorage.getItem("accessToken") !== null ||
      document.cookie.includes("refresh_token")
    );
  };

  useEffect(() => {
    // On mount, try to restore user from token in localStorage
    const initializeAuth = async () => {
      try {
        // Check for development bypass first
        const devBypassEnabled = localStorage.getItem("devBypassEnabled") === "true";
        if (devBypassEnabled && isDevBypassEnabled) {
          const devUser = localStorage.getItem("devUser");
          if (devUser) {
            const parsedUser = JSON.parse(devUser);
            setUser(parsedUser);
            setUserProfile(parsedUser);
            setAccessToken("dev-bypass-token");
            setIsDevelopmentBypass(true);
            setTokenExpiresIn(null);
            console.log("🔓 Restored development bypass from localStorage");
            setIsLoading(false);
            return;
          }
        }

        // Check for tokens in multiple possible storage keys (for backward compatibility)
        const token = localStorage.getItem("accessToken") || 
                     localStorage.getItem("token") || 
                     localStorage.getItem("quickAccessToken");

        if (token) {
          try {
            // Validate token format and expiration
            if (isTokenExpiredUtil(token)) {
              console.log("⚠️ Access token expired, attempting refresh");
              // Clear expired token
              localStorage.removeItem("accessToken");
              localStorage.removeItem("token");
              localStorage.removeItem("quickAccessToken");
              
              if (hasRefreshToken()) {
                await refreshToken();
              }
            } else {
              // Token is valid
              const decoded = decodeJWT(token);
              if (decoded) {
                setAccessToken(token);
                
                // Convert TokenPayload to User format
                const userData: User = {
                  id: typeof decoded.sub === 'number' ? decoded.sub : parseInt(decoded.sub || '0'),
                  email: decoded.email || '',
                  username: decoded.username || '',
                  role: decoded.role || '',
                  is_active: true,
                  first_name: decoded.first_name,
                  last_name: decoded.last_name,
                  full_name: decoded.full_name
                };
                setUser(userData);
                
                // Standardize storage key
                localStorage.setItem("accessToken", token);
                localStorage.removeItem("token");
                localStorage.removeItem("quickAccessToken");
                
                // Update expiration tracking
                const timeUntilExpiration = calculateTimeUntilExpiration(token);
                setTokenExpiresIn(timeUntilExpiration);
                
                // Log token info for debugging
                logTokenInfo(token, "Restored Token");
                
                console.log("✅ Restored valid access token from localStorage");
              } else {
                throw new Error("Failed to decode token");
              }
            }
          } catch (error) {
            console.log(
              "❌ Invalid token in localStorage, clearing and trying refresh"
            );
            // Clear all possible token keys
            localStorage.removeItem("accessToken");
            localStorage.removeItem("token");
            localStorage.removeItem("quickAccessToken");
            
            if (hasRefreshToken()) {
              await refreshToken();
            }
          }
        } else if (hasRefreshToken()) {
          // No access token but we might have a refresh token in cookies
          console.log("🔄 No access token found, attempting silent refresh");
          await refreshToken();
        } else {
          // This is normal for new users - not an error
          console.log("ℹ️ No authentication tokens found - user needs to login");
        }
      } catch (error) {
        console.log("❌ Error during auth initialization:", error);
        // Clear any potentially corrupted data
        clearAllAuthData();
      } finally {
        // Always set loading to false after initialization is complete
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [isDevBypassEnabled, clearAllAuthData]);

  // Computed authentication state
  const isAuthenticated = !!(user || isDevelopmentBypass);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        userProfile,
        isLoading,
        isAuthenticated,
        isDevelopmentBypass,
        tokenExpiresIn,
        login,
        logout,
        register,
        fetchUserProfile,
        refreshUserProfile,
        enableDevelopmentBypass,
        disableDevelopmentBypass,
        refreshToken,
        isTokenExpired,
        clearAllAuthData,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// useAuth hook for consuming the context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
