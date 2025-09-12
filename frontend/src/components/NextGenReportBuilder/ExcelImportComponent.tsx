/**
 * Excel Import Component for Next-Gen Report Builder
 * Allows users to upload Excel files and generate automated reports
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
  LinearProgress,
  Chip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
} from '@mui/material';
import {
  CloudUpload,
  TableChart,
  AutoAwesome,
  Download,
  Visibility,
  CheckCircle,
  Error as ErrorIcon,
  FileUpload,
  Description,
  Assignment,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { nextGenReportService } from '../../services/nextGenReportService';

interface ExcelImportComponentProps {
  onDataSourceCreated?: (dataSource: any) => void;
  onReportGenerated?: (report: any) => void;
}

interface UploadedFile {
  file: File;
  dataSource?: any;
  status: 'uploading' | 'processed' | 'error';
  error?: string;
}

const ExcelImportComponent: React.FC<ExcelImportComponentProps> = ({
  onDataSourceCreated,
  onReportGenerated,
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');

  // Debug logging for template selection
  React.useEffect(() => {
    console.log('📋 Templates loaded:', templates);
    console.log('🎯 Selected template:', selectedTemplate);
    
    // If selected template doesn't exist in templates array, reset it
    if (selectedTemplate && templates.length > 0) {
      const templateExists = templates.some(template => 
        template.id === selectedTemplate || template.name === selectedTemplate
      );
      if (!templateExists) {
        console.warn(`⚠️ Selected template '${selectedTemplate}' not found in templates. Resetting to empty.`);
        setSelectedTemplate('');
      }
    }
  }, [templates, selectedTemplate]);
  const [reportTitle, setReportTitle] = useState('');
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [selectedDataSource, setSelectedDataSource] = useState<any>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  // Load templates on component mount
  React.useEffect(() => {
    loadTemplates();
  }, []);

  // Ensure uploadedFiles is always a valid array
  React.useEffect(() => {
    if (!Array.isArray(uploadedFiles)) {
      setUploadedFiles([]);
    }
  }, [uploadedFiles]);

  const loadTemplates = async () => {
    try {
      const templatesList = await nextGenReportService.getReportTemplates();
      
      // Ensure unique templates by ID or name to prevent React key conflicts
      const uniqueTemplates = templatesList.filter((template, index, array) => {
        const identifier = template.id || template.name;
        return array.findIndex(t => (t.id || t.name) === identifier) === index;
      });
      
      // Log template loading for debugging
      if (templatesList.length !== uniqueTemplates.length) {
        console.warn(`Filtered out ${templatesList.length - uniqueTemplates.length} duplicate templates`);
      }
      
      setTemplates(uniqueTemplates);
    } catch (error) {
      // Templates loading failure is not critical, continue without them
      console.error('Failed to load templates:', error);
      setTemplates([]);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!Array.isArray(acceptedFiles) || acceptedFiles.length === 0) {
      return;
    }

    const excelFiles = acceptedFiles.filter(file => 
      file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
    );

    if (excelFiles.length === 0) {
      return;
    }

    setIsUploading(true);

    for (const file of excelFiles) {
      try {
        const uploadResult = await nextGenReportService.uploadExcelFile(file);
        
        if (uploadResult.success && uploadResult.dataSource) {
          const newFile: UploadedFile = {
            file,
            dataSource: uploadResult.dataSource,
            status: 'processed'
          };
          
          setUploadedFiles(prev => [...prev, newFile]);
          
          if (onDataSourceCreated) {
            onDataSourceCreated(uploadResult.dataSource);
          }
        } else {
          throw new Error('Invalid upload result structure');
        }
      } catch (error: any) {
        const errorMessage = error.message || 'Upload failed';
        const failedFile: UploadedFile = {
          file,
          status: 'error',
          error: errorMessage
        };
        
        setUploadedFiles(prev => [...prev, failedFile]);
      }
    }
    
    setIsUploading(false);
  }, [onDataSourceCreated]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: true,
  });

  const handleGenerateReport = (dataSource: any) => {
    if (!dataSource || !dataSource.name) {
      alert('Invalid data source. Please try uploading the file again.');
      return;
    }
    setSelectedDataSource(dataSource);
    setReportTitle(`Report from ${dataSource.name}`);
    setShowReportDialog(true);
  };

  const generateReport = async () => {
    if (!selectedDataSource || !selectedTemplate) {
      return;
    }

    try {
      setIsGeneratingReport(true);
      
      const report = await nextGenReportService.generateReportFromExcel(
        selectedDataSource.filePath,
        selectedTemplate,
        reportTitle
      );
      
      if (onReportGenerated) {
        onReportGenerated(report);
      }
      
      setShowReportDialog(false);
      setSelectedTemplate('');
      setReportTitle('');
    } catch (error: any) {
      // Handle report generation error
      const errorMessage = error.message || 'Failed to generate report';
      // You could set this to a state variable to show in the UI
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const removeFile = (fileToRemove: UploadedFile) => {
    setUploadedFiles(prev => prev.filter(f => f !== fileToRemove));
  };

  // Filter out any invalid uploaded files to prevent crashes
  const validUploadedFiles = uploadedFiles.filter(f => f && f.file);

  return (
    <Box>
      <Typography variant="h6" fontWeight="semibold" mb={2}>
        Excel Import & Automation
      </Typography>

      {/* Upload Area */}
      <Paper
        {...getRootProps()}
        variant="outlined"
        sx={{
          p: 4,
          mb: 3,
          borderStyle: 'dashed',
          borderWidth: 2,
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          backgroundColor: isDragActive ? 'primary.50' : 'grey.50',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: 'primary.main',
            backgroundColor: 'primary.25',
          },
        }}
      >
        <Box textAlign="center">
          <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" mb={1}>
            {isDragActive ? 'Drop Excel files here' : 'Drag & drop Excel files here'}
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            or click to browse (.xlsx, .xls)
          </Typography>
          <input {...getInputProps()} />
        </Box>
      </Paper>

      {/* Upload Progress */}
      {isUploading && (
        <Box mb={3}>
          <LinearProgress />
          <Typography variant="body2" color="text.secondary" mt={1}>
            Processing Excel files...
          </Typography>
        </Box>
      )}

      {/* Uploaded Files List */}
      {validUploadedFiles.length > 0 && (
        <Paper variant="outlined" sx={{ mb: 3 }}>
          <Box p={2}>
            <Typography variant="h6" fontWeight="semibold" mb={2}>
              Uploaded Files ({validUploadedFiles.length})
            </Typography>
            <List>
              {validUploadedFiles.map((uploadedFile, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemIcon>
                      {uploadedFile.status === 'processed' ? (
                        <CheckCircle color="success" />
                      ) : uploadedFile.status === 'error' ? (
                        <ErrorIcon color="error" />
                      ) : (
                        <TableChart color="primary" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={uploadedFile.file.name}
                      secondary={
                        uploadedFile.status === 'processed' && uploadedFile.dataSource
                          ? `${uploadedFile.dataSource.recordCount || 0} records • ${uploadedFile.dataSource.fields?.length || 0} fields`
                          : uploadedFile.status === 'error'
                          ? uploadedFile.error
                          : 'Processing...'
                      }
                    />
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip
                        label={uploadedFile.status}
                        size="small"
                        color={
                          uploadedFile.status === 'processed' 
                            ? 'success' 
                            : uploadedFile.status === 'error' 
                            ? 'error' 
                            : 'default'
                        }
                      />
                      {uploadedFile.status === 'processed' && uploadedFile.dataSource && (
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<AutoAwesome />}
                          onClick={() => handleGenerateReport(uploadedFile.dataSource)}
                        >
                          Generate Report
                        </Button>
                      )}
                    </Box>
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => removeFile(uploadedFile)}
                        size="small"
                      >
                        ✕
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < validUploadedFiles.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </Box>
        </Paper>
      )}

      {/* Quick Actions */}
      {validUploadedFiles.some(f => f.status === 'processed') && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Next Steps:</strong> Click "Generate Report" to create automated reports from your Excel data using predefined templates.
          </Typography>
        </Alert>
      )}

      {/* Report Generation Dialog */}
      <Dialog open={showReportDialog} onClose={() => setShowReportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Assignment />
            Generate Automated Report
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={3} pt={1}>
            <TextField
              label="Report Title"
              fullWidth
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              placeholder="Enter a title for your report"
            />
            
            <FormControl fullWidth>
              <InputLabel>Select Report Template</InputLabel>
              <Select
                value={selectedTemplate || ''}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                label="Select Report Template"
              >
                {templates.map((template, index) => (
                  <MenuItem 
                    key={template.id || template.name || `template-${index}`} 
                    value={template.name || template.id}
                  >
                    <Box sx={{ py: 1 }}>
                      <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                        <Typography variant="body1" fontWeight="medium">
                          {template.name}
                        </Typography>
                        {template.type === 'docx' && (
                          <Chip 
                            label="DOCX" 
                            size="small" 
                            color="primary" 
                            sx={{ height: 16, fontSize: '0.65rem' }}
                          />
                        )}
                        {template.isDefault && (
                          <Chip 
                            label="Recommended" 
                            size="small" 
                            color="success" 
                            sx={{ height: 16, fontSize: '0.65rem' }}
                          />
                        )}
                      </Box>
                      <Typography variant="caption" color="text.secondary" display="block">
                        {template.description}
                      </Typography>
                      {template.usageInstructions && (
                        <Typography variant="caption" color="info.main" display="block" mt={0.5}>
                          💡 {template.usageInstructions}
                        </Typography>
                      )}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {selectedTemplate && (
              <Paper variant="outlined" sx={{ p: 2, backgroundColor: 'grey.50' }}>
                <Typography variant="subtitle2" mb={1} color="primary">
                  Selected Template Details:
                </Typography>
                {(() => {
                  const template = templates.find(t => t.id === selectedTemplate);
                  return template ? (
                    <Box>
                      <Typography variant="body2" mb={1}>
                        <strong>Name:</strong> {template.name}
                      </Typography>
                      <Typography variant="body2" mb={1}>
                        <strong>Type:</strong> {template.type?.toUpperCase()} 
                        {template.category && ` (${template.category})`}
                      </Typography>
                      <Typography variant="body2" mb={1}>
                        <strong>Supports:</strong> {template.supports?.join(', ') || 'Standard formatting'}
                      </Typography>
                      {template.usageInstructions && (
                        <Typography variant="body2" color="text.secondary" fontStyle="italic">
                          {template.usageInstructions}
                        </Typography>
                      )}
                    </Box>
                  ) : null;
                })()}
              </Paper>
            )}

            {selectedDataSource && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" mb={1}>Data Source Details:</Typography>
                <Typography variant="body2">
                  <strong>File:</strong> {selectedDataSource.name || 'Unknown File'}
                </Typography>
                <Typography variant="body2">
                  <strong>Records:</strong> {selectedDataSource.recordCount || 'Unknown'}
                </Typography>
                <Typography variant="body2">
                  <strong>Fields:</strong> {selectedDataSource.fields?.length || 0}
                </Typography>
              </Paper>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowReportDialog(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={generateReport}
            disabled={!selectedTemplate || !reportTitle || isGeneratingReport}
            startIcon={isGeneratingReport ? undefined : <AutoAwesome />}
          >
            {isGeneratingReport ? 'Generating...' : 'Generate Report'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExcelImportComponent;
