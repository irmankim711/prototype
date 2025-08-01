import { useState, useCallback } from "react";
import {
  Box,
  Typography,
  Button,
  TextField,
  FormControlLabel,
  Checkbox,
  Card,
  CardContent,
  Grid,
  Alert,
  Snackbar,
  Paper,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Switch,
} from "@mui/material";
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  DragIndicator as DragIcon,
  Save as SaveIcon,
  Preview as PreviewIcon,
  Public as PublicIcon,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import type { FormField, FormData } from "../../types/forms";

const GlassPaper = styled(Paper)(() => ({
  background: "rgba(255, 255, 255, 0.1)",
  backdropFilter: "blur(20px)",
  border: "1px solid rgba(255, 255, 255, 0.2)",
  borderRadius: "16px",
  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
}));

const FieldCard = styled(Card)(() => ({
  marginBottom: "16px",
  borderRadius: "12px",
  border: "1px solid #e0e0e0",
  transition: "all 0.2s ease-in-out",
  "&:hover": {
    boxShadow: "0 4px 16px rgba(0, 0, 0, 0.1)",
    transform: "translateY(-2px)",
  },
}));

const FIELD_TYPES = [
  { value: "text", label: "Text Input" },
  { value: "textarea", label: "Textarea" },
  { value: "email", label: "Email" },
  { value: "number", label: "Number" },
  { value: "tel", label: "Phone" },
  { value: "url", label: "URL" },
  { value: "select", label: "Dropdown" },
  { value: "radio", label: "Radio Buttons" },
  { value: "checkbox", label: "Checkbox" },
  { value: "date", label: "Date" },
  { value: "time", label: "Time" },
  { value: "file", label: "File Upload" },
];

