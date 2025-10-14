/**
 * Firebase Authentication Types and Context Definition
 * Separated from component to fix Vite Fast Refresh issues
 */

import { createContext } from "react";
import type { User as FirebaseUser } from "firebase/auth";
import type { Auth } from "firebase/auth";
import type { GoogleAuthProvider as GoogleProviderType } from "firebase/auth";

// Helper types to avoid using `any` in this file
export type AdditionalData = { displayName?: string; [key: string]: any };

// Shape of the dynamically imported firebase config module
export interface FirebaseConfigModule {
  auth?: Auth;
  googleProvider?: GoogleProviderType;
  ensureAuth?: () => Promise<Auth | null>;
}

export type SafeError = {
  message?: string;
  code?: string;
  response?: { status?: number; data?: any, headers?: any };
  request?: any;
};

export function normalizeError(err: any): SafeError {
  if (!err || typeof err !== "object") return { message: String(err) };
  return (err as SafeError) || { message: "any error" };
}

export interface User {
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

export interface AuthContextType {
  user: User | null;
  firebaseUser: FirebaseUser | null;
  userProfile: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isDevelopmentBypass: boolean;

  // Firebase Auth Methods
  loginWithEmail: (email: string, password: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  registerWithEmail: (
    email: string,
    password: string,
    additionalData?: AdditionalData
  ) => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;

  // User Profile Methods
  fetchUserProfile: () => Promise<void>;
  refreshUserProfile: () => Promise<void>;
  updateUserProfile: (data: Partial<User>) => Promise<void>;

  // Development Bypass (keep for compatibility)
  enableDevelopmentBypass: () => void;
  disableDevelopmentBypass: () => void;
  clearAllAuthData: () => void;
}

// Provide a safe default context so calling code won't get `undefined` functions
// if the provider isn't mounted yet. Each method throws a clear error directing
// developers to mount the provider.
const _missingProviderError = () =>
  new Error(
    "FirebaseAuthProvider not found. Make sure your app is wrapped with <FirebaseAuthProvider>."
  );

const defaultAuthContext: AuthContextType = {
  user: null,
  firebaseUser: null,
  userProfile: null,
  isLoading: false,
  isAuthenticated: false,
  isDevelopmentBypass: false,
  loginWithEmail: async () => {
    throw _missingProviderError();
  },
  loginWithGoogle: async () => {
    throw _missingProviderError();
  },
  registerWithEmail: async () => {
    throw _missingProviderError();
  },
  logout: async () => {
    throw _missingProviderError();
  },
  resetPassword: async () => {
    throw _missingProviderError();
  },
  fetchUserProfile: async () => {},
  refreshUserProfile: async () => {},
  updateUserProfile: async () => {
    throw _missingProviderError();
  },
  enableDevelopmentBypass: () => {},
  disableDevelopmentBypass: () => {},
  clearAllAuthData: () => {},
};

// Export the context - this won't cause HMR issues since it's in a separate file
export const FirebaseAuthContext = createContext<AuthContextType>(defaultAuthContext);