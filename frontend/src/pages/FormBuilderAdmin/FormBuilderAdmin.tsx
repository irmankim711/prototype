import React, { useState, useContext } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { formBuilderAPI, type Form } from "../../services/formBuilder";
import { AuthContext } from "../../context/AuthContext";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  IconButton,
  TextField,
  Tabs,
  Tab,
  Paper,
  Divider,
  Fab,
  Menu,
  MenuItem,
  Badge,
  Chip,
  FormControlLabel,
  Checkbox,
} from "@mui/material";
import {
  Add,
  Delete,
  Edit,
  Share,
  QrCode,
  Analytics,
  Launch,
  Storage,
  Settings,
  VpnKey,
  ContentCopy,
  Info,
} from "@mui/icons-material";

import FormBuilder from "../../components/FormBuilder/FormBuilder";
import SimpleQRGenerator from "../../components/forms/SimpleQRGenerator";
import FormStatusManager from "../../components/FormStatusManager/FormStatusManager";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`form-admin-tabpanel-${index}`}
      aria-labelledby={`form-admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

interface ExternalForm {
  id: string;
  title: string;
  url: string;
  description?: string;
  createdAt: Date;
  qrCode?: string;
}

interface AccessCode {
  id: number;
  code: string;
  title: string;
  description?: string;
  expires_at: string;
  max_uses: number;
  current_uses: number;
  is_active: boolean;
  allowed_form_ids: number[];
  allowed_external_forms: ExternalForm[];
  accessible_forms_count: number;
  access_url: string;
}

export default function FormBuilderAdmin() {
  // Authentication context
  const { user, accessToken, isLoading, login } = useContext(AuthContext);

  // Authentication state for login form
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState("");

  const [tabValue, setTabValue] = useState(0); // Default to External Forms tab (was My Forms)
  const [editingFormId, setEditingFormId] = useState<number | null>(null);
  const [showFormBuilder, setShowFormBuilder] = useState(false);

  // Dialog states
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [externalFormDialogOpen, setExternalFormDialogOpen] = useState(false);
  const [accessCodeDialogOpen, setAccessCodeDialogOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedForm, setSelectedForm] = useState<Form | null>(null);

  // Access code management
  const [accessCodes, setAccessCodes] = useState<AccessCode[]>([]);
  const [selectedFormForCode, setSelectedFormForCode] = useState<Form | null>(
    null
  );
  const [codeSettings, setCodeSettings] = useState({
    expires_in_hours: 24,
    max_uses: 1,
  });

  // Generic access code settings
  const [genericCodeSettings, setGenericCodeSettings] = useState({
    title: "",
    description: "",
    expires_in_hours: 24,
    max_uses: 10,
    selected_forms: [] as number[],
    selected_external_forms: [] as ExternalForm[],
  });

  // Form data states
  const [shareUrl, setShareUrl] = useState("");
  const [newExternalForm, setNewExternalForm] = useState({
    title: "",
    url: "",
    description: "",
  });

  // External forms stored in localStorage
  const [externalForms, setExternalForms] = useState<ExternalForm[]>(() => {
    const saved = localStorage.getItem("externalForms");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Convert createdAt strings back to Date objects
        return parsed.map(
          (form: Omit<ExternalForm, "createdAt"> & { createdAt: string }) => ({
            ...form,
            createdAt: new Date(form.createdAt),
          })
        );
      } catch (error) {
        console.error("Error parsing external forms from localStorage:", error);
        return [];
      }
    }
    return [];
  });

  // Notification state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success" as "success" | "error" | "warning" | "info",
  });

  // Commented out unused variables from My Forms functionality
  // const [page] = useState(1);
  const [page] = useState(1);

  // QR Code state
  const [showQRGenerator, setShowQRGenerator] = useState(false);

  // Forms query - needed for generic access codes
  const {
    data: formsData,
    isLoading: formsLoading,
    error: formsError,
    refetch,
  } = useQuery({
    queryKey: ["forms", page],
    queryFn: () => formBuilderAPI.getForms({ page, limit: 10 }),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const forms = formsData?.forms || [];

  // Delete form mutation
  const deleteMutation = useMutation({
    mutationFn: formBuilderAPI.deleteForm,
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: "Form deleted successfully!",
        severity: "success",
      });
      // refetch(); // Commented out since My Forms query is disabled
    },
    onError: () => {
      setSnackbar({
        open: true,
        message: "Failed to delete form",
        severity: "error",
      });
    },
  });

  // Handlers
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleNewForm = () => {
    setShowFormBuilder(true);
    setEditingFormId(null);
  };

  const handleEditForm = (form: Form) => {
    setShowFormBuilder(true);
    setEditingFormId(form.id);
  };

  const handleDeleteForm = (formId: number) => {
    if (
      window.confirm(
        "Are you sure you want to delete this form? This action cannot be undone."
      )
    ) {
      deleteMutation.mutate(formId);
    }
  };

  // Commented out unused My Forms functions
  /*
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, form: Form) => {
    setAnchorEl(event.currentTarget);
    setSelectedForm(form);
  };
  */

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedForm(null);
  };

  // This function is not used with My Forms but let's keep it for potential future use
  const handleShareForm = (form: Form) => {
    const url = `${window.location.origin}/forms/${form.id}`;
    setShareUrl(url);
    setShareDialogOpen(true);
    handleMenuClose();
  };

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setSnackbar({
      open: true,
      message: "Copied to clipboard!",
      severity: "success",
    });
  };

  // Access code handlers
  const handleGenerateAccessCode = () => {
    setAccessCodeDialogOpen(true);
  };

  const handleCreateGenericAccessCode = async () => {
    if (!genericCodeSettings.title.trim()) {
      setSnackbar({
        open: true,
        message: "Please enter a title for the access code",
        severity: "error",
      });
      return;
    }

    if (
      genericCodeSettings.selected_forms.length === 0 &&
      genericCodeSettings.selected_external_forms.length === 0
    ) {
      setSnackbar({
        open: true,
        message: "Please select at least one form",
        severity: "error",
      });
      return;
    }

    try {
      const payload = {
        title: genericCodeSettings.title,
        description: genericCodeSettings.description,
        expires_at: new Date(
          Date.now() + genericCodeSettings.expires_in_hours * 60 * 60 * 1000
        ).toISOString(),
        max_uses: genericCodeSettings.max_uses,
        allowed_form_ids: genericCodeSettings.selected_forms,
        allowed_external_forms: genericCodeSettings.selected_external_forms,
      };

      const response = await formBuilderAPI.createGenericAccessCode(payload);

      const newCode: AccessCode = {
        id: response.access_code.id,
        code: response.access_code.code,
        title: response.access_code.title,
        description: response.access_code.description,
        expires_at: response.access_code.expires_at,
        max_uses: response.access_code.max_uses,
        current_uses: response.access_code.current_uses,
        is_active: response.access_code.is_active,
        allowed_form_ids: response.access_code.allowed_form_ids,
        allowed_external_forms: response.access_code.allowed_external_forms,
        accessible_forms_count: response.access_code.accessible_forms_count,
        access_url: `${window.location.origin}/public-forms?code=${response.access_code.code}`,
      };

      setAccessCodes([...accessCodes, newCode]);
      setAccessCodeDialogOpen(false);

      // Reset form
      setGenericCodeSettings({
        title: "",
        description: "",
        expires_in_hours: 24,
        max_uses: 10,
        selected_forms: [],
        selected_external_forms: [],
      });

      setSnackbar({
        open: true,
        message: `Access code ${newCode.code} generated successfully!`,
        severity: "success",
      });
    } catch (error) {
      console.error("Error creating access code:", error);
      setSnackbar({
        open: true,
        message: "Failed to generate access code",
        severity: "error",
      });
    }
  };

  // Legacy function - keeping for backward compatibility
  const handleCreateAccessCode = async () => {
    if (!selectedFormForCode) return;

    try {
      // Convert to generic access code format
      const payload = {
        title: `Access to ${selectedFormForCode.title}`,
        description: `Generated access code for form: ${selectedFormForCode.title}`,
        expires_at: new Date(
          Date.now() + codeSettings.expires_in_hours * 60 * 60 * 1000
        ).toISOString(),
        max_uses: codeSettings.max_uses,
        allowed_form_ids: [selectedFormForCode.id],
        allowed_external_forms: [],
      };

      const response = await formBuilderAPI.createGenericAccessCode(payload);

      const newCode: AccessCode = {
        id: response.access_code.id,
        code: response.access_code.code,
        title: response.access_code.title,
        description: response.access_code.description,
        expires_at: response.access_code.expires_at,
        max_uses: response.access_code.max_uses,
        current_uses: response.access_code.current_uses,
        is_active: response.access_code.is_active,
        allowed_form_ids: response.access_code.allowed_form_ids,
        allowed_external_forms: response.access_code.allowed_external_forms,
        accessible_forms_count: response.access_code.accessible_forms_count,
        access_url: `${window.location.origin}/public-forms?code=${response.access_code.code}`,
      };

      setAccessCodes([...accessCodes, newCode]);
      setAccessCodeDialogOpen(false);
      setSelectedFormForCode(null);
      setSnackbar({
        open: true,
        message: `Access code ${newCode.code} generated successfully!`,
        severity: "success",
      });
    } catch (error) {
      console.error("Error creating access code:", error);
      setSnackbar({
        open: true,
        message: "Failed to generate access code",
        severity: "error",
      });
    }
  };

  const generateRandomCode = (): string => {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    let result = "";
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const handleAddExternalForm = () => {
    if (!newExternalForm.title.trim() || !newExternalForm.url.trim()) {
      setSnackbar({
        open: true,
        message: "Please fill in title and URL",
        severity: "error",
      });
      return;
    }

    try {
      new URL(newExternalForm.url);
    } catch {
      setSnackbar({
        open: true,
        message: "Please enter a valid URL",
        severity: "error",
      });
      return;
    }

    const newForm: ExternalForm = {
      id: Date.now().toString(),
      title: newExternalForm.title.trim(),
      url: newExternalForm.url.trim(),
      description: newExternalForm.description.trim(),
      createdAt: new Date(),
    };

    const updatedForms = [...externalForms, newForm];
    setExternalForms(updatedForms);
    localStorage.setItem("externalForms", JSON.stringify(updatedForms));

    setNewExternalForm({ title: "", url: "", description: "" });
    setExternalFormDialogOpen(false);
    setSnackbar({
      open: true,
      message: "External form added successfully!",
      severity: "success",
    });
  };

  const handleDeleteExternalForm = (formId: string) => {
    if (window.confirm("Are you sure you want to remove this external form?")) {
      const updatedForms = externalForms.filter((form) => form.id !== formId);
      setExternalForms(updatedForms);
      localStorage.setItem("externalForms", JSON.stringify(updatedForms));
      setSnackbar({
        open: true,
        message: "External form removed!",
        severity: "success",
      });
    }
  };

  const handleFormSaved = () => {
    setShowFormBuilder(false);
    setEditingFormId(null);
    // refetch(); // Commented out since My Forms query is disabled
    setSnackbar({
      open: true,
      message: "Form saved successfully!",
      severity: "success",
    });
  };

  // QR Code handlers - commented out unused function
  /*
  const handleGenerateQR = (form: Form) => {
    setSelectedForm(form);
    setShowQRGenerator(true);
  };
  */

  const handleCloseQRGenerator = () => {
    setShowQRGenerator(false);
    setSelectedForm(null);
  };

  // Handle login form submission
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginLoading(true);
    setLoginError("");

    try {
      await login(loginEmail, loginPassword);
      setLoginEmail("");
      setLoginPassword("");
    } catch (error) {
      setLoginError("Login failed. Please check your credentials.");
      console.error("Login error:", error);
    } finally {
      setLoginLoading(false);
    }
  };

  // Show loading while authentication is being checked
  if (isLoading) {
    return (
      <Box sx={{ width: "100%", typography: "body1" }}>
        <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
          <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
            Form Builder Dashboard
          </Typography>
        </Box>
        <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
          <Typography>Loading...</Typography>
        </Box>
      </Box>
    );
  }

  // Show login form if user is not authenticated
  if (!user || !accessToken) {
    return (
      <Box sx={{ width: "100%", typography: "body1" }}>
        <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
          <Typography variant="h4" component="h1" sx={{ mb: 2 }}>
            Form Builder Dashboard
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            Please log in to access the Form Builder Dashboard
          </Alert>
        </Box>

        <Paper sx={{ p: 3, maxWidth: 400, mx: "auto", mt: 4 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Login to Continue
          </Typography>
          {loginError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {loginError}
            </Alert>
          )}
          <form onSubmit={handleLogin}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              margin="normal"
              required
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loginLoading}
              sx={{ mt: 2 }}
            >
              {loginLoading ? "Logging in..." : "Login"}
            </Button>
          </form>
        </Paper>
      </Box>
    );
  }

  if (showFormBuilder) {
    return (
      <FormBuilder
        formId={editingFormId || undefined}
        onSave={handleFormSaved}
        onCancel={() => {
          setShowFormBuilder(false);
          setEditingFormId(null);
        }}
      />
    );
  }

  return (
    <Box sx={{ width: "100%", typography: "body1" }}>
      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 2,
          }}
        >
          <Typography variant="h4" component="h1">
            Form Builder Dashboard
          </Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleNewForm}
            size="large"
          >
            Create New Form
          </Button>
        </Box>

        <Tabs value={tabValue} onChange={handleTabChange}>
          {/* COMMENTED OUT - My Forms Tab */}
          {/*
          <Tab
            label={
              <Badge badgeContent={forms.length} color="primary">
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <ViewList />
                  My Forms
                </Box>
              </Badge>
            }
          />
          */}
          <Tab
            label={
              <Badge badgeContent={externalForms.length} color="secondary">
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Storage />
                  External Forms
                </Box>
              </Badge>
            }
          />
          <Tab
            label={
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Analytics />
                Analytics
              </Box>
            }
          />
          <Tab
            label={
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Settings />
                Form Status
              </Box>
            }
          />
          <Tab
            label={
              <Badge badgeContent={accessCodes.length} color="info">
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <VpnKey />
                  Access Codes
                </Box>
              </Badge>
            }
          />
        </Tabs>
      </Box>

      {/* COMMENTED OUT - My Forms Tab Content */}
      {/*
      <TabPanel value={tabValue} index={0}>
        {formsLoading ? (
          <Typography>Loading forms...</Typography>
        ) : formsError ? (
          <Alert severity="error">Failed to load forms</Alert>
        ) : forms.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: "center" }}>
            <Dashboard sx={{ fontSize: 64, color: "gray", mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Forms Created Yet
            </Typography>
            <Typography color="text.secondary" paragraph>
              Start building your first form to collect data from users.
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleNewForm}
              size="large"
            >
              Create Your First Form
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {forms.map((form: Form) => (
              <Grid item xs={12} md={6} lg={4} key={form.id}>
                <Card
                  sx={{
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
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
                        component="h2"
                        noWrap
                        sx={{ flexGrow: 1, mr: 1 }}
                      >
                        {form.title}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, form)}
                      >
                        <MoreVert />
                      </IconButton>
                    </Box>

                    {form.description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        paragraph
                      >
                        {form.description}
                      </Typography>
                    )}

                    <Box
                      sx={{ display: "flex", gap: 1, mb: 2, flexWrap: "wrap" }}
                    >
                      <Chip
                        icon={<Visibility />}
                        label={`${form.submission_count || 0} submissions`}
                        size="small"
                      />
                      <Chip
                        icon={form.is_public ? <Public /> : <Settings />}
                        label={form.is_public ? "Public" : "Private"}
                        size="small"
                        color={form.is_public ? "success" : "default"}
                      />
                      <Chip
                        label={form.is_active ? "Active" : "Inactive"}
                        size="small"
                        color={form.is_active ? "primary" : "default"}
                      />
                    </Box>

                    <Typography variant="caption" color="text.secondary">
                      Created: {new Date(form.created_at).toLocaleDateString()}
                    </Typography>
                  </CardContent>

                  <CardActions>
                    <Button
                      size="small"
                      startIcon={<Edit />}
                      onClick={() => handleEditForm(form)}
                    >
                      Edit
                    </Button>
                    <Button
                      size="small"
                      startIcon={<QrCode />}
                      onClick={() => handleGenerateQR(form)}
                    >
                      QR Code
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Share />}
                      onClick={() => handleShareForm(form)}
                    >
                      Share
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>
      */}

      {/* External Forms Tab */}
      <TabPanel value={tabValue} index={0}>
        <Box
          sx={{
            mb: 3,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6">Stored External Forms</Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setExternalFormDialogOpen(true)}
          >
            Add External Form
          </Button>
        </Box>

        {externalForms.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: "center" }}>
            <Storage sx={{ fontSize: 64, color: "gray", mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No External Forms Stored
            </Typography>
            <Typography color="text.secondary" paragraph>
              Store external form URLs with QR codes for easy access and
              sharing.
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setExternalFormDialogOpen(true)}
            >
              Add Your First External Form
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {externalForms.map((form) => (
              <Grid item xs={12} md={6} lg={4} key={form.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" component="h2" noWrap gutterBottom>
                      {form.title}
                    </Typography>

                    {form.description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        paragraph
                      >
                        {form.description}
                      </Typography>
                    )}

                    <TextField
                      fullWidth
                      size="small"
                      value={form.url}
                      InputProps={{ readOnly: true }}
                      sx={{ mb: 2 }}
                    />

                    <Typography variant="caption" color="text.secondary">
                      Added: {new Date(form.createdAt).toLocaleDateString()}
                    </Typography>
                  </CardContent>

                  <CardActions>
                    <Button
                      size="small"
                      startIcon={<Launch />}
                      onClick={() => window.open(form.url, "_blank")}
                    >
                      Open
                    </Button>
                    <Button
                      size="small"
                      startIcon={<QrCode />}
                      onClick={() => {
                        // For external forms, create QR directly with URL
                        setSelectedForm({
                          id: parseInt(form.id),
                          title: form.title,
                          description: form.description || "",
                          external_url: form.url,
                        } as Form);
                        setShowQRGenerator(true);
                      }}
                    >
                      QR Code
                    </Button>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteExternalForm(form.id)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Analytics Tab */}
      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          Form Analytics
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  External Forms
                </Typography>
                <Typography variant="h4">{externalForms.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Forms with QR Codes
                </Typography>
                <Typography variant="h4">
                  {externalForms.filter((form) => form.qrCode).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Forms with Descriptions
                </Typography>
                <Typography variant="h4">
                  {externalForms.filter((form) => form.description).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Created
                </Typography>
                <Typography variant="h4">{externalForms.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Form Status Management Tab */}
      <TabPanel value={tabValue} index={2}>
        <FormStatusManager externalForms={externalForms} />
      </TabPanel>

      {/* Access Codes Tab */}
      <TabPanel value={tabValue} index={3}>
        <Box
          sx={{
            mb: 3,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6">Form Access Codes</Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleGenerateAccessCode}
          >
            Generate Access Code
          </Button>
        </Box>

        {accessCodes.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: "center" }}>
            <VpnKey sx={{ fontSize: 64, color: "gray", mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Access Codes Generated
            </Typography>
            <Typography color="text.secondary" paragraph>
              Generate access codes to allow participants to access specific
              forms.
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleGenerateAccessCode}
            >
              Generate Your First Code
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {accessCodes.map((accessCode) => (
              <Grid item xs={12} md={6} lg={4} key={accessCode.id}>
                <Card>
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
                        component="h2"
                        sx={{ fontFamily: "monospace" }}
                      >
                        {accessCode.code}
                      </Typography>
                      <Chip
                        label={accessCode.is_active ? "Active" : "Inactive"}
                        color={accessCode.is_active ? "success" : "default"}
                        size="small"
                      />
                    </Box>

                    <Typography
                      variant="body2"
                      color="text.secondary"
                      gutterBottom
                    >
                      {accessCode.description || "Generic access code"}
                    </Typography>

                    <Typography
                      variant="body2"
                      color="text.secondary"
                      gutterBottom
                    >
                      Forms: {accessCode.accessible_forms_count}
                    </Typography>

                    <Typography
                      variant="body2"
                      color="text.secondary"
                      gutterBottom
                    >
                      Uses: {accessCode.current_uses} / {accessCode.max_uses}
                    </Typography>

                    <Typography
                      variant="body2"
                      color="text.secondary"
                      gutterBottom
                    >
                      Expires:{" "}
                      {new Date(accessCode.expires_at).toLocaleString()}
                    </Typography>

                    <TextField
                      fullWidth
                      size="small"
                      value={accessCode.access_url}
                      InputProps={{
                        readOnly: true,
                        endAdornment: (
                          <IconButton
                            onClick={() =>
                              handleCopyToClipboard(accessCode.access_url)
                            }
                          >
                            <ContentCopy />
                          </IconButton>
                        ),
                      }}
                      sx={{ mt: 2 }}
                    />
                  </CardContent>

                  <CardActions>
                    <Button
                      size="small"
                      startIcon={<ContentCopy />}
                      onClick={() => handleCopyToClipboard(accessCode.code)}
                    >
                      Copy Code
                    </Button>
                    <Button
                      size="small"
                      startIcon={<Share />}
                      onClick={() =>
                        handleCopyToClipboard(accessCode.access_url)
                      }
                    >
                      Copy Link
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => selectedForm && handleEditForm(selectedForm)}>
          <Edit sx={{ mr: 1 }} /> Edit Form
        </MenuItem>
        <MenuItem onClick={() => selectedForm && handleShareForm(selectedForm)}>
          <Share sx={{ mr: 1 }} /> Share Form
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            if (selectedForm) {
              handleDeleteForm(selectedForm.id);
              handleMenuClose();
            }
          }}
          sx={{ color: "error.main" }}
        >
          <Delete sx={{ mr: 1 }} /> Delete Form
        </MenuItem>
      </Menu>

      {/* Share Dialog */}
      <Dialog
        open={shareDialogOpen}
        onClose={() => setShareDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Share Form</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>Share this form URL with others:</Typography>
          <TextField
            fullWidth
            value={shareUrl}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <IconButton onClick={() => handleCopyToClipboard(shareUrl)}>
                  <Share />
                </IconButton>
              ),
            }}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShareDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => handleCopyToClipboard(shareUrl)}
          >
            Copy Link
          </Button>
        </DialogActions>
      </Dialog>

      {/* External Form Dialog */}
      <Dialog
        open={externalFormDialogOpen}
        onClose={() => setExternalFormDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add External Form</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Form Title *"
            value={newExternalForm.title}
            onChange={(e) =>
              setNewExternalForm({ ...newExternalForm, title: e.target.value })
            }
            margin="normal"
          />
          <TextField
            fullWidth
            label="Form URL *"
            value={newExternalForm.url}
            onChange={(e) =>
              setNewExternalForm({ ...newExternalForm, url: e.target.value })
            }
            margin="normal"
            placeholder="https://example.com/form"
          />
          <TextField
            fullWidth
            label="Description"
            value={newExternalForm.description}
            onChange={(e) =>
              setNewExternalForm({
                ...newExternalForm,
                description: e.target.value,
              })
            }
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExternalFormDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleAddExternalForm}
            disabled={
              !newExternalForm.title.trim() || !newExternalForm.url.trim()
            }
          >
            Add Form
          </Button>
        </DialogActions>
      </Dialog>

      {/* Access Code Generation Dialog */}
      <Dialog
        open={accessCodeDialogOpen}
        onClose={() => setAccessCodeDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Generate Generic Access Code</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Generate a secure access code that participants can use to access
            multiple selected forms (both internal and external).
          </Alert>

          <TextField
            fullWidth
            label="Access Code Title"
            value={genericCodeSettings.title}
            onChange={(e) =>
              setGenericCodeSettings({
                ...genericCodeSettings,
                title: e.target.value,
              })
            }
            margin="normal"
            placeholder="e.g., Event Registration Forms"
          />

          <TextField
            fullWidth
            label="Description (Optional)"
            value={genericCodeSettings.description}
            onChange={(e) =>
              setGenericCodeSettings({
                ...genericCodeSettings,
                description: e.target.value,
              })
            }
            margin="normal"
            multiline
            rows={2}
            placeholder="Brief description of what this access code provides"
          />

          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Select Internal Forms:
          </Typography>
          <Box
            sx={{
              maxHeight: 200,
              overflowY: "auto",
              border: "1px solid #e0e0e0",
              borderRadius: 1,
              p: 1,
            }}
          >
            {forms.map((form: Form) => (
              <FormControlLabel
                key={form.id}
                control={
                  <Checkbox
                    checked={genericCodeSettings.selected_forms.includes(
                      form.id
                    )}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      const updatedForms = e.target.checked
                        ? [...genericCodeSettings.selected_forms, form.id]
                        : genericCodeSettings.selected_forms.filter(
                            (id) => id !== form.id
                          );
                      setGenericCodeSettings({
                        ...genericCodeSettings,
                        selected_forms: updatedForms,
                      });
                    }}
                  />
                }
                label={`${form.title} ${
                  form.is_public ? "(Public)" : "(Private)"
                }`}
              />
            ))}
            {forms.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                No forms available
              </Typography>
            )}
          </Box>

          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Select External Forms:
          </Typography>
          <Box
            sx={{
              maxHeight: 200,
              overflowY: "auto",
              border: "1px solid #e0e0e0",
              borderRadius: 1,
              p: 1,
            }}
          >
            {externalForms.map((extForm) => (
              <FormControlLabel
                key={extForm.id}
                control={
                  <Checkbox
                    checked={genericCodeSettings.selected_external_forms.some(
                      (f) => f.id === extForm.id
                    )}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      const updatedExternalForms = e.target.checked
                        ? [
                            ...genericCodeSettings.selected_external_forms,
                            extForm,
                          ]
                        : genericCodeSettings.selected_external_forms.filter(
                            (f) => f.id !== extForm.id
                          );
                      setGenericCodeSettings({
                        ...genericCodeSettings,
                        selected_external_forms: updatedExternalForms,
                      });
                    }}
                  />
                }
                label={extForm.title}
              />
            ))}
            {externalForms.length === 0 && (
              <Typography variant="body2" color="text.secondary">
                No external forms available
              </Typography>
            )}
          </Box>

          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Code Settings:
          </Typography>

          <TextField
            fullWidth
            label="Expires in Hours"
            type="number"
            value={genericCodeSettings.expires_in_hours}
            onChange={(e) =>
              setGenericCodeSettings({
                ...genericCodeSettings,
                expires_in_hours: parseInt(e.target.value) || 24,
              })
            }
            margin="normal"
            inputProps={{ min: 1, max: 168 }}
            helperText="How long the access code will be valid (1-168 hours)"
          />

          <TextField
            fullWidth
            label="Maximum Uses"
            type="number"
            value={genericCodeSettings.max_uses}
            onChange={(e) =>
              setGenericCodeSettings({
                ...genericCodeSettings,
                max_uses: parseInt(e.target.value) || 10,
              })
            }
            margin="normal"
            inputProps={{ min: 1, max: 1000 }}
            helperText="Maximum number of times this code can be used"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAccessCodeDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateGenericAccessCode}
            disabled={
              !genericCodeSettings.title.trim() ||
              (genericCodeSettings.selected_forms.length === 0 &&
                genericCodeSettings.selected_external_forms.length === 0)
            }
          >
            Generate Code
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add"
        sx={{ position: "fixed", bottom: 16, right: 16 }}
        onClick={handleNewForm}
      >
        <Add />
      </Fab>

      {/* QR Code Generator Modal */}
      {showQRGenerator && selectedForm && (
        <SimpleQRGenerator
          formTitle={selectedForm.title}
          targetUrl={
            selectedForm.external_url ||
            `${window.location.origin}/forms/${selectedForm.id}`
          }
          onClose={handleCloseQRGenerator}
        />
      )}

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
