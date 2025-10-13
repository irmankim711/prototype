import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Excel Report Uploader Component
 * Upload Excel files and generate reports in one step
 */

import { useState, useCallback } from "react";

import { Box, Paper, Typography, Button, LinearProgress, Alert, Chip, List, ListItem, ListItemIcon, ListItemText, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, FormControl, InputLabel, Select, MenuItem, TextField } from "@mui/material";

import { CloudUpload, InsertDriveFile, CheckCircle, Error, Delete, Visibility, PictureAsPdf, Description, FileDownload } from "@mui/icons-material";

import { useDropzone } from "react-dropzone";

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

interface ExcelReportUploaderProps {
  onReportGenerated?: (report: GeneratedReport) => void;
  maxFiles?: number;
  maxSize?: number; // in bytes
  disabled?: boolean;
}

const ExcelReportUploader: React.FC<ExcelReportUploaderProps> = ({
  onReportGenerated,
  maxFiles = 1,
  maxSize = 10 * 1024 * 1024, // 10MB
  disabled = false,
}) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Report configuration states
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [reportTitle, setReportTitle] = useState('');
  const [reportFormats, setReportFormats] = useState<string[]>(['pdf']);
  const [reportTemplate, setReportTemplate] = useState('excel_analysis');
  const [generatedReports, setGeneratedReports] = useState<GeneratedReport[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (disabled) return;

    setError(null);

    // Validate file count
    if (acceptedFiles.length > maxFiles) {
      setError(`Maximum ${maxFiles} file(s) allowed`);
      return;
    }

    const file = acceptedFiles[0];

    // Validate file size
    if (file.size > maxSize) {
      setError(`File size must be less than ${Math.round(maxSize / 1024 / 1024)}MB`);
      return;
    }

    // Validate file type
    const validTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ];

    if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls)$/i)) {
      setError('Only Excel files (.xlsx, .xls) are allowed');
      return;
    }

    // Set file and show configuration dialog
    setSelectedFile(file);
    setReportTitle(`Analysis Report - ${file.name}`);
    setShowConfigDialog(true);
  }, [maxFiles, maxSize, disabled]);

  const generateReport = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    setShowConfigDialog(false);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', reportTitle);
      formData.append('formats', reportFormats.join(','));
      formData.append('template', reportTemplate);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 5, 90));
      }, 200);

      const response = await fetch('/api/excel-to-pdf/upload-and-generate', {
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

        // Reset for next upload
        setSelectedFile(null);
        setReportTitle('');
      } else {
        throw new Error(result.error || 'Report generation failed');
      }
    } catch (err: any) {
      console.error('Report generation error:', err);
      setError(err.message || 'Report generation failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const downloadReport = (format: string, reportData: any) => {
    const link = document.createElement('a');
    link.href = reportData.url;
    link.download = reportData.filename;
    link.click();
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
          {isDragActive ? 'Drop Excel files here' : 'Upload Excel Files & Generate Reports'}
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
            Uploading file and generating report...
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

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
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
                            color="success"
                            startIcon={format === 'pdf' ? <PictureAsPdf /> : <Description />}
                            onClick={() => downloadReport(format, data)}
                            sx={{ textTransform: 'uppercase' }}
                          >
                            Download {format} ({Math.round(data.size / 1024)}KB)
                          </Button>
                        ))}
                      </Box>

                      {report.metadata?.method && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                          Generated using: {report.metadata.method}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {/* Report Configuration Dialog */}
      <Dialog open={showConfigDialog} onClose={() => setShowConfigDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Report Generation</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {selectedFile && (
              <Alert severity="info" sx={{ mb: 2 }}>
                File selected: {selectedFile.name} ({formatFileSize(selectedFile.size)})
              </Alert>
            )}

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
          <Button onClick={() => setShowConfigDialog(false)}>Cancel</Button>
          <Button
            onClick={generateReport}
            variant="contained"
            disabled={!reportTitle.trim() || reportFormats.length === 0}
            startIcon={<PictureAsPdf />}
          >
            Generate Report
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExcelReportUploader;