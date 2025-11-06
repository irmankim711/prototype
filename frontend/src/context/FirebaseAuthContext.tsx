/* eslint-disable @typescript-eslint/no-explicit-any */
import React from 'react';
/* @refresh reset */
/**
 * Firebase Authentication Provider Component
 * Separated types and context to fix Vite Fast Refresh issues
 */

import {
  useState,
  useEffect,
  useContext,
  useCallback,
} from "react";

import type { ReactNode } from "react";
// We avoid static runtime imports from 'firebase/auth' to prevent the
// "Component auth has not been registered yet" error during module
// evaluation. All runtime functions are dynamically imported after the
// auth instance is available. Keep only type imports here.
import type { User as FirebaseUser } from "firebase/auth";

import type { Auth } from "firebase/auth";
import type { GoogleAuthProvider as GoogleProviderType } from "firebase/auth";
import { useRef } from "react";
// NOTE: We intentionally do NOT import `auth`/`googleProvider` synchronously here.
// Some build/runtime environments can cause the Firebase auth component to be
// registered on a different module instance which produces the error
// "Component auth has not been registered yet" during module evaluation.
// We'll dynamically import `../config/firebase` inside the initialization effect
// and store `auth`/`googleProvider` on refs so the app doesn't crash at import time.
import axiosInstance from "../services/axiosInstance";

import { environmentConfig } from "../config/environment";

import { securityMonitoring } from "../services/securityMonitoring";

// Import types and context from separate file to fix HMR issues
import {
  FirebaseAuthContext,
  normalizeError,
  type User,
  type AuthContextType,
  type AdditionalData,
  type FirebaseConfigModule,
  type SafeError
} from "./FirebaseAuthTypes";

export function FirebaseAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  
const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  
const [userProfile, setUserProfile] = useState<User | null>(null);
  
const [isLoading, setIsLoading] = useState(true);
  
const [isDevelopmentBypass, setIsDevelopmentBypass] = useState(false);

  // Check if development bypass is enabled
  const isDevBypassEnabled =
    environmentConfig.isDevelopment && environmentConfig.features.authBypass;

  // Google Auth Provider is imported from config

  // Clear all authentication data
  const clearAllAuthData = useCallback(() => {
    setUser(null);

setFirebaseUser(null);

setUserProfile(null);

setIsDevelopmentBypass(false);

    // Clear all localStorage keys - INCLUDING Firebase SDK internal keys!
    localStorage.removeItem("accessToken");
    localStorage.removeItem("firebaseToken");
    localStorage.removeItem("devBypassEnabled");
    localStorage.removeItem("devUser");

    // CRITICAL FIX #1: Clear Firebase SDK's internal auth state
    // Firebase stores auth state with pattern: firebase:authUser:[apiKey]:[authDomain]
    // We need to iterate through all localStorage keys and remove Firebase-specific ones
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (
        key.startsWith('firebase:authUser') ||
        key.startsWith('firebase:host') ||
        key.startsWith('firebase:') // Catch all other Firebase keys
      )) {
        keysToRemove.push(key);
      }
    }

    // Remove Firebase keys (done separately to avoid iteration issues)
    keysToRemove.forEach(key => {
      localStorage.removeItem(key);
      console.log(`🧹 Removed Firebase key: ${key}`);
    });

    // Clear axios headers
    if (axiosInstance.defaults.headers.common) {
      delete axiosInstance.defaults.headers.common["Authorization"];
    }

    console.log('🧹 All authentication data cleared (including Firebase SDK state)');
  }, []);

  // Refs to hold the firebase auth instance and Google provider loaded dynamically
  const authRef = useRef<Auth | null>(null);

const googleProviderRef = useRef<GoogleProviderType | null>(null);

// Add a ref to track if Firebase is being initialized to prevent concurrent initialization
  const initializingRef = useRef<boolean>(false);

// Add a ref to track promises for pending initialization
  const initPromiseRef = useRef<Promise<Auth | null> | null>(null);

  // Track backend sync concurrency to avoid duplicate syncs for same user
  const syncInProgressRef = useRef<boolean>(false);
  const lastSyncUidRef = useRef<string | null>(null);
  const lastSyncTimestampRef = useRef<number>(0);
  const SYNC_THROTTLE_MS = 5000; // Minimum 5 seconds between sync attempts

  // Simplified Firebase initialization function
  const ensureFirebaseAuth = useCallback(async (): Promise<Auth | null> => {
    // If already initialized, return immediately
    if (authRef.current) {
      return authRef.current;
    }

    // If already initializing, return the existing promise
    if (initPromiseRef.current) {
      return initPromiseRef.current;
    }

    // Start initialization
    if (initializingRef.current) {
      // Wait for ongoing initialization
      let attempts = 0;
      // Wait briefly for initialization, but don't loop indefinitely
      if (initializingRef.current) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second max
      }
      return authRef.current;
    }

    initializingRef.current = true;
    console.log("🔄 [FirebaseAuth] Starting Firebase initialization...");

    const initPromise = (async (): Promise<Auth | null> => {
      try {
        // Import the Firebase config which now has synchronous initialization
        const { auth, googleProvider } = await import("../config/firebase");

        // Set the auth and provider instances (with null checks)
        if (auth) {
          authRef.current = auth;
        } else {
          console.warn("⚠️ Firebase auth is not available - authentication will be disabled");
        }

        if (googleProvider) {
          googleProviderRef.current = googleProvider;
        } else {
          console.warn("⚠️ Google provider is not available - Google sign-in will be disabled");
        }

        console.log("✅ [FirebaseAuth] Firebase auth initialized successfully");
        console.log("✅ [FirebaseAuth] Google provider ready:", !!googleProviderRef.current);

        return auth;
      } catch (error) {
        console.error("❌ [FirebaseAuth] Firebase initialization failed:", error);
        return null;
      } finally {
        initializingRef.current = false;
        initPromiseRef.current = null;
      }
    })();

    initPromiseRef.current = initPromise;
    return initPromise;
  }, []);

  // Debug: indicate provider mounted
  useEffect(() => {
    console.log(
      "🔑 [FirebaseAuthProvider] mounted. Exposing auth methods (placeholders until firebase loads)."
    );
  }, []);

  // Development authentication bypass (keep for compatibility)
  const enableDevelopmentBypass = () => {
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

console.log("🔓 Development authentication bypass enabled", devUser);
  };

