import React, { useState } from "react";
import {
  Box,
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
  InputAdornment,
  alpha,
  useTheme,
  CircularProgress,
  Fade,
  styled,
  keyframes,
} from "@mui/material";
import { VpnKey, Login, Security, CheckCircle } from "@mui/icons-material";
import axios from "axios";
import PublicFormViewer from "../PublicFormViewer";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

// Styled components with modern design
const float = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
`;

const StyledCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(145deg, ${alpha(
    theme.palette.common.white,
    0.9
  )}, ${alpha(theme.palette.common.white, 0.7)})`,
  backdropFilter: "blur(20px)",
  border: `1px solid ${alpha(theme.palette.common.white, 0.2)}`,
  borderRadius: "24px",
  boxShadow: `
    0 8px 32px ${alpha(theme.palette.common.black, 0.1)},
    0 2px 8px ${alpha(theme.palette.common.black, 0.05)}
  `,
  overflow: "visible",
  position: "relative",
  "&::before": {
    content: '""',
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    borderRadius: "24px",
    padding: "2px",
    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
    mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
    maskComposite: "exclude",
  },
}));

const FloatingIcon = styled(Box)(() => ({
  animation: `${float} 3s ease-in-out infinite`,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  margin: "0 auto 24px",
  width: "80px",
  height: "80px",
  borderRadius: "50%",
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  fontSize: "2rem",
}));

const PublicFormAccess: React.FC = () => {
  const [accessCode, setAccessCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const theme = useTheme();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!accessCode.trim()) {
      setError("Please enter an access code");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/forms/public/verify-code`,
        {
          code: accessCode.trim().toUpperCase(),
        }
      );

      setSuccess(true);
      setAccessToken(response.data.access_token);

      // Wait a moment to show success animation
      setTimeout(() => {
        setIsAuthenticated(true);
      }, 1000);
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      setError(
        axiosError.response?.data?.error ||
          "Failed to verify access code. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setAccessToken(null);
    setAccessCode("");
    setSuccess(false);
    setError(null);
  };

  const formatAccessCode = (value: string) => {
    // Remove any non-alphanumeric characters and convert to uppercase
    const cleaned = value.replace(/[^A-Z0-9]/g, "").toUpperCase();
    // Limit to 8 characters (typical access code length)
    return cleaned.slice(0, 8);
  };

  const handleAccessCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatAccessCode(e.target.value);
    setAccessCode(formatted);
    if (error) setError(null);
  };

  // Show the form viewer if authenticated
  if (isAuthenticated && accessToken) {
    return (
      <PublicFormViewer accessToken={accessToken} onLogout={handleLogout} />
    );
  }

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Fade in timeout={800}>
        <StyledCard>
          <CardContent sx={{ p: 4 }}>
            <FloatingIcon>
              {success ? <CheckCircle /> : <VpnKey />}
            </FloatingIcon>

            <Typography
              variant="h4"
              align="center"
              gutterBottom
              sx={{
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                fontWeight: "bold",
                mb: 2,
              }}
            >
              {success ? "Access Granted!" : "Enter Access Code"}
            </Typography>

            <Typography
              variant="body1"
              align="center"
              color="text.secondary"
              sx={{ mb: 4 }}
            >
              {success
                ? "Redirecting you to the forms..."
                : "Please enter the access code provided by the administrator"}
            </Typography>

            {!success && (
              <Box component="form" onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  label="Access Code"
                  value={accessCode}
                  onChange={handleAccessCodeChange}
                  placeholder="Enter 8-character code"
                  disabled={loading}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Security color="primary" />
                      </InputAdornment>
                    ),
                    sx: {
                      fontSize: "1.2rem",
                      letterSpacing: "0.1em",
                      fontFamily: "monospace",
                      textAlign: "center",
                    },
                  }}
                  sx={{
                    mb: 3,
                    "& .MuiOutlinedInput-root": {
                      borderRadius: "16px",
                      "&.Mui-focused": {
                        "& .MuiOutlinedInput-notchedOutline": {
                          borderColor: theme.palette.primary.main,
                          borderWidth: "2px",
                        },
                      },
                    },
                  }}
                />

                {error && (
                  <Alert severity="error" sx={{ mb: 3, borderRadius: "12px" }}>
                    {error}
                  </Alert>
                )}

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  size="large"
                  disabled={
                    loading || !accessCode.trim() || accessCode.length < 4
                  }
                  startIcon={
                    loading ? <CircularProgress size={20} /> : <Login />
                  }
                  sx={{
                    py: 1.5,
                    borderRadius: "16px",
                    background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                    boxShadow: `0 8px 20px ${alpha(
                      theme.palette.primary.main,
                      0.3
                    )}`,
                    "&:hover": {
                      transform: "translateY(-2px)",
                      boxShadow: `0 12px 24px ${alpha(
                        theme.palette.primary.main,
                        0.4
                      )}`,
                    },
                    transition: "all 0.3s ease-in-out",
                  }}
                >
                  {loading ? "Verifying..." : "Access Forms"}
                </Button>
              </Box>
            )}

            {success && (
              <Box sx={{ textAlign: "center", mt: 3 }}>
                <CircularProgress size={40} color="primary" />
              </Box>
            )}
          </CardContent>
        </StyledCard>
      </Fade>

      <Box sx={{ textAlign: "center", mt: 4 }}>
        <Typography variant="body2" color="text.secondary">
          Don't have an access code?{" "}
          <Typography
            component="span"
            color="primary"
            sx={{ fontWeight: "medium" }}
          >
            Contact your administrator
          </Typography>
        </Typography>
      </Box>
    </Container>
  );
};

export default PublicFormAccess;
