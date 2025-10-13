import React, { useState, useEffect } from 'react';
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
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  TableChart as TableChartIcon,
  Google as GoogleIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Login as LoginIcon,
  Description as DescriptionIcon,
} from '@mui/icons-material';
import { format, subDays } from 'date-fns';
import { formBuilderAPI } from '../services/formBuilder';

interface GoogleForm {
  id: string;
  title: string;
  description?: string;
  created_time?: string;
  modified_time?: string;
  web_view_link?: string;
  published_url?: string;
  response_count: number;
  question_count: number;
  type: string;
  status: string;
}

interface GoogleFormsStatus {
  success: boolean;
  status: string;
  is_authenticated: boolean;
  is_authorized: boolean;
  has_valid_token: boolean;
  requires_auth?: boolean;
  requires_config?: boolean;
  message: string;
  forms_count?: number;
}

interface ExportOptions {
  include_analytics: boolean;
  date_range: { start?: string; end?: string; };
  excel_options: {
    include_form_schema: boolean;
    include_submission_metadata: boolean;
    formatting: 'basic' | 'professional' | 'custom';
    compression: boolean;
  };
  max_responses: number;
}

interface ExportResult {
  success: boolean;
  message?: string;
  error?: string;
  download_url?: string;
  file_size?: number;
  responses_count?: number;
  generation_time?: number;
  form_info?: any;
}

