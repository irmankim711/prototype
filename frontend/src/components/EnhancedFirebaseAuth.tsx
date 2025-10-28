import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Enhanced Firebase Authentication Component
 * Features prominent Google sign-in with enhanced UI/UX
 */

import { useState } from "react";
  
import { Box, Card, CardContent, TextField, Button, Typography, Alert, Divider, IconButton, InputAdornment, Tab, Tabs, Grid } from "@mui/material";
  
import Google from "@mui/icons-material/Google";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import Email from "@mui/icons-material/Email";
import Person from "@mui/icons-material/Person";

import { useFirebaseAuth } from "../context/FirebaseAuthContext";

interface EnhancedFirebaseAuthProps {
  onSuccess?: () => void;
  
defaultTab?: 'login' | 'register';
  
showEmailAuth?: boolean;
}

const EnhancedFirebaseAuth: React.FC<EnhancedFirebaseAuthProps> = ({
  onSuccess,
  defaultTab = 'login',
  showEmailAuth = true,
}) => {
  const { 
    loginWithEmail, 
    loginWithGoogle, 
    registerWithEmail, 
    resetPassword, 
    isLoading 
  } = useFirebaseAuth();

const [currentTab, setCurrentTab] = useState(defaultTab);
  
const [email, setEmail] = useState('');
  
const [password, setPassword] = useState('');
  
const [confirmPassword, setConfirmPassword] = useState('');
  
const [firstName, setFirstName] = useState('');
  
const [lastName, setLastName] = useState('');
  
const [showPassword, setShowPassword] = useState(false);
  
const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
const [error, setError] = useState<string | null>(null);
  
const [success, setSuccess] = useState<string | null>(null);
  
const [isResettingPassword, setIsResettingPassword] = useState(false);

const resetMessages = () => {
    setError(null);
    
setSuccess(null);
  };

const handleGoogleAuth = async () => {
    resetMessages();

try {
      await loginWithGoogle();
      
setSuccess('Google authentication successful!');
      
onSuccess?.();
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Google authentication failed';
      
setError(errorMessage);
    }
  };

const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
resetMessages();

if (!email || !password) {
      setError('Please fill in all fields');
      
return;
    }

    try {
      await loginWithEmail(email, password);
      
setSuccess('Login successful!');
      
onSuccess?.();
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      
setError(errorMessage);
    }
  };

const handleEmailRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    
resetMessages();

if (!email || !password || !confirmPassword) {
      setError('Please fill in all required fields');
      
return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      
return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      
return;
    }

    try {
      const displayName = `${firstName} ${lastName}`.trim();
      
await registerWithEmail(email, password, {
        displayName: displayName || undefined,
        firstName,
        lastName,
      });

setSuccess('Registration successful! Welcome!');
      
onSuccess?.();
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      
setError(errorMessage);
    }
  };

const handlePasswordReset = async () => {
    if (!email) {
      setError('Please enter your email address first');
      
return;
    }

    setIsResettingPassword(true);
    
resetMessages();

try {
      await resetPassword(email);
      
setSuccess('Password reset email sent! Check your inbox.');
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Password reset failed';
      
setError(errorMessage);
    } finally {
      setIsResettingPassword(false);
    }
  };

return (
    <Card sx={{ maxWidth: 450, mx: 'auto', mt: 4, borderRadius: 2, boxShadow: 3 }}>
      <CardContent sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
            Welcome
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Sign in to your account or create a new one
          </Typography>
        </Box>

        {/* Google Sign-In - Prominent Display */}
        <Button
          fullWidth
          variant="outlined"
          size="large"
          startIcon={<Google />}
          onClick={handleGoogleAuth}
          disabled={isLoading}
          sx={{
            mb: 3,
            py: 1.5,
            px: 3,
            borderColor: '#dadce0',
            color: '#3c4043',
            fontSize: '1rem',
            fontWeight: 500,
            textTransform: 'none',
            '&:hover': {
              backgroundColor: '#f8f9fa',
              borderColor: '#dadce0',
            },
            '&:disabled': {
              backgroundColor: '#f5f5f5',
            },
          }}
        >
          {isLoading ? 'Signing in with Google...' : 'Continue with Google'}
        </Button>

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

        {/* Email Authentication (Optional) */}
        {showEmailAuth && (
          <>
            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                or
              </Typography>
            </Divider>

            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
              <Tabs 
                value={currentTab} 
                onChange={(_, newValue) => {
                  setCurrentTab(newValue);
                  
resetMessages();
                }}
                sx={{ minHeight: 40 }}
              >
                <Tab 
                  label="Sign In" 
                  value="login" 
                  icon={<Email />}
                  iconPosition="start"
                  sx={{ textTransform: 'none', minHeight: 40 }}
                />
                <Tab 
                  label="Sign Up" 
                  value="register"
                  icon={<Person />}
                  iconPosition="start"
                  sx={{ textTransform: 'none', minHeight: 40 }}
                />
              </Tabs>
            </Box>

            {/* Login Form */}
            {currentTab === 'login' && (
              <Box component="form" onSubmit={handleEmailLogin}>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e: any) => setEmail(e.target.value)}
                  margin="normal"
                  required
                  autoComplete="email"
                  size="medium"
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
                  size="medium"
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
                  {isLoading ? 'Signing In...' : 'Sign In with Email'}
                </Button>

                <Box sx={{ textAlign: 'center' }}>
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
              </Box>
            )}

            {/* Register Form */}
            {currentTab === 'register' && (
              <Box component="form" onSubmit={handleEmailRegister}>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="First Name"
                      value={firstName}
                      onChange={(e: any) => setFirstName(e.target.value)}
                      margin="normal"
                      autoComplete="given-name"
                      size="medium"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      label="Last Name"
                      value={lastName}
                      onChange={(e: any) => setLastName(e.target.value)}
                      margin="normal"
                      autoComplete="family-name"
                      size="medium"
                    />
                  </Grid>
                </Grid>

                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e: any) => setEmail(e.target.value)}
                  margin="normal"
                  required
                  autoComplete="email"
                  size="medium"
                />
                
                <TextField
                  fullWidth
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e: any) => setPassword(e.target.value)}
                  margin="normal"
                  required
                  autoComplete="new-password"
                  size="medium"
                  helperText="Password must be at least 6 characters long"
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

                <TextField
                  fullWidth
                  label="Confirm Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e: any) => setConfirmPassword(e.target.value)}
                  margin="normal"
                  required
                  autoComplete="new-password"
                  size="medium"
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          edge="end"
                        >
                          {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
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
                  {isLoading ? 'Creating Account...' : 'Create Account'}
                </Button>
              </Box>
            )}
          </>
        )}

        {/* Privacy Notice */}
        <Typography 
          variant="caption" 
          color="text.secondary" 
          sx={{ display: 'block', textAlign: 'center', mt: 2 }}
        >
          By continuing, you agree to our Terms of Service and Privacy Policy
        </Typography>
      </CardContent>
    </Card>
  );
};

export default EnhancedFirebaseAuth;
