import React, { useState, useEffect } from "react";
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

  // Fetch form data if editing
  const { data: existingForm, isLoading: formLoading } = useQuery({
    queryKey: ["form", formId],
    queryFn: () => formBuilderAPI.getForm(formId!),
    enabled: !!formId,
  });

  // Fetch field types
  const { data: fieldTypes, isLoading: fieldTypesLoading } = useQuery({
    queryKey: ["fieldTypes"],
    queryFn: formBuilderAPI.getFieldTypes,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: formBuilderAPI.createForm,
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: "Form created successfully!",
        severity: "success",
      });
      onSave?.(data.form);
    },
    onError: () => {
      setSnackbar({
        open: true,
        message: "Failed to create form",
        severity: "error",
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      formBuilderAPI.updateForm(id, data),
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: "Form updated successfully!",
        severity: "success",
      });
      onSave?.(data.form);
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

    setFormData((prev) => ({
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

    setFormData((prev) => ({
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
    setFormData((prev) => ({
      ...prev,
      schema: {
        ...prev.schema!,
        fields:
          prev.schema?.fields.map((field) =>
            field.id === fieldId ? { ...field, ...updates } : field
          ) || [],
      },
    }));
  };

  // Delete field
  const handleDeleteField = (fieldId: string) => {
    setFormData((prev) => ({
      ...prev,
      schema: {
        ...prev.schema!,
        fields:
          prev.schema?.fields.filter((field) => field.id !== fieldId) || [],
      },
    }));
  };

  // Save form
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
                  onChange={(e) =>
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
                  onChange={(e) =>
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
                  onChange={(e) =>
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
                      onChange={(e) =>
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
                      onChange={(e) => {
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
              {field.options?.map((option) => (
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
            {field.options?.map((option) => (
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
            {field.options?.slice(0, 2).map((option) => (
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
              {[1, 2, 3, 4, 5].map((star) => (
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

  if (formLoading || fieldTypesLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <Typography>Loading form builder...</Typography>
      </Box>
    );
  }

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
              {formId ? "✨ Edit Form" : "🚀 Create New Form"}
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
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, title: e.target.value }))
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
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, description: e.target.value }))
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
                  onChange={(e) =>
                    setFormData((prev) => ({
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
                  onChange={(e) =>
                    setFormData((prev) => ({
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
            🧩 Field Types
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
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <List dense>
              {fieldTypes?.categories?.Basic?.map((type) => (
                <ListItem key={type} disablePadding>
                  <ListItemButton onClick={() => handleAddField(type)}>
                    <ListItemIcon>{getFieldIcon(type)}</ListItemIcon>
                    <ListItemText
                      primary={fieldTypes?.field_types[type]?.label || type}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <List dense>
              {Object.entries(fieldTypes?.categories || {}).map(
                ([category, types]) => (
                  <Accordion key={category}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography variant="subtitle2">{category}</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List dense>
                        {types.map((type) => (
                          <ListItem key={type} disablePadding>
                            <ListItemButton
                              onClick={() => handleAddField(type)}
                            >
                              <ListItemIcon>{getFieldIcon(type)}</ListItemIcon>
                              <ListItemText
                                primary={
                                  fieldTypes?.field_types[type]?.label || type
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
                                  onClick={(e) => {
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
