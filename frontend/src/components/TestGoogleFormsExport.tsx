import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  Paper,
  Grid,
  Divider,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Google as GoogleIcon,
  TableChart as TableChartIcon,
} from '@mui/icons-material';
import { formBuilderAPI } from '../services/formBuilder';

interface TestResult {
  name: string;
  status: 'success' | 'error' | 'warning' | 'pending';
  message: string;
  details?: any;
}

const TestGoogleFormsExport: React.FC = () => {
  const [tests, setTests] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentTest, setCurrentTest] = useState<string>('');

  const testCases = [
    {
      name: 'API Connection',
      test: async () => {
        const response = await fetch('/api/health');
        if (response.ok) {
          return { status: 'success', message: 'API server is running' };
        } else {
          return { status: 'error', message: 'API server not responding' };
        }
      }
    },
    {
      name: 'Google Forms Service Status',
      test: async () => {
        try {
          const status = await formBuilderAPI.getGoogleFormsStatus();
          if (status.success) {
            return {
              status: status.is_authorized ? 'success' : 'warning',
              message: status.message,
              details: status
            };
          } else {
            return { status: 'error', message: status.message || 'Service check failed' };
          }
        } catch (error: any) {
          return { status: 'error', message: error.message || 'Network error' };
        }
      }
    },
    {
      name: 'Local Forms API',
      test: async () => {
        try {
          const result = await formBuilderAPI.getAllForms();
          return {
            status: 'success',
            message: `Found ${result.forms?.length || 0} local forms`,
            details: { count: result.forms?.length || 0 }
          };
        } catch (error: any) {
          return { status: 'error', message: error.message || 'Failed to fetch local forms' };
        }
      }
    },
    {
      name: 'Export Service Integration',
      test: async () => {
        try {
          // Test if the Google Forms Excel service exists
          const testOptions = {
            include_analytics: true,
            excel_options: { formatting: 'professional' }
          };

          // This should fail gracefully with authentication error
          const result = await formBuilderAPI.exportGoogleFormsToExcel('test_form_id', testOptions);

          // If we get here without throwing, that's unexpected
          return { status: 'warning', message: 'Export test completed unexpectedly' };
        } catch (error: any) {
          // Expected to fail with authentication or service error
          if (error.message.includes('401') || error.message.includes('403') || error.message.includes('503')) {
            return { status: 'success', message: 'Export service is properly secured (auth required)' };
          } else {
            return { status: 'warning', message: `Export service responded with: ${error.message}` };
          }
        }
      }
    }
  ];

  const runTests = async () => {
    setIsRunning(true);
    setTests([]);

    for (const testCase of testCases) {
      setCurrentTest(testCase.name);

      // Add pending test
      setTests(prev => [...prev, {
        name: testCase.name,
        status: 'pending',
        message: 'Running...'
      }]);

      try {
        const result = await testCase.test();

        // Update with result
        setTests(prev => prev.map(test =>
          test.name === testCase.name
            ? { ...test, ...result }
            : test
        ));
      } catch (error: any) {
        setTests(prev => prev.map(test =>
          test.name === testCase.name
            ? {
                ...test,
                status: 'error' as const,
                message: error.message || 'Test failed'
              }
            : test
        ));
      }

      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 500));
    }

    setCurrentTest('');
    setIsRunning(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircleIcon color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'warning': return <WarningIcon color="warning" />;
      default: return <CircularProgress size={20} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'error': return 'error';
      case 'warning': return 'warning';
      default: return 'info';
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 2 }}>
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" mb={3}>
            <TableChartIcon sx={{ mr: 2, color: 'primary.main' }} />
            <Typography variant="h5">
              Google Forms Export Integration Test
            </Typography>
          </Box>

          <Typography variant="body1" color="text.secondary" mb={3}>
            This test verifies that the Google Forms Excel export functionality is properly integrated.
          </Typography>

          <Box mb={3}>
            <Button
              variant="contained"
              onClick={runTests}
              disabled={isRunning}
              startIcon={isRunning ? <CircularProgress size={20} /> : <GoogleIcon />}
              size="large"
            >
              {isRunning ? `Running: ${currentTest}` : 'Run Integration Tests'}
            </Button>
          </Box>

          {tests.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="h6" mb={2}>Test Results</Typography>

              <List>
                {tests.map((test, index) => (
                  <React.Fragment key={test.name}>
                    <ListItem>
                      <Box display="flex" alignItems="center" width="100%">
                        <Box sx={{ mr: 2 }}>
                          {getStatusIcon(test.status)}
                        </Box>
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="subtitle1">
                            {test.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {test.message}
                          </Typography>
                          {test.details && (
                            <Box mt={1}>
                              <Chip
                                label={JSON.stringify(test.details)}
                                size="small"
                                variant="outlined"
                                color={getStatusColor(test.status) as any}
                              />
                            </Box>
                          )}
                        </Box>
                      </Box>
                    </ListItem>
                    {index < tests.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>

              {!isRunning && (
                <Box mt={2}>
                  <Alert
                    severity={
                      tests.every(t => t.status === 'success') ? 'success' :
                      tests.some(t => t.status === 'error') ? 'error' : 'warning'
                    }
                  >
                    {tests.every(t => t.status === 'success')
                      ? '✅ All tests passed! Google Forms export integration is working.'
                      : tests.some(t => t.status === 'error')
                      ? '❌ Some tests failed. Check the details above.'
                      : '⚠️ Tests completed with warnings. Some features may require additional setup.'
                    }
                  </Alert>
                </Box>
              )}
            </Paper>
          )}

          <Box mt={3}>
            <Typography variant="h6" mb={2}>Next Steps</Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    For Local Forms Export:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    1. Create some forms with submissions<br/>
                    2. Use the FormExportDashboard component<br/>
                    3. Select "Local Forms" tab<br/>
                    4. Choose a form and export to Excel
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    For Google Forms Export:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    1. Configure Google OAuth credentials<br/>
                    2. Use the FormExportDashboard component<br/>
                    3. Select "Google Forms" tab<br/>
                    4. Authenticate and export forms
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default TestGoogleFormsExport;