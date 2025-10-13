import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Container, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  Chip, 
  Tabs,
  Tab,
  Alert,
  Button
} from '@mui/material';
import FormDataExporter from '../../components/FormDataExporter';
import { type Form } from '../../services/formBuilder';

// Sample local form data
const sampleForm: Form = {
  id: 1,
  title: "Employee Performance Survey",
  description: "Annual employee performance evaluation form",
  schema: {
    fields: [
      { id: "name", label: "Full Name", type: "text", required: true, order: 1 },
      { id: "department", label: "Department", type: "select", required: true, order: 2 },
      { id: "rating", label: "Performance Rating", type: "radio", required: true, order: 3 },
      { id: "comments", label: "Additional Comments", type: "textarea", required: false, order: 4 }
    ]
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  creator_id: 1,
  creator_name: "Demo User",
  is_active: true,
  is_public: false,
  submission_count: 45,
  view_count: 0
};

// Sample Google Form data
const sampleGoogleForm: Form = {
  id: 2,
  title: "Customer Feedback Survey",
  description: "Google Forms-based customer satisfaction survey",
  schema: {
    fields: [
      { id: "customer_name", label: "Customer Name", type: "text", required: true, order: 1 },
      { id: "product_rating", label: "Product Rating", type: "radio", required: true, order: 2 },
      { id: "service_quality", label: "Service Quality", type: "select", required: true, order: 3 },
      { id: "feedback", label: "Additional Feedback", type: "textarea", required: false, order: 4 }
    ]
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  creator_id: 1,
  creator_name: "Demo User",
  is_active: true,
  is_public: false,
  submission_count: 128,
  view_count: 0
};

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
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const FormDataExportDemo: React.FC = () => {
  const [exportHistory, setExportHistory] = useState<any[]>([]);
  const [tabValue, setTabValue] = useState(0);

  const handleExportComplete = (result: any) => {
    const exportRecord = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      formType: tabValue === 0 ? 'Local Form' : 'Google Form',
      formTitle: tabValue === 0 ? sampleForm.title : sampleGoogleForm.title,
      result: result,
      status: result.success ? 'success' : 'error'
    };
    
    setExportHistory(prev => [exportRecord, ...prev]);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box textAlign="center" mb={4}>
        <Typography variant="h3" component="h1" gutterBottom>
          🚀 Form Data Export System
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Export your form data to Excel with advanced filtering and professional formatting
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Supports both local forms and Google Forms integration
        </Typography>
      </Box>

      {/* Export Tabs */}
      <Paper sx={{ width: '100%', mb: 4 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="export form types">
            <Tab label="Local Form Export" />
            <Tab label="Google Forms Export" />
          </Tabs>
        </Box>

        {/* Local Form Export Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box mb={3}>
            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>Local Form Export:</strong> Export data from forms created in your system.
            </Alert>
            
            <Box mb={2}>
              <Typography variant="h6" gutterBottom>
                Form: {sampleForm.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {sampleForm.description}
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                <Chip label={`${sampleForm.submission_count} submissions`} color="primary" />
                <Chip label={`${sampleForm.schema.fields.length} fields`} color="secondary" />
                <Chip label="Active" color="success" />
              </Box>
            </Box>
          </Box>
          
          <FormDataExporter 
            form={sampleForm} 
            onExportComplete={handleExportComplete}
            formType="local"
          />
        </TabPanel>

        {/* Google Forms Export Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box mb={3}>
            <Alert severity="success" sx={{ mb: 2 }}>
              <strong>Google Forms Export:</strong> Export data directly from your Google Forms.
            </Alert>
            
            <Box mb={2}>
              <Typography variant="h6" gutterBottom>
                Form: {sampleGoogleForm.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {sampleGoogleForm.description}
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                <Chip label={`${sampleGoogleForm.submission_count} responses`} color="primary" />
                <Chip label={`${sampleGoogleForm.schema.fields.length} questions`} color="secondary" />
                <Chip label="Google Forms" color="info" />
              </Box>
            </Box>
          </Box>
          
          <FormDataExporter 
            form={sampleGoogleForm} 
            onExportComplete={handleExportComplete}
            formType="google"
            googleFormId="sample-google-form-id"
          />
        </TabPanel>
      </Paper>

      {/* Export History */}
      {exportHistory.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h5">
              📋 Export History
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => setExportHistory([])}
            >
              Clear History
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            {exportHistory.slice(0, 10).map((record) => (
              <Grid item xs={12} key={record.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {record.formTitle}
                      </Typography>
                      <Chip 
                        label={record.formType} 
                        color="primary" 
                        size="small" 
                      />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {new Date(record.timestamp).toLocaleString()}
                    </Typography>
                    
                    {record.status === 'success' ? (
                      <Alert severity="success" sx={{ mt: 1 }}>
                        {record.result.message}
                        {record.result.responses_count && (
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            <strong>Responses:</strong> {record.result.responses_count}
                          </Typography>
                        )}
                        {record.result.submissions_count && (
                          <Typography variant="body2" sx={{ mt: 1 }}>
                            <strong>Submissions:</strong> {record.result.submissions_count}
                          </Typography>
                        )}
                      </Alert>
                    ) : (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        {record.result.error}
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Container>
  );
};

export default FormDataExportDemo;
