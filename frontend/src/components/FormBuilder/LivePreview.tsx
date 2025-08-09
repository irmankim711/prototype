/**
 * Live Preview Component
 * Real-time form preview with conditional logic evaluation
 */

import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Alert,
} from "@mui/material";

import type { Form, FormFieldValue } from "../../types/formBuilder";
import type { ConditionalLogicEngine } from "../../utils/conditionalLogicEngine";

interface LivePreviewProps {
  form: Partial<Form>;
  data: Record<string, FormFieldValue>;
  onDataChange: (fieldId: string, value: FormFieldValue) => void;
  logicEngine: ConditionalLogicEngine;
}

export const LivePreview: React.FC<LivePreviewProps> = ({
  form,
  data,
  onDataChange,
}) => {
  const [fieldStates, setFieldStates] = useState<
    Record<
      string,
      {
        visible: boolean;
        required: boolean;
        disabled: boolean;
      }
    >
  >({});

  // Update field states when data changes
  useEffect(() => {
    if (!form.schema?.fields) return;

    const states: Record<
      string,
      {
        visible: boolean;
        required: boolean;
        disabled: boolean;
      }
    > = {};

    form.schema.fields.forEach((field) => {
      states[field.id] = {
        visible: true,
        required: field.required || false,
        disabled: field.readonly || false,
      };
    });

    setFieldStates(states);
  }, [form.schema?.fields]);

  // Handle field value change
  const handleFieldChange = (fieldId: string, value: FormFieldValue) => {
    onDataChange(fieldId, value);
  };

  if (!form.schema?.fields || form.schema.fields.length === 0) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: 400,
          bgcolor: "grey.50",
          borderRadius: 2,
          border: "2px dashed",
          borderColor: "grey.300",
        }}
      >
        <Typography variant="h6" color="text.secondary">
          Add fields to see live preview
        </Typography>
      </Box>
    );
  }

  return (
    <Card>
      <CardContent sx={{ p: 4 }}>
        {/* Form Header */}
        <Box mb={4}>
          <Typography variant="h4" gutterBottom>
            {form.title || "Form Preview"}
          </Typography>
          {form.description && (
            <Typography variant="body1" color="text.secondary" paragraph>
              {form.description}
            </Typography>
          )}
        </Box>

        {/* Form Fields */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          {form.schema.fields
            .sort((a, b) => a.order - b.order)
            .map((field) => {
              const state = fieldStates[field.id];
              if (!state?.visible) return null;

              const fieldValue = data[field.id] || field.default_value || "";
              const isRequired = state.required;
              const isDisabled = state.disabled;

              return (
                <Box key={field.id}>
                  {field.type === "text" ||
                  field.type === "email" ||
                  field.type === "textarea" ? (
                    <TextField
                      fullWidth
                      required={isRequired}
                      disabled={isDisabled}
                      label={field.label}
                      placeholder={field.placeholder}
                      type={field.type === "email" ? "email" : "text"}
                      multiline={field.type === "textarea"}
                      rows={field.type === "textarea" ? 4 : 1}
                      value={fieldValue}
                      onChange={(e) =>
                        handleFieldChange(field.id, e.target.value)
                      }
                      helperText={field.description}
                    />
                  ) : (
                    <Alert severity="info">
                      Field type "{field.type}" preview not implemented yet
                    </Alert>
                  )}
                </Box>
              );
            })}
        </Box>

        {/* Submit Button */}
        <Box mt={4} display="flex" justifyContent="flex-end">
          <Button
            variant="contained"
            size="large"
            disabled={true}
            sx={{ minWidth: 120 }}
          >
            Submit (Preview)
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};
