/**
 * Conditional Rule Editor Component
 * Advanced editor for creating and modifying conditional rules
 */

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Box,
  Typography,
  Grid,
  Chip,
  Alert,
  Autocomplete,
} from "@mui/material";

import type { ConditionalRule, FormField } from "../../types/formBuilder";

interface ConditionalRuleEditorProps {
  open: boolean;
  rule: ConditionalRule | null;
  fields: FormField[];
  onSave: (rule: ConditionalRule) => void;
  onClose: () => void;
}

const conditions = [
  { value: "equals", label: "Equals" },
  { value: "not_equals", label: "Not equals" },
  { value: "contains", label: "Contains" },
  { value: "not_contains", label: "Does not contain" },
  { value: "greater_than", label: "Greater than" },
  { value: "less_than", label: "Less than" },
  { value: "greater_equal", label: "Greater than or equal" },
  { value: "less_equal", label: "Less than or equal" },
  { value: "is_empty", label: "Is empty" },
  { value: "is_not_empty", label: "Is not empty" },
  { value: "regex_match", label: "Matches pattern" },
];

const actions = [
  { value: "show", label: "Show field(s)" },
  { value: "hide", label: "Hide field(s)" },
  { value: "require", label: "Make required" },
  { value: "disable", label: "Disable field(s)" },
  { value: "set_value", label: "Set value" },
  { value: "calculate", label: "Calculate value" },
];

