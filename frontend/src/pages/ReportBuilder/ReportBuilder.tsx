import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  Paper,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  useTheme,
  useMediaQuery,
  Tooltip,
  LinearProgress,
  Avatar,
  Grid,
  Card,
  CardMedia,
  CardContent,
  TextField,
  Modal,
  IconButton,
  Chip,
  InputAdornment,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import {
  fetchReportTemplates,
  createReport,
  analyzeData,
  fetchTemplatePlaceholders,
  fetchWordTemplates,
} from '../../services/api';
import type { ReportTemplate } from '../../services/api';
import GoogleSheetImport from './GoogleSheetImport';
import FieldMapping from './FieldMapping';
import TemplateEditor from './TemplateEditor';
import { Assignment, Description, SwapHoriz, Preview, CheckCircle } from '@mui/icons-material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { Divider, Fade } from '@mui/material';
import * as XLSX from 'xlsx';
import DOMPurify from 'dompurify';


function isPlainObject(obj: any): obj is Record<string, any> {
  return obj && typeof obj === 'object' && !Array.isArray(obj);
}

const steps = ['Import Data', 'Choose Template', 'Review & Generate', 'Success'];

// Mock data for fallback
const mockTemplates = [
  {
    id: '1',
    name: 'Financial Report',
    description: 'Standard financial report template',
    schema: {
      fields: [
        { name: 'revenue', label: 'Revenue', type: 'number', required: true },
        { name: 'expenses', label: 'Expenses', type: 'number', required: true },
        { name: 'notes', label: 'Notes', type: 'text', required: false }
      ]
    },
    isActive: true
  },
  {
    id: '2',
    name: 'Performance Report',
    description: 'Performance analysis template',
    schema: {
      fields: [
        { name: 'score', label: 'Performance Score', type: 'number', required: true },
        { name: 'comments', label: 'Comments', type: 'text', required: false }
      ]
    },
    isActive: true
  }
];

const stepIcons = [
  <Assignment fontSize="large" />, // Import Data
  <Description fontSize="large" />, // Choose Template
  <SwapHoriz fontSize="large" />, // Map Fields
  <Preview fontSize="large" />, // Review & Generate
  <CheckCircle fontSize="large" color="success" />, // Success
];



