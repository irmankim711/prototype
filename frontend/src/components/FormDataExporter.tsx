import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Tabs,
  Tab,
  Paper,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  InsertDriveFile as InsertDriveFileIcon,
  Google as GoogleIcon,
  AssessmentOutlined as AssessmentOutlinedIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
  BarChart as BarChartIcon,
} from '@mui/icons-material';
import { format, subDays } from 'date-fns';
import { formBuilderAPI, type Form } from '../services/formBuilder';

interface FormDataExporterProps {
  form: Form;
  onExportComplete?: (result: any) => void;
  formType?: 'local' | 'google'; // Add form type support
  googleFormId?: string; // Add Google Form ID support
}

interface ExportOptions {
  include_analytics: boolean;
  use_ai_enhancement: boolean;
  date_range: { start?: string; end?: string; };
  filters: { status: string; submitter_email: string; };
  excel_options: {
    include_form_schema: boolean;
    include_submission_metadata: boolean;
    formatting: 'basic' | 'professional' | 'custom';
    compression: boolean;
  };
}

interface ExportResult {
  success: boolean;
  message?: string;
  error?: string;
  download_url?: string;
  file_size?: number;
  submissions_count?: number;
  responses_count?: number; // For Google Forms
  generation_time?: number;
  data_quality_score?: number;
  ai_enhanced?: boolean;
}

