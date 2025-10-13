import React from "react";
import { useState, useEffect, useContext } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AuthContext } from "../../context/AuthContext";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Tabs,
  Tab,
  Badge,
  Tooltip,
  Fab,
  CircularProgress,
} from '@mui/material';
import {
  PlayArrow,
  Download,
  Visibility,
  Edit,
  Delete,
  Refresh,
  Schedule,
  Analytics,
  Assessment,
  TrendingUp,
  Timeline,
  BarChart,
  PieChart,
  Description,
  CloudDownload,
  CheckCircle,
  Error,
  Pending,
  Stop,
} from '@mui/icons-material';
import { formBuilderAPI } from "../../services/formBuilder";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`automated-reports-tabpanel-${index}`}
      aria-labelledby={`automated-reports-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

interface AutomatedReport {
  id: number;
  title: string;
  description: string;
  form_id: number;
  form_title: string;
  report_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  output_url?: string;
  task_id?: string;
  analysis?: any;
  submissions_count?: number;
  date_range?: string;
}

interface Form {
  id: number;
  title: string;
  description?: string;
  submission_count: number;
  form_settings?: {
    auto_generate_reports?: boolean;
    report_schedule?: string;
  };
}

export default function AutomatedReports() {
  const { user, accessToken } = useContext(AuthContext);
  const queryClient = useQueryClient();
  
  const [tabValue, setTabValue] = useState(0);
  const [selectedReport, setSelectedReport] = useState<AutomatedReport | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'warning' | 'info',
  });

  // Form for generating new reports
  const [reportForm, setReportForm] = useState({
    form_id: '',
    report_type: 'summary',
    date_range: 'last_30_days',
  });

  // Mock forms for demonstration
  const mockForms = [
    {
      id: 1,
      title: "Employee Satisfaction Survey",
      description: "Quarterly employee feedback and satisfaction survey",
      submission_count: 45,
      is_active: true,
      created_at: "2024-01-01T00:00:00Z"
    },
    {
      id: 2,
      title: "Customer Feedback Form",
      description: "Customer experience and product feedback collection",
      submission_count: 128,
      is_active: true,
      created_at: "2024-01-05T00:00:00Z"
    },
    {
      id: 3,
      title: "IT Support Request",
      description: "Technical support and issue reporting form",
      submission_count: 67,
      is_active: true,
      created_at: "2024-01-10T00:00:00Z"
    },
    {
      id: 4,
      title: "Event Registration",
      description: "Conference and workshop registration form",
      submission_count: 89,
      is_active: true,
      created_at: "2024-01-12T00:00:00Z"
    }
  ];

  // Fetch forms for dropdown
  const { data: formsData, isLoading: formsLoading } = useQuery({
    queryKey: ['forms'],
    queryFn: async () => {
      try {
        const response = await formBuilderAPI.getForms({ page: 1, limit: 100 });
        return response;
      } catch (error) {
        console.error('Error fetching forms:', error);
        // Return mock data if API fails
        return { forms: mockForms };
      }
    },
    enabled: !!accessToken,
  });

  // Fetch automated reports
  const { data: reportsData, isLoading: reportsLoading, refetch: refetchReports } = useQuery({
    queryKey: ['automated-reports'],
    queryFn: async () => {
      const response = await fetch('/api/reports/automated', {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });
      if (!response.ok) throw Error('Failed to fetch reports');
      return response.json();
    },
    enabled: !!accessToken,
  });

  // Generate report mutation
  const generateReportMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await fetch('/api/reports/automated/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw Error('Failed to generate report');
      return response.json();
    },
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: 'Report generation started successfully',
        severity: 'success',
      });
      setGenerateDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['automated-reports'] });
    },
    onError: (error: any) => {
      setSnackbar({
        open: true,
        message: `Failed to generate report: ${error.message}`,
        severity: 'error',
      });
    },
  });

  // Check report status
  const checkReportStatus = async (taskId: string) => {
    try {
      const response = await fetch(`/api/reports/automated/status/${taskId}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });
      if (!response.ok) throw Error('Failed to check status');
      return response.json();
    } catch (error) {
      console.error('Error checking report status:', error);
      return null;
    }
  };

  // Poll for status updates
  useEffect(() => {
    const interval = setInterval(() => {
      if (reportsData?.reports) {
        const pendingReports = reportsData.reports.filter(
          (report: AutomatedReport) => 
            report.status === 'pending' || report.status === 'processing'
        );
        
        if (pendingReports.length > 0) {
          refetchReports();
        }
      }
    }, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, [reportsData, refetchReports]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleGenerateReport = () => {
    if (!reportForm.form_id) {
      setSnackbar({
        open: true,
        message: 'Please select a form',
        severity: 'warning',
      });
      return;
    }

    generateReportMutation.mutate({
      form_id: parseInt(reportForm.form_id),
      report_type: reportForm.report_type,
      date_range: reportForm.date_range,
    });
  };

  const handleDownloadReport = async (report: AutomatedReport) => {
    if (!report.output_url) {
      setSnackbar({
        open: true,
        message: 'Report not ready for download',
        severity: 'warning',
      });
      return;
    }

    try {
      const response = await fetch(report.output_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${report.title}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to download report',
        severity: 'error',
      });
    }
  };

  const handlePreviewReport = (report: AutomatedReport) => {
    setSelectedReport(report);
    setPreviewDialogOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'info';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle />;
      case 'processing':
        return <CircularProgress size={20} />;
      case 'pending':
        return <Pending />;
      case 'failed':
        return <Error />;
      default:
        return <Pending />;
    }
  };

  const getReportTypeIcon = (type: string) => {
    switch (type) {
      case 'summary':
        return <Assessment />;
      case 'detailed':
        return <Analytics />;
      case 'trends':
        return <TrendingUp />;
      default:
        return <Description />;
    }
  };

  if (!user) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Automated Reports
        </Typography>
        <Alert severity="info">
          Please log in to access automated report generation.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Automated Reports
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Generate AI-powered reports from your form submissions with charts and insights.
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Generated Reports" />
          <Tab label="Generate New Report" />
          <Tab label="Form Settings" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Recent Reports</Typography>
          <Button
            startIcon={<Refresh />}
            onClick={() => refetchReports()}
            disabled={reportsLoading}
          >
            Refresh
          </Button>
        </Box>

        {reportsLoading ? (
          <LinearProgress />
        ) : reportsData?.reports?.length > 0 ? (
          <Grid container spacing={3}>
            {reportsData.reports.map((report: AutomatedReport) => (
              <Grid item xs={12} md={6} lg={4} key={report.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {report.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {report.form_title}
                        </Typography>
                      </Box>
                      <Chip
                        icon={getStatusIcon(report.status)}
                        label={report.status}
                        color={getStatusColor(report.status) as any}
                        size="small"
                      />
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {getReportTypeIcon(report.report_type)}
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {report.report_type.charAt(0).toUpperCase() + report.report_type.slice(1)} Report
                      </Typography>
                    </Box>

                    {report.submissions_count && (
                      <Typography variant="body2" color="text.secondary">
                        {report.submissions_count} submissions analyzed
                      </Typography>
                    )}

                    {report.date_range && (
                      <Typography variant="body2" color="text.secondary">
                        {report.date_range}
                      </Typography>
                    )}

                    <Typography variant="caption" color="text.secondary">
                      Generated: {new Date(report.created_at).toLocaleDateString()}
                    </Typography>
                  </CardContent>

                  <CardActions>
                    {report.status === 'completed' && (
                      <>
                        <Button
                          size="small"
                          startIcon={<Visibility />}
                          onClick={() => handlePreviewReport(report)}
                        >
                          Preview
                        </Button>
                        <Button
                          size="small"
                          startIcon={<Download />}
                          onClick={() => handleDownloadReport(report)}
                        >
                          Download
                        </Button>
                      </>
                    )}
                    {report.status === 'processing' && (
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CircularProgress size={16} sx={{ mr: 1 }} />
                        <Typography variant="body2">Processing...</Typography>
                      </Box>
                    )}
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No reports generated yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Generate your first automated report to get started.
            </Typography>
          </Paper>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Generate New Report
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Select a form and configure report settings to generate an AI-powered analysis.
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Select Form</InputLabel>
                  <Select
                    value={reportForm.form_id}
                    onChange={(e: any) => setReportForm({ ...reportForm, form_id: e.target.value })}
                    disabled={formsLoading}
                  >
                    {formsData?.forms?.map((form: Form) => (
                      <MenuItem key={form.id} value={form.id}>
                        {form.title} ({form.submission_count} submissions)
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Report Type</InputLabel>
                  <Select
                    value={reportForm.report_type}
                    onChange={(e: any) => setReportForm({ ...reportForm, report_type: e.target.value })}
                  >
                    <MenuItem value="summary">Summary Report</MenuItem>
                    <MenuItem value="detailed">Detailed Analysis</MenuItem>
                    <MenuItem value="trends">Trends Report</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Date Range</InputLabel>
                  <Select
                    value={reportForm.date_range}
                    onChange={(e: any) => setReportForm({ ...reportForm, date_range: e.target.value })}
                  >
                    <MenuItem value="last_7_days">Last 7 Days</MenuItem>
                    <MenuItem value="last_30_days">Last 30 Days</MenuItem>
                    <MenuItem value="last_90_days">Last 90 Days</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={handleGenerateReport}
                disabled={generateReportMutation.isPending || !reportForm.form_id}
              >
                {generateReportMutation.isPending ? 'Generating...' : 'Generate Report'}
              </Button>
              <Button
                variant="outlined"
                onClick={() => setReportForm({
                  form_id: '',
                  report_type: 'summary',
                  date_range: 'last_30_days',
                })}
              >
                Reset
              </Button>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" gutterBottom>
          Form Automation Settings
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Configure forms to automatically generate reports when new submissions are received.
        </Typography>

        {formsLoading ? (
          <LinearProgress />
        ) : (
          <Grid container spacing={3}>
            {formsData?.forms?.map((form: Form) => (
              <Grid item xs={12} md={6} key={form.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {form.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {form.description || 'No description'}
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Chip
                        label={`${form.submission_count} submissions`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </Box>

                    <Typography variant="body2" color="text.secondary">
                      Auto-reports: {form.form_settings?.auto_generate_reports ? 'Enabled' : 'Disabled'}
                    </Typography>
                    {form.form_settings?.report_schedule && (
                      <Typography variant="body2" color="text.secondary">
                        Schedule: {form.form_settings.report_schedule}
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Report Preview Dialog */}
      <Dialog
        open={previewDialogOpen}
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Report Preview: {selectedReport?.title}
        </DialogTitle>
        <DialogContent>
          {selectedReport?.analysis ? (
            <Box>
              <Typography variant="h6" gutterBottom>
                Executive Summary
              </Typography>
              <Typography variant="body2" paragraph>
                {selectedReport.analysis.summary}
              </Typography>

              {selectedReport.analysis.insights && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Key Insights
                  </Typography>
                  <List dense>
                    {selectedReport.analysis.insights.map((insight: string, index: number) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckCircle color="success" />
                        </ListItemIcon>
                        <ListItemText primary={insight} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}

              {selectedReport.analysis.recommendations && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Recommendations
                  </Typography>
                  <List dense>
                    {selectedReport.analysis.recommendations.map((rec: string, index: number) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <TrendingUp color="primary" />
                        </ListItemIcon>
                        <ListItemText primary={rec} />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}

              {selectedReport.analysis.charts && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Generated Charts
                  </Typography>
                  <Grid container spacing={2}>
                    {Object.entries(selectedReport.analysis.charts).map(([name, path]) => (
                      <Grid item xs={12} md={6} key={name}>
                        <img
                          src={path as string}
                          alt={name}
                          style={{ width: '100%', height: 'auto' }}
                        />
                      </Grid>
                    ))}
                  </Grid>
                </>
              )}
            </Box>
          ) : (
            <Typography>No preview available for this report.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
          {selectedReport?.output_url && (
            <Button
              startIcon={<Download />}
              onClick={() => handleDownloadReport(selectedReport)}
            >
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Floating Action Button for quick report generation */}
      <Fab
        color="primary"
        aria-label="generate report"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => setTabValue(1)}
      >
        <PlayArrow />
      </Fab>
    </Box>
  );
} 