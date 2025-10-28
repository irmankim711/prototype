         import React from 'react';

import { Box, Button, Alert, AlertTitle, Typography, Chip } from "@mui/material";

import { useFirebaseAuth } from "../../context/FirebaseAuthContext";

import { environmentConfig } from "../../config/environment";

export function DevAuthBypass() {
  const { isDevelopmentBypass, enableDevelopmentBypass, disableDevelopmentBypass } = useFirebaseAuth();

  // Only show in development environment
  if (!environmentConfig.isDevelopment || !environmentConfig.features.authBypass) {
    return null;
  }

  return (
    <Box sx={{ p: 2, border: '1px dashed #ccc', borderRadius: 1, mb: 2 }}>
      <Alert severity="info" sx={{ mb: 2 }}>
        <AlertTitle>Development Mode</AlertTitle>
        Authentication bypass is available for development purposes.
      </Alert>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Status:
        </Typography>
        <Chip
          label={isDevelopmentBypass ? "BYPASS ACTIVE" : "NORMAL AUTH"}
          color={isDevelopmentBypass ? "success" : "default"}
          size="small"
        />
      </Box>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {!isDevelopmentBypass ? (
          <Button
            variant="contained"
            color="warning"
            size="small"
            onClick={enableDevelopmentBypass}
            startIcon={<span>🔓</span>}
          >
            Enable Dev Bypass
          </Button>
        ) : (
          <Button
            variant="outlined"
            color="warning"
            size="small"
            onClick={disableDevelopmentBypass}
            startIcon={<span>🔒</span>}
          >
            Disable Dev Bypass
          </Button>
        )}

        {isDevelopmentBypass && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Dev User:
            </Typography>
            <Chip
              label={environmentConfig.devAuth.userEmail}
              size="small"
              variant="outlined"
            />
            <Chip
              label={environmentConfig.devAuth.userRole}
              size="small"
              variant="outlined"
              color="primary"
            />
          </Box>
        )}
      </Box>

      {isDevelopmentBypass && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          <strong>Warning:</strong> Development bypass is active. This bypasses all authentication checks and should only be used in development environments.
        </Alert>
      )}
    </Box>
  );
}

export default DevAuthBypass;
