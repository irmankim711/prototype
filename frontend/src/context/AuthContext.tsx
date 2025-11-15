import { createContext, useState, useEffect, useContext, useCallback } from "react";
import type { ReactNode } from "react";
import axiosInstance from "../services/axiosInstance";
import { setTokenGetter } from "../services/formBuilder";
import { environmentConfig } from "../config/environment";
import {
  isTokenExpired as isTokenExpiredUtil,
  calculateTimeUntilExpiration,
  clearAllAuthData as clearAuthData
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
      const response = await api.get("/api/users/profile");
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

  // Secure token refresh function - with Firebase, tokens auto-refresh
  const refreshToken = async (): Promise<boolean> => {
    if (isDevelopmentBypass) {
      console.log("Skipping token refresh - development bypass active");
      return false;
    }

    try {
      console.log("🔄 Attempting to refresh Firebase token...");

      // Get fresh token from Firebase (Firebase handles token refresh automatically)
      const { getAuth } = await import("firebase/auth");
      const { auth } = await import("../config/firebase");

      const firebaseAuth = auth || getAuth();
      const currentUser = firebaseAuth.currentUser;

      if (!currentUser) {
        console.error("❌ No Firebase user found for token refresh");
        throw new Error("No authenticated user found");
      }

      // Force refresh the token
      const freshToken = await currentUser.getIdToken(true);

      // Store the new token
      setAccessToken(freshToken);
      localStorage.setItem("accessToken", freshToken);

      // Firebase tokens don't need expiration tracking - they auto-refresh
      setTokenExpiresIn(null);

      console.log("✅ Firebase token refreshed successfully");
      return true;
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
      // Authenticate with Firebase first
      console.log("🔐 Authenticating with Firebase...");

      // Dynamically import Firebase auth to authenticate the user
      const { getAuth, signInWithEmailAndPassword } = await import("firebase/auth");
      const { auth } = await import("../config/firebase");

      const firebaseAuth = auth || getAuth();
      const userCredential = await signInWithEmailAndPassword(firebaseAuth, email, password);

      // Get Firebase ID token
      const firebaseToken = await userCredential.user.getIdToken();
      console.log("✅ Firebase authentication successful");

      // Sync with backend using Firebase token
      console.log("🔄 Syncing with backend...");
      const { data } = await api.post(
        "/auth/login",
        {},  // Empty body - backend expects token in Authorization header
        {
          withCredentials: true,
          headers: {
            'Authorization': `Bearer ${firebaseToken}`
          }
        }
      );

      // Backend returns user data but NOT an access_token (uses Firebase token instead)
      // Store the Firebase token as our access token
      setAccessToken(firebaseToken);
      localStorage.setItem("accessToken", firebaseToken);

      // Set user data from backend response
      if (data.user) {
        const userData: User = {
          id: data.user.id,
          email: data.user.email,
          username: data.user.username || data.user.email?.split('@')[0] || '',
          role: data.user.role || 'user',
          is_active: data.user.is_active !== false,
          first_name: data.user.first_name,
          last_name: data.user.last_name,
          full_name: data.user.full_name || `${data.user.first_name || ''} ${data.user.last_name || ''}`.trim()
        };
        setUser(userData);
        console.log("✅ User data set from backend");
      }

      // Firebase tokens don't have traditional JWT expiration tracking
      // They auto-refresh through Firebase SDK
      setTokenExpiresIn(null);

      // Fetch full user profile after successful login
      try {
        await fetchUserProfile();
      } catch (error) {
        console.log(
          "Could not fetch user profile after login, continuing anyway"
        );
      }

      console.log("✅ Login successful");
    } catch (error: any) {
      console.error("❌ Login failed:", error);

      // Provide more helpful error messages for Firebase errors
      if (error.code === 'auth/user-not-found') {
        throw new Error("No account found with this email address");
      } else if (error.code === 'auth/wrong-password') {
        throw new Error("Invalid email or password");
      } else if (error.code === 'auth/invalid-email') {
        throw new Error("Invalid email address format");
      } else if (error.code === 'auth/user-disabled') {
        throw new Error("This account has been disabled");
      } else if (error.code === 'auth/too-many-requests') {
        throw new Error("Too many failed login attempts. Please try again later");
      }

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
      console.log("📝 Registering new user with Firebase...");

      // Create user with Firebase Auth
      const { getAuth, createUserWithEmailAndPassword } = await import("firebase/auth");
      const { auth } = await import("../config/firebase");

      const firebaseAuth = auth || getAuth();
      const userCredential = await createUserWithEmailAndPassword(firebaseAuth, email, password);

      // Get Firebase ID token
      const firebaseToken = await userCredential.user.getIdToken();
      console.log("✅ Firebase registration successful");

      // Sync with backend
      console.log("🔄 Syncing new user with backend...");
      await api.post(
        "/auth/register",
        { organizationName },  // Optional organization name
        {
          withCredentials: true,
          headers: {
            'Authorization': `Bearer ${firebaseToken}`
          }
        }
      );

      console.log("✅ User registered and synced with backend");
    } catch (error: any) {
      console.error("Registration failed:", error);

      // Provide helpful Firebase error messages
      if (error.code === 'auth/email-already-in-use') {
        throw new Error("An account with this email already exists");
      } else if (error.code === 'auth/weak-password') {
        throw new Error("Password should be at least 6 characters");
      } else if (error.code === 'auth/invalid-email') {
        throw new Error("Invalid email address format");
      }

      throw error;
    }
  }

  async function logout() {
    try {
      if (!isDevelopmentBypass) {
        // Sign out from Firebase first
        try {
          const { getAuth, signOut } = await import("firebase/auth");
          const { auth } = await import("../config/firebase");
          const firebaseAuth = auth || getAuth();
          await signOut(firebaseAuth);
          console.log("✅ Signed out from Firebase");
        } catch (firebaseError) {
          console.warn("Firebase signout failed, continuing:", firebaseError);
        }

        // Attempt to call logout endpoint
        try {
          await api.post("/api/auth/logout");
        } catch (apiError) {
          console.warn("Logout API call failed, continuing with local cleanup:", apiError);
        }
      }
    } catch (error) {
      console.warn("Logout error, continuing with local cleanup:", error);
    } finally {
      // Always clear local data regardless of API call success
      clearAllAuthData();
      console.log("✅ Logout completed successfully");
    }
  }

  useEffect(() => {
    // On mount, listen to Firebase auth state changes
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

        // Set up Firebase auth state listener
        const { getAuth, onAuthStateChanged } = await import("firebase/auth");
        const { auth } = await import("../config/firebase");

        const firebaseAuth = auth || getAuth();

        // Listen to auth state changes
        const unsubscribe = onAuthStateChanged(firebaseAuth, async (firebaseUser) => {
          if (firebaseUser) {
            // User is signed in
            console.log("🔄 Firebase user detected, syncing with backend...");

            try {
              // Get Firebase ID token
              const firebaseToken = await firebaseUser.getIdToken();

              // Store token
              setAccessToken(firebaseToken);
              localStorage.setItem("accessToken", firebaseToken);

              // Sync with backend to get full user data
              try {
                const { data } = await api.post(
                  "/auth/login",
                  {},
                  {
                    withCredentials: true,
                    headers: {
                      'Authorization': `Bearer ${firebaseToken}`
                    }
                  }
                );

                if (data.user) {
                  const userData: User = {
                    id: data.user.id,
                    email: data.user.email,
                    username: data.user.username || data.user.email?.split('@')[0] || '',
                    role: data.user.role || 'user',
                    is_active: data.user.is_active !== false,
                    first_name: data.user.first_name,
                    last_name: data.user.last_name,
                    full_name: data.user.full_name || `${data.user.first_name || ''} ${data.user.last_name || ''}`.trim()
                  };
                  setUser(userData);
                  console.log("✅ User restored from Firebase auth");
                }
              } catch (syncError) {
                console.warn("Backend sync failed, using Firebase data only:", syncError);
                // Fall back to Firebase user data
                const userData: User = {
                  id: 0,  // Temporary ID until backend sync
                  email: firebaseUser.email || '',
                  username: firebaseUser.email?.split('@')[0] || '',
                  role: 'user',
                  is_active: true,
                  first_name: firebaseUser.displayName?.split(' ')[0],
                  last_name: firebaseUser.displayName?.split(' ')[1],
                  full_name: firebaseUser.displayName || ''
                };
                setUser(userData);
              }
            } catch (error) {
              console.error("Error restoring Firebase auth:", error);
              clearAllAuthData();
            }
          } else {
            // User is signed out
            console.log("ℹ️ No Firebase user - user needs to login");
            setUser(null);
            setAccessToken(null);
            setUserProfile(null);
          }

          setIsLoading(false);
        });

        // Cleanup subscription on unmount
        return () => unsubscribe();

      } catch (error) {
        console.log("❌ Error during auth initialization:", error);
        // Clear any potentially corrupted data
        clearAllAuthData();
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
