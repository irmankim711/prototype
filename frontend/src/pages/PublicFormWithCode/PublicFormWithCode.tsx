import React from "react";
import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Fade,
  alpha,
  useTheme,
  styled,
  Alert,
  CircularProgress,
  Divider,
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  RadioGroup,
  Radio,
} from "@mui/material";
import {
  ArrowBack,
  VpnKey,
  Description,
  OpenInNew,
  Send,
} from "@mui/icons-material";
import { useNavigate, useLocation } from "react-router-dom";
import PublicFormAccess from "../../components/PublicFormAccess";
import FormRenderer from "../../components/FormRenderer";
import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000";

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
}));

interface FormData {
  id: number;
  title: string;
  description: string;
  schema?: FormField[];
}

interface FormField {
  id: string;
  type: string;
  label: string;
  required?: boolean;
  options?: string[];
  placeholder?: string;
}

const PublicFormWithCode: React.FC = () => {
  const [step, setStep] = useState<"access" | "form" | "success">("access");
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [formData, setFormData] = useState<FormData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submissionSuccess, setSubmissionSuccess] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  // Check if there's a code in the URL
  const handleCodeVerification = useCallback(async (code: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/forms/public/verify-code`,
        {
          code: code.trim().toUpperCase(),
        }
      );

      setAccessToken(response.data.access_token);
      setFormData(response.data.form);
      await loadFormData(response.data.form.id, response.data.access_token);
      setStep("form");
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      setError(
        axiosError.response?.data?.error || "Failed to verify access code"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const code = urlParams.get("code");
    if (code) {
      // Auto-verify if code is in URL
      handleCodeVerification(code);
    }
  }, [location.search, handleCodeVerification]);

  const loadFormData = async (formId: number, token: string) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/forms/public/code-access/${formId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setFormData(response.data);
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      setError(axiosError.response?.data?.error || "Failed to load form");
    }
  };

  const handleAccessGranted = async (token: string, form: FormData) => {
    setAccessToken(token);
    setFormData(form);
    await loadFormData(form.id, token);
    setStep("form");
  };

  const handleFormSubmit = async (formSubmissionData: Record<string, any>) => {
    if (!accessToken || !formData) return;

    setLoading(true);
    try {
      await axios.post(
        `${API_BASE_URL}/forms/public/code-access/${formData.id}/submit`,
        { data: formSubmissionData },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      setSubmissionSuccess(true);
      setStep("success");
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      setError(axiosError.response?.data?.error || "Failed to submit form");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (step === "form") {
      setStep("access");
      setAccessToken(null);
      setFormData(null);
    } else {
      navigate("/public-forms");
    }
  };

  const renderAccessStep = () => (
    <PublicFormAccess onAccessGranted={handleAccessGranted} />
  );

  const renderFormStep = () => {
    if (!formData) {
      return (
        <Container maxWidth="md" sx={{ py: 4 }}>
          <Box sx={{ textAlign: "center" }}>
            <CircularProgress size={40} />
            <Typography variant="body1" sx={{ mt: 2 }}>
              Loading form...
            </Typography>
          </Box>
        </Container>
      );
    }

    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Fade in timeout={600}>
          <StyledCard>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: "flex", alignItems: "center", mb: 3 }}>
                <Button
                  startIcon={<ArrowBack />}
                  onClick={handleBack}
                  sx={{ mr: 2 }}
                >
                  Back
                </Button>
                <VpnKey sx={{ mr: 2, color: "primary.main" }} />
                <Typography variant="h5" sx={{ fontWeight: "bold" }}>
                  Secure Form Access
                </Typography>
              </Box>

              <Alert severity="success" sx={{ mb: 3, borderRadius: "12px" }}>
                Access granted! You can now fill out this form.
              </Alert>

              <Typography variant="h4" gutterBottom sx={{ fontWeight: "bold" }}>
                {formData.title}
              </Typography>

              {formData.description && (
                <Typography variant="body1" color="text.secondary" paragraph>
                  {formData.description}
                </Typography>
              )}

              <Divider sx={{ my: 3 }} />

              {formData.schema && (
                <FormRenderer
                  schema={formData.schema}
                  onSubmit={handleFormSubmit}
                  loading={loading}
                />
              )}
            </CardContent>
          </StyledCard>
        </Fade>
      </Container>
    );
  };

  const renderSuccessStep = () => (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Fade in timeout={800}>
        <StyledCard>
          <CardContent sx={{ p: 4, textAlign: "center" }}>
            <Box
              sx={{
                width: 80,
                height: 80,
                borderRadius: "50%",
                background: `linear-gradient(135deg, ${theme.palette.success.main}, ${theme.palette.success.dark})`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 24px",
                color: "white",
              }}
            >
              <Description sx={{ fontSize: "2rem" }} />
            </Box>

            <Typography
              variant="h4"
              gutterBottom
              sx={{ fontWeight: "bold", color: "success.main" }}
            >
              Form Submitted Successfully!
            </Typography>

            <Typography variant="body1" color="text.secondary" paragraph>
              Thank you for your submission. Your response has been recorded.
            </Typography>

            <Box sx={{ mt: 4 }}>
              <Button
                variant="contained"
                onClick={() => navigate("/public-forms")}
                startIcon={<OpenInNew />}
                sx={{
                  borderRadius: "16px",
                  py: 1.5,
                  px: 3,
                  mr: 2,
                }}
              >
                View More Forms
              </Button>
              <Button
                variant="outlined"
                onClick={() => {
                  setStep("access");
                  setAccessToken(null);
                  setFormData(null);
                  setSubmissionSuccess(false);
                }}
                sx={{ borderRadius: "16px", py: 1.5, px: 3 }}
              >
                Submit Another
              </Button>
            </Box>
          </CardContent>
        </StyledCard>
      </Fade>
    </Container>
  );

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: `linear-gradient(135deg, ${alpha(
          theme.palette.primary.main,
          0.1
        )}, ${alpha(theme.palette.secondary.main, 0.1)})`,
        py: 2,
      }}
    >
      {loading && (
        <Paper
          sx={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            backgroundColor: alpha(theme.palette.common.white, 0.8),
            backdropFilter: "blur(4px)",
          }}
        >
          <Box sx={{ textAlign: "center" }}>
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ mt: 2 }}>
              Processing...
            </Typography>
          </Box>
        </Paper>
      )}

      {error && (
        <Container maxWidth="sm" sx={{ pt: 2 }}>
          <Alert
            severity="error"
            sx={{ borderRadius: "12px" }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        </Container>
      )}

      {step === "access" && renderAccessStep()}
      {step === "form" && renderFormStep()}
      {step === "success" && renderSuccessStep()}
    </Box>
  );
};

export default PublicFormWithCode;
