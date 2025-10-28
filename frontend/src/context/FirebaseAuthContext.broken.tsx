/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
import {
  createContext,
  useState,
  useEffect,
  useContext,
  useCallback,
  useRef,
} from "react";
import type { ReactNode } from "react";
import type { User as FirebaseUser } from "firebase/auth";
import type { Auth } from "firebase/auth";
import type { GoogleAuthProvider as GoogleProviderType } from "firebase/auth";
import axiosInstance from "../services/axiosInstance";
import { environmentConfig } from "../config/environment";

// Helper types
type AdditionalData = { displayName?: string; [key: string]: any };

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
  firebase_uid?: string;
}

interface AuthContextType {
  user: User | null;
  firebaseUser: FirebaseUser | null;
  userProfile: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isDevelopmentBypass: boolean;
  loginWithEmail: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  registerWithEmail: (
    email: string,
    password: string,
    additionalData?: AdditionalData
  ) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  fetchUserProfile: () => Promise<void>;
  refreshUserProfile: () => Promise<void>;
  updateUserProfile: (data: Partial<User>) => Promise<void>;
  enableDevelopmentBypass: () => void;
  disableDevelopmentBypass: () => void;
  clearAllAuthData: () => void;
}

const defaultAuthContext: AuthContextType = {
  user: null,
  firebaseUser: null,
  userProfile: null,
  isLoading: false,
  isAuthenticated: false,
  isDevelopmentBypass: false,
  loginWithEmail: async () => { throw new Error("FirebaseAuthProvider not found"); },
  loginWithGoogle: async () => { throw new Error("FirebaseAuthProvider not found"); },
  registerWithEmail: async () => { throw new Error("FirebaseAuthProvider not found"); },
  logout: async () => { throw new Error("FirebaseAuthProvider not found"); },
  resetPassword: async () => { throw new Error("FirebaseAuthProvider not found"); },
  fetchUserProfile: async () => {},
  refreshUserProfile: async () => {},
  updateUserProfile: async () => { throw new Error("FirebaseAuthProvider not found"); },
  enableDevelopmentBypass: () => {},
  disableDevelopmentBypass: () => {},
  clearAllAuthData: () => {},
};

export const FirebaseAuthContext = createContext<AuthContextType>(defaultAuthContext);

