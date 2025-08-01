import React from "react";
import { Box, Typography, Card, CardContent, Chip } from "@mui/material";

const GoogleOAuthDebug: React.FC = () => {
  const checkGoogleAPI = () => {
    return (
      typeof window.google !== "undefined" &&
      window.google?.accounts?.id !== undefined
    );
  };

  const getClientId = () => {
    const scriptTag = document.querySelector("[data-client_id]");
    return scriptTag?.getAttribute("data-client_id") || "Not found";
  };

  const checkDOMElements = () => {
    const onloadDiv = document.getElementById("g_id_onload");
    const scriptTag = document.querySelector('script[src*="gsi/client"]');

    return {
      onloadDiv: !!onloadDiv,
      scriptTag: !!scriptTag,
    };
  };

  const elements = checkDOMElements();

  return (
    <Card sx={{ m: 2, maxWidth: 600 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          🔧 Google OAuth Debug Info
        </Typography>

        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="body2">Google API Loaded:</Typography>
            <Chip
              label={checkGoogleAPI() ? "YES" : "NO"}
              color={checkGoogleAPI() ? "success" : "error"}
              size="small"
            />
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="body2">Client ID:</Typography>
            <Typography
              variant="body2"
              sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}
            >
              {getClientId()}
            </Typography>
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="body2">GSI Script Tag:</Typography>
            <Chip
              label={elements.scriptTag ? "FOUND" : "MISSING"}
              color={elements.scriptTag ? "success" : "error"}
              size="small"
            />
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="body2">Onload Div:</Typography>
            <Chip
              label={elements.onloadDiv ? "FOUND" : "MISSING"}
              color={elements.onloadDiv ? "success" : "error"}
              size="small"
            />
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Typography variant="body2">Current Origin:</Typography>
            <Typography
              variant="body2"
              sx={{ fontFamily: "monospace", fontSize: "0.8rem" }}
            >
              {window.location.origin}
            </Typography>
          </Box>
        </Box>

        <Typography
          variant="caption"
          color="textSecondary"
          sx={{ mt: 2, display: "block" }}
        >
          ✅ All items should be green/found for Google Sign-In to work properly
        </Typography>
      </CardContent>
    </Card>
  );
};

export default GoogleOAuthDebug;
