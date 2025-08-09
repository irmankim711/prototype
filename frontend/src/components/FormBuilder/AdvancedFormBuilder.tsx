/**
 * Advanced Form Builder Component with Conditional Logic
 * Enhanced drag & drop form builder with real-time preview and conditional rules
 */

import React, { useState, useCallback, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  TextField,
  Switch,
  FormControlLabel,
  Alert,
  Snackbar,
  Fab,
  Chip,
} from "@mui/material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  DragIndicator as DragIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Bolt as BoltIcon,
  PlayArrow as PlayIcon,
} from "@mui/icons-material";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";
import type { DropResult } from "@hello-pangea/dnd";

import type {
  FormField,
  ConditionalRule,
  Form,
  FormFieldValue,
} from "../../types/formBuilder";
import { ConditionalLogicEngine } from "../../utils/conditionalLogicEngine";
import { FieldTypeSelector } from "./FieldTypeSelector";
import { FieldEditor } from "./FieldEditor";
import { ConditionalRuleEditor } from "./ConditionalRuleEditor";
import { LivePreview } from "./LivePreview";

// Mock API for now - will integrate with real API later
const mockFormBuilderAPI = {
  createForm: async (form: Partial<Form>): Promise<Form> => {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      id: Date.now(),
      title: form.title || "Untitled Form",
      description: form.description || "",
      schema: form.schema || { version: "1.0", fields: [], global_rules: [] },
      is_active: form.is_active || true,
      is_public: form.is_public || false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      user_id: 1,
    } as Form;
  },
  updateForm: async (id: number, form: Partial<Form>): Promise<Form> => {
    await new Promise((resolve) => setTimeout(resolve, 800));
    return {
      id,
      title: form.title || "Untitled Form",
      description: form.description || "",
      schema: form.schema || { version: "1.0", fields: [], global_rules: [] },
      is_active: form.is_active || true,
      is_public: form.is_public || false,
      created_at: new Date(Date.now() - 86400000).toISOString(),
      updated_at: new Date().toISOString(),
      user_id: 1,
    } as Form;
  },
};

