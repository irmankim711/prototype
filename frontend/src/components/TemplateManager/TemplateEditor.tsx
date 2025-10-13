import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Alert,
  Snackbar
} from '@mui/material';
import { Save, Cancel, Preview, Download } from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';

interface Template {
  id: string;
  name: string;
  type: 'latex' | 'jinja2' | 'docx';
  description: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

interface TemplateEditorProps {
  template?: Template;
  onSave: (template: Template) => void;
  onCancel: () => void;
}

const TemplateEditor: React.FC<TemplateEditorProps> = ({
  template,
  onSave,
  onCancel
}) => {
  const theme = useTheme();
  const [formData, setFormData] = useState<Partial<Template>>({
    name: '',
    type: 'jinja2',
    description: '',
    content: ''
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    if (template) {
      setFormData(template);
    }
  }, [template]);

  const handleInputChange = (field: keyof Template, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name?.trim()) {
      newErrors.name = 'Template name is required';
    }

    if (!formData.description?.trim()) {
      newErrors.description = 'Template description is required';
    }

    if (!formData.content?.trim()) {
      newErrors.content = 'Template content is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validateForm()) return;

    const templateData: Template = {
      id: template?.id || Date.now().toString(),
      name: formData.name!,
      type: formData.type!,
      description: formData.description!,
      content: formData.content!,
      createdAt: template?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    onSave(templateData);
    setShowSuccess(true);
  };

  const handlePreview = () => {
    // Open template preview in new window/tab
    const previewWindow = window.open('', '_blank');
    if (previewWindow) {
      previewWindow.document.write(`
        <html>
          <head>
            <title>Template Preview - ${formData.name}</title>
            <style>
              body { font-family: monospace; padding: 20px; }
              pre { background: #f5f5f5; padding: 15px; border-radius: 5px; }
            </style>
          </head>
          <body>
            <h2>${formData.name}</h2>
            <p><strong>Type:</strong> ${formData.type}</p>
            <p><strong>Description:</strong> ${formData.description}</p>
            <h3>Content Preview:</h3>
            <pre>${formData.content}</pre>
          </body>
        </html>
      `);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([formData.content || ''], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${formData.name || 'template'}.${formData.type}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h2">
            {template ? 'Edit Template' : 'Create New Template'}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Preview Template">
              <IconButton onClick={handlePreview} color="primary">
                <Preview />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download Template">
              <IconButton onClick={handleDownload} color="success">
                <Download />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Template Name"
              value={formData.name || ''}
              onChange={(e) => handleInputChange('name', e.target.value)}
              error={!!errors.name}
              helperText={errors.name}
              required
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth required>
              <InputLabel>Template Type</InputLabel>
              <Select
                value={formData.type || 'jinja2'}
                label="Template Type"
                onChange={(e) => handleInputChange('type', e.target.value)}
              >
                <MenuItem value="jinja2">Jinja2</MenuItem>
                <MenuItem value="latex">LaTeX</MenuItem>
                <MenuItem value="docx">DOCX</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Description"
              value={formData.description || ''}
              onChange={(e) => handleInputChange('description', e.target.value)}
              error={!!errors.description}
              helperText={errors.description}
              multiline
              rows={2}
              required
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Template Content"
              value={formData.content || ''}
              onChange={(e) => handleInputChange('content', e.target.value)}
              error={!!errors.content}
              helperText={errors.content}
              multiline
              rows={20}
              required
              sx={{
                '& .MuiInputBase-root': {
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                }
              }}
            />
          </Grid>
        </Grid>

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 3 }}>
          <Button
            variant="outlined"
            startIcon={<Cancel />}
            onClick={onCancel}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSave}
          >
            {template ? 'Update Template' : 'Create Template'}
          </Button>
        </Box>
      </Paper>

      <Snackbar
        open={showSuccess}
        autoHideDuration={3000}
        onClose={() => setShowSuccess(false)}
      >
        <Alert onClose={() => setShowSuccess(false)} severity="success">
          Template {template ? 'updated' : 'created'} successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default TemplateEditor;
