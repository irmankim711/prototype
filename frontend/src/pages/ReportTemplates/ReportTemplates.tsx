import React from "react";
import { useState } from "react";
import {
  Box,
  Typography,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  CardActions,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Snackbar,
} from "@mui/material";
import { Edit as EditIcon, Delete as DeleteIcon, Add as AddIcon } from "@mui/icons-material";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchReportTemplates, updateReportTemplate, createReportTemplate, deleteReportTemplate } from "../../services/api";
import type { ReportTemplate } from "../../services/api";

// No mock data - templates will be fetched from backend

type DialogMode = 'create' | 'edit' | 'rename';

export default function ReportTemplates() {
  const [editTemplate, setEditTemplate] = useState<ReportTemplate | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<DialogMode>('edit');
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState<ReportTemplate | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const queryClient = useQueryClient();

  const {
    data: templates,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["reportTemplates"],
    queryFn: fetchReportTemplates,
    retry: 3,
    onError: (error: any) => {
      console.error("API Error fetching templates:", error);
    },
  });

  // Use templates from API only
  const displayTemplates = templates || [];

  const createTemplateMutation = useMutation({
    mutationFn: (data: Partial<ReportTemplate>) => createReportTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reportTemplates"] });
      setSnackbar({ open: true, message: 'Template created successfully!', severity: 'success' });
      handleCloseDialog();
    },
    onError: (error: any) => {
      console.error("Create template error:", error);
      setSnackbar({ open: true, message: 'Failed to create template', severity: 'error' });
    },
  });

  const updateTemplateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ReportTemplate> }) =>
      updateReportTemplate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reportTemplates"] });
      setSnackbar({ open: true, message: 'Template updated successfully!', severity: 'success' });
      handleCloseDialog();
    },
    onError: (error: any) => {
      console.error("Update template error:", error);
      setSnackbar({ open: true, message: 'Failed to update template', severity: 'error' });
    },
  });

  const deleteTemplateMutation = useMutation({
    mutationFn: (id: string) => deleteReportTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reportTemplates"] });
      setSnackbar({ open: true, message: 'Template deleted successfully!', severity: 'success' });
    },
    onError: (error: any) => {
      console.error("Delete template error:", error);
      setSnackbar({ open: true, message: 'Failed to delete template', severity: 'error' });
    },
  });

  const handleOpenCreateDialog = () => {
    setDialogMode('create');
    setEditTemplate(null);
    setIsDialogOpen(true);
  };

  const handleOpenEditDialog = (template: ReportTemplate) => {
    setDialogMode('edit');
    setEditTemplate(template);
    setIsDialogOpen(true);
  };

  const handleOpenRenameDialog = (template: ReportTemplate) => {
    setDialogMode('rename');
    setEditTemplate(template);
    setIsDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setEditTemplate(null);
    setIsDialogOpen(false);
  };

  const handleSaveTemplate = (event: React.FormEvent) => {
    event.preventDefault();
    const formData = new FormData(event.target as HTMLFormElement);

    if (dialogMode === 'create') {
      const data = {
        name: formData.get("name") as string,
        description: formData.get("description") as string,
        template_type: formData.get("template_type") as string,
        category: formData.get("category") as string,
        template_content: formData.get("template_content") as string || '',
        is_active: true,
      };
      createTemplateMutation.mutate(data);
    } else if (dialogMode === 'rename') {
      if (!editTemplate) return;
      const data = {
        name: formData.get("name") as string,
      };
      updateTemplateMutation.mutate({
        id: editTemplate.id,
        data,
      });
    } else {
      if (!editTemplate) return;
      const data = {
        name: formData.get("name") as string,
        description: formData.get("description") as string,
        is_active: formData.get("isActive") === "on",
      };
      updateTemplateMutation.mutate({
        id: editTemplate.id,
        data,
      });
    }
  };

  const handleDeleteClick = (template: ReportTemplate) => {
    setTemplateToDelete(template);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (!templateToDelete) return;
    // Delete the template
    deleteTemplateMutation.mutate(templateToDelete.id);
    setDeleteConfirmOpen(false);
    setTemplateToDelete(null);
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmOpen(false);
    setTemplateToDelete(null);
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (isLoading) {
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
      {error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load templates. Please try again later.
        </Alert>
      ) : null}

      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={4}
      >
        <Typography variant="h4">Report Templates</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleOpenCreateDialog}
        >
          Create Template
        </Button>
      </Box>

      <Grid container spacing={3}>
        {displayTemplates?.map((template: any) => (
          <Grid item xs={12} sm={6} md={4} key={template.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {template.name}
                </Typography>
                <Typography color="textSecondary" gutterBottom>
                  {template.description}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Type: {template.template_type || 'Unknown'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Category: {template.category || 'General'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Placeholders:{" "}
                  {Array.isArray(template.placeholder_schema?.fields)
                    ? template.placeholder_schema.fields.length
                    : 0}
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={template.is_active}
                      color="primary"
                      disabled
                    />
                  }
                  label={template.is_active ? "Active" : "Inactive"}
                />
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={() => handleOpenEditDialog(template)}
                >
                  Edit
                </Button>
                <Button
                  size="small"
                  onClick={() => handleOpenRenameDialog(template)}
                >
                  Rename
                </Button>
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => handleDeleteClick(template)}
                >
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Create/Edit/Rename Dialog */}
      <Dialog
        open={isDialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <form onSubmit={handleSaveTemplate}>
          <DialogTitle>
            {dialogMode === 'create' ? 'Create New Template' :
             dialogMode === 'rename' ? 'Rename Template' : 'Edit Template'}
          </DialogTitle>
          <DialogContent>
            <TextField
              name="name"
              label="Template Name"
              fullWidth
              defaultValue={editTemplate?.name}
              margin="normal"
              required
            />

            {dialogMode !== 'rename' && (
              <>
                <TextField
                  name="description"
                  label="Description"
                  fullWidth
                  multiline
                  rows={3}
                  defaultValue={editTemplate?.description}
                  margin="normal"
                />

                {dialogMode === 'create' && (
                  <>
                    <FormControl fullWidth margin="normal">
                      <InputLabel>Template Type</InputLabel>
                      <Select
                        name="template_type"
                        defaultValue="jinja2"
                        label="Template Type"
                        required
                      >
                        <MenuItem value="jinja2">Jinja2</MenuItem>
                        <MenuItem value="latex">LaTeX</MenuItem>
                        <MenuItem value="docx">DOCX</MenuItem>
                      </Select>
                    </FormControl>

                    <FormControl fullWidth margin="normal">
                      <InputLabel>Category</InputLabel>
                      <Select
                        name="category"
                        defaultValue="general"
                        label="Category"
                      >
                        <MenuItem value="general">General</MenuItem>
                        <MenuItem value="business">Business</MenuItem>
                        <MenuItem value="academic">Academic</MenuItem>
                        <MenuItem value="technical">Technical</MenuItem>
                        <MenuItem value="financial">Financial</MenuItem>
                      </Select>
                    </FormControl>

                    <TextField
                      name="template_content"
                      label="Template Content"
                      fullWidth
                      multiline
                      rows={6}
                      margin="normal"
                      placeholder="Enter your template content here..."
                      helperText="Use {{variable_name}} for placeholders"
                    />
                  </>
                )}

                {dialogMode === 'edit' && (
                  <FormControlLabel
                    control={
                      <Switch
                        name="isActive"
                        defaultChecked={editTemplate?.is_active}
                        color="primary"
                      />
                    }
                    label="Active"
                  />
                )}
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={createTemplateMutation.isPending || updateTemplateMutation.isPending}
            >
              {(createTemplateMutation.isPending || updateTemplateMutation.isPending) ? (
                <CircularProgress size={24} />
              ) : (
                dialogMode === 'create' ? 'Create Template' : 'Save Changes'
              )}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={handleDeleteCancel}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the template "{templateToDelete?.name}"?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deleteTemplateMutation.isPending}
          >
            {deleteTemplateMutation.isPending ? (
              <CircularProgress size={24} />
            ) : (
              'Delete'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
