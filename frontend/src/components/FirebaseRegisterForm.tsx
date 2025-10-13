import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Firebase Registration Form Component
 * Registration form with Firebase authentication
 */

import { useState } from "react";
  
import { Box, Card, CardContent, TextField, Button, Typography, Alert, Divider, IconButton, InputAdornment } from "@mui/material";
  
import { Google, Visibility, VisibilityOff } from "@mui/icons-material";

import { useFirebaseAuth } from "../context/FirebaseAuthContext";

interface FirebaseRegisterFormProps {
  onSuccess?: () => void;
  
onLoginClick?: () => void;
  
showGoogleRegister?: boolean;
  
showLoginLink?: boolean;
}

const FirebaseRegisterForm: React.FC<FirebaseRegisterFormProps> = ({
  onSuccess,
  onLoginClick,
  showGoogleRegister = true,
  showLoginLink = true,
}) => {
  const { registerWithEmail, loginWithGoogle, isLoading } = useFirebaseAuth();

const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
  });
  
const [showPassword, setShowPassword] = useState(false);
  
const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
const [error, setError] = useState<string | null>(null);
  
const [success, setSuccess] = useState<string | null>(null);

const handleInputChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value
    }));
  };

const validateForm = () => {
    if (!formData.email || !formData.password || !formData.confirmPassword) {
      setError('Please fill in all required fields');
      
return false;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      
return false;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      
return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address');
      
return false;
    }

    return true;
  };

const handleEmailRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    
setError(null);
    
setSuccess(null);

if (!validateForm()) {
      return;
    }

    try {
      const displayName = `${formData.firstName} ${formData.lastName}`.trim();

await registerWithEmail(formData.email, formData.password, {
        displayName: displayName || undefined,
        firstName: formData.firstName,
        lastName: formData.lastName,
      });

setSuccess('Registration successful! Welcome!');
      
onSuccess?.();
    } catch (error: any) {
      setError(error.message || 'Registration failed');
    }
  };

const handleGoogleRegister = async () => {
    setError(null);
    
setSuccess(null);

try {
      await loginWithGoogle();
      
setSuccess('Google registration successful!');
      
onSuccess?.();
    } catch (error: any) {
      setError(error.message || 'Google registration failed');
    }
  };

return (
    <Card sx={{ maxWidth: 400, mx: 'auto', mt: 4 }}>
      <CardContent sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Sign Up
        </Typography>
        
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
          Create your account to get started
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

        {/* Google Registration Button */}
        {showGoogleRegister && (
          <>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Google />}
              onClick={handleGoogleRegister}
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

        {/* Email/Password Registration Form */}
        <Box component="form" onSubmit={handleEmailRegister} sx={{ width: '100%' }}>
          {/* Name Fields */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              label="First Name"
              value={formData.firstName}
              onChange={handleInputChange('firstName')}
              margin="normal"
              autoComplete="given-name"
            />
            <TextField
              fullWidth
              label="Last Name"
              value={formData.lastName}
              onChange={handleInputChange('lastName')}
              margin="normal"
              autoComplete="family-name"
            />
          </Box>

          <TextField
            fullWidth
            label="Email"
            type="email"
            value={formData.email}
            onChange={handleInputChange('email')}
            margin="normal"
            required
            autoComplete="email"
          />
          
          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={formData.password}
            onChange={handleInputChange('password')}
            margin="normal"
            required
            autoComplete="new-password"
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
            value={formData.confirmPassword}
            onChange={handleInputChange('confirmPassword')}
            margin="normal"
            required
            autoComplete="new-password"
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

        {/* Login Link */}
        {showLoginLink && (
          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Already have an account?{' '}
              <Button
                variant="text"
                size="small"
                onClick={onLoginClick}
                sx={{ textTransform: 'none', p: 0, minWidth: 'auto' }}
              >
                Sign in
              </Button>
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default FirebaseRegisterForm;
