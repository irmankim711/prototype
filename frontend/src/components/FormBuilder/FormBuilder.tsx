/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable no-empty */
import React from "react";
import { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Box,
  Typography,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Grid,
  Card,
  CardContent,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  Chip,
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
  Radio,
  Checkbox,
} from "@mui/material";
import {
  Add,
  Delete,
  Edit,
  Save,
  Preview,
  DragIndicator,
  ExpandMore,
  TextFields,
  Email,
  Phone,
  AttachFile,
  LocationOn,
  Star,
  ArrowDropDown,
  Subject,
  Numbers,
  RadioButtonChecked,
  CheckBox,
  DateRange,
  AccessTime,
  Event as EventIcon,
  Link as LinkIcon,
} from "@mui/icons-material";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";
import type {
  DropResult,
  DroppableProvided,
  DraggableProvided,
} from "@hello-pangea/dnd";
import {
  formBuilderAPI,
  type Form,
  type FormField,
  formBuilderUtils,
} from "../../services/formBuilder";
import FormQRManager from "../forms/FormQRManager";

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

export default function FormBuilder({
  formId,
  onSave,
  onCancel,
}: FormBuilderProps) {
  const [tabValue, setTabValue] = useState(0);
  const [formData, setFormData] = useState<Partial<Form>>({
    title: "",
    description: "",
    schema: { fields: [] },
    is_active: true,
    is_public: false,
  });
  const [selectedField, setSelectedField] = useState<FormField | null>(null);
  const [fieldDialogOpen, setFieldDialogOpen] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success" as "success" | "error" | "warning" | "info",
  });
  const [savedForms, setSavedForms] = useState<any[]>([]);

  // Fetch form data only if editing existing form (disabled for new forms)
  const { data: existingForm, isLoading: formLoading } = useQuery(
    ["form", formId],
    () => formBuilderAPI.getForm(formId!),
    {
      enabled: !!formId, // Only enabled when editing existing form
      staleTime: 1000 * 60 * 5, // 5 minutes cache
      retry: 0, // No retries for faster response
    }
  );

  // Fetch field types with immediate fallback (no loading wait)
  const { data: fieldTypes, isLoading: fieldTypesLoading } = useQuery(
    ["fieldTypes"],
    formBuilderAPI.getFieldTypes,
    {
      staleTime: 1000 * 60 * 10, // 10 minutes cache
      cacheTime: 1000 * 60 * 30, // 30 minutes cache retention
      retry: 0, // NO RETRIES - use fallback immediately
      enabled: false, // DISABLED - we'll use fallback primarily
    }
  );

  // Mutations
  const createMutation = useMutation({
    mutationFn: formBuilderAPI.createForm,
    onSuccess: (data: any) => {
      // Persist a backup and the canonical saved form
      const savedForm = data.form || { ...formData, id: Date.now() };
      const formBackup = {
        ...formData,
        id: savedForm.id || Date.now(),
        created_at: new Date().toISOString(),
      };
      localStorage.setItem(
        `form_backup_${formBackup.id}`,
        JSON.stringify(formBackup)
      );
      // Store last saved form for other pages (e.g., listings) to highlight
      try {
        localStorage.setItem("last_saved_form", JSON.stringify(savedForm));
      } catch {}

      // Update builder state with the saved form (so QR tab and IDs work immediately)
      setFormData(savedForm);

      // Update Saved tab list
      setSavedForms((prev) => {
        const list = Array.isArray(prev) ? [...prev] : [];
        const idx = list.findIndex((f: any) => f?.id === savedForm.id);
        if (idx >= 0) list[idx] = savedForm;
        else list.unshift(savedForm);
        try { localStorage.setItem("saved_forms", JSON.stringify(list)); } catch {}
        return list;
      });

      // Notify listeners that forms changed (list pages may refresh)
      try {
        window.dispatchEvent(
          new CustomEvent("forms:updated", { detail: { formId: savedForm.id } })
        );
      } catch {}

      setSnackbar({
        open: true,
        message: "Form created successfully!",
        severity: "success",
      });
      onSave?.(savedForm as any);
    },
    onError: () => {
      // Fallback: Save to local storage even if API fails
      const formBackup = {
        ...formData,
        id: `local_${Date.now()}`,
        created_at: new Date().toISOString(),
        local_only: true,
      };
      localStorage.setItem(
        `form_backup_${formBackup.id}`,
        JSON.stringify(formBackup)
      );

      setSnackbar({
        open: true,
        message: "Form saved locally (server issue - will sync later)",
        severity: "warning",
      });
      onSave?.(formBackup as any);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      formBuilderAPI.updateForm(id, data),
    onSuccess: (data: any) => {
      const updatedForm = data.form || formData;

      // Update local state so the builder reflects saved values
      setFormData(updatedForm);

      // Update Saved tab list
      setSavedForms((prev) => {
        const list = Array.isArray(prev) ? [...prev] : [];
        const idx = list.findIndex((f: any) => f?.id === updatedForm?.id);
        if (idx >= 0) list[idx] = updatedForm;
        else if (updatedForm) list.unshift(updatedForm as any);
        try { localStorage.setItem("saved_forms", JSON.stringify(list)); } catch {}
        return list;
      });

      // Store last saved form for cross-page usage
      try {
        localStorage.setItem("last_saved_form", JSON.stringify(updatedForm));
      } catch {}

      // Dispatch cross-page update event
      try {
        window.dispatchEvent(
          new CustomEvent("forms:updated", { detail: { formId: updatedForm?.id } })
        );
      } catch {}

      setSnackbar({
        open: true,
        message: "Form updated successfully!",
        severity: "success",
      });
      onSave?.(updatedForm as any);
    },
    onError: () => {
      setSnackbar({
        open: true,
        message: "Failed to update form",
        severity: "error",
      });
    },
  });

  // Load existing form data
  useEffect(() => {
    if (existingForm) {
      setFormData(existingForm);
    }
  }, [existingForm]);

  // Load saved forms list from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem("saved_forms");
      if (raw) {
        const arr = JSON.parse(raw);
        if (Array.isArray(arr)) setSavedForms(arr);
      }
    } catch {}
  }, []);

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

    setFormData((prev: any) => ({
      ...prev,
      schema: { ...prev.schema!, fields },
    }));
  };

  // Add new field
  const handleAddField = (fieldType: string) => {
    const newField: FormField = {
      id: formBuilderUtils.generateFieldId(),
      label: `New ${fieldType} field`,
      type: fieldType,
      required: false,
      order: formData.schema?.fields?.length || 0,
      options:
        fieldType === "select" ||
        fieldType === "radio" ||
        fieldType === "checkbox"
          ? ["Option 1", "Option 2"]
          : undefined,
    };

    setFormData((prev: any) => ({
      ...prev,
      schema: {
        ...prev.schema!,
        fields: [...(prev.schema?.fields || []), newField],
      },
    }));

    setSelectedField(newField);
    setFieldDialogOpen(true);
  };

  // Update field
  const handleUpdateField = (fieldId: string, updates: Partial<FormField>) => {
    // Update schema
    setFormData((prev: any) => ({
      ...prev,
      schema: {
        ...prev.schema!,
        fields:
          prev.schema?.fields.map((field: any) =>
            field.id === fieldId ? { ...field, ...updates } : field
          ) || [],
      },
    }));

    // Keep selected field in sync so dialog inputs update immediately
    setSelectedField((prev) =>
      prev && prev.id === fieldId ? { ...prev, ...updates } : prev
    );
  };

  // Delete field
  const handleDeleteField = (fieldId: string) => {
    setFormData((prev: any) => ({
      ...prev,
      schema: {
        ...prev.schema!,
        fields:
          prev.schema?.fields.filter((field: any) => field.id !== fieldId) ||
          [],
      },
    }));
  };

  // Save form (normalize payload for backend validation)
  const handleSave = () => {
    const errors = formBuilderUtils.validateFormSchema(formData.schema!);
    if (errors.length > 0) {
      setSnackbar({
        open: true,
        message: `Validation errors: ${errors.join(", ")}`,
        severity: "error",
      });
      return;
    }

    // Map field types and options to match backend marshmallow schema
    const mapFieldType = (t: string) => {
      switch (t) {
        case "phone":
          return "tel";
        case "datetime":
          return "datetime-local";
        case "rating":
          return "number";
        case "location":
          return "text";
        default:
          return t;
      }
    };

    const normalizedFields = (formData.schema?.fields || []).map((f: any, idx: number) => {
      const needsOptions = ["select", "radio", "checkbox"].includes(f.type);
      const options = needsOptions
        ? (f.options || []).map((o: any) => ({ value: String(o), label: String(o) }))
        : undefined;

      return {
        id: f.id,
        type: mapFieldType(f.type),
        label: f.label || `Field ${idx + 1}`,
        required: !!f.required,
        placeholder: f.placeholder,
        options,
      };
    });

    const normalizedData: any = {
      title: (formData.title || "").trim(),
      description: (formData.description || "").trim() || undefined,
      is_public: !!formData.is_public,
      is_active: formData.is_active !== false,
      schema: { fields: normalizedFields },
    };

    if (formId) {
      updateMutation.mutate({ id: formId, data: normalizedData });
    } else {
      createMutation.mutate(normalizedData);
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
      datetime: <EventIcon />,
      file: <AttachFile />,
      phone: <Phone />,
      url: <LinkIcon />,
      rating: <Star />,
      location: <LocationOn />,
    };
    return icons[type] || <TextFields />;
  };

  // Render field configuration dialog
  const renderFieldDialog = () => (
    <Dialog
      open={fieldDialogOpen}
      onClose={() => setFieldDialogOpen(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>Configure Field</DialogTitle>
      <DialogContent>
        {selectedField && (
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Field Label"
                  value={selectedField.label}
                  onChange={(e: any) =>
                    handleUpdateField(selectedField.id, {
                      label: e.target.value,
                    })
                  }
                  fullWidth
                  margin="normal"
                  autoComplete="on"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Placeholder"
                  value={selectedField.placeholder || ""}
                  onChange={(e: any) =>
                    handleUpdateField(selectedField.id, {
                      placeholder: e.target.value,
                    })
                  }
                  fullWidth
                  margin="normal"
                  autoComplete="on"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Description"
                  value={selectedField.description || ""}
                  onChange={(e: any) =>
                    handleUpdateField(selectedField.id, {
                      description: e.target.value,
                    })
                  }
                  fullWidth
                  margin="normal"
                  multiline
                  rows={2}
                  autoComplete="on"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={selectedField.required}
                      onChange={(e: any) =>
                        handleUpdateField(selectedField.id, {
                          required: e.target.checked,
                        })
                      }
                    />
                  }
                  label="Required"
                />
              </Grid>
              {(selectedField.type === "select" ||
                selectedField.type === "radio" ||
                selectedField.type === "checkbox") && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" gutterBottom>
                    Options
                  </Typography>
                  {selectedField.options?.map((option, index) => (
                    <TextField
                      key={index}
                      value={option}
                      onChange={(e: any) => {
                        const newOptions = [...(selectedField.options || [])];
                        newOptions[index] = e.target.value;
                        handleUpdateField(selectedField.id, {
                          options: newOptions,
                        });
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
                                const newOptions =
                                  selectedField.options?.filter(
                                    (_, i) => i !== index
                                  );
                                handleUpdateField(selectedField.id, {
                                  options: newOptions,
                                });
                              }}
                            >
                              <Delete />
                            </IconButton>
                          </InputAdornment>
                        ),
                      }}
                    />
                  ))}
                  <Button
                    startIcon={<Add />}
                    onClick={() => {
                      const newOptions = [
                        ...(selectedField.options || []),
                        `Option ${(selectedField.options?.length || 0) + 1}`,
                      ];
                      handleUpdateField(selectedField.id, {
                        options: newOptions,
                      });
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
    const previewData = formBuilderUtils.generatePreviewData({
      fields: [field],
    });
    const value = previewData[field.id];

    switch (field.type) {
      case "text":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value}
            fullWidth
            disabled
            size="small"
            autoComplete="on"
          />
        );
      case "textarea":
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
            autoComplete="on"
          />
        );
      case "email":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value}
            type="email"
            fullWidth
            disabled
            size="small"
            autoComplete="email"
          />
        );
      case "number":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value}
            type="number"
            fullWidth
            disabled
            size="small"
            autoComplete="off"
          />
        );
      case "select":
        return (
          <FormControl fullWidth size="small">
            <InputLabel>{field.label}</InputLabel>
            <Select value={value} label={field.label} disabled>
              {field.options?.map((option: any) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );
      case "radio":
        return (
          <FormControl component="fieldset" size="small">
            <Typography variant="subtitle2" gutterBottom>
              {field.label}
            </Typography>
            {field.options?.map((option: any) => (
              <FormControlLabel
                key={option}
                control={<Radio disabled />}
                label={option}
              />
            ))}
          </FormControl>
        );
      case "checkbox":
        return (
          <FormControl component="fieldset" size="small">
            <Typography variant="subtitle2" gutterBottom>
              {field.label}
            </Typography>
            {field.options?.slice(0, 2).map((option: any) => (
              <FormControlLabel
                key={option}
                control={<Checkbox disabled />}
                label={option}
              />
            ))}
          </FormControl>
        );
      case "rating":
        return (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              {field.label}
            </Typography>
            <Box display="flex" gap={0.5}>
              {[1, 2, 3, 4, 5].map((star: any) => (
                <Star
                  key={star}
                  color={star <= value ? "primary" : "disabled"}
                />
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
            autoComplete="on"
          />
        );
    }
  };

  // Enhanced fallback field types with all necessary fields
  const fallbackFieldTypes = {
    field_types: {
      text: { label: "Text Input", category: "Basic", validation: {} },
      textarea: { label: "Text Area", category: "Basic", validation: {} },
      email: {
        label: "Email",
        category: "Basic",
        validation: { type: "email" },
      },
      number: {
        label: "Number",
        category: "Basic",
        validation: { type: "number" },
      },
      phone: { label: "Phone", category: "Contact", validation: {} },
      url: { label: "URL", category: "Contact", validation: {} },
      select: { label: "Dropdown", category: "Choice", validation: {} },
      radio: { label: "Radio Buttons", category: "Choice", validation: {} },
      checkbox: { label: "Checkboxes", category: "Choice", validation: {} },
      date: { label: "Date", category: "Date & Time", validation: {} },
      time: { label: "Time", category: "Date & Time", validation: {} },
      datetime: {
        label: "Date & Time",
        category: "Date & Time",
        validation: {},
      },
      file: { label: "File Upload", category: "File", validation: {} },
      location: { label: "Location", category: "Advanced", validation: {} },
      rating: { label: "Rating", category: "Feedback", validation: {} },
    },
    categories: {
      Basic: ["text", "textarea", "email", "number"],
      Contact: ["phone", "url"],
      Choice: ["select", "radio", "checkbox"],
      "Date & Time": ["date", "time", "datetime"],
      File: ["file"],
      Advanced: ["location"],
      Feedback: ["rating"],
    },
  };

  // Use fallback if loading takes too long or fails
  const effectiveFieldTypes = fieldTypes || fallbackFieldTypes;

  // Try to load field types in background after component mounts
  useEffect(() => {
    // Delay the API call to allow immediate UI rendering
    const timer = setTimeout(() => {
      // Manually trigger field types query if not already loaded
      if (!fieldTypes && !fieldTypesLoading) {
        // This will happen in background without blocking UI
        formBuilderAPI
          .getFieldTypes()
          .then(() => {
            void 0; // Field types will update automatically via React Query
          })
          .catch(() => {
            void 0; // Silently fail, fallback is already in use
          });
      }
    }, 100); // Small delay to ensure UI renders first

    return () => clearTimeout(timer);
  }, [fieldTypes, fieldTypesLoading]);

  // REMOVED LOADING STATE - Always render FormBuilder immediately
  // This ensures instant loading without any buffering delays

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        display: "flex",
        flexDirection: "column",
        position: "relative",
        "&::before": {
          content: '""',
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background:
            "radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.1) 0%, transparent 50%)",
          pointerEvents: "none",
        },
      }}
    >
      {/* Modern Header with Glassmorphism */}
      <Box
        sx={{
          background: "rgba(255, 255, 255, 0.1)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.2)",
          p: 3,
          mb: 3,
          position: "relative",
          zIndex: 1,
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography
              variant="h4"
              sx={{
                fontWeight: 700,
                background: "linear-gradient(45deg, #ffffff 30%, #f0f0f0 90%)",
                backgroundClip: "text",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                mb: 0.5,
              }}
            >
              {formId ? "✨ Edit Form" : "🚀 Create New Form"}{" "}
              {formLoading && "(Loading...)"}
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: "rgba(255, 255, 255, 0.8)",
                fontWeight: 400,
              }}
            >
              Build beautiful forms with drag & drop simplicity
            </Typography>
          </Box>
          <Box display="flex" gap={2}>
            <Button
              variant={previewMode ? "outlined" : "contained"}
              onClick={() => setPreviewMode(!previewMode)}
              startIcon={previewMode ? <Edit /> : <Preview />}
              sx={{
                borderRadius: "12px",
                textTransform: "none",
                fontWeight: 600,
                px: 3,
                py: 1.5,
                background: previewMode
                  ? "rgba(255, 255, 255, 0.1)"
                  : "linear-gradient(45deg, #FF6B6B, #FF8E53)",
                border: previewMode
                  ? "2px solid rgba(255, 255, 255, 0.3)"
                  : "none",
                color: "white",
                backdropFilter: "blur(10px)",
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                "&:hover": {
                  transform: "translateY(-2px)",
                  boxShadow: "0 8px 25px rgba(0,0,0,0.15)",
                },
              }}
            >
              {previewMode ? "Edit Mode" : "Preview"}
            </Button>
            <Button
              variant="contained"
              onClick={handleSave}
              startIcon={<Save />}
              disabled={createMutation.isPending || updateMutation.isPending}
              sx={{
                borderRadius: "12px",
                textTransform: "none",
                fontWeight: 600,
                px: 3,
                py: 1.5,
                background: "linear-gradient(45deg, #4FACFE, #00F2FE)",
                border: "none",
                color: "white",
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                "&:hover": {
                  transform: "translateY(-2px)",
                  boxShadow: "0 8px 25px rgba(79, 172, 254, 0.4)",
                },
                "&:disabled": {
                  background: "rgba(255, 255, 255, 0.2)",
                  color: "rgba(255, 255, 255, 0.5)",
                },
              }}
            >
              {createMutation.isPending || updateMutation.isPending
                ? "Saving..."
                : "Save Form"}
            </Button>
            {onCancel && (
              <Button
                variant="outlined"
                onClick={onCancel}
                sx={{
                  borderRadius: "12px",
                  textTransform: "none",
                  fontWeight: 600,
                  px: 3,
                  py: 1.5,
                  border: "2px solid rgba(255, 255, 255, 0.3)",
                  color: "white",
                  backdropFilter: "blur(10px)",
                  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                  "&:hover": {
                    background: "rgba(255, 255, 255, 0.1)",
                    transform: "translateY(-2px)",
                  },
                }}
              >
                Cancel
              </Button>
            )}
          </Box>
        </Box>
      </Box>

      <Box
        sx={{
          flex: 1,
          display: "flex",
          gap: 3,
          px: 3,
          pb: 3,
          position: "relative",
          zIndex: 1,
        }}
      >
        {/* Left Panel - Form Configuration */}
        <Box
          sx={{
            width: 320,
            background: "rgba(255, 255, 255, 0.1)",
            backdropFilter: "blur(20px)",
            borderRadius: "20px",
            border: "1px solid rgba(255, 255, 255, 0.2)",
            p: 3,
            height: "fit-content",
            position: "sticky",
            top: 20,
            transition: "all 0.3s ease",
          }}
        >
          <Typography
            variant="h6"
            gutterBottom
            sx={{
              color: "white",
              fontWeight: 700,
              mb: 3,
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            ⚙️ Form Settings
          </Typography>
          <TextField
            label="Form Title"
            value={formData.title}
            onChange={(e: any) =>
              setFormData((prev: any) => ({ ...prev, title: e.target.value }))
            }
            fullWidth
            margin="normal"
            sx={{
              "& .MuiOutlinedInput-root": {
                background: "rgba(255, 255, 255, 0.1)",
                borderRadius: "12px",
                backdropFilter: "blur(10px)",
                "& fieldset": {
                  borderColor: "rgba(255, 255, 255, 0.3)",
                  borderWidth: "2px",
                },
                "&:hover fieldset": {
                  borderColor: "rgba(255, 255, 255, 0.5)",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#4FACFE",
                },
              },
              "& .MuiInputLabel-root": {
                color: "rgba(255, 255, 255, 0.8)",
                fontWeight: 500,
              },
              "& .MuiOutlinedInput-input": {
                color: "white",
                fontWeight: 500,
              },
            }}
          />
          <TextField
            label="Description"
            value={formData.description || ""}
            onChange={(e: any) =>
              setFormData((prev: any) => ({
                ...prev,
                description: e.target.value,
              }))
            }
            fullWidth
            margin="normal"
            multiline
            rows={3}
            sx={{
              "& .MuiOutlinedInput-root": {
                background: "rgba(255, 255, 255, 0.1)",
                borderRadius: "12px",
                backdropFilter: "blur(10px)",
                "& fieldset": {
                  borderColor: "rgba(255, 255, 255, 0.3)",
                  borderWidth: "2px",
                },
                "&:hover fieldset": {
                  borderColor: "rgba(255, 255, 255, 0.5)",
                },
                "&.Mui-focused fieldset": {
                  borderColor: "#4FACFE",
                },
              },
              "& .MuiInputLabel-root": {
                color: "rgba(255, 255, 255, 0.8)",
                fontWeight: 500,
              },
              "& .MuiOutlinedInput-input": {
                color: "white",
                fontWeight: 500,
              },
            }}
          />
          <Box sx={{ mt: 3, mb: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e: any) =>
                    setFormData((prev: any) => ({
                      ...prev,
                      is_active: e.target.checked,
                    }))
                  }
                  sx={{
                    "& .MuiSwitch-switchBase.Mui-checked": {
                      color: "#4FACFE",
                    },
                    "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                      backgroundColor: "#4FACFE",
                    },
                  }}
                />
              }
              label={
                <Typography sx={{ color: "white", fontWeight: 500 }}>
                  🟢 Active
                </Typography>
              }
              sx={{ mb: 1 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_public}
                  onChange={(e: any) =>
                    setFormData((prev: any) => ({
                      ...prev,
                      is_public: e.target.checked,
                    }))
                  }
                  sx={{
                    "& .MuiSwitch-switchBase.Mui-checked": {
                      color: "#FF6B6B",
                    },
                    "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                      backgroundColor: "#FF6B6B",
                    },
                  }}
                />
              }
              label={
                <Typography sx={{ color: "white", fontWeight: 500 }}>
                  🌐 Public
                </Typography>
              }
            />
          </Box>

          <Box
            sx={{
              height: "2px",
              background:
                "linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)",
              my: 3,
            }}
          />

          <Typography
            variant="h6"
            gutterBottom
            sx={{
              color: "white",
              fontWeight: 700,
              mb: 2,
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            🧩 Field Types {fieldTypesLoading && "(Loading...)"}
          </Typography>
          <Tabs
            value={tabValue}
            onChange={(_, newValue) => setTabValue(newValue)}
            sx={{
              "& .MuiTabs-indicator": {
                background: "linear-gradient(45deg, #4FACFE, #00F2FE)",
                height: "3px",
                borderRadius: "3px",
              },
              "& .MuiTab-root": {
                color: "rgba(255, 255, 255, 0.7)",
                fontWeight: 600,
                textTransform: "none",
                fontSize: "0.95rem",
                "&.Mui-selected": {
                  color: "white",
                },
              },
            }}
          >
            <Tab label="✨ Basic" />
            <Tab label="🔧 Advanced" />
            <Tab label="📱 QR Codes" />
            <Tab label="🏠 In-House" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <List dense>
              {effectiveFieldTypes?.categories?.Basic?.map((type: any) => (
                <ListItem key={type} disablePadding>
                  <ListItemButton onClick={() => handleAddField(type)}>
                    <ListItemIcon>{getFieldIcon(type)}</ListItemIcon>
                    <ListItemText
                      primary={
                        effectiveFieldTypes?.field_types[type]?.label || type
                      }
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <List dense>
              {Object.entries(effectiveFieldTypes?.categories || {}).map(
                ([category, types]) => (
                  <Accordion key={category}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography variant="subtitle2">{category}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List dense>
                        {types.map((type: any) => (
                          <ListItem key={type} disablePadding>
                            <ListItemButton
                              onClick={() => handleAddField(type)}
                            >
                              <ListItemIcon>{getFieldIcon(type)}</ListItemIcon>
                              <ListItemText
                                primary={
                                  effectiveFieldTypes?.field_types[type]
                                    ?.label || type
                                }
                              />
                            </ListItemButton>
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                )
              )}
            </List>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            {formData.id ? (
              <FormQRManager
                formId={formData.id}
                formTitle={formData.title || "Untitled Form"}
              />
            ) : (
              <Box sx={{ textAlign: "center", py: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  Save your form first to generate QR codes
                </Typography>
              </Box>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Typography variant="subtitle1" sx={{ color: "white", mb: 1, fontWeight: 600 }}>
              In-House Forms
            </Typography>
            {savedForms.length === 0 ? (
              <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.8)" }}>
                No in-house forms yet. Save a form to see it listed here.
              </Typography>
            ) : (
              <List dense>
                {savedForms.map((f: any) => (
                  <ListItem key={f.id} secondaryAction={
                    <Box>
                      <Button size="small" variant="outlined" sx={{ mr: 1 }} onClick={() => {
                        setFormData(f);
                        setTabValue(0);
                      }}>Open</Button>
                      <IconButton size="small" onClick={() => {
                        setSavedForms((prev) => {
                          const next = prev.filter((x: any) => x.id !== f.id);
                          try { localStorage.setItem("saved_forms", JSON.stringify(next)); } catch {}
                          return next;
                        });
                      }}>
                        <Delete fontSize="small" />
                      </IconButton>
                    </Box>
                  }>
                    <ListItemText
                      primary={<span style={{ color: "white" }}>{f.title || "Untitled Form"}</span>}
                      secondary={
                        <span style={{ color: "rgba(255,255,255,0.7)" }}>
                          ID: {f.id} {f.updated_at ? `• Updated: ${new Date(f.updated_at).toLocaleString()}` : ""}
                        </span>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </TabPanel>
        </Box>

        {/* Center Panel - Form Builder */}
        <Box
          sx={{
            flex: 1,
            background: "rgba(255, 255, 255, 0.05)",
            backdropFilter: "blur(20px)",
            borderRadius: "20px",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            p: 4,
            position: "relative",
            overflow: "hidden",
            "&::before": {
              content: '""',
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: "1px",
              background:
                "linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)",
            },
          }}
        >
          <Box sx={{ mb: 4 }}>
            <Typography
              variant="h5"
              sx={{
                color: "white",
                fontWeight: 700,
                mb: 1,
                display: "flex",
                alignItems: "center",
                gap: 2,
              }}
            >
              {previewMode ? "👁️ Form Preview" : "🎨 Form Builder"}
            </Typography>
            <Typography
              variant="body1"
              sx={{
                color: "rgba(255, 255, 255, 0.7)",
                fontWeight: 400,
              }}
            >
              {previewMode
                ? "See how your form will look to users"
                : "Drag and drop fields to build your form"}
            </Typography>
          </Box>

          {previewMode ? (
            // Preview Mode
            <Box
              sx={{
                p: 4,
                background: "rgba(255, 255, 255, 0.1)",
                backdropFilter: "blur(10px)",
                border: "2px dashed rgba(255, 255, 255, 0.3)",
                borderRadius: "16px",
                minHeight: "400px",
              }}
            >
              {formData.schema?.fields.map((field: any) => (
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
                    sx={{
                      minHeight: 400,
                      background: "rgba(255, 255, 255, 0.05)",
                      borderRadius: "16px",
                      border: "2px dashed rgba(255, 255, 255, 0.2)",
                      p: 3,
                      position: "relative",
                      "&:empty::after": {
                        content:
                          '"🎯 Drop fields here to start building your form"',
                        position: "absolute",
                        top: "50%",
                        left: "50%",
                        transform: "translate(-50%, -50%)",
                        color: "rgba(255, 255, 255, 0.5)",
                        fontSize: "1.1rem",
                        fontWeight: 500,
                        textAlign: "center",
                      },
                    }}
                  >
                    {formData.schema?.fields.map((field, index) => (
                      <Draggable
                        key={field.id}
                        draggableId={field.id}
                        index={index}
                      >
                        {(provided: DraggableProvided) => (
                          <Card
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            sx={{
                              mb: 3,
                              cursor: "pointer",
                              background: "rgba(255, 255, 255, 0.1)",
                              backdropFilter: "blur(10px)",
                              borderRadius: "16px",
                              border: "1px solid rgba(255, 255, 255, 0.2)",
                              transition:
                                "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                              "&:hover": {
                                transform: "translateY(-4px)",
                                boxShadow: "0 12px 40px rgba(0,0,0,0.15)",
                                background: "rgba(255, 255, 255, 0.15)",
                                border: "1px solid rgba(255, 255, 255, 0.3)",
                              },
                            }}
                            onClick={() => {
                              setSelectedField(field);
                              setFieldDialogOpen(true);
                            }}
                          >
                            <CardContent sx={{ p: 3 }}>
                              <Box display="flex" alignItems="center" gap={2}>
                                <Box
                                  {...provided.dragHandleProps}
                                  sx={{
                                    p: 1,
                                    borderRadius: "8px",
                                    background: "rgba(255, 255, 255, 0.1)",
                                    cursor: "grab",
                                    "&:active": {
                                      cursor: "grabbing",
                                    },
                                  }}
                                >
                                  <DragIndicator
                                    sx={{ color: "rgba(255, 255, 255, 0.7)" }}
                                  />
                                </Box>
                                <Box sx={{ flex: 1 }}>
                                  <Box
                                    display="flex"
                                    alignItems="center"
                                    gap={2}
                                    mb={1}
                                  >
                                    <Box
                                      sx={{
                                        p: 1,
                                        borderRadius: "8px",
                                        background:
                                          "linear-gradient(45deg, #4FACFE, #00F2FE)",
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "center",
                                      }}
                                    >
                                      {getFieldIcon(field.type)}
                                    </Box>
                                    <Typography
                                      variant="h6"
                                      sx={{
                                        color: "white",
                                        fontWeight: 600,
                                      }}
                                    >
                                      {field.label}
                                    </Typography>
                                    {field.required && (
                                      <Chip
                                        label="Required"
                                        size="small"
                                        sx={{
                                          background:
                                            "linear-gradient(45deg, #FF6B6B, #FF8E53)",
                                          color: "white",
                                          fontWeight: 600,
                                          border: "none",
                                        }}
                                      />
                                    )}
                                  </Box>
                                  {field.description && (
                                    <Typography
                                      variant="body2"
                                      sx={{
                                        color: "rgba(255, 255, 255, 0.7)",
                                        fontWeight: 400,
                                      }}
                                    >
                                      {field.description}
                                    </Typography>
                                  )}
                                </Box>
                                <IconButton
                                  size="small"
                                  onClick={(e: any) => {
                                    e.stopPropagation();
                                    handleDeleteField(field.id);
                                  }}
                                  sx={{
                                    background: "rgba(255, 107, 107, 0.2)",
                                    color: "#FF6B6B",
                                    "&:hover": {
                                      background: "rgba(255, 107, 107, 0.3)",
                                      transform: "scale(1.1)",
                                    },
                                    transition: "all 0.2s ease",
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
                  </Box>
                )}
              </Droppable>
            </DragDropContext>
          )}
        </Box>
      </Box>

      {/* Field Configuration Dialog */}
      {renderFieldDialog()}

      {/* Snackbar */}
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
