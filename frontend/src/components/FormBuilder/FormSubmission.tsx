import React, { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  FormControl,
  FormControlLabel,
  FormLabel,
  RadioGroup,
  Radio,
  Checkbox,
  FormGroup,
  Rating,
  Alert,
  Snackbar,
  CircularProgress,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  Divider,
  Chip,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  InputLabel,
} from "@mui/material";
import {
  Send,
  CheckCircle,
  Error,
  Warning,
  Help,
  Star,
  LocationOn,
  Phone,
  Link,
  Email,
  Numbers,
  TextFields,
  Subject,
  DateRange,
  AccessTime,
  Event,
  AttachFile,
  ArrowDropDown,
  RadioButtonChecked,
  CheckBox,
} from "@mui/icons-material";
import {
  formBuilderAPI,
  type Form,
  type FormField,
  formBuilderUtils,
} from "../../services/formBuilder";

interface FormSubmissionProps {
  formId: number;
  onSuccess?: (submissionId: number) => void;
  onError?: (error: string) => void;
}

interface FormData {
  [key: string]: any;
}

export default function FormSubmission({
  formId,
  onSuccess,
  onError,
}: FormSubmissionProps) {
  const [formData, setFormData] = useState<FormData>({});
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [activeStep, setActiveStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success" as "success" | "error" | "warning" | "info",
  });

  // Fetch form data
  const {
    data: form,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["form", formId],
    queryFn: () => formBuilderAPI.getForm(formId),
    enabled: !!formId,
  });

  // Submit form mutation
  const submitMutation = useMutation({
    mutationFn: (data: { data: FormData; email?: string }) =>
      formBuilderAPI.submitForm(formId, data),
    onSuccess: (data) => {
      setSnackbar({
        open: true,
        message: "Form submitted successfully!",
        severity: "success",
      });
      onSuccess?.(data.submission_id);
    },
    onError: (error: any) => {
      const message = error.response?.data?.error || "Failed to submit form";
      setSnackbar({ open: true, message, severity: "error" });
      onError?.(message);
    },
  });

  // Initialize form data with default values
  useEffect(() => {
    if (form?.schema?.fields) {
      const initialData: FormData = {};
      form.schema.fields.forEach((field) => {
        if (field.defaultValue !== undefined) {
          initialData[field.id] = field.defaultValue;
        }
      });
      setFormData(initialData);
    }
  }, [form]);

  // Validate form data
  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    form?.schema?.fields.forEach((field) => {
      const value = formData[field.id];

      // Check required fields
      if (
        field.required &&
        (value === undefined || value === null || value === "")
      ) {
        newErrors[field.id] = `${field.label} is required`;
        return;
      }

      // Skip validation for empty optional fields
      if (value === undefined || value === null || value === "") {
        return;
      }

      // Type-specific validation
      switch (field.type) {
        case "email":
          const emailPattern =
            /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
          if (!emailPattern.test(String(value))) {
            newErrors[field.id] = "Please enter a valid email address";
          }
          break;

        case "number":
          const numValue = Number(value);
          if (isNaN(numValue)) {
            newErrors[field.id] = "Please enter a valid number";
          } else {
            if (
              field.validation?.min !== undefined &&
              numValue < field.validation.min
            ) {
              newErrors[
                field.id
              ] = `Value must be at least ${field.validation.min}`;
            }
            if (
              field.validation?.max !== undefined &&
              numValue > field.validation.max
            ) {
              newErrors[
                field.id
              ] = `Value must be at most ${field.validation.max}`;
            }
          }
          break;

        case "text":
        case "textarea":
          const textValue = String(value);
          if (
            field.validation?.minLength &&
            textValue.length < field.validation.minLength
          ) {
            newErrors[
              field.id
            ] = `Must be at least ${field.validation.minLength} characters`;
          }
          if (
            field.validation?.maxLength &&
            textValue.length > field.validation.maxLength
          ) {
            newErrors[
              field.id
            ] = `Must be at most ${field.validation.maxLength} characters`;
          }
          break;

        case "select":
        case "radio":
          if (field.options && !field.options.includes(String(value))) {
            newErrors[field.id] = "Please select a valid option";
          }
          break;

        case "rating":
          const ratingValue = Number(value);
          if (isNaN(ratingValue) || ratingValue < 1 || ratingValue > 5) {
            newErrors[field.id] = "Please select a rating between 1 and 5";
          }
          break;
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle field value change
  const handleFieldChange = (fieldId: string, value: any) => {
    setFormData((prev) => ({ ...prev, [fieldId]: value }));

    // Clear error for this field
    if (errors[fieldId]) {
      setErrors((prev) => ({ ...prev, [fieldId]: "" }));
    }
  };

  // Handle form submission
  const handleSubmit = async () => {
    if (!validateForm()) {
      setSnackbar({
        open: true,
        message: "Please fix the errors before submitting",
        severity: "error",
      });
      return;
    }

    setIsSubmitting(true);
    try {
      await submitMutation.mutateAsync({ data: formData });
    } finally {
      setIsSubmitting(false);
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
      location: <LocationOn />,
    };
    return icons[type] || <TextFields />;
  };

  // Render form field
  const renderField = (field: FormField) => {
    const value = formData[field.id];
    const error = errors[field.id];
    const hasError = !!error;

    switch (field.type) {
      case "text":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="on"
          />
        );

      case "textarea":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            multiline
            rows={4}
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="on"
          />
        );

      case "email":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            type="email"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="email"
          />
        );

      case "number":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            type="number"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="off"
          />
        );

      case "select":
        return (
          <FormControl
            fullWidth
            margin="normal"
            error={hasError}
            required={field.required}
          >
            <InputLabel>{field.label}</InputLabel>
            <Select
              value={value || ""}
              onChange={(e) => handleFieldChange(field.id, e.target.value)}
              label={field.label}
              startAdornment={getFieldIcon(field.type)}
            >
              {field.options?.map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
            {error && (
              <Typography variant="caption" color="error">
                {error}
              </Typography>
            )}
          </FormControl>
        );

      case "radio":
        return (
          <FormControl
            component="fieldset"
            margin="normal"
            error={hasError}
            required={field.required}
          >
            <FormLabel component="legend">
              <Box display="flex" alignItems="center" gap={1}>
                {getFieldIcon(field.type)}
                {field.label}
              </Box>
            </FormLabel>
            <RadioGroup
              value={value || ""}
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
            {error && (
              <Typography variant="caption" color="error">
                {error}
              </Typography>
            )}
          </FormControl>
        );

      case "checkbox":
        return (
          <FormControl
            component="fieldset"
            margin="normal"
            error={hasError}
            required={field.required}
          >
            <FormLabel component="legend">
              <Box display="flex" alignItems="center" gap={1}>
                {getFieldIcon(field.type)}
                {field.label}
              </Box>
            </FormLabel>
            <FormGroup>
              {field.options?.map((option) => (
                <FormControlLabel
                  key={option}
                  control={
                    <Checkbox
                      checked={
                        Array.isArray(value) ? value.includes(option) : false
                      }
                      onChange={(e) => {
                        const currentValue = Array.isArray(value) ? value : [];
                        const newValue = e.target.checked
                          ? [...currentValue, option]
                          : currentValue.filter((v) => v !== option);
                        handleFieldChange(field.id, newValue);
                      }}
                    />
                  }
                  label={option}
                />
              ))}
            </FormGroup>
            {error && (
              <Typography variant="caption" color="error">
                {error}
              </Typography>
            )}
          </FormControl>
        );

      case "date":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            type="date"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="bday"
          />
        );

      case "time":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            type="time"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="off"
          />
        );

      case "datetime":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            type="datetime-local"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="off"
          />
        );

      case "phone":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            type="tel"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="tel"
          />
        );

      case "url":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            type="url"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="url"
          />
        );

      case "rating":
        return (
          <Box margin="normal">
            <Typography component="legend" gutterBottom>
              <Box display="flex" alignItems="center" gap={1}>
                {getFieldIcon(field.type)}
                {field.label}
                {field.required && (
                  <Chip label="Required" size="small" color="primary" />
                )}
              </Box>
            </Typography>
            <Rating
              value={Number(value) || 0}
              onChange={(_, newValue) => handleFieldChange(field.id, newValue)}
              size="large"
            />
            {error && (
              <Typography variant="caption" color="error">
                {error}
              </Typography>
            )}
          </Box>
        );

      case "file":
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            fullWidth
            margin="normal"
            type="file"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            onChange={(e) => {
              const file = (e.target as HTMLInputElement).files?.[0];
              handleFieldChange(field.id, file);
            }}
          />
        );

      default:
        return (
          <TextField
            label={field.label}
            placeholder={field.placeholder}
            value={value || ""}
            onChange={(e) => handleFieldChange(field.id, e.target.value)}
            fullWidth
            margin="normal"
            error={hasError}
            helperText={error}
            required={field.required}
            InputProps={{
              startAdornment: getFieldIcon(field.type),
            }}
            autoComplete="on"
          />
        );
    }
  };

  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <Alert severity="error">Failed to load form. Please try again.</Alert>
      </Box>
    );
  }

  if (!form) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <Alert severity="warning">Form not found.</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", p: 3 }}>
      {/* Form Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography
          variant="h4"
          gutterBottom
          sx={{ fontWeight: 600, color: "#1e3a8a" }}
        >
          {form.title}
        </Typography>
        {form.description && (
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            {form.description}
          </Typography>
        )}
        <Box display="flex" gap={1} flexWrap="wrap">
          <Chip
            label={form.is_public ? "Public Form" : "Private Form"}
            color={form.is_public ? "success" : "default"}
            size="small"
          />
          {form.statistics && (
            <Chip
              label={`${form.statistics.total_submissions} submissions`}
              color="primary"
              size="small"
            />
          )}
        </Box>
      </Paper>

      {/* Form Fields */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Please fill out the form below
        </Typography>

        <Box
          component="form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
        >
          {form.schema?.fields.map((field, index) => (
            <Box key={field.id} sx={{ mb: 3 }}>
              {renderField(field)}
              {field.helpText && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ mt: 1, display: "block" }}
                >
                  <Help
                    fontSize="small"
                    sx={{ mr: 0.5, verticalAlign: "middle" }}
                  />
                  {field.helpText}
                </Typography>
              )}
            </Box>
          ))}

          {/* Submit Button */}
          <Box sx={{ mt: 4, display: "flex", justifyContent: "center" }}>
            <Button
              type="submit"
              variant="contained"
              size="large"
              startIcon={
                isSubmitting ? <CircularProgress size={20} /> : <Send />
              }
              disabled={isSubmitting}
              sx={{ minWidth: 200 }}
            >
              {isSubmitting ? "Submitting..." : "Submit Form"}
            </Button>
          </Box>
        </Box>
      </Paper>

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