const EnhancedFormBuilder = () => {
  const [formData, setFormData] = useState<FormData>({
    title: "",
    description: "",
    schema: [],
    is_public: false,
    is_active: true,
    external_url: "",
  });

  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const addField = useCallback(() => {
    const newField: FormField = {
      id: `field_${Date.now()}`,
      type: "text",
      label: "New Field",
      required: false,
      placeholder: "",
    };

    setFormData((prev) => ({
      ...prev,
      schema: [...prev.schema, newField],
    }));
  }, []);

  const updateField = useCallback(
    (index: number, updates: Partial<FormField>) => {
      setFormData((prev) => ({
        ...prev,
        schema: prev.schema.map((field, i) =>
          i === index ? { ...field, ...updates } : field
        ),
      }));
    },
    []
  );

  const deleteField = useCallback((index: number) => {
    setFormData((prev) => ({
      ...prev,
      schema: prev.schema.filter((_, i) => i !== index),
    }));
  }, []);

  const moveField = useCallback((fromIndex: number, toIndex: number) => {
    setFormData((prev) => {
      const newSchema = [...prev.schema];
      const [removed] = newSchema.splice(fromIndex, 1);
      newSchema.splice(toIndex, 0, removed);
      return { ...prev, schema: newSchema };
    });
  }, []);

  const saveForm = useCallback(async () => {
    if (!formData.title.trim()) {
      setError("Form title is required");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch("/api/admin/forms", {
        method: "POST",
        headers: {
          Authorization: `Bearer dev-bypass-token`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        await response.json();
        setSuccess(`Form "${formData.title}" created successfully!`);

        // Reset form after successful creation
        setFormData({
          title: "",
          description: "",
          schema: [],
          is_public: false,
          is_active: true,
          external_url: "",
        });
      } else {
        const errorData = await response.json();
        setError(errorData.error || "Failed to create form");
      }
    } catch {
      setError("Error creating form");
    } finally {
      setSaving(false);
    }
  }, [formData]);

  const previewForm = useCallback(() => {
    // Open preview in new tab/modal
    console.log("Preview form:", formData);
    // You can implement a preview modal here
  }, [formData]);

  const renderFieldEditor = (field: FormField, index: number) => (
    <FieldCard key={field.id}>
      <CardContent>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
          <IconButton size="small">
            <DragIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Field {index + 1}
          </Typography>
          <IconButton
            size="small"
            color="error"
            onClick={() => deleteField(index)}
          >
            <DeleteIcon />
          </IconButton>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Field Type</InputLabel>
              <Select
                value={field.type}
                label="Field Type"
                onChange={(e) => updateField(index, { type: e.target.value })}
              >
                {FIELD_TYPES.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Field Label"
              value={field.label}
              onChange={(e) => updateField(index, { label: e.target.value })}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Placeholder"
              value={field.placeholder || ""}
              onChange={(e) =>
                updateField(index, { placeholder: e.target.value })
              }
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={field.required || false}
                  onChange={(e) =>
                    updateField(index, { required: e.target.checked })
                  }
                />
              }
              label="Required Field"
            />
          </Grid>

          {(field.type === "select" || field.type === "radio") && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Options (one per line)"
                multiline
                rows={3}
                value={(field.options || []).join("\n")}
                onChange={(e) =>
                  updateField(index, {
                    options: e.target.value
                      .split("\n")
                      .filter((option) => option.trim()),
                  })
                }
                placeholder="Option 1&#10;Option 2&#10;Option 3"
              />
            </Grid>
          )}
        </Grid>
      </CardContent>
    </FieldCard>
  );

  return (
    <Box
      sx={{
        p: 3,
        minHeight: "100vh",
        background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
      }}
    >
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, color: "#333", mb: 1 }}>
          Enhanced Form Builder
        </Typography>
        <Typography variant="subtitle1" sx={{ color: "#666" }}>
          Create dynamic forms that automatically appear in your public forms
          page
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Form Settings */}
        <Grid item xs={12} md={4}>
          <GlassPaper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Form Settings
            </Typography>

            <TextField
              fullWidth
              label="Form Title"
              value={formData.title}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, title: e.target.value }))
              }
              sx={{ mb: 2 }}
              required
            />

            <TextField
              fullWidth
              label="Description"
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              multiline
              rows={3}
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="External URL (optional)"
              value={formData.external_url}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  external_url: e.target.value,
                }))
              }
              placeholder="https://example.com/form"
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
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
                    color="primary"
                  />
                }
                label={
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <PublicIcon fontSize="small" />
                    Make Form Public
                  </Box>
                }
              />

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
                    color="primary"
                  />
                }
                label="Form is Active"
              />
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: "flex", gap: 1, flexDirection: "column" }}>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={saveForm}
                disabled={saving || !formData.title.trim()}
                sx={{
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  borderRadius: "12px",
                  textTransform: "none",
                  fontWeight: 600,
                }}
              >
                {saving ? "Saving..." : "Save Form"}
              </Button>

              <Button
                variant="outlined"
                startIcon={<PreviewIcon />}
                onClick={previewForm}
                sx={{ borderRadius: "12px", textTransform: "none" }}
              >
                Preview
              </Button>
            </Box>

            {/* Form Stats */}
            <Box
              sx={{
                mt: 3,
                p: 2,
                bgcolor: "rgba(255, 255, 255, 0.5)",
                borderRadius: 2,
              }}
            >
              <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                Form Statistics
              </Typography>
              <Typography variant="body2">
                Fields: {formData.schema.length}
              </Typography>
              <Typography variant="body2">
                Required Fields:{" "}
                {formData.schema.filter((f) => f.required).length}
              </Typography>
              <Typography variant="body2">
                Status: {formData.is_active ? "Active" : "Inactive"}
              </Typography>
              <Typography variant="body2">
                Visibility: {formData.is_public ? "Public" : "Private"}
              </Typography>
            </Box>
          </GlassPaper>
        </Grid>

        {/* Form Fields */}
        <Grid item xs={12} md={8}>
          <GlassPaper sx={{ p: 3 }}>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 3,
              }}
            >
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Form Fields
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={addField}
                sx={{
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  borderRadius: "12px",
                  textTransform: "none",
                }}
              >
                Add Field
              </Button>
            </Box>

            {formData.schema.length === 0 ? (
              <Box
                sx={{
                  textAlign: "center",
                  py: 4,
                  border: "2px dashed #ccc",
                  borderRadius: 2,
                  bgcolor: "rgba(255, 255, 255, 0.5)",
                }}
              >
                <Typography variant="body1" color="textSecondary">
                  No fields added yet. Click "Add Field" to get started.
                </Typography>
              </Box>
            ) : (
              <Box>
                {formData.schema.map((field, index) =>
                  renderFieldEditor(field, index)
                )}
              </Box>
            )}
          </GlassPaper>
        </Grid>
      </Grid>

      {/* Success/Error Snackbars */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess("")}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert onClose={() => setSuccess("")} severity="success">
          {success}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError("")}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert onClose={() => setError("")} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EnhancedFormBuilder;
