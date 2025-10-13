import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Excel Uploader Component
 * Drag-and-drop Excel file upload with validation and preview
 */

import { useState, useCallback } from "react";

import { Box, Paper, Typography, Button, LinearProgress, Alert, Chip, List, ListItem, ListItemIcon, ListItemText, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, FormControl, InputLabel, Select, MenuItem, TextField } from "@mui/material";

import { CloudUpload, InsertDriveFile, CheckCircle, Error, Delete, Visibility, PictureAsPdf, Description } from "@mui/icons-material";

import { useDropzone } from "react-dropzone";

interface UploadedFile {
  file_id: string;
  filename: string;
  size: number;
  sheets: string[];
  total_rows: number;
  columns: string[];
  preview_data: any[];
}

interface GeneratedReport {
  report_id: number;
  title: string;
  formats: {
    [key: string]: {
      url: string;
      filename: string;
      size: number;
      method?: string;
    };
  };
  metadata: any;
}

interface ExcelUploaderProps {
  onFileUploaded: (fileData: UploadedFile) => void;
  onFileRemoved?: (fileId: string) => void;
  onReportGenerated?: (report: GeneratedReport) => void;
  maxFiles?: number;
  maxSize?: number; // in bytes
  uploadedFiles?: UploadedFile[];
  disabled?: boolean;
  enableReportGeneration?: boolean;
}

const ExcelUploader: React.FC<ExcelUploaderProps> = ({
  onFileUploaded,
  onFileRemoved,
  onReportGenerated,
  maxFiles = 1,
  maxSize = 10 * 1024 * 1024, // 10MB
  uploadedFiles = [],
  disabled = false,
  enableReportGeneration = true,
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Report generation states
  const [generatingReport, setGeneratingReport] = useState(false);
  const [reportProgress, setReportProgress] = useState(0);
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<UploadedFile | null>(null);
  const [reportTitle, setReportTitle] = useState('');
  const [reportFormats, setReportFormats] = useState<string[]>(['pdf']);
  const [reportTemplate, setReportTemplate] = useState('excel_analysis');
  const [generatedReports, setGeneratedReports] = useState<GeneratedReport[]>([]);

const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (disabled) return;

setError(null);
    
    // Validate file count
    if (uploadedFiles.length + acceptedFiles.length > maxFiles) {
      setError(`Maximum ${maxFiles} file(s) allowed`);
      
return;
    }

    for (const file of acceptedFiles) {
      // Validate file size
      if (file.size > maxSize) {
        setError(`File size must be less than ${Math.round(maxSize / 1024 / 1024)}MB`);
        
continue;
      }

      // Validate file type
      const validTypes = [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
      ];

if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls)$/i)) {
        setError('Only Excel files (.xlsx, .xls) are allowed');
        
continue;
      }

      await uploadFile(file);
    }
  }, [uploadedFiles.length, maxFiles, maxSize, disabled]);

const uploadFile = async (file: File) => {
    setUploading(true);
    
setUploadProgress(0);

try {
      const formData = new FormData();
      
formData.append('file', file);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 100);

const response = await fetch('/api/v1/reports/excel-upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('accessToken')}`,
        },
        body: formData,
      });

clearInterval(progressInterval);
      
setUploadProgress(100);

if (!response.ok) {
        const errorData = await response.json();
        
throw Error(errorData.error || 'Upload failed');
      }

      const result = await response.json();

if (result.success) {
        const fileData: UploadedFile = {
          file_id: result.file_id,
          filename: result.filename,
          size: file.size,
          sheets: result.sheets || [],
          total_rows: result.total_rows || 0,
          columns: result.columns || [],
          preview_data: result.preview_data || [],
        };

onFileUploaded(fileData);
        
setError(null);
      } else {
        throw Error(result.error || 'Upload failed');
      }
    } catch (err: any) {
      console.error('Upload error:', err);
      
setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      
setUploadProgress(0);
    }
  };

