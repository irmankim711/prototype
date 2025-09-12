/**
 * Test Script for API Debugging Utilities
 * Run this in your browser console or import into a component
 */

import { 
  testEndpoint, 
  testAnalyticsEndpoints, 
  testNextGenEndpoints, 
  generateDebugReport, 
  quickHealthCheck 
} from './debugApiEndpoints';

// Example usage functions
export const runQuickTest = async () => {
  console.log('🚀 Running quick API health check...');
  
  try {
    // Test a single endpoint
    const result = await testEndpoint('/v1/nextgen/data-sources');
    console.log('Single endpoint test result:', result);
    
    // Quick health check
    const isHealthy = await quickHealthCheck();
    console.log('System health:', isHealthy ? '✅ Healthy' : '❌ Unhealthy');
    
  } catch (error) {
    console.error('Quick test failed:', error);
  }
};

export const runAnalyticsTest = async () => {
  console.log('📊 Testing all analytics endpoints...');
  
  try {
    const results = await testAnalyticsEndpoints();
    console.log('Analytics endpoints test results:', results);
    
    // Count successful vs failed
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);
    
    console.log(`📈 Results: ${successful.length} successful, ${failed.length} failed`);
    
  } catch (error) {
    console.error('Analytics test failed:', error);
  }
};

export const runNextGenTest = async () => {
  console.log('🔮 Testing all NextGen report endpoints...');
  
  try {
    const results = await testNextGenEndpoints();
    console.log('NextGen endpoints test results:', results);
    
    // Count successful vs failed
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);
    
    console.log(`📈 Results: ${successful.length} successful, ${failed.length} failed`);
    
  } catch (error) {
    console.error('NextGen test failed:', error);
  }
};

export const runFullDebugReport = async () => {
  console.log('📋 Generating comprehensive debug report...');
  
  try {
    const report = await generateDebugReport();
    console.log('📄 Debug Report:');
    console.log(report);
    
    // You can also copy this to clipboard or save to file
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(report);
      console.log('📋 Report copied to clipboard!');
    }
    
  } catch (error) {
    console.error('Debug report generation failed:', error);
  }
};

// Browser console helpers
if (typeof window !== 'undefined') {
  // Make functions available globally for browser console testing
  (window as any).debugAPI = {
    quickTest: runQuickTest,
    analyticsTest: runAnalyticsTest,
    nextGenTest: runNextGenTest,
    fullReport: runFullDebugReport,
    testEndpoint,
    quickHealthCheck
  };
  
  console.log('🔧 API Debugging utilities loaded!');
  console.log('Available commands:');
  console.log('  debugAPI.quickTest() - Quick health check');
  console.log('  debugAPI.analyticsTest() - Test all analytics endpoints');
  console.log('  debugAPI.nextGenTest() - Test all NextGen endpoints');
  console.log('  debugAPI.fullReport() - Generate comprehensive report');
  console.log('  debugAPI.testEndpoint("/endpoint") - Test specific endpoint');
  console.log('  debugAPI.quickHealthCheck() - Quick system health check');
}

export default {
  runQuickTest,
  runAnalyticsTest,
  runNextGenTest,
  runFullDebugReport
};
