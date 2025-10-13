/**
 * Create Data Source Dialog Component
 */

import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Box,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Typography,
  Chip,
} from "@mui/material";
import { useMutation } from "@tanstack/react-query";
import {
  formPipelineApi,
  type CreateDataSourceRequest,
} from "../services/formPipelineApi";

interface CreateDataSourceDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const sourceTypes = [
  { value: "google_forms", label: "Google Forms", icon: "📋" },
  { value: "microsoft_forms", label: "Microsoft Forms", icon: "📊" },
  { value: "zoho_forms", label: "Zoho Forms", icon: "📄" },
  { value: "typeform", label: "Typeform", icon: "📝" },
  { value: "custom", label: "Custom Form", icon: "⚙️" },
];

const steps = ["Basic Info", "Configuration", "Sync Settings"];

export const CreateDataSourceDialog: React.FC<CreateDataSourceDialogProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState<CreateDataSourceRequest>({
    name: "",
    source_type: "",
    source_id: "",
    source_url: "",
    webhook_secret: "",
    api_config: {},
    field_mapping: {},
    auto_sync: true,
    sync_interval: 300,
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateDataSourceRequest) =>
      formPipelineApi.createDataSource(data),
    onSuccess: () => {
      onSuccess();
      handleClose();
    },
  });

  const handleClose = () => {
    setActiveStep(0);
    setFormData({
      name: "",
      source_type: "",
      source_id: "",
      source_url: "",
      webhook_secret: "",
      api_config: {},
      field_mapping: {},
      auto_sync: true,
      sync_interval: 300,
    });
    onClose();
  };

  const handleNext = () => {
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleSubmit = () => {
    createMutation.mutate(formData);
  };

  const updateFormData = (
    field: keyof CreateDataSourceRequest,
    value: string | number | boolean | Record<string, unknown>
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const isStepValid = (step: number): boolean => {
    switch (step) {
      case 0:
        return !!(formData.name && formData.source_type && formData.source_id);
      case 1:
        return true; // Configuration is optional
      case 2:
        return true; // Sync settings have defaults
      default:
        return false;
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ minHeight: 300 }}>
            <TextField
              fullWidth
              label="Data Source Name"
              value={formData.name}
              onChange={(e) => updateFormData("name", e.target.value)}
              margin="normal"
              required
              helperText="A descriptive name for this data source"
            />

            <FormControl fullWidth margin="normal" required>
              <InputLabel>Source Type</InputLabel>
              <Select
                value={formData.source_type}
                onChange={(e) => updateFormData("source_type", e.target.value)}
                label="Source Type"
              >
                {sourceTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <span>{type.icon}</span>
                      {type.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Source ID"
              value={formData.source_id}
              onChange={(e) => updateFormData("source_id", e.target.value)}
              margin="normal"
              required
              helperText="The unique identifier for your form (e.g., form ID from the provider)"
            />

            <TextField
              fullWidth
              label="Source URL (Optional)"
              value={formData.source_url}
              onChange={(e) => updateFormData("source_url", e.target.value)}
              margin="normal"
              helperText="Direct link to the form"
            />
          </Box>
        );

      case 1:
        return (
          <Box sx={{ minHeight: 300 }}>
            <Typography variant="h6" gutterBottom>
              Configuration
            </Typography>

            <TextField
              fullWidth
              label="Webhook Secret (Optional)"
              value={formData.webhook_secret}
              onChange={(e) => updateFormData("webhook_secret", e.target.value)}
              margin="normal"
              type="password"
              helperText="Secret key for webhook verification (recommended for security)"
            />

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Webhook URL:</strong> Your webhook endpoint will be:
                <br />
                <code>
                  {window.location.origin}/api/forms/webhook/
                  {formData.source_type || "{source_type}"}
                </code>
              </Typography>
            </Alert>

            {formData.source_type && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Integration Instructions:
                </Typography>
                <Chip
                  label={`${
                    sourceTypes.find((t) => t.value === formData.source_type)
                      ?.label
                  } Setup`}
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="textSecondary">
                  {getIntegrationInstructions(formData.source_type)}
                </Typography>
              </Box>
            )}
          </Box>
        );

      case 2:
        return (
          <Box sx={{ minHeight: 300 }}>
            <Typography variant="h6" gutterBottom>
              Sync Settings
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={formData.auto_sync}
                  onChange={(e) =>
                    updateFormData("auto_sync", e.target.checked)
                  }
                />
              }
              label="Enable Automatic Synchronization"
              sx={{ mb: 2 }}
            />

            {formData.auto_sync && (
              <TextField
                fullWidth
                label="Sync Interval (seconds)"
                type="number"
                value={formData.sync_interval}
                onChange={(e) =>
                  updateFormData(
                    "sync_interval",
                    parseInt(e.target.value) || 300
                  )
                }
                margin="normal"
                helperText="How often to check for new submissions (minimum 60 seconds)"
                inputProps={{ min: 60, max: 86400 }}
              />
            )}

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                You can always manually trigger synchronization from the
                dashboard. Automatic sync will only run when there are webhooks
                or API access configured.
              </Typography>
            </Alert>
          </Box>
        );

      default:
        return null;
    }
  };

  const getIntegrationInstructions = (sourceType: string): string => {
    switch (sourceType) {
      case "google_forms":
        return "Configure Google Forms to send notifications to the webhook URL above. You may need to set up a Google Cloud Pub/Sub topic.";
      case "microsoft_forms":
        return "Set up a Microsoft Power Automate flow to call the webhook URL when new responses are submitted.";
      case "zoho_forms":
        return "Configure Zoho Forms webhook integration to send data to the webhook URL above.";
      case "typeform":
        return "Add the webhook URL to your Typeform webhook settings in the Connect panel.";
      case "custom":
        return "Configure your custom form to POST submission data to the webhook URL above.";
      default:
        return "Follow your form provider's webhook documentation to integrate with the URL above.";
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Data Source</DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {createMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to create data source. Please try again.
          </Alert>
        )}

        {renderStepContent(activeStep)}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>

        {activeStep > 0 && <Button onClick={handleBack}>Back</Button>}

        {activeStep < steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={!isStepValid(activeStep)}
          >
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!isStepValid(activeStep) || createMutation.isPending}
          >
            {createMutation.isPending ? "Creating..." : "Create Data Source"}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};