const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles,
    maxSize,
    disabled: disabled || uploading,
  });

const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    
const k = 1024;
    
const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    
const i = Math.floor(Math.log(bytes) / Math.log(k));
    
return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

const handleRemoveFile = (fileId: string) => {
    onFileRemoved?.(fileId);
  };

  const handleGenerateReport = (file: UploadedFile) => {
    setSelectedFile(file);
    setReportTitle(`Analysis Report - ${file.filename}`);
    setShowReportDialog(true);
  };

  const generateReport = async () => {
    if (!selectedFile) return;

    setGeneratingReport(true);
    setReportProgress(0);
    setShowReportDialog(false);

    try {
      // Note: In a real implementation, we would need to either:
      // 1. Store the file on the server after upload and reference it by ID
      // 2. Allow the user to re-select the file for report generation
      // For now, we'll show a message about needing to re-upload

      setError('Please re-upload the Excel file to generate a report. This will be improved in the next version.');
      return;

      // The following code shows how it would work if we had the file:
      /*
      const formData = new FormData();
      // formData.append('file', actualFileObject);
      formData.append('title', reportTitle);
      formData.append('formats', reportFormats.join(','));
      formData.append('template', reportTemplate);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setReportProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('/api/excel-to-pdf/upload-and-generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('accessToken')}`,
        },
        body: formData,
      });

      clearInterval(progressInterval);
      setReportProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Report generation failed');
      }

      const result = await response.json();

      if (result.success) {
        const newReport: GeneratedReport = {
          report_id: result.report_id,
          title: result.title,
          formats: result.formats,
          metadata: result.metadata
        };

        setGeneratedReports(prev => [...prev, newReport]);
        onReportGenerated?.(newReport);
        setError(null);
      } else {
        throw new Error(result.error || 'Report generation failed');
      }
      */
    } catch (err: any) {
      console.error('Report generation error:', err);
      setError(err.message || 'Report generation failed');
    } finally {
      setGeneratingReport(false);
      setReportProgress(0);
    }
  };

  const downloadReport = (format: string, reportData: any) => {
    const link = document.createElement('a');
    link.href = reportData.url;
    link.download = reportData.filename;
    link.click();
  };