export const ConditionalRuleEditor: React.FC<ConditionalRuleEditorProps> = ({
  open,
  rule,
  fields,
  onSave,
  onClose,
}) => {
  const [editedRule, setEditedRule] = useState<ConditionalRule>({
    id: "",
    sourceFieldId: "",
    condition: "equals",
    value: "",
    action: "show",
    targetFieldIds: [],
  });

  const [validationError, setValidationError] = useState("");

  // Initialize rule data when dialog opens
  useEffect(() => {
    if (rule) {
      setEditedRule({ ...rule });
    } else {
      setEditedRule({
        id: `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        sourceFieldId: "",
        condition: "equals",
        value: "",
        action: "show",
        targetFieldIds: [],
      });
    }
    setValidationError("");
  }, [rule, open]);

  // Handle rule property changes
  const handleRuleChange = (
    property: keyof ConditionalRule,
    value: string | string[] | number | boolean | undefined
  ) => {
    setEditedRule((prev) => ({
      ...prev,
      [property]: value,
    }));
  };

  // Get available target fields (excluding source field)
  const getAvailableTargetFields = () => {
    return fields.filter((field) => field.id !== editedRule.sourceFieldId);
  };

  // Validate rule before saving
  const validateRule = (): boolean => {
    if (!editedRule.sourceFieldId) {
      setValidationError("Please select a source field");
      return false;
    }

    if (!editedRule.condition) {
      setValidationError("Please select a condition");
      return false;
    }

    if (
      !["is_empty", "is_not_empty"].includes(editedRule.condition) &&
      !editedRule.value
    ) {
      setValidationError("Please enter a value for the condition");
      return false;
    }

    if (!editedRule.action) {
      setValidationError("Please select an action");
      return false;
    }

    if (editedRule.targetFieldIds.length === 0) {
      setValidationError("Please select at least one target field");
      return false;
    }

    return true;
  };

  // Handle save
  const handleSave = () => {
    if (!validateRule()) return;

    onSave(editedRule);
  };

  // Get source field
  const sourceField = fields.find((f) => f.id === editedRule.sourceFieldId);

  // Determine if condition requires a value
  const requiresValue = !["is_empty", "is_not_empty"].includes(
    editedRule.condition
  );

  // Render value input based on source field type and condition
  const renderValueInput = () => {
    if (!requiresValue) return null;

    const sourceField = fields.find((f) => f.id === editedRule.sourceFieldId);

    if (!sourceField) {
      return (
        <TextField
          fullWidth
          label="Value"
          value={editedRule.value}
          onChange={(e) => handleRuleChange("value", e.target.value)}
        />
      );
    }

    // For select/radio fields, show options
    if (["select", "radio"].includes(sourceField.type) && sourceField.options) {
      return (
        <FormControl fullWidth>
          <InputLabel>Value</InputLabel>
          <Select
            value={editedRule.value}
            label="Value"
            onChange={(e) => handleRuleChange("value", e.target.value)}
          >
            {sourceField.options.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      );
    }

    // For checkbox fields, allow multiple values
    if (sourceField.type === "checkbox" && sourceField.options) {
      return (
        <Autocomplete
          multiple
          options={sourceField.options}
          value={Array.isArray(editedRule.value) ? editedRule.value : []}
          onChange={(_, value) => handleRuleChange("value", value)}
          renderTags={(value, getTagProps) =>
            value.map((option, index) => (
              <Chip
                variant="outlined"
                label={option}
                {...getTagProps({ index })}
              />
            ))
          }
          renderInput={(params) => (
            <TextField {...params} label="Values" placeholder="Select values" />
          )}
        />
      );
    }

    // For number fields
    if (sourceField.type === "number") {
      return (
        <TextField
          fullWidth
          type="number"
          label="Value"
          value={editedRule.value}
          onChange={(e) =>
            handleRuleChange("value", parseFloat(e.target.value) || 0)
          }
        />
      );
    }

    // For date fields
    if (sourceField.type === "date") {
      return (
        <TextField
          fullWidth
          type="date"
          label="Value"
          value={editedRule.value}
          onChange={(e) => handleRuleChange("value", e.target.value)}
          InputLabelProps={{ shrink: true }}
        />
      );
    }

    // Default text input
    return (
      <TextField
        fullWidth
        label="Value"
        value={editedRule.value}
        onChange={(e) => handleRuleChange("value", e.target.value)}
      />
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {rule ? "Edit Conditional Rule" : "Add Conditional Rule"}
      </DialogTitle>

      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {validationError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {validationError}
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Rule Description */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Rule Configuration
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Create a rule that triggers when a field meets certain
                conditions
              </Typography>
            </Grid>

            {/* Source Field */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>When field</InputLabel>
                <Select
                  value={editedRule.sourceFieldId}
                  label="When field"
                  onChange={(e) =>
                    handleRuleChange("sourceFieldId", e.target.value)
                  }
                >
                  {fields.map((field) => (
                    <MenuItem key={field.id} value={field.id}>
                      {field.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Condition */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Condition</InputLabel>
                <Select
                  value={editedRule.condition}
                  label="Condition"
                  onChange={(e) =>
                    handleRuleChange("condition", e.target.value)
                  }
                >
                  {conditions.map((condition) => (
                    <MenuItem key={condition.value} value={condition.value}>
                      {condition.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Value */}
            {requiresValue && (
              <Grid item xs={12}>
                {renderValueInput()}
              </Grid>
            )}

            {/* Action */}
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Then</InputLabel>
                <Select
                  value={editedRule.action}
                  label="Then"
                  onChange={(e) => handleRuleChange("action", e.target.value)}
                >
                  {actions.map((action) => (
                    <MenuItem key={action.value} value={action.value}>
                      {action.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Target Fields */}
            <Grid item xs={12}>
              <Autocomplete
                multiple
                options={getAvailableTargetFields()}
                getOptionLabel={(option) => option.label}
                value={fields.filter((field) =>
                  editedRule.targetFieldIds.includes(field.id)
                )}
                onChange={(_, value) =>
                  handleRuleChange(
                    "targetFieldIds",
                    value.map((field) => field.id)
                  )
                }
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option.label}
                      {...getTagProps({ index })}
                    />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Target Fields"
                    placeholder="Select fields to apply action to"
                  />
                )}
              />
            </Grid>

            {/* Advanced Options */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mt: 2 }}>
                Advanced Options
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Priority"
                value={editedRule.priority || ""}
                onChange={(e) =>
                  handleRuleChange(
                    "priority",
                    parseInt(e.target.value) || undefined
                  )
                }
                helperText="Lower numbers execute first (optional)"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Logic Operator</InputLabel>
                <Select
                  value={editedRule.logicOperator || "AND"}
                  label="Logic Operator"
                  onChange={(e) =>
                    handleRuleChange("logicOperator", e.target.value)
                  }
                >
                  <MenuItem value="AND">AND</MenuItem>
                  <MenuItem value="OR">OR</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Rule Preview */}
            <Grid item xs={12}>
              <Box sx={{ p: 2, bgcolor: "grey.50", borderRadius: 1, mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Rule Preview:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  When "{sourceField?.label || "field"}"{" "}
                  {conditions
                    .find((c) => c.value === editedRule.condition)
                    ?.label.toLowerCase() || "condition"}
                  {requiresValue && ` "${editedRule.value}"`}, then{" "}
                  {actions
                    .find((a) => a.value === editedRule.action)
                    ?.label.toLowerCase() || "action"}{" "}
                  the selected target fields.
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSave}>
          Save Rule
        </Button>
      </DialogActions>
    </Dialog>
  );
};