const GoogleFormsExporter: React.FC = () => {
  const [googleFormsStatus, setGoogleFormsStatus] = useState<GoogleFormsStatus | null>(null);
  const [availableForms, setAvailableForms] = useState<GoogleForm[]>([]);
  const [selectedForm, setSelectedForm] = useState<GoogleForm | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);
  const [isLoadingForms, setIsLoadingForms] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [exportResult, setExportResult] = useState<ExportResult | null>(null);

  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    include_analytics: true,
    date_range: {
      start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      end: format(new Date(), 'yyyy-MM-dd'),
    },
    excel_options: {
      include_form_schema: true,
      include_submission_metadata: true,
      formatting: 'professional',
      compression: true,
    },
    max_responses: 1000,
  });

  const steps = [
    'Connect Google Forms',
    'Select Form',
    'Configure Export',
    'Export to Excel'
  ];

  useEffect(() => {
    checkGoogleFormsStatus();
  }, []);

  const checkGoogleFormsStatus = async () => {
    setIsLoadingStatus(true);
    try {
      const status = await formBuilderAPI.getGoogleFormsStatus();
      setGoogleFormsStatus(status);

      if (status.success && status.is_authorized) {
        setCurrentStep(1);
        await loadGoogleForms();
      } else if (status.requires_auth || status.requires_config) {
        setCurrentStep(0);
      }
    } catch (error) {
      console.error('Error checking Google Forms status:', error);
      setGoogleFormsStatus({
        success: false,
        status: 'error',
        is_authenticated: false,
        is_authorized: false,
        has_valid_token: false,
        message: 'Failed to check Google Forms status'
      });
    } finally {
      setIsLoadingStatus(false);
    }
  };

  const loadGoogleForms = async () => {
    if (!googleFormsStatus?.is_authorized) return;

    setIsLoadingForms(true);
    try {
      const formsResponse = await formBuilderAPI.getGoogleForms(20);
      if (formsResponse.success) {
        setAvailableForms(formsResponse.forms || []);
      } else {
        console.error('Failed to load Google Forms:', formsResponse.error);
      }
    } catch (error) {
      console.error('Error loading Google Forms:', error);
    } finally {
      setIsLoadingForms(false);
    }
  };

  const handleGoogleAuth = async () => {
    try {
      const authResponse = await formBuilderAPI.initiateGoogleAuth();
      if (authResponse.success && authResponse.authorization_url) {
        // Open authorization URL in a new window
        window.open(authResponse.authorization_url, '_blank');
        setShowAuthDialog(true);
      }
    } catch (error) {
      console.error('Error initiating Google auth:', error);
    }
  };

  const handleAuthComplete = async () => {
    setShowAuthDialog(false);
    await checkGoogleFormsStatus();
  };

  const handleFormSelect = (form: GoogleForm) => {
    setSelectedForm(form);
    setCurrentStep(2);
  };

  const handleExportOptionChange = (section: keyof ExportOptions, key: string, value: any) => {
    setExportOptions(prev => {
      const newOptions = { ...prev };
      if (section === 'date_range') {
        newOptions.date_range = { ...prev.date_range, [key]: value };
      } else if (section === 'excel_options') {
        newOptions.excel_options = { ...prev.excel_options, [key]: value };
      } else if (key in prev) {
        (newOptions as any)[key] = value;
      }
      return newOptions;
    });
  };

  const handleExport = async () => {
    if (!selectedForm) return;

    setIsExporting(true);
    setExportResult(null);
    setCurrentStep(3);

    try {
      const result = await formBuilderAPI.exportGoogleFormsToExcel(selectedForm.id, exportOptions);
      setExportResult(result);
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

  const handleDownload = async () => {
    if (!exportResult?.download_url) return;

    try {
      const blob = await formBuilderAPI.downloadExcelFile(exportResult.download_url);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `google_form_${selectedForm?.id}_export_${format(new Date(), 'yyyyMMdd_HHmmss')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: GoogleFormsStatus) => {
    if (!status.success) return <ErrorIcon color="error" />;
    if (status.is_authorized) return <CheckCircleIcon color="success" />;
    if (status.requires_auth) return <WarningIcon color="warning" />;
    return <InfoIcon color="info" />;
  };

  if (isLoadingStatus) {
    return (
      <Card sx={{ maxWidth: 800, mx: 'auto', mt: 2 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="center" p={3}>
            <CircularProgress />
            <Typography variant="body1" sx={{ ml: 2 }}>
              Checking Google Forms connection...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ maxWidth: 900, mx: 'auto', mt: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={3}>
          <GoogleIcon sx={{ mr: 1, color: '#4285f4' }} />
          <Typography variant="h5" component="h1">
            Google Forms Excel Export
          </Typography>
        </Box>

        <Typography variant="body2" color="text.secondary" mb={3}>
          Export your Google Forms responses to professional Excel files with analytics and insights.
        </Typography>

        {/* Progress Stepper */}
        <Stepper activeStep={currentStep} alternativeLabel sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Step 1: Google Forms Connection Status */}
        {currentStep === 0 && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                {googleFormsStatus && getStatusIcon(googleFormsStatus)}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Google Forms Connection
                </Typography>
              </Box>

              {googleFormsStatus && (
                <Alert
                  severity={
                    googleFormsStatus.success && googleFormsStatus.is_authorized ? 'success' :
                    googleFormsStatus.requires_auth ? 'warning' : 'error'
                  }
                  sx={{ mb: 2 }}
                >
                  {googleFormsStatus.message}
                </Alert>
              )}

              {googleFormsStatus?.requires_auth && (
                <Box>
                  <Typography variant="body2" color="text.secondary" mb={2}>
                    To export Google Forms data, you need to authorize access to your Google account.
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<LoginIcon />}
                    onClick={handleGoogleAuth}
                    sx={{ backgroundColor: '#4285f4', '&:hover': { backgroundColor: '#3367d6' } }}
                  >
                    Connect Google Forms
                  </Button>
                </Box>
              )}

              {googleFormsStatus?.requires_config && (
                <Alert severity="error">
                  Google Forms service is not configured. Please contact your administrator to set up Google OAuth credentials.
                </Alert>
              )}
            </CardContent>
          </Card>
        )}

        {/* Step 2: Form Selection */}
        {currentStep >= 1 && googleFormsStatus?.is_authorized && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">Select Google Form</Typography>
                <Button
                  startIcon={<RefreshIcon />}
                  onClick={loadGoogleForms}
                  disabled={isLoadingForms}
                  size="small"
                >
                  Refresh
                </Button>
              </Box>

              {isLoadingForms ? (
                <Box display="flex" alignItems="center" p={2}>
                  <CircularProgress size={24} />
                  <Typography variant="body2" sx={{ ml: 2 }}>
                    Loading your Google Forms...
                  </Typography>
                </Box>
              ) : availableForms.length > 0 ? (
                <List>
                  {availableForms.map((form) => (
                    <ListItem key={form.id} disablePadding>
                      <ListItemButton
                        selected={selectedForm?.id === form.id}
                        onClick={() => handleFormSelect(form)}
                      >
                        <ListItemIcon>
                          <DescriptionIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary={form.title}
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {form.description || 'No description'}
                              </Typography>
                              <Box display="flex" gap={1} mt={0.5}>
                                <Chip label={`${form.response_count} responses`} size="small" />
                                <Chip label={`${form.question_count} questions`} size="small" />
                              </Box>
                            </Box>
                          }
                        />
                      </ListItemButton>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Alert severity="info">
                  No Google Forms found in your account. Make sure you have created at least one form.
                </Alert>
              )}
            </CardContent>
          </Card>
        )}

        {/* Step 3: Export Configuration */}
        {currentStep >= 2 && selectedForm && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" mb={2}>Configure Export Options</Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                Selected Form: <strong>{selectedForm.title}</strong>
                {selectedForm.response_count > 0 && (
                  <span> • {selectedForm.response_count} responses available</span>
                )}
              </Alert>

              {/* Date Range */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center">
                    <FilterIcon sx={{ mr: 1 }} />
                    <Typography>Date Range & Limits</Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="date"
                        label="Start Date"
                        value={exportOptions.date_range.start}
                        onChange={(e) => handleExportOptionChange('date_range', 'start', e.target.value)}
                        InputLabelProps={{ shrink: true }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="date"
                        label="End Date"
                        value={exportOptions.date_range.end}
                        onChange={(e) => handleExportOptionChange('date_range', 'end', e.target.value)}
                        InputLabelProps={{ shrink: true }}
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <TextField
                        fullWidth
                        type="number"
                        label="Max Responses"
                        value={exportOptions.max_responses}
                        onChange={(e) => handleExportOptionChange('excel_options', 'max_responses', parseInt(e.target.value))}
                        inputProps={{ min: 1, max: 10000 }}
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* Excel Options */}
              <Accordion>
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
                          onChange={(e) => handleExportOptionChange('excel_options', 'formatting', e.target.value)}
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
                            onChange={(e) => handleExportOptionChange('excel_options', 'compression', e.target.checked)}
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
                            onChange={(e) => handleExportOptionChange('excel_options', 'include_form_schema', e.target.checked)}
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
                            onChange={(e) => handleExportOptionChange('excel_options', 'include_submission_metadata', e.target.checked)}
                          />
                        }
                        label="Include Response Metadata"
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>

              {/* Analytics */}
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center">
                    <AnalyticsIcon sx={{ mr: 1 }} />
                    <Typography>Analytics & Insights</Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={exportOptions.include_analytics}
                        onChange={(e) => handleExportOptionChange('excel_options', 'include_analytics', e.target.checked)}
                      />
                    }
                    label="Include Analytics and Statistical Analysis"
                  />
                  <Typography variant="caption" display="block" color="text.secondary">
                    Adds a separate analytics sheet with response statistics, insights, and data quality metrics.
                  </Typography>
                </AccordionDetails>
              </Accordion>

              <Box mt={3}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleExport}
                  disabled={isExporting}
                  startIcon={isExporting ? <CircularProgress size={16} /> : <TableChartIcon />}
                >
                  {isExporting ? 'Generating Excel...' : 'Export to Excel'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Step 4: Export Results */}
        {currentStep >= 3 && (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" mb={2}>Export Results</Typography>

              {isExporting && (
                <Box mb={2}>
                  <Typography variant="body2" mb={1}>Generating Excel file...</Typography>
                  <LinearProgress />
                </Box>
              )}

              {exportResult && (
                <Box>
                  {exportResult.success ? (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      {exportResult.message || 'Excel file generated successfully!'}
                    </Alert>
                  ) : (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      {exportResult.error || 'Export failed'}
                    </Alert>
                  )}

                  {exportResult.success && (
                    <Box>
                      <Grid container spacing={2} mb={2}>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="body2" color="text.secondary">Responses</Typography>
                          <Typography variant="h6">{exportResult.responses_count || 0}</Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="body2" color="text.secondary">File Size</Typography>
                          <Typography variant="h6">
                            {exportResult.file_size ? formatFileSize(exportResult.file_size) : 'N/A'}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="body2" color="text.secondary">Generation Time</Typography>
                          <Typography variant="h6">
                            {exportResult.generation_time ? `${exportResult.generation_time.toFixed(1)}s` : 'N/A'}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} sm={3}>
                          <Typography variant="body2" color="text.secondary">Format</Typography>
                          <Typography variant="h6">Excel (.xlsx)</Typography>
                        </Grid>
                      </Grid>

                      <Button
                        variant="contained"
                        color="success"
                        onClick={handleDownload}
                        startIcon={<DownloadIcon />}
                        size="large"
                      >
                        Download Excel File
                      </Button>
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* Authentication Dialog */}
        <Dialog open={showAuthDialog} onClose={() => setShowAuthDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Google Forms Authorization</DialogTitle>
          <DialogContent>
            <Typography variant="body1" mb={2}>
              Please complete the authorization in the opened window, then click "Done" below.
            </Typography>
            <Alert severity="info">
              Make sure to allow access to your Google Forms data when prompted.
            </Alert>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowAuthDialog(false)}>Cancel</Button>
            <Button onClick={handleAuthComplete} variant="contained">Done</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default GoogleFormsExporter;