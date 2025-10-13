import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
  Paper,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  ListItemIcon,
  Chip,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Google as GoogleIcon,
  Description as DescriptionIcon,
  TableChart as TableChartIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Assessment as AssessmentIcon,
  CloudDownload as CloudDownloadIcon,
} from '@mui/icons-material';
import FormDataExporter from './FormDataExporter';
import GoogleFormsExporter from './GoogleFormsExporter';
import { formBuilderAPI, type Form } from '../services/formBuilder';

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
      id={`export-tabpanel-${index}`}
      aria-labelledby={`export-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const FormExportDashboard: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [localForms, setLocalForms] = useState<Form[]>([]);
  const [selectedLocalForm, setSelectedLocalForm] = useState<Form | null>(null);
  const [showLocalFormSelector, setShowLocalFormSelector] = useState(false);
  const [isLoadingLocalForms, setIsLoadingLocalForms] = useState(false);
  const [googleFormsStatus, setGoogleFormsStatus] = useState<any>(null);

  useEffect(() => {
    loadLocalForms();
    checkGoogleFormsStatus();
  }, []);

  const loadLocalForms = async () => {
    setIsLoadingLocalForms(true);
    try {
      const response = await formBuilderAPI.getAllForms();
      if (response.success) {
        setLocalForms(response.forms || []);
      }
    } catch (error) {
      console.error('Error loading local forms:', error);
    } finally {
      setIsLoadingLocalForms(false);
    }
  };

  const checkGoogleFormsStatus = async () => {
    try {
      const status = await formBuilderAPI.getGoogleFormsStatus();
      setGoogleFormsStatus(status);
    } catch (error) {
      console.error('Error checking Google Forms status:', error);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleLocalFormSelect = (form: Form) => {
    setSelectedLocalForm(form);
    setShowLocalFormSelector(false);
  };

  const getStatusChip = (form: Form) => {
    if (form.submission_count === 0) {
      return <Chip label="No submissions" size="small" color="default" />;
    } else if (form.submission_count < 10) {
      return <Chip label={`${form.submission_count} submissions`} size="small" color="warning" />;
    } else {
      return <Chip label={`${form.submission_count} submissions`} size="small" color="success" />;
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 1200, mx: 'auto', p: 2 }}>
      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <CloudDownloadIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
            <Box>
              <Typography variant="h4" component="h1">
                Form Data Export Center
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Export your form data to Excel with professional formatting and analytics
              </Typography>
            </Box>
          </Box>

          {/* Quick Stats */}
          <Grid container spacing={2} mt={2}>
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h6" color="primary">
                  {localForms.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Local Forms
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h6" color="secondary">
                  {googleFormsStatus?.forms_count || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Google Forms
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h6" color="success.main">
                  Excel
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Export Format
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Main Export Interface */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange} aria-label="export tabs">
            <Tab
              label="Local Forms"
              icon={<DescriptionIcon />}
              iconPosition="start"
              id="export-tab-0"
              aria-controls="export-tabpanel-0"
            />
            <Tab
              label="Google Forms"
              icon={<GoogleIcon />}
              iconPosition="start"
              id="export-tab-1"
              aria-controls="export-tabpanel-1"
            />
          </Tabs>
        </Box>

        {/* Local Forms Export */}
        <TabPanel value={currentTab} index={0}>
          {localForms.length === 0 ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="h6" gutterBottom>No Local Forms Found</Typography>
              <Typography variant="body2">
                You haven't created any forms yet. Create a form first to export its data.
              </Typography>
              <Button variant="outlined" sx={{ mt: 2 }} onClick={() => window.location.href = '/forms'}>
                Create New Form
              </Button>
            </Alert>
          ) : !selectedLocalForm ? (
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Select a Local Form to Export</Typography>
                <Button
                  startIcon={<RefreshIcon />}
                  onClick={loadLocalForms}
                  disabled={isLoadingLocalForms}
                >
                  Refresh
                </Button>
              </Box>

              <Grid container spacing={2}>
                {localForms.map((form) => (
                  <Grid item xs={12} sm={6} md={4} key={form.id}>
                    <Card
                      variant="outlined"
                      sx={{
                        cursor: 'pointer',
                        '&:hover': { boxShadow: 2 },
                        transition: 'box-shadow 0.2s'
                      }}
                      onClick={() => handleLocalFormSelect(form)}
                    >
                      <CardContent>
                        <Box display="flex" alignItems="start" justifyContent="space-between" mb={1}>
                          <DescriptionIcon color="primary" />
                          <Tooltip title="Export to Excel">
                            <IconButton size="small">
                              <TableChartIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                        <Typography variant="h6" gutterBottom noWrap>
                          {form.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 40 }}>
                          {form.description || 'No description'}
                        </Typography>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          {getStatusChip(form)}
                          <Typography variant="caption" color="text.secondary">
                            {form.is_active ? 'Active' : 'Inactive'}
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          ) : (
            <Box>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Export: {selectedLocalForm.title}
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => setSelectedLocalForm(null)}
                >
                  Change Form
                </Button>
              </Box>

              <FormDataExporter
                form={selectedLocalForm}
                formType="local"
                onExportComplete={(result) => {
                  console.log('Local form export completed:', result);
                }}
              />
            </Box>
          )}
        </TabPanel>

        {/* Google Forms Export */}
        <TabPanel value={currentTab} index={1}>
          <GoogleFormsExporter />
        </TabPanel>
      </Card>

      {/* Help Section */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <InfoIcon sx={{ mr: 1, color: 'info.main' }} />
            <Typography variant="h6">Export Features</Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" gutterBottom>Local Forms</Typography>
              <Typography variant="body2" color="text.secondary">
                • Export form submissions from your internal forms<br/>
                • Filter by date range and submission status<br/>
                • Include form schema and metadata<br/>
                • Professional Excel formatting
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" gutterBottom>Google Forms</Typography>
              <Typography variant="body2" color="text.secondary">
                • Connect with Google OAuth authentication<br/>
                • Export responses from any Google Form<br/>
                • Advanced analytics and insights<br/>
                • Multi-sheet Excel with statistics
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default FormExportDashboard;