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

  // Auto-generate preview when data changes (with debounce)
  useEffect(() => {
    if (editedData && Object.keys(editedData).length > 0) {
      const timer = setTimeout(() => {
        handleGeneratePreview();
      }, 1000); // Wait 1 second after data changes
      
      return () => clearTimeout(timer);
    }
  }, [editedData]);

  // Generate live preview
  const handleGeneratePreview = async () => {
    if (!templateName || !editedData) return;

    setIsGeneratingPreview(true);
    setPreviewError(null);

    try {
      console.log('Generating preview with data:', editedData);
      const preview = await generateLivePreview(templateName, editedData);
      console.log('Preview generated:', preview);
      setLivePreview(preview.preview);
    } catch (error: any) {
      console.error('Preview generation error:', error);
      setPreviewError(error?.message || 'Failed to generate preview. Please check your data and try again.');
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

  // Download original template
  const handleDownloadTemplate = () => {
    const link = document.createElement('a');
    link.href = `/mvp/templates/${templateName}/download`;
    link.download = templateName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
          <Tab label="Original Template" />
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
              startIcon={isGeneratingPreview ? <CircularProgress size={20} /> : <PreviewIcon />}
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
          
          {livePreview && !isGeneratingPreview && !previewError && (
            <Alert severity="success" sx={{ mb: 2 }}>
              Preview generated successfully! You can see how your report will look below.
            </Alert>
          )}
          
          {isGeneratingPreview && (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
              <Box textAlign="center">
                <CircularProgress size={40} sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  Generating preview...
                </Typography>
              </Box>
            </Box>
          )}
          
          {livePreview && !isGeneratingPreview ? (
            <Paper sx={{ p: 2, bgcolor: '#f8fafc' }}>
              <iframe
                src={livePreview}
                width="100%"
                height="600px"
                style={{ border: '1px solid #e0e7ef', borderRadius: '4px' }}
                title="Template Preview"
              />
            </Paper>
          ) : !isGeneratingPreview ? (
            <Paper sx={{ p: 4, textAlign: 'center', bgcolor: '#f8fafc' }}>
              <Typography variant="body1" color="text.secondary">
                Click "Generate Preview" to see a live preview of your filled template
              </Typography>
            </Paper>
          ) : null}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Original Template Preview
            </Typography>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
              size="small"
            >
              Download Original
            </Button>
          </Box>
          <Alert severity="info" sx={{ mb: 2 }}>
            This shows how your template looks before any data is filled in. The placeholders are shown as they appear in the original document.
          </Alert>
          <Paper sx={{ p: 2, bgcolor: '#f8fafc', minHeight: '400px' }}>
            {templateContent ? (
              <Box>
                {templateContent.content.map((item: any, index: number) => (
                  <Box key={index} sx={{ mb: 2 }}>
                    {item.type === 'paragraph' && (
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          whiteSpace: 'pre-wrap',
                          fontWeight: item.formatting?.bold ? 'bold' : 'normal',
                          fontStyle: item.formatting?.italic ? 'italic' : 'normal',
                          fontSize: item.formatting?.font_size ? `${item.formatting.font_size}px` : 'inherit',
                          textAlign: item.formatting?.alignment === 1 ? 'center' : 
                                   item.formatting?.alignment === 2 ? 'right' : 'left'
                        }}
                      >
                        {item.text}
                      </Typography>
                    )}
                    {item.type === 'table' && (
                      <Box sx={{ mt: 2, mb: 2 }}>
                        <table style={{ 
                          borderCollapse: 'collapse', 
                          width: '100%',
                          border: '1px solid #ccc'
                        }}>
                          <tbody>
                            {item.rows.map((row: any[], rowIndex: number) => (
                              <tr key={rowIndex}>
                                {row.map((cell: any, cellIndex: number) => (
                                  <td key={cellIndex} style={{
                                    border: '1px solid #ccc',
                                    padding: '8px',
                                    fontWeight: cell.formatting?.bold ? 'bold' : 'normal',
                                    fontStyle: cell.formatting?.italic ? 'italic' : 'normal',
                                    fontSize: cell.formatting?.font_size ? `${cell.formatting.font_size}px` : 'inherit'
                                  }}>
                                    {cell.text}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </Box>
                    )}
                  </Box>
                ))}
              </Box>
            ) : (
              <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
                <Typography variant="body1" color="text.secondary">
                  Loading template preview...
                </Typography>
              </Box>
            )}
          </Paper>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Template Content
          </Typography>
          {templateContent && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Template Information:
              </Typography>
              <Paper sx={{ p: 2, mb: 2, bgcolor: '#f8fafc' }}>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Filename</Typography>
                    <Typography variant="body2">{templateContent.template_info?.filename}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Paragraphs</Typography>
                    <Typography variant="body2">{templateContent.template_info?.total_paragraphs}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Tables</Typography>
                    <Typography variant="body2">{templateContent.template_info?.total_tables}</Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="caption" color="text.secondary">Placeholders</Typography>
                    <Typography variant="body2">{templateContent.template_info?.total_placeholders}</Typography>
                  </Grid>
                </Grid>
              </Paper>
              
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
                Template Content Structure:
              </Typography>
              <Paper sx={{ p: 2, bgcolor: '#f8fafc', maxHeight: '400px', overflow: 'auto' }}>
                {templateContent.content.map((item: any, index: number) => (
                  <Box key={index} sx={{ mb: 2, p: 1, border: '1px solid #e0e7ef', borderRadius: 1 }}>
                    {item.type === 'paragraph' && (
                      <Box>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Paragraph - Style: {item.style}
                          {item.formatting?.font_size && ` | Font: ${item.formatting.font_size}pt`}
                          {item.formatting?.bold && ' | Bold'}
                          {item.formatting?.italic && ' | Italic'}
                        </Typography>
                        <Typography variant="body2" sx={{ 
                          whiteSpace: 'pre-wrap',
                          fontWeight: item.formatting?.bold ? 'bold' : 'normal',
                          fontStyle: item.formatting?.italic ? 'italic' : 'normal',
                          fontSize: item.formatting?.font_size ? `${item.formatting.font_size}px` : 'inherit'
                        }}>
                          {item.text}
                        </Typography>
                      </Box>
                    )}
                    {item.type === 'table' && (
                      <Box>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Table {item.index + 1} - {item.rows.length} rows
                        </Typography>
                        <Box sx={{ mt: 1, overflowX: 'auto' }}>
                          <table style={{ 
                            borderCollapse: 'collapse', 
                            width: '100%',
                            fontSize: '12px'
                          }}>
                            <tbody>
                              {item.rows.map((row: any[], rowIndex: number) => (
                                <tr key={rowIndex}>
                                  {row.map((cell: any, cellIndex: number) => (
                                    <td key={cellIndex} style={{
                                      border: '1px solid #ccc',
                                      padding: '4px 8px',
                                      fontWeight: cell.formatting?.bold ? 'bold' : 'normal',
                                      fontStyle: cell.formatting?.italic ? 'italic' : 'normal',
                                      fontSize: cell.formatting?.font_size ? `${cell.formatting.font_size}px` : 'inherit'
                                    }}>
                                      {cell.text}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </Box>
                      </Box>
                    )}
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