/**
 * Excel to DOCX Converter Component
 * Direct conversion from Excel files to editable DOCX reports
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
} from '@mui/material';
import {
  CloudUpload,
  Description as DocxIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { reportService } from '../services/reportService';
import DocumentPreview from './DocumentPreview';
import ReportSuccessModal from './ReportSuccessModal';

interface ExcelToDocxConverterProps {
  onReportGenerated?: (report: any) => void;
  onEditReport?: (reportId: string) => void;
}

const ExcelToDocxConverter: React.FC<ExcelToDocxConverterProps> = ({
  onReportGenerated,
  onEditReport,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [reportTitle, setReportTitle] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('default');
  const [generatedReport, setGeneratedReport] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [successModalOpen, setSuccessModalOpen] = useState(false);

  const queryClient = useQueryClient();

  // Load available templates
  const { data: templatesData } = useQuery({
    queryKey: ['docx-templates'],
    queryFn: () => reportService.getDocxTemplates(),
  });

  // Convert Excel to DOCX mutation
  const convertMutation = useMutation({
    mutationFn: ({ file, options }: { file: File; options: any }) =>
      reportService.convertExcelToDocx(file, options),
    onSuccess: (report) => {
      setGeneratedReport(report);
      setSuccess(`Successfully converted ${selectedFile?.name} to DOCX report!`);
      onReportGenerated?.(report);
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      
      // Auto-generate title from filename if not provided
      if (!reportTitle && selectedFile) {
        setReportTitle(`Report from ${selectedFile.name}`);
      }
      
      // Show success modal with clear next steps
      setSuccessModalOpen(true);
    },
    onError: (error: any) => {
      setError(`Conversion failed: ${error.response?.data?.error || error.message}`);
    },
  });

  // Download report mutation
  const downloadMutation = useMutation({
    mutationFn: (reportId: string) => reportService.downloadReport(reportId, 'docx'),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${reportTitle || 'report'}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setSuccess('DOCX file downloaded successfully!');
    },
    onError: (error: any) => {
      setError(`Download failed: ${error.message}`);
    },
  });

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
        setError(null);
        
        // Auto-generate title from filename
        const filename = acceptedFiles[0].name;
        const nameWithoutExt = filename.replace(/\.[^/.]+$/, '');
        setReportTitle(`Report from ${nameWithoutExt}`);
      }
    },
  });

  const handleConvert = () => {
    if (!selectedFile) {
      setError('Please select an Excel file first');
      return;
    }

    convertMutation.mutate({
      file: selectedFile,
      options: {
        title: reportTitle || `Report from ${selectedFile.name}`,
        template: selectedTemplate,
      },
    });
  };

  const handleDownload = () => {
    if (generatedReport?.report_id) {
      downloadMutation.mutate(generatedReport.report_id.toString());
    }
  };

  const handleEdit = () => {
    if (generatedReport?.report_id) {
      onEditReport?.(generatedReport.report_id.toString());
    }
  };

  const handlePreview = () => {
    setPreviewOpen(true);
  };

  const getStatusColor = () => {
    if (convertMutation.isPending) return 'info';
    if (error) return 'error';
    if (success && generatedReport) return 'success';
    return 'default';
  };

  const templates = templatesData?.templates || [];

  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Excel to DOCX Converter
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          Upload an Excel file to automatically generate a professional DOCX report with charts, tables, and analysis.
        </Typography>

        {/* File Upload Section */}
        <Box
          {...getRootProps()}
          sx={{
            border: 2,
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            borderStyle: 'dashed',
            borderRadius: 2,
            p: 3,
            textAlign: 'center',
            cursor: 'pointer',
            mb: 3,
            bgcolor: isDragActive ? 'primary.light' : 'background.paper',
            transition: 'all 0.3s ease',
          }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
          {selectedFile ? (
            <Box>
              <Typography variant="body1" color="primary">
                ✓ {selectedFile.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </Typography>
            </Box>
          ) : (
            <Box>
              <Typography variant="body1" gutterBottom>
                Drag & drop an Excel file here, or click to browse
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Supports .xlsx and .xls files up to 50MB
              </Typography>
            </Box>
          )}
        </Box>

        {/* Configuration Section */}
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Report Title"
            value={reportTitle}
            onChange={(e) => setReportTitle(e.target.value)}
            placeholder="Enter a title for your report"
            sx={{ mb: 2 }}
          />

          <FormControl fullWidth>
            <InputLabel>Template</InputLabel>
            <Select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              label="Template"
            >
              {templates.map((template: any) => (
                <MenuItem key={template.id} value={template.id}>
                  <Box>
                    <Typography variant="body2">{template.name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {template.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Button
            variant="contained"
            onClick={handleConvert}
            disabled={!selectedFile || convertMutation.isPending}
            startIcon={convertMutation.isPending ? <CircularProgress size={20} /> : <DocxIcon />}
            fullWidth
          >
            {convertMutation.isPending ? 'Converting...' : 'Convert to DOCX'}
          </Button>
        </Box>

        {/* Status Messages */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {/* Generated Report Section */}
        {generatedReport && (
          <Box>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Generated Report
            </Typography>
            
            <List>
              <ListItem>
                <ListItemText
                  primary={generatedReport.title}
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        Report ID: {generatedReport.report_id}
                      </Typography>
                      <Typography variant="caption" display="block">
                        Size: {(generatedReport.file_size / 1024).toFixed(1)} KB
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip
                          icon={<CheckCircle />}
                          label="Ready"
                          color="success"
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        <Chip
                          label={generatedReport.metadata?.template_used || 'default'}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <IconButton
                      onClick={handlePreview}
                      title="Preview Document"
                      color="primary"
                    >
                      <ViewIcon />
                    </IconButton>
                    <IconButton
                      onClick={handleDownload}
                      disabled={downloadMutation.isPending}
                      title="Download DOCX"
                    >
                      {downloadMutation.isPending ? (
                        <CircularProgress size={20} />
                      ) : (
                        <DownloadIcon />
                      )}
                    </IconButton>
                    <IconButton onClick={handleEdit} title="Edit Report">
                      <EditIcon />
                    </IconButton>
                  </Box>
                </ListItemSecondaryAction>
              </ListItem>
            </List>
          </Box>
        )}

        {/* Document Preview Dialog */}
        {generatedReport && (
          <DocumentPreview
            open={previewOpen}
            onClose={() => setPreviewOpen(false)}
            reportId={generatedReport.report_id}
            title={generatedReport.title}
            onEdit={handleEdit}
            onDownload={handleDownload}
          />
        )}

        {/* Success Modal with Clear Next Steps */}
        <ReportSuccessModal
          open={successModalOpen}
          onClose={() => setSuccessModalOpen(false)}
          report={generatedReport}
          onView={handlePreview}
          onEdit={handleEdit}
          onDownload={handleDownload}
        />
      </CardContent>
    </Card>
  );
};

export default ExcelToDocxConverter;