import { useState, useEffect, useContext, useCallback } from "react";
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Switch,
  FormControlLabel,
  Box,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import {
  Public,
  VisibilityOff,
  PlayArrow,
  Pause,
  Refresh,
  Info,
  OpenInNew,
} from "@mui/icons-material";
import { AuthContext } from "../../context/AuthContext";
import { formBuilderAPI, type Form } from "../../services/formBuilder";

// External form interface to match the one from FormBuilderAdmin
interface ExternalForm {
  id: string;
  title: string;
  url: string;
  description?: string;
  createdAt: Date;
  qrCode?: string;
}

interface FormStatusManagerProps {
  onRefresh?: () => void;
  externalForms?: ExternalForm[];
}

// Extended form type that can handle both backend and external forms
interface ExtendedForm {
  id: string;
  title: string;
  description?: string;
  is_external?: boolean;
  external_url?: string;
  created_at?: string;
  updated_at?: string;
  creator_name?: string;
  is_public?: boolean;
  is_active?: boolean;
  submission_count?: number;
}

export default function FormStatusManager({
  onRefresh,
  externalForms = [],
}: FormStatusManagerProps) {
  const [combinedForms, setCombinedForms] = useState<ExtendedForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updating, setUpdating] = useState<string | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedForm, setSelectedForm] = useState<ExtendedForm | null>(null);

  // Get auth context for user authentication state
  const { user, accessToken } = useContext(AuthContext);

  const fetchForms = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      let backendFormsData: ExtendedForm[] = [];

      // Check if user is authenticated before fetching backend forms
      if (user && accessToken) {
        try {
          // Use the formBuilder service which handles auth automatically
          const data = await formBuilderAPI.getForms({
            page: 1,
            limit: 100, // Get more forms for status management
          });

          console.log("Backend forms fetched:", data);

          // Handle different response formats and convert to ExtendedForm
          const formsData = data.forms || data || [];
          backendFormsData = Array.isArray(formsData)
            ? formsData.map((form: Form) => ({
                id: form.id.toString(),
                title: form.title,
                description: form.description,
                created_at: form.created_at,
                updated_at: form.updated_at,
                creator_name: form.creator_name,
                is_public: form.is_public,
                is_active: form.is_active,
                submission_count: form.submission_count,
                is_external: false,
              }))
            : [];
        } catch (backendError) {
          console.error("Error fetching backend forms:", backendError);
          // Don't throw error, just continue with external forms
        }
      }

      // Convert external forms to ExtendedForm format
      const externalFormsData: ExtendedForm[] = externalForms.map((form) => ({
        id: `external_${form.id}`,
        title: form.title,
        description: form.description,
        external_url: form.url,
        created_at:
          form.createdAt instanceof Date
            ? form.createdAt.toISOString()
            : new Date(form.createdAt).toISOString(),
        is_external: true,
        is_public: true, // External forms are considered public since they have URLs
        is_active: true, // External forms are considered active
      }));

      // Combine backend and external forms
      const combined = [...backendFormsData, ...externalFormsData];
      setCombinedForms(combined);
    } catch (err) {
      console.error("Error in fetchForms:", err);
      if (err instanceof Error) {
        // Handle specific error cases
        if (err.message.includes("401") || err.message.includes("403")) {
          setError("Session expired. Please log in again.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Failed to fetch forms");
      }
    } finally {
      setLoading(false);
    }
  }, [user, accessToken, externalForms]);

  const toggleFormStatus = async (
    formId: string,
    field: "is_public" | "is_active",
    newValue: boolean
  ) => {
    try {
      setUpdating(formId);

      // Check if this is an external form
      if (formId.startsWith("external_")) {
        setError("Cannot toggle status for external forms");
        return;
      }

      // Check if user is authenticated
      if (!user || !accessToken) {
        setError("Please log in to update form status");
        return;
      }

      // Use the formBuilder service which handles auth automatically
      const data = await formBuilderAPI.toggleFormStatus(Number(formId), {
        [field]: newValue,
      });

      console.log("Form status updated:", data);

      // Update local state
      setCombinedForms((prevForms) =>
        prevForms.map((form) =>
          form.id === formId
            ? {
                ...form,
                [field]: newValue,
                updated_at: new Date().toISOString(),
              }
            : form
        )
      );

      // Call parent refresh if available
      if (onRefresh) {
        onRefresh();
      }
    } catch (err) {
      console.error("Error updating form status:", err);
      if (err instanceof Error) {
        // Handle specific error cases
        if (err.message.includes("401") || err.message.includes("403")) {
          setError(
            "Session expired or insufficient permissions. Please log in again."
          );
        } else {
          setError(err.message);
        }
      } else {
        setError("Failed to update form status");
      }
    } finally {
      setUpdating(null);
    }
  };

  const getStatusColor = (form: ExtendedForm) => {
    if (form.is_external) return "info"; // Blue for external forms
    if (form.is_public && form.is_active) return "success";
    if (!form.is_active) return "error";
    if (!form.is_public) return "warning";
    return "default";
  };

  const getStatusText = (form: ExtendedForm) => {
    if (form.is_external) return "External";
    if (form.is_public && form.is_active) return "Live";
    if (!form.is_active) return "Inactive";
    if (!form.is_public) return "Private";
    return "Unknown";
  };

  const openDetails = (form: ExtendedForm) => {
    setSelectedForm(form);
    setDetailsOpen(true);
  };

  useEffect(() => {
    fetchForms();
  }, [fetchForms]);

  // Show login prompt if user is not authenticated
  if (!user || !accessToken) {
    return (
      <Box sx={{ textAlign: "center", py: 4 }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          Please log in to view and manage form status
        </Alert>
        <Typography variant="body2" color="text.secondary">
          You need to be authenticated to access the form management features.
        </Typography>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          py: 4,
        }}
      >
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading forms...</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography variant="h6">Form Status Management</Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={fetchForms}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2}>
        {combinedForms.map((form) => (
          <Grid item xs={12} md={6} lg={4} key={form.id}>
            <Card sx={{ height: "100%", position: "relative" }}>
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    mb: 2,
                  }}
                >
                  <Typography
                    variant="h6"
                    component="h3"
                    sx={{ flexGrow: 1, mr: 1 }}
                  >
                    {form.title}
                  </Typography>
                  <Chip
                    label={getStatusText(form)}
                    color={getStatusColor(form)}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Box>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2, minHeight: 40 }}
                >
                  {form.description || "No description provided"}
                </Typography>

                {/* Show toggle switches for all forms, disable for external ones */}
                <Box sx={{ mb: 2 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.is_public}
                        onChange={(e) =>
                          form.is_external
                            ? undefined
                            : toggleFormStatus(
                                form.id,
                                "is_public",
                                e.target.checked
                              )
                        }
                        disabled={updating === form.id || form.is_external}
                        color="primary"
                      />
                    }
                    label={
                      <Box
                        sx={{ display: "flex", alignItems: "center", gap: 1 }}
                      >
                        {form.is_public ? (
                          <Public fontSize="small" />
                        ) : (
                          <VisibilityOff fontSize="small" />
                        )}
                        Public
                        {form.is_external && (
                          <Tooltip title="External forms are always public">
                            <Info
                              fontSize="small"
                              sx={{ color: "text.secondary", ml: 0.5 }}
                            />
                          </Tooltip>
                        )}
                      </Box>
                    }
                  />
                </Box>

                <Box sx={{ mb: 2 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.is_active}
                        onChange={(e) =>
                          form.is_external
                            ? undefined
                            : toggleFormStatus(
                                form.id,
                                "is_active",
                                e.target.checked
                              )
                        }
                        disabled={updating === form.id || form.is_external}
                        color="success"
                      />
                    }
                    label={
                      <Box
                        sx={{ display: "flex", alignItems: "center", gap: 1 }}
                      >
                        {form.is_active ? (
                          <PlayArrow fontSize="small" />
                        ) : (
                          <Pause fontSize="small" />
                        )}
                        Active
                        {form.is_external && (
                          <Tooltip title="External forms are always active">
                            <Info
                              fontSize="small"
                              sx={{ color: "text.secondary", ml: 0.5 }}
                            />
                          </Tooltip>
                        )}
                      </Box>
                    }
                  />
                </Box>

                {/* Show external form URL for external forms */}
                {form.is_external && form.external_url && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      External URL:
                    </Typography>
                    <Typography
                      variant="body2"
                      sx={{
                        wordBreak: "break-all",
                        fontSize: "0.85rem",
                        color: "primary.main",
                      }}
                    >
                      {form.external_url}
                    </Typography>
                  </Box>
                )}

                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {form.is_external
                      ? "External Form"
                      : `${form.submission_count || 0} submissions`}
                  </Typography>
                  <Box>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => openDetails(form)}
                      >
                        <Info />
                      </IconButton>
                    </Tooltip>
                    {/* Show different buttons for external vs backend forms */}
                    {form.is_external && form.external_url ? (
                      <Tooltip title="Open External Form">
                        <IconButton
                          size="small"
                          onClick={() =>
                            window.open(form.external_url, "_blank")
                          }
                        >
                          <OpenInNew />
                        </IconButton>
                      </Tooltip>
                    ) : (
                      form.is_public &&
                      form.is_active && (
                        <Tooltip title="View Public Form">
                          <IconButton
                            size="small"
                            onClick={() =>
                              window.open(`/public-forms`, "_blank")
                            }
                          >
                            <OpenInNew />
                          </IconButton>
                        </Tooltip>
                      )
                    )}
                  </Box>
                </Box>

                {updating === form.id && (
                  <Box
                    sx={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      right: 0,
                      bottom: 0,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: "rgba(255, 255, 255, 0.8)",
                      borderRadius: 1,
                    }}
                  >
                    <CircularProgress size={24} />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {combinedForms.length === 0 && !loading && (
        <Box sx={{ textAlign: "center", py: 4 }}>
          <Typography variant="h6" color="text.secondary">
            No forms found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create your first form to get started
          </Typography>
        </Box>
      )}

      {/* Form Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Form Details</DialogTitle>
        <DialogContent>
          {selectedForm && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedForm.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {selectedForm.description || "No description provided"}
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2">Status:</Typography>
                <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
                  {selectedForm.is_external && (
                    <Chip label="External" color="info" size="small" />
                  )}
                  <Chip
                    label={selectedForm.is_public ? "Public" : "Private"}
                    color={selectedForm.is_public ? "primary" : "default"}
                    size="small"
                  />
                  <Chip
                    label={selectedForm.is_active ? "Active" : "Inactive"}
                    color={selectedForm.is_active ? "success" : "error"}
                    size="small"
                  />
                </Box>
              </Box>

              {/* Show external URL if it's an external form */}
              {selectedForm.is_external && selectedForm.external_url && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">External URL:</Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      wordBreak: "break-all",
                      color: "primary.main",
                      cursor: "pointer",
                    }}
                    onClick={() =>
                      window.open(selectedForm.external_url, "_blank")
                    }
                  >
                    {selectedForm.external_url}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2">Statistics:</Typography>
                {!selectedForm.is_external && (
                  <Typography variant="body2">
                    Submissions: {selectedForm.submission_count || 0}
                  </Typography>
                )}
                <Typography variant="body2">
                  Created:{" "}
                  {selectedForm.created_at
                    ? new Date(selectedForm.created_at).toLocaleDateString()
                    : "Unknown"}
                </Typography>
                <Typography variant="body2">
                  Last Updated:{" "}
                  {selectedForm.updated_at
                    ? new Date(selectedForm.updated_at).toLocaleDateString()
                    : "Unknown"}
                </Typography>
                {selectedForm.creator_name && (
                  <Typography variant="body2">
                    Creator: {selectedForm.creator_name}
                  </Typography>
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
