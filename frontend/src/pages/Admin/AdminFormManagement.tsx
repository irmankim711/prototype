import React from "react";
import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Switch,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
  InputAdornment,
  Pagination,
  MenuItem,
  Tooltip,
  Card,
  CardContent,
  Grid,
  Snackbar,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  Public as PublicIcon,
  Link as LinkIcon,
  Dashboard as DashboardIcon,
  Assessment as StatsIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import type {
  Form,
  FormStats,
  FormData,
  FormsResponse,
} from "../../types/forms";

// Styled components with Apple-style design
const GlassPaper = styled(Paper)(() => ({
  background: "rgba(255, 255, 255, 0.1)",
  backdropFilter: "blur(20px)",
  border: "1px solid rgba(255, 255, 255, 0.2)",
  borderRadius: "16px",
  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
}));

const StatsCard = styled(Card)(() => ({
  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  color: "white",
  borderRadius: "16px",
  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
  transition: "transform 0.2s ease-in-out",
  "&:hover": {
    transform: "translateY(-4px)",
  },
}));

const ActionButton = styled(IconButton)(() => ({
  borderRadius: "12px",
  transition: "all 0.2s ease-in-out",
  "&:hover": {
    background: "rgba(0, 0, 0, 0.08)",
    transform: "scale(1.1)",
  },
}));

const StyledSwitch = styled(Switch)(() => ({
  "& .MuiSwitch-switchBase.Mui-checked": {
    color: "#667eea",
  },
  "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
    backgroundColor: "#667eea",
  },
}));

