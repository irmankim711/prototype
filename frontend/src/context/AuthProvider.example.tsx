/**
 * ========================================
 * PRODUCTION-GRADE FIREBASE AUTH PROVIDER
 * ========================================
 *
 * This is a reference implementation showing best practices for Firebase Auth
 * in modern React applications. It addresses common authentication bugs:
 *
 * ✅ FIXES IMPLEMENTED:
 * 1. Token persists after logout → Clears ALL Firebase keys from localStorage
 * 2. User appears unauthenticated after login → Immediately updates state
 * 3. Handles page reload, multi-tab, network delays
 * 4. Comprehensive error handling and fallbacks
 *
 * Framework: React + Firebase v9+ Modular SDK
 * State Management: React Context API
 * Persistence: localStorage (with proper cleanup)
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import type { ReactNode } from 'react';
import type { User as FirebaseUser, Auth } from 'firebase/auth';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface User {
  id: string | number;
  email: string;
  displayName?: string | null;
  photoURL?: string | null;
  emailVerified: boolean;
  uid: string;
  customClaims?: Record<string, any>;
}

interface AuthContextValue {
  // State
  user: User | null;
  firebaseUser: FirebaseUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;

  // Methods
  loginWithEmail: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  registerWithEmail: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  clearError: () => void;
}

// ============================================================================
// CONTEXT
// ============================================================================

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ============================================================================
// PROVIDER COMPONENT
// ============================================================================

export function AuthProvider({ children }: { children: ReactNode }) {
  // State
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Refs for Firebase instances (lazy loaded to prevent HMR issues)
  const authRef = useRef<Auth | null>(null);
  const initPromiseRef = useRef<Promise<void> | null>(null);

  // ============================================================================
  // UTILITY: Clear All Auth Data (FIX #1)
  // ============================================================================

  const clearAllAuthData = useCallback(() => {
    console.log('🧹 Clearing all authentication data...');

    // Clear React state
    setUser(null);
    setFirebaseUser(null);
    setError(null);

    // Clear custom tokens
    const customKeys = ['firebaseToken', 'accessToken', 'refreshToken', 'userData'];
    customKeys.forEach(key => localStorage.removeItem(key));

    // CRITICAL: Clear Firebase SDK's internal auth state
    // Firebase stores auth with pattern: firebase:authUser:[apiKey]:[authDomain]
    const firebaseKeys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('firebase:')) {
        firebaseKeys.push(key);
      }
    }

    firebaseKeys.forEach(key => {
      localStorage.removeItem(key);
      console.log(`  ✓ Removed ${key}`);
    });

    console.log('✅ All auth data cleared successfully');
  }, []);

  // ============================================================================
  // UTILITY: Initialize Firebase Auth (Lazy Load)
  // ============================================================================

  const ensureAuth = useCallback(async (): Promise<Auth> => {
    if (authRef.current) {
      return authRef.current;
    }

    if (initPromiseRef.current) {
      await initPromiseRef.current;
      if (!authRef.current) throw new Error('Auth initialization failed');
      return authRef.current;
    }

    initPromiseRef.current = (async () => {
      try {
        const { auth } = await import('../config/firebase');
        authRef.current = auth;
        console.log('✅ Firebase Auth initialized');
      } catch (err) {
        console.error('❌ Firebase Auth initialization failed:', err);
        throw new Error('Authentication service unavailable');
      } finally {
        initPromiseRef.current = null;
      }
    })();

    await initPromiseRef.current;
    if (!authRef.current) throw new Error('Auth initialization failed');
    return authRef.current;
  }, []);

  // ============================================================================
  // UTILITY: Convert Firebase User to App User
  // ============================================================================

  const convertFirebaseUser = useCallback((firebaseUser: FirebaseUser): User => {
    return {
      id: firebaseUser.uid,
      email: firebaseUser.email || '',
      displayName: firebaseUser.displayName,
      photoURL: firebaseUser.photoURL,
      emailVerified: firebaseUser.emailVerified,
      uid: firebaseUser.uid,
    };
  }, []);

  // ============================================================================
  // AUTH METHOD: Login with Email (FIX #2)
  // ============================================================================

  const loginWithEmail = useCallback(async (email: string, password: string) => {
    try {
      setIsLoading(true);
      setError(null);
      console.log(`🔐 Logging in with email: ${email}`);

      const auth = await ensureAuth();
      const { signInWithEmailAndPassword } = await import('firebase/auth');

      // Authenticate with Firebase
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const authenticatedUser = userCredential.user;

      // CRITICAL FIX #2: Immediately update state (don't wait for onAuthStateChanged)
      setFirebaseUser(authenticatedUser);
      setUser(convertFirebaseUser(authenticatedUser));

      // Store token for API calls
      const idToken = await authenticatedUser.getIdToken(true);
      localStorage.setItem('firebaseToken', idToken);

      console.log(`✅ Login successful for ${email}`);
    } catch (err: any) {
      console.error('❌ Login failed:', err);

      // User-friendly error messages
      const errorMap: Record<string, string> = {
        'auth/user-not-found': 'No account found with this email',
        'auth/wrong-password': 'Incorrect password',
        'auth/invalid-email': 'Invalid email address',
        'auth/too-many-requests': 'Too many failed attempts. Please try again later',
        'auth/network-request-failed': 'Network error. Check your connection',
      };

      setError(errorMap[err.code] || 'Login failed. Please try again');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [ensureAuth, convertFirebaseUser]);

  // ============================================================================
  // AUTH METHOD: Login with Google (FIX #2)
  // ============================================================================

  const loginWithGoogle = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      console.log('🔐 Logging in with Google...');

      const auth = await ensureAuth();
      const { signInWithPopup } = await import('firebase/auth');
      const { googleProvider } = await import('../config/firebase');

      // Authenticate with Google
      const result = await signInWithPopup(auth, googleProvider);
      const authenticatedUser = result.user;

      // CRITICAL FIX #2: Immediately update state
      setFirebaseUser(authenticatedUser);
      setUser(convertFirebaseUser(authenticatedUser));

      // Store token
      const idToken = await authenticatedUser.getIdToken(true);
      localStorage.setItem('firebaseToken', idToken);

      console.log(`✅ Google login successful for ${authenticatedUser.email}`);
    } catch (err: any) {
      console.error('❌ Google login failed:', err);

      const errorMap: Record<string, string> = {
        'auth/popup-closed-by-user': 'Login cancelled',
        'auth/popup-blocked': 'Popup blocked. Please allow popups',
        'auth/cancelled-popup-request': 'Login cancelled',
      };

      setError(errorMap[err.code] || 'Google login failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [ensureAuth, convertFirebaseUser]);

  // ============================================================================
  // AUTH METHOD: Register with Email
  // ============================================================================

  const registerWithEmail = useCallback(async (
    email: string,
    password: string,
    displayName?: string
  ) => {
    try {
      setIsLoading(true);
      setError(null);
      console.log(`📝 Registering new user: ${email}`);

      const auth = await ensureAuth();
      const { createUserWithEmailAndPassword, updateProfile } = await import('firebase/auth');

      // Create user
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const newUser = userCredential.user;

      // Update profile if displayName provided
      if (displayName) {
        await updateProfile(newUser, { displayName });
      }

      // Update state
      setFirebaseUser(newUser);
      setUser(convertFirebaseUser(newUser));

      // Store token
      const idToken = await newUser.getIdToken(true);
      localStorage.setItem('firebaseToken', idToken);

      console.log(`✅ Registration successful for ${email}`);
    } catch (err: any) {
      console.error('❌ Registration failed:', err);

      const errorMap: Record<string, string> = {
        'auth/email-already-in-use': 'Email already registered',
        'auth/weak-password': 'Password too weak (min 6 characters)',
        'auth/invalid-email': 'Invalid email address',
      };

      setError(errorMap[err.code] || 'Registration failed');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [ensureAuth, convertFirebaseUser]);

  // ============================================================================
  // AUTH METHOD: Logout (FIX #1)
  // ============================================================================

  const logout = useCallback(async () => {
    try {
      console.log('👋 Logging out...');

      if (authRef.current) {
        const { signOut } = await import('firebase/auth');
        await signOut(authRef.current);
      }

      // CRITICAL FIX #1: Clear ALL auth data including Firebase keys
      clearAllAuthData();

      console.log('✅ Logout successful');
    } catch (err: any) {
      console.error('❌ Logout error:', err);
      // Clear data even if signOut fails
      clearAllAuthData();
    }
  }, [clearAllAuthData]);

  // ============================================================================
  // AUTH METHOD: Reset Password
  // ============================================================================

  const resetPassword = useCallback(async (email: string) => {
    try {
      setError(null);
      console.log(`📧 Sending password reset email to: ${email}`);

      const auth = await ensureAuth();
      const { sendPasswordResetEmail } = await import('firebase/auth');

      await sendPasswordResetEmail(auth, email);

      console.log('✅ Password reset email sent');
    } catch (err: any) {
      console.error('❌ Password reset failed:', err);

      const errorMap: Record<string, string> = {
        'auth/user-not-found': 'No account found with this email',
        'auth/invalid-email': 'Invalid email address',
      };

      setError(errorMap[err.code] || 'Failed to send reset email');
      throw err;
    }
  }, [ensureAuth]);

  // ============================================================================
  // UTILITY: Clear Error
  // ============================================================================

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // ============================================================================
  // EFFECT: Listen to Auth State Changes
  // ============================================================================

  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    const setupAuthListener = async () => {
      try {
        const auth = await ensureAuth();
        const { onAuthStateChanged } = await import('firebase/auth');

        unsubscribe = onAuthStateChanged(
          auth,
          async (firebaseUser) => {
            console.log('🔄 Auth state changed:', firebaseUser ? firebaseUser.email : 'logged out');

            if (firebaseUser) {
              setFirebaseUser(firebaseUser);
              setUser(convertFirebaseUser(firebaseUser));

              // Refresh token and store
              try {
                const idToken = await firebaseUser.getIdToken();
                localStorage.setItem('firebaseToken', idToken);
              } catch (tokenErr) {
                console.warn('⚠️ Token refresh failed:', tokenErr);
              }
            } else {
              setFirebaseUser(null);
              setUser(null);
              localStorage.removeItem('firebaseToken');
            }

            setIsLoading(false);
          },
          (error) => {
            console.error('❌ Auth state change error:', error);
            setError('Authentication error occurred');
            setIsLoading(false);
          }
        );
      } catch (err) {
        console.error('❌ Failed to setup auth listener:', err);
        setIsLoading(false);
      }
    };

    setupAuthListener();

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, [ensureAuth, convertFirebaseUser]);

  // ============================================================================
  // EFFECT: Token Refresh (every 50 minutes)
  // ============================================================================

  useEffect(() => {
    if (!firebaseUser) return;

    const refreshToken = async () => {
      try {
        console.log('🔄 Refreshing token...');
        const idToken = await firebaseUser.getIdToken(true); // Force refresh
        localStorage.setItem('firebaseToken', idToken);
        console.log('✅ Token refreshed');
      } catch (err) {
        console.error('❌ Token refresh failed:', err);
      }
    };

    // Refresh every 50 minutes (tokens expire in 60 minutes)
    const interval = setInterval(refreshToken, 50 * 60 * 1000);

    // Refresh immediately
    refreshToken();

    return () => clearInterval(interval);
  }, [firebaseUser]);

  // ============================================================================
  // CONTEXT VALUE
  // ============================================================================

  const value: AuthContextValue = {
    user,
    firebaseUser,
    isLoading,
    isAuthenticated: !!user,
    error,
    loginWithEmail,
    loginWithGoogle,
    registerWithEmail,
    logout,
    resetPassword,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ============================================================================
// HOOK
// ============================================================================

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

// ============================================================================
// USAGE EXAMPLE
// ============================================================================

/*
// 1. Wrap your app with AuthProvider
import { AuthProvider } from './context/AuthProvider';

function App() {
  return (
    <AuthProvider>
      <YourApp />
    </AuthProvider>
  );
}

// 2. Use the hook in components
import { useAuth } from './context/AuthProvider';

function LoginPage() {
  const { loginWithEmail, loginWithGoogle, isLoading, error } = useAuth();

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    try {
      await loginWithEmail(email, password);
      // UI will update automatically
    } catch (err) {
      // Error is already set in context
    }
  };

  return (
    <div>
      {error && <div className="error">{error}</div>}
      <button onClick={handleEmailLogin} disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
      <button onClick={loginWithGoogle}>Login with Google</button>
    </div>
  );
}

function ProtectedComponent() {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div>
      <h1>Welcome, {user.displayName || user.email}!</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
*/
