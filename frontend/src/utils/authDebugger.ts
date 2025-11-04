/**
 * Authentication Debugging Utilities
 *
 * Use these functions in the browser console to debug authentication issues:
 *
 * window.authDebug.inspectAuth() - Check current auth state
 * window.authDebug.inspectStorage() - Check localStorage/sessionStorage
 * window.authDebug.clearFirebaseKeys() - Manually clear Firebase keys
 * window.authDebug.monitorAuthChanges() - Start monitoring auth changes
 */

export class AuthDebugger {
  private authChangeListeners: Array<() => void> = [];

  /**
   * Inspect current authentication state
   */
  inspectAuth(): void {
    console.group('🔍 Authentication State Inspection');

    // Check if Firebase is loaded
    try {
      const firebaseKeys = Object.keys(localStorage).filter(k => k.startsWith('firebase:'));
      console.log('Firebase keys in localStorage:', firebaseKeys.length);
      firebaseKeys.forEach(key => {
        const value = localStorage.getItem(key);
        console.log(`  - ${key}: ${value?.substring(0, 100)}...`);
      });
    } catch (err) {
      console.error('Error inspecting Firebase keys:', err);
    }

    // Check custom tokens
    const customTokens = {
      firebaseToken: localStorage.getItem('firebaseToken'),
      accessToken: localStorage.getItem('accessToken'),
      refreshToken: localStorage.getItem('refreshToken'),
    };

    console.log('Custom tokens:', {
      firebaseToken: customTokens.firebaseToken ? 'Present ✓' : 'Missing ✗',
      accessToken: customTokens.accessToken ? 'Present ✓' : 'Missing ✗',
      refreshToken: customTokens.refreshToken ? 'Present ✓' : 'Missing ✗',
    });

    // Decode firebaseToken if present
    if (customTokens.firebaseToken) {
      try {
        const decoded = this.decodeJWT(customTokens.firebaseToken);
        console.log('Decoded firebaseToken:', {
          email: decoded?.email,
          sub: decoded?.sub,
          exp: decoded?.exp ? new Date(decoded.exp * 1000).toISOString() : 'N/A',
          iat: decoded?.iat ? new Date(decoded.iat * 1000).toISOString() : 'N/A',
          isExpired: decoded?.exp ? decoded.exp < Date.now() / 1000 : 'Unknown',
        });
      } catch (err) {
        console.error('Failed to decode firebaseToken:', err);
      }
    }

    console.groupEnd();
  }

  /**
   * Inspect all storage (localStorage + sessionStorage)
   */
  inspectStorage(): void {
    console.group('💾 Storage Inspection');

    console.log('📦 LocalStorage:');
    console.table(
      Object.keys(localStorage).map(key => ({
        key,
        value: localStorage.getItem(key)?.substring(0, 50) + '...',
        length: localStorage.getItem(key)?.length || 0,
      }))
    );

    console.log('📦 SessionStorage:');
    console.table(
      Object.keys(sessionStorage).map(key => ({
        key,
        value: sessionStorage.getItem(key)?.substring(0, 50) + '...',
        length: sessionStorage.getItem(key)?.length || 0,
      }))
    );

    console.groupEnd();
  }

