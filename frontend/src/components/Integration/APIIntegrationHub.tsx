import React, { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Alert,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  CircularProgress,
  Tooltip,
  IconButton,
} from "@mui/material";
import {
  Google as GoogleIcon,
  Microsoft as MicrosoftIcon,
  CloudUpload,
  Description,
  TableChart,
  Share,
  Refresh,
  Settings,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";

// Types
interface IntegrationService {
  id: string;
  name: string;
  icon: React.ReactNode;
  status: "connected" | "disconnected" | "error";
  lastSync?: string;
  metrics?: {
    totalRequests: number;
    successRate: number;
    lastUsed: string;
  };
}

interface ExportOption {
  service: string;
  format: string;
  templateId?: string;
  includeResponses: boolean;
}

interface ShareSettings {
  recipients: string[];
  permissionLevel: "read" | "write" | "comment";
  message: string;
}

// Styled Components
const IntegrationCard = styled(Card)(({ theme }) => ({
  position: "relative",
  transition: "all 0.3s ease-in-out",
  "&:hover": {
    transform: "translateY(-4px)",
    boxShadow: theme.shadows[8],
  },
}));

const StatusIndicator = styled(Box)<{ status: string }>(
  ({ status, theme }) => ({
    position: "absolute",
    top: 16,
    right: 16,
    width: 12,
    height: 12,
    borderRadius: "50%",
    backgroundColor:
      status === "connected"
        ? theme.palette.success.main
        : status === "error"
        ? theme.palette.error.main
        : theme.palette.grey[400],
  })
);

const MetricBox = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.grey[50],
  borderRadius: theme.shape.borderRadius,
  textAlign: "center",
  marginTop: theme.spacing(2),
}));

