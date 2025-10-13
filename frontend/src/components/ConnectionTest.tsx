import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ConnectionTest: React.FC = () => {
  const [status, setStatus] = useState<string>('Testing...');
  const [details, setDetails] = useState<any>({});

  useEffect(() => {
    const testConnection = async () => {
      const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
      
      console.log('🔧 Connection Test Debug:');
      console.log('  VITE_API_URL:', import.meta.env.VITE_API_URL);
      console.log('  Final API_BASE_URL:', API_BASE_URL);
      console.log('  Environment Mode:', import.meta.env.MODE);
      console.log('  All env vars:', import.meta.env);

      setDetails({
        envApiUrl: import.meta.env.VITE_API_URL,
        finalApiUrl: API_BASE_URL,
        mode: import.meta.env.MODE,
      });

      try {
        // Test 1: Basic health check
        console.log('Testing basic health endpoint...');
        const healthResponse = await axios.get('http://localhost:5000/health');
        console.log('✅ Health check passed:', healthResponse.status);

        // Test 2: API endpoint with expected auth error
        console.log('Testing API endpoint...');
        const apiResponse = await axios.get(`${API_BASE_URL}/analytics/performance-comparison`);
        console.log('Unexpected success:', apiResponse.status);
        setStatus('✅ Connection working (unexpected success)');
        
      } catch (error: any) {
        console.log('API Error details:', error);
        
        if (error.code === 'ERR_NETWORK') {
          setStatus('❌ Network Error - Backend not reachable');
        } else if (error.response?.status === 401) {
          setStatus('✅ Connection working (401 auth error expected)');
        } else if (error.response?.status) {
          setStatus(`✅ Connection working (HTTP ${error.response.status})`);
        } else {
          setStatus(`❌ Unknown error: ${error.message}`);
        }
      }
    };

    testConnection();
  }, []);

  return (
    <div style={{ 
      position: 'fixed', 
      top: '10px', 
      right: '10px', 
      background: 'white', 
      border: '2px solid #ccc', 
      padding: '15px', 
      borderRadius: '5px',
      zIndex: 9999,
      boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
      maxWidth: '400px'
    }}>
      <h3 style={{ margin: '0 0 10px 0', color: '#333' }}>🔧 Connection Test</h3>
      <div style={{ marginBottom: '10px' }}>
        <strong>Status:</strong> {status}
      </div>
      <div style={{ fontSize: '12px', color: '#666' }}>
        <div><strong>Env API URL:</strong> {details.envApiUrl || 'undefined'}</div>
        <div><strong>Final API URL:</strong> {details.finalApiUrl}</div>
        <div><strong>Mode:</strong> {details.mode}</div>
      </div>
      <div style={{ marginTop: '10px', fontSize: '11px', color: '#999' }}>
        Check browser console for detailed logs
      </div>
    </div>
  );
};

export default ConnectionTest;