export function FirebaseAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [userProfile, setUserProfile] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDevelopmentBypass, setIsDevelopmentBypass] = useState(false);

  // Refs for Firebase instances
  const authRef = useRef<Auth | null>(null);
  const googleProviderRef = useRef<GoogleProviderType | null>(null);
  const initializingRef = useRef<boolean>(false);

  // Check if development bypass is enabled
  const isDevBypassEnabled = environmentConfig.isDevelopment && environmentConfig.features.authBypass;

  // Clear all authentication data
  const clearAllAuthData = useCallback(() => {
    setUser(null);
    setFirebaseUser(null);
    setUserProfile(null);
    setIsDevelopmentBypass(false);
    localStorage.removeItem("accessToken");
    localStorage.removeItem("firebaseToken");
    localStorage.removeItem("devBypassEnabled");
    localStorage.removeItem("devUser");
    if (axiosInstance.defaults.headers.common) {
      delete axiosInstance.defaults.headers.common["Authorization"];
    }
  }, []);

  // Simplified Firebase initialization
  const ensureFirebaseAuth = useCallback(async (): Promise<Auth | null> => {
    if (authRef.current) return authRef.current;
    if (initializingRef.current) return null; // Prevent concurrent initialization

    initializingRef.current = true;
    try {
      const { auth, googleProvider } = await import("../config/firebase");
      authRef.current = auth || null;
      googleProviderRef.current = googleProvider || null;
      return auth || null;
    } catch (error) {
      console.error("Firebase initialization failed:", error);
      return null;
    } finally {
      initializingRef.current = false;
    }
  }, []);

  // Development authentication bypass
  const enableDevelopmentBypass = useCallback(() => {
    if (!isDevBypassEnabled) {
      console.warn("Development bypass not enabled in this environment");
      return;
    }

    const devUser: User = {
      id: parseInt(environmentConfig.devAuth.userId),
      email: environmentConfig.devAuth.userEmail,
      username: environmentConfig.devAuth.userEmail.split("@")[0],
      role: environmentConfig.devAuth.userRole,
      is_active: true,
      first_name: "Development",
      last_name: "User",
      full_name: "Development User",
    };

    setUser(devUser);
    setUserProfile(devUser);
    setIsDevelopmentBypass(true);
    localStorage.setItem("devBypassEnabled", "true");
    localStorage.setItem("devUser", JSON.stringify(devUser));
  }, [isDevBypassEnabled]);

  const disableDevelopmentBypass = useCallback(() => {
    clearAllAuthData();
  }, [clearAllAuthData]);

  // Simplified backend sync - no infinite retry loops
  const syncUserWithBackend = async (firebaseUser: FirebaseUser): Promise<User | null> => {
    try {
      const idToken = await firebaseUser.getIdToken(true);
      const syncPayload = {
        firstName: firebaseUser.displayName?.split(" ")[0] || "",
        lastName: firebaseUser.displayName?.split(" ").slice(1).join(" ") || "",
        displayName: firebaseUser.displayName,
        photoUrl: firebaseUser.photoURL,
        emailVerified: firebaseUser.emailVerified,
      };

      const response = await axiosInstance.post("/auth/firebase-sync", syncPayload, {
        headers: {
          Authorization: `Bearer ${idToken}`,
          "Content-Type": "application/json",
        },
        timeout: 10000,
      });

      axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${idToken}`;
      localStorage.setItem("firebaseToken", idToken);
      return response.data.user;
    } catch (error) {
      console.error("Backend sync failed:", error);
      throw error;
    }
  };

  // Fetch user profile
  const fetchUserProfile = useCallback(async () => {
    if (isDevelopmentBypass || !firebaseUser) return;

    try {
      const response = await axiosInstance.get("/auth/profile");
      setUserProfile(response.data);
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
    }
  }, [isDevelopmentBypass, firebaseUser]);

  const refreshUserProfile = useCallback(async () => {
    if (!firebaseUser || isDevelopmentBypass) return;
    await fetchUserProfile();
  }, [firebaseUser, isDevelopmentBypass, fetchUserProfile]);

  // Update user profile
  const updateUserProfile = async (data: Partial<User>) => {
    try {
      const response = await axiosInstance.put("/users/profile", data);
      setUserProfile(response.data.user);

      if (firebaseUser && (data.first_name || data.last_name)) {
        const displayName = `${data.first_name || ""} ${data.last_name || ""}`.trim();
        const { updateProfile } = await import("firebase/auth");
        await updateProfile(firebaseUser, { displayName });
      }
    } catch (error) {
      console.error("Failed to update user profile:", error);
      throw error;
    }
  };

  // Authentication methods
  const loginWithEmail = async (email: string, password: string) => {
    try {
      setIsLoading(true);
      const authInstance = await ensureFirebaseAuth();
      if (!authInstance) throw new Error("Authentication service unavailable");

      const { signInWithEmailAndPassword } = await import("firebase/auth");
      await signInWithEmailAndPassword(authInstance, email, password);
    } catch (error: any) {
      console.error("Email login failed:", error);
      let errorMessage = "Login failed";
      if (error.code === "auth/user-not-found") errorMessage = "No account found with this email address";
      else if (error.code === "auth/wrong-password") errorMessage = "Incorrect password";
      else if (error.code === "auth/invalid-email") errorMessage = "Invalid email address";
      else if (error.code === "auth/too-many-requests") errorMessage = "Too many failed attempts. Please try again later";
      else if (error.message) errorMessage = error.message;
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithGoogle = async () => {
    try {
      setIsLoading(true);
      const authInstance = await ensureFirebaseAuth();
      if (!authInstance || !googleProviderRef.current) {
        throw new Error("Google sign-in not available");
      }

      const { signInWithPopup } = await import("firebase/auth");
      await signInWithPopup(authInstance, googleProviderRef.current);
    } catch (error: any) {
      console.error("Google login failed:", error);
      let errorMessage = "Google login failed";
      if (error.code === "auth/popup-closed-by-user") errorMessage = "Login cancelled by user";
      else if (error.code === "auth/popup-blocked") errorMessage = "Popup blocked. Please allow popups and try again";
      else if (error.message) errorMessage = error.message;
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const registerWithEmail = async (email: string, password: string, additionalData?: AdditionalData) => {
    try {
      setIsLoading(true);
      const authInstance = await ensureFirebaseAuth();
      if (!authInstance) throw new Error("Authentication service unavailable");

      const { createUserWithEmailAndPassword } = await import("firebase/auth");
      const userCredential = await createUserWithEmailAndPassword(authInstance, email, password);
      const firebaseUser = userCredential.user;

      if (additionalData?.displayName) {
        const { updateProfile } = await import("firebase/auth");
        await updateProfile(firebaseUser, { displayName: additionalData.displayName });
      }

      const backendUser = await syncUserWithBackend(firebaseUser);
      if (backendUser) setUser(backendUser);
    } catch (error: any) {
      console.error("Registration failed:", error);
      throw new Error(error.message || "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (!isDevelopmentBypass && authRef.current) {
        const { signOut } = await import("firebase/auth");
        await signOut(authRef.current);
      }
      clearAllAuthData();
    } catch (error) {
      console.error("Logout failed:", error);
      clearAllAuthData(); // Clear local data even if Firebase signout fails
    }
  };

  const resetPassword = async (email: string) => {
    try {
      if (!authRef.current) throw new Error("Authentication service unavailable");
      const { sendPasswordResetEmail } = await import("firebase/auth");
      await sendPasswordResetEmail(authRef.current, email);
    } catch (error: any) {
      console.error("Password reset failed:", error);
      throw new Error(error.message || "Password reset failed");
    }
  };

  // Initialize Firebase auth listener - SIMPLIFIED
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    const initializeAuth = async () => {
      try {
        const authInstance = await ensureFirebaseAuth();
        if (!authInstance) {
          setIsLoading(false);
          return;
        }

        const { onAuthStateChanged } = await import("firebase/auth");
        unsubscribe = onAuthStateChanged(authInstance, async (firebaseUser) => {
          try {
            if (firebaseUser) {
              setFirebaseUser(firebaseUser);
              try {
                const backendUser = await syncUserWithBackend(firebaseUser);
                if (backendUser) {
                  setUser(backendUser);
                  // Fetch profile in background
                  fetchUserProfile().catch(console.error);
                }
              } catch (syncError) {
                console.error("Backend sync failed:", syncError);
                // Keep Firebase user but show sync error
              }
            } else {
              setFirebaseUser(null);
              setUser(null);
              setUserProfile(null);
              localStorage.removeItem("firebaseToken");
              if (axiosInstance.defaults.headers.common) {
                delete axiosInstance.defaults.headers.common["Authorization"];
              }
            }
          } catch (error) {
            console.error("Auth state change error:", error);
          } finally {
            setIsLoading(false);
          }
        });
      } catch (error) {
        console.error("Firebase Auth initialization failed:", error);
        setIsLoading(false);
      }
    };

    initializeAuth();
    return () => {
      if (unsubscribe) unsubscribe();
    };
  }, [ensureFirebaseAuth, fetchUserProfile]);

  // Initialize authentication state from localStorage
  useEffect(() => {
    const devBypassEnabled = localStorage.getItem("devBypassEnabled") === "true";
    if (devBypassEnabled && isDevBypassEnabled) {
      const devUser = localStorage.getItem("devUser");
      if (devUser) {
        try {
          const parsedUser = JSON.parse(devUser);
          setUser(parsedUser);
          setUserProfile(parsedUser);
          setIsDevelopmentBypass(true);
          setIsLoading(false);
          return;
        } catch (e) {
          console.error("Failed to parse dev user:", e);
        }
      }
    }

    // Set up stored Firebase token
    const storedToken = localStorage.getItem("firebaseToken");
    if (storedToken) {
      axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${storedToken}`;
    }
  }, [isDevBypassEnabled]);

  // Token refresh - SIMPLIFIED, no aggressive intervals
  useEffect(() => {
    if (!firebaseUser) return;

    const refreshToken = async () => {
      try {
        const idToken = await firebaseUser.getIdToken(true);
        axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${idToken}`;
        localStorage.setItem("firebaseToken", idToken);
      } catch (error) {
        console.error("Token refresh failed:", error);
      }
    };

    // Refresh token every 45 minutes (less aggressive)
    const interval = setInterval(refreshToken, 45 * 60 * 1000);
    return () => clearInterval(interval);
  }, [firebaseUser]);

  const isAuthenticated = !!(user || isDevelopmentBypass);

  return (
    <FirebaseAuthContext.Provider
      value={{
        user,
        firebaseUser,
        userProfile,
        isLoading,
        isAuthenticated,
        isDevelopmentBypass,
        loginWithEmail,
        loginWithGoogle,
        registerWithEmail,
        logout,
        resetPassword,
        fetchUserProfile,
        refreshUserProfile,
        updateUserProfile,
        enableDevelopmentBypass,
        disableDevelopmentBypass,
        clearAllAuthData,
      }}
    >
      {children}
    </FirebaseAuthContext.Provider>
  );
}

export function useFirebaseAuth() {
  const context = useContext(FirebaseAuthContext);
  if (context === undefined) {
    throw new Error("useFirebaseAuth must be used within a FirebaseAuthProvider");
  }
  return context;
}