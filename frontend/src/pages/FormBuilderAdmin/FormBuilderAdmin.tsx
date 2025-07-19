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
  RestaurantOutlined,
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

interface FormTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  fields: FormField[];
  preview: string;
  tags: string[];
}

interface FormStyle {
  theme: 'light' | 'dark' | 'auto';
  primaryColor: string;
  secondaryColor: string;
  backgroundColor: string;
  textColor: string;
  borderRadius: number;
  spacing: number;
  fontFamily: string;
  fontSize: number;
  buttonStyle: 'filled' | 'outlined' | 'text';
  inputStyle: 'filled' | 'outlined' | 'standard';
  layout: 'single' | 'multi' | 'wizard';
  animation: boolean;
  shadows: boolean;
  gradients: boolean;
}

interface ValidationRule {
  type: 'required' | 'email' | 'url' | 'number' | 'pattern' | 'minLength' | 'maxLength' | 'min' | 'max';
  value?: any;
  message: string;
}

interface FormSettings {
  allowMultipleSubmissions: boolean;
  requireAuthentication: boolean;
  showProgressBar: boolean;
  enableAutoSave: boolean;
  redirectUrl?: string;
  successMessage: string;
  errorMessage: string;
  emailNotifications: boolean;
  webhookUrl?: string;
  captcha: boolean;
  analytics: boolean;
  exportFormat: 'json' | 'csv' | 'excel';
  responseLimit?: number;
  expirationDate?: Date;
  password?: string;
  allowedDomains?: string[];
  customCSS?: string;
  customJS?: string;
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
  },
  { 
    value: 'textarea', 
    label: 'Text Area', 
    icon: <TextFields />, 
    description: 'Multi-line text input',
    category: 'Basic',
    color: '#9C27B0',
    preview: 'Enter multiple lines...'
  },
  { 
    value: 'select', 
    label: 'Dropdown', 
    icon: <ArrowDropDown />, 
    description: 'Select from options',
    category: 'Choice',
    color: '#FF5722',
    preview: 'Choose an option...'
  },
  { 
    value: 'radio', 
    label: 'Radio Buttons', 
    icon: <RadioButtonChecked />, 
    description: 'Single choice selection',
    category: 'Choice',
    color: '#E91E63',
    preview: 'Option 1, Option 2, Option 3'
  },
  { 
    value: 'checkbox', 
    label: 'Checkboxes', 
    icon: <CheckBox />, 
    description: 'Multiple choice selection',
    category: 'Choice',
    color: '#00BCD4',
    preview: '☑ Option 1, ☐ Option 2'
  },
  { 
    value: 'date', 
    label: 'Date Picker', 
    icon: <DateRange />, 
    description: 'Date selection',
    category: 'Advanced',
    color: '#795548',
    preview: 'MM/DD/YYYY'
  },
  { 
    value: 'time', 
    label: 'Time Picker', 
    icon: <AccessTime />, 
    description: 'Time selection',
    category: 'Advanced',
    color: '#607D8B',
    preview: 'HH:MM AM/PM'
  },
  { 
    value: 'datetime', 
    label: 'Date & Time', 
    icon: <Schedule />, 
    description: 'Date and time selection',
    category: 'Advanced',
    color: '#3F51B5',
    preview: 'MM/DD/YYYY HH:MM'
  },
  { 
    value: 'file', 
    label: 'File Upload', 
    icon: <AttachFile />, 
    description: 'File attachment',
    category: 'Advanced',
    color: '#9E9E9E',
    preview: 'Choose file...'
  },
  { 
    value: 'rating', 
    label: 'Rating', 
    icon: <Star />, 
    description: 'Star rating input',
    category: 'Advanced',
    color: '#FFC107',
    preview: '★★★★☆'
  },
  { 
    value: 'slider', 
    label: 'Slider', 
    icon: <TouchApp />, 
    description: 'Range slider input',
    category: 'Advanced',
    color: '#8BC34A',
    preview: '━━━●━━━'
  },
  { 
    value: 'url', 
    label: 'URL', 
    icon: <Link />, 
    description: 'Website URL input',
    category: 'Basic',
    color: '#2196F3',
    preview: 'https://example.com'
  },
  { 
    value: 'phone', 
    label: 'Phone Number', 
    icon: <Phone />, 
    description: 'Phone number input',
    category: 'Basic',
    color: '#4CAF50',
    preview: '+1 (555) 123-4567'
  },
  { 
    value: 'address', 
    label: 'Address', 
    icon: <LocationOn />, 
    description: 'Address input with autocomplete',
    category: 'Advanced',
    color: '#F44336',
    preview: '123 Main St, City, State'
  },
  { 
    value: 'signature', 
    label: 'Signature', 
    icon: <ToggleOn />, 
    description: 'Digital signature pad',
    category: 'Advanced',
    color: '#673AB7',
    preview: 'Sign here...'
  },
  { 
    value: 'color', 
    label: 'Color Picker', 
    icon: <TouchApp />, 
    description: 'Color selection input',
    category: 'Advanced',
    color: '#E91E63',
    preview: '#FF5722'
  },
  { 
    value: 'password', 
    label: 'Password', 
    icon: <ToggleOn />, 
    description: 'Password input field',
    category: 'Basic',
    color: '#795548',
    preview: '••••••••'
  },
  { 
    value: 'toggle', 
    label: 'Toggle Switch', 
    icon: <ToggleOn />, 
    description: 'On/off toggle switch',
    category: 'Choice',
    color: '#00BCD4',
    preview: 'ON | OFF'
  }
];

