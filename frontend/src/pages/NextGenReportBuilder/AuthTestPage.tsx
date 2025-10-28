import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Authentication Test Page for NextGen Report Builder
 * Simple test to verify authentication and API connectivity
 */

import { useState, useEffect } from "react";
  
import { Box, Paper, Typography, Button, Alert, CircularProgress, List, ListItem, ListItemText, Divider } from "@mui/material";
  
import { Check, Error, Refresh } from "@mui/icons-material";

import { useFirebaseAuth } from "../../context/FirebaseAuthContext";

import { nextGenReportService } from "../../services/nextGenReportService";

import { useOptimizedDataFetch } from "../../hooks/useOptimizedDataFetch";

const AuthTestPage: React.FC = () => {
  const { isAuthenticated, isLoading } = useFirebaseAuth();
  const accessToken = localStorage.getItem('firebaseToken');
  
  // Use optimized data fetching to prevent multiple API calls
  const { data: dataSources, isLoading: dataSourcesLoading, error: dataSourcesError } = useOptimizedDataFetch({
    fetchFn: () => nextGenReportService.getDataSources(),
    cacheKey: 'authTest_dataSources',
    cacheDuration: 2 * 60 * 1000, // 2 minutes
    enabled: isAuthenticated && !isLoading
  });

const { data: templates, isLoading: templatesLoading, error: templatesError } = useOptimizedDataFetch({
    fetchFn: () => nextGenReportService.getReportTemplates(),
    cacheKey: 'authTest_templates',
    cacheDuration: 2 * 60 * 1000, // 2 minutes
    enabled: isAuthenticated && !isLoading
  });

const [testResults, setTestResults] = useState<{
    auth: 'pending' | 'success' | 'error';
    
dataSources: 'pending' | 'success' | 'error';
    
templates: 'pending' | 'success' | 'error';
  }>({
    auth: 'pending',
    dataSources: 'pending',
    templates: 'pending'
  });
  
const [errorMessages, setErrorMessages] = useState<string[]>([]);
  
const [isRunningTests, setIsRunningTests] = useState(false);

useEffect(() => {
    if (isAuthenticated && !isLoading) {
      // Update test results based on optimized data fetching
      updateTestResults();
    }
  }, [isAuthenticated, isLoading, dataSources, templates, dataSourcesError, templatesError]);

const updateTestResults = () => {
    // Auth test is always successful if we reach this point
    setTestResults(prev => ({ ...prev, auth: 'success' }));

    // Data sources test
    if (dataSourcesLoading) {
      setTestResults(prev => ({ ...prev, dataSources: 'pending' }));
    } else if (dataSourcesError) {
      setTestResults(prev => ({ ...prev, dataSources: 'error' }));
      
setErrorMessages(prev => [...prev.filter(msg => !msg.includes('Data Sources')), `Data Sources: ${dataSourcesError.message}`]);
    } else if (dataSources) {
      setTestResults(prev => ({ ...prev, dataSources: 'success' }));
      
setErrorMessages(prev => prev.filter(msg => !msg.includes('Data Sources')));
    }

    // Templates test
    if (templatesLoading) {
      setTestResults(prev => ({ ...prev, templates: 'pending' }));
    } else if (templatesError) {
      setTestResults(prev => ({ ...prev, templates: 'error' }));
      
setErrorMessages(prev => [...prev.filter(msg => !msg.includes('Templates')), `Templates: ${templatesError.message}`]);
    } else if (templates) {
      setTestResults(prev => ({ ...prev, templates: 'success' }));
      
setErrorMessages(prev => prev.filter(msg => !msg.includes('Templates')));
    }
  };

const runTests = async () => {
    setIsRunningTests(true);
    
setErrorMessages([]);
    
    // Test 1: Authentication
    setTestResults(prev => ({ ...prev, auth: 'success' }));

    // Test 2: Data Sources API - use cached data if available, otherwise fetch fresh
    try {
      if (dataSources) {
        setTestResults(prev => ({ ...prev, dataSources: 'success' }));
      } else {
        await nextGenReportService.getDataSources();
        
setTestResults(prev => ({ ...prev, dataSources: 'success' }));
      }
    } catch (error: any) {
      setTestResults(prev => ({ ...prev, dataSources: 'error' }));
      
setErrorMessages(prev => [...prev, `Data Sources: ${error.message}`]);
    }

    // Test 3: Templates API - use cached data if available, otherwise fetch fresh
    try {
      if (templates) {
        setTestResults(prev => ({ ...prev, templates: 'success' }));
      } else {
        await nextGenReportService.getReportTemplates();
        
setTestResults(prev => ({ ...prev, templates: 'success' }));
      }
    } catch (error: any) {
      setTestResults(prev => ({ ...prev, templates: 'error' }));
      
setErrorMessages(prev => [...prev, `Templates: ${error.message}`]);
    }

    setIsRunningTests(false);
  };

const getTestIcon = (status: 'pending' | 'success' | 'error') => {
    switch (status) {
      case 'success':
        return <Check color="success" />;
      
case 'error':
        return <Error color="error" />;
      
default:
        return <CircularProgress size={20} />;
    }
  };

const getTestColor = (status: 'pending' | 'success' | 'error') => {
    switch (status) {
      case 'success':
        return 'success.main';
      
case 'error':
        return 'error.main';
      
default:
        return 'text.secondary';
    }
  };

if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <Paper sx={{ p: 4, maxWidth: 500, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Authentication Required
          </Typography>
          <Typography color="text.secondary">
            Please log in to run authentication tests.
          </Typography>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h4" gutterBottom>
        NextGen Report Builder - Authentication Test
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Authentication Status
        </Typography>
        <List>
          <ListItem>
            <ListItemText 
              primary="User Authenticated" 
              secondary={`Token: ${accessToken ? 'Present' : 'Missing'}`}
            />
            {getTestIcon(testResults.auth)}
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Data Sources API" 
              secondary="Testing connection to /v1/nextgen/data-sources"
            />
            {getTestIcon(testResults.dataSources)}
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Templates API" 
              secondary="Testing connection to /v1/nextgen/templates"
            />
            {getTestIcon(testResults.templates)}
          </ListItem>
        </List>

        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            startIcon={<Refresh />}
            onClick={runTests}
            disabled={isRunningTests}
          >
            {isRunningTests ? 'Running Tests...' : 'Run Tests Again'}
          </Button>
        </Box>
      </Paper>

      {errorMessages.length > 0 && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Test Errors
          </Typography>
          {errorMessages.map((message, index) => (
            <Typography key={index} variant="body2">
              • {message}
            </Typography>
          ))}
        </Alert>
      )}

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Test Summary
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          This page tests the authentication flow and API connectivity for the NextGen Report Builder.
          All tests should pass for the system to work correctly.
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Typography variant="body2">
            Auth: <span style={{ color: getTestColor(testResults.auth) }}>
              {testResults.auth === 'pending' ? 'Pending' : 
               testResults.auth === 'success' ? '✓ Success' : '✗ Error'}
            </span>
          </Typography>
          <Typography variant="body2">
            Data Sources: <span style={{ color: getTestColor(testResults.dataSources) }}>
              {testResults.dataSources === 'pending' ? 'Pending' : 
               testResults.dataSources === 'success' ? '✓ Success' : '✗ Error'}
            </span>
          </Typography>
          <Typography variant="body2">
            Templates: <span style={{ color: getTestColor(testResults.templates) }}>
              {testResults.templates === 'pending' ? 'Pending' : 
               testResults.templates === 'success' ? '✓ Success' : '✗ Error'}
            </span>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default AuthTestPage;
