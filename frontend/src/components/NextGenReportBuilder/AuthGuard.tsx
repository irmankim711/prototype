import React from 'react';
/**
 * Authentication Guard for NextGen Report Builder
 * Ensures users are authenticated before accessing protected features
 * Updated to use unified authentication approach checking both Firebase and JWT tokens
 */

import { useEffect, useState } from "react";

import { useNavigate } from "react-router-dom";

import { Box, Paper, Typography, Button, CircularProgress, Alert, AlertTitle } from "@mui/material";

import { Lock, Login, Refresh } from "@mui/icons-material";

import { useFirebaseAuth } from "../../context/FirebaseAuthContext";
import { useAuth as useJWTAuth } from "../../context/AuthContext";

interface AuthGuardProps {
  children: React.ReactNode;
  
fallback?: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children, fallback }) => {
  // Use both authentication contexts to support both Firebase and JWT authentication
  const firebaseAuth = useFirebaseAuth();
  const jwtAuth = useJWTAuth();

  const navigate = useNavigate();
  const [showRetry, setShowRetry] = useState(false);

  // Determine if user is authenticated using either Firebase or JWT
  // Priority: Check JWT first (since landing page uses JWT), then Firebase as fallback
  const isAuthenticated = jwtAuth.isAuthenticated || firebaseAuth.isAuthenticated;
  const isLoading = jwtAuth.isLoading && firebaseAuth.isLoading; // Only show loading if BOTH are loading
  const currentUser = jwtAuth.user || firebaseAuth.user;

  // Debug logging to help troubleshoot authentication issues
  useEffect(() => {
    console.log('🔍 [AuthGuard] Authentication Status:', {
      firebaseAuth: {
        isAuthenticated: firebaseAuth.isAuthenticated,
        isLoading: firebaseAuth.isLoading,
        user: firebaseAuth.user?.email,
        firebaseUser: firebaseAuth.firebaseUser?.email
      },
      jwtAuth: {
        isAuthenticated: jwtAuth.isAuthenticated,
        isLoading: jwtAuth.isLoading,
        user: jwtAuth.user?.email,
        accessToken: jwtAuth.accessToken ? 'Present' : 'Missing'
      },
      combined: {
        isAuthenticated,
        isLoading,
        currentUser: currentUser?.email
      }
    });
  }, [firebaseAuth.isAuthenticated, jwtAuth.isAuthenticated, firebaseAuth.isLoading, jwtAuth.isLoading]);

  useEffect(() => {
    // Check authentication after initial loading is complete
    // We need to wait for at least one auth system to finish loading
    const anyAuthLoaded = !jwtAuth.isLoading || !firebaseAuth.isLoading;

    if (anyAuthLoaded && !isAuthenticated) {
      console.log('⚠️ [AuthGuard] User not authenticated, showing retry option');
      setShowRetry(true);
    } else if (isAuthenticated) {
      console.log('✅ [AuthGuard] User authenticated, access granted');
      setShowRetry(false);
    }
  }, [jwtAuth.isLoading, firebaseAuth.isLoading, isAuthenticated]);

const handleLogin = () => {
    navigate('/'); // Navigate to landing page for authentication
  };

const handleRetry = () => {
    window.location.reload();
  };

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '400px',
          p: 3
        }}
      >
        <CircularProgress size={48} sx={{ mb: 2 }} />
        <Typography variant="h6" color="text.secondary">
          Verifying authentication...
        </Typography>
      </Box>
    );
  }

  // Show authentication required message
  if (!isAuthenticated) {
    return fallback || (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '400px',
          p: 3
        }}
      >
        <Paper
          elevation={2}
          sx={{
            p: 4,
            maxWidth: 500,
            textAlign: 'center',
            borderRadius: 2
          }}
        >
          <Lock
            sx={{
              fontSize: 64,
              color: 'warning.main',
              mb: 2
            }}
          />
          
          <Typography variant="h5" component="h2" gutterBottom>
            Authentication Required
          </Typography>
          
          <Typography variant="body1" color="text.secondary" paragraph>
            You must be logged in to access the NextGen Report Builder. 
            Please sign in to continue.
          </Typography>

          <Alert severity="info" sx={{ mb: 3, textAlign: 'left' }}>
            <AlertTitle>Why is this required?</AlertTitle>
            The NextGen Report Builder connects to secure data sources and 
            requires valid authentication to protect your data and ensure 
            proper access controls.
          </Alert>

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              startIcon={<Login />}
              onClick={handleLogin}
              size="large"
            >
              Sign In
            </Button>
            
            {showRetry && (
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={handleRetry}
                size="large"
              >
                Retry
              </Button>
            )}
          </Box>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
            User Status: {currentUser ? `Authenticated (${currentUser.email})` : 'Not Authenticated'}
          </Typography>

          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Auth Methods: Firebase: {firebaseAuth.isAuthenticated ? '✅' : '❌'}, JWT: {jwtAuth.isAuthenticated ? '✅' : '❌'}
          </Typography>
        </Paper>
      </Box>
    );
  }

  // User is authenticated, render children
  return <>{children}</>;
};

export default AuthGuard;
