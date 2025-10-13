import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Alert,
  AlertTitle,
  Divider,
  useTheme,
} from '@mui/material';
import {
  BugReport,
  NetworkCheck,
  Security,
  Info,
  Refresh,
  Error,
} from '@mui/icons-material';
import { useError } from '../../context/ErrorContext';
import { useEnhancedApi } from '../../services/enhancedApiService';
import { NetworkStatus } from '../../components/NetworkStatus';
import { ErrorDashboard } from '../../components/ErrorDashboard';

export const ErrorHandlingDemo: React.FC = () => {
  const theme = useTheme();
  const { addError, state } = useError();
  const { api } = useEnhancedApi();
  const [activeTab, setActiveTab] = useState<'demo' | 'dashboard' | 'network'>('demo');

  // Demo error functions
  const triggerApiError = () => {
    addError({
      message: 'This is a simulated API error for demonstration purposes',
      status: 500,
      endpoint: '/api/demo/error',
      errorType: 'api',
      maxRetries: 3,
      context: {
        demo: true,
        timestamp: new Date().toISOString(),
        source: 'demo-trigger',
      },
    });
  };

  const triggerNetworkError = () => {
    addError({
      message: 'Simulated network connectivity issue',
      status: undefined,
      endpoint: '/api/demo/network',
      errorType: 'network',
      maxRetries: 3,
      context: {
        demo: true,
        timestamp: new Date().toISOString(),
        source: 'demo-trigger',
      },
    });
  };

  const triggerValidationError = () => {
    addError({
      message: 'Input validation failed: Required fields missing',
      status: 400,
      endpoint: '/api/demo/validation',
      errorType: 'validation',
      maxRetries: 1,
      context: {
        demo: true,
        timestamp: new Date().toISOString(),
        source: 'demo-trigger',
        field: 'email',
        value: '',
      },
    });
  };

  const triggerAuthError = () => {
    addError({
      message: 'Authentication token expired. Please log in again.',
      status: 401,
      endpoint: '/api/demo/auth',
      errorType: 'auth',
      maxRetries: 0,
      context: {
        demo: true,
        timestamp: new Date().toISOString(),
        source: 'demo-trigger',
        requiresLogin: true,
      },
    });
  };

  const triggerMultipleErrors = () => {
    // Trigger multiple errors to test the system
    for (let i = 0; i < 3; i++) {
      setTimeout(() => {
        addError({
          message: `Batch error ${i + 1} - Testing error handling system`,
          status: 500 + i,
          endpoint: `/api/demo/batch/${i + 1}`,
          errorType: 'api',
          maxRetries: 2,
          context: {
            demo: true,
            timestamp: new Date().toISOString(),
            source: 'batch-demo',
            batchId: i + 1,
          },
        });
      }, i * 500);
    }
  };

  const testNetworkConnectivity = async () => {
    try {
      const status = await api.getNetworkStatus();
      console.log('Network status:', status);
    } catch (error) {
      console.error('Network check failed:', error);
    }
  };

  const clearAllDemoErrors = () => {
    // This would typically clear all errors, but for demo purposes we'll just add a success message
    addError({
      message: 'Demo errors cleared successfully',
      status: 200,
      endpoint: '/api/demo/clear',
      errorType: 'unknown',
      maxRetries: 0,
      context: {
        demo: true,
        timestamp: new Date().toISOString(),
        source: 'demo-clear',
      },
    });
  };

  const getTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <ErrorDashboard />;
      case 'network':
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Network Status Monitor
            </Typography>
            <NetworkStatus />
          </Box>
        );
      default:
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Error Handling Demo
            </Typography>
            
            {/* System Status */}
            <Alert severity="info" sx={{ mb: 3 }}>
              <AlertTitle>System Status</AlertTitle>
              This demo showcases the global error handling system. Use the buttons below to trigger different types of errors and see how they are handled.
            </Alert>

            {/* Error Statistics */}
            <Grid container spacing={2} mb={3}>
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="error">
                      {state.globalErrorCount}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Total Errors
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="warning">
                      {state.errors.filter(e => e.errorType === 'network').length}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Network Errors
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="info">
                      {state.errors.filter(e => e.errorType === 'api').length}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      API Errors
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Card>
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="h4" color="success">
                      {state.networkStatus.isOnline ? 'Online' : 'Offline'}
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Network Status
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            {/* Demo Controls */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Trigger Demo Errors
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  Click the buttons below to simulate different error scenarios and see how the system handles them.
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<BugReport />}
                      onClick={triggerApiError}
                      fullWidth
                    >
                      API Error
                    </Button>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<NetworkCheck />}
                      onClick={triggerNetworkError}
                      fullWidth
                    >
                      Network Error
                    </Button>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      variant="outlined"
                      color="info"
                      startIcon={<Info />}
                      onClick={triggerValidationError}
                      fullWidth
                    >
                      Validation Error
                    </Button>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      variant="outlined"
                      color="warning"
                      startIcon={<Security />}
                      onClick={triggerAuthError}
                      fullWidth
                    >
                      Auth Error
                    </Button>
                  </Grid>
                </Grid>
                
                <Divider sx={{ my: 2 }} />
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<Error />}
                      onClick={triggerMultipleErrors}
                      fullWidth
                    >
                      Batch Errors
                    </Button>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={<NetworkCheck />}
                      onClick={testNetworkConnectivity}
                      fullWidth
                    >
                      Test Network
                    </Button>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Button
                      variant="outlined"
                      color="success"
                      startIcon={<Refresh />}
                      onClick={clearAllDemoErrors}
                      fullWidth
                    >
                      Clear Errors
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Features Overview */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Error Handling Features
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      🚨 Automatic Error Detection
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      All API requests are automatically monitored for errors and categorized by type.
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      🔄 Smart Retry Logic
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Transient failures are automatically retried with exponential backoff.
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      📱 Toast Notifications
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Users are immediately notified of errors with actionable information.
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      🌐 Network Monitoring
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Real-time network status monitoring with connectivity checks.
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      📊 Error Analytics
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Comprehensive error tracking with statistics and filtering.
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      🛠️ Manual Recovery
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Users can manually retry failed requests or clear resolved errors.
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Box>
        );
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box display="flex" alignItems="center" gap={2} mb={4}>
          <BugReport sx={{ fontSize: 32, color: theme.palette.error.main }} />
          <Typography variant="h4" component="h1">
            Error Handling System Demo
          </Typography>
        </Box>

        {/* Navigation Tabs */}
        <Box display="flex" gap={1} mb={3} flexWrap="wrap">
          <Button
            variant={activeTab === 'demo' ? 'contained' : 'outlined'}
            onClick={() => setActiveTab('demo')}
            startIcon={<BugReport />}
          >
            Demo
          </Button>
          <Button
            variant={activeTab === 'dashboard' ? 'contained' : 'outlined'}
            onClick={() => setActiveTab('dashboard')}
            startIcon={<Error />}
          >
            Error Dashboard
          </Button>
          <Button
            variant={activeTab === 'network' ? 'contained' : 'outlined'}
            onClick={() => setActiveTab('network')}
            startIcon={<NetworkCheck />}
          >
            Network Status
          </Button>
        </Box>

        {/* Content */}
        {getTabContent()}
      </Box>
    </Container>
  );
};

export default ErrorHandlingDemo;