const FormDataExporter: React.FC<FormDataExporterProps> = ({ 
  form, 
  onExportComplete, 
  formType = 'local',
  googleFormId 
}) => {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    include_analytics: true,
    use_ai_enhancement: false,
    date_range: {
      start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    },
    filters: {
      status: 'all',
      submitter_email: '',
    },
    excel_options: {
      include_form_schema: true,
      include_submission_metadata: true,
      formatting: 'professional',
      compression: true,
    },
  });

  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<ExportResult | null>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState<'excel' | 'csv' | 'googlesheets'>('excel');

  // Handle export options changes
  const handleExportOptionChange = (section: keyof ExportOptions, key: string, value: any) => {
    console.log('handleExportOptionChange called:', { section, key, value });
    setExportOptions(prev => {
      const newOptions = { ...prev };
      if (section === 'date_range' && key in prev.date_range) {
        newOptions.date_range = { ...prev.date_range, [key]: value };
      } else if (section === 'filters' && key in prev.filters) {
        newOptions.filters = { ...prev.filters, [key]: value };
      } else if (section === 'excel_options' && key in prev.excel_options) {
        newOptions.excel_options = { ...prev.excel_options, [key]: value };
      } else if (section === 'include_analytics') {
        newOptions.include_analytics = value;
      } else if (section === 'use_ai_enhancement') {
        newOptions.use_ai_enhancement = value;
      }
      console.log('New export options:', newOptions);
      return newOptions;
    });
  };

  // Handle nested export option changes
  const handleNestedOptionChange = (section: keyof ExportOptions, subsection: string, key: string, value: any) => {
    setExportOptions(prev => {
      const newOptions = { ...prev };
      if (section === 'excel_options' && subsection === 'formatting') {
        newOptions.excel_options = { ...prev.excel_options, [key]: value };
      }
      return newOptions;
    });
  };

  // Preview form data before export
  const handlePreviewData = async () => {
    if (formType === 'google' && googleFormId) {
      setIsLoadingPreview(true);
      try {
        const result = await formBuilderAPI.getGoogleFormResponses(googleFormId, {
          limit: 10,
          include_analysis: exportOptions.include_analytics
        });

        if (result.success) {
          setPreviewData({
            form_info: result.form_info,
            responses: result.responses || [],
            total_count: result.total_count || 0,
            analysis: result.analysis
          });
        } else {
          setPreviewData({
            message: result.error || 'Failed to load Google Forms preview',
            error: true
          });
        }
      } catch (error) {
        console.error('Error previewing Google Forms data:', error);
        setPreviewData({
          message: 'Error loading Google Forms data',
          error: true
        });
      } finally {
        setIsLoadingPreview(false);
      }
      return;
    }

    setIsLoadingPreview(true);
    try {
      const params: any = {
        page: 1,
        per_page: 10,
        include_metadata: exportOptions.excel_options.include_form_schema,
        include_analytics: exportOptions.include_analytics,
      };

      if (exportOptions.date_range.start) {
        params.date_from = exportOptions.date_range.start;
      }
      if (exportOptions.date_range.end) {
        params.date_to = exportOptions.date_range.end;
      }
      if (exportOptions.filters.status !== 'all') {
        params.status = exportOptions.filters.status;
      }
      if (exportOptions.filters.submitter_email) {
        params.submitter_email = exportOptions.filters.submitter_email;
      }

      const result = await formBuilderAPI.fetchFormData(form.id, params);
      setPreviewData(result);
    } catch (error) {
      console.error('Error previewing data:', error);
      setPreviewData(null);
    } finally {
      setIsLoadingPreview(false);
    }
  };

  // Export form data to Excel
  const handleExportToExcel = async () => {
    setIsExporting(true);
    setExportResult(null);

    try {
      const exportParams: any = {
        include_analytics: exportOptions.include_analytics,
        use_ai_enhancement: exportOptions.use_ai_enhancement,
        excel_options: exportOptions.excel_options,
      };

      if (exportOptions.date_range.start || exportOptions.date_range.end) {
        exportParams.date_range = {
          start: exportOptions.date_range.start,
          end: exportOptions.date_range.end,
        };
      }

      if (exportOptions.filters.status !== 'all' || exportOptions.filters.submitter_email) {
        exportParams.filters = {
          status: exportOptions.filters.status,
          submitter_email: exportOptions.filters.submitter_email,
        };
      }

      let result;
      if (formType === 'google' && googleFormId) {
        // Export Google Forms data
        result = await formBuilderAPI.exportGoogleFormsToExcel(googleFormId, exportParams);
      } else {
        // Export local form data
        result = await formBuilderAPI.exportFormDataToExcel(form.id, exportParams);
      }

      setExportResult(result);

      if (result.success && onExportComplete) {
        onExportComplete(result);
      }
    } catch (error: any) {
      console.error('Export failed:', error);
      setExportResult({
        success: false,
        error: error.message || 'Export failed',
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Download the generated Excel file
  const handleDownload = async () => {
    if (!exportResult?.download_url) return;

    try {
      const blob = await formBuilderAPI.downloadExcelFile(exportResult.download_url);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Generate filename based on form type
      const timestamp = format(new Date(), 'yyyyMMdd_HHmmss');
      if (formType === 'google') {
        a.download = `google_form_${googleFormId}_export_${timestamp}.xlsx`;
      } else {
        a.download = `form_${form.id}_data_export_${timestamp}.xlsx`;
      }
      
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const isGoogleForm = formType === 'google';
  const formTitle = isGoogleForm ? `Google Form: ${form.title}` : form.title;

  // Handle Preview Dialog
  const handleOpenPreview = async () => {
    await handlePreviewData();
    setPreviewDialogOpen(true);
  };

  const handleClosePreview = () => {
    setPreviewDialogOpen(false);
  };

  // Get submission count
  const getSubmissionCount = () => {
    if (previewData?.error) return 0;
    if (isGoogleForm) return previewData?.total_count || 0;
    return previewData?.pagination?.total || 0;
  };

  const getFieldCount = () => {
    if (isGoogleForm) return previewData?.form_info?.questions?.length || form.schema?.fields?.length || 0;
    return form.schema?.fields?.length || 0;
  };

  return (
    <Box sx={{
      bgcolor: '#F8FAFC',
      minHeight: '100vh',
      py: 4,
      fontFamily: 'Inter, sans-serif'
    }}>
      {/* Header */}
      <Box sx={{ maxWidth: 1200, mx: 'auto', px: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Box sx={{ fontSize: '2rem' }}>🚀</Box>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 700, color: '#1E293B', mb: 0.5 }}>
              Form Data Export System
            </Typography>
            <Typography variant="body1" sx={{ color: '#64748B' }}>
              Easily export form submissions to Excel, Google Sheets, or CSV with advanced filters and professional formatting.
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Main Content */}
      <Box sx={{ maxWidth: 1200, mx: 'auto', px: 3 }}>
        {/* Export Content */}
        <Paper sx={{
          borderRadius: '16px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
          overflow: 'hidden',
          mb: 3
        }}>
          <Box sx={{ p: 4 }}>
            {/* Form Header Info */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" sx={{ fontWeight: 600, color: '#1E293B', mb: 1 }}>
                {form.title}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                <Chip
                  label={isGoogleForm ? 'Google Forms' : 'Active'}
                  size="small"
                  sx={{
                    bgcolor: isGoogleForm ? '#DCFCE7' : '#E0E7FF',
                    color: isGoogleForm ? '#16A34A' : '#4F46E5',
                    fontWeight: 600
                  }}
                />
                <Chip
                  label={`${form.submission_count || 0} ${isGoogleForm ? 'responses' : 'submissions'}`}
                  size="small"
                  sx={{ bgcolor: '#F3E8FF', color: '#9333EA', fontWeight: 600 }}
                />
                <Chip
                  label={`${getFieldCount()} ${isGoogleForm ? 'questions' : 'fields'}`}
                  size="small"
                  sx={{ bgcolor: '#DBEAFE', color: '#2563EB', fontWeight: 600 }}
                />
              </Box>
            </Box>

            {/* Export Settings Section */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#1E293B', mb: 3 }}>
                Export Settings
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Start Date"
                    value={exportOptions.date_range.start}
                    onChange={(e) => handleExportOptionChange('date_range', 'start', e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: '12px',
                      }
                    }}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="date"
                    label="End Date"
                    value={exportOptions.date_range.end}
                    onChange={(e) => handleExportOptionChange('date_range', 'end', e.target.value)}
                    InputLabelProps={{ shrink: true }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: '12px',
                      }
                    }}
                  />
                </Grid>
                {!isGoogleForm && (
                  <>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>Status Filter</InputLabel>
                        <Select
                          value={exportOptions.filters.status}
                          label="Status Filter"
                          onChange={(e) => handleExportOptionChange('filters', 'status', e.target.value)}
                          sx={{
                            borderRadius: '12px',
                          }}
                        >
                          <MenuItem value="all">All</MenuItem>
                          <MenuItem value="approved">Approved</MenuItem>
                          <MenuItem value="rejected">Rejected</MenuItem>
                          <MenuItem value="pending">Pending</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Submitter Email"
                        value={exportOptions.filters.submitter_email}
                        onChange={(e) => handleExportOptionChange('filters', 'submitter_email', e.target.value)}
                        placeholder="Enter email address"
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            borderRadius: '12px',
                          }
                        }}
                      />
                    </Grid>
                  </>
                )}
              </Grid>
            </Box>

            {/* Excel Options Section */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#1E293B', mb: 3 }}>
                Excel Options
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Box sx={{
                    p: 2,
                    borderRadius: '12px',
                    bgcolor: exportOptions.use_ai_enhancement ? '#EEF2FF' : '#F8FAFC',
                    border: '2px solid',
                    borderColor: exportOptions.use_ai_enhancement ? '#6366F1' : '#E2E8F0',
                    transition: 'all 0.3s ease'
                  }}>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={exportOptions.use_ai_enhancement}
                          onChange={(e) => {
                            console.log('AI Checkbox clicked:', e.target.checked);
                            handleExportOptionChange('use_ai_enhancement', '', e.target.checked);
                          }}
                          sx={{
                            color: '#6366F1',
                            '&.Mui-checked': { color: '#6366F1' }
                          }}
                        />
                      }
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography sx={{ fontWeight: 600, color: '#1E293B' }}>
                            🤖 AI-Enhanced Excel Export
                          </Typography>
                          <Chip
                            label="BETA"
                            size="small"
                            sx={{
                              bgcolor: '#6366F1',
                              color: 'white',
                              fontWeight: 700,
                              fontSize: '0.7rem'
                            }}
                          />
                        </Box>
                      }
                    />
                    <Typography variant="body2" sx={{ color: '#64748B', ml: 4, mt: 0.5 }}>
                      Use Claude AI to analyze your data and create professional Excel reports with intelligent formatting,
                      dynamic charts, AI-generated insights, and data visualizations.
                    </Typography>
                    {exportOptions.use_ai_enhancement && (
                      <Box sx={{ ml: 4, mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        <Chip
                          icon={<CheckCircleOutlineIcon sx={{ fontSize: '1rem' }} />}
                          label="Smart Formatting"
                          size="small"
                          variant="outlined"
                          sx={{ borderColor: '#6366F1', color: '#6366F1' }}
                        />
                        <Chip
                          icon={<BarChartIcon sx={{ fontSize: '1rem' }} />}
                          label="Auto Charts"
                          size="small"
                          variant="outlined"
                          sx={{ borderColor: '#6366F1', color: '#6366F1' }}
                        />
                        <Chip
                          icon={<AssessmentOutlinedIcon sx={{ fontSize: '1rem' }} />}
                          label="AI Insights"
                          size="small"
                          variant="outlined"
                          sx={{ borderColor: '#6366F1', color: '#6366F1' }}
                        />
                      </Box>
                    )}
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={exportOptions.excel_options.include_form_schema}
                        onChange={(e) => handleNestedOptionChange('excel_options', 'formatting', 'include_form_schema', e.target.checked)}
                        sx={{ color: '#4F46E5' }}
                      />
                    }
                    label="Include header row"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={exportOptions.excel_options.include_submission_metadata}
                        onChange={(e) => handleNestedOptionChange('excel_options', 'formatting', 'include_submission_metadata', e.target.checked)}
                        sx={{ color: '#4F46E5' }}
                      />
                    }
                    label="Auto-adjust column width"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>File format</InputLabel>
                    <Select
                      value={exportFormat}
                      label="File format"
                      onChange={(e) => setExportFormat(e.target.value as any)}
                      sx={{
                        borderRadius: '12px',
                      }}
                    >
                      <MenuItem value="excel">Excel (.xlsx)</MenuItem>
                      <MenuItem value="csv">CSV (.csv)</MenuItem>
                      <MenuItem value="googlesheets">Google Sheets</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Box>

            {/* Analytics & Preview Section */}
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#1E293B', mb: 3 }}>
                Analytics & Preview
              </Typography>
              <Button
                variant="outlined"
                onClick={handleOpenPreview}
                disabled={isLoadingPreview}
                startIcon={isLoadingPreview ? <CircularProgress size={20} /> : <Box>👁️</Box>}
                sx={{
                  borderRadius: '12px',
                  textTransform: 'none',
                  borderColor: '#E2E8F0',
                  color: '#1E293B',
                  px: 3,
                  py: 1.5,
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: '#4F46E5',
                    bgcolor: '#F5F3FF'
                  }
                }}
              >
                {isLoadingPreview ? 'Loading...' : 'Preview Data'}
              </Button>
            </Box>

            {/* Export Progress */}
            {isExporting && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="body2" sx={{ mb: 1, color: '#64748B' }}>
                  Generating export file...
                </Typography>
                <LinearProgress
                  sx={{
                    borderRadius: '8px',
                    height: 8,
                    bgcolor: '#E2E8F0',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: '#4F46E5'
                    }
                  }}
                />
              </Box>
            )}

            {/* Export Action */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, color: '#1E293B', mb: 3 }}>
                Export Action
              </Typography>
              <Button
                variant="contained"
                onClick={handleExportToExcel}
                disabled={isExporting}
                startIcon={<Box>⬇️</Box>}
                sx={{
                  bgcolor: '#4F46E5',
                  color: 'white',
                  borderRadius: '12px',
                  textTransform: 'none',
                  px: 4,
                  py: 1.5,
                  fontSize: '1rem',
                  fontWeight: 600,
                  boxShadow: '0 4px 12px rgba(79, 70, 229, 0.25)',
                  '&:hover': {
                    bgcolor: '#4338CA',
                    boxShadow: '0 6px 16px rgba(79, 70, 229, 0.35)'
                  },
                  '&:disabled': {
                    bgcolor: '#CBD5E1'
                  }
                }}
              >
                {isExporting ? 'Generating...' : `Export to ${exportFormat === 'excel' ? 'Excel' : exportFormat === 'csv' ? 'CSV' : 'Google Sheets'}`}
              </Button>
            </Box>

            {/* Export Results */}
            {exportResult && (
              <Box sx={{ mt: 4 }}>
                {exportResult.success ? (
                  <Paper sx={{
                    p: 3,
                    borderRadius: '12px',
                    bgcolor: '#F0FDF4',
                    border: '1px solid #BBF7D0'
                  }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <CheckCircleOutlineIcon sx={{ color: '#16A34A' }} />
                      <Typography sx={{ fontWeight: 600, color: '#166534' }}>
                        Export completed successfully!
                      </Typography>
                      {exportResult.ai_enhanced && (
                        <Chip
                          label="AI Enhanced"
                          size="small"
                          sx={{
                            bgcolor: '#6366F1',
                            color: 'white',
                            fontWeight: 700,
                            fontSize: '0.7rem'
                          }}
                        />
                      )}
                    </Box>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          {isGoogleForm ? 'Responses' : 'Submissions'}
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {isGoogleForm ? (exportResult.responses_count || 0) : (exportResult.submissions_count || 0)}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          File Size
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {exportResult.file_size ? formatFileSize(exportResult.file_size) : 'N/A'}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          Generation Time
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {exportResult.generation_time ? `${exportResult.generation_time.toFixed(1)}s` : 'N/A'}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          Quality Score
                        </Typography>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {exportResult.data_quality_score ? `${(exportResult.data_quality_score * 100).toFixed(0)}%` : 'N/A'}
                        </Typography>
                      </Grid>
                    </Grid>
                    <Button
                      variant="contained"
                      onClick={handleDownload}
                      startIcon={<DownloadIcon />}
                      sx={{
                        bgcolor: '#16A34A',
                        borderRadius: '12px',
                        textTransform: 'none',
                        fontWeight: 600,
                        '&:hover': { bgcolor: '#15803D' }
                      }}
                    >
                      Download File
                    </Button>
                  </Paper>
                ) : (
                  <Alert
                    severity="error"
                    sx={{
                      borderRadius: '12px',
                      '& .MuiAlert-message': { fontWeight: 500 }
                    }}
                  >
                    {exportResult.error}
                  </Alert>
                )}
              </Box>
            )}
          </Box>
        </Paper>
      </Box>

      {/* Preview Dialog */}
      <Dialog
        open={previewDialogOpen}
        onClose={handleClosePreview}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: '16px',
            maxHeight: '80vh'
          }
        }}
      >
        <DialogTitle sx={{
          fontWeight: 700,
          fontSize: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: 1
        }}>
          <Box>📊</Box>
          Data Preview & Analytics
        </DialogTitle>
        <DialogContent dividers>
          {isLoadingPreview ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : previewData?.error ? (
            <Alert severity="error" sx={{ borderRadius: '12px' }}>
              {previewData.message}
            </Alert>
          ) : previewData ? (
            <Box>
              {/* Summary Stats */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} sm={3}>
                  <Paper sx={{ p: 2, borderRadius: '12px', textAlign: 'center', bgcolor: '#F0F9FF' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#0284C7' }}>
                      {getSubmissionCount()}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Total {isGoogleForm ? 'Responses' : 'Submissions'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Paper sx={{ p: 2, borderRadius: '12px', textAlign: 'center', bgcolor: '#FFF7ED' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#EA580C' }}>
                      {getFieldCount()}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      {isGoogleForm ? 'Questions' : 'Fields'}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Paper sx={{ p: 2, borderRadius: '12px', textAlign: 'center', bgcolor: '#F0FDF4' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#16A34A' }}>
                      {exportOptions.include_analytics ? 'Yes' : 'No'}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Analytics
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Paper sx={{ p: 2, borderRadius: '12px', textAlign: 'center', bgcolor: '#FDF4FF' }}>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#C026D3' }}>
                      {exportFormat === 'excel' ? 'XLSX' : exportFormat.toUpperCase()}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      Format
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>

              {/* Sample Data Table */}
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Sample Data
              </Typography>
              <TableContainer component={Paper} sx={{ borderRadius: '12px', mb: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: '#F8FAFC' }}>
                      <TableCell sx={{ fontWeight: 600 }}>Field</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Sample Value</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(isGoogleForm ?
                      previewData.responses?.slice(0, 3) :
                      previewData.submissions?.slice(0, 3)
                    )?.map((item: any, idx: number) => (
                      <TableRow key={idx}>
                        <TableCell>{`Field ${idx + 1}`}</TableCell>
                        <TableCell>{JSON.stringify(item).substring(0, 30)}...</TableCell>
                        <TableCell>
                          <Chip label="Text" size="small" sx={{ bgcolor: '#E0E7FF', color: '#4F46E5' }} />
                        </TableCell>
                      </TableRow>
                    )) || (
                      <TableRow>
                        <TableCell colSpan={3} align="center">
                          No data available
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Chart Summary */}
              {exportOptions.include_analytics && (
                <Paper sx={{ p: 3, borderRadius: '12px', bgcolor: '#FAFAFA' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <BarChartIcon sx={{ color: '#4F46E5' }} />
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      Analytics Summary
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Analytics data will be included in your export file with charts and visualizations.
                  </Typography>
                </Paper>
              )}
            </Box>
          ) : (
            <Typography color="text.secondary" align="center">
              No preview data available
            </Typography>
          )}
        </DialogContent>
        <DialogActions sx={{ p: 2 }}>
          <Button
            onClick={handleClosePreview}
            sx={{
              borderRadius: '12px',
              textTransform: 'none',
              fontWeight: 600
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FormDataExporter;
