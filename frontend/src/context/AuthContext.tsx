import { createContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import axios from "axios";

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
  const [accessToken, setAccessToken] = useState<string | null>(() =>
    localStorage.getItem("accessToken")
  );

  const api = axios.create({
    baseURL: import.meta.env.VITE_AUTH_API_URL || "http://localhost:5000/api",
    withCredentials: true,
  });

  api.interceptors.request.use((config) => {
    // Always get the latest token from localStorage
    const token = localStorage.getItem("accessToken");
    if (token) config.headers["Authorization"] = `Bearer ${token}`;
    return config;
  });

  let refreshPromise: Promise<unknown> | null = null;

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

  api.interceptors.response.use(
    (res) => res,
    async (error) => {
      const original = error.config;
      if (
        (error.response?.status === 401 || error.response?.status === 403) &&
        !original._retry
      ) {
        original._retry = true;
        if (!refreshPromise) {
          refreshPromise = api
            .post("/auth/refresh", {}, { withCredentials: true })
            .then(({ data }) => {
              setAccessToken(data.access_token);
              localStorage.setItem("accessToken", data.access_token);
              const decoded = JSON.parse(atob(data.access_token.split(".")[1]));
              setUser(decoded);
              return data.access_token;
            })
            .catch((err) => {
              console.log("Token refresh failed in interceptor:", err.message);
              setUser(null);
              setAccessToken(null);
              localStorage.removeItem("accessToken");

              // Only redirect on auth errors, not network errors
              if (
                err.response?.status === 401 ||
                err.response?.status === 403
              ) {
                console.log("Authentication failed - redirecting to login");
                // In development, don't auto-redirect to allow debugging
                // window.location.href = '/';
              }
              throw err;
            })
            .finally(() => {
              refreshPromise = null;
            });
        }
        try {
          const newToken = await refreshPromise;
          original.headers["Authorization"] = `Bearer ${newToken}`;
          return api(original);
        } catch (err) {
          return Promise.reject(err);
        }
      }
      return Promise.reject(error);
    }
  );

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
          refreshTokenSilently();
        }
      } catch (error) {
        console.log(
          "Invalid token in localStorage, clearing and trying refresh"
        );
        localStorage.removeItem("accessToken");
        if (hasRefreshToken()) {
          refreshTokenSilently();
        }
      }
    } else if (hasRefreshToken()) {
      // No access token but we might have a refresh token in cookies
      console.log("No access token found, attempting silent refresh");
      refreshTokenSilently();
    } else {
      console.log("No tokens found, user needs to login");
    }
  }, []);

  const refreshTokenSilently = async () => {
    try {
      const { data } = await api.post(
        "/auth/refresh",
        {},
        { withCredentials: true }
      );

      if (!data.access_token) {
        throw new Error("No access token received");
      }

      // Validate token structure
      const tokenParts = data.access_token.split(".");
      if (tokenParts.length !== 3) {
        throw new Error("Invalid token format");
      }

      const decoded = JSON.parse(atob(tokenParts[1]));

      // Check if token is not expired
      const currentTime = Date.now() / 1000;
      if (decoded.exp && decoded.exp <= currentTime) {
        throw new Error("Received expired token");
      }

      setAccessToken(data.access_token);
      localStorage.setItem("accessToken", data.access_token);
      setUser(decoded);

      console.log("Token refreshed successfully");
    } catch (error: any) {
      console.log("Silent refresh failed:", error.message);

      // Clear any stale data
      setUser(null);
      setAccessToken(null);
      localStorage.removeItem("accessToken");

      // If it's a 401/403, the refresh token is invalid/expired
      if (error.response?.status === 401 || error.response?.status === 403) {
        console.log("Refresh token expired - redirecting to login");
        // Don't redirect immediately in development, just log
        // window.location.href = '/';
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        userProfile,
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
