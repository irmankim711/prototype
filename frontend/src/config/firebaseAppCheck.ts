/**
 * Firebase App Check Configuration
 * Protects your app from abuse by preventing unauthorized clients from accessing your backend
 *
 * Setup Instructions:
 * 1. Enable App Check in Firebase Console: https://console.firebase.google.com/project/report-automation-57f6e/appcheck
 * 2. Register your app for reCAPTCHA v3
 * 3. Get your reCAPTCHA site key from Google reCAPTCHA Console: https://www.google.com/recaptcha/admin
 * 4. Add VITE_RECAPTCHA_SITE_KEY to your .env file
 * 5. Uncomment the initialization code below
 */

import { getApp } from 'firebase/app';
import { initializeAppCheck, ReCaptchaV3Provider, CustomProvider } from 'firebase/app-check';

let appCheck: ReturnType<typeof initializeAppCheck> | null = null;

/**
 * Initialize Firebase App Check
 * This should be called after Firebase app initialization
 */
export function initializeFirebaseAppCheck(): void {
  // Skip in development if not explicitly enabled
  if (import.meta.env.MODE === 'development' && !import.meta.env.VITE_APP_CHECK_ENABLED) {
    console.log('[AppCheck] Skipped in development mode');

    // Use debug token provider in development for testing
    if (import.meta.env.VITE_APP_CHECK_DEBUG_TOKEN) {
      try {
        const app = getApp();

        // Enable debug mode
        // @ts-ignore - self is available in browser
        self.FIREBASE_APPCHECK_DEBUG_TOKEN = import.meta.env.VITE_APP_CHECK_DEBUG_TOKEN;

        appCheck = initializeAppCheck(app, {
          provider: new CustomProvider({
            getToken: () => {
              return Promise.resolve({
                token: import.meta.env.VITE_APP_CHECK_DEBUG_TOKEN,
                expireTimeMillis: Date.now() + 60 * 60 * 1000, // 1 hour
              });
            },
          }),
          isTokenAutoRefreshEnabled: true,
        });

        console.log('[AppCheck] Debug mode enabled');
      } catch (error) {
        console.warn('[AppCheck] Debug initialization failed:', error);
      }
    }

    return;
  }

  // Production setup with reCAPTCHA v3
  const recaptchaSiteKey = import.meta.env.VITE_RECAPTCHA_SITE_KEY;

  if (!recaptchaSiteKey) {
    console.warn(
      '[AppCheck] reCAPTCHA site key not configured. ' +
      'App Check will not be enabled. ' +
      'Add VITE_RECAPTCHA_SITE_KEY to your .env file.'
    );
    return;
  }

  try {
    const app = getApp();

    appCheck = initializeAppCheck(app, {
      provider: new ReCaptchaV3Provider(recaptchaSiteKey),

      // Enable automatic token refresh
      isTokenAutoRefreshEnabled: true,
    });

    console.log('[AppCheck] Successfully initialized with reCAPTCHA v3');
  } catch (error) {
    console.error('[AppCheck] Initialization failed:', error);
  }
}

/**
 * Get the App Check instance
 */
export function getAppCheckInstance() {
  return appCheck;
}

/**
 * Manually get an App Check token
 * Useful for debugging or manual API calls
 */
export async function getAppCheckToken(forceRefresh = false): Promise<string | null> {
  if (!appCheck) {
    console.warn('[AppCheck] Not initialized');
    return null;
  }

  try {
    const { getToken } = await import('firebase/app-check');
    const tokenResult = await getToken(appCheck, forceRefresh);
    return tokenResult.token;
  } catch (error) {
    console.error('[AppCheck] Failed to get token:', error);
    return null;
  }
}

export default initializeFirebaseAppCheck;
