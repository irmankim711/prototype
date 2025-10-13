import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";
  
import { Box, Button, TextField, Typography, Alert, Card, CardContent, CircularProgress } from "@mui/material";

import { reportService } from "../services/reportService";

import DocumentPreview from './DocumentPreview';

const DebugPreview: React.FC = () => {
  const [reportId, setReportId] = useState('');
  
const [testResults, setTestResults] = useState<Array<{
    name: string;
    
url: string;
    
status: number;
    
success: boolean;
    
data: any;
    
error: string | null;
  }>>([]);
  
const [loading, setLoading] = useState(false);
  
const [showPreview, setShowPreview] = useState(false);
  
const [selectedReportId, setSelectedReportId] = useState('');

const testPreviewEndpoints = async () => {
    if (!reportId) {
      alert('Please enter a report ID');
      
return;
    }

    setLoading(true);
    
setTestResults([]);

const endpoints = [
      { name: 'Reports API', url: `/api/reports/${reportId}/preview` },
      { name: 'NextGen API', url: `/api/v1/nextgen/reports/${reportId}/preview` },
      { name: 'Excel-to-DOCX', url: `/api/excel-to-docx/${reportId}/preview` },
    ];

const results = [];

for (const endpoint of endpoints) {
      try {
        console.log(`🔍 Testing ${endpoint.name}: ${endpoint.url}`);

const response = await fetch(endpoint.url, {
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken') || ''}`,
            'Content-Type': 'application/json',
          },
        });

const data = await response.json();

results.push({
          name: endpoint.name,
          url: endpoint.url,
          status: response.status,
          success: response.ok,
          data: data,
          error: response.ok ? null : data.error || 'any error',
        });

      } catch (error: any) {
        const errorMessage = error instanceof Error ? error.message : 'any error';
        
results.push({
          name: endpoint.name,
          url: endpoint.url,
          status: 0,
          success: false,
          data: null,
          error: errorMessage,
        });
      }
    }

    setTestResults(results);
    
setLoading(false);
  };

const testReportService = async () => {
    if (!reportId) {
      alert('Please enter a report ID');
      
return;
    }

    setLoading(true);
    
try {
      console.log('🧪 Testing reportService.previewReport()...');
      
const result = await reportService.previewReport(reportId);
      
console.log('✅ reportService result:', result);

setTestResults([{
        name: 'reportService.previewReport()',
        url: 'Service call',
        status: 200,
        success: true,
        data: result,
        error: null,
      }]);

    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'any error';
      
const errorStatus = error && typeof error === 'object' && 'response' in error &&
        error.response && typeof error.response === 'object' && 'status' in error.response ?
        (error.response as { status: number }).status : 0;
      
console.error('❌ reportService failed:', error);
      
setTestResults([{
        name: 'reportService.previewReport()',
        url: 'Service call',
        status: errorStatus,
        success: false,
        data: null,
        error: errorMessage,
      }]);
    }
    setLoading(false);
  };

const openPreviewModal = () => {
    if (!reportId) {
      alert('Please enter a report ID');
      
return;
    }
    setSelectedReportId(reportId);
    
setShowPreview(true);
  };

const checkAuthStatus = () => {
    const token = localStorage.getItem('accessToken');
    
const refreshToken = localStorage.getItem('refreshToken');

alert(`Auth Status:
Access Token: ${token ? 'Present' : 'Missing'}
Refresh Token: ${refreshToken ? 'Present' : 'Missing'}
Token Preview: ${token ? token.substring(0, 20) + '...' : 'N/A'}`);
  };

return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        🐛 Debug Report Preview
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        Use this tool to debug why report previews aren't showing. 
        First make sure you're logged in, then test with a real report ID.
      </Alert>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
        <TextField
          label="Report ID"
          value={reportId}
          onChange={(e: any) => setReportId(e.target.value)}
          placeholder="e.g., 1, 2, 3"
          size="small"
        />
        <Button variant="outlined" onClick={checkAuthStatus}>
          Check Auth
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button 
          variant="contained" 
          onClick={testPreviewEndpoints}
          disabled={loading}
        >
          Test All Endpoints
        </Button>
        <Button 
          variant="outlined" 
          onClick={testReportService}
          disabled={loading}
        >
          Test Service
        </Button>
        <Button 
          variant="outlined" 
          onClick={openPreviewModal}
          disabled={loading}
          color="success"
        >
          Open Preview Modal
        </Button>
      </Box>

      {loading && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <CircularProgress size={20} />
          <Typography>Testing endpoints...</Typography>
        </Box>
      )}

      {testResults.length > 0 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Test Results:
          </Typography>
          {testResults.map((result, index) => (
            <Card key={index} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {result.name}
                  </Typography>
                  <Box
                    sx={{
                      px: 1,
                      py: 0.5,
                      borderRadius: 1,
                      fontSize: '0.75rem',
                      backgroundColor: result.success ? 'success.light' : 'error.light',
                      color: result.success ? 'success.contrastText' : 'error.contrastText',
                    }}
                  >
                    {result.status}
                  </Box>
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {result.url}
                </Typography>

                {result.success ? (
                  <Alert severity="success" sx={{ mb: 1 }}>
                    ✅ Success! Preview data received.
                  </Alert>
                ) : (
                  <Alert severity="error" sx={{ mb: 1 }}>
                    ❌ {result.error}
                  </Alert>
                )}

                {result.data && (
                  <Box>
                    <Typography variant="subtitle2">Response Data:</Typography>
                    <pre style={{ 
                      backgroundColor: '#f5f5f5', 
                      padding: '8px', 
                      borderRadius: '4px',
                      fontSize: '12px',
                      overflow: 'auto',
                      maxHeight: '200px'
                    }}>
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  </Box>
                )}
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      <DocumentPreview
        open={showPreview}
        onClose={() => setShowPreview(false)}
        reportId={selectedReportId}
        title={`Debug Preview - Report ${selectedReportId}`}
      />

      <Box sx={{ mt: 4, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
        <Typography variant="h6">🔧 Troubleshooting Steps:</Typography>
        <ol>
          <li>Click "Check Auth" to verify you're logged in</li>
          <li>Generate a report in NextGen Report Builder first</li>
          <li>Note the report ID from the success message</li>
          <li>Enter that ID above and click "Test All Endpoints"</li>
          <li>Check which endpoint works (should be green)</li>
          <li>Click "Open Preview Modal" to test the actual component</li>
        </ol>
      </Box>
    </Box>
  );
};

export default DebugPreview;
