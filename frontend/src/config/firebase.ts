/**
 * Firebase Configuration
 * Initialize Firebase app with authentication
 *
 * IMPORTANT: This configuration uses LOCAL persistence (default) which stores
 * auth state in localStorage. While this is convenient for users, it requires
 * proper cleanup on logout to prevent security issues.
 */

import { initializeApp } from 'firebase/app';
import {
  getAuth,
  connectAuthEmulator,
  GoogleAuthProvider,
  setPersistence,
  browserLocalPersistence
} from 'firebase/auth';
import { initializeFirebaseAppCheck } from './firebaseAppCheck';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "",
  projectId: "report-automation-57f6e",
  storageBucket: "report-automation-57f6e.firebasestorage.app",
  messagingSenderId: "87279819935",
  appId: "1:87279819935:web:9f78b1c4c2efe16ad4d6aa",
  measurementId: "G-R2HGN102D3"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

/**
 * CRITICAL: Set persistence mode explicitly
 *
 * Options:
 * - browserLocalPersistence: Persists auth state in localStorage (survives page reload & browser close)
 * - browserSessionPersistence: Persists in sessionStorage only (cleared when tab closes)
 * - inMemoryPersistence: No persistence (cleared on page reload)
 *
 * We use LOCAL persistence for better UX, but ensure proper cleanup in clearAllAuthData()
 */
setPersistence(auth, browserLocalPersistence)
  .then(() => {
    console.log('✅ Firebase Auth persistence set to LOCAL (localStorage)');
    console.log('⚠️ Auth state will persist across sessions - ensure proper logout cleanup');
  })
  .catch((error) => {
    console.error('❌ Failed to set Firebase Auth persistence:', error);
  });

// Configure Google Auth Provider
export const googleProvider = new GoogleAuthProvider();
// Add additional scopes
googleProvider.addScope('email');
googleProvider.addScope('profile');
// Configure custom parameters
googleProvider.setCustomParameters({
  prompt: 'select_account', // Always show account selection
});

// Connect to Firebase Auth emulator in development
if (import.meta.env.MODE === 'development' && import.meta.env.VITE_FIREBASE_USE_EMULATOR === 'true') {
  connectAuthEmulator(auth, 'http://localhost:9099');
}

// Initialize App Check for production security
// This helps prevent abuse and unauthorized access to your Firebase resources
initializeFirebaseAppCheck();

export default app;