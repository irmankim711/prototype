import React, { useEffect, useState } from 'react';
import { NextGenReportService } from './nextGenReportService';

/**
 * Debug Test Component for NextGen Report Service
 * Use this to test and debug the data sources endpoint
 */

interface DebugTestProps {
  autoTest?: boolean;
  showLogs?: boolean;
}

export const DebugTestComponent: React.FC<DebugTestProps> = ({ 
  autoTest = false, 
  showLogs = true 
}) => {
  const [testResults, setTestResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Test function with comprehensive logging
  const testDataSources = async (testId: string) => {
    const startTime = Date.now();
    console.log(`🧪 [Test-${testId}] Starting data sources test...`);
    
    try {
      console.log(`🧪 [Test-${testId}] Calling NextGenReportService.getDataSources()...`);
      const dataSources = await NextGenReportService.getDataSources();
      
      const duration = Date.now() - startTime;
      const result = {
        testId,
        success: true,
        duration,
        dataSourcesCount: dataSources?.length || 0,
        timestamp: new Date().toISOString(),
        data: dataSources
      };
      
      console.log(`✅ [Test-${testId}] Test succeeded:`, result);
      return result;
      
    } catch (error: any) {
      const duration = Date.now() - startTime;
      const result = {
        testId,
        success: false,
        duration,
        error: error.message,
        timestamp: new Date().toISOString(),
        stack: error.stack
      };
      
      console.error(`❌ [Test-${testId}] Test failed:`, result);
      return result;
    }
  };

  // Run multiple tests to trigger deduplication
  const runMultipleTests = async () => {
    setIsLoading(true);
    setError(null);
    setTestResults([]);
    
    console.log('🚀 Starting multiple concurrent tests to trigger deduplication...');
    
    try {
      // Run 3 tests simultaneously to trigger deduplication
      const testPromises = [
        testDataSources('A'),
        testDataSources('B'),
        testDataSources('C')
      ];
      
      const results = await Promise.all(testPromises);
      setTestResults(results);
      
      // Analyze results
      const successful = results.filter(r => r.success);
      const failed = results.filter(r => !r.success);
      
      console.log(`📊 Test Results Summary:`);
      console.log(`  Total Tests: ${results.length}`);
      console.log(`  Successful: ${successful.length}`);
      console.log(`  Failed: ${failed.length}`);
      
      if (failed.length > 0) {
        console.log(`❌ Failed Tests:`, failed);
      }
      
      if (successful.length > 0) {
        console.log(`✅ Successful Tests:`, successful);
      }
      
    } catch (error: any) {
      setError(error.message);
      console.error('🚨 Multiple tests failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Single test
  const runSingleTest = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await testDataSources('Single');
      setTestResults([result]);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-test on mount
  useEffect(() => {
    if (autoTest) {
      runMultipleTests();
    }
  }, [autoTest]);

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>🔍 NextGen Report Service Debug Test</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <button 
          onClick={runSingleTest} 
          disabled={isLoading}
          style={{ marginRight: '10px', padding: '10px 20px' }}
        >
          🧪 Single Test
        </button>
        
        <button 
          onClick={runMultipleTests} 
          disabled={isLoading}
          style={{ padding: '10px 20px' }}
        >
          🚀 Multiple Tests (Trigger Deduplication)
        </button>
      </div>

      {isLoading && (
        <div style={{ color: 'blue', marginBottom: '10px' }}>
          ⏳ Running tests... Check browser console for detailed logs
        </div>
      )}

      {error && (
        <div style={{ color: 'red', marginBottom: '10px', padding: '10px', backgroundColor: '#ffeeee' }}>
          ❌ Error: {error}
        </div>
      )}

      {testResults.length > 0 && (
        <div>
          <h3>📊 Test Results ({testResults.length})</h3>
          {testResults.map((result, index) => (
            <div 
              key={index}
              style={{
                border: '1px solid #ccc',
                padding: '15px',
                marginBottom: '10px',
                backgroundColor: result.success ? '#f0fff0' : '#fff0f0',
                borderRadius: '5px'
              }}
            >
              <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>
                Test {result.testId} - {result.success ? '✅ SUCCESS' : '❌ FAILED'}
              </div>
              <div>Duration: {result.duration}ms</div>
              <div>Timestamp: {result.timestamp}</div>
              {result.success ? (
                <div>Data Sources: {result.dataSourcesCount}</div>
              ) : (
                <div>Error: {result.error}</div>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
        <h4>🔧 How to Use:</h4>
        <ol>
          <li>Open your browser's Developer Console (F12)</li>
          <li>Click "Multiple Tests" to trigger the race condition</li>
          <li>Watch the console logs to see the deduplication process</li>
          <li>Look for request IDs and deduplication IDs in the logs</li>
          <li>Identify which requests succeed vs fail</li>
        </ol>
        
        <h4>📝 Expected Console Output:</h4>
        <pre style={{ backgroundColor: '#fff', padding: '10px', borderRadius: '3px' }}>
{`🆔 [abc123def] getDataSources called
🔄 [Dedup-xyz789] Checking deduplication for key: getDataSources
🚀 [Dedup-xyz789] Creating new request for key: getDataSources
📡 [abc123def] Making API request to /v1/nextgen/data-sources...
📥 [abc123def] Raw API response received: {...}
✅ [abc123def] Response has data property with array
✅ [abc123def] Successfully processed 4 valid data sources`}
        </pre>
      </div>
    </div>
  );
};

export default DebugTestComponent;