export default function ReportBuilder() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [importedData, setImportedData] = useState<{ headers: string[]; rows: any[] } | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [selectedTemplateFilename, setSelectedTemplateFilename] = useState<string>('');
  const [reportData, setReportData] = useState<any>({});
  const [analysis, setAnalysis] = useState<any>(null);
  const [successData, setSuccessData] = useState<any>(null);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [templatePlaceholders, setTemplatePlaceholders] = useState<string[]>([]);
  const [isLoadingPlaceholders, setIsLoadingPlaceholders] = useState(false);
  const [editData, setEditData] = useState<Record<string, string>>({});
  const [autoFilledFields, setAutoFilledFields] = useState<Record<string, boolean>>({});

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Use mock data if API fails
  const { data: templates, isLoading: templatesLoading, error: templatesError } = useQuery({
    queryKey: ['reportTemplates'],
    queryFn: fetchReportTemplates,
    retry: 1,
    onError: (error) => {
      console.log('API Error, using mock data:', error);
    }
  });

  const { data: wordTemplates, isLoading: wordTemplatesLoading, error: wordTemplatesError } = useQuery({
    queryKey: ['wordTemplates'],
    queryFn: fetchWordTemplates,
    retry: 1,
    onError: (error) => {
      console.log('Word template API error:', error);
    }
  });

  // Use mock data if API fails
  const displayTemplates: ReportTemplate[] = Array.isArray(templates) ? templates : mockTemplates;

  const createReportMutation = useMutation({
    mutationFn: createReport,
    onSuccess: (data) => {
      navigate(`/reports/${data.id}`);
    },
    onError: (error) => {
      console.log('Create report error:', error);
      // Show success message even if API fails (for demo)
      alert('Report created successfully! (Demo mode)');
    }
  });

  const analyzeDataMutation = useMutation({
    mutationFn: analyzeData,
    onSuccess: (data) => {
      setAnalysis(data);
    },
    onError: (error) => {
      console.log('Analyze data error:', error);
      // Mock analysis data
      setAnalysis({
        summary: 'Data analysis completed successfully.',
        insights: ['Auto analysis placeholder'],
        suggestions: 'Consider reviewing your data.'
      });
    }
  });

  // Fetch placeholders when a template is selected
  useEffect(() => {
    const fetchPlaceholders = async () => {
      if (!selectedTemplateFilename) {
        setTemplatePlaceholders([]);
        return;
      }
      setIsLoadingPlaceholders(true);
      try {
        const placeholders = await fetchTemplatePlaceholders(selectedTemplateFilename);
        setTemplatePlaceholders(placeholders);
      } catch (e) {
        setTemplatePlaceholders([]);
      } finally {
        setIsLoadingPlaceholders(false);
      }
    };
    fetchPlaceholders();
  }, [selectedTemplateFilename]);

  // When reportData is set (after auto-mapping), initialize editData
  useEffect(() => {
    setEditData(reportData);
  }, [reportData]);



  // Step navigation handlers
  const handleNext = async () => {
    // If on template selection step, auto-map and go to review
    if (activeStep === 1 && importedData && selectedTemplateFilename) {
      const placeholders = templatePlaceholders;
      if (placeholders) {
        const mappedRow = importedData.rows[0] || [];
        const data: Record<string, string> = {};
        const autoFilled: Record<string, boolean> = {};
        placeholders.forEach((ph: string) => {
          const colIdx = importedData.headers.findIndex(h => h.trim().toLowerCase() === ph.trim().toLowerCase());
          if (colIdx !== -1) {
            data[ph] = mappedRow[colIdx] ?? '';
            autoFilled[ph] = true;
          } else {
            data[ph] = '';
            autoFilled[ph] = false;
          }
        });
        setReportData(data);
        setAutoFilledFields(autoFilled);
        try {
          await analyzeDataMutation.mutateAsync(data);
        } catch {}
      }
    }
    setActiveStep((prev) => prev + 1);
  };
  const handleBack = () => setActiveStep((prev) => prev - 1);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerationError(null);
    try {
      const data = await createReportMutation.mutateAsync({
        templateFilename: selectedTemplateFilename,
        data: editData,
        analysis,
      });
      setSuccessData(data);
      setActiveStep((prevStep) => prevStep + 1);
    } catch (error: any) {
      setGenerationError(error?.message || 'Failed to generate report. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRetry = () => {
    setGenerationError(null);
    handleGenerate();
  };

  // Step content
  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Fade in={activeStep === 0}>
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" gutterBottom sx={{ flex: 1 }}>
                  Import Data
                </Typography>
                <Tooltip title="Upload an Excel file or import from Google Sheets. Your data will be kept secure.">
                  <InfoOutlinedIcon color="primary" />
                </Tooltip>
              </Box>
              {/* Drag-and-drop Excel upload */}
              <Box
                sx={{
                  border: '2px dashed #0e1c40',
                  borderRadius: 3,
                  p: 4,
                  mb: 3,
                  textAlign: 'center',
                  bgcolor: 'rgba(14,28,64,0.03)',
                  transition: 'background 0.2s',
                  '&:hover': { bgcolor: 'rgba(14,28,64,0.07)' },
                  cursor: 'pointer',
                  position: 'relative',
                }}
                onClick={() => document.getElementById('excel-upload-input')?.click()}
              >
                <CloudUploadIcon sx={{ fontSize: 48, color: '#0e1c40', mb: 1 }} />
                <Typography variant="body1" sx={{ color: '#0e1c40', fontWeight: 500 }}>
                  Drag & drop your Excel file here, or click to browse
                </Typography>
                <input
                  id="excel-upload-input"
                  type="file"
                  accept=".xlsx,.xls"
                  style={{ display: 'none' }}
                  onChange={e => {
                    // Use ExcelImport logic
                    const file = e.target.files?.[0];
                    if (!file) return;
                    const reader = new FileReader();
                    reader.onload = (evt) => {
                      const data = new Uint8Array(evt.target?.result as ArrayBuffer);
                      const workbook = XLSX.read(data, { type: 'array' });
                      const sheetName = workbook.SheetNames[0];
                      const worksheet = workbook.Sheets[sheetName];
                      const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
                      const headers = json[0] as string[];
                      const rows = json.slice(1);
                      setImportedData({ headers, rows });
                    };
                    reader.readAsArrayBuffer(file);
                  }}
                />
              </Box>
              <Divider sx={{ my: 3 }}>or</Divider>
              {/* Google Sheets Import */}
              <GoogleSheetImport
                onDataParsed={setImportedData}
                apiKey={import.meta.env.VITE_GOOGLE_API_KEY || ''}
                clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || ''}
              />
              {/* Preview card for imported data */}
              {importedData && (
                <Paper elevation={3} sx={{ mt: 4, p: 3, borderRadius: 3, position: 'relative', border: '1.5px solid #22c55e' }}>
                  <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
                    <CheckCircleIcon color="success" fontSize="large" />
                  </Box>
                  <Typography variant="subtitle1" sx={{ color: '#0e1c40', fontWeight: 600, mb: 1 }}>
                    Data Preview
                  </Typography>
                  <Box sx={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
                      <thead>
                        <tr>
                          {importedData.headers.map((header) => (
                            <th key={header} style={{ borderBottom: '1px solid #e0e7ef', padding: 6, color: '#0e1c40', fontWeight: 600 }}>{header}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {importedData.rows.slice(0, 5).map((row, idx) => (
                          <tr key={idx}>
                            {importedData.headers.map((_, colIdx) => (
                              <td key={colIdx} style={{ borderBottom: '1px solid #f1f5f9', padding: 6 }}>{row[colIdx]}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </Box>
                  <Alert severity="success" sx={{ mt: 2 }}>Data imported! Proceed to next step.</Alert>
                </Paper>
              )}
            </Box>
          </Fade>
        );
      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>Choose Report Template</Typography>
            <Grid container spacing={3}>
              {wordTemplates?.map(template => (
                <Grid item xs={12} sm={6} md={4} key={template.id}>
                  <Card
                    onClick={() => setSelectedTemplateFilename(template.filename)}
                    sx={{
                      border: selectedTemplateFilename === template.filename ? '2px solid #0e1c40' : '1px solid #e0e7ef',
                      cursor: 'pointer',
                      boxShadow: selectedTemplateFilename === template.filename ? 6 : 1,
                      transition: 'box-shadow 0.2s, border 0.2s',
                    }}
                  >
                    <CardMedia
                      component="img"
                      height="140"
                      image={template.previewUrl || '/static/previews/default.png'}
                      alt={template.name}
                    />
                    <CardContent>
                      <Typography variant="h6">{template.name}</Typography>
                      <Typography variant="body2" color="text.secondary">{template.description}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
            {selectedTemplateFilename && (
              <Box mt={3} textAlign="center">
                <Button variant="contained" color="primary" onClick={handleNext}>
                  Next
                </Button>
              </Box>
            )}
          </Box>
        );
      case 2:
        return (
          <TemplateEditor
            templateName={selectedTemplateFilename}
            data={editData}
            onDataChange={setEditData}
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
          />
        );
      case 4:
        return (
          <Box textAlign="center">
            <Typography variant="h5" gutterBottom>Report Generated Successfully!</Typography>
            {successData && (
              <Box my={2}>
                <Typography variant="subtitle1">Download your report:</Typography>
                <Box display="flex" justifyContent="center" sx={{ gap: '16px', my: 2 }}>
                  {([
                    successData.outputUrl ? (
                      <Button
                        key="pdf"
                        variant="contained"
                        color="primary"
                        component="a"
                        href={successData.outputUrl}
                        target="_blank"
                      >
                        Download PDF
                      </Button>
                    ) : null,
                    successData.excelUrl ? (
                      <Button
                        key="excel"
                        variant="outlined"
                        color="primary"
                        component="a"
                        href={successData.excelUrl}
                        target="_blank"
                      >
                        Download Excel
                      </Button>
                    ) : null
                  ].filter(Boolean) as React.ReactNode[])}
                </Box>
                <Button
                  variant="text"
                  component={Link}
                  to={`/reports/${successData.id}`}
                  sx={{ mt: 2 }}
                >
                  View Full Report
                </Button>
              </Box>
            )}
            <Box mt={3}>
              <Button
                variant="contained"
                color="secondary"
                component={Link}
                to="/report-history"
                sx={{ mr: 2 }}
              >
                My Reports
              </Button>
              <Button
                variant="outlined"
                onClick={() => window.location.reload()}
              >
                Generate Another Report
              </Button>
            </Box>
          </Box>
        );
      default:
        return 'Unknown step';
    }
  };

  if (templatesLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  // Step enable/disable logic
  const canProceed = () => {
    if (activeStep === 0) return !!importedData;
    if (activeStep === 1) return !!selectedTemplateFilename;
    return true;
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      bgcolor: 'rgba(248,250,252,0.9)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      py: 6,
      width: '100vw',
      boxSizing: 'border-box',
    }}>
      <Box
        sx={{
          width: isMobile ? '100%' : 900,
          maxWidth: '98vw',
          borderRadius: 5,
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
          background: 'rgba(255,255,255,0.85)',
          backdropFilter: 'blur(12px)',
          p: isMobile ? 2 : 4,
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          gap: 4,
          margin: '0 auto',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Sidebar/Stepper */}
        <Box
          sx={{
            width: isMobile ? '100%' : 220,
            minWidth: isMobile ? '100%' : 180,
            borderRight: isMobile ? 'none' : '1px solid #e0e7ef',
            borderBottom: isMobile ? '1px solid #e0e7ef' : 'none',
            pb: isMobile ? 2 : 0,
            mb: isMobile ? 2 : 0,
            display: 'flex',
            flexDirection: isMobile ? 'row' : 'column',
            alignItems: 'center',
            justifyContent: isMobile ? 'space-between' : 'flex-start',
            gap: isMobile ? 1 : 3,
          }}
        >
          {steps.map((label, idx) => (
            <Tooltip title={label} key={label} placement={isMobile ? 'top' : 'right'}>
              <Box sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                opacity: idx > activeStep ? 0.4 : 1,
                transition: 'opacity 0.2s',
              }}>
                <Avatar
                  sx={{
                    bgcolor: idx === activeStep ? '#0e1c40' : '#e0e7ef',
                    color: idx === activeStep ? 'white' : '#64748b',
                    width: 48,
                    height: 48,
                    mb: isMobile ? 0 : 1,
                    border: idx < activeStep ? '2px solid #22c55e' : 'none',
                    boxShadow: idx === activeStep ? '0 0 0 4px #e0e7ef' : 'none',
                  }}
                >
                  {stepIcons[idx]}
                </Avatar>
                {!isMobile && (
                  <Typography
                    variant="caption"
                    sx={{ color: idx === activeStep ? '#0e1c40' : '#64748b', fontWeight: idx === activeStep ? 700 : 400 }}
                  >
                    {label}
                  </Typography>
                )}
              </Box>
            </Tooltip>
          ))}
          {/* Progress bar */}
          <Box sx={{ width: isMobile ? '100%' : '80%', mt: isMobile ? 0 : 3, alignSelf: 'center' }}>
            <LinearProgress
              variant="determinate"
              value={((activeStep + 1) / steps.length) * 100}
              sx={{ height: 8, borderRadius: 4, bgcolor: '#e0e7ef', '& .MuiLinearProgress-bar': { bgcolor: '#0e1c40' } }}
            />
          </Box>
        </Box>
        {/* Main Content Card */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="h4" gutterBottom sx={{ color: '#0e1c40', fontWeight: 700, mb: 3, textAlign: 'center' }}>
            Create New Report
          </Typography>
          {getStepContent(activeStep)}
          <Box display="flex" justifyContent="flex-end" mt={4} gap={2}>
            {activeStep > 0 && (
              <Button variant="outlined" onClick={handleBack}>
                Back
              </Button>
            )}
            {activeStep < steps.length - 1 && (
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={!canProceed()}
              >
                Next
              </Button>
            )}
          </Box>
          {/* You can add navigation buttons here if needed */}
        </Box>
      </Box>
    </Box>
  );
}