  /**
   * Clear all Firebase-related keys from storage
   */
  clearFirebaseKeys(): void {
    console.group('🧹 Clearing Firebase Keys');

    const firebaseKeys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('firebase:')) {
        firebaseKeys.push(key);
      }
    }

    console.log(`Found ${firebaseKeys.length} Firebase keys to remove`);
    firebaseKeys.forEach(key => {
      localStorage.removeItem(key);
      console.log(`  ✓ Removed: ${key}`);
    });

    // Also clear custom keys
    const customKeys = ['firebaseToken', 'accessToken', 'refreshToken', 'userData'];
    customKeys.forEach(key => {
      if (localStorage.getItem(key)) {
        localStorage.removeItem(key);
        console.log(`  ✓ Removed: ${key}`);
      }
    });

    console.log('✅ Cleanup complete');
    console.groupEnd();
  }

  /**
   * Monitor authentication changes in real-time
   */
  monitorAuthChanges(): () => void {
    console.log('👁️ Starting auth change monitoring...');
    console.log('Watch this console for authentication events');

    // Monitor localStorage changes
    const originalSetItem = localStorage.setItem.bind(localStorage);
    const originalRemoveItem = localStorage.removeItem.bind(localStorage);

    localStorage.setItem = (key: string, value: string) => {
      if (key.includes('firebase') || key.includes('token') || key.includes('auth')) {
        console.log(`📝 [${new Date().toISOString()}] localStorage.setItem:`, {
          key,
          valueLength: value.length,
          preview: value.substring(0, 50) + '...',
        });
      }
      return originalSetItem(key, value);
    };

    localStorage.removeItem = (key: string) => {
      if (key.includes('firebase') || key.includes('token') || key.includes('auth')) {
        console.log(`🗑️ [${new Date().toISOString()}] localStorage.removeItem:`, key);
      }
      return originalRemoveItem(key);
    };

    // Return cleanup function
    return () => {
      localStorage.setItem = originalSetItem;
      localStorage.removeItem = originalRemoveItem;
      console.log('✅ Stopped auth change monitoring');
    };
  }

  /**
   * Decode JWT token
   */
  private decodeJWT(token: string): any {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;

      const payload = parts[1];
      const decoded = JSON.parse(atob(payload));
      return decoded;
    } catch (error) {
      console.error('Failed to decode JWT:', error);
      return null;
    }
  }

  /**
   * Test logout cleanup
   */
  async testLogoutCleanup(): Promise<void> {
    console.group('🧪 Testing Logout Cleanup');

    console.log('📊 Before logout:');
    const beforeKeys = Object.keys(localStorage).filter(
      k => k.includes('firebase') || k.includes('token')
    );
    console.log('  Keys:', beforeKeys);

    console.log('\n⏳ Simulating logout...');

    // Simulate clearAllAuthData
    const authKeys = ['accessToken', 'refreshToken', 'firebaseToken', 'userData'];
    authKeys.forEach(key => localStorage.removeItem(key));

    const firebaseKeys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('firebase:')) {
        firebaseKeys.push(key);
      }
    }
    firebaseKeys.forEach(key => localStorage.removeItem(key));

    console.log('\n📊 After logout:');
    const afterKeys = Object.keys(localStorage).filter(
      k => k.includes('firebase') || k.includes('token')
    );
    console.log('  Keys:', afterKeys);

    const cleanupSuccess = afterKeys.length === 0;
    console.log(
      cleanupSuccess
        ? '\n✅ Cleanup successful - all auth keys removed'
        : '\n❌ Cleanup failed - some keys remain'
    );

    console.groupEnd();
  }

  /**
   * Simulate login flow (for testing)
   */
  simulateLogin(email: string = 'test@example.com'): void {
    console.group('🧪 Simulating Login Flow');

    // Simulate Firebase auth state
    const mockFirebaseKey = 'firebase:authUser:MOCK_API_KEY:localhost';
    const mockUserData = {
      uid: 'mock-uid-12345',
      email,
      displayName: 'Test User',
      emailVerified: true,
    };

    localStorage.setItem(mockFirebaseKey, JSON.stringify(mockUserData));
    console.log('✓ Set Firebase auth key:', mockFirebaseKey);

    // Simulate custom token
    const mockToken = this.generateMockJWT(email);
    localStorage.setItem('firebaseToken', mockToken);
    console.log('✓ Set firebaseToken');

    console.log('\n📊 Current state:');
    this.inspectAuth();

    console.groupEnd();
  }

  /**
   * Generate mock JWT for testing
   */
  private generateMockJWT(email: string): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(
      JSON.stringify({
        sub: 'mock-uid-12345',
        email,
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour
      })
    );
    const signature = 'mock-signature';

    return `${header}.${payload}.${signature}`;
  }
}

// Create global instance
const authDebugger = new AuthDebugger();

// Expose to window for browser console access
if (typeof window !== 'undefined') {
  (window as any).authDebug = authDebugger;
  console.log('🔧 Auth Debugger loaded. Try: window.authDebug.inspectAuth()');
}

export default authDebugger;
