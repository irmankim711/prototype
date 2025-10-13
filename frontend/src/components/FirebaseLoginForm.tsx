import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Firebase Login Form Component
 * Replaces the existing login form with Firebase authentication
 */

import { useState } from "react";
  
import { Box, Card, CardContent, TextField, Button, Typography, Alert, Divider, IconButton, InputAdornment } from "@mui/material";
  
import { Google, Visibility, VisibilityOff } from "@mui/icons-material";

import { useFirebaseAuth } from "../context/FirebaseAuthContext";

interface FirebaseLoginFormProps {
  onSuccess?: () => void;
  
onRegisterClick?: () => void;
  
showGoogleLogin?: boolean;
  
showRegisterLink?: boolean;
}

const FirebaseLoginForm: React.FC<FirebaseLoginFormProps> = ({
  onSuccess,
  onRegisterClick,
  showGoogleLogin = true,
  showRegisterLink = true,
}) => {
  const { loginWithEmail, loginWithGoogle, resetPassword, isLoading } = useFirebaseAuth();

const [email, setEmail] = useState('');
  
const [password, setPassword] = useState('');
  
const [showPassword, setShowPassword] = useState(false);
  
const [error, setError] = useState<string | null>(null);
  
const [success, setSuccess] = useState<string | null>(null);
  
const [isResettingPassword, setIsResettingPassword] = useState(false);

const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
setError(null);
    
setSuccess(null);

if (!email || !password) {
      setError('Please fill in all fields');
      
return;
    }

    try {
      await loginWithEmail(email, password);
      
setSuccess('Login successful!');
      
onSuccess?.();
    } catch (error: any) {
      setError(error.message || 'Login failed');
    }
  };

const handleGoogleLogin = async () => {
    setError(null);
    
setSuccess(null);

try {
      await loginWithGoogle();
      
setSuccess('Google login successful!');
      
onSuccess?.();
    } catch (error: any) {
      setError(error.message || 'Google login failed');
    }
  };

const handlePasswordReset = async () => {
    if (!email) {
      setError('Please enter your email address first');
      
return;
    }

    setIsResettingPassword(true);
    
setError(null);

try {
      await resetPassword(email);
      
setSuccess('Password reset email sent! Check your inbox.');
    } catch (error: any) {
      setError(error.message || 'Password reset failed');
    } finally {
      setIsResettingPassword(false);
    }
  };

return (
    <Card sx={{ maxWidth: 400, mx: 'auto', mt: 4 }}>
      <CardContent sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Sign In
        </Typography>
        
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
          Sign in to access your account
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        {/* Google Login Button */}
        {showGoogleLogin && (
          <>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Google />}
              onClick={handleGoogleLogin}
              disabled={isLoading}
              sx={{
                mb: 2,
                py: 1.5,
                borderColor: '#dadce0',
                color: '#3c4043',
                '&:hover': {
                  backgroundColor: '#f8f9fa',
                  borderColor: '#dadce0',
                },
              }}
            >
              Continue with Google
            </Button>

            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                or
              </Typography>
            </Divider>
          </>
        )}

        {/* Email/Password Form */}
        <Box component="form" onSubmit={handleEmailLogin} sx={{ width: '100%' }}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={email}
            onChange={(e: any) => setEmail(e.target.value)}
            margin="normal"
            required
            autoComplete="email"
            autoFocus
          />
          
          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e: any) => setPassword(e.target.value)}
            margin="normal"
            required
            autoComplete="current-password"
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={isLoading}
            sx={{ mt: 3, mb: 2, py: 1.5 }}
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </Button>
        </Box>

        {/* Forgot Password Link */}
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Button
            variant="text"
            size="small"
            onClick={handlePasswordReset}
            disabled={isResettingPassword || !email}
            sx={{ textTransform: 'none' }}
          >
            {isResettingPassword ? 'Sending...' : 'Forgot password?'}
          </Button>
        </Box>

        {/* Register Link */}
        {showRegisterLink && (
          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{' '}
              <Button
                variant="text"
                size="small"
                onClick={onRegisterClick}
                sx={{ textTransform: 'none', p: 0, minWidth: 'auto' }}
              >
                Sign up
              </Button>
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default FirebaseLoginForm;
