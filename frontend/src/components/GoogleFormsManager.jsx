import React, { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  FormControlLabel,
  TextField,
  MenuItem,
  Divider,
} from "@mui/material";
import {
  Assignment as FormIcon,
  CloudDownload as DownloadIcon,
  Visibility as PreviewIcon,
  Analytics as AnalyticsIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from "@mui/icons-material";
import { useAuth } from "../context/AuthContext";
import { googleFormsService } from "../services/googleFormsService";

const GoogleFormsManager = () => {
  const { user } = useAuth();
  const [forms, setForms] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [selectedForms, setSelectedForms] = useState(new Set());
  const [authStatus, setAuthStatus] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Report generation states
  const [reportDialog, setReportDialog] = useState(false);
  const [reportConfig, setReportConfig] = useState({
    format: "pdf",
    include_charts: true,
    include_ai_analysis: true,
    title: "",
    description: "",
  });
  const [generatingReports, setGeneratingReports] = useState(false);
  const [reportResults, setReportResults] = useState([]);

  useEffect(() => {
    checkAuthorizationStatus();
  }, []);

  const checkAuthorizationStatus = async () => {
    try {
      setLoading(true);
      const response = await googleFormsService.getAuthorizationStatus();

      setIsAuthorized(response.is_authorized);
      setAuthStatus(response);

      if (response.is_authorized) {
        await fetchUserForms();
      }
    } catch (error) {
      console.error("Error checking authorization:", error);
      setError("Failed to check Google Forms authorization status");
    } finally {
      setLoading(false);
    }
  };

  const fetchUserForms = async () => {
    try {
      setLoading(true);
      const response = await googleFormsService.getUserForms(20);

      if (response.success) {
        setForms(response.forms);
        setSuccess(`Found ${response.forms.length} Google Forms`);
      } else {
        throw new Error(response.error);
      }
    } catch (error) {
      console.error("Error fetching forms:", error);
      setError(
        "Failed to fetch Google Forms. Please check your authorization."
      );
      setIsAuthorized(false);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuthorization = async () => {
    try {
      setLoading(true);
      const response = await googleFormsService.initiateAuth();

      if (response.success) {
        // Open Google authorization in new window
        const authWindow = window.open(
          response.authorization_url,
          "google-auth",
          "width=500,height=600,scrollbars=yes,resizable=yes"
        );

        // Listen for the authorization completion
        const checkClosed = setInterval(() => {
          if (authWindow.closed) {
            clearInterval(checkClosed);
            // Check if authorization was successful
            setTimeout(() => {
              checkAuthorizationStatus();
            }, 1000);
          }
        }, 1000);
      }
    } catch (error) {
      console.error("Error initiating authorization:", error);
      setError("Failed to initiate Google authorization");
    } finally {
      setLoading(false);
    }
  };

  const handleFormSelection = (formId) => {
    const newSelected = new Set(selectedForms);
    if (newSelected.has(formId)) {
      newSelected.delete(formId);
    } else {
      newSelected.add(formId);
    }
    setSelectedForms(newSelected);
  };

  const previewFormData = async (formId) => {
    try {
      setLoading(true);
      const response = await googleFormsService.previewReportData(formId);

      if (response.success) {
        const preview = response.preview;
        alert(
          `Form: ${preview.form_info.title}\nResponses: ${
            preview.response_count
          }\nCompletion Rate: ${preview.completion_stats.completion_rate?.toFixed(
            1
          )}%`
        );
      }
    } catch (error) {
      setError("Failed to preview form data");
    } finally {
      setLoading(false);
    }
  };

  const generateReportsForSelectedForms = async () => {
    if (selectedForms.size === 0) {
      setError("Please select at least one form");
      return;
    }

    setGeneratingReports(true);
    setReportResults([]);
    const results = [];

    try {
      for (const formId of selectedForms) {
        const form = forms.find((f) => f.formId === formId);
        const config = {
          ...reportConfig,
          title:
            reportConfig.title ||
            `Automated Report - ${form?.info?.title || "Google Form"}`,
        };

        try {
          const response = await googleFormsService.generateAutomatedReport(
            formId,
            config
          );

          if (response.success) {
            results.push({
              formId,
              formTitle: form?.info?.title || "Unknown Form",
              success: true,
              reportId: response.report_id,
              downloadUrl: response.download_url,
              summary: response.summary,
            });
          } else {
            results.push({
              formId,
              formTitle: form?.info?.title || "Unknown Form",
              success: false,
              error: response.error,
            });
          }
        } catch (error) {
          results.push({
            formId,
            formTitle: form?.info?.title || "Unknown Form",
            success: false,
            error: "Failed to generate report",
          });
        }
      }

      setReportResults(results);
      const successCount = results.filter((r) => r.success).length;
      setSuccess(`Generated ${successCount} reports successfully`);
    } catch (error) {
      setError("Failed to generate reports");
    } finally {
      setGeneratingReports(false);
      setReportDialog(false);
    }
  };

  const downloadReport = async (downloadUrl) => {
    try {
      const blob = await googleFormsService.downloadReport(downloadUrl);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `google_forms_report_${Date.now()}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError("Failed to download report");
    }
  };

  if (loading && forms.length === 0) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Google Forms Integration
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess("")}>
          {success}
        </Alert>
      )}

      {/* Authorization Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Authorization Status
          </Typography>
          <Box display="flex" alignItems="center" gap={2}>
            {isAuthorized ? (
              <>
                <Chip
                  icon={<SuccessIcon />}
                  label="Authorized"
                  color="success"
                />
                <Typography variant="body2">
                  Connected to Google Forms ({authStatus?.forms_count || 0}{" "}
                  forms accessible)
                </Typography>
                <Button
                  variant="outlined"
                  onClick={fetchUserForms}
                  disabled={loading}
                >
                  Refresh Forms
                </Button>
              </>
            ) : (
              <>
                <Chip
                  icon={<ErrorIcon />}
                  label="Not Authorized"
                  color="error"
                />
                <Button
                  variant="contained"
                  onClick={handleGoogleAuthorization}
                  disabled={loading}
                >
                  Connect to Google Forms
                </Button>
              </>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Forms List */}
      {isAuthorized && (
        <>
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
            mb={2}
          >
            <Typography variant="h6">
              Available Forms ({forms.length})
            </Typography>
            <Box display="flex" gap={2}>
              <Button
                variant="outlined"
                onClick={() => setSelectedForms(new Set())}
                disabled={selectedForms.size === 0}
              >
                Clear Selection
              </Button>
              <Button
                variant="outlined"
                onClick={() =>
                  setSelectedForms(new Set(forms.map((f) => f.formId)))
                }
                disabled={forms.length === 0}
              >
                Select All
              </Button>
              <Button
                variant="contained"
                onClick={() => setReportDialog(true)}
                disabled={selectedForms.size === 0}
                startIcon={<AnalyticsIcon />}
              >
                Generate Reports ({selectedForms.size})
              </Button>
            </Box>
          </Box>

          <Grid container spacing={2}>
            {forms.map((form) => (
              <Grid item xs={12} md={6} lg={4} key={form.formId}>
                <Card
                  sx={{
                    height: "100%",
                    border: selectedForms.has(form.formId) ? 2 : 1,
                    borderColor: selectedForms.has(form.formId)
                      ? "primary.main"
                      : "divider",
                  }}
                >
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <FormIcon color="primary" />
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={selectedForms.has(form.formId)}
                            onChange={() => handleFormSelection(form.formId)}
                          />
                        }
                        label=""
                        sx={{ ml: "auto" }}
                      />
                    </Box>

                    <Typography variant="h6" gutterBottom noWrap>
                      {form.info?.title || "Untitled Form"}
                    </Typography>

                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2 }}
                    >
                      {form.info?.description || "No description available"}
                    </Typography>

                    <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                      {form.info?.linkedSheetId && (
                        <Chip
                          label="Linked to Sheets"
                          size="small"
                          color="info"
                        />
                      )}
                      <Chip
                        label={`ID: ${form.formId.substring(0, 8)}...`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>

                    <Box display="flex" gap={1}>
                      <Button
                        size="small"
                        startIcon={<PreviewIcon />}
                        onClick={() => previewFormData(form.formId)}
                        disabled={loading}
                      >
                        Preview
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() =>
                          window.open(
                            `https://docs.google.com/forms/d/${form.formId}/edit`,
                            "_blank"
                          )
                        }
                      >
                        Open in Google
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {forms.length === 0 && !loading && (
            <Box textAlign="center" py={4}>
              <Typography variant="body1" color="text.secondary">
                No Google Forms found. Make sure you have created forms in your
                Google account.
              </Typography>
            </Box>
          )}
        </>
      )}

      {/* Report Results */}
      {reportResults.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Generated Reports
            </Typography>
            <List>
              {reportResults.map((result, index) => (
                <ListItem
                  key={index}
                  divider={index < reportResults.length - 1}
                >
                  <ListItemIcon>
                    {result.success ? (
                      <SuccessIcon color="success" />
                    ) : (
                      <ErrorIcon color="error" />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={result.formTitle}
                    secondary={
                      result.success
                        ? `Report generated successfully - ${
                            result.summary?.total_responses || 0
                          } responses analyzed`
                        : `Error: ${result.error}`
                    }
                  />
                  {result.success && (
                    <Button
                      startIcon={<DownloadIcon />}
                      onClick={() => downloadReport(result.downloadUrl)}
                    >
                      Download PDF
                    </Button>
                  )}
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Report Configuration Dialog */}
      <Dialog
        open={reportDialog}
        onClose={() => setReportDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Configure Reports</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Report Title"
              value={reportConfig.title}
              onChange={(e) =>
                setReportConfig({ ...reportConfig, title: e.target.value })
              }
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Description"
              multiline
              rows={3}
              value={reportConfig.description}
              onChange={(e) =>
                setReportConfig({
                  ...reportConfig,
                  description: e.target.value,
                })
              }
              sx={{ mb: 2 }}
            />

            <TextField
              select
              fullWidth
              label="Format"
              value={reportConfig.format}
              onChange={(e) =>
                setReportConfig({ ...reportConfig, format: e.target.value })
              }
              sx={{ mb: 2 }}
            >
              <MenuItem value="pdf">PDF</MenuItem>
              <MenuItem value="docx">Word Document</MenuItem>
            </TextField>

            <FormControlLabel
              control={
                <Checkbox
                  checked={reportConfig.include_charts}
                  onChange={(e) =>
                    setReportConfig({
                      ...reportConfig,
                      include_charts: e.target.checked,
                    })
                  }
                />
              }
              label="Include Charts and Visualizations"
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={reportConfig.include_ai_analysis}
                  onChange={(e) =>
                    setReportConfig({
                      ...reportConfig,
                      include_ai_analysis: e.target.checked,
                    })
                  }
                />
              }
              label="Include AI-Powered Analysis"
            />

            <Divider sx={{ my: 2 }} />

            <Typography variant="body2" color="text.secondary">
              Will generate reports for {selectedForms.size} selected form(s)
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReportDialog(false)}>Cancel</Button>
          <Button
            onClick={generateReportsForSelectedForms}
            variant="contained"
            disabled={generatingReports}
            startIcon={
              generatingReports ? (
                <CircularProgress size={20} />
              ) : (
                <AnalyticsIcon />
              )
            }
          >
            {generatingReports ? "Generating..." : "Generate Reports"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default GoogleFormsManager;
