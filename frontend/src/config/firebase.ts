/**
 * Firebase Configuration
 * Initialize Firebase app with authentication
 */

import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator, GoogleAuthProvider } from 'firebase/auth';

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

export default app;