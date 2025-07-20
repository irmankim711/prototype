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
  Tooltip
} from '@mui/material';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Switch,
  Divider,
  Stack,
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
  Assessment,
  Visibility,
  VisibilityOff,
  Settings,
  Preview,
  Save
} from '@mui/icons-material';

import FormBuilder from '../../components/FormBuilder/FormBuilder';

export default function FormBuilderAdmin() {
  const [showExistingForms, setShowExistingForms] = useState(false);
  const [editingFormId, setEditingFormId] = useState<number | null>(null);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' | 'info' });

  const { data: formsData, isLoading: formsLoading, error: formsError, refetch } = useQuery({
    queryKey: ['forms'],
    queryFn: () => formBuilderAPI.getForms()
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
    setShowExistingForms(false);
    setEditingFormId(null);
  };

  const handleEditForm = (form: Form) => {
    setShowExistingForms(false);
    setEditingFormId(form.id);
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

  const handleFormSave = (form: Form) => {
    setSnackbar({ open: true, message: 'Form saved successfully!', severity: 'success' });
    setShowExistingForms(true);
    setEditingFormId(null);
    refetch();
  };

  const handleFormCancel = () => {
    setShowExistingForms(true);
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
              variant={showExistingForms ? 'contained' : 'outlined'} 
              onClick={() => setShowExistingForms(true)}
              sx={{ mr: 1 }}
            >
              My Forms
            </Button>
            <Button 
              variant={!showExistingForms ? 'contained' : 'outlined'} 
              onClick={handleNewForm}
              startIcon={<Add />}
            >
              New Form
            </Button>
          </Box>
        </Box>

        {showExistingForms ? (
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
                {forms.length === 0 ? (
                  <Grid item xs={12}>
                    <Box textAlign="center" p={4}>
                      <Typography variant="h6" color="text.secondary">No forms found</Typography>
                      <Typography variant="body2" color="text.secondary" mb={2}>Create your first form to get started</Typography>
                      <Button variant="contained" onClick={handleNewForm} startIcon={<Add />}>
                        Create New Form
                      </Button>
                    </Box>
                  </Grid>
                ) : (
                  forms.map((form: Form) => (
                    <Grid item xs={12} md={6} lg={4} key={form.id}>
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
                  ))
                )}
              </Grid>
            )}
          </Box>
        ) : (
          <FormBuilder 
            formId={editingFormId || undefined}
            onSave={handleFormSave}
            onCancel={handleFormCancel}
          />
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
                  <Button variant="outlined" startIcon={<Download />}>
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