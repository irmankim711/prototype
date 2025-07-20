import React, { useState, useEffect, useCallback } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  Grid,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  Chip,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  InputAdornment,
  OutlinedInput
} from '@mui/material';
import {
  Add,
  Delete,
  Edit,
  Save,
  Preview,
  Settings,
  DragIndicator,
  ContentCopy,
  Download,
  Upload,
  Visibility,
  VisibilityOff,
  ExpandMore,
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
  Phone,
  Link,
  AccessTime,
  Event,
  Subject,
  Palette,
  Code,
  Help
} from '@mui/icons-material';
import type { DraggableProvided, DroppableProvided, DropResult } from '@hello-pangea/dnd';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { formBuilderAPI, formBuilderUtils, type FormField, type FormSchema, type Form, FORM_BUILDER_CONSTANTS } from '../../services/formBuilder';

interface FormBuilderProps {
  formId?: number;
  onSave?: (form: Form) => void;
  onCancel?: () => void;
}

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
      id={`form-builder-tabpanel-${index}`}
      aria-labelledby={`form-builder-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function FormBuilder({ formId, onSave, onCancel }: FormBuilderProps) {
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState<Partial<Form>>({
    title: '',
    description: '',
    schema: { fields: [] },
    is_active: true,
    is_public: false
  });
  const [selectedField, setSelectedField] = useState<FormField | null>(null);
  const [fieldDialogOpen, setFieldDialogOpen] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' | 'info' });

  // Fetch form data if editing
  const { data: existingForm, isLoading: formLoading } = useQuery({
    queryKey: ['form', formId],
    queryFn: () => formBuilderAPI.getForm(formId!),
    enabled: !!formId
  });

  // Fetch field types
  const { data: fieldTypes, isLoading: fieldTypesLoading } = useQuery({
    queryKey: ['fieldTypes'],
    queryFn: formBuilderAPI.getFieldTypes
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: formBuilderAPI.createForm,
    onSuccess: (data) => {
      setSnackbar({ open: true, message: 'Form created successfully!', severity: 'success' });
      onSave?.(data.form);
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to create form', severity: 'error' });
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => formBuilderAPI.updateForm(id, data),
    onSuccess: (data) => {
      setSnackbar({ open: true, message: 'Form updated successfully!', severity: 'success' });
      onSave?.(data.form);
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to update form', severity: 'error' });
    }
  });

  // Load existing form data
  useEffect(() => {
    if (existingForm) {
      setFormData(existingForm);
    }
  }, [existingForm]);

  // Handle drag and drop
  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const fields = [...(formData.schema?.fields || [])];
    const [reorderedField] = fields.splice(result.source.index, 1);
    fields.splice(result.destination.index, 0, reorderedField);

    // Update field orders
    fields.forEach((field, index) => {
      field.order = index;
    });

    setFormData(prev => ({
      ...prev,
      schema: { ...prev.schema!, fields }
    }));
  };

  // Add new field
  const handleAddField = (fieldType: string) => {
    const newField: FormField = {
      id: formBuilderUtils.generateFieldId(),
      label: `New ${fieldType} field`,
      type: fieldType,
      required: false,
      order: (formData.schema?.fields?.length || 0),
      options: fieldType === 'select' || fieldType === 'radio' || fieldType === 'checkbox' ? ['Option 1', 'Option 2'] : undefined
    };

    setFormData(prev => ({
      ...prev,
      schema: {
        ...prev.schema!,
        fields: [...(prev.schema?.fields || []), newField]
      }
    }));

    setSelectedField(newField);
    setFieldDialogOpen(true);
  };

  // Update field
  const handleUpdateField = (fieldId: string, updates: Partial<FormField>) => {
    setFormData(prev => ({
      ...prev,
      schema: {
        ...prev.schema!,
        fields: prev.schema?.fields.map(field =>
          field.id === fieldId ? { ...field, ...updates } : field
        ) || []
      }
    }));
  };

  // Delete field
  const handleDeleteField = (fieldId: string) => {
    setFormData(prev => ({
      ...prev,
      schema: {
        ...prev.schema!,
        fields: prev.schema?.fields.filter(field => field.id !== fieldId) || []
      }
    }));
  };

  // Save form
  const handleSave = () => {
    const errors = formBuilderUtils.validateFormSchema(formData.schema!);
    if (errors.length > 0) {
      setSnackbar({ open: true, message: `Validation errors: ${errors.join(', ')}`, severity: 'error' });
      return;
    }

    if (formId) {
      updateMutation.mutate({ id: formId, data: formData });
    } else {
      createMutation.mutate(formData as any);
    }
  };

  // Get field icon
  const getFieldIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      text: <TextFields />,
      textarea: <Subject />,
      email: <Email />,
      number: <Numbers />,
      select: <ArrowDropDown />,
      radio: <RadioButtonChecked />,
      checkbox: <CheckBox />,
      date: <DateRange />,
      time: <AccessTime />,
      datetime: <Event />,
      file: <AttachFile />,
      phone: <Phone />,
      url: <Link />,
      rating: <Star />,
      location: <LocationOn />
    };
    return icons[type] || <TextFields />;
  };

  // Render field configuration dialog
  const renderFieldDialog = () => (
    <Dialog open={fieldDialogOpen} onClose={() => setFieldDialogOpen(false)} maxWidth="md" fullWidth>
      <DialogTitle>Configure Field</DialogTitle>
      <DialogContent>
        {selectedField && (
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Field Label"
                  value={selectedField.label}
                  onChange={(e) => handleUpdateField(selectedField.id, { label: e.target.value })}
                  fullWidth
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Placeholder"
                  value={selectedField.placeholder || ''}
                  onChange={(e) => handleUpdateField(selectedField.id, { placeholder: e.target.value })}
                  fullWidth
                  margin="normal"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Description"
                  value={selectedField.description || ''}
                  onChange={(e) => handleUpdateField(selectedField.id, { description: e.target.value })}
                  fullWidth
                  margin="normal"
                  multiline
                  rows={2}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={selectedField.required}
                      onChange={(e) => handleUpdateField(selectedField.id, { required: e.target.checked })}
                    />
                  }
                  label="Required"
                />
              </Grid>
              {(selectedField.type === 'select' || selectedField.type === 'radio' || selectedField.type === 'checkbox') && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>Options</Typography>
                  {selectedField.options?.map((option, index) => (
                    <TextField
                      key={index}
                      value={option}
                      onChange={(e) => {
                        const newOptions = [...(selectedField.options || [])];
                        newOptions[index] = e.target.value;
                        handleUpdateField(selectedField.id, { options: newOptions });
                      }}
                      fullWidth
                      margin="dense"
                      size="small"
                      InputProps={{
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton
                              size="small"
                              onClick={() => {
                                const newOptions = selectedField.options?.filter((_, i) => i !== index);
                                handleUpdateField(selectedField.id, { options: newOptions });
                              }}
                            >
                              <Delete />
                            </IconButton>
                          </InputAdornment>
                        )
                      }}
                    />
                  ))}
                  <Button
                    startIcon={<Add />}
                    onClick={() => {
                      const newOptions = [...(selectedField.options || []), `Option ${(selectedField.options?.length || 0) + 1}`];
                      handleUpdateField(selectedField.id, { options: newOptions });
                    }}
                    sx={{ mt: 1 }}
                  >
                    Add Option
                  </Button>
                </Grid>
              )}
            </Grid>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setFieldDialogOpen(false)}>Close</Button>
      </DialogActions>
    </Dialog>
  );

  // Render field preview
  const renderFieldPreview = (field: FormField) => {
    const previewData = formBuilderUtils.generatePreviewData({ fields: [field] });
    const value = previewData[field.id];

    switch (field.type) {
      case 'text':
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value}
            fullWidth
            disabled
            size="small"
          />
        );
      case 'textarea':
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value}
            fullWidth
            multiline
            rows={3}
            disabled
            size="small"
          />
        );
      case 'email':
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value}
            type="email"
            fullWidth
            disabled
            size="small"
          />
        );
      case 'number':
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value}
            type="number"
            fullWidth
            disabled
            size="small"
          />
        );
      case 'select':
        return (
          <FormControl fullWidth size="small">
            <InputLabel>{field.label}</InputLabel>
            <Select value={value} label={field.label} disabled>
              {field.options?.map((option) => (
                <MenuItem key={option} value={option}>{option}</MenuItem>
              ))}
            </Select>
          </FormControl>
        );
      case 'radio':
        return (
          <FormControl component="fieldset" size="small">
            <Typography variant="subtitle2" gutterBottom>{field.label}</Typography>
            {field.options?.map((option) => (
              <FormControlLabel
                key={option}
                control={<RadioButtonChecked disabled />}
                label={option}
              />
            ))}
          </FormControl>
        );
      case 'checkbox':
        return (
          <FormControl component="fieldset" size="small">
            <Typography variant="subtitle2" gutterBottom>{field.label}</Typography>
            {field.options?.slice(0, 2).map((option) => (
              <FormControlLabel
                key={option}
                control={<CheckBox disabled />}
                label={option}
              />
            ))}
          </FormControl>
        );
      case 'rating':
        return (
          <Box>
            <Typography variant="subtitle2" gutterBottom>{field.label}</Typography>
            <Box display="flex" gap={0.5}>
              {[1, 2, 3, 4, 5].map((star) => (
                <Star key={star} color={star <= value ? 'primary' : 'disabled'} />
              ))}
            </Box>
          </Box>
        );
      default:
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value}
            fullWidth
            disabled
            size="small"
          />
        );
    }
  };

  if (formLoading || fieldTypesLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading form builder...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            {formId ? 'Edit Form' : 'Create New Form'}
          </Typography>
          <Box display="flex" gap={1}>
            <Button
              variant={previewMode ? 'outlined' : 'contained'}
              onClick={() => setPreviewMode(!previewMode)}
              startIcon={previewMode ? <Edit /> : <Preview />}
            >
              {previewMode ? 'Edit Mode' : 'Preview'}
            </Button>
            <Button
              variant="contained"
              onClick={handleSave}
              startIcon={<Save />}
              disabled={createMutation.isPending || updateMutation.isPending}
            >
              Save Form
            </Button>
            {onCancel && (
              <Button variant="outlined" onClick={onCancel}>
                Cancel
              </Button>
            )}
          </Box>
        </Box>
      </Paper>

      <Box sx={{ flex: 1, display: 'flex', gap: 2 }}>
        {/* Left Panel - Form Configuration */}
        <Paper sx={{ width: 300, p: 2 }}>
          <Typography variant="h6" gutterBottom>Form Settings</Typography>
          <TextField
            label="Form Title"
            value={formData.title}
            onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
            fullWidth
            margin="normal"
          />
          <TextField
            label="Description"
            value={formData.description || ''}
            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
            fullWidth
            margin="normal"
            multiline
            rows={3}
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
              />
            }
            label="Active"
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_public}
                onChange={(e) => setFormData(prev => ({ ...prev, is_public: e.target.checked }))}
              />
            }
            label="Public"
          />

          <Divider sx={{ my: 2 }} />

          <Typography variant="h6" gutterBottom>Field Types</Typography>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Basic" />
            <Tab label="Advanced" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <List dense>
              {fieldTypes?.categories?.Basic?.map((type) => (
                <ListItem key={type} disablePadding>
                  <ListItemButton onClick={() => handleAddField(type)}>
                    <ListItemIcon>{getFieldIcon(type)}</ListItemIcon>
                    <ListItemText primary={fieldTypes?.field_types[type]?.label || type} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <List dense>
              {Object.entries(fieldTypes?.categories || {}).map(([category, types]) => (
                <Accordion key={category}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="subtitle2">{category}</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List dense>
                      {types.map((type) => (
                        <ListItem key={type} disablePadding>
                          <ListItemButton onClick={() => handleAddField(type)}>
                            <ListItemIcon>{getFieldIcon(type)}</ListItemIcon>
                            <ListItemText primary={fieldTypes?.field_types[type]?.label || type} />
                          </ListItemButton>
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>
              ))}
            </List>
          </TabPanel>
        </Paper>

        {/* Center Panel - Form Builder */}
        <Paper sx={{ flex: 1, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {previewMode ? 'Form Preview' : 'Form Builder'}
          </Typography>

          {previewMode ? (
            // Preview Mode
            <Box sx={{ p: 2, border: '1px dashed #ccc', borderRadius: 1 }}>
              {formData.schema?.fields.map((field) => (
                <Box key={field.id} sx={{ mb: 2 }}>
                  {renderFieldPreview(field)}
                </Box>
              ))}
            </Box>
          ) : (
            // Builder Mode
            <DragDropContext onDragEnd={handleDragEnd}>
              <Droppable droppableId="form-fields">
                {(provided: DroppableProvided) => (
                  <Box
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                    sx={{ minHeight: 200 }}
                  >
                    {formData.schema?.fields.map((field, index) => (
                      <Draggable key={field.id} draggableId={field.id} index={index}>
                        {(provided: DraggableProvided) => (
                          <Card
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            sx={{ mb: 2, cursor: 'pointer' }}
                            onClick={() => {
                              setSelectedField(field);
                              setFieldDialogOpen(true);
                            }}
                          >
                            <CardContent>
                              <Box display="flex" alignItems="center" gap={1}>
                                <Box {...provided.dragHandleProps}>
                                  <DragIndicator color="action" />
                                </Box>
                                <Box sx={{ flex: 1 }}>
                                  <Box display="flex" alignItems="center" gap={1}>
                                    {getFieldIcon(field.type)}
                                    <Typography variant="subtitle1">{field.label}</Typography>
                                    {field.required && <Chip label="Required" size="small" color="primary" />}
                                  </Box>
                                  {field.description && (
                                    <Typography variant="body2" color="text.secondary">
                                      {field.description}
                                    </Typography>
                                  )}
                                </Box>
                                <IconButton
                                  size="small"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteField(field.id);
                                  }}
                                >
                                  <Delete />
                                </IconButton>
                              </Box>
                            </CardContent>
                          </Card>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </Box>
                )}
              </Droppable>
            </DragDropContext>
          )}
        </Paper>
      </Box>

      {/* Field Configuration Dialog */}
      {renderFieldDialog()}

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
} 