export const APIIntegrationHub: React.FC = () => {
  // State Management
  const [services, setServices] = useState<IntegrationService[]>([
    {
      id: "google_sheets",
      name: "Google Sheets",
      icon: <GoogleIcon />,
      status: "disconnected",
      metrics: {
        totalRequests: 0,
        successRate: 0,
        lastUsed: "Never",
      },
    },
    {
      id: "microsoft_graph",
      name: "Microsoft Word",
      icon: <MicrosoftIcon />,
      status: "disconnected",
      metrics: {
        totalRequests: 0,
        successRate: 0,
        lastUsed: "Never",
      },
    },
  ]);

  const [loading, setLoading] = useState<{ [key: string]: boolean }>({});
  const [exportDialog, setExportDialog] = useState(false);
  const [shareDialog, setShareDialog] = useState(false);
  const [selectedFormId, setSelectedFormId] = useState<number | null>(null);
  const [exportOptions, setExportOptions] = useState<ExportOption>({
    service: "google_sheets",
    format: "spreadsheet",
    includeResponses: true,
  });
  const [shareSettings, setShareSettings] = useState<ShareSettings>({
    recipients: [],
    permissionLevel: "read",
    message: "",
  });
  const [alerts, setAlerts] = useState<
    Array<{ type: "success" | "error" | "info"; message: string }>
  >([]);

  // API Functions
  const connectService = async (serviceId: string) => {
    setLoading((prev) => ({ ...prev, [serviceId]: true }));

    try {
      // Get authorization URL
      const authResponse = await fetch(
        `/api/v1/integrations/${serviceId}/auth-url?redirect_uri=${encodeURIComponent(
          window.location.origin + "/auth/callback"
        )}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!authResponse.ok) throw new Error("Failed to get authorization URL");

      const authData = await authResponse.json();

      // Store code verifier for Microsoft Graph
      if (serviceId === "microsoft" && authData.code_verifier) {
        localStorage.setItem("ms_code_verifier", authData.code_verifier);
      }

      // Redirect to authorization URL
      window.location.href = authData.authorization_url;
    } catch (error) {
      console.error("Connection failed:", error);
      setAlerts((prev) => [
        ...prev,
        { type: "error", message: `Failed to connect to ${serviceId}` },
      ]);
    } finally {
      setLoading((prev) => ({ ...prev, [serviceId]: false }));
    }
  };

  const disconnectService = async (serviceId: string) => {
    setLoading((prev) => ({ ...prev, [serviceId]: true }));

    try {
      // Clear tokens and update status
      setServices((prev) =>
        prev.map((service) =>
          service.id === serviceId
            ? {
                ...service,
                status: "disconnected" as const,
                lastSync: undefined,
              }
            : service
        )
      );

      setAlerts((prev) => [
        ...prev,
        { type: "info", message: `Disconnected from ${serviceId}` },
      ]);
    } catch (error) {
      console.error("Disconnection failed:", error);
      setAlerts((prev) => [
        ...prev,
        { type: "error", message: `Failed to disconnect from ${serviceId}` },
      ]);
    } finally {
      setLoading((prev) => ({ ...prev, [serviceId]: false }));
    }
  };

  const exportFormData = async () => {
    if (!selectedFormId) return;

    setLoading((prev) => ({ ...prev, export: true }));

    try {
      const response = await fetch("/api/v1/integrations/export/form", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          form_id: selectedFormId,
          target_service: exportOptions.service,
          template_id: exportOptions.templateId,
          include_responses: exportOptions.includeResponses,
        }),
      });

      if (!response.ok) throw new Error("Export failed");

      await response.json(); // Process the result

      setAlerts((prev) => [
        ...prev,
        {
          type: "success",
          message: `Form exported successfully to ${exportOptions.service}`,
        },
      ]);

      setExportDialog(false);
    } catch (error) {
      console.error("Export failed:", error);
      setAlerts((prev) => [
        ...prev,
        { type: "error", message: "Export failed" },
      ]);
    } finally {
      setLoading((prev) => ({ ...prev, export: false }));
    }
  };

  const shareDocument = async (documentId: string) => {
    setLoading((prev) => ({ ...prev, share: true }));

    try {
      const response = await fetch(
        "/api/v1/integrations/microsoft/documents/share",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({
            document_id: documentId,
            recipients: shareSettings.recipients,
            permission_level: shareSettings.permissionLevel,
            message: shareSettings.message,
          }),
        }
      );

      if (!response.ok) throw new Error("Sharing failed");

      await response.json(); // Process the result

      setAlerts((prev) => [
        ...prev,
        {
          type: "success",
          message: `Document shared with ${shareSettings.recipients.length} recipients`,
        },
      ]);

      setShareDialog(false);
    } catch (error) {
      console.error("Sharing failed:", error);
      setAlerts((prev) => [
        ...prev,
        { type: "error", message: "Document sharing failed" },
      ]);
    } finally {
      setLoading((prev) => ({ ...prev, share: false }));
    }
  };

  const refreshMetrics = async () => {
    try {
      const [googleMetrics, microsoftMetrics] = await Promise.all([
        fetch("/api/v1/integrations/metrics/google-sheets", {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        })
          .then((res) => res.json())
          .catch(() => null),
        fetch("/api/v1/integrations/metrics/microsoft-graph", {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        })
          .then((res) => res.json())
          .catch(() => null),
      ]);

      setServices((prev) =>
        prev.map((service) => {
          if (service.id === "google_sheets" && googleMetrics) {
            return {
              ...service,
              metrics: {
                totalRequests: googleMetrics.metrics.total_requests,
                successRate: googleMetrics.metrics.success_rate,
                lastUsed: googleMetrics.timestamp,
              },
            };
          }
          if (service.id === "microsoft_graph" && microsoftMetrics) {
            return {
              ...service,
              metrics: {
                totalRequests: microsoftMetrics.metrics.total_requests,
                successRate: microsoftMetrics.metrics.success_rate,
                lastUsed: microsoftMetrics.timestamp,
              },
            };
          }
          return service;
        })
      );
    } catch (error) {
      console.error("Failed to refresh metrics:", error);
    }
  };

  // Effects
  useEffect(() => {
    refreshMetrics();
    const interval = setInterval(refreshMetrics, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Handle OAuth callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const state = urlParams.get("state");
    const error = urlParams.get("error");

    if (error) {
      setAlerts((prev) => [
        ...prev,
        { type: "error", message: `OAuth error: ${error}` },
      ]);
      return;
    }

    if (code && state) {
      // Handle OAuth callback
      const handleOAuthCallback = async () => {
        try {
          const serviceId = state.includes("google") ? "google" : "microsoft";
          const codeVerifier = localStorage.getItem("ms_code_verifier");

          const response = await fetch(
            `/api/v1/integrations/${serviceId}/authenticate`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${localStorage.getItem("token")}`,
              },
              body: JSON.stringify({
                authorization_code: code,
                redirect_uri: window.location.origin + "/auth/callback",
                ...(serviceId === "microsoft" && {
                  code_verifier: codeVerifier,
                }),
              }),
            }
          );

          if (!response.ok) throw new Error("Authentication failed");

          // Update service status
          setServices((prev) =>
            prev.map((service) =>
              service.id ===
              `${serviceId}_${serviceId === "google" ? "sheets" : "graph"}`
                ? {
                    ...service,
                    status: "connected" as const,
                    lastSync: new Date().toISOString(),
                  }
                : service
            )
          );

          setAlerts((prev) => [
            ...prev,
            {
              type: "success",
              message: `Successfully connected to ${serviceId}`,
            },
          ]);

          // Clean up URL
          window.history.replaceState(
            {},
            document.title,
            window.location.pathname
          );

          // Clean up localStorage
          if (serviceId === "microsoft") {
            localStorage.removeItem("ms_code_verifier");
          }
        } catch (error) {
          console.error("OAuth callback failed:", error);
          setAlerts((prev) => [
            ...prev,
            { type: "error", message: "Authentication failed" },
          ]);
        }
      };

      handleOAuthCallback();
    }
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        sx={{
          mb: 4,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h4" component="h1" fontWeight="bold">
          API Integration Hub
        </Typography>
        <Button
          startIcon={<Refresh />}
          onClick={refreshMetrics}
          variant="outlined"
        >
          Refresh Metrics
        </Button>
      </Box>

      {/* Alerts */}
      {alerts.map((alert, index) => (
        <Alert
          key={index}
          severity={alert.type}
          sx={{ mb: 2 }}
          onClose={() =>
            setAlerts((prev) => prev.filter((_, i) => i !== index))
          }
        >
          {alert.message}
        </Alert>
      ))}

      {/* Integration Services */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {services.map((service) => (
          <Grid item xs={12} md={6} key={service.id}>
            <IntegrationCard>
              <StatusIndicator status={service.status} />
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                  {service.icon}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {service.name}
                  </Typography>
                  <Chip
                    label={service.status}
                    color={
                      service.status === "connected" ? "success" : "default"
                    }
                    size="small"
                    sx={{ ml: "auto" }}
                  />
                </Box>

                {service.metrics && (
                  <MetricBox>
                    <Grid container spacing={2}>
                      <Grid item xs={4}>
                        <Typography variant="h6" color="primary">
                          {service.metrics.totalRequests}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Total Requests
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="h6" color="success.main">
                          {service.metrics.successRate.toFixed(1)}%
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Success Rate
                        </Typography>
                      </Grid>
                      <Grid item xs={4}>
                        <Typography variant="body2" color="textSecondary">
                          Last Used:{" "}
                          {service.metrics.lastUsed === "Never"
                            ? "Never"
                            : new Date(
                                service.metrics.lastUsed
                              ).toLocaleDateString()}
                        </Typography>
                      </Grid>
                    </Grid>
                  </MetricBox>
                )}

                <Box sx={{ mt: 3, display: "flex", gap: 1 }}>
                  {service.status === "connected" ? (
                    <>
                      <Button
                        variant="outlined"
                        color="error"
                        onClick={() => disconnectService(service.id)}
                        disabled={loading[service.id]}
                        startIcon={
                          loading[service.id] ? (
                            <CircularProgress size={16} />
                          ) : undefined
                        }
                      >
                        Disconnect
                      </Button>
                      <Tooltip title="Configure integration settings">
                        <IconButton>
                          <Settings />
                        </IconButton>
                      </Tooltip>
                    </>
                  ) : (
                    <Button
                      variant="contained"
                      onClick={() => connectService(service.id)}
                      disabled={loading[service.id]}
                      startIcon={
                        loading[service.id] ? (
                          <CircularProgress size={16} />
                        ) : undefined
                      }
                      fullWidth
                    >
                      Connect
                    </Button>
                  )}
                </Box>
              </CardContent>
            </IntegrationCard>
          </Grid>
        ))}
      </Grid>

      {/* Quick Actions */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<CloudUpload />}
                onClick={() => setExportDialog(true)}
                disabled={!services.some((s) => s.status === "connected")}
              >
                Export Form Data
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Description />}
                disabled={
                  !services.find((s) => s.id === "microsoft_graph")?.status
                }
              >
                Create Document
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<TableChart />}
                disabled={
                  !services.find((s) => s.id === "google_sheets")?.status
                }
              >
                Create Spreadsheet
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                variant="outlined"
                fullWidth
                startIcon={<Share />}
                onClick={() => setShareDialog(true)}
                disabled={!services.some((s) => s.status === "connected")}
              >
                Share Document
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Export Dialog */}
      <Dialog
        open={exportDialog}
        onClose={() => setExportDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Export Form Data</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 3, mt: 2 }}>
            <TextField
              label="Form ID"
              type="number"
              value={selectedFormId || ""}
              onChange={(e) => setSelectedFormId(Number(e.target.value))}
              fullWidth
              required
            />

            <FormControl fullWidth>
              <InputLabel>Export Service</InputLabel>
              <Select
                value={exportOptions.service}
                label="Export Service"
                onChange={(e) =>
                  setExportOptions((prev) => ({
                    ...prev,
                    service: e.target.value,
                  }))
                }
              >
                <MenuItem value="google_sheets">Google Sheets</MenuItem>
                <MenuItem value="microsoft_word">Microsoft Word</MenuItem>
              </Select>
            </FormControl>

            {exportOptions.service === "microsoft_word" && (
              <TextField
                label="Template ID (Optional)"
                value={exportOptions.templateId || ""}
                onChange={(e) =>
                  setExportOptions((prev) => ({
                    ...prev,
                    templateId: e.target.value,
                  }))
                }
                fullWidth
                helperText="Leave blank to create document from scratch"
              />
            )}

            <FormControlLabel
              control={
                <Switch
                  checked={exportOptions.includeResponses}
                  onChange={(e) =>
                    setExportOptions((prev) => ({
                      ...prev,
                      includeResponses: e.target.checked,
                    }))
                  }
                />
              }
              label="Include Form Responses"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>Cancel</Button>
          <Button
            onClick={exportFormData}
            variant="contained"
            disabled={!selectedFormId || loading.export}
            startIcon={
              loading.export ? <CircularProgress size={16} /> : <CloudUpload />
            }
          >
            Export
          </Button>
        </DialogActions>
      </Dialog>

      {/* Share Dialog */}
      <Dialog
        open={shareDialog}
        onClose={() => setShareDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Share Document</DialogTitle>
        <DialogContent>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 3, mt: 2 }}>
            <TextField
              label="Recipients (comma-separated emails)"
              value={shareSettings.recipients.join(", ")}
              onChange={(e) =>
                setShareSettings((prev) => ({
                  ...prev,
                  recipients: e.target.value
                    .split(",")
                    .map((email) => email.trim())
                    .filter(Boolean),
                }))
              }
              fullWidth
              multiline
              rows={2}
            />

            <FormControl fullWidth>
              <InputLabel>Permission Level</InputLabel>
              <Select
                value={shareSettings.permissionLevel}
                label="Permission Level"
                onChange={(e) =>
                  setShareSettings((prev) => ({
                    ...prev,
                    permissionLevel: e.target.value as
                      | "read"
                      | "write"
                      | "comment",
                  }))
                }
              >
                <MenuItem value="read">Read Only</MenuItem>
                <MenuItem value="comment">Comment</MenuItem>
                <MenuItem value="write">Edit</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Message (Optional)"
              value={shareSettings.message}
              onChange={(e) =>
                setShareSettings((prev) => ({
                  ...prev,
                  message: e.target.value,
                }))
              }
              fullWidth
              multiline
              rows={3}
              placeholder="Add a personal message..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialog(false)}>Cancel</Button>
          <Button
            onClick={() => shareDocument("sample-doc-id")}
            variant="contained"
            disabled={shareSettings.recipients.length === 0 || loading.share}
            startIcon={
              loading.share ? <CircularProgress size={16} /> : <Share />
            }
          >
            Share
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
