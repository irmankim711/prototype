/**
 * Field Editor Component
 * Advanced field configuration dialog with validation and conditional rules
 */

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Box,
  Typography,
  Grid,
  Chip,
  IconButton,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from "@mui/material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  DragIndicator as DragIcon,
} from "@mui/icons-material";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";
import type { DropResult } from "@hello-pangea/dnd";

import type { FormField } from "../../types/formBuilder";

interface FieldEditorProps {
  open: boolean;
  field: FormField | null;
  fields: FormField[];
  onSave: (field: FormField) => void;
  onClose: () => void;
}

const fieldTypes = [
  "text",
  "textarea",
  "email",
  "phone",
  "number",
  "date",
  "time",
  "checkbox",
  "radio",
  "select",
  "file",
  "url",
  "password",
  "color",
];

export const FieldEditor: React.FC<FieldEditorProps> = ({
  open,
  field,
  onSave,
  onClose,
}) => {
  const [editedField, setEditedField] = useState<FormField>({
    id: "",
    type: "text",
    label: "",
    placeholder: "",
    required: false,
    order: 0,
    conditional_rules: [],
  });

  const [newOption, setNewOption] = useState("");
  const [validationError, setValidationError] = useState("");

  // Initialize field data when dialog opens
  useEffect(() => {
    if (field) {
      setEditedField({
        ...field,
        options: field.options ? [...field.options] : [],
        validation: field.validation ? { ...field.validation } : {},
        conditional_rules: field.conditional_rules
          ? [...field.conditional_rules]
          : [],
      });
    } else {
      setEditedField({
        id: "",
        type: "text",
        label: "",
        placeholder: "",
        required: false,
        order: 0,
        conditional_rules: [],
      });
    }
    setValidationError("");
  }, [field, open]);

  // Handle field property changes
  const handleFieldChange = (
    property: keyof FormField,
    value: string | boolean | number | string[] | undefined
  ) => {
    setEditedField((prev) => ({
      ...prev,
      [property]: value,
    }));
  };

  // Handle validation rule changes
  const handleValidationChange = (
    rule: string,
    value: string | number | boolean | undefined
  ) => {
    setEditedField((prev) => ({
      ...prev,
      validation: {
        ...prev.validation,
        [rule]: value,
      },
    }));
  };

  // Add option for select/radio/checkbox fields
  const handleAddOption = () => {
    if (!newOption.trim()) return;

    setEditedField((prev) => ({
      ...prev,
      options: [...(prev.options || []), newOption.trim()],
    }));
    setNewOption("");
  };

  // Remove option
  const handleRemoveOption = (index: number) => {
    setEditedField((prev) => ({
      ...prev,
      options: prev.options?.filter((_, i) => i !== index) || [],
    }));
  };

  // Handle option drag and drop
  const handleOptionDragEnd = (result: DropResult) => {
    if (!result.destination || !editedField.options) return;

    const options = [...editedField.options];
    const [reorderedOption] = options.splice(result.source.index, 1);
    options.splice(result.destination.index, 0, reorderedOption);

    setEditedField((prev) => ({
      ...prev,
      options,
    }));
  };

  // Validate field before saving
  const validateField = (): boolean => {
    if (!editedField.label.trim()) {
      setValidationError("Field label is required");
      return false;
    }

    if (
      ["select", "radio", "checkbox"].includes(editedField.type) &&
      (!editedField.options || editedField.options.length === 0)
    ) {
      setValidationError("At least one option is required for this field type");
      return false;
    }

    return true;
  };

  // Handle save
  const handleSave = () => {
    if (!validateField()) return;

    onSave(editedField);
  };

  // Check if field type supports options
  const supportsOptions = ["select", "radio", "checkbox"].includes(
    editedField.type
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{field ? "Edit Field" : "Add Field"}</DialogTitle>

      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {validationError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {validationError}
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Basic Properties */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Basic Properties
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Field Type</InputLabel>
                <Select
                  value={editedField.type}
                  label="Field Type"
                  onChange={(e) => handleFieldChange("type", e.target.value)}
                >
                  {fieldTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Field Label"
                value={editedField.label}
                onChange={(e) => handleFieldChange("label", e.target.value)}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Placeholder Text"
                value={editedField.placeholder || ""}
                onChange={(e) =>
                  handleFieldChange("placeholder", e.target.value)
                }
                helperText="Text shown when field is empty"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Description"
                value={editedField.description || ""}
                onChange={(e) =>
                  handleFieldChange("description", e.target.value)
                }
                helperText="Additional guidance for users"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={editedField.required}
                    onChange={(e) =>
                      handleFieldChange("required", e.target.checked)
                    }
                  />
                }
                label="Required Field"
              />
            </Grid>

            {/* Options for select/radio/checkbox */}
            {supportsOptions && (
              <>
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Options
                  </Typography>
                </Grid>

                <Grid item xs={12}>
                  <Box display="flex" gap={2} mb={2}>
                    <TextField
                      fullWidth
                      label="Add Option"
                      value={newOption}
                      onChange={(e) => setNewOption(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddOption();
                        }
                      }}
                    />
                    <Button
                      variant="outlined"
                      startIcon={<AddIcon />}
                      onClick={handleAddOption}
                      disabled={!newOption.trim()}
                    >
                      Add
                    </Button>
                  </Box>

                  <DragDropContext onDragEnd={handleOptionDragEnd}>
                    <Droppable droppableId="options">
                      {(provided) => (
                        <Box
                          {...provided.droppableProps}
                          ref={provided.innerRef}
                          sx={{
                            minHeight: 100,
                            p: 2,
                            border: "1px dashed",
                            borderColor: "grey.300",
                            borderRadius: 1,
                          }}
                        >
                          {editedField.options?.map((option, index) => (
                            <Draggable
                              key={`option-${index}`}
                              draggableId={`option-${index}`}
                              index={index}
                            >
                              {(provided) => (
                                <Box
                                  ref={provided.innerRef}
                                  {...provided.draggableProps}
                                  sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 1,
                                    p: 1,
                                    mb: 1,
                                    bgcolor: "grey.50",
                                    borderRadius: 1,
                                  }}
                                >
                                  <Box {...provided.dragHandleProps}>
                                    <DragIcon fontSize="small" />
                                  </Box>
                                  <Chip label={option} sx={{ flex: 1 }} />
                                  <IconButton
                                    size="small"
                                    onClick={() => handleRemoveOption(index)}
                                  >
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                </Box>
                              )}
                            </Draggable>
                          ))}
                          {provided.placeholder}
                        </Box>
                      )}
                    </Droppable>
                  </DragDropContext>
                </Grid>
              </>
            )}

            {/* Validation Rules */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Validation Rules
              </Typography>
            </Grid>

            {editedField.type === "text" ||
              (editedField.type === "textarea" && (
                <>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Minimum Length"
                      value={editedField.validation?.minLength || ""}
                      onChange={(e) =>
                        handleValidationChange(
                          "minLength",
                          parseInt(e.target.value) || undefined
                        )
                      }
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Maximum Length"
                      value={editedField.validation?.maxLength || ""}
                      onChange={(e) =>
                        handleValidationChange(
                          "maxLength",
                          parseInt(e.target.value) || undefined
                        )
                      }
                    />
                  </Grid>
                </>
              ))}

            {editedField.type === "number" && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Minimum Value"
                    value={editedField.validation?.min || ""}
                    onChange={(e) =>
                      handleValidationChange(
                        "min",
                        parseFloat(e.target.value) || undefined
                      )
                    }
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Maximum Value"
                    value={editedField.validation?.max || ""}
                    onChange={(e) =>
                      handleValidationChange(
                        "max",
                        parseFloat(e.target.value) || undefined
                      )
                    }
                  />
                </Grid>
              </>
            )}

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Custom Pattern (Regex)"
                value={editedField.validation?.pattern || ""}
                onChange={(e) =>
                  handleValidationChange("pattern", e.target.value)
                }
                helperText="Regular expression for custom validation"
              />
            </Grid>
          </Grid>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave}>
          Save Field
        </Button>
      </DialogActions>
    </Dialog>
  );
};
