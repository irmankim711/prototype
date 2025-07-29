import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { formBuilderAPI, type Form } from "../../services/formBuilder";
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
  Chip,
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
} from "@mui/material";
import {
  Add,
  Delete,
  Edit,
  Share,
  QrCode,
  Visibility,
  Analytics,
  Settings,
  Public,
  Launch,
  Storage,
  MoreVert,
  Dashboard,
  ViewList,
} from "@mui/icons-material";

import FormBuilder from "../../components/FormBuilder/FormBuilder";
import SimpleQRGenerator from "../../components/forms/SimpleQRGenerator";

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

export default function FormBuilderAdmin() {
  const [tabValue, setTabValue] = useState(0);
  const [editingFormId, setEditingFormId] = useState<number | null>(null);
  const [showFormBuilder, setShowFormBuilder] = useState(false);

  // Dialog states
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [externalFormDialogOpen, setExternalFormDialogOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedForm, setSelectedForm] = useState<Form | null>(null);

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
    return saved ? JSON.parse(saved) : [];
  });

  // Notification state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success" as "success" | "error" | "warning" | "info",
  });

  const [page] = useState(1);

  // QR Code state
  const [showQRGenerator, setShowQRGenerator] = useState(false);

  // Fetch forms data
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
      refetch();
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

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, form: Form) => {
    setAnchorEl(event.currentTarget);
    setSelectedForm(form);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedForm(null);
  };

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
    refetch();
    setSnackbar({
      open: true,
      message: "Form saved successfully!",
      severity: "success",
    });
  };

  // QR Code handlers
  const handleGenerateQR = (form: Form) => {
    setSelectedForm(form);
    setShowQRGenerator(true);
  };

  const handleCloseQRGenerator = () => {
    setShowQRGenerator(false);
    setSelectedForm(null);
  };

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
        </Tabs>
      </Box>

      {/* My Forms Tab */}
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

      {/* External Forms Tab */}
      <TabPanel value={tabValue} index={1}>
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
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" gutterBottom>
          Form Analytics
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Forms
                </Typography>
                <Typography variant="h4">{forms.length}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Submissions
                </Typography>
                <Typography variant="h4">
                  {forms.reduce(
                    (sum: number, form: Form) =>
                      sum + (form.submission_count || 0),
                    0
                  )}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6} lg={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Active Forms
                </Typography>
                <Typography variant="h4">
                  {forms.filter((form: Form) => form.is_active).length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
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
        </Grid>
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
          formId={selectedForm.id}
          formTitle={selectedForm.title}
          onClose={handleCloseQRGenerator}
          defaultUrl={selectedForm.external_url}
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
