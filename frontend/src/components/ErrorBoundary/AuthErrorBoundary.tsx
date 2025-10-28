import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
import { Component, ErrorInfo, ReactNode } from "react";

import { Box, Typography, Button, Alert, AlertTitle } from "@mui/material";

import { useFirebaseAuth } from "../../context/FirebaseAuthContext";

interface Props {
  children: ReactNode;
  
fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  
error: Error | null;
  
errorInfo: ErrorInfo | null;
}

class AuthErrorBoundaryClass extends Component<Props & { authContext: any }, State> {
  constructor(props: Props & { authContext: any }) {
    super(props);
    
this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Authentication Error Boundary caught an error:', error, errorInfo);
    
this.setState({ error, errorInfo });
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

handleLogout = async () => {
    try {
      await this.props.authContext.logout();
      
this.setState({ hasError: false, error: null, errorInfo: null });
    } catch (error) {
      console.error('Failed to logout after error:', error);
    }
  };

render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            p: 3,
            textAlign: 'center',
          }}
        >
          <Alert severity="error" sx={{ mb: 3, maxWidth: 600 }}>
            <AlertTitle>Authentication Error</AlertTitle>
            Something went wrong with the authentication system.
          </Alert>

          <Typography variant="h5" gutterBottom>
            🔐 Authentication Error
          </Typography>

          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            We encountered an error while processing your authentication. This might be due to:
          </Typography>

          <Box component="ul" sx={{ textAlign: 'left', mb: 3 }}>
            <Typography component="li" variant="body2" color="text.secondary">
              Expired or invalid authentication tokens
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Network connectivity issues
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary">
              Server-side authentication problems
            </Typography>
          </Box>

          {this.state.error && (
            <Alert severity="info" sx={{ mb: 3, maxWidth: 600, textAlign: 'left' }}>
              <AlertTitle>Error Details</AlertTitle>
              <Typography variant="body2" fontFamily="monospace">
                {this.state.error.message}
              </Typography>
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              color="primary"
              onClick={this.handleRetry}
              sx={{ minWidth: 120 }}
            >
              🔄 Retry
            </Button>

            <Button
              variant="outlined"
              color="secondary"
              onClick={this.handleLogout}
              sx={{ minWidth: 120 }}
            >
              🚪 Logout & Retry
            </Button>
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 3 }}>
            If the problem persists, please contact support or try refreshing the page.
          </Typography>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Wrapper component to provide auth context
export function AuthErrorBoundary({ children, fallback }: Props) {
  const authContext = useFirebaseAuth();

return (
    <AuthErrorBoundaryClass authContext={authContext} fallback={fallback}>
      {children}
    </AuthErrorBoundaryClass>
  );
}

export default AuthErrorBoundary;
