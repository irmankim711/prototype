/**
 * Report Error Boundary Component
 * Catches and handles errors in report generation and display
 */

import React from 'react';
  
import { Box, Typography, Button, Alert, Paper, Accordion, AccordionSummary, AccordionDetails } from "@mui/material";
  
import { Error, Refresh, ExpandMore, BugReport } from "@mui/icons-material";

interface ReportErrorBoundaryState {
  hasError: boolean;
  
error: Error | null;
  
errorInfo: React.ErrorInfo | null;
}

interface ReportErrorBoundaryProps {
  children: React.ReactNode;
  
onRetry?: () => void;
  
onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  
fallbackComponent?: React.ComponentType<{ error: Error; 
retry: () => void }>;
}

class ReportErrorBoundary extends React.Component<
  ReportErrorBoundaryProps,
  ReportErrorBoundaryState
> {
  constructor(props: ReportErrorBoundaryProps) {
    super(props);
    
this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ReportErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Minimal logging to prevent console flooding
    if (import.meta.env.DEV) {
      console.error('Report Error Boundary caught an error:', error.message);
    }

    this.setState({
      error,
      errorInfo,
    });

    // Call onError callback if provided (with error handling)
    if (this.props.onError) {
      try {
        this.props.onError(error, errorInfo);
      } catch (callbackError) {
        // Silent fail to prevent cascading errors
        if (import.meta.env.DEV) {
          console.error('Error in onError callback:', callbackError);
        }
      }
    }
  }

  handleRetry = () => {
    console.log('🔄 Attempting to recover from error...');

this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });

    // Call onRetry callback if provided
    if (this.props.onRetry) {
      this.props.onRetry();
    }
  };

getErrorType = (error: Error): string => {
    const message = error.message.toLowerCase();
    
const stack = error.stack?.toLowerCase() || '';

if (message.includes('network') || message.includes('fetch')) return 'Network Error';
    
if (message.includes('api') || message.includes('axios')) return 'API Error';
    
if (message.includes('authentication') || message.includes('unauthorized')) return 'Authentication Error';
    
if (message.includes('validation') || message.includes('invalid')) return 'Data Validation Error';
    
if (message.includes('chart') || message.includes('visualization')) return 'Chart Generation Error';
    
if (message.includes('report') || message.includes('generation')) return 'Report Generation Error';
    
if (message.includes('cannot read') || message.includes('undefined')) return 'Data Access Error';
    
if (message.includes('render') || stack.includes('render')) return 'Rendering Error';
    
if (message.includes('lazy') || message.includes('suspense')) return 'Component Loading Error';
    
return 'Application Error';
  };

getErrorSeverity = (error: Error): 'error' | 'warning' => {
    if (error.message.includes('Network') || error.message.includes('API')) {
      return 'warning';
    }
    return 'error';
  };

getUserFriendlyMessage = (error: Error): string => {
    const message = error.message.toLowerCase();
    
const stack = error.stack?.toLowerCase() || '';

if (message.includes('network') || message.includes('connection') || message.includes('fetch')) {
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    }
    
    if (message.includes('authentication') || message.includes('unauthorized')) {
      return 'Your session has expired. Please log in again to continue.';
    }
    
    if (message.includes('validation') || message.includes('invalid data')) {
      return 'The data format is not valid. Please check your input and try again.';
    }
    
    if (message.includes('chart') || message.includes('visualization')) {
      return 'There was a problem generating the chart. Please verify your data and chart configuration.';
    }
    
    if (message.includes('report') || message.includes('generation')) {
      return 'Report generation failed. Please try again or contact support if the problem persists.';
    }
    
    if (message.includes('cannot read') || message.includes('undefined') || message.includes('null')) {
      return 'Some required data is missing or not loaded yet. Please wait for the data to load or refresh the page.';
    }
    
    if (message.includes('render') || stack.includes('render')) {
      return 'There was a problem displaying the component. This might be due to invalid data or a temporary issue.';
    }
    
    if (message.includes('lazy') || message.includes('suspense') || message.includes('chunk')) {
      return 'Failed to load a component. Please refresh the page to try again.';
    }
    
    return 'An unexpected error occurred. Please try again or refresh the page.';
  };

render() {
    if (this.state.hasError && this.state.error) {
      // Use custom fallback component if provided
      if (this.props.fallbackComponent) {
        const FallbackComponent = this.props.fallbackComponent;
        
return <FallbackComponent error={this.state.error} retry={this.handleRetry} />;
      }

      const errorType = this.getErrorType(this.state.error);
      
const severity = this.getErrorSeverity(this.state.error);
      
const userMessage = this.getUserFriendlyMessage(this.state.error);

return (
        <Box
          sx={{
            p: 3,
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#f8fafc',
          }}
        >
          <Paper
            sx={{
              p: 4,
              maxWidth: 600,
              width: '100%',
              textAlign: 'center',
              borderRadius: 3,
            }}
          >
            <Error 
              sx={{ 
                fontSize: 64, 
                color: severity === 'error' ? 'error.main' : 'warning.main',
                mb: 2 
              }} 
            />
            
            <Typography variant="h5" fontWeight="semibold" gutterBottom>
              {errorType}
            </Typography>
            
            <Typography variant="body1" color="text.secondary" mb={3}>
              {userMessage}
            </Typography>

            <Alert severity={severity} sx={{ mb: 3, textAlign: 'left' }}>
              {this.state.error.message}
            </Alert>

            <Box display="flex" gap={2} justifyContent="center" mb={3}>
              <Button
                variant="contained"
                onClick={this.handleRetry}
                startIcon={<Refresh />}
              >
                Try Again
              </Button>
              
              <Button
                variant="outlined"
                onClick={() => window.location.reload()}
              >
                Refresh Page
              </Button>
            </Box>

            {/* Error Details for Debugging */}
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Box display="flex" alignItems="center" gap={1}>
                  <BugReport fontSize="small" />
                  <Typography variant="body2">
                    Technical Details (for debugging)
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box textAlign="left">
                  <Typography variant="caption" component="div" gutterBottom>
                    <strong>Error:</strong>
                  </Typography>
                  <Typography variant="body2" fontFamily="monospace" mb={2}>
                    {this.state.error.message}
                  </Typography>
                  
                  {this.state.error.stack && (
                    <>
                      <Typography variant="caption" component="div" gutterBottom>
                        <strong>Stack Trace:</strong>
                      </Typography>
                      <Typography 
                        variant="body2" 
                        fontFamily="monospace" 
                        sx={{ 
                          whiteSpace: 'pre-wrap',
                          fontSize: '0.7rem',
                          backgroundColor: '#f5f5f5',
                          p: 1,
                          borderRadius: 1,
                          overflow: 'auto',
                          maxHeight: 200,
                        }}
                      >
                        {this.state.error.stack}
                      </Typography>
                    </>
                  )}
                </Box>
              </AccordionDetails>
            </Accordion>
          </Paper>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ReportErrorBoundary;
