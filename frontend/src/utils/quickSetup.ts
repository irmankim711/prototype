/**
 * Quick Setup Utility for Browser Console
 * Easy commands for users to set up authentication and test reports
 */

import { setupTestAuth, isAuthenticated, getCurrentUser, clearAuth } from './authHelper';

// Make these functions globally available in browser console
declare global {
  interface Window {
    quickLogin: () => Promise<void>;
    checkAuth: () => void;
    clearAuth: () => void;
    goToReports: () => void;
    helpMe: () => void;
  }
}

/**
 * Quick login function for browser console
 */
window.quickLogin = async () => {
  console.log('🔐 Starting quick login...');
  try {
    const result = await setupTestAuth();
    if (result.success) {
      console.log('✅ Login successful!');
      console.log('👤 User:', result.user);
      console.log('🎯 You can now access report features!');
      console.log('📱 Run: goToReports() to navigate to reports page');
    } else {
      console.error('❌ Login failed:', result.error);
    }
  } catch (error) {
    console.error('💥 Login error:', error);
  }
};

/**
 * Check current authentication status
 */
window.checkAuth = () => {
  const authenticated = isAuthenticated();
  const user = getCurrentUser();
  
  console.log('🔍 Authentication Status:');
  console.log('✅ Authenticated:', authenticated);
  console.log('👤 User:', user);
  
  if (!authenticated) {
    console.log('💡 Run: quickLogin() to login quickly');
  }
};

/**
 * Clear authentication
 */
window.clearAuth = () => {
  clearAuth();
  console.log('🧹 Authentication cleared');
};

/**
 * Navigate to reports page
 */
window.goToReports = () => {
  window.location.href = '/reports';
  console.log('📊 Navigating to reports page...');
};

/**
 * Help function showing all available commands
 */
window.helpMe = () => {
  console.log('🚀 QUICK SETUP COMMANDS:');
  console.log('');
  console.log('📋 Available Commands:');
  console.log('  quickLogin()   - Quick login with test account');
  console.log('  checkAuth()    - Check if you are logged in');
  console.log('  clearAuth()    - Clear login data');
  console.log('  goToReports()  - Navigate to reports page');
  console.log('  helpMe()       - Show this help');
  console.log('');
  console.log('🎯 QUICK START:');
  console.log('  1. Run: quickLogin()');
  console.log('  2. Run: goToReports()');
  console.log('  3. Click "DOCX Generator" tab');
  console.log('  4. Upload Excel file');
  console.log('  5. After generation, click View/Edit/Download!');
  console.log('');
  console.log('🔍 TROUBLESHOOTING:');
  console.log('  - If 401 errors: Run quickLogin()');
  console.log('  - If page not loading: Check network tab');
  console.log('  - Need help: Run helpMe()');
};

// Auto-run help on load
console.log('🎉 QUICK SETUP LOADED!');
console.log('💡 Run: helpMe() for available commands');
console.log('🚀 Or run: quickLogin() to start immediately');

export { };