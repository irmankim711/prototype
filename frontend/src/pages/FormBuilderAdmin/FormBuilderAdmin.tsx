import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { formBuilderAPI, type Form } from '../../services/formBuilder';
import { QRCodeSVG } from 'qrcode.react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Alert, 
  Snackbar, 
  Chip,
  IconButton,
  TextField,
  InputAdornment
} from '@mui/material';

import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid
} from '@mui/material';

import {
  Add,
  Delete,
  Edit,
  Share,
  ContentCopy,
  Download,
  Link as LinkIcon,
  QrCode
} from '@mui/icons-material';

import FormBuilder from '../../components/FormBuilder/FormBuilder';

interface ExternalForm {
  id: string;
  title: string;
  url: string;
  description?: string;
  createdAt: Date;
}

export default function FormBuilderAdmin() {
  const [editingFormId, setEditingFormId] = useState<number | null>(null);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' | 'info' });
  const [page, setPage] = useState(1);
  
  // External form states
  const [externalForms, setExternalForms] = useState<ExternalForm[]>(() => {
    const saved = localStorage.getItem('externalForms');
    return saved ? JSON.parse(saved) : [];
  });
  const [newExternalForm, setNewExternalForm] = useState({ title: '', url: '', description: '' });
  const [externalFormDialogOpen, setExternalFormDialogOpen] = useState(false);
  const [showFormBuilder, setShowFormBuilder] = useState(false);

  const { data: formsData, isLoading: formsLoading, error: formsError, refetch } = useQuery({
    queryKey: ['forms', page],
    queryFn: () => formBuilderAPI.getForms({ page, limit: 10 }),
    staleTime: 1000 * 60 * 5 // 5 minutes
  });

  const forms = formsData?.forms || [];

  const deleteMutation = useMutation({
    mutationFn: formBuilderAPI.deleteForm,
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Form deleted successfully!', severity: 'success' });
      refetch();
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to delete form', severity: 'error' });
    }
  });

  const handleNewForm = () => {
    setShowFormBuilder(true);
    setEditingFormId(null);
  };

  const handleEditForm = (form: Form) => {
    setShowFormBuilder(true);
    setEditingFormId(form.id);
  };

  const handleAddExternalForm = () => {
    if (!newExternalForm.title.trim() || !newExternalForm.url.trim()) {
      setSnackbar({ open: true, message: 'Please fill in title and URL', severity: 'error' });
      return;
    }

    // Basic URL validation
    try {
      new URL(newExternalForm.url);
    } catch {
      setSnackbar({ open: true, message: 'Please enter a valid URL', severity: 'error' });
      return;
    }

    const newForm: ExternalForm = {
      id: Date.now().toString(),
      title: newExternalForm.title,
      url: newExternalForm.url,
      description: newExternalForm.description,
      createdAt: new Date()
    };

    const updatedForms = [...externalForms, newForm];
    setExternalForms(updatedForms);
    localStorage.setItem('externalForms', JSON.stringify(updatedForms));
    
    setNewExternalForm({ title: '', url: '', description: '' });
    setExternalFormDialogOpen(false);
    setSnackbar({ open: true, message: 'External form added successfully!', severity: 'success' });
  };

  const handleDeleteExternalForm = (formId: string) => {
    if (window.confirm('Are you sure you want to delete this external form?')) {
      const updatedForms = externalForms.filter(form => form.id !== formId);
      setExternalForms(updatedForms);
      localStorage.setItem('externalForms', JSON.stringify(updatedForms));
      setSnackbar({ open: true, message: 'External form deleted successfully!', severity: 'success' });
    }
  };

  const handleShareExternalForm = (form: ExternalForm) => {
    setShareUrl(form.url);
    setShareDialogOpen(true);
  };

  const handleCopyLink = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setSnackbar({ open: true, message: 'Link copied to clipboard!', severity: 'success' });
    }
  };

  const handleDeleteForm = (formId: number) => {
    if (window.confirm('Are you sure you want to delete this form?')) {
      deleteMutation.mutate(formId);
    }
  };

  const handleFormSave = () => {
    setSnackbar({ open: true, message: 'Form saved successfully!', severity: 'success' });
    setShowFormBuilder(false);
    setEditingFormId(null);
    refetch();
  };

  const handleFormCancel = () => {
    setShowFormBuilder(false);
    setEditingFormId(null);
  };

  const handleShareForm = (form: Form) => {
    const baseUrl = window.location.origin;
    const shareUrl = `${baseUrl}/form/${form.id}`;
    setShareUrl(shareUrl);
    setShareDialogOpen(true);
  };

  return (
    <React.Fragment>
      <Box sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" gutterBottom sx={{ color: '#1e3a8a', fontWeight: 600 }}>
            Form Builder
          </Typography>
          <Box>
            <Button 
              variant="contained" 
              onClick={handleNewForm}
              startIcon={<Add />}
              sx={{ mr: 1, bgcolor: '#1e3a8a' }}
            >
              New Form
            </Button>
            <Button 
              variant="outlined" 
              onClick={() => setExternalFormDialogOpen(true)}
              startIcon={<LinkIcon />}
            >
              Add Link
            </Button>
          </Box>
        </Box>

        {showFormBuilder ? (
          <FormBuilder 
            formId={editingFormId || undefined}
            onSave={handleFormSave}
            onCancel={handleFormCancel}
          />
        ) : (
          <Box>
            {formsLoading && (
              <Box display="flex" justifyContent="center" p={4}>
                <Typography>Loading forms...</Typography>
              </Box>
            )}
            {formsError ? (
              <Box p={2}>
                <Alert severity="error">Failed to load forms. Please try again.</Alert>
              </Box>
            ) : null}
            {!formsLoading && !formsError && (
              <Grid container spacing={3}>
                {forms.length === 0 && externalForms.length === 0 ? (
                  <Grid item xs={12}>
                    <Box textAlign="center" p={4}>
                      <Typography variant="h6" color="text.secondary">No forms found</Typography>
                      <Typography variant="body2" color="text.secondary" mb={2}>Create your first form or add an external form link to get started</Typography>
                      <Box display="flex" gap={2} justifyContent="center">
                        <Button variant="contained" onClick={handleNewForm} startIcon={<Add />} sx={{ bgcolor: '#1e3a8a' }}>
                          Create New Form
                        </Button>
                        <Button variant="outlined" onClick={() => setExternalFormDialogOpen(true)} startIcon={<LinkIcon />}>
                          Add Link
                        </Button>
                      </Box>
                    </Box>
                  </Grid>
                ) : (
                  <>
                    {/* Internal Forms */}
                    {forms.map((form: Form) => (
                      <Grid item xs={12} md={6} lg={4} key={`internal-${form.id}`}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                          <CardContent sx={{ flexGrow: 1 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                              <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e3a8a' }}>
                                {form.title}
                              </Typography>
                              <Chip 
                                label={form.is_active ? 'Active' : 'Inactive'} 
                                color={form.is_active ? 'success' : 'default'} 
                                size="small" 
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                              {form.description || 'No description provided'}
                            </Typography>
                            <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                              <Chip 
                                label={`${form.submission_count} submissions`} 
                                size="small" 
                                color="primary"
                              />
                              <Chip 
                                label={form.is_public ? 'Public' : 'Private'} 
                                size="small" 
                                color={form.is_public ? 'success' : 'default'}
                              />
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              Created: {new Date(form.created_at).toLocaleDateString()}
                            </Typography>
                          </CardContent>
                          <CardActions sx={{ p: 2, pt: 0 }}>
                            <Button 
                              size="small" 
                              onClick={() => handleEditForm(form)}
                              startIcon={<Edit />}
                              sx={{ color: '#1e3a8a' }}
                            >
                              Edit
                            </Button>
                            <Button 
                              size="small" 
                              onClick={() => handleShareForm(form)}
                              startIcon={<Share />}
                              sx={{ color: '#059669' }}
                            >
                              Share
                            </Button>
                            <IconButton 
                              size="small" 
                              onClick={() => handleDeleteForm(form.id)}
                              sx={{ color: '#dc2626', ml: 'auto' }}
                            >
                              <Delete />
                            </IconButton>
                          </CardActions>
                        </Card>
                      </Grid>
                    ))}
                    
                    {/* External Forms */}
                    {externalForms.map((form) => (
                      <Grid item xs={12} md={6} lg={4} key={`external-${form.id}`}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                          <CardContent sx={{ flexGrow: 1 }}>
                            <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                              <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e3a8a' }}>
                                {form.title}
                              </Typography>
                              <Chip 
                                label="External" 
                                color="info" 
                                size="small" 
                                icon={<LinkIcon />}
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                              {form.description || 'No description provided'}
                            </Typography>
                            <Box 
                              sx={{ 
                                p: 1, 
                                bgcolor: 'grey.100', 
                                borderRadius: 1, 
                                mb: 2,
                                wordBreak: 'break-all'
                              }}
                            >
                              <Typography variant="caption" color="text.secondary">
                                {form.url}
                              </Typography>
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              Added: {new Date(form.createdAt).toLocaleDateString()}
                            </Typography>
                          </CardContent>
                          <CardActions sx={{ p: 2, pt: 0 }}>
                            <Button 
                              size="small" 
                              onClick={() => window.open(form.url, '_blank')}
                              startIcon={<LinkIcon />}
                              sx={{ color: '#1e3a8a' }}
                            >
                              Open
                            </Button>
                            <Button 
                              size="small" 
                              onClick={() => handleShareExternalForm(form)}
                              startIcon={<QrCode />}
                              sx={{ color: '#059669' }}
                            >
                              QR Code
                            </Button>
                            <IconButton 
                              size="small" 
                              onClick={() => handleDeleteExternalForm(form.id)}
                              sx={{ color: '#dc2626', ml: 'auto' }}
                            >
                              <Delete />
                            </IconButton>
                          </CardActions>
                        </Card>
                      </Grid>
                    ))}
                  </>
                )}
              </Grid>
            )}
            {forms.length > 0 && (
              <Box display="flex" justifyContent="center" mt={3}>
                <Button 
                  variant="outlined" 
                  onClick={() => setPage(page - 1)} 
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Typography variant="body1" sx={{ mx: 2 }}>
                  Page {page}
                </Typography>
                <Button 
                  variant="outlined" 
                  onClick={() => setPage(page + 1)} 
                  disabled={forms.length < 10}
                >
                  Next
                </Button>
              </Box>
            )}
          </Box>
        )}

        {/* Share dialog */}
        <Dialog open={shareDialogOpen} onClose={() => setShareDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Share Your Form</DialogTitle>
          <DialogContent>
            {shareUrl && (
              <Box textAlign="center" my={2}>
                <QRCodeSVG value={shareUrl} size={200} />
                <Box mt={2} p={2} bgcolor="grey.100" borderRadius={1}>
                  <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                    {shareUrl}
                  </Typography>
                </Box>
                <Box mt={2} display="flex" gap={1} justifyContent="center">
                  <Button variant="outlined" startIcon={<ContentCopy />} onClick={handleCopyLink}>
                    Copy Link
                  </Button>
                  <Button 
                    variant="outlined" 
                    startIcon={<Download />}
                    onClick={() => {
                      const canvas = document.createElement('canvas');
                      const ctx = canvas.getContext('2d');
                      const svg = document.querySelector('svg');
                      if (svg && ctx) {
                        const svgData = new XMLSerializer().serializeToString(svg);
                        const img = new Image();
                        img.onload = () => {
                          canvas.width = img.width;
                          canvas.height = img.height;
                          ctx.drawImage(img, 0, 0);
                          const link = document.createElement('a');
                          link.download = 'qr-code.png';
                          link.href = canvas.toDataURL();
                          link.click();
                        };
                        img.src = 'data:image/svg+xml;base64,' + btoa(svgData);
                      }
                    }}
                  >
                    Download QR
                  </Button>
                </Box>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShareDialogOpen(false)}>Close</Button>
          </DialogActions>
        </Dialog>

        {/* Add External Form Dialog */}
        <Dialog 
          open={externalFormDialogOpen} 
          onClose={() => setExternalFormDialogOpen(false)} 
          maxWidth="sm" 
          fullWidth
        >
          <DialogTitle>Add Form Link</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 1 }}>
              <TextField
                fullWidth
                label="Form Title"
                value={newExternalForm.title}
                onChange={(e) => setNewExternalForm({ ...newExternalForm, title: e.target.value })}
                margin="normal"
                required
              />
              <TextField
                fullWidth
                label="Form URL"
                value={newExternalForm.url}
                onChange={(e) => setNewExternalForm({ ...newExternalForm, url: e.target.value })}
                margin="normal"
                required
                placeholder="https://example.com/form"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <LinkIcon />
                    </InputAdornment>
                  ),
                }}
              />
              <TextField
                fullWidth
                label="Description (Optional)"
                value={newExternalForm.description}
                onChange={(e) => setNewExternalForm({ ...newExternalForm, description: e.target.value })}
                margin="normal"
                multiline
                rows={3}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setExternalFormDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleAddExternalForm} 
              variant="contained"
              sx={{ bgcolor: '#1e3a8a' }}
            >
              Add Form
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          onClose={(_event?: React.SyntheticEvent | Event, reason?: string) => {
            if (reason !== 'clickaway') {
              setSnackbar({ ...snackbar, open: false });
            }
          }}
        >
          <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </React.Fragment>
  );
} 