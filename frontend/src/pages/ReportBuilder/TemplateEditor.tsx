import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  IconButton,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Divider,
  Chip,
} from '@mui/material';
import {
  Preview as PreviewIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { fetchTemplateContent, generateLivePreview } from '../../services/api';

interface TemplateEditorProps {
  templateName: string;
  data: Record<string, string>;
  onDataChange: (data: Record<string, string>) => void;
  onGenerate: () => void;
  isGenerating: boolean;
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
      id={`template-tabpanel-${index}`}
      aria-labelledby={`template-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function TemplateEditor({
  templateName,
  data,
  onDataChange,
  onGenerate,
  isGenerating,
}: TemplateEditorProps) {
  const [tabValue, setTabValue] = useState(0);
  const [templateContent, setTemplateContent] = useState<any>(null);
  const [livePreview, setLivePreview] = useState<string | null>(null);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [editedData, setEditedData] = useState<Record<string, string>>(data);

  // Load template content when component mounts
  useEffect(() => {
    const loadTemplateContent = async () => {
      if (!templateName) return;
      
      setIsLoadingContent(true);
      try {
        const content = await fetchTemplateContent(templateName);
        setTemplateContent(content);
      } catch (error) {
        console.error('Failed to load template content:', error);
      } finally {
        setIsLoadingContent(false);
      }
    };

    loadTemplateContent();
  }, [templateName]);

  // Update edited data when data prop changes
  useEffect(() => {
    setEditedData(data);
  }, [data]);

  // Generate live preview
  const handleGeneratePreview = async () => {
    if (!templateName || !editedData) return;

    setIsGeneratingPreview(true);
    setPreviewError(null);

    try {
      const preview = await generateLivePreview(templateName, editedData);
      setLivePreview(preview.preview);
    } catch (error: any) {
      setPreviewError(error?.message || 'Failed to generate preview');
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  // Handle data field changes
  const handleDataChange = (key: string, value: string) => {
    const newData = { ...editedData, [key]: value };
    setEditedData(newData);
    onDataChange(newData);
  };

  if (isLoadingContent) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2">
          Template Editor
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleGeneratePreview}
            disabled={isGeneratingPreview}
            sx={{ mr: 1 }}
          >
            {isGeneratingPreview ? 'Generating...' : 'Refresh Preview'}
          </Button>
        </Box>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Data Fields" />
          <Tab label="Live Preview" />
          <Tab label="Template Content" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Fill Template Data
          </Typography>
          <Grid container spacing={2}>
            {Object.keys(editedData).map((key) => (
              <Grid item xs={12} sm={6} key={key}>
                <TextField
                  fullWidth
                  label={key}
                  value={editedData[key] || ''}
                  onChange={(e) => handleDataChange(key, e.target.value)}
                  variant="outlined"
                  size="small"
                />
              </Grid>
            ))}
          </Grid>
          <Box mt={3}>
            <Button
              variant="contained"
              color="primary"
              onClick={onGenerate}
              disabled={isGenerating}
              startIcon={isGenerating ? <CircularProgress size={20} /> : <DownloadIcon />}
            >
              {isGenerating ? 'Generating Report...' : 'Generate Report'}
            </Button>
          </Box>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Live Preview
            </Typography>
            <Button
              variant="outlined"
              startIcon={<PreviewIcon />}
              onClick={handleGeneratePreview}
              disabled={isGeneratingPreview}
            >
              {isGeneratingPreview ? 'Generating...' : 'Generate Preview'}
            </Button>
          </Box>
          
          {previewError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {previewError}
            </Alert>
          )}
          
          {livePreview ? (
            <Paper sx={{ p: 2, bgcolor: '#f8fafc' }}>
              <iframe
                src={livePreview}
                width="100%"
                height="600px"
                style={{ border: '1px solid #e0e7ef', borderRadius: '4px' }}
                title="Template Preview"
              />
            </Paper>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center', bgcolor: '#f8fafc' }}>
              <Typography variant="body1" color="text.secondary">
                Click "Generate Preview" to see a live preview of your filled template
              </Typography>
            </Paper>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Template Structure
          </Typography>
          {templateContent && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Placeholders found in template:
              </Typography>
              <Box sx={{ mb: 2 }}>
                {templateContent.placeholders.map((placeholder: string) => (
                  <Chip
                    key={placeholder}
                    label={placeholder}
                    variant="outlined"
                    size="small"
                    sx={{ mr: 1, mb: 1 }}
                  />
                ))}
              </Box>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>
                Template Content:
              </Typography>
              <Paper sx={{ p: 2, bgcolor: '#f8fafc', maxHeight: '400px', overflow: 'auto' }}>
                {templateContent.content.map((item: any, index: number) => (
                  <Box key={index} sx={{ mb: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {item.style}
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {item.text}
                    </Typography>
                  </Box>
                ))}
              </Paper>
            </Box>
          )}
        </TabPanel>
      </Paper>
    </Box>
  );
} 