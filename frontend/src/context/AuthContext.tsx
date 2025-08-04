import { createContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import axiosInstance from "../services/axiosInstance";
import { setTokenGetter } from "../services/formBuilder";

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
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    organizationName?: string;
  }) => Promise<void>;
  fetchUserProfile: () => Promise<void>;
  refreshUserProfile: () => Promise<void>;
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

  // Set up token getter for formBuilder service
  useEffect(() => {
    setTokenGetter(() => accessToken);
  }, [accessToken]);

  // Use the configured axios instance
  const api = axiosInstance;

  // Fetch user profile from backend
  const fetchUserProfile = async () => {
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
    if (!accessToken) return;
    await fetchUserProfile();
  };

  async function login(email: string, password: string) {
    const { data } = await api.post(
      "/auth/login",
      { email, password },
      { withCredentials: true }
    );
    setAccessToken(data.access_token);
    localStorage.setItem("accessToken", data.access_token);
    const decoded = JSON.parse(atob(data.access_token.split(".")[1]));
    setUser(decoded);

    // Fetch full user profile after successful login
    try {
      await fetchUserProfile();
    } catch (error) {
      console.log(
        "Could not fetch user profile after login, continuing anyway"
      );
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
    await api.post("/auth/register", { email, password, organizationName });
  }

  async function logout() {
    await api.post("/auth/logout");
    setUser(null);
    setAccessToken(null);
    localStorage.removeItem("accessToken");
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
        const token = localStorage.getItem("accessToken");

        if (token) {
          try {
            const decoded = JSON.parse(atob(token.split(".")[1]));
            const currentTime = Date.now() / 1000;

            if (decoded.exp && decoded.exp > currentTime) {
              // Token is still valid
              setAccessToken(token);
              setUser(decoded);
              console.log("Restored valid access token from localStorage");
            } else {
              // Token is expired, try to refresh
              console.log("Access token expired, attempting refresh");
              await refreshTokenSilently();
            }
          } catch (error) {
            console.log(
              "Invalid token in localStorage, clearing and trying refresh"
            );
            localStorage.removeItem("accessToken");
            if (hasRefreshToken()) {
              await refreshTokenSilently();
            }
          }
        } else if (hasRefreshToken()) {
          // No access token but we might have a refresh token in cookies
          console.log("No access token found, attempting silent refresh");
          await refreshTokenSilently();
        } else {
          console.log("No tokens found, user needs to login");
        }
      } catch (error) {
        console.log("Error during auth initialization:", error);
      } finally {
        // Always set loading to false after initialization is complete
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const refreshTokenSilently = async () => {
    try {
      console.log("Attempting to refresh token...");
      const { data } = await api.post(
        "/auth/refresh",
        {},
        { withCredentials: true }
      );

      if (data.access_token) {
        setAccessToken(data.access_token);
        localStorage.setItem("accessToken", data.access_token);

        // Decode user from token
        const decoded = JSON.parse(atob(data.access_token.split(".")[1]));
        setUser(decoded);

        console.log("Token refreshed successfully");
      } else {
        throw new Error("No access token received");
      }
    } catch (error: any) {
      console.log("Silent refresh failed:", error.message);

      // Clear any stale data
      setUser(null);
      setAccessToken(null);
      localStorage.removeItem("accessToken");

      // The interceptor will handle redirect logic
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        userProfile,
        isLoading,
        login,
        logout,
        register,
        fetchUserProfile,
        refreshUserProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
