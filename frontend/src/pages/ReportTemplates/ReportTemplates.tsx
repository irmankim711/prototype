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
  Chip,
} from "@mui/material";
import { 
  Edit as EditIcon, 
  Delete as DeleteIcon, 
  Add as AddIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Description as DescriptionIcon
} from "@mui/icons-material";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  fetchReportTemplates, 
  updateReportTemplate, 
  createReportTemplate, 
  deleteReportTemplate,
  uploadReportTemplate,
  downloadTemplateFile
} from "../../services/api";
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
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadFileName, setUploadFileName] = useState<string>('');
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

  // Use templates from API only - filter out duplicates based on ID
  const displayTemplates = React.useMemo(() => {
    if (!templates) return [];

    // Remove duplicates based on template ID
    const uniqueTemplates = templates.filter((template, index, array) => {
      const identifier = template.id || template.name;
      return array.findIndex(t => (t.id || t.name) === identifier) === index;
    });

    // Log if duplicates were found
    if (templates.length !== uniqueTemplates.length) {
      console.warn(`Filtered out ${templates.length - uniqueTemplates.length} duplicate templates from display`);
    }

    return uniqueTemplates;
  }, [templates]);

  const uploadTemplateMutation = useMutation({
    mutationFn: ({ file, name, description, category, templateType }: { 
      file: File; 
      name?: string; 
      description?: string; 
      category?: string;
      templateType?: string;
    }) => uploadReportTemplate(file, name, description, category, templateType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reportTemplates"] });
      setSnackbar({ open: true, message: 'Template uploaded successfully!', severity: 'success' });
      setUploadFile(null);
      setUploadFileName('');
      handleCloseDialog();
    },
    onError: (error: any) => {
      console.error("Upload template error:", error);
      setSnackbar({ open: true, message: error.message || 'Failed to upload template', severity: 'error' });
    },
  });

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

      // Check if it's a file-based template error
      const errorMessage = error.response?.data?.message || error.response?.data?.error || error.message || 'Failed to update template';
      const isFileBased = error.response?.data?.is_file_based || errorMessage.includes('file-based');

      setSnackbar({
        open: true,
        message: isFileBased
          ? 'Cannot edit file-based templates. Please download and edit the file directly, or upload as a new template.'
          : errorMessage,
        severity: 'error'
      });
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


  const handleCloseDialog = () => {
    setEditTemplate(null);
    setIsDialogOpen(false);
    setUploadFile(null);
    setUploadFileName('');
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploadFile(file);
      setUploadFileName(file.name);
    }
  };

  const handleDownloadTemplate = async (template: ReportTemplate) => {
    try {
      await downloadTemplateFile(template.id, template.name);
      setSnackbar({ open: true, message: 'Template downloaded successfully', severity: 'success' });
    } catch (error: any) {
      console.error("Download error:", error);
      setSnackbar({ open: true, message: error.message || 'Failed to download template', severity: 'error' });
    }
  };

  const handleSaveTemplate = (event: React.FormEvent) => {
    event.preventDefault();
    const formData = new FormData(event.target as HTMLFormElement);

    if (dialogMode === 'create') {
      // If file is uploaded, use file upload
      if (uploadFile) {
        const name = formData.get("name") as string || uploadFileName.replace(/\.[^/.]+$/, "");
        const description = formData.get("description") as string || '';
        const category = formData.get("category") as string || 'general';
        const templateType = formData.get("template_type") as string || '';
        
        uploadTemplateMutation.mutate({
          file: uploadFile,
          name,
          description,
          category,
          templateType
        });
        return;
      }

      // Otherwise, use text content (fallback)
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
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 1 }}>
                  <Typography variant="h6" gutterBottom>
                    {template.name}
                  </Typography>
                  <Chip 
                    label={template.template_type || 'Unknown'} 
                    size="small" 
                    color="primary"
                    variant="outlined"
                  />
                </Box>
                <Typography color="textSecondary" gutterBottom variant="body2">
                  {template.description || 'No description'}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  Category: {template.category || 'General'}
                </Typography>
                {template.file_path && (
                  <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 0.5 }}>
                    <DescriptionIcon fontSize="small" color="action" />
                    <Typography variant="caption" color="textSecondary">
                      File available
                    </Typography>
                  </Box>
                )}
                {template.file_size && (
                  <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 0.5 }}>
                    Size: {(template.file_size / 1024).toFixed(2)} KB
                  </Typography>
                )}
                <FormControlLabel
                  control={
                    <Switch
                      checked={template.is_active}
                      color="primary"
                      disabled
                      size="small"
                    />
                  }
                  label={template.is_active ? "Active" : "Inactive"}
                  sx={{ mt: 1 }}
                />
              </CardContent>
              <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                <Box>
                  {/* Check if template is file-based (string ID that's not a number) */}
                  {(() => {
                    const isFileBasedTemplate = template.id && typeof template.id === 'string' && !/^\d+$/.test(template.id);

                    return (
                      <Button
                        size="small"
                        startIcon={<EditIcon />}
                        onClick={() => handleOpenEditDialog(template)}
                        disabled={isFileBasedTemplate}
                        title={isFileBasedTemplate ? 'File-based templates cannot be edited via UI. Please edit the file directly or upload as a new template.' : 'Edit template'}
                      >
                        Edit
                      </Button>
                    );
                  })()}
                  {template.file_path && (
                    <>
                      <Button
                        size="small"
                        startIcon={<DownloadIcon />}
                        onClick={() => handleDownloadTemplate(template)}
                        color="success"
                      >
                        Download
                      </Button>
                    </>
                  )}
                </Box>
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
                    <Box sx={{ mt: 2, mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Upload Template File (DOCX, DOC, TXT, etc.)
                      </Typography>
                      <input
                        accept=".docx,.doc,.txt,.html,.tex,.jinja,.jinja2"
                        style={{ display: 'none' }}
                        id="template-file-upload"
                        type="file"
                        onChange={handleFileChange}
                      />
                      <label htmlFor="template-file-upload">
                        <Button
                          variant="outlined"
                          component="span"
                          startIcon={<UploadIcon />}
                          fullWidth
                          sx={{ mb: 2 }}
                        >
                          {uploadFile ? uploadFileName : 'Choose Template File'}
                        </Button>
                      </label>
                      {uploadFile && (
                        <Alert severity="info" sx={{ mt: 1 }}>
                          File selected: {uploadFileName}
                        </Alert>
                      )}
                      <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
                        Supported formats: DOCX, DOC, TXT, HTML, TEX, JINJA, JINJA2
                      </Typography>
                    </Box>

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

                    <FormControl fullWidth margin="normal">
                      <InputLabel>Template Type (Optional - auto-detected from file)</InputLabel>
                      <Select
                        name="template_type"
                        defaultValue=""
                        label="Template Type (Optional - auto-detected from file)"
                      >
                        <MenuItem value="">Auto-detect</MenuItem>
                        <MenuItem value="docx">DOCX</MenuItem>
                        <MenuItem value="jinja2">Jinja2</MenuItem>
                        <MenuItem value="latex">LaTeX</MenuItem>
                        <MenuItem value="text">Text</MenuItem>
                      </Select>
                    </FormControl>

                    <Typography variant="body2" color="textSecondary" sx={{ mt: 2, mb: 1 }}>
                      OR enter template content manually (if not uploading a file):
                    </Typography>
                    <TextField
                      name="template_content"
                      label="Template Content (Optional)"
                      fullWidth
                      multiline
                      rows={6}
                      margin="normal"
                      placeholder="Enter your template content here..."
                      helperText="Use {{variable_name}} for placeholders. Leave empty if uploading a file."
                      disabled={!!uploadFile}
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
              disabled={
                createTemplateMutation.isPending || 
                updateTemplateMutation.isPending || 
                uploadTemplateMutation.isPending
              }
            >
              {(createTemplateMutation.isPending || updateTemplateMutation.isPending || uploadTemplateMutation.isPending) ? (
                <CircularProgress size={24} />
              ) : (
                dialogMode === 'create' ? (uploadFile ? 'Upload Template' : 'Create Template') : 'Save Changes'
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