interface AdvancedFormBuilderProps {
  formId?: number;
  initialForm?: Partial<Form>;
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

export const AdvancedFormBuilder: React.FC<AdvancedFormBuilderProps> = ({
  formId,
  initialForm,
  onSave,
  onCancel,
}) => {
  // State management
  const [currentTab, setCurrentTab] = useState(0);
  const [form, setForm] = useState<Partial<Form>>(
    initialForm || {
      title: "New Form",
      description: "",
      schema: {
        version: "1.0",
        fields: [],
        global_rules: [],
      },
      is_active: true,
      is_public: false,
    }
  );

  const [selectedField, setSelectedField] = useState<FormField | null>(null);
  const [selectedRule, setSelectedRule] = useState<ConditionalRule | null>(
    null
  );
  const [previewMode, setPreviewMode] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Dialog states
  const [fieldEditorOpen, setFieldEditorOpen] = useState(false);
  const [ruleEditorOpen, setRuleEditorOpen] = useState(false);
  const [fieldTypeSelectorOpen, setFieldTypeSelectorOpen] = useState(false);

  // Snackbar state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success" as "success" | "error" | "warning" | "info",
  });

  // Conditional logic engine
  const [logicEngine] = useState(() => new ConditionalLogicEngine());
  const [previewData, setPreviewData] = useState<
    Record<string, FormFieldValue>
  >({});

  // Initialize logic engine when form changes
  useEffect(() => {
    if (form.schema?.fields) {
      logicEngine.initializeFieldStates(form.schema.fields);
      if (form.schema.global_rules) {
        logicEngine.addRules(form.schema.global_rules);
      }
    }
  }, [form.schema, logicEngine]);

  // Generate unique field ID
  const generateFieldId = useCallback(() => {
    return `field_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Handle drag and drop
  const handleDragEnd = useCallback(
    (result: DropResult) => {
      if (!result.destination || !form.schema) return;

      const fields = [...form.schema.fields];
      const [reorderedField] = fields.splice(result.source.index, 1);
      fields.splice(result.destination.index, 0, reorderedField);

      // Update field orders
      const updatedFields = fields.map((field, index) => ({
        ...field,
        order: index,
      }));

      setForm((prev) => ({
        ...prev,
        schema: {
          ...prev.schema!,
          fields: updatedFields,
        },
      }));
      setIsDirty(true);
    },
    [form.schema]
  );

  // Add new field
  const handleAddField = useCallback(
    (fieldType: string) => {
      const newField: FormField = {
        id: generateFieldId(),
        type: fieldType as FormField["type"],
        label: `New ${fieldType} field`,
        placeholder: `Enter ${fieldType}...`,
        required: false,
        order: form.schema?.fields.length || 0,
        conditional_rules: [],
      };

      // Add field-specific defaults
      if (["select", "radio", "checkbox"].includes(fieldType)) {
        newField.options = ["Option 1", "Option 2"];
      }

      setForm((prev) => ({
        ...prev,
        schema: {
          ...prev.schema!,
          fields: [...(prev.schema?.fields || []), newField],
        },
      }));
      setIsDirty(true);
      setFieldTypeSelectorOpen(false);

      // Auto-open field editor for new fields
      setSelectedField(newField);
      setFieldEditorOpen(true);
    },
    [form.schema?.fields, generateFieldId]
  );

  // Update field
  const handleUpdateField = useCallback(
    (updatedField: FormField) => {
      if (!form.schema) return;

      const updatedFields = form.schema.fields.map((field) =>
        field.id === updatedField.id ? updatedField : field
      );

      setForm((prev) => ({
        ...prev,
        schema: {
          ...prev.schema!,
          fields: updatedFields,
        },
      }));
      setIsDirty(true);
      setFieldEditorOpen(false);
      setSelectedField(null);
    },
    [form.schema]
  );

  // Delete field
  const handleDeleteField = useCallback(
    (fieldId: string) => {
      if (!form.schema) return;

      const updatedFields = form.schema.fields.filter(
        (field) => field.id !== fieldId
      );

      setForm((prev) => ({
        ...prev,
        schema: {
          ...prev.schema!,
          fields: updatedFields,
        },
      }));
      setIsDirty(true);
    },
    [form.schema]
  );

  // Add conditional rule
  const handleAddRule = useCallback(
    (rule: ConditionalRule) => {
      if (!form.schema) return;

      const updatedRules = [...(form.schema.global_rules || []), rule];

      setForm((prev) => ({
        ...prev,
        schema: {
          ...prev.schema!,
          global_rules: updatedRules,
        },
      }));
      setIsDirty(true);
      setRuleEditorOpen(false);
    },
    [form.schema]
  );

  // Update rule
  const handleUpdateRule = useCallback(
    (updatedRule: ConditionalRule) => {
      if (!form.schema?.global_rules) return;

      const updatedRules = form.schema.global_rules.map((rule) =>
        rule.id === updatedRule.id ? updatedRule : rule
      );

      setForm((prev) => ({
        ...prev,
        schema: {
          ...prev.schema!,
          global_rules: updatedRules,
        },
      }));
      setIsDirty(true);
      setRuleEditorOpen(false);
      setSelectedRule(null);
    },
    [form.schema]
  );

  // Delete rule
  const handleDeleteRule = useCallback(
    (ruleId: string) => {
      if (!form.schema?.global_rules) return;

      const updatedRules = form.schema.global_rules.filter(
        (rule) => rule.id !== ruleId
      );

      setForm((prev) => ({
        ...prev,
        schema: {
          ...prev.schema!,
          global_rules: updatedRules,
        },
      }));
      setIsDirty(true);
    },
    [form.schema]
  );

  // Handle preview data change
  const handlePreviewDataChange = useCallback(
    (fieldId: string, value: FormFieldValue) => {
      setPreviewData((prev) => ({
        ...prev,
        [fieldId]: value,
      }));

      // Update conditional logic
      logicEngine.updateFormData(fieldId, value);
    },
    [logicEngine]
  );

  // Test conditional logic
  const handleTestLogic = useCallback(() => {
    if (!form.schema?.fields || !form.schema?.global_rules) return;

    try {
      const validation = logicEngine.validateRules(
        form.schema.global_rules,
        form.schema.fields
      );

      if (validation.valid) {
        setSnackbar({
          open: true,
          message: "Conditional logic validation passed!",
          severity: "success",
        });
      } else {
        setSnackbar({
          open: true,
          message: `Validation failed: ${validation.errors.join(", ")}`,
          severity: "error",
        });
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Logic test failed: ${error}`,
        severity: "error",
      });
    }
  }, [form.schema, logicEngine]);

  // Save form
  const handleSave = useCallback(async () => {
    if (!form.title?.trim()) {
      setSnackbar({
        open: true,
        message: "Please enter a form title",
        severity: "error",
      });
      return;
    }

    setIsLoading(true);
    try {
      let savedForm: Form;

      if (formId) {
        savedForm = await mockFormBuilderAPI.updateForm(formId, form);
      } else {
        savedForm = await mockFormBuilderAPI.createForm(form);
      }

      setSnackbar({
        open: true,
        message: "Form saved successfully!",
        severity: "success",
      });
      setIsDirty(false);
      onSave?.(savedForm);
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to save form: ${error}`,
        severity: "error",
      });
    } finally {
      setIsLoading(false);
    }
  }, [form, formId, onSave]);

  // Render field list
  const renderFieldList = () => (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="form-fields">
        {(provided) => (
          <Box
            {...provided.droppableProps}
            ref={provided.innerRef}
            sx={{
              minHeight: 400,
              p: 2,
              border: "2px dashed",
              borderColor: "grey.300",
              borderRadius: 2,
              bgcolor: "grey.50",
            }}
          >
            {form.schema?.fields.length === 0 && (
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  height: 200,
                  color: "grey.500",
                }}
              >
                <Typography variant="h6">
                  Drop fields here or click + to add fields
                </Typography>
              </Box>
            )}

            {form.schema?.fields.map((field, index) => (
              <Draggable key={field.id} draggableId={field.id} index={index}>
                {(provided, snapshot) => (
                  <Card
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    sx={{
                      mb: 2,
                      cursor: "pointer",
                      transform: snapshot.isDragging ? "rotate(5deg)" : "none",
                      boxShadow: snapshot.isDragging ? 4 : 1,
                      "&:hover": {
                        boxShadow: 3,
                      },
                    }}
                  >
                    <CardContent sx={{ py: 2 }}>
                      <Box display="flex" alignItems="center" gap={2}>
                        <Box {...provided.dragHandleProps}>
                          <DragIcon color="action" />
                        </Box>

                        <Box flex={1}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {field.label}
                          </Typography>
                          <Box
                            display="flex"
                            alignItems="center"
                            gap={1}
                            mt={0.5}
                          >
                            <Chip
                              label={field.type}
                              size="small"
                              variant="outlined"
                            />
                            {field.required && (
                              <Chip
                                label="Required"
                                size="small"
                                color="error"
                              />
                            )}
                            {field.conditional_rules &&
                              field.conditional_rules.length > 0 && (
                                <Chip
                                  label={`${field.conditional_rules.length} Rules`}
                                  size="small"
                                  color="info"
                                  icon={<BoltIcon fontSize="small" />}
                                />
                              )}
                          </Box>
                        </Box>

                        <Box display="flex" gap={1}>
                          <Tooltip title="Edit Field">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedField(field);
                                setFieldEditorOpen(true);
                              }}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="Delete Field">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteField(field.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
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
  );

  // Render conditional rules list
  const renderRulesList = () => (
    <Box>
      {form.schema?.global_rules?.length === 0 && (
        <Alert severity="info">
          No conditional rules defined. Add rules to create dynamic form
          behavior.
        </Alert>
      )}

      {form.schema?.global_rules?.map((rule) => (
        <Card key={rule.id} sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" alignItems="center" gap={2}>
              <BoltIcon color="primary" />

              <Box flex={1}>
                <Typography variant="subtitle2" fontWeight={600}>
                  When "
                  {form.schema?.fields.find((f) => f.id === rule.sourceFieldId)
                    ?.label || rule.sourceFieldId}
                  " {rule.condition} "{rule.value}"
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Then {rule.action} fields: {rule.targetFieldIds.join(", ")}
                </Typography>
              </Box>

              <Box display="flex" gap={1}>
                <Tooltip title="Edit Rule">
                  <IconButton
                    size="small"
                    onClick={() => {
                      setSelectedRule(rule);
                      setRuleEditorOpen(true);
                    }}
                  >
                    <EditIcon />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Delete Rule">
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDeleteRule(rule.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
          </CardContent>
        </Card>
      ))}
    </Box>
  );

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <Box sx={{ p: 3, borderBottom: 1, borderColor: "divider" }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="h4" fontWeight={700}>
              {formId ? "✏️ Edit Form" : "🚀 Create Form"}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Build advanced forms with conditional logic and real-time preview
            </Typography>
          </Box>

          <Box display="flex" gap={2} alignItems="center">
            <Button
              variant={previewMode ? "contained" : "outlined"}
              startIcon={
                previewMode ? <VisibilityOffIcon /> : <VisibilityIcon />
              }
              onClick={() => setPreviewMode(!previewMode)}
            >
              {previewMode ? "Edit" : "Preview"}
            </Button>

            <Button
              variant="outlined"
              startIcon={<PlayIcon />}
              onClick={handleTestLogic}
              disabled={!form.schema?.global_rules?.length}
            >
              Test Logic
            </Button>

            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={isLoading || !isDirty}
            >
              Save Form
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {!previewMode ? (
          <>
            {/* Left Panel - Form Builder */}
            <Box
              sx={{ width: "70%", display: "flex", flexDirection: "column" }}
            >
              <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                <Tabs
                  value={currentTab}
                  onChange={(_, value) => setCurrentTab(value)}
                >
                  <Tab label="Form Fields" />
                  <Tab label="Conditional Logic" />
                  <Tab label="Settings" />
                </Tabs>
              </Box>

              <Box sx={{ flex: 1, overflow: "auto" }}>
                <TabPanel value={currentTab} index={0}>
                  {renderFieldList()}
                </TabPanel>

                <TabPanel value={currentTab} index={1}>
                  {renderRulesList()}
                </TabPanel>

                <TabPanel value={currentTab} index={2}>
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Form Title"
                        value={form.title || ""}
                        onChange={(e) => {
                          setForm((prev) => ({
                            ...prev,
                            title: e.target.value,
                          }));
                          setIsDirty(true);
                        }}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        multiline
                        rows={3}
                        label="Form Description"
                        value={form.description || ""}
                        onChange={(e) => {
                          setForm((prev) => ({
                            ...prev,
                            description: e.target.value,
                          }));
                          setIsDirty(true);
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={form.is_active || false}
                            onChange={(e) => {
                              setForm((prev) => ({
                                ...prev,
                                is_active: e.target.checked,
                              }));
                              setIsDirty(true);
                            }}
                          />
                        }
                        label="Form Active"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={form.is_public || false}
                            onChange={(e) => {
                              setForm((prev) => ({
                                ...prev,
                                is_public: e.target.checked,
                              }));
                              setIsDirty(true);
                            }}
                          />
                        }
                        label="Public Form"
                      />
                    </Grid>
                  </Grid>
                </TabPanel>
              </Box>
            </Box>

            {/* Right Panel - Field Types */}
            <Box
              sx={{ width: "30%", borderLeft: 1, borderColor: "divider", p: 2 }}
            >
              <Typography variant="h6" gutterBottom>
                Field Types
              </Typography>
              <FieldTypeSelector onSelect={handleAddField} />
            </Box>
          </>
        ) : (
          /* Preview Mode */
          <Box sx={{ width: "100%", p: 3 }}>
            <LivePreview
              form={form}
              data={previewData}
              onDataChange={handlePreviewDataChange}
              logicEngine={logicEngine}
            />
          </Box>
        )}
      </Box>

      {/* Floating Action Buttons */}
      {!previewMode && (
        <Box sx={{ position: "fixed", bottom: 24, right: 24 }}>
          {currentTab === 0 && (
            <Fab
              color="primary"
              onClick={() => setFieldTypeSelectorOpen(true)}
              sx={{ mr: 2 }}
            >
              <AddIcon />
            </Fab>
          )}
          {currentTab === 1 && (
            <Fab color="secondary" onClick={() => setRuleEditorOpen(true)}>
              <BoltIcon />
            </Fab>
          )}
        </Box>
      )}

      {/* Dialogs */}
      <FieldEditor
        open={fieldEditorOpen}
        field={selectedField}
        fields={form.schema?.fields || []}
        onSave={handleUpdateField}
        onClose={() => {
          setFieldEditorOpen(false);
          setSelectedField(null);
        }}
      />

      <ConditionalRuleEditor
        open={ruleEditorOpen}
        rule={selectedRule}
        fields={form.schema?.fields || []}
        onSave={selectedRule ? handleUpdateRule : handleAddRule}
        onClose={() => {
          setRuleEditorOpen(false);
          setSelectedRule(null);
        }}
      />

      <Dialog
        open={fieldTypeSelectorOpen}
        onClose={() => setFieldTypeSelectorOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add New Field</DialogTitle>
        <DialogContent>
          <FieldTypeSelector onSelect={handleAddField} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFieldTypeSelectorOpen(false)}>
            Cancel
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};
