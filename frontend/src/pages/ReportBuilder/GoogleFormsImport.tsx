import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Button,
  Typography,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  TextField,
  MenuItem,
  Chip,
  Grid,
  IconButton,
  Tooltip,
  LinearProgress,
} from "@mui/material";
import { Google, Refresh, CheckCircle } from "@mui/icons-material";
import googleFormsService from "../../services/googleFormsService";
import type {
  GoogleForm,
  GoogleFormAnalytics,
} from "../../services/googleFormsService";

interface GoogleFormsImportProps {
  onFormSelect: (formId: string, formData: GoogleForm) => void;
  selectedFormId?: string;
}

const GoogleFormsImport: React.FC<GoogleFormsImportProps> = ({
  onFormSelect,
  selectedFormId,
}) => {
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [forms, setForms] = useState<GoogleForm[]>([]);
  const [selectedForm, setSelectedForm] = useState<GoogleForm | null>(null);
  const [formAnalytics, setFormAnalytics] =
    useState<GoogleFormAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Check authorization status on component mount
  useEffect(() => {
    checkAuthAndLoadForms();
  }, []);

  // Handle form selection
  useEffect(() => {
    if (selectedFormId && forms.length > 0) {
      const form = forms.find((f: any) => f.id === selectedFormId);
      if (form) {
        setSelectedForm(form);
        loadFormAnalytics(form.id);
      }
    }
  }, [selectedFormId, forms]);

  const checkAuthAndLoadForms = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Try to load forms directly - if successful, user is already authorized
      const formsData = await googleFormsService.getUserForms();
      setForms(formsData.forms);
      setIsAuthorized(true);
    } catch {
      console.log("User not authorized or no forms available");
      setIsAuthorized(false);
      setForms([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthorize = async () => {
    try {
      setError(null);
      console.log("🔑 Initiating Google Forms authorization...");

      const authData = await googleFormsService.initiateAuth();
      console.log("✅ Auth URL received:", authData.auth_url);

      // Open auth window
      const popup = window.open(
        authData.auth_url,
        "google_auth",
        "width=500,height=600,scrollbars=yes,resizable=yes"
      );

      // Poll for window closure (indicating auth completion)
      const pollTimer = setInterval(() => {
        if (popup?.closed) {
          clearInterval(pollTimer);
          // Wait a moment then try to load forms
          setTimeout(() => {
            checkAuthAndLoadForms();
          }, 1000);
        }
      }, 1000);
    } catch (error: unknown) {
      console.error("❌ Authorization error:", error);
      setError("Failed to initiate authorization. Please try again.");
    }
  };

  const refreshForms = async () => {
    setIsRefreshing(true);
    setError(null);

    try {
      const formsData = await googleFormsService.getUserForms();
      setForms(formsData.forms);
      setIsAuthorized(true);
    } catch (error: unknown) {
      console.error("❌ Error refreshing forms:", error);
      setError("Failed to refresh forms. Please check your authorization.");
      setIsAuthorized(false);
    } finally {
      setIsRefreshing(false);
    }
  };

  const loadFormAnalytics = async (formId: string) => {
    try {
      const analyticsData = await googleFormsService.getFormAnalytics(formId);
      setFormAnalytics(analyticsData.analytics);
    } catch (error: unknown) {
      console.error("❌ Error loading form analytics:", error);
      // Don't show error for analytics as it's optional
    }
  };

  const handleFormSelect = (form: GoogleForm) => {
    setSelectedForm(form);
    loadFormAnalytics(form.id);
    onFormSelect(form.id, form);
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" flexDirection="column" alignItems="center" py={4}>
            <CircularProgress size={40} />
            <Typography variant="body2" sx={{ mt: 2 }}>
              Checking Google Forms authorization...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!isAuthorized) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" flexDirection="column" alignItems="center" py={4}>
            <Google sx={{ fontSize: 48, color: "#4285f4", mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Connect to Google Forms
            </Typography>
            <Typography
              variant="body2"
              color="textSecondary"
              textAlign="center"
              sx={{ mb: 3 }}
            >
              Authorize access to your Google Forms to import and analyze form
              responses
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2, width: "100%" }}>
                {error}
              </Alert>
            )}

            <Button
              variant="contained"
              size="large"
              onClick={handleAuthorize}
              startIcon={<Google />}
              sx={{
                bgcolor: "#4285f4",
                "&:hover": { bgcolor: "#3367d6" },
                px: 4,
                py: 1.5,
              }}
            >
              Authorize Google Forms
            </Button>

            <Typography variant="caption" color="textSecondary" sx={{ mt: 2 }}>
              You'll be redirected to Google to grant permissions
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          mb={2}
        >
          <Typography variant="h6" display="flex" alignItems="center" gap={1}>
            <Google sx={{ color: "#4285f4" }} />
            Google Forms
          </Typography>
          <Tooltip title="Refresh forms list">
            <IconButton
              onClick={refreshForms}
              disabled={isRefreshing}
              size="small"
            >
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {isRefreshing && <LinearProgress sx={{ mb: 2 }} />}

        {forms.length === 0 ? (
          <Alert severity="info">
            No Google Forms found. Create some forms in Google Forms first.
          </Alert>
        ) : (
          <>
            <TextField
              select
              fullWidth
              label="Select Google Form"
              value={selectedForm?.id || ""}
              onChange={(e: any) => {
                const form = forms.find((f: any) => f.id === e.target.value);
                if (form) handleFormSelect(form);
              }}
              variant="outlined"
              sx={{ mb: 2 }}
            >
              <MenuItem value="">
                <em>Choose a form to analyze...</em>
              </MenuItem>
              {forms.map((form: any) => (
                <MenuItem key={form.id} value={form.id}>
                  <Box
                    display="flex"
                    justifyContent="space-between"
                    width="100%"
                  >
                    <Typography variant="body2">{form.title}</Typography>
                    <Chip
                      label={`${form.responseCount} responses`}
                      size="small"
                      color={form.responseCount > 0 ? "success" : "default"}
                    />
                  </Box>
                </MenuItem>
              ))}
            </TextField>

            {selectedForm && (
              <Card variant="outlined" sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {selectedForm.title}
                  </Typography>

                  {selectedForm.description && (
                    <Typography
                      variant="body2"
                      color="textSecondary"
                      sx={{ mb: 2 }}
                    >
                      {selectedForm.description}
                    </Typography>
                  )}

                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Box textAlign="center">
                        <Typography variant="h6" color="primary">
                          {selectedForm.responseCount}
                        </Typography>
                        <Typography variant="caption">Responses</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box textAlign="center">
                        <Typography variant="body2" color="textSecondary">
                          {new Date(
                            selectedForm.createdTime
                          ).toLocaleDateString()}
                        </Typography>
                        <Typography variant="caption">Created</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box textAlign="center">
                        <Typography variant="body2" color="textSecondary">
                          {new Date(
                            selectedForm.lastModifiedTime
                          ).toLocaleDateString()}
                        </Typography>
                        <Typography variant="caption">Modified</Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box textAlign="center">
                        <CheckCircle sx={{ color: "success.main" }} />
                        <Typography variant="caption">Connected</Typography>
                      </Box>
                    </Grid>
                  </Grid>

                  {formAnalytics && (
                    <Box
                      sx={{
                        mt: 2,
                        pt: 2,
                        borderTop: 1,
                        borderColor: "divider",
                      }}
                    >
                      <Typography variant="subtitle2" gutterBottom>
                        📊 Quick Analytics
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={4}>
                          <Box textAlign="center">
                            <Typography variant="h6" color="primary">
                              {formAnalytics.totalResponses}
                            </Typography>
                            <Typography variant="caption">
                              Total Responses
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={4}>
                          <Box textAlign="center">
                            <Typography variant="h6" color="primary">
                              {formAnalytics.responseRate.toFixed(1)}%
                            </Typography>
                            <Typography variant="caption">
                              Response Rate
                            </Typography>
                          </Box>
                        </Grid>
                        <Grid item xs={4}>
                          <Box textAlign="center">
                            <Typography variant="h6" color="primary">
                              {Math.round(formAnalytics.averageCompletionTime)}s
                            </Typography>
                            <Typography variant="caption">Avg. Time</Typography>
                          </Box>
                        </Grid>
                      </Grid>
                    </Box>
                  )}
                </CardContent>
              </Card>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default GoogleFormsImport;
