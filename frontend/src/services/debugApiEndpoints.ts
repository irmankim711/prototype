/**
 * API Endpoint Debugging Utility
 * Comprehensive testing and debugging for all API endpoints
 */

import axiosInstance from './axiosInstance';

export interface DebugResult {
  endpoint: string;
  method: string;
  success: boolean;
  status: number;
  statusText: string;
  responseTime: number;
  contentType: string;
  dataSize: number;
  error?: string;
  response?: any;
  headers?: any;
}

export class ApiDebugger {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || 'http://localhost:5000/api';
  }

  /**
   * Test a single endpoint with comprehensive logging
   */
  async testEndpoint(
    endpoint: string, 
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    body?: any
  ): Promise<DebugResult> {
    const startTime = Date.now();
    const fullUrl = `${this.baseUrl}${endpoint}`;
    
    console.log(`🔍 [ApiDebugger] Testing ${method} ${fullUrl}`);
    
    try {
      const config: any = {
        method,
        url: endpoint,
        timeout: 10000,
      };

      if (body) {
        config.data = body;
        console.log('📦 Request body:', body);
      }

      const response = await axiosInstance(config);
      const responseTime = Date.now() - startTime;
      
      const result: DebugResult = {
        endpoint,
        method,
        success: true,
        status: response.status,
        statusText: response.statusText,
        responseTime,
        contentType: response.headers['content-type'] || 'unknown',
        dataSize: JSON.stringify(response.data).length,
        response: response.data,
        headers: response.headers
      };

      console.log('✅ Endpoint test successful:', result);
      return result;

    } catch (error: any) {
      const responseTime = Date.now() - startTime;
      
      const result: DebugResult = {
        endpoint,
        method,
        success: false,
        status: error.response?.status || 0,
        statusText: error.response?.statusText || 'Network Error',
        responseTime,
        contentType: error.response?.headers?.['content-type'] || 'unknown',
        dataSize: 0,
        error: error.message,
        response: error.response?.data,
        headers: error.response?.headers
      };

      console.error('❌ Endpoint test failed:', result);
      return result;
    }
  }

  /**
   * Test multiple endpoints in sequence
   */
  async testMultipleEndpoints(endpoints: Array<{endpoint: string, method?: 'GET' | 'POST' | 'PUT' | 'DELETE', body?: any}>): Promise<DebugResult[]> {
    console.log(`🚀 [ApiDebugger] Testing ${endpoints.length} endpoints...`);
    
    const results: DebugResult[] = [];
    
    for (const endpointConfig of endpoints) {
      const result = await this.testEndpoint(
        endpointConfig.endpoint, 
        endpointConfig.method || 'GET',
        endpointConfig.body
      );
      results.push(result);
      
      // Add delay between requests to avoid overwhelming the server
      if (endpoints.indexOf(endpointConfig) < endpoints.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
    
    return results;
  }

  /**
   * Test all analytics endpoints
   */
  async testAnalyticsEndpoints(): Promise<DebugResult[]> {
    const endpoints = [
      { endpoint: '/analytics/dashboard/stats' },
      { endpoint: '/analytics/trends?days=30' },
      { endpoint: '/analytics/top-forms?limit=5' },
      { endpoint: '/analytics/field-analytics/1' },
      { endpoint: '/analytics/geographic' },
      { endpoint: '/analytics/time-of-day' },
      { endpoint: '/analytics/performance-comparison' },
      { endpoint: '/analytics/real-time' },
      { endpoint: '/analytics/charts/submissions-trend?days=30' }
    ];

    return this.testMultipleEndpoints(endpoints);
  }

  /**
   * Test all NextGen report endpoints
   */
  async testNextGenEndpoints(): Promise<DebugResult[]> {
    const endpoints = [
      { endpoint: '/v1/nextgen/data-sources' },
      { endpoint: '/v1/nextgen/templates' },
      { endpoint: '/v1/nextgen/reports' },
      { endpoint: '/v1/nextgen/charts/generate', method: 'POST', body: { dataSourceId: 'test', config: {} } }
    ];

    return this.testMultipleEndpoints(endpoints);
  }

  /**
   * Generate a comprehensive debug report
   */
  async generateDebugReport(): Promise<string> {
    console.log('📊 [ApiDebugger] Generating comprehensive debug report...');
    
    const analyticsResults = await this.testAnalyticsEndpoints();
    const nextGenResults = await this.testNextGenEndpoints();
    
    const allResults = [...analyticsResults, ...nextGenResults];
    
    const report = this.formatDebugReport(allResults);
    console.log('📋 Debug Report Generated:', report);
    
    return report;
  }

  /**
   * Format debug results into a readable report
   */
  private formatDebugReport(results: DebugResult[]): string {
    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);
    
    let report = `
🔍 API ENDPOINT DEBUG REPORT
Generated: ${new Date().toISOString()}
Base URL: ${this.baseUrl}

📊 SUMMARY
Total Endpoints Tested: ${results.length}
Successful: ${successful.length}
Failed: ${failed.length}
Success Rate: ${((successful.length / results.length) * 100).toFixed(1)}%

✅ SUCCESSFUL ENDPOINTS
${successful.map(r => 
  `  ${r.method} ${r.endpoint} - ${r.status} (${r.responseTime}ms) - ${r.contentType}`
).join('\n')}

❌ FAILED ENDPOINTS
${failed.map(r => 
  `  ${r.method} ${r.endpoint} - ${r.status} ${r.statusText} - ${r.error}`
).join('\n')}

🔧 RECOMMENDATIONS
`;

    if (failed.length > 0) {
      report += `
1. Check if backend server is running on port 5000
2. Verify endpoint routes are properly configured
3. Check CORS settings if testing from browser
4. Review server logs for detailed error information
5. Ensure database connections are working
`;
    } else {
      report += `
🎉 All endpoints are working correctly!
`;
    }

    return report;
  }

  /**
   * Quick health check for critical endpoints
   */
  async quickHealthCheck(): Promise<boolean> {
    console.log('🏥 [ApiDebugger] Performing quick health check...');
    
    try {
      const result = await this.testEndpoint('/analytics/dashboard/stats');
      const isHealthy = result.success && result.status === 200;
      
      console.log(`Health Check Result: ${isHealthy ? '✅ Healthy' : '❌ Unhealthy'}`);
      return isHealthy;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const apiDebugger = new ApiDebugger();

// Export convenience functions
export const testEndpoint = (endpoint: string, method?: 'GET' | 'POST' | 'PUT' | 'DELETE', body?: any) => 
  apiDebugger.testEndpoint(endpoint, method, body);

export const testAnalyticsEndpoints = () => apiDebugger.testAnalyticsEndpoints();
export const testNextGenEndpoints = () => apiDebugger.testNextGenEndpoints();
export const generateDebugReport = () => apiDebugger.generateDebugReport();
export const quickHealthCheck = () => apiDebugger.quickHealthCheck();

export default apiDebugger;
