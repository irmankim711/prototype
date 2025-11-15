/**
 * Firebase Phone Authentication Component
 * Provides phone number login with SMS OTP verification using Firebase Authentication
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  InputAdornment,
} from '@mui/material';
import { Phone, Lock } from '@mui/icons-material';
import {
  RecaptchaVerifier,
  signInWithPhoneNumber,
  ConfirmationResult,
  PhoneAuthProvider,
  signInWithCredential,
} from 'firebase/auth';
import { auth } from '../config/firebase';

interface FirebasePhoneAuthProps {
  onSuccess?: (user: any) => void;
  onError?: (error: string) => void;
  buttonText?: string;
  containerStyle?: React.CSSProperties;
}

export const FirebasePhoneAuth: React.FC<FirebasePhoneAuthProps> = ({
  onSuccess,
  onError,
  buttonText = 'Sign In with Phone',
  containerStyle,
}) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null);

  const recaptchaContainerRef = useRef<HTMLDivElement>(null);
  const recaptchaVerifierRef = useRef<RecaptchaVerifier | null>(null);

  // Initialize reCAPTCHA on component mount
  useEffect(() => {
    if (!recaptchaContainerRef.current) return;

    try {
      // Create reCAPTCHA verifier
      recaptchaVerifierRef.current = new RecaptchaVerifier(
        auth,
        recaptchaContainerRef.current,
        {
          size: 'invisible',
          callback: () => {
            console.log('reCAPTCHA solved successfully');
          },
          'expired-callback': () => {
            setError('reCAPTCHA expired. Please try again.');
            setLoading(false);
          },
        }
      );

      console.log('✅ reCAPTCHA verifier initialized');
    } catch (err: any) {
      console.error('❌ Failed to initialize reCAPTCHA:', err);
      setError('Failed to initialize phone authentication. Please refresh the page.');
    }

    // Cleanup on unmount
    return () => {
      if (recaptchaVerifierRef.current) {
        recaptchaVerifierRef.current.clear();
        recaptchaVerifierRef.current = null;
      }
    };
  }, []);

  const formatPhoneNumber = (phone: string): string => {
    // Remove all non-numeric characters
    const cleaned = phone.replace(/\D/g, '');

    // If doesn't start with +, assume Malaysian number and add +60
    if (!phone.startsWith('+')) {
      // Remove leading 0 if present (Malaysian mobile numbers)
      const withoutLeadingZero = cleaned.startsWith('0') ? cleaned.substring(1) : cleaned;
      return `+60${withoutLeadingZero}`;
    }

    return `+${cleaned}`;
  };

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Validate phone number
      if (!phoneNumber) {
        throw new Error('Please enter your phone number');
      }

      const formattedPhone = formatPhoneNumber(phoneNumber);
      console.log('📱 Sending OTP to:', formattedPhone);

      // Ensure reCAPTCHA is initialized
      if (!recaptchaVerifierRef.current) {
        throw new Error('reCAPTCHA not initialized. Please refresh the page.');
      }

      // Send OTP via Firebase
      const confirmation = await signInWithPhoneNumber(
        auth,
        formattedPhone,
        recaptchaVerifierRef.current
      );

      setConfirmationResult(confirmation);
      setOtpSent(true);
      setSuccess('OTP sent successfully! Please check your phone.');
      console.log('✅ OTP sent successfully');
    } catch (err: any) {
      console.error('❌ Failed to send OTP:', err);

      let errorMessage = 'Failed to send OTP. Please try again.';

      if (err.code === 'auth/invalid-phone-number') {
        errorMessage = 'Invalid phone number format. Please enter a valid phone number.';
      } else if (err.code === 'auth/too-many-requests') {
        errorMessage = 'Too many requests. Please wait a few minutes and try again.';
      } else if (err.code === 'auth/quota-exceeded') {
        errorMessage = 'SMS quota exceeded. Please try again later or contact support.';
      } else if (err.code === 'auth/captcha-check-failed') {
        errorMessage = 'reCAPTCHA verification failed. Please refresh the page and try again.';
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      if (onError) onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Validate OTP
      if (!otp || otp.length !== 6) {
        throw new Error('Please enter the 6-digit OTP code');
      }

      if (!confirmationResult) {
        throw new Error('No confirmation result. Please request a new OTP.');
      }

      console.log('🔍 Verifying OTP...');

      // Verify OTP with Firebase
      const userCredential = await confirmationResult.confirm(otp);
      const user = userCredential.user;

      console.log('✅ Phone authentication successful:', user.uid);
      setSuccess('Phone verified successfully!');

      // Get Firebase ID token for backend sync
      const idToken = await user.getIdToken();
      localStorage.setItem('firebaseToken', idToken);

      // Call success callback
      if (onSuccess) {
        onSuccess(user);
      }
    } catch (err: any) {
      console.error('❌ Failed to verify OTP:', err);

      let errorMessage = 'Invalid OTP code. Please try again.';

      if (err.code === 'auth/invalid-verification-code') {
        errorMessage = 'Invalid OTP code. Please check and try again.';
      } else if (err.code === 'auth/code-expired') {
        errorMessage = 'OTP code has expired. Please request a new one.';
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      if (onError) onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleTryDifferentNumber = () => {
    setPhoneNumber('');
    setOtp('');
    setOtpSent(false);
    setError('');
    setSuccess('');
    setConfirmationResult(null);
  };

  return (
    <Box sx={{ width: '100%', ...containerStyle }}>
      {/* reCAPTCHA container (invisible) */}
      <div ref={recaptchaContainerRef} id="recaptcha-container" />

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Success Alert */}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {!otpSent ? (
        // Phone Number Entry Form
        <Box component="form" onSubmit={handleSendOtp}>
          <TextField
            fullWidth
            label="Phone Number"
            placeholder="+60123456789 or 0123456789"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            disabled={loading}
            required
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Phone />
                </InputAdornment>
              ),
            }}
            helperText="Enter your phone number with country code (e.g., +60123456789) or Malaysian format (e.g., 0123456789)"
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            disabled={loading || !phoneNumber}
            sx={{
              py: 1.5,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5568d3 0%, #63408a 100%)',
              },
            }}
          >
            {loading ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1, color: 'white' }} />
                Sending OTP...
              </>
            ) : (
              buttonText
            )}
          </Button>
        </Box>
      ) : (
        // OTP Verification Form
        <Box component="form" onSubmit={handleVerifyOtp}>
          <Typography variant="body2" sx={{ mb: 2, color: 'text.secondary' }}>
            Enter the 6-digit code sent to {phoneNumber}
          </Typography>

          <TextField
            fullWidth
            label="OTP Code"
            placeholder="123456"
            value={otp}
            onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
            disabled={loading}
            required
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Lock />
                </InputAdornment>
              ),
            }}
            inputProps={{
              maxLength: 6,
              pattern: '[0-9]{6}',
              inputMode: 'numeric',
            }}
            helperText="Enter the 6-digit code from your SMS"
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            disabled={loading || otp.length !== 6}
            sx={{
              py: 1.5,
              mb: 1,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5568d3 0%, #63408a 100%)',
              },
            }}
          >
            {loading ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1, color: 'white' }} />
                Verifying...
              </>
            ) : (
              'Verify OTP'
            )}
          </Button>

          <Button
            variant="text"
            fullWidth
            onClick={handleTryDifferentNumber}
            disabled={loading}
            sx={{ color: 'primary.main' }}
          >
            Try Different Number
          </Button>
        </Box>
      )}

      {/* Firebase Phone Auth Info */}
      <Typography variant="caption" sx={{ display: 'block', mt: 2, color: 'text.secondary', textAlign: 'center' }}>
        Secured by Firebase Phone Authentication
      </Typography>
    </Box>
  );
};

export default FirebasePhoneAuth;
