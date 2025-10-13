import React, { useState } from "react";
import {
  Box,
  TextField,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Checkbox,
  Select,
  MenuItem,
  InputLabel,
  CircularProgress,
  Alert,
} from "@mui/material";

interface FormField {
  id: string;
  type:
    | "text"
    | "email"
    | "number"
    | "textarea"
    | "select"
    | "radio"
    | "checkbox";
  label: string;
  required?: boolean;
  options?: string[];
  placeholder?: string;
}

interface FormSchema {
  fields: FormField[];
  title?: string;
  description?: string;
}

interface FormRendererProps {
  schema: FormSchema;
  onSubmit: (data: Record<string, any>) => void;
  loading?: boolean;
}

const FormRenderer: React.FC<FormRendererProps> = ({
  schema,
  onSubmit,
  loading = false,
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleFieldChange = (fieldId: string, value: any) => {
    setFormData((prev) => ({ ...prev, [fieldId]: value }));
    if (errors[fieldId]) {
      setErrors((prev) => ({ ...prev, [fieldId]: "" }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    schema.fields.forEach((field) => {
      if (
        field.required &&
        (!formData[field.id] || formData[field.id] === "")
      ) {
        newErrors[field.id] = `${field.label} is required`;
      }

      if (field.type === "email" && formData[field.id]) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData[field.id])) {
          newErrors[field.id] = "Please enter a valid email address";
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const renderField = (field: FormField) => {
    const commonProps = {
      key: field.id,
      fullWidth: true,
      margin: "normal" as const,
      error: !!errors[field.id],
      helperText: errors[field.id],
    };

    switch (field.type) {
      case "text":
      case "email":
      case "number":
        return (
          <TextField
            {...commonProps}
            id={field.id}
            label={field.label}
            type={field.type}
            value={formData[field.id] || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            required={field.required}
            placeholder={field.placeholder}
          />
        );

      case "textarea":
        return (
          <TextField
            {...commonProps}
            id={field.id}
            label={field.label}
            multiline
            rows={4}
            value={formData[field.id] || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            required={field.required}
            placeholder={field.placeholder}
          />
        );

      case "select":
        return (
          <FormControl {...commonProps} key={field.id}>
            <InputLabel id={`${field.id}-label`}>{field.label}</InputLabel>
            <Select
              labelId={`${field.id}-label`}
              id={field.id}
              value={formData[field.id] || ""}
              label={field.label}
              onChange={(e) => handleFieldChange(field.id, e.target.value)}
              required={field.required}
            >
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
          <FormControl {...commonProps} key={field.id}>
            <FormLabel component="legend">{field.label}</FormLabel>
            <RadioGroup
              value={formData[field.id] || ""}
              onChange={(e) => handleFieldChange(field.id, e.target.value)}
            >
              {field.options?.map((option) => (
                <FormControlLabel
                  key={option}
                  value={option}
                  control={<Radio />}
                  label={option}
                />
              ))}
            </RadioGroup>
          </FormControl>
        );

      case "checkbox":
        return (
          <FormControl {...commonProps} key={field.id}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData[field.id] || false}
                  onChange={(e) =>
                    handleFieldChange(field.id, e.target.checked)
                  }
                />
              }
              label={field.label}
            />
          </FormControl>
        );

      default:
        return null;
    }
  };

  if (!schema?.fields) {
    return <Alert severity="error">Invalid form schema</Alert>;
  }

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
      {schema.title && (
        <Box sx={{ mb: 2 }}>
          <h2>{schema.title}</h2>
          {schema.description && <p>{schema.description}</p>}
        </Box>
      )}

      {schema.fields.map(renderField)}

      <Button
        type="submit"
        variant="contained"
        sx={{ mt: 3, mb: 2 }}
        disabled={loading}
        startIcon={loading ? <CircularProgress size={20} /> : null}
      >
        {loading ? "Submitting..." : "Submit"}
      </Button>
    </Box>
  );
};

export default FormRenderer;
