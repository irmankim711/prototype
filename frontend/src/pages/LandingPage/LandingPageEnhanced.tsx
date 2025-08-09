import { useState, useEffect, useRef } from "react";
import {
  Box,
  Button,
  Card,
  Container,
  Divider,
  Grid,
  Typography,
  AppBar,
  Toolbar,
  TextField,
  Checkbox,
  FormControlLabel,
  useMediaQuery,
  styled,
  useTheme,
  Alert,
  CircularProgress,
  Modal,
  alpha,
  Fade,
  keyframes,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { login, register } from "../../services/api";
import React from "react";
import GoogleSignInButton from "../../components/GoogleSignInButton";
import {
  AutoAwesome,
  Security,
  Speed,
  Timeline,
  CloudUpload,
  Hub,
} from "@mui/icons-material";

// Keyframe animations
const float = keyframes`
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(2deg); }
`;

const pulse = keyframes`
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
`;

const rotate = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const fadeInUp = keyframes`
  from { transform: translateY(50px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
`;

// TypeScript declarations for Google Sign-In
declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: any) => void;
          prompt: (callback?: any) => void;
          renderButton: (element: HTMLElement, config: any) => void;
        };
      };
    };
  }
}

// Enhanced styled components
const StyledAppBar = styled(AppBar)(() => ({
  backgroundColor: "rgba(255, 255, 255, 0.95)",
  backdropFilter: "blur(20px)",
  boxShadow: "0 4px 30px rgba(0, 0, 0, 0.1)",
  borderBottom: "1px solid rgba(255, 255, 255, 0.3)",
  position: "fixed",
  top: 0,
  zIndex: 1000,
  transition: "all 0.3s ease",
}));

const StyledToolbar = styled(Toolbar)(({ theme }) => ({
  display: "flex",
  justifyContent: "space-between",
  padding: theme.spacing(1.5, 3),
  transition: "all 0.3s ease",
}));

const NavButton = styled(Button)(() => ({
  color: "#475569",
  textTransform: "none",
  fontWeight: 600,
  position: "relative",
  overflow: "hidden",
  padding: "8px 16px",
  borderRadius: "8px",
  "&::before": {
    content: '""',
    position: "absolute",
    top: 0,
    left: "-100%",
    width: "100%",
    height: "100%",
    background:
      "linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.1), transparent)",
    transition: "left 0.5s ease",
  },
  "&:hover": {
    backgroundColor: alpha("#6366f1", 0.1),
    color: "#6366f1",
    transform: "translateY(-2px)",
    "&::before": {
      left: "100%",
    },
  },
}));

const RegisterButton = styled(Button)(({ theme }) => ({
  background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
  color: "white",
  textTransform: "none",
  fontWeight: 600,
  padding: theme.spacing(1, 3),
  borderRadius: "12px",
  boxShadow: "0 8px 25px rgba(99, 102, 241, 0.3)",
  transition: "all 0.3s ease",
  "&:hover": {
    background: "linear-gradient(135deg, #5856eb 0%, #7c3aed 100%)",
    transform: "translateY(-3px)",
    boxShadow: "0 12px 35px rgba(99, 102, 241, 0.4)",
  },
}));

const HeroSection = styled(Box)(() => ({
  minHeight: "100vh",
  background: `
    radial-gradient(circle at 20% 80%, ${alpha(
      "#6366f1",
      0.15
    )} 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, ${alpha(
      "#8b5cf6",
      0.15
    )} 0%, transparent 50%),
    linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)
  `,
  position: "relative",
  overflow: "hidden",
  display: "flex",
  alignItems: "center",
  "&::before": {
    content: '""',
    position: "absolute",
    top: "10%",
    right: "10%",
    width: "300px",
    height: "300px",
    borderRadius: "50%",
    background: `radial-gradient(circle, ${alpha(
      "#6366f1",
      0.1
    )} 0%, transparent 70%)`,
    animation: `${float} 6s ease-in-out infinite`,
  },
  "&::after": {
    content: '""',
    position: "absolute",
    bottom: "10%",
    left: "10%",
    width: "200px",
    height: "200px",
    borderRadius: "50%",
    background: `radial-gradient(circle, ${alpha(
      "#8b5cf6",
      0.1
    )} 0%, transparent 70%)`,
    animation: `${float} 8s ease-in-out infinite reverse`,
  },
}));

const FeatureCard = styled(Box)(({ theme }) => ({
  background: "rgba(255, 255, 255, 0.8)",
  backdropFilter: "blur(20px)",
  borderRadius: "20px",
  boxShadow: "0 15px 35px rgba(0, 0, 0, 0.08)",
  padding: theme.spacing(4),
  transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
  border: "1px solid rgba(255, 255, 255, 0.3)",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  position: "relative",
  overflow: "hidden",
  "&::before": {
    content: '""',
    position: "absolute",
    top: 0,
    left: "-100%",
    width: "100%",
    height: "100%",
    background:
      "linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent)",
    transition: "left 0.6s ease",
  },
  "&:hover": {
    transform: "translateY(-15px) scale(1.02)",
    boxShadow: "0 25px 50px rgba(99, 102, 241, 0.15)",
    border: "1px solid rgba(99, 102, 241, 0.3)",
    "&::before": {
      left: "100%",
    },
  },
}));