return (
    <Box>
      {/* Upload Area */}
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: disabled || uploading ? 'not-allowed' : 'pointer',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          transition: 'all 0.2s',
          opacity: disabled ? 0.6 : 1,
          '&:hover': {
            borderColor: disabled || uploading ? 'grey.300' : 'primary.main',
            bgcolor: disabled || uploading ? 'background.paper' : 'action.hover',
          },
        }}
      >
        <input {...getInputProps()} />
        
        <CloudUpload
          sx={{
            fontSize: 48,
            color: isDragActive ? 'primary.main' : 'text.secondary',
            mb: 2,
          }}
        />
        
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop Excel files here' : 'Upload Excel Files'}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Drag and drop Excel files (.xlsx, .xls) here, or click to browse
        </Typography>
        
        <Button
          variant="outlined"
          disabled={disabled || uploading}
          sx={{ mb: 2 }}
        >
          Choose Files
        </Button>
        
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            label={`Max ${maxFiles} file${maxFiles > 1 ? 's' : ''}`}
            size="small"
            variant="outlined"
          />
          <Chip
            label={`Max ${Math.round(maxSize / 1024 / 1024)}MB`}
            size="small"
            variant="outlined"
          />
          <Chip
            label="Excel files only"
            size="small"
            variant="outlined"
          />
        </Box>
      </Paper>

      {/* Upload Progress */}
      {uploading && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Uploading and processing file...
          </Typography>
          <LinearProgress
            variant="determinate"
            value={uploadProgress}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {uploadProgress}% complete
          </Typography>
        </Box>
      )}

      {/* Report Generation Progress */}
      {generatingReport && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Generating report...
          </Typography>
          <LinearProgress
            variant="determinate"
            value={reportProgress}
            sx={{ height: 8, borderRadius: 4, bgcolor: 'primary.light' }}
          />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {reportProgress}% complete
          </Typography>
        </Box>
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Uploaded Files List */}
      {uploadedFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Uploaded Files ({uploadedFiles.length})
          </Typography>
          
          <List>
            {uploadedFiles.map((file: any) => (
              <ListItem
                key={file.file_id}
                sx={{
                  border: 1,
                  borderColor: 'grey.300',
                  borderRadius: 1,
                  mb: 1,
                }}
              >
                <ListItemIcon>
                  <InsertDriveFile color="primary" />
                </ListItemIcon>
                
                <ListItemText
                  primary={file.filename}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {formatFileSize(file.size)} • {file.total_rows} rows • {file.columns.length} columns
                      </Typography>
                      
                      {file.sheets.length > 0 && (
                        <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {file.sheets.map((sheet, index) => (
                            <Chip
                              key={index}
                              label={sheet}
                              size="small"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      )}
                    </Box>
                  }
                />
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <IconButton
                    size="small"
                    color="primary"
                    title="Preview data"
                  >
                    <Visibility />
                  </IconButton>

                  {enableReportGeneration && (
                    <IconButton
                      size="small"
                      color="success"
                      onClick={() => handleGenerateReport(file)}
                      title="Generate Report"
                      disabled={generatingReport}
                    >
                      <PictureAsPdf />
                    </IconButton>
                  )}

                  {onFileRemoved && (
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleRemoveFile(file.file_id)}
                      title="Remove file"
                    >
                      <Delete />
                    </IconButton>
                  )}
                </Box>
                
                <CheckCircle color="success" sx={{ ml: 1 }} />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Generated Reports Section */}
      {generatedReports.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Generated Reports ({generatedReports.length})
          </Typography>

          <List>
            {generatedReports.map((report) => (
              <ListItem
                key={report.report_id}
                sx={{
                  border: 1,
                  borderColor: 'success.light',
                  borderRadius: 1,
                  mb: 1,
                  bgcolor: 'success.light',
                  bgcolor: 'rgba(76, 175, 80, 0.1)',
                }}
              >
                <ListItemIcon>
                  <Description color="success" />
                </ListItemIcon>

                <ListItemText
                  primary={report.title}
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Available formats: {Object.keys(report.formats).join(', ')}
                      </Typography>

                      <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {Object.entries(report.formats).map(([format, data]) => (
                          <Button
                            key={format}
                            size="small"
                            variant="outlined"
                            startIcon={format === 'pdf' ? <PictureAsPdf /> : <Description />}
                            onClick={() => downloadReport(format, data)}
                            sx={{ textTransform: 'uppercase' }}
                          >
                            {format} ({Math.round(data.size / 1024)}KB)
                          </Button>
                        ))}
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Report Configuration Dialog */}
      <Dialog open={showReportDialog} onClose={() => setShowReportDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate Report</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Report Title"
              value={reportTitle}
              onChange={(e) => setReportTitle(e.target.value)}
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Template</InputLabel>
              <Select
                value={reportTemplate}
                onChange={(e) => setReportTemplate(e.target.value)}
                label="Template"
              >
                <MenuItem value="excel_analysis">Excel Data Analysis</MenuItem>
                <MenuItem value="financial">Financial Report</MenuItem>
                <MenuItem value="executive">Executive Summary</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Output Formats</InputLabel>
              <Select
                multiple
                value={reportFormats}
                onChange={(e) => setReportFormats(e.target.value as string[])}
                label="Output Formats"
              >
                <MenuItem value="docx">Word Document (DOCX)</MenuItem>
                <MenuItem value="pdf">PDF Document</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowReportDialog(false)}>Cancel</Button>
          <Button
            onClick={generateReport}
            variant="contained"
            disabled={!reportTitle.trim() || reportFormats.length === 0}
          >
            Generate Report
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExcelUploader;