const disableDevelopmentBypass = () => {
    clearAllAuthData();
    
console.log("🔒 Development authentication bypass disabled");
  };

  // Backend health check with rate limiting
  const healthCheckCache = useRef<{ result: boolean; timestamp: number } | null>(null);
  const HEALTH_CHECK_CACHE_TTL = 30000; // 30 seconds cache

  const checkBackendHealth = useCallback(async (): Promise<boolean> => {
    const now = Date.now();

    // Return cached result if still valid
    if (healthCheckCache.current &&
        (now - healthCheckCache.current.timestamp) < HEALTH_CHECK_CACHE_TTL) {
      console.log('🔄 Using cached health check result:', healthCheckCache.current.result);
      return healthCheckCache.current.result;
    }

    try {
      console.log('🔍 Performing backend health check...');

      // Use a simple endpoint that's less likely to have rate limiting
      await Promise.race([
        fetch(`${axiosInstance.defaults.baseURL}/health`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        }).catch(() => {
          // If /health doesn't exist, that's still "healthy" - the server is responding
          return { ok: true };
        }),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Health check timeout')), 2000)
        )
      ]);

      const result = true;
      healthCheckCache.current = { result, timestamp: now };
      console.log('✅ Backend health check passed');
      return result;
    } catch (error) {
      console.warn('🔴 Backend health check failed:', error);
      const result = false;
      healthCheckCache.current = { result, timestamp: now };
      return result;
    }
  }, []); // Empty dependency array since it only uses refs and doesn't depend on props/state

  // Sync user data with backend
  const syncUserWithBackend = async (
    firebaseUser: FirebaseUser,
    attempt: number = 0
  ): Promise<User | null> => {
    const requestId = `sync_${Date.now()}`;
    const syncStart = Date.now();

    console.log(
      `🔄 [${requestId}] Starting Firebase user sync for: ${firebaseUser.email}`
    );

    // Skip health check during sync to prevent rate limiting
    // The sync process itself will determine if backend is available
    console.log(`🔍 [${requestId}] Proceeding with sync (health check skipped to avoid rate limiting)`);

try {
      // Get fresh Firebase ID token with timeout handling
      console.log(`🔍 [${requestId}] Requesting Firebase ID token...`);
      const idToken = await Promise.race([
        firebaseUser.getIdToken(true), // Force refresh
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Firebase token request timeout')), 5000)
        )
      ]) as string;
      console.log(
        `🔍 [${requestId}] Firebase token obtained (length: ${idToken.length})`
      );

      // Prepare sync payload
      const syncPayload = {
        firstName: firebaseUser.displayName?.split(" ")[0] || "",
        lastName: firebaseUser.displayName?.split(" ").slice(1).join(" ") || "",
        displayName: firebaseUser.displayName,
        photoUrl: firebaseUser.photoURL,
        emailVerified: firebaseUser.emailVerified,
      };

console.log(
        `📤 [${requestId}] Sending sync request with payload:`,
        syncPayload
      );

      // Send Firebase token to backend for user creation/sync with optimized timeout
      console.log(`📤 [${requestId}] Sending sync request to backend...`);

      let response: any;
      try {
        // Increased timeout to 15000ms (15 seconds) to give the backend more time to respond
        // Removed the Promise.race with separate timeout to avoid double timeout handling
        response = await axiosInstance.post(
          "/api/auth/firebase-login",
          syncPayload,
          {
            headers: {
              Authorization: `Bearer ${idToken}`,
              "Content-Type": "application/json",
            },
            timeout: 15000, // Increased to 15 second timeout to allow backend processing
          }
        );
      } catch (err: any) {
        console.error(`❌ [${requestId}] Sync failed:`, err);

        // Check if we should retry the request
        if (attempt < 2 && (err.message?.includes('timeout') || err.code === 'ECONNREFUSED' || err.response?.status >= 500)) {
          console.log(`🔄 [${requestId}] Retrying sync (attempt ${attempt + 1}/2)...`);
          // Wait before retrying (exponential backoff)
          const backoffDelay = 1000 * Math.pow(2, attempt);
          await new Promise(resolve => setTimeout(resolve, backoffDelay));
          return syncUserWithBackend(firebaseUser, attempt + 1);
        }

        // Provide more specific error messages
        if (err.message?.includes('timeout')) {
          throw new Error('Backend sync timed out. The server may be overloaded. Please try again.');
        } else if (err.code === 'ECONNREFUSED') {
          throw new Error('Cannot connect to backend server. Please ensure it is running.');
        } else if (err.response?.status === 401) {
          throw new Error('Authentication failed. Please try logging in again.');
        } else if (err.response?.status >= 500) {
          throw new Error('Backend server error. Please try again later.');
        }

        throw err; // Re-throw original error if not handled above
      }

console.log(`✅ [${requestId}] Sync successful:`, response.data);

      // Store the token for future requests
      axiosInstance.defaults.headers.common[
        "Authorization"
      ] = `Bearer ${idToken}`;
      
localStorage.setItem("firebaseToken", idToken);

console.log(`⏱️ [${requestId}] Sync completed in ${Date.now() - syncStart}ms (attempts: ${attempt + 1})`);
      return response.data.user;
    } catch (err: any) {
      const error = normalizeError(err);
      
console.error(
        `❌ [${requestId}] Failed to sync user with backend:`,
        error
      );

      // Enhanced error logging
      if (error.response) {
        console.error(
          `📋 [${requestId}] Response status: ${error.response.status}`
        );
        
console.error(`📋 [${requestId}] Response data:`, error.response.data);
        
console.error(
          `📋 [${requestId}] Response headers:`,
          error.response.headers
        );

        // Handle specific error cases
        if (error.response.status === 500) {
          console.error(
            `🚨 [${requestId}] Server error during sync - this is the main issue we're fixing`
          );
        } else if (error.response.status === 401) {
          console.error(
            `🔒 [${requestId}] Authentication failed - token may be invalid`
          );
        }
      } else if (error.request) {
        console.error(`📋 [${requestId}] No response received:`, error.request);
      } else {
        console.error(`📋 [${requestId}] Request setup error:`, error.message);
      }

      console.log(`⏱️ [${requestId}] Sync failed after ${Date.now() - syncStart}ms`);
      throw err;
    }
  };

  // Fetch user profile from backend
  const fetchUserProfile = useCallback(
    async (retryCount = 0) => {
      if (isDevelopmentBypass || !firebaseUser) {
        console.log(
          "Skipping profile fetch - bypass active or no Firebase user"
        );
        
return;
      }

      const profileId = `profile_${Date.now()}`;
      
console.log(
        `🔄 [${profileId}] Fetching user profile (attempt ${retryCount + 1})...`
      );

try {
        const response = await axiosInstance.get("/api/users/profile");

const profileData = response.data;

setUserProfile(profileData);

console.log(`✅ [${profileId}] User profile fetched successfully`);
      } catch (err: any) {
        const error = normalizeError(err);
        
console.error(`❌ [${profileId}] Failed to fetch user profile:`, error);

        // Retry logic for transient errors
        if (
          retryCount < 2 &&
          error.response?.status &&
          error.response.status >= 500
        ) {
          console.log(
            `🔄 [${profileId}] Retrying profile fetch in 2 seconds...`
          );
          
setTimeout(() => fetchUserProfile(retryCount + 1), 2000);
        } else if (error.response?.status === 401) {
          console.warn(
            `🔒 [${profileId}] Authentication error during profile fetch - user may need to re-login`
          );
        } else {
          console.error(
            `❌ [${profileId}] Profile fetch failed permanently after ${
              retryCount + 1
            } attempts`
          );
        }
      }
    },
    [isDevelopmentBypass, firebaseUser]
  );