const AnimatedIcon = styled(Box)<{ color?: string }>(
  ({ theme, color = "#6366f1" }) => ({
    width: "80px",
    height: "80px",
    borderRadius: "20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "32px",
    marginBottom: theme.spacing(3),
    background: `linear-gradient(135deg, ${color} 0%, ${alpha(
      color,
      0.8
    )} 100%)`,
    color: "white",
    boxShadow: `0 10px 25px ${alpha(color, 0.3)}`,
    transition: "all 0.3s ease",
    position: "relative",
    "&::before": {
      content: '""',
      position: "absolute",
      inset: "-2px",
      borderRadius: "22px",
      padding: "2px",
      background: `linear-gradient(135deg, ${color}, transparent, ${color})`,
      mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
      maskComposite: "xor",
      animation: `${rotate} 3s linear infinite`,
    },
    "&:hover": {
      transform: "rotate(10deg) scale(1.1)",
      animation: `${pulse} 0.6s ease-in-out`,
    },
  })
);

const LoginCard = styled(Card)(({ theme }) => ({
  maxWidth: 450,
  margin: "0 auto",
  padding: theme.spacing(4),
  boxShadow: "0 25px 50px rgba(0, 0, 0, 0.15)",
  borderRadius: "24px",
  background: "rgba(255, 255, 255, 0.95)",
  backdropFilter: "blur(20px)",
  border: "1px solid rgba(255, 255, 255, 0.3)",
  transition: "all 0.3s ease",
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  marginBottom: theme.spacing(2),
  "& .MuiOutlinedInput-root": {
    borderRadius: "12px",
    transition: "all 0.3s ease",
    "& fieldset": {
      borderColor: "rgba(0, 0, 0, 0.1)",
      transition: "all 0.3s ease",
    },
    "&:hover fieldset": {
      borderColor: "#6366f1",
      boxShadow: "0 4px 12px rgba(99, 102, 241, 0.15)",
    },
    "&.Mui-focused fieldset": {
      borderColor: "#6366f1",
      borderWidth: "2px",
      boxShadow: "0 4px 12px rgba(99, 102, 241, 0.25)",
    },
  },
  "& .MuiInputLabel-root": {
    color: "#64748b",
    "&.Mui-focused": {
      color: "#6366f1",
    },
  },
  "& .MuiInputBase-input": {
    padding: "16px 18px",
  },
}));

