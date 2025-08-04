import React, { useState } from "react";
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Paper,
  FormControl,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
} from "@mui/material";
import {
  Add,
  Delete,
  DragIndicator,
  Preview,
  Publish,
  Share,
} from "@mui/icons-material";

interface FormField {
  id: string;
  type:
    | "text"
    | "email"
    | "number"
    | "select"
    | "checkbox"
    | "radio"
    | "textarea"
    | "date";
  label: string;
  placeholder?: string;
  required: boolean;
  options?: string[];
}

interface FormSettings {
  title: string;
  description: string;
  submitButtonText: string;
  successMessage: string;
  allowMultipleSubmissions: boolean;
  collectEmail: boolean;
  requireAuth: boolean;
}

const steps = ["Form Design", "Settings", "Preview", "Publish"];

const PublicFormBuilder: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [formFields, setFormFields] = useState<FormField[]>([]);
  const [formSettings, setFormSettings] = useState<FormSettings>({
    title: "New Form",
    description: "",
    submitButtonText: "Submit",
    successMessage: "Thank you for your submission!",
    allowMultipleSubmissions: true,
    collectEmail: false,
    requireAuth: false,
  });
  const [previewMode, setPreviewMode] = useState(false);

  const fieldTypes = [
    { value: "text", label: "Text Input" },
    { value: "email", label: "Email" },
    { value: "number", label: "Number" },
    { value: "textarea", label: "Long Text" },
    { value: "select", label: "Dropdown" },
    { value: "radio", label: "Multiple Choice" },
    { value: "checkbox", label: "Checkboxes" },
    { value: "date", label: "Date" },
  ];

  const addField = (type: FormField["type"]) => {
    const newField: FormField = {
      id: `field_${Date.now()}`,
      type,
      label: `New ${type} field`,
      placeholder: "",
      required: false,
      options:
        type === "select" || type === "radio" || type === "checkbox"
          ? ["Option 1", "Option 2"]
          : undefined,
    };
    setFormFields([...formFields, newField]);
  };

  const updateField = (id: string, updates: Partial<FormField>) => {
    setFormFields(
      formFields.map((field) =>
        field.id === id ? { ...field, ...updates } : field
      )
    );
  };

  const deleteField = (id: string) => {
    setFormFields(formFields.filter((field) => field.id !== id));
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const renderFieldEditor = (field: FormField) => (
    <Card key={field.id} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <DragIndicator sx={{ color: "text.secondary", mr: 1 }} />
          <Typography variant="h6" sx={{ flex: 1 }}>
            {field.label}
          </Typography>
          <Chip label={field.type} size="small" sx={{ mr: 1 }} />
          <IconButton
            size="small"
            onClick={() => deleteField(field.id)}
            color="error"
          >
            <Delete />
          </IconButton>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Field Label"
              value={field.label}
              onChange={(e) => updateField(field.id, { label: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Placeholder"
              value={field.placeholder || ""}
              onChange={(e) =>
                updateField(field.id, { placeholder: e.target.value })
              }
            />
          </Grid>
          {(field.type === "select" ||
            field.type === "radio" ||
            field.type === "checkbox") && (
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Options
              </Typography>
              {field.options?.map((option, index) => (
                <Box
                  key={index}
                  sx={{ display: "flex", alignItems: "center", mb: 1 }}
                >
                  <TextField
                    size="small"
                    value={option}
                    onChange={(e) => {
                      const newOptions = [...(field.options || [])];
                      newOptions[index] = e.target.value;
                      updateField(field.id, { options: newOptions });
                    }}
                    sx={{ flex: 1, mr: 1 }}
                  />
                  <IconButton
                    size="small"
                    onClick={() => {
                      const newOptions = field.options?.filter(
                        (_, i) => i !== index
                      );
                      updateField(field.id, { options: newOptions });
                    }}
                  >
                    <Delete />
                  </IconButton>
                </Box>
              ))}
              <Button
                size="small"
                startIcon={<Add />}
                onClick={() => {
                  const newOptions = [
                    ...(field.options || []),
                    `Option ${(field.options?.length || 0) + 1}`,
                  ];
                  updateField(field.id, { options: newOptions });
                }}
              >
                Add Option
              </Button>
            </Grid>
          )}
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={field.required}
                  onChange={(e) =>
                    updateField(field.id, { required: e.target.checked })
                  }
                />
              }
              label="Required field"
            />
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

  const renderFormDesign = () => (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography variant="h5">Form Design</Typography>
        <Button
          variant="outlined"
          startIcon={<Preview />}
          onClick={() => setPreviewMode(!previewMode)}
        >
          {previewMode ? "Edit" : "Preview"}
        </Button>
      </Box>

      {!previewMode ? (
        <>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Add Fields
            </Typography>
            <Grid container spacing={1}>
              {fieldTypes.map((fieldType) => (
                <Grid item key={fieldType.value}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Add />}
                    onClick={() =>
                      addField(fieldType.value as FormField["type"])
                    }
                  >
                    {fieldType.label}
                  </Button>
                </Grid>
              ))}
            </Grid>
          </Box>

          <Box>
            <Typography variant="h6" gutterBottom>
              Form Fields
            </Typography>
            {formFields.length === 0 ? (
              <Paper sx={{ p: 3, textAlign: "center" }}>
                <Typography color="text.secondary">
                  No fields added yet. Click on the buttons above to add form
                  fields.
                </Typography>
              </Paper>
            ) : (
              formFields.map(renderFieldEditor)
            )}
          </Box>
        </>
      ) : (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" gutterBottom>
            {formSettings.title}
          </Typography>
          {formSettings.description && (
            <Typography variant="body1" sx={{ mb: 3 }}>
              {formSettings.description}
            </Typography>
          )}

          {formFields.map((field) => (
            <Box key={field.id} sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                {field.label}{" "}
                {field.required && <span className="required-asterisk">*</span>}
              </Typography>
              {field.type === "textarea" && (
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder={field.placeholder}
                />
              )}
              {field.type === "select" && (
                <FormControl fullWidth>
                  <Select placeholder={field.placeholder}>
                    {field.options?.map((option, index) => (
                      <MenuItem key={index} value={option}>
                        {option}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}
              {["text", "email", "number", "date"].includes(field.type) && (
                <TextField
                  fullWidth
                  type={field.type}
                  placeholder={field.placeholder}
                />
              )}
            </Box>
          ))}

          <Button variant="contained" sx={{ mt: 2 }}>
            {formSettings.submitButtonText}
          </Button>
        </Paper>
      )}
    </Box>
  );

  const renderFormSettings = () => (
    <Box>
      <Typography variant="h5" gutterBottom>
        Form Settings
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Form Title"
            value={formSettings.title}
            onChange={(e) =>
              setFormSettings({ ...formSettings, title: e.target.value })
            }
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label="Submit Button Text"
            value={formSettings.submitButtonText}
            onChange={(e) =>
              setFormSettings({
                ...formSettings,
                submitButtonText: e.target.value,
              })
            }
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Form Description"
            value={formSettings.description}
            onChange={(e) =>
              setFormSettings({ ...formSettings, description: e.target.value })
            }
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="Success Message"
            value={formSettings.successMessage}
            onChange={(e) =>
              setFormSettings({
                ...formSettings,
                successMessage: e.target.value,
              })
            }
          />
        </Grid>
        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={formSettings.allowMultipleSubmissions}
                onChange={(e) =>
                  setFormSettings({
                    ...formSettings,
                    allowMultipleSubmissions: e.target.checked,
                  })
                }
              />
            }
            label="Allow multiple submissions from same user"
          />
        </Grid>
        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={formSettings.collectEmail}
                onChange={(e) =>
                  setFormSettings({
                    ...formSettings,
                    collectEmail: e.target.checked,
                  })
                }
              />
            }
            label="Collect email addresses"
          />
        </Grid>
        <Grid item xs={12}>
          <FormControlLabel
            control={
              <Switch
                checked={formSettings.requireAuth}
                onChange={(e) =>
                  setFormSettings({
                    ...formSettings,
                    requireAuth: e.target.checked,
                  })
                }
              />
            }
            label="Require user authentication"
          />
        </Grid>
      </Grid>
    </Box>
  );

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return renderFormDesign();
      case 1:
        return renderFormSettings();
      case 2:
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Preview & Test
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              This is how your form will appear to users. Test it to ensure
              everything works correctly.
            </Alert>
            {renderFormDesign()}
          </Box>
        );
      case 3:
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Publish Form
            </Typography>
            <Alert severity="success" sx={{ mb: 2 }}>
              Your form is ready to be published! You can share it with users or
              embed it on your website.
            </Alert>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Button variant="contained" fullWidth startIcon={<Publish />}>
                  Publish Form
                </Button>
              </Grid>
              <Grid item xs={12} md={6}>
                <Button variant="outlined" fullWidth startIcon={<Share />}>
                  Get Share Link
                </Button>
              </Grid>
            </Grid>
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Public Form Builder
        </Typography>

        <Typography
          variant="h6"
          color="text.secondary"
          gutterBottom
          sx={{ mb: 4 }}
        >
          Create custom forms that anyone can fill out without authentication
        </Typography>

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Card>
          <CardContent sx={{ p: 4 }}>{renderStepContent()}</CardContent>
        </Card>

        <Box sx={{ display: "flex", justifyContent: "space-between", mt: 3 }}>
          <Button disabled={activeStep === 0} onClick={handleBack}>
            Back
          </Button>
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={activeStep === steps.length - 1}
          >
            {activeStep === steps.length - 1 ? "Finish" : "Next"}
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default PublicFormBuilder;