const FORM_TEMPLATES: FormTemplate[] = [
  {
    id: 'contact',
    name: 'Contact Form',
    description: 'Basic contact form with name, email, and message',
    category: 'Business',
    preview: '/api/placeholder/300/200',
    tags: ['contact', 'business', 'basic'],
    fields: [
      { id: '1', label: 'Full Name', type: 'text', required: true, options: [], order: 1 },
      { id: '2', label: 'Email Address', type: 'email', required: true, options: [], order: 2 },
      { id: '3', label: 'Subject', type: 'text', required: false, options: [], order: 3 },
      { id: '4', label: 'Message', type: 'textarea', required: true, options: [], order: 4 }
    ]
  },
  {
    id: 'survey',
    name: 'Customer Survey',
    description: 'Customer satisfaction survey with ratings and feedback',
    category: 'Survey',
    preview: '/api/placeholder/300/200',
    tags: ['survey', 'feedback', 'rating'],
    fields: [
      { id: '1', label: 'Overall Satisfaction', type: 'rating', required: true, options: [], order: 1 },
      { id: '2', label: 'Service Quality', type: 'radio', required: true, options: ['Excellent', 'Good', 'Average', 'Poor'], order: 2 },
      { id: '3', label: 'Would you recommend us?', type: 'radio', required: true, options: ['Yes', 'No', 'Maybe'], order: 3 },
      { id: '4', label: 'Additional Comments', type: 'textarea', required: false, options: [], order: 4 }
    ]
  },
  {
    id: 'registration',
    name: 'Event Registration',
    description: 'Event registration form with personal details and preferences',
    category: 'Event',
    preview: '/api/placeholder/300/200',
    tags: ['registration', 'event', 'personal'],
    fields: [
      { id: '1', label: 'First Name', type: 'text', required: true, options: [], order: 1 },
      { id: '2', label: 'Last Name', type: 'text', required: true, options: [], order: 2 },
      { id: '3', label: 'Email', type: 'email', required: true, options: [], order: 3 },
      { id: '4', label: 'Phone', type: 'phone', required: false, options: [], order: 4 },
      { id: '5', label: 'Dietary Restrictions', type: 'checkbox', required: false, options: ['Vegetarian', 'Vegan', 'Gluten-free', 'None'], order: 5 },
      { id: '6', label: 'T-shirt Size', type: 'select', required: false, options: ['XS', 'S', 'M', 'L', 'XL', 'XXL'], order: 6 }
    ]
  },
  {
    id: 'feedback',
    name: 'Product Feedback',
    description: 'Collect detailed product feedback and suggestions',
    category: 'Feedback',
    preview: '/api/placeholder/300/200',
    tags: ['feedback', 'product', 'improvement'],
    fields: [
      { id: '1', label: 'Product Name', type: 'select', required: true, options: ['Product A', 'Product B', 'Product C'], order: 1 },
      { id: '2', label: 'Usage Frequency', type: 'radio', required: true, options: ['Daily', 'Weekly', 'Monthly', 'Rarely'], order: 2 },
      { id: '3', label: 'Feature Rating', type: 'rating', required: true, options: [], order: 3 },
      { id: '4', label: 'Improvement Suggestions', type: 'textarea', required: false, options: [], order: 4 },
      { id: '5', label: 'Would you purchase again?', type: 'toggle', required: true, options: [], order: 5 }
    ]
  },
  {
    id: 'job-application',
    name: 'Job Application',
    description: 'Comprehensive job application form',
    category: 'HR',
    preview: '/api/placeholder/300/200',
    tags: ['job', 'application', 'hr', 'career'],
    fields: [
      { id: '1', label: 'Full Name', type: 'text', required: true, options: [], order: 1 },
      { id: '2', label: 'Email', type: 'email', required: true, options: [], order: 2 },
      { id: '3', label: 'Phone', type: 'phone', required: true, options: [], order: 3 },
      { id: '4', label: 'Position Applied For', type: 'select', required: true, options: ['Software Engineer', 'Product Manager', 'Designer', 'Marketing Specialist'], order: 4 },
      { id: '5', label: 'Experience Level', type: 'radio', required: true, options: ['Entry Level', 'Mid Level', 'Senior Level', 'Executive'], order: 5 },
      { id: '6', label: 'Resume', type: 'file', required: true, options: [], order: 6 },
      { id: '7', label: 'Cover Letter', type: 'textarea', required: false, options: [], order: 7 },
      { id: '8', label: 'Available Start Date', type: 'date', required: true, options: [], order: 8 }
    ]
  }
];

