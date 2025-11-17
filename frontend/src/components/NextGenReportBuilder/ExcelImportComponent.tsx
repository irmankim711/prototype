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
  CheckCircle,
  Error as ErrorIcon,
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

  // Load templates on component mount and refresh periodically
  React.useEffect(() => {
    loadTemplates();
    
    // Refresh templates every 30 seconds to pick up newly uploaded ones
    const refreshInterval = setInterval(() => {
      loadTemplates();
    }, 30000);
    
    return () => clearInterval(refreshInterval);
  }, []);

  // Ensure uploadedFiles is always a valid array
  React.useEffect(() => {
    if (!Array.isArray(uploadedFiles)) {
      setUploadedFiles([]);
    }
  }, [uploadedFiles]);

  const loadTemplates = async () => {
    try {
      // Clear cache to get fresh templates including newly uploaded ones
      nextGenReportService.clearCache('reportTemplates');
      
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
      
      // Sort templates: file-based templates first, then others
      const sortedTemplates = uniqueTemplates.sort((a, b) => {
        const aHasFile = !!(a.file_path || a.filePath);
        const bHasFile = !!(b.file_path || b.filePath);
        if (aHasFile && !bHasFile) return -1;
        if (!aHasFile && bHasFile) return 1;
        return (a.name || '').localeCompare(b.name || '');
      });
      
      setTemplates(sortedTemplates);
      console.log(`✅ Loaded ${sortedTemplates.length} templates (${sortedTemplates.filter(t => t.file_path || t.filePath).length} with files)`);
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

      // Convert template ID to string to ensure proper API handling
      const templateId = String(selectedTemplate);
      console.log('🎯 Generating report with template ID:', templateId);

      console.log('🚀 Starting report generation...');
      console.log('📊 Parameters:', {
        filePath: selectedDataSource.filePath,
        templateId: templateId,
        reportTitle: reportTitle
      });

      // ✅ Define charts to include in the report
      const charts = [
        {
          type: 'bar',
          title: 'PENILAIAN KESELURUHAN',
          sheetName: '04- LAPORAN PENILAIAN PROGRAM',  // Read from this specific sheet
          groupBy: 'KESELURUHAN KURSUS',  // Group by "KESELURUHAN KURSUS" column
          orientation: 'horizontal',  // Horizontal bar chart like the example
          showPercentage: true,  // Show percentage labels
          categories: ['TIDAK MEMUASKAN', 'KURANG MEMUASKAN', 'MEMUASKAN', 'BAIK', 'CEMERLANG'],  // Order from bottom to top
          color: '#ff8c42'  // Orange color like the example
        }
      ];

      const report = await nextGenReportService.generateReportFromExcel(
        selectedDataSource.filePath,
        templateId,
        reportTitle,
        charts  // Pass charts configuration
      );
      
      console.log('✅ Report generation completed successfully');
      console.log('📄 Report response:', report);
      console.log('📄 Report response keys:', Object.keys(report || {}));
      
      // Validate report response has an ID (0 is valid)
      const reportId = (report?.id ?? report?.reportId ?? report?.report_id ?? report?.report?.id);
      if (reportId === undefined || reportId === null) {
        console.error('❌ Report generated but missing ID in response');
        console.error('❌ Full report object:', JSON.stringify(report, null, 2));
        throw new Error('Report generated but missing ID - please check console for details');
      }
      
      console.log('✅ Report ID extracted:', reportId);
      
      // Call callback with report data
      if (onReportGenerated) {
        console.log('📤 Calling onReportGenerated callback...');
        onReportGenerated(report);
        console.log('✅ Callback executed');
      } else {
        console.warn('⚠️ No onReportGenerated callback provided');
      }
      
      // Close dialog and reset form
      setShowReportDialog(false);
      setSelectedTemplate('');
      setReportTitle('');
      
      console.log('✅ Report generation flow completed');
    } catch (error: any) {
      // Handle report generation error
      const errorMessage = error.message || 'Failed to generate report';
      console.error('❌ Report generation error:', errorMessage);
      console.error('❌ Error details:', error);
      console.error('❌ Error response:', error.response?.data);
      
      // Show user-friendly error message
      alert(`Failed to generate report: ${errorMessage}\n\nPlease check the browser console for more details.`);
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
                {templates.map((template, index) => {
                  const hasFile = !!(template.file_path || template.filePath);
                  const templateType = template.template_type || template.type || 'unknown';
                  
                  return (
                    <MenuItem
                      key={template.id || template.name || `template-${index}`}
                      value={template.id || template.name}
                    >
                      <Box sx={{ py: 1 }}>
                        <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                          <Typography variant="body1" fontWeight="medium">
                            {template.name}
                          </Typography>
                          {hasFile && (
                            <Chip 
                              label="📄 File" 
                              size="small" 
                              color="success" 
                              sx={{ height: 16, fontSize: '0.65rem' }}
                            />
                          )}
                          {(templateType === 'docx' || templateType === 'DOCX') && (
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
                          {template.description || 'No description'}
                        </Typography>
                        {hasFile && (
                          <Typography variant="caption" color="info.main" display="block" mt={0.5}>
                            📎 File-based template
                          </Typography>
                        )}
                        {template.usageInstructions && (
                          <Typography variant="caption" color="info.main" display="block" mt={0.5}>
                            💡 {template.usageInstructions}
                          </Typography>
                        )}
                      </Box>
                    </MenuItem>
                  );
                })}
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