const AdminFormManagement = () => {
  // State management
  const [forms, setForms] = useState<Form[]>([]);
  const [stats, setStats] = useState<FormStats>({
    total_forms: 0,
    public_forms: 0,
    active_forms: 0,
    external_forms: 0,
    private_forms: 0,
    inactive_forms: 0,
    recent_forms: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedForm, setSelectedForm] = useState<Form | null>(null);

  // Form states
  const [formData, setFormData] = useState<FormData>({
    title: "",
    description: "",
    schema: [],
    is_public: false,
    is_active: true,
    external_url: "",
  });

  // Filter and pagination states
  const [searchTerm, setSearchTerm] = useState("");
  const [filterPublic, setFilterPublic] = useState("all");
  const [filterActive, setFilterActive] = useState("all");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // API calls
  const fetchForms = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: "10",
        search: searchTerm,
      });

      if (filterPublic !== "all") {
        params.append("is_public", filterPublic);
      }
      if (filterActive !== "all") {
        params.append("is_active", filterActive);
      }

      const response = await fetch(`/api/admin/forms?${params}`, {
        headers: {
          Authorization: `Bearer dev-bypass-token`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data: FormsResponse = await response.json();
        setForms(data.forms);
        setTotalPages(data.pagination.pages);
      } else {
        setError("Failed to fetch forms");
      }
    } catch {
      setError("Error fetching forms");
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm, filterPublic, filterActive]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch("/api/admin/forms/stats", {
        headers: {
          Authorization: `Bearer dev-bypass-token`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data: FormStats = await response.json();
        setStats(data);
      }
    } catch {
      console.error("Error fetching stats");
    }
  }, []);

  const handleCreateForm = async () => {
    try {
      const response = await fetch("/api/admin/forms", {
        method: "POST",
        headers: {
          Authorization: `Bearer dev-bypass-token`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setSuccess("Form created successfully");
        setCreateDialogOpen(false);
        resetFormData();
        fetchForms();
        fetchStats();
      } else {
        const errorData = await response.json();
        setError(errorData.error || "Failed to create form");
      }
    } catch (err) {
      setError("Error creating form");
    }
  };

  const handleUpdateForm = async () => {
    if (!selectedForm) return;

    try {
      const response = await fetch(`/api/admin/forms/${selectedForm.id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer dev-bypass-token`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setSuccess("Form updated successfully");
        setEditDialogOpen(false);
        resetFormData();
        fetchForms();
      } else {
        const errorData = await response.json();
        setError(errorData.error || "Failed to update form");
      }
    } catch {
      setError("Error updating form");
    }
  };

  const handleDeleteForm = async () => {
    if (!selectedForm) return;

    try {
      const response = await fetch(`/api/admin/forms/${selectedForm.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer dev-bypass-token`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        setSuccess("Form deleted successfully");
        setDeleteDialogOpen(false);
        setSelectedForm(null);
        fetchForms();
        fetchStats();
      } else {
        setError("Failed to delete form");
      }
    } catch {
      setError("Error deleting form");
    }
  };

  const handleToggleField = async (formId: number, field: string) => {
    try {
      const response = await fetch(
        `/api/admin/forms/${formId}/toggle/${field}`,
        {
          method: "PATCH",
          headers: {
            Authorization: `Bearer dev-bypass-token`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        setSuccess(`Form ${field} toggled successfully`);
        fetchForms();
      } else {
        setError(`Failed to toggle ${field}`);
      }
    } catch {
      setError(`Error toggling ${field}`);
    }
  };

  const resetFormData = () => {
    setFormData({
      title: "",
      description: "",
      schema: [],
      is_public: false,
      is_active: true,
      external_url: "",
    });
  };

  const openEditDialog = (form: Form) => {
    setSelectedForm(form);
    setFormData({
      title: form.title,
      description: form.description || "",
      schema: form.schema || [],
      is_public: form.is_public,
      is_active: form.is_active,
      external_url: form.external_url || "",
    });
    setEditDialogOpen(true);
  };

  const openDeleteDialog = (form: Form) => {
    setSelectedForm(form);
    setDeleteDialogOpen(true);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getFormTypeChip = (form: Form) => {
    if (form.external_url) {
      return (
        <Chip icon={<LinkIcon />} label="External" size="small" color="info" />
      );
    }
    return (
      <Chip
        icon={<DashboardIcon />}
        label="Internal"
        size="small"
        color="default"
      />
    );
  };

  // Effects
  useEffect(() => {
    fetchForms();
    fetchStats();
  }, [page, searchTerm, filterPublic, filterActive, fetchForms, fetchStats]);

  return (
    <Box
      sx={{
        p: 3,
        minHeight: "100vh",
        background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
      }}
    >
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: "#333", mb: 1 }}>
          Form Management Dashboard
        </Typography>
        <Typography variant="subtitle1" sx={{ color: "#666" }}>
          Manage all your forms, toggles, and settings
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard>
            <CardContent>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.total_forms || 0}
                  </Typography>
                  <Typography variant="body2">Total Forms</Typography>
                </Box>
                <StatsIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </StatsCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            sx={{
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            }}
          >
            <CardContent>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.public_forms || 0}
                  </Typography>
                  <Typography variant="body2">Public Forms</Typography>
                </Box>
                <PublicIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </StatsCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            sx={{
              background: "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)",
              color: "#333",
            }}
          >
            <CardContent>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.active_forms || 0}
                  </Typography>
                  <Typography variant="body2">Active Forms</Typography>
                </Box>
                <ViewIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </StatsCard>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            sx={{
              background: "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
              color: "#333",
            }}
          >
            <CardContent>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.external_forms || 0}
                  </Typography>
                  <Typography variant="body2">External Forms</Typography>
                </Box>
                <LinkIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </StatsCard>
        </Grid>
      </Grid>

      {/* Controls */}
      <GlassPaper sx={{ p: 3, mb: 3 }}>
        <Box
          sx={{
            display: "flex",
            gap: 2,
            flexWrap: "wrap",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Box
            sx={{
              display: "flex",
              gap: 2,
              flexWrap: "wrap",
              alignItems: "center",
            }}
          >
            <TextField
              placeholder="Search forms..."
              value={searchTerm}
              onChange={(e: any) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 250 }}
            />

            <TextField
              select
              label="Public Status"
              value={filterPublic}
              onChange={(e: any) => setFilterPublic(e.target.value)}
              sx={{ minWidth: 120 }}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="true">Public</MenuItem>
              <MenuItem value="false">Private</MenuItem>
            </TextField>

            <TextField
              select
              label="Active Status"
              value={filterActive}
              onChange={(e: any) => setFilterActive(e.target.value)}
              sx={{ minWidth: 120 }}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="true">Active</MenuItem>
              <MenuItem value="false">Inactive</MenuItem>
            </TextField>

            <Tooltip title="Refresh">
              <ActionButton
                onClick={() => {
                  fetchForms();
                  fetchStats();
                }}
              >
                <RefreshIcon />
              </ActionButton>
            </Tooltip>
          </Box>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
            sx={{
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              borderRadius: "12px",
              textTransform: "none",
              fontWeight: 600,
              boxShadow: "0 4px 16px rgba(102, 126, 234, 0.3)",
              "&:hover": {
                boxShadow: "0 6px 20px rgba(102, 126, 234, 0.4)",
              },
            }}
          >
            Create Form
          </Button>
        </Box>
      </GlassPaper>

      {/* Forms Table */}
      <GlassPaper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Form</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Public</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Fields</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Views</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Created</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} sx={{ textAlign: "center", py: 4 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : forms.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} sx={{ textAlign: "center", py: 4 }}>
                    <Typography variant="body1" color="textSecondary">
                      No forms found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                forms.map((form: any) => (
                  <TableRow key={form.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>
                          {form.title}
                        </Typography>
                        {form.description && (
                          <Typography
                            variant="body2"
                            color="textSecondary"
                            sx={{ mt: 0.5 }}
                          >
                            {form.description.length > 50
                              ? `${form.description.substring(0, 50)}...`
                              : form.description}
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>{getFormTypeChip(form)}</TableCell>
                    <TableCell>
                      <FormControlLabel
                        control={
                          <StyledSwitch
                            checked={form.is_active}
                            onChange={() =>
                              handleToggleField(form.id, "is_active")
                            }
                            size="small"
                          />
                        }
                        label={form.is_active ? "Active" : "Inactive"}
                        sx={{ margin: 0 }}
                      />
                    </TableCell>
                    <TableCell>
                      <FormControlLabel
                        control={
                          <StyledSwitch
                            checked={form.is_public}
                            onChange={() =>
                              handleToggleField(form.id, "is_public")
                            }
                            size="small"
                          />
                        }
                        label={form.is_public ? "Public" : "Private"}
                        sx={{ margin: 0 }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={form.field_count}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {form.view_count || 0}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {formatDate(form.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", gap: 1 }}>
                        <Tooltip title="Edit">
                          <ActionButton
                            size="small"
                            onClick={() => openEditDialog(form)}
                          >
                            <EditIcon fontSize="small" />
                          </ActionButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <ActionButton
                            size="small"
                            onClick={() => openDeleteDialog(form)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </ActionButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ display: "flex", justifyContent: "center", p: 2 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_e, newPage) => setPage(newPage)}
              color="primary"
              showFirstButton
              showLastButton
            />
          </Box>
        )}
      </GlassPaper>

      {/* Create Form Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Form</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Form Title"
            value={formData.title}
            onChange={(e: any) =>
              setFormData({ ...formData, title: e.target.value })
            }
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e: any) =>
              setFormData({ ...formData, description: e.target.value })
            }
            margin="normal"
            multiline
            rows={3}
          />
          <TextField
            fullWidth
            label="External URL (optional)"
            value={formData.external_url}
            onChange={(e: any) =>
              setFormData({ ...formData, external_url: e.target.value })
            }
            margin="normal"
            placeholder="https://example.com/form"
          />
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.is_public}
                  onChange={(e: any) =>
                    setFormData({ ...formData, is_public: e.target.checked })
                  }
                />
              }
              label="Make form public"
            />
          </Box>
          <Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.is_active}
                  onChange={(e: any) =>
                    setFormData({ ...formData, is_active: e.target.checked })
                  }
                />
              }
              label="Form is active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateForm}
            variant="contained"
            disabled={!formData.title}
          >
            Create Form
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Form Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit Form</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Form Title"
            value={formData.title}
            onChange={(e: any) =>
              setFormData({ ...formData, title: e.target.value })
            }
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Description"
            value={formData.description}
            onChange={(e: any) =>
              setFormData({ ...formData, description: e.target.value })
            }
            margin="normal"
            multiline
            rows={3}
          />
          <TextField
            fullWidth
            label="External URL (optional)"
            value={formData.external_url}
            onChange={(e: any) =>
              setFormData({ ...formData, external_url: e.target.value })
            }
            margin="normal"
            placeholder="https://example.com/form"
          />
          <Box sx={{ mt: 2 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.is_public}
                  onChange={(e: any) =>
                    setFormData({ ...formData, is_public: e.target.checked })
                  }
                />
              }
              label="Make form public"
            />
          </Box>
          <Box>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.is_active}
                  onChange={(e: any) =>
                    setFormData({ ...formData, is_active: e.target.checked })
                  }
                />
              }
              label="Form is active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleUpdateForm}
            variant="contained"
            disabled={!formData.title}
          >
            Update Form
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Form</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedForm?.title}"? This action
            cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteForm} variant="contained" color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbars */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess("")}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert onClose={() => setSuccess("")} severity="success">
          {success}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError("")}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert onClose={() => setError("")} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AdminFormManagement;
