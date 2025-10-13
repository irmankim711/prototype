import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControlLabel,
  Switch,
  Typography,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  LinearProgress,
  Chip,
} from "@mui/material";
import {
  ExpandMore as ExpandMoreIcon,
  Privacy as PrivacyIcon,
  Security as SecurityIcon,
  Analytics as AnalyticsIcon,
  Cookie as CookieIcon,
  Share as ShareIcon,
  CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";

interface ConsentItem {
  type: string;
  title: string;
  description: string;
  required: boolean;
  granted: boolean;
  icon: React.ReactNode;
  details: string;
}

interface ConsentModalProps {
  open: boolean;
  onClose: () => void;
  onConsentUpdate: (consents: Record<string, boolean>) => void;
  initialConsents?: Record<string, boolean>;
  privacyPolicyVersion: string;
}

const ConsentModal: React.FC<ConsentModalProps> = ({
  open,
  onClose,
  onConsentUpdate,
  initialConsents = {},
  privacyPolicyVersion,
}) => {
  const [consents, setConsents] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState<string | false>("data_processing");

  const consentItems: ConsentItem[] = [
    {
      type: "data_processing",
      title: "Data Processing",
      description:
        "Allow us to process your personal data to provide our services",
      required: true,
      granted: consents.data_processing || false,
      icon: <PrivacyIcon color="primary" />,
      details:
        "We need to process your personal data (name, email, form responses) to provide our report generation services. This includes storing your data securely and using it to create personalized reports.",
    },
    {
      type: "analytics",
      title: "Analytics & Performance",
      description: "Help us improve our services by collecting usage analytics",
      required: false,
      granted: consents.analytics || false,
      icon: <AnalyticsIcon color="info" />,
      details:
        "We collect anonymized usage data to understand how our platform is used and identify areas for improvement. This helps us provide better user experience and more relevant features.",
    },
    {
      type: "marketing",
      title: "Marketing Communications",
      description: "Receive updates about new features and improvements",
      required: false,
      granted: consents.marketing || false,
      icon: <ShareIcon color="secondary" />,
      details:
        "We may send you emails about product updates, new features, and tips for using our platform more effectively. You can unsubscribe at any time.",
    },
    {
      type: "cookies",
      title: "Cookies & Local Storage",
      description: "Store preferences and session data for better experience",
      required: false,
      granted: consents.cookies || false,
      icon: <CookieIcon color="warning" />,
      details:
        "We use cookies and local storage to remember your preferences, keep you logged in, and provide a personalized experience. Essential cookies are required for the platform to function.",
    },
    {
      type: "third_party_sharing",
      title: "Third-party Integrations",
      description:
        "Enable integrations with Google Forms, Excel, and other services",
      required: false,
      granted: consents.third_party_sharing || false,
      icon: <SecurityIcon color="success" />,
      details:
        "To provide integrations with external services like Google Forms and Microsoft Excel, we may need to share relevant data with these platforms according to their privacy policies.",
    },
  ];

  useEffect(() => {
    setConsents(initialConsents);
  }, [initialConsents]);

  const handleConsentChange = (type: string, granted: boolean) => {
    setConsents((prev) => ({
      ...prev,
      [type]: granted,
    }));
  };

  const handleAccordionChange =
    (panel: string) => (_event: React.SyntheticEvent, isExpanded: boolean) => {
      setExpanded(isExpanded ? panel : false);
    };

  const handleSaveConsents = async () => {
    setLoading(true);
    try {
      // Validate required consents
      const requiredConsents = consentItems.filter((item) => item.required);
      const missingRequired = requiredConsents.some(
        (item) => !consents[item.type]
      );

      if (missingRequired) {
        alert("Please provide consent for all required items to continue.");
        return;
      }

      await onConsentUpdate(consents);
      onClose();
    } catch (error) {
      console.error("Failed to save consents:", error);
      alert("Failed to save consent preferences. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const getConsentSummary = () => {
    const total = consentItems.length;
    const granted = Object.values(consents).filter(Boolean).length;
    return { total, granted, percentage: (granted / total) * 100 };
  };

  const summary = getConsentSummary();

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          maxHeight: "90vh",
        },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={2}>
          <PrivacyIcon color="primary" />
          <Box>
            <Typography variant="h6" component="div">
              Privacy & Consent Preferences
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Privacy Policy Version {privacyPolicyVersion} • Manage your data
              preferences
            </Typography>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        {/* Consent Progress */}
        <Box mb={3}>
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
            mb={1}
          >
            <Typography variant="body2" color="text.secondary">
              Consent Preferences
            </Typography>
            <Chip
              label={`${summary.granted}/${summary.total} Enabled`}
              color={summary.percentage >= 50 ? "success" : "warning"}
              size="small"
            />
          </Box>
          <LinearProgress
            variant="determinate"
            value={summary.percentage}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: "grey.200",
              "& .MuiLinearProgress-bar": {
                borderRadius: 4,
              },
            }}
          />
        </Box>

        {/* Privacy Notice */}
        <Alert severity="info" sx={{ mb: 3 }} icon={<SecurityIcon />}>
          <Typography variant="body2">
            Your privacy is important to us. We are committed to protecting your
            personal data in accordance with GDPR and PDPA regulations. You can
            modify these preferences at any time from your account settings.
          </Typography>
        </Alert>

        {/* Consent Items */}
        <Box>
          {consentItems.map((item) => (
            <Accordion
              key={item.type}
              expanded={expanded === item.type}
              onChange={handleAccordionChange(item.type)}
              sx={{
                mb: 1,
                border: 1,
                borderColor: "divider",
                borderRadius: 1,
                "&:before": { display: "none" },
                boxShadow: "none",
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{
                  "& .MuiAccordionSummary-content": {
                    alignItems: "center",
                    gap: 2,
                  },
                }}
              >
                {item.icon}
                <Box flex={1}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="subtitle1" fontWeight={600}>
                      {item.title}
                    </Typography>
                    {item.required && (
                      <Chip
                        label="Required"
                        size="small"
                        color="error"
                        variant="outlined"
                      />
                    )}
                    {item.granted && (
                      <CheckCircleIcon color="success" fontSize="small" />
                    )}
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {item.description}
                  </Typography>
                </Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={item.granted}
                      onChange={(e) =>
                        handleConsentChange(item.type, e.target.checked)
                      }
                      disabled={item.required && item.granted}
                      color="primary"
                    />
                  }
                  label=""
                  onClick={(e) => e.stopPropagation()}
                />
              </AccordionSummary>

              <AccordionDetails sx={{ pt: 0 }}>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ pl: 5 }}
                >
                  {item.details}
                </Typography>

                {item.required && !item.granted && (
                  <Alert severity="warning" sx={{ mt: 2, ml: 5 }}>
                    <Typography variant="body2">
                      This consent is required to use our services. Without it,
                      we cannot provide the core functionality of our platform.
                    </Typography>
                  </Alert>
                )}
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>

        {/* Legal Information */}
        <Box mt={3} p={2} bgcolor="grey.50" borderRadius={1}>
          <Typography variant="body2" color="text.secondary">
            <strong>Legal Basis:</strong> We process your data based on your
            consent, contract performance, and legitimate interests. You have
            the right to withdraw consent, access your data, request data
            portability, and request deletion at any time.
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3, gap: 2 }}>
        <Button onClick={onClose} color="inherit" disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSaveConsents}
          variant="contained"
          disabled={loading}
          startIcon={
            loading ? (
              <LinearProgress sx={{ width: 20, height: 20 }} />
            ) : (
              <CheckCircleIcon />
            )
          }
        >
          {loading ? "Saving..." : "Save Preferences"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConsentModal;
