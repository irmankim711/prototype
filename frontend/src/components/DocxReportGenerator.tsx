import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Alert,
  CircularProgress,
  Paper,
  Grid,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Description as DocxIcon,
  PictureAsPdf as PdfIcon,
  TableChart as ExcelIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { reportService } from '../services/reportService';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface DocxReportGeneratorProps {
  onReportGenerated?: (report: unknown) => void;
}

const DocxReportGenerator: React.FC<DocxReportGeneratorProps> = ({ onReportGenerated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [generatedReport, setGeneratedReport] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Generate report mutation
  const generateReportMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      // First, upload the file to get a file path
      const uploadResponse = await reportService.uploadFile(formData);
      const filePath = uploadResponse.file_path;
      
      // Then generate the report using the file path
      return await reportService.generateLatexReport({
        title: title,
        description: description,
        latex_file_path: filePath,
        config: {
          output_formats: ['docx', 'pdf', 'excel'],
          template: 'default'
        }
      });
    },
    onSuccess: (report) => {
      setGeneratedReport(report);
      setSuccess('Report generated successfully!');
      onReportGenerated?.(report);
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
    onError: (error: unknown) => {
      setError(`Failed to generate report: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  });

  // Download report mutation
  const downloadMutation = useMutation({
    mutationFn: (fileType: 'pdf' | 'docx' | 'excel') => {
      if (!generatedReport) throw new Error('No report to download');
      return reportService.downloadReport(generatedReport.id.toString(), fileType);
    },
    onSuccess: (blob, fileType) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${title || 'report'}_${fileType}.${fileType === 'excel' ? 'xlsx' : fileType}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setSuccess(`${fileType.toUpperCase()} downloaded successfully!`);
    },
    onError: (error: unknown) => {
      setError(`Failed to download ${fileType}: ${error.message}`);
    }
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Check if it's a supported file type
      if (file.name.endsWith('.docx') || file.name.endsWith('.doc')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Please select a DOCX or DOC file');
        setSelectedFile(null);
      }
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedFile || !title.trim()) {
      setError('Please provide a title and select a file');
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', title);
      if (description) {
        formData.append('description', description);
      }

      await generateReportMutation.mutateAsync(formData);
    } catch (error: unknown) {
      setError(`Failed to generate report: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleDownload = (fileType: 'pdf' | 'docx' | 'excel') => {
    downloadMutation.mutate(fileType);
  };

  const handleRefresh = () => {
    if (generatedReport) {
      // Refresh report status
      reportService.getReport(generatedReport.id.toString())
        .then(updatedReport => {
          setGeneratedReport(updatedReport);
          setSuccess('Report status updated');
        })
        .catch(error => {
          setError(`Failed to refresh report: ${error.message}`);
        });
    }
  };

  const isGenerating = generateReportMutation.isPending;
  const isDownloading = downloadMutation.isPending;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Generate DOCX Report
      </Typography>
      
      <Grid container spacing={3}>
        {/* Input Form */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Report Details
              </Typography>
              
              <TextField
                fullWidth
                label="Report Title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                margin="normal"
                required
                placeholder="Enter report title"
              />
              
              <TextField
                fullWidth
                label="Description (Optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                margin="normal"
                multiline
                rows={3}
                placeholder="Enter report description"
              />
              
              <Box sx={{ mt: 2 }}>
                <input
                  accept=".docx,.doc"
                  style={{ display: 'none' }}
                  id="file-upload"
                  type="file"
                  onChange={handleFileSelect}
                />
                <label htmlFor="file-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<UploadIcon />}
                    fullWidth
                    sx={{ mb: 1 }}
                  >
                    Select DOCX File
                  </Button>
                </label>
                
                {selectedFile && (
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" color="text.secondary">
                      Selected: {selectedFile.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Size: {(selectedFile.size / 1024).toFixed(1)} KB
                    </Typography>
                  </Paper>
                )}
              </Box>
              
              <Button
                variant="contained"
                onClick={handleGenerateReport}
                disabled={!selectedFile || !title.trim() || isGenerating}
                fullWidth
                sx={{ mt: 2 }}
                startIcon={isGenerating ? <CircularProgress size={20} /> : <DocxIcon />}
              >
                {isGenerating ? 'Generating Report...' : 'Generate Report'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Generated Report Display */}
        <Grid item xs={12} md={6}>
          {generatedReport && (
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    Generated Report
                  </Typography>
                  <IconButton onClick={handleRefresh} size="small">
                    <RefreshIcon />
                  </IconButton>
                </Box>
                
                <Typography variant="body2" gutterBottom>
                  <strong>Title:</strong> {generatedReport.title}
                </Typography>
                
                {generatedReport.description && (
                  <Typography variant="body2" gutterBottom>
                    <strong>Description:</strong> {generatedReport.description}
                  </Typography>
                )}
                
                <Typography variant="body2" gutterBottom>
                  <strong>Status:</strong> 
                  <Chip
                    label={generatedReport.status}
                    color={
                      generatedReport.status === 'completed' ? 'success' :
                      generatedReport.status === 'generating' ? 'warning' :
                      generatedReport.status === 'failed' ? 'error' : 'default'
                    }
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Typography>
                
                <Typography variant="body2" gutterBottom>
                  <strong>Created:</strong> {new Date(generatedReport.created_at || '').toLocaleString()}
                </Typography>
                
                <Typography variant="body2" gutterBottom>
                  <strong>Type:</strong> {generatedReport.report_type || 'docx_based'}
                </Typography>
                
                {/* Download Options */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Download Options:
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {generatedReport.pdf_file_path && (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<PdfIcon />}
                        onClick={() => handleDownload('pdf')}
                        disabled={isDownloading}
                        color="error"
                      >
                        PDF
                      </Button>
                    )}
                    
                    {generatedReport.docx_file_path && (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<DocxIcon />}
                        onClick={() => handleDownload('docx')}
                        disabled={isDownloading}
                        color="primary"
                      >
                        DOCX
                      </Button>
                    )}
                    
                    {generatedReport.excel_file_path && (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<ExcelIcon />}
                        onClick={() => handleDownload('excel')}
                        disabled={isDownloading}
                        color="success"
                      >
                        Excel
                      </Button>
                    )}
                  </Box>
                </Box>
                
                {/* File Information */}
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    File Information:
                  </Typography>
                  
                  <Grid container spacing={1}>
                    {generatedReport.pdf_file_size && (
                      <Grid item xs={4}>
                        <Typography variant="caption" color="text.secondary">
                          PDF: {Math.round(generatedReport.pdf_file_size / 1024)} KB
                        </Typography>
                      </Grid>
                    )}
                    
                    {generatedReport.docx_file_size && (
                      <Grid item xs={4}>
                        <Typography variant="caption" color="text.secondary">
                          DOCX: {Math.round(generatedReport.docx_file_size / 1024)} KB
                        </Typography>
                      </Grid>
                    )}
                    
                    {generatedReport.excel_file_size && (
                      <Grid item xs={4}>
                        <Typography variant="caption" color="text.secondary">
                          Excel: {Math.round(generatedReport.excel_file_size / 1024)} KB
                        </Typography>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mt: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
    </Box>
  );
};

export default DocxReportGenerator;