const DEFAULT_FORM_STYLE: FormStyle = {
  theme: 'light',
  primaryColor: '#1976d2',
  secondaryColor: '#dc004e',
  backgroundColor: '#ffffff',
  textColor: '#333333',
  borderRadius: 8,
  spacing: 16,
  fontFamily: 'Roboto, sans-serif',
  fontSize: 14,
  buttonStyle: 'filled',
  inputStyle: 'outlined',
  layout: 'single',
  animation: true,
  shadows: true,
  gradients: false
};

const DEFAULT_FORM_SETTINGS: FormSettings = {
  allowMultipleSubmissions: false,
  requireAuthentication: false,
  showProgressBar: true,
  enableAutoSave: true,
  successMessage: 'Thank you for your submission!',
  errorMessage: 'Please check your inputs and try again.',
  emailNotifications: false,
  captcha: false,
  analytics: true,
  exportFormat: 'json'
};

// Animation constants
const ANIMATION_DURATION = 300;
const STAGGER_DELAY = 50;

const defaultField: FormField = {
  id: '',
  label: '',
  type: 'text',
  required: false,
  options: [],
  placeholder: '',
  description: '',
  validation: {},
  styling: {
    width: 'full',
    color: '#1976d2',
    backgroundColor: '#ffffff',
    borderRadius: 8,
    fontSize: 14
  },
  defaultValue: '',
  helpText: '',
  icon: '',
  order: 0
};

function TabPanel(props: { children?: React.ReactNode; index: number; value: number }) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function FormBuilderAdmin() {
  // Core state
  const [fields, setFields] = useState<FormField[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [field, setField] = useState<FormField>(defaultField);
  const [formTitle, setFormTitle] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [formId, setFormId] = useState<string | null>(null);
  
  // UI state
  const [currentView, setCurrentView] = useState<'dashboard' | 'builder' | 'templates' | 'settings'>('dashboard');
  const [currentTab, setCurrentTab] = useState(0);
  const [previewMode, setPreviewMode] = useState(false);
  const [fullscreenPreview, setFullscreenPreview] = useState(false);
  const [devicePreview, setDevicePreview] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [fieldPanelOpen, setFieldPanelOpen] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState<FormTemplate | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'date' | 'submissions'>('date');
  const [showExistingForms, setShowExistingForms] = useState(true);
  
  // Dialog states
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [formToDelete, setFormToDelete] = useState<string | null>(null);
  
  // Form configuration
  const [formStyle, setFormStyle] = useState<FormStyle>(DEFAULT_FORM_STYLE);
  const [formSettings, setFormSettings] = useState<FormSettings>(DEFAULT_FORM_SETTINGS);
  
  // Notifications
  const [snackbar, setSnackbar] = useState({ 
    open: false, 
    message: '', 
    severity: 'success' as 'success' | 'error' | 'warning' | 'info' 
  });
  
  // Loading states
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  const shareUrl = formId ? `${window.location.origin}/forms/${formId}` : '';

  // Fetch existing forms
  const { data: existingForms = [], refetch: refetchForms, isLoading: formsLoading, error: formsError } = useQuery({
    queryKey: ['forms'],
    queryFn: fetchForms,
  });

  // Type guard for forms
  const forms = Array.isArray(existingForms) ? existingForms : [];

  const handleAddField = () => {
    setFields([...fields, { ...field, options: field.options || [] }]);
    setField(defaultField);
    setEditingIndex(null);
  };

  const handleEditField = (index: number, updatedField: FormField) => {
    setField(updatedField);
    setEditingIndex(index);
  };

  const handleSaveField = () => {
    if (editingIndex !== null) {
      const updated = [...fields];
      updated[editingIndex] = field;
      setFields(updated);
      setEditingIndex(null);
    } else {
      handleAddField();
    }
    setField(defaultField);
  };

  const handleDeleteField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;
    const newFields = Array.from(fields);
    const [reorderedItem] = newFields.splice(result.source.index, 1);
    newFields.splice(result.destination.index, 0, reorderedItem);
    setFields(newFields);
  };

  const handleFieldChange = (key: keyof FormField, value: any) => {
    setField((prev: FormField) => ({ ...prev, [key]: value }));
  };

  const handleOptionChange = (idx: number, value: string) => {
    const newOptions = [...field.options];
    newOptions[idx] = value;
    setField((prev: FormField) => ({ ...prev, options: newOptions }));
  };

  const addOption = () => {
    setField((prev: FormField) => ({ ...prev, options: [...prev.options, ''] }));
  };

  const removeOption = (idx: number) => {
    setField((prev: FormField) => ({ ...prev, options: prev.options.filter((_: string, i: number) => i !== idx) }));
  };

  // Removed unused functions to clean up lint warnings

  const publishMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        title: formTitle || 'Untitled Form',
        description: '',
        fields,
        is_active: isActive,
        is_public: true,
      };
      if (formId) {
        const updated = await updateForm(formId, payload as any);
        return updated;
      }
      const created = await createForm(payload as any);
      return created;
    },
    onSuccess: (data: any) => {
      setFormId(data.id);
      setShareDialogOpen(true);
      setSnackbar({ open: true, message: 'Form published successfully!', severity: 'success' });
      refetchForms();
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to publish form', severity: 'error' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteForm,
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Form deleted successfully!', severity: 'success' });
      refetchForms();
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to delete form', severity: 'error' });
    },
  });

  const handlePublish = () => {
    publishMutation.mutate();
  };

  const handleToggleActive = () => {
    setIsActive((prev) => !prev);
    if (formId) {
      updateForm(formId, { is_active: !isActive });
    }
  };

  const handleEditForm = (form: any) => {
    // setSelectedForm(form); // Commented out for future use
    setFormId(form.id);
    setFormTitle(form.title);
    setIsActive(form.is_active);
    setFields(form.fields || []);
    setCurrentView('builder');
  };

  const handleNewForm = () => {
    // setSelectedForm(null); // Commented out for future use
    setFormId(null);
    setFormTitle('');
    setIsActive(true);
    setFields([]);
    setCurrentView('builder');
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
          {formsError && (
            <Box p={2}>
              <Alert severity="error">Failed to load forms. Please try again.</Alert>
            </Box>
          )}
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
                    <Typography variant="h6" component="h2" sx={{ fontWeight: 600, color: '#1e3a8a' }}>
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
                  <Box display="flex" alignItems="center" gap={2} sx={{ mb: 1 }}>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <AccessTime fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        Created {new Date(form.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <Schedule fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        Updated {new Date(form.updated_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>
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
                      setFormId(form.id);
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
    </Box>
  ) : (
        <Box>
          {formsLoading && (
            <Box display="flex" justifyContent="center" p={4}>
              <Typography>Loading forms...</Typography>
            </Box>
          )}
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
                    <Typography variant="h6" component="h2" sx={{ fontWeight: 600, color: '#1e3a8a' }}>
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
                  <Box display="flex" alignItems="center" gap={2} sx={{ mb: 1 }}>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <AccessTime fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        Created {new Date(form.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Box display="flex" alignItems="center" gap={0.5}>
                      <Schedule fontSize="small" color="action" />
                      <Typography variant="caption" color="text.secondary">
                        Updated {new Date(form.updated_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>
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
                      setFormId(form.id);
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
    </Box>
  )}

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
      <Stack direction="row" spacing={2}>
        <Box flex={1} maxWidth="500px">
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              {editingIndex !== null ? 'Edit Field' : 'Add Field'}
            </Typography>
            <TextField
              label="Label"
              value={field.label}
              onChange={e => handleFieldChange('label', e.target.value)}
              fullWidth
              margin="normal"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Type</InputLabel>
              <Select
                value={field.type}
                label="Type"
                onChange={e => handleFieldChange('type', e.target.value)}
              >
                {FIELD_TYPES.map(opt => (
                  <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            {(field.type === 'select' || field.type === 'radio') && (
              <Box>
                <Typography variant="subtitle2" sx={{ mt: 2 }}>
                  Options
                </Typography>
                {(field.options || []).map((opt: string, idx: number) => (
                  <Box key={idx} display="flex" alignItems="center" mb={1}>
                    <TextField
                      value={opt}
                      onChange={e => handleOptionChange(idx, e.target.value)}
                      size="small"
                      sx={{ flex: 1, mr: 1 }}
                    />
                    <IconButton size="small" onClick={() => removeOption(idx)}>
                      <Delete fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
                <Button size="small" onClick={addOption} sx={{ mt: 1 }}>
                  Add Option
                </Button>
              </Box>
            )}
            <FormControl fullWidth margin="normal">
              <Box display="flex" alignItems="center">
                <Switch
                  checked={field.required}
                  onChange={e => handleFieldChange('required', e.target.checked)}
                />
                <Typography>Required</Typography>
              </Box>
            </FormControl>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSaveField}
              sx={{ mt: 2 }}
              fullWidth
            >
              {editingIndex !== null ? 'Save Changes' : 'Add Field'}
            </Button>
          </Paper>
        </Box>
        <Box flex={2}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Form Fields
            </Typography>
            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="fields-droppable">
                {(provided: DroppableProvided) => (
                  <Box ref={provided.innerRef} {...provided.droppableProps}>
                    {fields.map((f, idx) => (
                      <Draggable key={idx} draggableId={`field-${idx}`} index={idx}>
                        {(provided: DraggableProvided, snapshot: DraggableStateSnapshot) => (
                          <Box
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            sx={{
                              p: 2,
                              mb: 2,
                              display: 'flex',
                              alignItems: 'center',
                              bgcolor: snapshot.isDragging ? 'action.hover' : 'background.paper',
                              borderRadius: 1,
                              boxShadow: 1,
                            }}
                          >
                            <Box {...provided.dragHandleProps} sx={{ mr: 2, cursor: 'grab' }}>
                              <DragIndicator />
                            </Box>
                            <Box sx={{ flex: 1 }}>
                              <Typography>{f.label} ({f.type}) {f.required && '*'}</Typography>
                            </Box>
                            <Tooltip title="Edit">
                              <IconButton onClick={() => handleEditField(idx)} size="small">
                                <Edit fontSize="small" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete">
                              <IconButton onClick={() => handleDeleteField(idx)} size="small" color="error">
                                <Delete fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </Box>
                )}
              </Droppable>
            </DragDropContext>
          </Paper>
        </Box>
      </Stack>
    )}

    {previewMode && (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Form Preview
        </Typography>
        <form>
          {fields.map((f, idx) => {
            switch (f.type) {
              case 'text':
              case 'email':
              case 'number':
              case 'date':
                return (
                  <TextField
                    key={idx}
                    label={f.label}
                    type={f.type}
                    required={f.required}
                    fullWidth
                    margin="normal"
                  />
                );
              case 'select':
                return (
                  <FormControl fullWidth margin="normal" key={idx}>
                    <InputLabel>{f.label}</InputLabel>
                    <Select label={f.label} required={f.required} defaultValue="">
                      {f.options?.map((opt: string, i: number) => (
                        <MenuItem key={i} value={opt}>{opt}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                );
              case 'checkbox':
                return (
                  <FormControl key={idx} margin="normal">
                    <Box display="flex" alignItems="center">
                      <Switch required={f.required} />
                      <Typography>{f.label}</Typography>
                    </Box>
                  </FormControl>
                );
              case 'radio':
                return (
                  <FormControl component="fieldset" key={idx} margin="normal">
                    <Typography>{f.label}</Typography>
                    {f.options?.map((opt: string, i: number) => (
                      <Box key={i} display="flex" alignItems="center">
                        <Switch />
                        <Typography>{opt}</Typography>
                      </Box>
                    ))}
                  </FormControl>
                );
              case 'file':
                return (
                  <Box key={idx} marginY={2}>
                    <Typography>{f.label}</Typography>
                    <input type="file" required={f.required} />
                  </Box>
                );
              default:
                return null;
            }
          })}
        </form>
      </Paper>
    )}

        <Box mt={4} display="flex" justifyContent="space-between">
          <Button variant="outlined" onClick={() => setShowExistingForms(true)}>
            Back to Forms
          </Button>
          <Button variant="contained" color="primary" size="large" onClick={handlePublish} disabled={publishMutation.isLoading}>
            {publishMutation.isLoading ? 'Publishing...' : formId ? 'Update Form' : 'Publish Form'}
          </Button>
        </Box>
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
      onClose={(event?: React.SyntheticEvent | Event, reason?: string) => {
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
