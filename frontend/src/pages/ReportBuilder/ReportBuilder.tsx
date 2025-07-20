import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Box,
  Button,
  Typography,
  Paper,
  CircularProgress,
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
} from '@mui/material';
// Removed unused react-hook-form imports
import {
  fetchReportTemplates,
  createReport,
  analyzeData,
  fetchTemplatePlaceholders,
  fetchWordTemplates,
  generateReport,
  downloadReport,
} from '../../services/api';
import type { ReportTemplate } from '../../services/api';
import GoogleSheetImport from './GoogleSheetImport';
import TemplateEditor from './TemplateEditor';
import FieldMapping from './FieldMapping';
import { Assignment, Description, SwapHoriz, Preview, CheckCircle } from '@mui/icons-material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { Divider, Fade } from '@mui/material';
import * as XLSX from 'xlsx';
import DownloadIcon from '@mui/icons-material/Download';

const steps = ['Import Data', 'Choose Template', 'Map Fields', 'Review & Generate', 'Success'];

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
  const [importedData, setImportedData] = useState<{ headers: string[]; rows: any[]; processedData: Record<string, any> } | null>(null);
  // Removed unused mapping state
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
  const [fieldMapping, setFieldMapping] = useState<Record<string, string>>({});

  // Enhanced Excel upload handler
  const handleExcelUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const data = new Uint8Array(evt.target?.result as ArrayBuffer);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const json = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
        
        if (json.length === 0) {
          alert('Excel file appears to be empty');
          return;
        }
        
        const headers = json[0] as string[];
        const rows = json.slice(1).filter((row: any) => Array.isArray(row) && row.length > 0); // Filter empty rows
        
        // Process data for intelligent field mapping
        const processedData = processExcelData(headers, rows);
        
        setImportedData({ headers, rows, processedData });
        
        // Auto-populate editData with processed values
        const autoMappedData: Record<string, string> = {};
        Object.keys(processedData).forEach(key => {
          if (processedData[key] !== null && processedData[key] !== undefined) {
            autoMappedData[key] = String(processedData[key]);
          }
        });
        
        setEditData(prev => ({ ...prev, ...autoMappedData }));
        
      } catch (error) {
        console.error('Error processing Excel file:', error);
        alert('Error processing Excel file. Please check the file format.');
      }
    };
    reader.readAsArrayBuffer(file);
  };
  
  // Process Excel data to extract meaningful information
  const processExcelData = (headers: string[], rows: any[]): Record<string, any> => {
    console.log('Processing Excel data...');
    console.log('Headers:', headers);
    console.log('Number of rows:', rows.length);
    console.log('First few rows:', rows.slice(0, 3));
    
    const processed: Record<string, any> = {};
    
    // Enhanced field mappings for the specific template placeholders
    const fieldMappings: Record<string, string[]> = {
      // Template-specific mappings
      'nama_peserta': ['nama', 'peserta', 'name', 'participant', 'nama peserta', 'participant name'],
      'PROGRAM_TITLE': ['program', 'title', 'judul', 'program title', 'nama program', 'program name'],
      'LOCATION_MAIN': ['location', 'lokasi', 'place', 'tempat', 'venue', 'alamat'],
      'Time': ['time', 'waktu', 'jam', 'tanggal', 'date', 'schedule'],
      'Place1': ['place', 'tempat', 'location', 'lokasi', 'venue'],
      'bannering': ['banner', 'bannering', 'promosi', 'promotion'],
      'Signature_Consultant': ['signature', 'consultant', 'konsultan', 'tanda tangan'],
      'Image2': ['image', 'gambar', 'photo', 'foto'],
      'Image4': ['image', 'gambar', 'photo', 'foto'],
      'Image7': ['image', 'gambar', 'photo', 'foto'],
      
      // Generic mappings for common fields
      'company_name': ['company', 'company name', 'organization', 'business name', 'perusahaan'],
      'revenue': ['revenue', 'total revenue', 'sales', 'income', 'turnover', 'pendapatan'],
      'expenses': ['expenses', 'total expenses', 'costs', 'expenditure', 'biaya'],
      'profit': ['profit', 'net profit', 'earnings', 'net income', 'keuntungan'],
      'date': ['date', 'report date', 'period', 'month', 'year', 'tanggal'],
      'quarter': ['quarter', 'q1', 'q2', 'q3', 'q4', 'period', 'kuartal'],
      'department': ['department', 'division', 'team', 'unit', 'departemen'],
      'manager': ['manager', 'supervisor', 'lead', 'director', 'manajer'],
      'total': ['total', 'sum', 'amount', 'value', 'jumlah'],
      'percentage': ['percentage', 'percent', '%', 'rate', 'persentase'],
      'count': ['count', 'number', 'quantity', 'qty', 'jumlah'],
      'average': ['average', 'avg', 'mean', 'rata-rata']
    };
    
    // Try to map headers to common fields
    headers.forEach((header, index) => {
      const normalizedHeader = header.toLowerCase().trim();
      console.log(`Processing header: "${header}" (normalized: "${normalizedHeader}")`);
      
      // Find matching field
      for (const [field, patterns] of Object.entries(fieldMappings)) {
        if (patterns.some(pattern => normalizedHeader.includes(pattern))) {
          console.log(`Found match for "${header}" -> "${field}"`);
          
          // Get the most common non-empty value from this column
          const columnValues = rows.map(row => row[index]).filter(val => val !== null && val !== undefined && val !== '');
          console.log(`Column values for "${header}":`, columnValues.slice(0, 5));
          
          if (columnValues.length > 0) {
            // For numeric fields, try to sum or average
            if (['revenue', 'expenses', 'profit', 'total'].includes(field)) {
              const numericValues = columnValues.map(val => parseFloat(String(val))).filter(val => !isNaN(val));
              if (numericValues.length > 0) {
                processed[field] = numericValues.reduce((sum, val) => sum + val, 0);
                console.log(`Calculated sum for "${field}":`, processed[field]);
              }
            } else if (field === 'average') {
              const numericValues = columnValues.map(val => parseFloat(String(val))).filter(val => !isNaN(val));
              if (numericValues.length > 0) {
                processed[field] = numericValues.reduce((sum, val) => sum + val, 0) / numericValues.length;
                console.log(`Calculated average for "${field}":`, processed[field]);
              }
            } else {
              // For text fields, use the first non-empty value
              processed[field] = columnValues[0];
              console.log(`Set text value for "${field}":`, processed[field]);
            }
          }
          break;
        }
      }
    });
    
    // If no specific mappings found, create generic mappings for all headers
    if (Object.keys(processed).length === 0) {
      console.log('No specific mappings found, creating generic mappings...');
      headers.forEach((header, index) => {
        const normalizedHeader = header.toLowerCase().replace(/[^a-z0-9]/g, '_');
        const columnValues = rows.map(row => row[index]).filter(val => val !== null && val !== undefined && val !== '');
        
        if (columnValues.length > 0) {
          // Try to determine if it's numeric
          const numericValues = columnValues.map(val => parseFloat(String(val))).filter(val => !isNaN(val));
          if (numericValues.length > columnValues.length * 0.5) {
            // Mostly numeric, calculate sum
            processed[normalizedHeader] = numericValues.reduce((sum, val) => sum + val, 0);
          } else {
            // Text field, use first value
            processed[normalizedHeader] = columnValues[0];
          }
          console.log(`Created generic mapping for "${header}" -> "${normalizedHeader}":`, processed[normalizedHeader]);
        }
      });
    }
    
    // Add summary statistics
    if (rows.length > 0) {
      processed['total_rows'] = rows.length;
      processed['data_source'] = 'Excel Import';
      processed['import_date'] = new Date().toLocaleDateString();
    }
    
    console.log('Final processed data:', processed);
    return processed;
  };

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Use mock data if API fails
  const { data: templatesData, isLoading: templatesLoading } = useQuery({
    queryKey: ['reportTemplates'],
    queryFn: fetchReportTemplates,
  });

  const { data: wordTemplatesData } = useQuery({
    queryKey: ['wordTemplates'],
    queryFn: fetchWordTemplates,
  });

  // Use mock data if API fails
  const displayTemplates: ReportTemplate[] = Array.isArray(templatesData) ? templatesData : mockTemplates;

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
        const response = await fetchTemplatePlaceholders(selectedTemplateFilename);
        setTemplatePlaceholders(response);
      } catch (error) {
        console.error('Failed to fetch template placeholders:', error);
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
    if (activeStep === 1) {
      // Template placeholders are already fetched via useEffect when template is selected
      // No need to fetch again here
    }
    
    if (activeStep === 2) {
      // Process field mapping data
      const mappedData: Record<string, string> = {};
      
      // Apply field mapping to imported data
      if (importedData && fieldMapping) {
        Object.entries(fieldMapping).forEach(([excelHeader, placeholder]) => {
          const headerIndex = importedData.headers.indexOf(excelHeader);
          if (headerIndex !== -1) {
            // Get the first non-empty value from this column
            const columnValues = importedData.rows
              .map(row => row[headerIndex])
              .filter(val => val !== null && val !== undefined && val !== '');
            
            if (columnValues.length > 0) {
              mappedData[placeholder] = String(columnValues[0]);
            }
          }
        });
      }
      
      // Merge with existing editData
      setEditData(prev => ({ ...prev, ...mappedData }));
    }
    
    setActiveStep((prev) => prev + 1);
  };
  const handleBack = () => setActiveStep((prev) => prev - 1);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerationError(null);
    try {
      const result = await generateReport(selectedTemplateFilename, editData);
      setSuccessData({
        downloadUrl: result.downloadUrl,
        message: result.message
      });
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
                  onChange={handleExcelUpload}
                />
              </Box>
              <Divider sx={{ my: 3 }}>or</Divider>
              {/* Google Sheets Import */}
              <GoogleSheetImport
                onDataParsed={(data) => setImportedData({ ...data, processedData: processExcelData(data.headers, data.rows) })}
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
              {wordTemplatesData?.map((template: any) => (
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
          <FieldMapping
            excelHeaders={importedData?.headers || []}
            templatePlaceholders={templatePlaceholders}
            currentMapping={fieldMapping}
            onMappingChange={setFieldMapping}
          />
        );
      case 3:
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
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => downloadReport(successData.downloadUrl)}
                    startIcon={<DownloadIcon />}
                  >
                    Download Report
                  </Button>
                  <Button
                    variant="outlined"
                    color="primary"
                    component="a"
                    href={successData.downloadUrl}
                    target="_blank"
                  >
                    Open in New Tab
                  </Button>
                </Box>
                <Alert severity="success" sx={{ mt: 2 }}>
                  {successData.message || 'Your report has been generated successfully!'}
                </Alert>
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
    if (activeStep === 2) return Object.keys(fieldMapping).length > 0; // At least one field mapped
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
