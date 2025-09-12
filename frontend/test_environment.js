#!/usr/bin/env node
/**
 * Test Vite Environment Variables
 * Verifies that environment variables are properly loaded
 */

console.log('🧪 Testing Vite Environment Variables...');
console.log('=' * 50);

// Test if environment variables are accessible
try {
  // Check if we're in a Vite environment
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    console.log('✅ Vite environment detected');
    
    // Test key environment variables
    const envVars = [
      'VITE_API_URL',
      'VITE_ENVIRONMENT',
      'VITE_APP_NAME',
      'VITE_ENABLE_AI_FEATURES'
    ];
    
    envVars.forEach(varName => {
      const value = import.meta.env[varName];
      if (value !== undefined) {
        console.log(`✅ ${varName}: ${value}`);
      } else {
        console.log(`❌ ${varName}: NOT SET`);
      }
    });
    
  } else {
    console.log('❌ Vite environment not detected');
    console.log('This script should be run in a Vite environment');
  }
  
} catch (error) {
  console.error('❌ Error testing environment variables:', error.message);
}

console.log('\n' + '=' * 50);
console.log('✅ Environment Test Complete');

// Additional environment info
console.log('\n📋 Environment Information:');
console.log(`Node Version: ${process.version}`);
console.log(`Platform: ${process.platform}`);
console.log(`Architecture: ${process.arch}`);
console.log(`Current Directory: ${process.cwd()}`);
