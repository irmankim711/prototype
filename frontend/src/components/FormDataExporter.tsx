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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Paper,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  TableChart as TableChartIcon,
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
}

const FormDataExporter: React.FC<FormDataExporterProps> = ({ 
  form, 
  onExportComplete, 
  formType = 'local',
  googleFormId 
}) => {
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    include_analytics: true,
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
  const [expandedSection, setExpandedSection] = useState<string | null>('filters');

  // Handle export options changes
  const handleExportOptionChange = (section: keyof ExportOptions, key: string, value: any) => {
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
      }
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
    if (formType === 'google') {
      // Google Forms preview not available yet
      setPreviewData({ message: 'Preview not available for Google Forms' });
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

  return (
    <Card sx={{ maxWidth: 800, mx: 'auto', mt: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <TableChartIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6" component="h2">
            Export {isGoogleForm ? 'Google Form' : 'Form'} Data to Excel
          </Typography>
        </Box>

        <Typography variant="body2" color="text.secondary" mb={3}>
          Export {isGoogleForm ? 'Google Form responses' : 'form submissions'} with advanced filtering and Excel formatting options.
        </Typography>

        {/* Form Type Indicator */}
        {isGoogleForm && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>Google Forms Export:</strong> This will export data directly from your Google Form using the Google Forms API.
          </Alert>
        )}

        {/* Filters Section */}
        <Accordion 
          expanded={expandedSection === 'filters'} 
          onChange={() => setExpandedSection(expandedSection === 'filters' ? null : 'filters')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center">
              <FilterIcon sx={{ mr: 1 }} />
              <Typography>Filters & Date Range</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="Start Date"
                  value={exportOptions.date_range.start}
                  onChange={(e) => handleExportOptionChange('date_range', 'start', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="End Date"
                  value={exportOptions.date_range.end}
                  onChange={(e) => handleExportOptionChange('date_range', 'end', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              {!isGoogleForm && (
                <>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>Status Filter</InputLabel>
                      <Select
                        value={exportOptions.filters.status}
                        label="Status Filter"
                        onChange={(e) => handleExportOptionChange('filters', 'status', e.target.value)}
                      >
                        <MenuItem value="all">All Statuses</MenuItem>
                        <MenuItem value="submitted">Submitted</MenuItem>
                        <MenuItem value="reviewed">Reviewed</MenuItem>
                        <MenuItem value="approved">Approved</MenuItem>
                        <MenuItem value="rejected">Rejected</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Submitter Email"
                      value={exportOptions.filters.submitter_email}
                      onChange={(e) => handleExportOptionChange('filters', 'submitter_email', e.target.value)}
                      placeholder="Filter by email (optional)"
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Excel Options Section */}
        <Accordion 
          expanded={expandedSection === 'excel-options'} 
          onChange={() => setExpandedSection(expandedSection === 'excel-options' ? null : 'excel-options')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center">
              <SettingsIcon sx={{ mr: 1 }} />
              <Typography>Excel Options</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Formatting Style</InputLabel>
                  <Select
                    value={exportOptions.excel_options.formatting}
                    label="Formatting Style"
                    onChange={(e) => handleNestedOptionChange('excel_options', 'formatting', 'formatting', e.target.value)}
                  >
                    <MenuItem value="basic">Basic</MenuItem>
                    <MenuItem value="professional">Professional</MenuItem>
                    <MenuItem value="custom">Custom</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.excel_options.compression}
                      onChange={(e) => handleNestedOptionChange('excel_options', 'formatting', 'compression', e.target.checked)}
                    />
                  }
                  label="Enable Compression"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.excel_options.include_form_schema}
                      onChange={(e) => handleNestedOptionChange('excel_options', 'formatting', 'include_form_schema', e.target.checked)}
                    />
                  }
                  label="Include Form Schema"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={exportOptions.excel_options.include_submission_metadata}
                      onChange={(e) => handleNestedOptionChange('excel_options', 'formatting', 'include_submission_metadata', e.target.checked)}
                    />
                  }
                  label="Include Submission Metadata"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Analytics Section */}
        <Accordion 
          expanded={expandedSection === 'analytics'} 
          onChange={() => setExpandedSection(expandedSection === 'analytics' ? null : 'analytics')}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center">
              <AnalyticsIcon sx={{ mr: 1 }} />
              <Typography>Analytics & Preview</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box mb={2}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={exportOptions.include_analytics}
                    onChange={(e) => handleExportOptionChange('include_analytics', 'include_analytics', e.target.checked)}
                  />
                }
                label="Include Analytics in Export"
              />
            </Box>
            
            {!isGoogleForm && (
              <Button
                variant="outlined"
                onClick={handlePreviewData}
                disabled={isLoadingPreview}
                startIcon={isLoadingPreview ? <CircularProgress size={16} /> : <RefreshIcon />}
                sx={{ mb: 2 }}
              >
                {isLoadingPreview ? 'Loading...' : 'Preview Data'}
              </Button>
            )}

            {previewData && (
              <Box mt={2}>
                <Typography variant="subtitle2" gutterBottom>
                  {isGoogleForm ? 'Google Forms Export' : `Preview (${previewData.submissions?.length || 0} submissions)`}
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {!isGoogleForm ? (
                    <>
                      <Chip label={`Total: ${previewData.pagination?.total || 0}`} color="primary" />
                      <Chip label={`Form: ${previewData.form?.title}`} color="secondary" />
                      {previewData.analytics && (
                        <Chip label="Analytics Included" color="success" />
                      )}
                    </>
                  ) : (
                    <Chip label={previewData.message} color="info" />
                  )}
                </Box>
              </Box>
            )}
          </AccordionDetails>
        </Accordion>

        {/* Export Actions */}
        <Box mt={3} display="flex" gap={2} flexWrap="wrap">
          <Button
            variant="contained"
            color="primary"
            onClick={handleExportToExcel}
            disabled={isExporting}
            startIcon={isExporting ? <CircularProgress size={16} /> : <DownloadIcon />}
            size="large"
          >
            {isExporting ? 'Generating Excel...' : `Export ${isGoogleForm ? 'Google Form' : 'Form'} to Excel`}
          </Button>

          {exportResult?.success && (
            <Button
              variant="outlined"
              color="success"
              onClick={handleDownload}
              startIcon={<DownloadIcon />}
              size="large"
            >
              Download Excel File
            </Button>
          )}
        </Box>

        {/* Export Results */}
        {exportResult && (
          <Box mt={3}>
            <Divider sx={{ mb: 2 }} />
            {exportResult.success ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                {exportResult.message}
              </Alert>
            ) : (
              <Alert severity="error" sx={{ mb: 2 }}>
                {exportResult.error}
              </Alert>
            )}

            {exportResult.success && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Export Details:
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      {isGoogleForm ? 'Responses' : 'Submissions'}
                    </Typography>
                    <Typography variant="body1">
                      {isGoogleForm ? (exportResult.responses_count || 0) : (exportResult.submissions_count || 0)}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      File Size
                    </Typography>
                    <Typography variant="body1">
                      {exportResult.file_size ? formatFileSize(exportResult.file_size) : 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Generation Time
                    </Typography>
                    <Typography variant="body1">
                      {exportResult.generation_time ? `${exportResult.generation_time.toFixed(1)}s` : 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Typography variant="body2" color="text.secondary">
                      Quality Score
                    </Typography>
                    <Typography variant="body1">
                      {exportResult.data_quality_score ? `${(exportResult.data_quality_score * 100).toFixed(1)}%` : 'N/A'}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default FormDataExporter;
