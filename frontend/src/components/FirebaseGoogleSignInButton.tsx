import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Firebase Google Sign-In Button
 * Modern Google OAuth button using Firebase Authentication
 */

import { useState } from "react";

import { Button, CircularProgress, Box } from "@mui/material";

import Google from "@mui/icons-material/Google";

import { useFirebaseAuth } from "../context/FirebaseAuthContext";

interface FirebaseGoogleSignInButtonProps {
  onSuccess?: (user: React.ChangeEvent<HTMLInputElement>) => void;
  
onError?: (error: string) => void;
  
variant?: 'contained' | 'outlined' | 'text';
  
size?: 'small' | 'medium' | 'large';
  
fullWidth?: boolean;
  
disabled?: boolean;
  
text?: string;
}

const FirebaseGoogleSignInButton: React.FC<FirebaseGoogleSignInButtonProps> = ({
  onSuccess,
  onError,
  variant = 'outlined',
  size = 'large',
  fullWidth = false,
  disabled = false,
  text = 'Continue with Google',
}) => {
  const { loginWithGoogle, isLoading } = useFirebaseAuth();
  
const [isSigningIn, setIsSigningIn] = useState(false);

const handleGoogleSignIn = async () => {
    setIsSigningIn(true);

try {
      await loginWithGoogle();
      
onSuccess?.(true);
    } catch (error: any) {
      const errorMessage = error.message || 'Google sign-in failed';
      
console.error('Google sign-in error:', error);
      
onError?.(errorMessage);
    } finally {
      setIsSigningIn(false);
    }
  };

const isButtonDisabled = disabled || isLoading || isSigningIn;

return (
    <Button
      variant={variant}
      size={size}
      fullWidth={fullWidth}
      disabled={isButtonDisabled}
      onClick={handleGoogleSignIn}
      startIcon={
        isSigningIn ? (
          <CircularProgress size={20} />
        ) : (
          <Google />
        )
      }
      sx={{
        py: size === 'large' ? 1.5 : size === 'medium' ? 1.2 : 1,
        px: size === 'large' ? 3 : size === 'medium' ? 2.5 : 2,
        borderColor: variant === 'outlined' ? '#dadce0' : undefined,
        color: variant === 'outlined' ? '#3c4043' : undefined,
        fontSize: size === 'large' ? '1rem' : size === 'medium' ? '0.9rem' : '0.8rem',
        fontWeight: 500,
        textTransform: 'none',
        '&:hover': {
          backgroundColor: variant === 'outlined' ? '#f8f9fa' : undefined,
          borderColor: variant === 'outlined' ? '#dadce0' : undefined,
        },
        '&:disabled': {
          backgroundColor: '#f5f5f5',
          color: '#9aa0a6',
        },
      }}
    >
      {isSigningIn ? 'Signing in...' : text}
    </Button>
  );
};

export default FirebaseGoogleSignInButton;
