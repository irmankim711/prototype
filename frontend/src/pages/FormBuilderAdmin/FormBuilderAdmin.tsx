import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { createForm, updateForm, fetchForms, deleteForm } from '../../services/api';
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

import type { DraggableProvided, DroppableProvided, DropResult, DraggableStateSnapshot } from '@hello-pangea/dnd';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import {
  Add,
  Delete,
  Edit,
  Share,
  ContentCopy,
  Download,
  DragIndicator,
  Assessment,
  TextFields,
  Email,
  Numbers,
  DateRange,
  CheckBox,
  RadioButtonChecked,
  ArrowDropDown,
  AttachFile,
  Star,
  LocationOn,
  Restaurant,
  Event,
  Schedule,
  AccessTime,
  Link,
  Phone,
  TouchApp,
  ToggleOn
} from '@mui/icons-material';

interface FormField {
  id: string;
  label: string;
  type: string;
  required: boolean;
  options: string[];
  placeholder?: string;
  description?: string;
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: string;
    min?: number;
    max?: number;
  };
  styling?: {
    width?: 'full' | 'half' | 'third' | 'quarter';
    color?: string;
    backgroundColor?: string;
    borderRadius?: number;
    fontSize?: number;
  };
  conditional?: {
    dependsOn?: string;
    showWhen?: string;
    value?: any;
  };
  defaultValue?: any;
  helpText?: string;
  icon?: string;
  order: number;
}

const FIELD_TYPES = [
  { 
    value: 'text', 
    label: 'Text Input', 
    icon: <TextFields />, 
    description: 'Single line text input',
    category: 'Basic',
    color: '#2196F3',
    preview: 'Enter your text here...'
  },
  { 
    value: 'email', 
    label: 'Email', 
    icon: <Email />, 
    description: 'Email address field',
    category: 'Basic',
    color: '#FF9800',
    preview: 'user@example.com'
  },
  { 
    value: 'number', 
    label: 'Number', 
    icon: <Numbers />, 
    description: 'Numeric input field',
    category: 'Basic',
    color: '#4CAF50',
    preview: '123'
  }
];

export default function FormBuilderAdmin() {
  const [showExistingForms, setShowExistingForms] = useState(false);
  const [formTitle, setFormTitle] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [previewMode, setPreviewMode] = useState(false);
  const [fields, setFields] = useState<FormField[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [field, setField] = useState<FormField>({
    id: '',
    label: '',
    type: 'text',
    required: false,
    options: [],
    order: 0
  });
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' | 'info' });

  const { data: forms = [], isLoading: formsLoading, error: formsError } = useQuery({
    queryKey: ['forms'],
    queryFn: fetchForms
  });

  const createMutation = useMutation({
    mutationFn: createForm,
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Form created successfully!', severity: 'success' });
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to create form', severity: 'error' });
    }
  });

  const updateMutation = useMutation({
    mutationFn: updateForm,
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Form updated successfully!', severity: 'success' });
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to update form', severity: 'error' });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteForm,
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Form deleted successfully!', severity: 'success' });
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to delete form', severity: 'error' });
    }
  });

  const handleToggleActive = () => {
    setIsActive(!isActive);
  };

  const handleNewForm = () => {
    setShowExistingForms(false);
    setFormTitle('');
    setFields([]);
    setField({
      id: '',
      label: '',
      type: 'text',
      required: false,
      options: [],
      order: 0
    });
  };

  const handleEditForm = (form: any) => {
    setShowExistingForms(false);
    setFormTitle(form.title);
    setFields(form.fields || []);
  };

  const handleCopyLink = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      setSnackbar({ open: true, message: 'Link copied to clipboard!', severity: 'success' });
    }
  };

  const handleDeleteForm = (formId: string) => {
    if (window.confirm('Are you sure you want to delete this form?')) {
      deleteMutation.mutate(formId);
    }
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
                  forms.map((form: any) => (
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
                            onClick={() => {
                              setShareDialogOpen(true);
                            }}
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
          <Box>
            <Paper sx={{ p: 3, mb: 3 }}>
              <TextField
                label="Form Title"
                value={formTitle}
                onChange={(e) => setFormTitle(e.target.value)}
                fullWidth
                sx={{ mb: 2 }}
              />
              <Box display="flex" alignItems="center" mb={2}>
                <Switch checked={isActive} onChange={handleToggleActive} />
                <Typography sx={{ ml: 1 }}>{isActive ? 'Active' : 'Inactive'}</Typography>
              </Box>
            </Paper>
            
            <Box mb={2}>
              <Button variant={previewMode ? 'outlined' : 'contained'} onClick={() => setPreviewMode(false)} sx={{ mr: 1 }}>
                Edit Mode
              </Button>
              <Button variant={previewMode ? 'contained' : 'outlined'} onClick={() => setPreviewMode(true)}>
                Preview
              </Button>
            </Box>
            
            <Divider sx={{ mb: 3 }} />

            {!previewMode && (
              <Typography variant="h6" gutterBottom>
                Form Builder - Edit Mode
              </Typography>
            )}

            {previewMode && (
              <Box>
                <Paper sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Form Preview
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Preview mode is active. Form fields will be displayed here.
                  </Typography>
                </Paper>
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