// Main component
export default function LandingPageEnhanced() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showQuickAccess, setShowQuickAccess] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [signupEmail, setSignupEmail] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupConfirm, setSignupConfirm] = useState("");
  const [signupLoading, setSignupLoading] = useState(false);
  const [signupError, setSignupError] = useState("");
  const [signupSuccess, setSignupSuccess] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  // Quick Access states
  const [quickAccessPhone, setQuickAccessPhone] = useState("");
  const [quickAccessOtp, setQuickAccessOtp] = useState("");
  const [quickAccessToken, setQuickAccessToken] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [quickAccessLoading, setQuickAccessLoading] = useState(false);
  const [quickAccessError, setQuickAccessError] = useState("");
  const [useGoogleAuth, setUseGoogleAuth] = useState(false);

  // Refs for scroll animations
  const featuresRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Mouse move effect
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) * 100;
      const y = (e.clientY / window.innerHeight) * 100;
      document.documentElement.style.setProperty("--mouse-x", `${x}%`);
      document.documentElement.style.setProperty("--mouse-y", `${y}%`);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  const handleShowLogin = () => {
    setShowLogin(true);
    setShowSignup(false);
  };
  const handleShowSignup = () => {
    setShowSignup(true);
    setShowLogin(false);
  };
  const handleBackToHome = () => {
    setShowLogin(false);
    setShowSignup(false);
    setShowQuickAccess(false);
    setOtpSent(false);
    setQuickAccessError("");
    setQuickAccessPhone("");
    setQuickAccessOtp("");
    setUseGoogleAuth(false);
  };

  const handleAboutUs = () => {
    navigate("/about");
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage("");
    console.log("Login attempt started with:", { email, password });
    try {
      const response = await login({ email, password });
      console.log("Login response received:", response);
      if (response.access_token) {
        localStorage.setItem("token", response.access_token);
        console.log("Token saved to localStorage, navigating to dashboard...");
        navigate("/dashboard");
      } else {
        console.log("No access token in response");
        setErrorMessage("Login failed. No token received.");
      }
    } catch (err: any) {
      console.error("Login error:", err);
      setErrorMessage(err?.response?.data?.msg || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  // Signup handler
  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSignupError("");
    setSignupSuccess(false);
    if (!signupEmail || !signupPassword || !signupConfirm) {
      setSignupError("All fields are required.");
      return;
    }
    if (signupPassword !== signupConfirm) {
      setSignupError("Passwords do not match.");
      return;
    }
    setSignupLoading(true);
    try {
      await register({
        email: signupEmail,
        password: signupPassword,
        confirmPassword: signupConfirm,
      });
      setSignupSuccess(true);
      setSignupEmail("");
      setSignupPassword("");
      setSignupConfirm("");
    } catch (err: any) {
      setSignupError(err?.response?.data?.msg || "Registration failed.");
    } finally {
      setSignupLoading(false);
    }
  };

  // Quick Access handlers
  const handleShowQuickAccess = () => {
    setShowQuickAccess(true);
    setShowLogin(false);
    setShowSignup(false);
  };

  const handleQuickAccessWithPhone = async (e: React.FormEvent) => {
    e.preventDefault();
    setQuickAccessLoading(true);
    setQuickAccessError("");

    try {
      const response = await fetch(
        "http://localhost:5000/api/quick-auth/request-otp",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ phone: quickAccessPhone }),
        }
      );

      const data = await response.json();
      if (response.ok) {
        setOtpSent(true);
        setQuickAccessToken(data.token_id); // Store token_id for verification
        setQuickAccessError("");
      } else {
        setQuickAccessError(data.error || data.msg || "Failed to send OTP");
      }
    } catch (error) {
      setQuickAccessError("Network error. Please try again.");
    } finally {
      setQuickAccessLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setQuickAccessLoading(true);
    setQuickAccessError("");

    try {
      const response = await fetch(
        "http://localhost:5000/api/quick-auth/verify-otp",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            token_id: quickAccessToken, // Use stored token_id
            otp_code: quickAccessOtp, // Use otp_code instead of otp
          }),
        }
      );

      const data = await response.json();
      if (response.ok) {
        console.log("OTP verification successful:", data);
        console.log("Saving token to localStorage:", data.access_token);
        localStorage.setItem("quickAccessToken", data.access_token);

        // Verify token was saved
        const savedToken = localStorage.getItem("quickAccessToken");
        console.log("Token saved successfully:", !!savedToken);

        console.log("Navigating to /forms/public");
        navigate("/forms/public");
      } else {
        console.error("OTP verification failed:", data);
        setQuickAccessError(data.error || data.msg || "Invalid OTP");
      }
    } catch (error) {
      setQuickAccessError("Network error. Please try again.");
    } finally {
      setQuickAccessLoading(false);
    }
  };

  const handleGoogleSignInSuccess = async (credential: string) => {
    setQuickAccessLoading(true);
    setQuickAccessError("");

    try {
      // Send the credential to our backend
      const apiResponse = await fetch(
        "http://localhost:5000/api/quick-auth/google-signin",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            googleToken: credential,
          }),
        }
      );

      const data = await apiResponse.json();
      if (apiResponse.ok) {
        localStorage.setItem("quickAccessToken", data.access_token);
        navigate("/forms/public");
      } else {
        setQuickAccessError(data.error || data.msg || "Google Sign-In failed");
      }
    } catch (error) {
      console.error("Google Sign-In error:", error);
      setQuickAccessError("Network error. Please try again.");
    } finally {
      setQuickAccessLoading(false);
    }
  };

  const handleGoogleSignInError = (error: string) => {
    setQuickAccessError(error);
    setQuickAccessLoading(false);
  };

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState<
    "solutions" | "learn" | null
  >(null);

  // Scroll handlers
  const scrollToSection = (ref: React.RefObject<HTMLDivElement | null>) => {
    if (ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Modal openers
  const handleOpenModal = (content: "solutions" | "learn") => {
    setModalContent(content);
    setModalOpen(true);
  };
  const handleCloseModal = () => setModalOpen(false);

  const features = [
    {
      icon: <AutoAwesome />,
      title: "AI-Powered Analytics",
      description:
        "Advanced machine learning algorithms that transform your data into actionable insights automatically.",
      color: "#6366f1",
      delay: 100,
    },
    {
      icon: <Security />,
      title: "Enterprise Security",
      description:
        "Bank-grade encryption and compliance standards protecting your most sensitive business data.",
      color: "#10b981",
      delay: 200,
    },
    {
      icon: <Speed />,
      title: "Lightning Fast",
      description:
        "Optimized performance that processes millions of records in seconds, not hours.",
      color: "#f59e0b",
      delay: 300,
    },
    {
      icon: <Hub />,
      title: "Seamless Integration",
      description:
        "Connect with 500+ business tools and platforms with just a few clicks.",
      color: "#ec4899",
      delay: 400,
    },
    {
      icon: <Timeline />,
      title: "Real-time Insights",
      description:
        "Live dashboards and real-time analytics keep you ahead of the competition.",
      color: "#8b5cf6",
      delay: 500,
    },
    {
      icon: <CloudUpload />,
      title: "Cloud Native",
      description:
        "Built for the cloud with automatic scaling and 99.9% uptime guarantee.",
      color: "#06b6d4",
      delay: 600,
    },
  ];

  const stats = [
    { number: "10M+", label: "Reports Generated", color: "#6366f1" },
    { number: "500+", label: "Enterprise Clients", color: "#10b981" },
    { number: "99.9%", label: "Uptime Guarantee", color: "#f59e0b" },
    { number: "24/7", label: "Expert Support", color: "#ec4899" },
  ];

  return (
    <Box>
      {/* Navigation Bar */}
      <StyledAppBar elevation={0}>
        <StyledToolbar>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
              backgroundClip: "text",
              color: "transparent",
              cursor: "pointer",
            }}
            onClick={handleBackToHome}
          >
            StratoSys
          </Typography>
          {!showLogin && !showSignup && !showQuickAccess && (
            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <NavButton onClick={() => scrollToSection(featuresRef)}>
                Features
              </NavButton>
              <NavButton onClick={() => handleOpenModal("solutions")}>
                Solutions
              </NavButton>
              <NavButton onClick={() => handleOpenModal("learn")}>
                Pricing
              </NavButton>
              <NavButton onClick={handleAboutUs}>About Us</NavButton>
              <NavButton onClick={handleShowLogin}>Admin Login</NavButton>
              <NavButton
                onClick={handleShowQuickAccess}
                sx={{
                  backgroundColor: alpha("#10B981", 0.1),
                  color: "#10B981",
                  border: "1px solid #10B981",
                  "&:hover": {
                    backgroundColor: alpha("#10B981", 0.2),
                    transform: "translateY(-2px)",
                  },
                }}
              >
                Quick Access
              </NavButton>
              <RegisterButton onClick={handleShowSignup}>
                Get Started Free
              </RegisterButton>
            </Box>
          )}
          {(showLogin || showSignup || showQuickAccess) && (
            <NavButton onClick={handleBackToHome}>Back to Home</NavButton>
          )}
        </StyledToolbar>
      </StyledAppBar>

      {/* Login Form */}
      {showLogin && (
        <Container maxWidth="lg" sx={{ py: 8, mt: 8 }}>
          <Fade in={showLogin} timeout={800}>
            <LoginCard>
              <Typography
                variant="h4"
                align="center"
                sx={{
                  mb: 4,
                  fontWeight: 700,
                  background:
                    "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                Welcome Back
              </Typography>
              {errorMessage && (
                <Alert severity="error" sx={{ mb: 3, borderRadius: "12px" }}>
                  {errorMessage}
                </Alert>
              )}
              <Box component="form" onSubmit={handleLoginSubmit}>
                <StyledTextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e: any) => setEmail(e.target.value)}
                  required
                />
                <StyledTextField
                  fullWidth
                  label="Password"
                  type="password"
                  value={password}
                  onChange={(e: any) => setPassword(e.target.value)}
                  required
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={rememberMe}
                      onChange={(e: any) => setRememberMe(e.target.checked)}
                      sx={{
                        color: "#6366f1",
                        "&.Mui-checked": { color: "#6366f1" },
                      }}
                    />
                  }
                  label="Remember me"
                  sx={{ mb: 3 }}
                />
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  disabled={loading}
                  sx={{
                    py: 2,
                    mb: 2,
                    borderRadius: "12px",
                    background:
                      "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                    fontSize: "1.1rem",
                    fontWeight: 600,
                    boxShadow: "0 8px 25px rgba(99, 102, 241, 0.3)",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      background:
                        "linear-gradient(135deg, #5856eb 0%, #7c3aed 100%)",
                      transform: "translateY(-2px)",
                      boxShadow: "0 12px 35px rgba(99, 102, 241, 0.4)",
                    },
                  }}
                >
                  {loading ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    "Sign In"
                  )}
                </Button>
              </Box>
              <Divider sx={{ my: 3 }} />
              <Typography align="center" color="textSecondary">
                Don't have an account?{" "}
                <Button
                  onClick={handleShowSignup}
                  sx={{ color: "#6366f1", fontWeight: 600 }}
                >
                  Sign up
                </Button>
              </Typography>
            </LoginCard>
          </Fade>
        </Container>
      )}

      {/* Quick Access Form */}
      {showQuickAccess && (
        <Container maxWidth="lg" sx={{ py: 8, mt: 8 }}>
          <Fade in={showQuickAccess} timeout={800}>
            <LoginCard>
              <Typography
                variant="h4"
                align="center"
                sx={{
                  mb: 4,
                  fontWeight: 700,
                  background:
                    "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                Quick Access
              </Typography>
              <Typography
                variant="body1"
                align="center"
                color="textSecondary"
                sx={{ mb: 4 }}
              >
                Choose your preferred access method
              </Typography>

              {quickAccessError && (
                <Alert severity="error" sx={{ mb: 3, borderRadius: "12px" }}>
                  {quickAccessError}
                </Alert>
              )}

              {/* Google Sign-In Option */}
              <Box sx={{ mb: 3, display: "flex", justifyContent: "center" }}>
                <GoogleSignInButton
                  onSuccess={handleGoogleSignInSuccess}
                  onError={handleGoogleSignInError}
                  disabled={quickAccessLoading}
                />
              </Box>

              <Divider sx={{ my: 3 }}>
                <Typography variant="body2" color="textSecondary">
                  OR
                </Typography>
              </Divider>

              {/* Phone Number Option */}
              {!otpSent ? (
                <Box component="form" onSubmit={handleQuickAccessWithPhone}>
                  <StyledTextField
                    fullWidth
                    label="Phone Number"
                    type="tel"
                    value={quickAccessPhone}
                    onChange={(e: any) => setQuickAccessPhone(e.target.value)}
                    required
                    sx={{ mb: 3 }}
                    placeholder="+60 123456 7890"
                    helperText="We'll send you a verification code via SMS"
                  />
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    disabled={quickAccessLoading}
                    sx={{
                      py: 2,
                      mb: 2,
                      borderRadius: "12px",
                      background:
                        "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                      fontSize: "1.1rem",
                      fontWeight: 600,
                      boxShadow: "0 8px 25px rgba(16, 185, 129, 0.3)",
                      transition: "all 0.3s ease",
                      "&:hover": {
                        background:
                          "linear-gradient(135deg, #059669 0%, #047857 100%)",
                        transform: "translateY(-2px)",
                        boxShadow: "0 12px 35px rgba(16, 185, 129, 0.4)",
                      },
                    }}
                  >
                    {quickAccessLoading ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      "Send SMS Code"
                    )}
                  </Button>
                </Box>
              ) : (
                <Box component="form" onSubmit={handleVerifyOtp}>
                  <Typography
                    variant="body2"
                    color="textSecondary"
                    sx={{ mb: 2, textAlign: "center" }}
                  >
                    Enter the verification code sent to {quickAccessPhone}
                  </Typography>
                  <StyledTextField
                    fullWidth
                    label="Verification Code"
                    value={quickAccessOtp}
                    onChange={(e: any) => setQuickAccessOtp(e.target.value)}
                    required
                    sx={{ mb: 3 }}
                    placeholder="Enter 6-digit code"
                  />
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    disabled={quickAccessLoading}
                    sx={{
                      py: 2,
                      mb: 2,
                      borderRadius: "12px",
                      background:
                        "linear-gradient(135deg, #10B981 0%, #059669 100%)",
                      fontSize: "1.1rem",
                      fontWeight: 600,
                      boxShadow: "0 8px 25px rgba(16, 185, 129, 0.3)",
                      transition: "all 0.3s ease",
                      "&:hover": {
                        background:
                          "linear-gradient(135deg, #059669 0%, #047857 100%)",
                        transform: "translateY(-2px)",
                        boxShadow: "0 12px 35px rgba(16, 185, 129, 0.4)",
                      },
                    }}
                  >
                    {quickAccessLoading ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      "Verify & Access Forms"
                    )}
                  </Button>
                  <Button
                    onClick={() => {
                      setOtpSent(false);
                      setQuickAccessOtp("");
                      setQuickAccessError("");
                    }}
                    fullWidth
                    variant="text"
                    sx={{ color: "#10B981", fontWeight: 600 }}
                  >
                    Try Different Number
                  </Button>
                </Box>
              )}

              {/* Development Bypass Button */}
              <Divider sx={{ my: 3 }}>
                <Typography variant="body2" color="textSecondary">
                  DEVELOPMENT
                </Typography>
              </Divider>

              <Button
                onClick={() => {
                  // Store a dummy token for bypass
                  localStorage.setItem("quickAccessToken", "dev-bypass-token");
                  localStorage.setItem(
                    "quickAccessUser",
                    JSON.stringify({
                      name: "Development User",
                      email: "dev@example.com",
                      access_type: "bypass",
                    })
                  );
                  console.log("Development bypass: Navigating to public forms");
                  navigate("/forms/public");
                }}
                fullWidth
                variant="outlined"
                sx={{
                  py: 2,
                  mb: 3,
                  borderRadius: "12px",
                  border: "2px solid #f59e0b",
                  color: "#f59e0b",
                  fontSize: "1.1rem",
                  fontWeight: 600,
                  transition: "all 0.3s ease",
                  "&:hover": {
                    background: "#fef3c7",
                    borderColor: "#d97706",
                    color: "#d97706",
                  },
                }}
              >
                🚀 Skip Authentication (Dev Mode)
              </Button>

              <Divider sx={{ my: 3 }} />
              <Typography align="center" color="textSecondary">
                Need full admin access?{" "}
                <Button
                  onClick={handleShowLogin}
                  sx={{ color: "#6366f1", fontWeight: 600 }}
                >
                  Admin Login
                </Button>
              </Typography>
            </LoginCard>
          </Fade>
        </Container>
      )}

      {/* Signup Form */}
      {showSignup && (
        <Container maxWidth="lg" sx={{ py: 8, mt: 8 }}>
          <Fade in={showSignup} timeout={800}>
            <LoginCard>
              <Typography
                variant="h4"
                align="center"
                sx={{
                  mb: 4,
                  fontWeight: 700,
                  background:
                    "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                Join StratoSys
              </Typography>
              {signupError && (
                <Alert severity="error" sx={{ mb: 3, borderRadius: "12px" }}>
                  {signupError}
                </Alert>
              )}
              {signupSuccess && (
                <Alert severity="success" sx={{ mb: 3, borderRadius: "12px" }}>
                  Registration successful! You can now log in.
                </Alert>
              )}
              <Box component="form" onSubmit={handleSignupSubmit}>
                <StyledTextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={signupEmail}
                  onChange={(e: any) => setSignupEmail(e.target.value)}
                  required
                />
                <StyledTextField
                  fullWidth
                  label="Password"
                  type="password"
                  value={signupPassword}
                  onChange={(e: any) => setSignupPassword(e.target.value)}
                  required
                />
                <StyledTextField
                  fullWidth
                  label="Confirm Password"
                  type="password"
                  value={signupConfirm}
                  onChange={(e: any) => setSignupConfirm(e.target.value)}
                  required
                />
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  disabled={signupLoading}
                  sx={{
                    py: 2,
                    mb: 2,
                    borderRadius: "12px",
                    background:
                      "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                    fontSize: "1.1rem",
                    fontWeight: 600,
                    boxShadow: "0 8px 25px rgba(99, 102, 241, 0.3)",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      background:
                        "linear-gradient(135deg, #5856eb 0%, #7c3aed 100%)",
                      transform: "translateY(-2px)",
                      boxShadow: "0 12px 35px rgba(99, 102, 241, 0.4)",
                    },
                  }}
                >
                  {signupLoading ? (
                    <CircularProgress size={24} color="inherit" />
                  ) : (
                    "Create Account"
                  )}
                </Button>
              </Box>
              <Divider sx={{ my: 3 }} />
              <Typography align="center" color="textSecondary">
                Already have an account?{" "}
                <Button
                  onClick={handleShowLogin}
                  sx={{ color: "#6366f1", fontWeight: 600 }}
                >
                  Sign in
                </Button>
              </Typography>
            </LoginCard>
          </Fade>
        </Container>
      )}

      {/* Hero Section */}
      {!showLogin && !showSignup && (
        <>
          <HeroSection>
            <Container maxWidth="lg" sx={{ position: "relative", zIndex: 10 }}>
              <Grid container spacing={6} alignItems="center">
                <Grid item xs={12} md={6}>
                  <Fade in={true} timeout={1000}>
                    <Box>
                      <Typography
                        variant="h1"
                        sx={{
                          fontSize: { xs: "3rem", md: "4rem", lg: "5rem" },
                          fontWeight: 800,
                          lineHeight: 1.1,
                          mb: 3,
                          background:
                            "linear-gradient(135deg, #1e293b 0%, #475569 50%, #6366f1 100%)",
                          backgroundClip: "text",
                          color: "transparent",
                          animation: `${fadeInUp} 1s ease-out`,
                        }}
                      >
                        Transform Data Into
                        <Box
                          component="span"
                          sx={{
                            display: "block",
                            background:
                              "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                            backgroundClip: "text",
                            color: "transparent",
                            animation: `${pulse} 2s ease-in-out infinite`,
                          }}
                        >
                          Business Gold
                        </Box>
                      </Typography>
                      <Typography
                        variant="h5"
                        sx={{
                          color: "#64748b",
                          mb: 4,
                          lineHeight: 1.6,
                          fontWeight: 400,
                          animation: `${fadeInUp} 1s ease-out 0.3s both`,
                        }}
                      >
                        Unlock the power of AI-driven analytics and automated
                        reporting. Make decisions faster with real-time insights
                        that matter.
                      </Typography>
                      <Box
                        sx={{
                          display: "flex",
                          gap: 3,
                          flexDirection: { xs: "column", sm: "row" },
                          animation: `${fadeInUp} 1s ease-out 0.6s both`,
                        }}
                      >
                        <Button
                          size="large"
                          variant="contained"
                          onClick={handleShowSignup}
                          sx={{
                            py: 2,
                            px: 4,
                            borderRadius: "16px",
                            background:
                              "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                            fontSize: "1.2rem",
                            fontWeight: 600,
                            boxShadow: "0 12px 30px rgba(99, 102, 241, 0.4)",
                            transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
                            "&:hover": {
                              background:
                                "linear-gradient(135deg, #5856eb 0%, #7c3aed 100%)",
                              transform: "translateY(-4px) scale(1.05)",
                              boxShadow: "0 20px 40px rgba(99, 102, 241, 0.5)",
                            },
                          }}
                        >
                          Start Free Trial
                        </Button>
                        <Button
                          size="large"
                          variant="outlined"
                          onClick={() => scrollToSection(featuresRef)}
                          sx={{
                            py: 2,
                            px: 4,
                            borderRadius: "16px",
                            border: "2px solid #e2e8f0",
                            color: "#475569",
                            fontSize: "1.2rem",
                            fontWeight: 600,
                            transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
                            "&:hover": {
                              border: "2px solid #6366f1",
                              color: "#6366f1",
                              transform: "translateY(-2px)",
                              boxShadow: "0 8px 25px rgba(99, 102, 241, 0.2)",
                            },
                          }}
                        >
                          Watch Demo
                        </Button>
                      </Box>
                    </Box>
                  </Fade>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box
                    sx={{
                      position: "relative",
                      height: "500px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {/* Animated dashboard preview */}
                    <Box
                      sx={{
                        width: "100%",
                        height: "400px",
                        background: "rgba(255, 255, 255, 0.9)",
                        backdropFilter: "blur(20px)",
                        borderRadius: "24px",
                        boxShadow: "0 25px 50px rgba(0, 0, 0, 0.15)",
                        border: "1px solid rgba(255, 255, 255, 0.3)",
                        position: "relative",
                        overflow: "hidden",
                        animation: `${float} 6s ease-in-out infinite`,
                        "&::before": {
                          content: '""',
                          position: "absolute",
                          top: 0,
                          left: "-100%",
                          width: "100%",
                          height: "100%",
                          background:
                            "linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.1), transparent)",
                          animation: "shimmer 3s ease-in-out infinite",
                        },
                      }}
                    >
                      {/* Mock dashboard content */}
                      <Box sx={{ p: 3 }}>
                        <Box
                          sx={{
                            height: "20px",
                            background:
                              "linear-gradient(90deg, #e2e8f0, #cbd5e1)",
                            borderRadius: "10px",
                            mb: 2,
                            width: "60%",
                          }}
                        />
                        <Grid container spacing={2} sx={{ mb: 3 }}>
                          {[1, 2, 3, 4].map((i: any) => (
                            <Grid item xs={6} key={i}>
                              <Box
                                sx={{
                                  height: "80px",
                                  background: `linear-gradient(135deg, ${
                                    features[i - 1]?.color || "#6366f1"
                                  }20, ${
                                    features[i - 1]?.color || "#6366f1"
                                  }10)`,
                                  borderRadius: "12px",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  color: features[i - 1]?.color || "#6366f1",
                                  fontWeight: 600,
                                  animation: `${pulse} ${
                                    2 + i * 0.5
                                  }s ease-in-out infinite`,
                                }}
                              >
                                {features[i - 1]?.icon}
                              </Box>
                            </Grid>
                          ))}
                        </Grid>
                        <Box
                          sx={{
                            height: "150px",
                            background:
                              "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)",
                            borderRadius: "16px",
                            position: "relative",
                            overflow: "hidden",
                          }}
                        >
                          {/* Animated chart bars */}
                          <Box
                            sx={{
                              position: "absolute",
                              bottom: 20,
                              left: 20,
                              right: 20,
                              display: "flex",
                              alignItems: "end",
                              gap: 1,
                            }}
                          >
                            {[40, 70, 45, 85, 60, 90, 55].map((height, i) => (
                              <Box
                                key={i}
                                sx={{
                                  flex: 1,
                                  height: `${height}px`,
                                  background: `linear-gradient(to top, ${
                                    features[i % features.length]?.color
                                  }80, ${
                                    features[i % features.length]?.color
                                  }40)`,
                                  borderRadius: "4px 4px 0 0",
                                  animation: `${fadeInUp} ${
                                    1 + i * 0.1
                                  }s ease-out ${i * 0.1}s both`,
                                }}
                              />
                            ))}
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                  </Box>
                </Grid>
              </Grid>

              {/* Stats Section */}
              <Box sx={{ mt: 12 }}>
                <Grid container spacing={4}>
                  {stats.map((stat, index) => (
                    <Grid item xs={6} md={3} key={index}>
                      <Box
                        sx={{
                          textAlign: "center",
                          background: "rgba(255, 255, 255, 0.8)",
                          backdropFilter: "blur(20px)",
                          borderRadius: "16px",
                          padding: 3,
                          border: "1px solid rgba(255, 255, 255, 0.3)",
                          transition: "all 0.3s ease",
                          animation: `${fadeInUp} 1s ease-out ${
                            index * 0.1
                          }s both`,
                          "&:hover": {
                            transform: "translateY(-8px) scale(1.05)",
                            boxShadow: "0 20px 40px rgba(0, 0, 0, 0.1)",
                          },
                        }}
                      >
                        <Typography
                          variant="h3"
                          sx={{
                            fontWeight: 800,
                            color: stat.color,
                            mb: 1,
                            animation: `${pulse} 2s ease-in-out infinite`,
                          }}
                        >
                          {stat.number}
                        </Typography>
                        <Typography
                          variant="body1"
                          color="textSecondary"
                          fontWeight={600}
                        >
                          {stat.label}
                        </Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Box>
            </Container>
          </HeroSection>

          {/* Features Section */}
          <Box ref={featuresRef} sx={{ py: 12, background: "#f8fafc" }}>
            <Container maxWidth="lg">
              <Box sx={{ textAlign: "center", mb: 8 }}>
                <Typography
                  variant="h2"
                  sx={{
                    fontWeight: 800,
                    mb: 3,
                    background:
                      "linear-gradient(135deg, #1e293b 0%, #6366f1 100%)",
                    backgroundClip: "text",
                    color: "transparent",
                  }}
                >
                  Powerful Features
                </Typography>
                <Typography
                  variant="h6"
                  color="textSecondary"
                  sx={{ maxWidth: 600, mx: "auto" }}
                >
                  Everything you need to transform your data into actionable
                  insights
                </Typography>
              </Box>
              <Grid container spacing={4}>
                {features.map((feature, index) => (
                  <Grid item xs={12} md={6} lg={4} key={index}>
                    <FeatureCard
                      sx={{
                        animation: `${fadeInUp} 0.8s ease-out ${
                          index * 0.1
                        }s both`,
                      }}
                    >
                      <AnimatedIcon color={feature.color}>
                        {feature.icon}
                      </AnimatedIcon>
                      <Typography
                        variant="h5"
                        fontWeight={700}
                        sx={{ mb: 2, color: "#1e293b" }}
                      >
                        {feature.title}
                      </Typography>
                      <Typography
                        color="textSecondary"
                        sx={{ lineHeight: 1.7 }}
                      >
                        {feature.description}
                      </Typography>
                    </FeatureCard>
                  </Grid>
                ))}
              </Grid>
            </Container>
          </Box>

          {/* CTA Section */}
          <Box
            sx={{
              py: 12,
              background: "linear-gradient(135deg, #1e293b 0%, #475569 100%)",
              color: "white",
              position: "relative",
              overflow: "hidden",
              "&::before": {
                content: '""',
                position: "absolute",
                top: "50%",
                left: "50%",
                width: "600px",
                height: "600px",
                borderRadius: "50%",
                background:
                  "radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%)",
                transform: "translate(-50%, -50%)",
                animation: `${float} 8s ease-in-out infinite`,
              },
            }}
          >
            <Container maxWidth="lg" sx={{ position: "relative", zIndex: 10 }}>
              <Box sx={{ textAlign: "center" }}>
                <Typography
                  variant="h2"
                  sx={{
                    fontWeight: 800,
                    mb: 3,
                    background:
                      "linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%)",
                    backgroundClip: "text",
                    color: "transparent",
                  }}
                >
                  Ready to Get Started?
                </Typography>
                <Typography
                  variant="h6"
                  sx={{ mb: 6, color: "#cbd5e1", maxWidth: 600, mx: "auto" }}
                >
                  Join thousands of companies already using StratoSys to make
                  better decisions
                </Typography>
                <Box
                  sx={{
                    display: "flex",
                    gap: 3,
                    justifyContent: "center",
                    flexWrap: "wrap",
                  }}
                >
                  <Button
                    size="large"
                    variant="contained"
                    onClick={handleShowSignup}
                    sx={{
                      py: 2,
                      px: 6,
                      borderRadius: "16px",
                      background:
                        "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
                      fontSize: "1.2rem",
                      fontWeight: 600,
                      boxShadow: "0 12px 30px rgba(99, 102, 241, 0.4)",
                      transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
                      "&:hover": {
                        background:
                          "linear-gradient(135deg, #5856eb 0%, #7c3aed 100%)",
                        transform: "translateY(-4px) scale(1.05)",
                        boxShadow: "0 20px 40px rgba(99, 102, 241, 0.5)",
                      },
                    }}
                  >
                    Start Your Free Trial
                  </Button>
                  <Button
                    size="large"
                    variant="outlined"
                    onClick={handleShowLogin}
                    sx={{
                      py: 2,
                      px: 6,
                      borderRadius: "16px",
                      border: "2px solid rgba(255, 255, 255, 0.3)",
                      color: "white",
                      fontSize: "1.2rem",
                      fontWeight: 600,
                      transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
                      "&:hover": {
                        border: "2px solid #6366f1",
                        background: "rgba(99, 102, 241, 0.1)",
                        transform: "translateY(-2px)",
                        boxShadow: "0 8px 25px rgba(99, 102, 241, 0.3)",
                      },
                    }}
                  >
                    Sign In
                  </Button>
                </Box>
              </Box>
            </Container>
          </Box>
        </>
      )}

      {/* Modal */}
      <Modal open={modalOpen} onClose={handleCloseModal}>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: { xs: "90%", sm: 600 },
            bgcolor: "background.paper",
            borderRadius: "20px",
            boxShadow: 24,
            p: 4,
            outline: "none",
          }}
        >
          <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
            {modalContent === "solutions" ? "Our Solutions" : "Pricing Plans"}
          </Typography>
          <Typography variant="body1" sx={{ mb: 3, color: "textSecondary" }}>
            {modalContent === "solutions"
              ? "Discover how StratoSys can transform your business with our comprehensive suite of analytics tools."
              : "Choose the perfect plan for your business needs. All plans include our core features with varying levels of support and customization."}
          </Typography>
          <Button
            variant="contained"
            onClick={handleCloseModal}
            sx={{
              background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
              borderRadius: "12px",
            }}
          >
            Close
          </Button>
        </Box>
      </Modal>

      <style>
        {`
          @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
          }
        `}
      </style>
    </Box>
  );
}