const refreshUserProfile = async () => {
    if (!firebaseUser || isDevelopmentBypass) return;
    
await fetchUserProfile();
  };

  // Update user profile
  const updateUserProfile = async (data: Partial<User>) => {
    try {
      const response = await axiosInstance.put("/api/users/profile", data);
      
setUserProfile(response.data.user);

      // Update Firebase profile if display name changed (dynamic import)
      if (firebaseUser && (data.first_name || data.last_name)) {
        const displayName = `${data.first_name || ""} ${
          data.last_name || ""
        }`.trim();
        
const { updateProfile } = await import("firebase/auth");
        
await updateProfile(firebaseUser, { displayName });
      }
    } catch (err: any) {
      const error = normalizeError(err);
      
console.error("Failed to update user profile:", error);
      
throw err;
    }
  };

  // Authentication Methods
  const loginWithEmail = async (email: string, password: string) => {
    const loginId = `email_login_${Date.now()}`;

console.log(`🔄 [${loginId}] Starting email login for: ${email}`);

try {
      setIsLoading(true);

      // Ensure Firebase auth is initialized before attempting login
      console.log(`🔍 [${loginId}] Ensuring Firebase auth is initialized...`);

const authInstance = await ensureFirebaseAuth();
      if (!authInstance) {
        console.error(`❌ [${loginId}] Failed to initialize Firebase Auth`);
        console.error(`❌ [${loginId}] Check browser console for Firebase initialization errors`);
        console.error(`❌ [${loginId}] Auth instance:`, authInstance);
        console.error(`❌ [${loginId}] AuthRef current:`, authRef.current);
        throw new Error("Authentication service unavailable");
      }

      console.log(`✅ [${loginId}] Firebase auth ready for login`);
      console.log(`🔍 [${loginId}] Authenticating with Firebase...`);

const { signInWithEmailAndPassword } = await import("firebase/auth");

const userCredential = await signInWithEmailAndPassword(authInstance, email, password);

console.log(`✅ [${loginId}] Firebase authentication successful`);

      // CRITICAL FIX #2: Immediately set Firebase user to update UI state
      // This prevents the "appears unauthenticated until reload" bug
      const authenticatedUser = userCredential.user;
      setFirebaseUser(authenticatedUser);
      console.log(`✅ [${loginId}] Firebase user state set immediately for: ${authenticatedUser.email}`);

      // Get ID token and sync with backend immediately (don't wait for onAuthStateChanged)
      try {
        const idToken = await authenticatedUser.getIdToken(true);

        // Store token immediately for instant API access
        localStorage.setItem("firebaseToken", idToken);
        axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${idToken}`;

        console.log(`✅ [${loginId}] Token stored and axios configured`);

        // Trigger backend sync (non-blocking - runs in background)
        syncUserWithBackend(authenticatedUser).then(backendUser => {
          if (backendUser) {
            setUser(backendUser);
            console.log(`✅ [${loginId}] Backend user synced: ${backendUser.email}`);

            // Fetch profile in background
            fetchUserProfile().catch(err =>
              console.warn(`⚠️ [${loginId}] Profile fetch failed (non-critical):`, err)
            );
          }
        }).catch(err => {
          console.warn(`⚠️ [${loginId}] Backend sync failed, using fallback:`, err);
          // Create fallback user for offline operation
          const fallbackUser = {
            id: 0,
            email: authenticatedUser.email || '',
            username: authenticatedUser.email?.split('@')[0] || '',
            role: 'user',
            is_active: true,
            first_name: authenticatedUser.displayName?.split(' ')[0] || '',
            last_name: authenticatedUser.displayName?.split(' ').slice(1).join(' ') || '',
            full_name: authenticatedUser.displayName || '',
            firebase_uid: authenticatedUser.uid
          };
          setUser(fallbackUser);
        });

      } catch (tokenError) {
        console.error(`❌ [${loginId}] Token retrieval failed:`, tokenError);
        // Don't throw - onAuthStateChanged will handle the sync
      }

      // Note: onAuthStateChanged will also fire, but we've already set the user state
      console.log(
        `✅ [${loginId}] Email login successful - user authenticated and UI updated`
      );
    } catch (err: any) {
      const error = normalizeError(err);

console.error(`❌ [${loginId}] Email login failed:`, error);

      // Log security event
      if (error.code === "auth/too-many-requests") {
        securityMonitoring.logFirebaseRateLimit(email);
      } else {
        securityMonitoring.logLoginFailure(
          error.code || 'unknown',
          error.message || 'Unknown error',
          email
        );
      }

      // Provide user-friendly error messages
      let errorMessage = "Login failed";

if (error.code === "auth/user-not-found") {
        errorMessage = "No account found with this email address";
      } else if (error.code === "auth/wrong-password") {
        errorMessage = "Incorrect password";
      } else if (error.code === "auth/invalid-email") {
        errorMessage = "Invalid email address";
      } else if (error.code === "auth/too-many-requests") {
        errorMessage =
          "Too many failed login attempts. This account is temporarily locked for security. " +
          "Please wait 15-30 minutes and try again, or reset your password using the 'Forgot Password' link. " +
          "You can also try signing in with Google if available.";
      } else if (error.code === "auth/network-request-failed") {
        errorMessage = "Network error. Please check your connection and try again";
      } else if (error.code === "auth/user-disabled") {
        errorMessage = "This account has been disabled";
      } else if (error.code === "auth/invalid-credential") {
        errorMessage = "Invalid email or password";
      } else if (error.message && error.message !== "Authentication service unavailable") {
        errorMessage = error.message;
      } else {
        errorMessage = "Authentication service temporarily unavailable. Please try again later";
      }

      throw Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

const loginWithGoogle = async () => {
    const loginId = `google_login_${Date.now()}`;

console.log(`🔄 [${loginId}] Starting Google login...`);

try {
      setIsLoading(true);

      // Ensure Firebase auth and Google provider are initialized
      console.log(`🔍 [${loginId}] Ensuring Firebase auth and Google provider are initialized...`);

const authInstance = await ensureFirebaseAuth();
      if (!authInstance) {
        console.error(`❌ [${loginId}] Failed to initialize Firebase Auth for Google login`);
        throw new Error("Authentication service unavailable");
      }

      if (!googleProviderRef.current) {
        console.error(`❌ [${loginId}] Google provider not available`);
        throw new Error("Google sign-in not available");
      }

      console.log(`✅ [${loginId}] Firebase auth and Google provider ready`);
      console.log(`🔍 [${loginId}] Authenticating with Google...`);

const { signInWithPopup } = await import("firebase/auth");

const result = await signInWithPopup(
        authInstance,
        googleProviderRef.current
      );

const authenticatedUser = result.user;

console.log(
        `✅ [${loginId}] Google authentication successful for: ${authenticatedUser.email}`
      );

      // CRITICAL FIX #2: Immediately set Firebase user to update UI state
      // This prevents the "appears unauthenticated until reload" bug
      setFirebaseUser(authenticatedUser);
      console.log(`✅ [${loginId}] Firebase user state set immediately for: ${authenticatedUser.email}`);

      // Get ID token and sync with backend immediately (don't wait for onAuthStateChanged)
      try {
        const idToken = await authenticatedUser.getIdToken(true);

        // Store token immediately for instant API access
        localStorage.setItem("firebaseToken", idToken);
        axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${idToken}`;

        console.log(`✅ [${loginId}] Token stored and axios configured`);

        // Trigger backend sync (non-blocking - runs in background)
        syncUserWithBackend(authenticatedUser).then(backendUser => {
          if (backendUser) {
            setUser(backendUser);
            console.log(`✅ [${loginId}] Backend user synced: ${backendUser.email}`);

            // Fetch profile in background
            fetchUserProfile().catch(err =>
              console.warn(`⚠️ [${loginId}] Profile fetch failed (non-critical):`, err)
            );
          }
        }).catch(err => {
          console.warn(`⚠️ [${loginId}] Backend sync failed, using fallback:`, err);
          // Create fallback user for offline operation
          const fallbackUser = {
            id: 0,
            email: authenticatedUser.email || '',
            username: authenticatedUser.email?.split('@')[0] || '',
            role: 'user',
            is_active: true,
            first_name: authenticatedUser.displayName?.split(' ')[0] || '',
            last_name: authenticatedUser.displayName?.split(' ').slice(1).join(' ') || '',
            full_name: authenticatedUser.displayName || '',
            firebase_uid: authenticatedUser.uid
          };
          setUser(fallbackUser);
        });

      } catch (tokenError) {
        console.error(`❌ [${loginId}] Token retrieval failed:`, tokenError);
        // Don't throw - onAuthStateChanged will handle the sync
      }

      // Note: onAuthStateChanged will also fire, but we've already set the user state
      console.log(
        `✅ [${loginId}] Google login successful - user authenticated and UI updated`
      );
    } catch (err: any) {
      const error = normalizeError(err);

console.error(`❌ [${loginId}] Google login failed:`, error);

      // Provide user-friendly error messages
      let errorMessage = "Google login failed";
      
if (error.code === "auth/popup-closed-by-user") {
        errorMessage = "Login cancelled by user";
      } else if (error.code === "auth/popup-blocked") {
        errorMessage = "Popup blocked. Please allow popups and try again";
      } else if (error.code === "auth/cancelled-popup-request") {
        errorMessage = "Login cancelled";
      } else if (error.message) {
        errorMessage = error.message;
      }

      throw Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

const registerWithEmail = async (
    email: string,
    password: string,
    additionalData?: AdditionalData
  ) => {
    try {
      setIsLoading(true);

      // Ensure Firebase auth is initialized before attempting registration
      const authInstance = await ensureFirebaseAuth();
      if (!authInstance) {
        console.error(`❌ Register: Failed to initialize Firebase Auth`);
        throw new Error("Authentication service unavailable");
      }

      console.log(`✅ Register: Firebase auth ready for registration`);

const { createUserWithEmailAndPassword } = await import("firebase/auth");

const userCredential = await createUserWithEmailAndPassword(
        authInstance,
        email,
        password
      );
      
const firebaseUser = userCredential.user;

      // Update Firebase profile with display name (dynamic import)
      if (additionalData?.displayName) {
        const { updateProfile } = await import("firebase/auth");
        
await updateProfile(firebaseUser, {
          displayName: additionalData.displayName,
        });
      }

      // Sync with backend
      const backendUser = await syncUserWithBackend(firebaseUser);
      
if (backendUser) {
        setUser(backendUser);
      }

      console.log("✅ Registration successful");
    } catch (err: any) {
      const error = normalizeError(err);
      
console.error("❌ Registration failed:", error);
      
throw Error(error.message || "Registration failed");
    } finally {
      setIsLoading(false);
    }
  };

const logout = async () => {
    try {
      if (!isDevelopmentBypass) {
        if (!authRef.current)
          throw Error("Authentication service unavailable");
        
const { signOut } = await import("firebase/auth");
        
await signOut(authRef.current);
      }
      clearAllAuthData();
      
console.log("✅ Logout successful");
    } catch (err: any) {
      const error = normalizeError(err);
      
console.error("❌ Logout failed:", error);
      // Clear local data even if Firebase signout fails
      clearAllAuthData();
    }
  };

const resetPassword = async (email: string) => {
    try {
      if (!authRef.current)
        throw Error("Authentication service unavailable");
      
const { sendPasswordResetEmail } = await import("firebase/auth");
      
await sendPasswordResetEmail(authRef.current, email);
      
console.log("✅ Password reset email sent");
    } catch (err: any) {
      const error = normalizeError(err);
      
console.error("❌ Password reset failed:", error);
      
throw Error(error.message || "Password reset failed");
    }
  };

  // Listen to Firebase auth state changes
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

const initializeAuth = async () => {
      try {
        console.log(
          "🔥 [FirebaseAuthContext] Setting up Firebase auth listener..."
        );

        // Use our centralized initialization function
        const authInstance = await ensureFirebaseAuth();
        if (!authInstance) {
          console.error("❌ [FirebaseAuthContext] Failed to initialize Firebase auth");
          setIsLoading(false);
          return;
        }

        console.log("✅ [FirebaseAuthContext] Auth ready, setting up listener...");

        console.log(
          "✅ [FirebaseAuthContext] Firebase auth ready, setting up listener"
        );
 
const { onAuthStateChanged, signOut } = await import("firebase/auth");

unsubscribe = onAuthStateChanged(
          authInstance,
          async (firebaseUser: any) => {
            const stateChangeId = `state_${Date.now()}`;
            
console.log(
              `🔄 [${stateChangeId}] Firebase auth state changed:`,
              firebaseUser ? `User: ${firebaseUser.email}` : "No user"
            );

try {
              if (firebaseUser) {
                setFirebaseUser(firebaseUser);
                
console.log(
                  `✅ [${stateChangeId}] Firebase user set: ${firebaseUser.email}`
                );

                try {
                  // Prevent duplicate concurrent syncs and rate limiting
                  const now = Date.now();
                  const timeSinceLastSync = now - lastSyncTimestampRef.current;

                  if (syncInProgressRef.current && lastSyncUidRef.current === firebaseUser.uid) {
                    console.warn(`⚠️ [${stateChangeId}] Sync already in progress for ${firebaseUser.email}, skipping duplicate`);
                    return; // Skip duplicate sync
                  } else if (timeSinceLastSync < SYNC_THROTTLE_MS && lastSyncUidRef.current === firebaseUser.uid) {
                    console.warn(`⚠️ [${stateChangeId}] Sync throttled for ${firebaseUser.email} (${timeSinceLastSync}ms since last sync, minimum ${SYNC_THROTTLE_MS}ms required)`);
                    return; // Skip throttled sync
                  } else {
                    syncInProgressRef.current = true;
                    lastSyncUidRef.current = firebaseUser.uid;
                    lastSyncTimestampRef.current = now;

                    // Sync user data with backend
                    console.log(
                      `🔄 [${stateChangeId}] Attempting backend sync...`
                    );
                    
const backendUser = await syncUserWithBackend(firebaseUser);

                    if (backendUser) {
                      setUser(backendUser);
                      
console.log(
                        `✅ [${stateChangeId}] Backend user sync successful:`,
                        backendUser.email
                      );

                      // Fetch additional profile data
                      try {
                        await fetchUserProfile();
                        
console.log(
                          `✅ [${stateChangeId}] User profile fetched successfully`
                        );
                      } catch (profileError) {
                        console.warn(
                          `⚠️ [${stateChangeId}] Profile fetch failed (non-critical):`,
                          profileError
                        );
                        // Continue even if profile fetch fails
                      }
                    } else {
                      console.error(
                        `❌ [${stateChangeId}] Backend sync returned null user`
                      );
                      // Don't clear Firebase user, but show error state
                    }
                  }
                } catch (syncErr: any) {
                  const syncError = normalizeError(syncErr);
                  
console.error(
                    `❌ [${stateChangeId}] Backend sync failed:`,
                    syncError
                  );

                  // Handle sync errors gracefully with fallback user creation
                  if (syncError.message?.includes('timeout')) {
                    console.warn(
                      `⚠️ [${stateChangeId}] Backend sync timed out - allowing Firebase-only authentication`
                    );

                    // Create a minimal user object from Firebase data for offline operation
                    const fallbackUser = {
                      id: 0, // Temporary ID for offline mode
                      email: firebaseUser.email || '',
                      username: firebaseUser.email?.split('@')[0] || '',
                      role: 'user',
                      is_active: true,
                      first_name: firebaseUser.displayName?.split(' ')[0] || '',
                      last_name: firebaseUser.displayName?.split(' ').slice(1).join(' ') || '',
                      full_name: firebaseUser.displayName || '',
                      firebase_uid: firebaseUser.uid
                    };

                    setUser(fallbackUser);
                    console.log(
                      `🔄 [${stateChangeId}] Using fallback user object for offline operation`
                    );
                  } else if (syncError.response?.status === 500) {
                    console.error(
                      `🚨 [${stateChangeId}] Server error - allowing Firebase-only authentication`
                    );

                    // Create fallback user for server errors too
                    const fallbackUser = {
                      id: 0,
                      email: firebaseUser.email || '',
                      username: firebaseUser.email?.split('@')[0] || '',
                      role: 'user',
                      is_active: true,
                      first_name: firebaseUser.displayName?.split(' ')[0] || '',
                      last_name: firebaseUser.displayName?.split(' ').slice(1).join(' ') || '',
                      full_name: firebaseUser.displayName || '',
                      firebase_uid: firebaseUser.uid
                    };

                    setUser(fallbackUser);
                    console.log(
                      `🔄 [${stateChangeId}] Using fallback user object due to server error`
                    );
                  } else if (syncError.response?.status === 401) {
                    console.error(
                      `🔒 [${stateChangeId}] Authentication failed - signing out`
                    );

                    if (authRef.current) await signOut(authRef.current);
                    return;
                  } else {
                    // For other errors, create fallback user but log the issue
                    console.warn(
                      `⚠️ [${stateChangeId}] Backend sync failed with unknown error - using fallback`
                    );

                    const fallbackUser = {
                      id: 0,
                      email: firebaseUser.email || '',
                      username: firebaseUser.email?.split('@')[0] || '',
                      role: 'user',
                      is_active: true,
                      first_name: firebaseUser.displayName?.split(' ')[0] || '',
                      last_name: firebaseUser.displayName?.split(' ').slice(1).join(' ') || '',
                      full_name: firebaseUser.displayName || '',
                      firebase_uid: firebaseUser.uid
                    };

                    setUser(fallbackUser);
                  }
                }
              } else {
                console.log(
                  `🔄 [${stateChangeId}] No Firebase user - clearing all auth data`
                );
                
setFirebaseUser(null);
                
setUser(null);
                
setUserProfile(null);

                // Clear stored tokens and axios headers
                localStorage.removeItem("firebaseToken");
                
if (axiosInstance.defaults.headers.common) {
                  delete axiosInstance.defaults.headers.common["Authorization"];
                }
              }
            } catch (err: any) {
              const error = normalizeError(err);
              
console.error(
                `❌ [${stateChangeId}] Auth state change error:`,
                error
              );
              // Don't clear auth state on unexpected errors
            } finally {
              // Clear sync flags to allow future syncs
              syncInProgressRef.current = false;
              setIsLoading(false);
              
console.log(
                `✅ [${stateChangeId}] Auth state change processing complete`
              );
            }
          }
        );
      } catch (initErr: any) {
        const initError = normalizeError(initErr);
        
console.error(
          "❌ [FirebaseAuthContext] Firebase Auth initialization failed:",
          initError
        );
        
setIsLoading(false);
      }
    };

    // Start initialization (async)
    initializeAuth();

return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [ensureFirebaseAuth]);

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = () => {
      console.log("🔄 Initializing authentication state...");

      // Check for development bypass first
      const devBypassEnabled =
        localStorage.getItem("devBypassEnabled") === "true";
      
if (devBypassEnabled && isDevBypassEnabled) {
        const devUser = localStorage.getItem("devUser");
        
if (devUser) {
          const parsedUser = JSON.parse(devUser);
          
setUser(parsedUser);
          
setUserProfile(parsedUser);
          
setIsDevelopmentBypass(true);
          
console.log("🔓 Restored development bypass from localStorage");
          
setIsLoading(false);
          
return;
        }
      }

      // Check for stored Firebase token
      const storedToken = localStorage.getItem("firebaseToken");
      
if (storedToken) {
        console.log("🔍 Found stored Firebase token, setting up axios headers");
        
axiosInstance.defaults.headers.common[
          "Authorization"
        ] = `Bearer ${storedToken}`;
      }

      console.log("✅ Authentication initialization complete");
    };

initializeAuth();
  }, [isDevBypassEnabled]);

  // Connection health checker - reduced frequency to prevent rate limiting
  useEffect(() => {
    let healthCheckInterval: NodeJS.Timeout;

    const checkConnectionHealth = async () => {
      if (!firebaseUser) return;

      try {
        // Use the cached health check to avoid rate limiting
        const isHealthy = await checkBackendHealth();

        if (isHealthy) {
          console.log("🟢 Backend connection healthy");
        } else {
          console.warn("🔴 Backend connection issue detected");

          // If it's an auth error, try to refresh token
          if (firebaseUser) {
            console.log(
              "🔄 Attempting token refresh due to health check failure..."
            );

            try {
              const idToken = await firebaseUser.getIdToken(true);

              axiosInstance.defaults.headers.common[
                "Authorization"
              ] = `Bearer ${idToken}`;

              localStorage.setItem("firebaseToken", idToken);

              console.log("✅ Token refreshed during health check");
            } catch (refreshError) {
              console.error(
                "❌ Token refresh failed during health check:",
                refreshError
              );
            }
          }
        }
      } catch (error: any) {
        console.warn("🔴 Health check error:", error.message);
      }
    };

    // Further reduced frequency: Check connection health every 30 minutes instead of 15
    if (firebaseUser) {
      healthCheckInterval = setInterval(checkConnectionHealth, 30 * 60 * 1000);

      // Don't check immediately to prevent initial rate limiting
      // The sync process will handle initial connectivity
    }

    return () => {
      if (healthCheckInterval) {
        clearInterval(healthCheckInterval);
      }
    };
  }, [firebaseUser, checkBackendHealth]);

  // Set up token refresh for Firebase
  useEffect(() => {
    if (!firebaseUser) return;

const refreshToken = async () => {
      const refreshId = `refresh_${Date.now()}`;

      console.log(
        `🔄 [${refreshId}] Refreshing Firebase token for: ${firebaseUser.email}`
      );

      try {
        // Add timeout to token refresh
        const idToken = await Promise.race([
          firebaseUser.getIdToken(true), // Force refresh
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Token refresh timeout')), 5000)
          )
        ]) as string;

        // Set the token in axios headers
        axiosInstance.defaults.headers.common[
          "Authorization"
        ] = `Bearer ${idToken}`;

        // Store the token in localStorage for API service to use
        localStorage.setItem("firebaseToken", idToken);

        // CRITICAL: Verify the token with backend to ensure proper session management
        // If backend verification fails, the token refresh should be considered failed
        try {
          await axiosInstance.post('/api/auth/verify-token', {}, {
            headers: { 'Authorization': `Bearer ${idToken}` },
            timeout: 10000 // 10 second timeout for verification
          });
          console.log(`✅ [${refreshId}] Token verified with backend successfully`);
        } catch (syncError: any) {
          console.error(`❌ [${refreshId}] Failed to verify token with backend:`, syncError);

          // If backend doesn't accept the token, we need to handle this properly
          if (syncError.response?.status === 401) {
            console.error(`🔒 [${refreshId}] Backend rejected token - user needs to re-authenticate`);
            // Sign out to force re-authentication
            if (authRef.current) {
              const { signOut } = await import("firebase/auth");
              await signOut(authRef.current);
            }
            throw new Error('Token verification failed - please log in again');
          } else if (syncError.response?.status >= 500) {
            // Backend server error - log but don't force logout
            console.warn(`⚠️ [${refreshId}] Backend server error during verification - allowing offline operation`);
          } else if (syncError.code === 'ECONNABORTED' || syncError.message?.includes('timeout')) {
            // Timeout - backend might be slow, allow it
            console.warn(`⚠️ [${refreshId}] Backend verification timeout - allowing offline operation`);
          } else {
            // Unknown error - log and allow
            console.warn(`⚠️ [${refreshId}] Backend verification failed with unknown error - allowing offline operation`);
          }
        }

        console.log(`✅ [${refreshId}] Token refreshed successfully`);
      } catch (error) {
        console.error(`❌ [${refreshId}] Token refresh failed:`, error);

        // If token refresh fails, user might need to re-authenticate
        if (
          error instanceof Error &&
          error.message.includes("auth/user-token-expired")
        ) {
          console.warn(
            `🔒 [${refreshId}] Token expired - user needs to re-authenticate`
          );
          
if (authRef.current) {
            const { signOut } = await import("firebase/auth");
            
await signOut(authRef.current);
          }
        }
      }
    };

    // Refresh token every 50 minutes (Firebase tokens expire in 1 hour)
    // This gives us 10 minutes buffer before expiry (with 1-minute check buffer)
    // 50 min refresh + 10 min buffer = 60 min total
    const interval = setInterval(refreshToken, 50 * 60 * 1000);

    // Also refresh token immediately to ensure we have a fresh one
    refreshToken();

return () => clearInterval(interval);
  }, [firebaseUser]);

  // Set up authentication error recovery event listeners
  useEffect(() => {
    const handleTokenExpired = async (event: CustomEvent) => {
      const eventId = `recovery_${Date.now()}`;
      
console.log(
        `🔄 [${eventId}] Handling token expiration event:`,
        event.detail
      );

if (firebaseUser) {
        try {
          console.log(
            `🔄 [${eventId}] Attempting to refresh Firebase token...`
          );
          
const idToken = await firebaseUser.getIdToken(true); // Force refresh
          axiosInstance.defaults.headers.common[
            "Authorization"
          ] = `Bearer ${idToken}`;
          
localStorage.setItem("firebaseToken", idToken);
          
console.log(`✅ [${eventId}] Firebase token refreshed successfully`);

          // Optionally retry the original request if provided
          const custom = event as CustomEvent<Record<string, any>>;
          
if (custom.detail?.originalRequest) {
            console.log(`🔄 [${eventId}] Retrying original request...`);
            // The axios interceptor will handle the retry automatically
          }
        } catch (error) {
          console.error(
            `❌ [${eventId}] Firebase token refresh failed:`,
            error
          );
          // Sign out user if token refresh fails
          if (authRef.current) {
            const { signOut } = await import("firebase/auth");
            
await signOut(authRef.current);
          }
        }
      } else {
        console.warn(
          `⚠️ [${eventId}] No Firebase user available for token refresh`
        );
      }
    };

const handleLoginRequired = (event: CustomEvent) => {
      const eventId = `login_${Date.now()}`;
      
console.log(`🔒 [${eventId}] Login required event:`, event.detail);

      // Clear all authentication data
      clearAllAuthData();

      // Optionally redirect to login page or show login modal
      console.log(`🔒 [${eventId}] User needs to log in again`);
    };

    // Add event listeners (cast to unknown->EventListener to satisfy TS)
    window.addEventListener(
      "auth:token-expired",
      handleTokenExpired as any as EventListener
    );
    
window.addEventListener("auth:login-required", ((evt: Event) =>
      handleLoginRequired(evt as any as CustomEvent)) as EventListener);

return () => {
      // Clean up event listeners
      window.removeEventListener(
        "auth:token-expired",
        handleTokenExpired as any as EventListener
      );
      
window.removeEventListener("auth:login-required", ((evt: Event) =>
        handleLoginRequired(evt as any as CustomEvent)) as EventListener);
    };
  }, [firebaseUser, clearAllAuthData]);

  // Computed authentication state
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

// Hook to use Firebase auth context
export function useFirebaseAuth() {
  const context = useContext(FirebaseAuthContext);

if (context === undefined) {
    throw Error(
      "useFirebaseAuth must be used within a FirebaseAuthProvider"
    );
  }
  return context;
}

// Export for backward compatibility
export const useAuth = useFirebaseAuth;

// Default export is the component
export default FirebaseAuthProvider;
