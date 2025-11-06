import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Container,
  Paper,
  Alert,
  CircularProgress,
  Button,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import {
  Google as GoogleIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Login as LoginIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useFirebaseAuth } from '../../context/FirebaseAuthContext';
import { formBuilderAPI } from '../../services/formBuilder';
import FormDataExporter from '../../components/FormDataExporter';

interface GoogleForm {
  id: string;
  title: string;
  description?: string;
  response_count: number;
  question_count: number;
  created_time?: string;
  modified_time?: string;
  web_view_link?: string;
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
  service_enabled?: boolean;
}

const GoogleFormsExport: React.FC = () => {
  const navigate = useNavigate();
  const { user: firebaseUser, isLoading: authLoading } = useFirebaseAuth();
  const isAuthenticated = !!firebaseUser;
  const [status, setStatus] = useState<GoogleFormsStatus | null>(null);
  const [forms, setForms] = useState<GoogleForm[]>([]);
  const [selectedForm, setSelectedForm] = useState<GoogleForm | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(true);
  const [isLoadingForms, setIsLoadingForms] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check if user is authenticated to the application
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      // Redirect to landing page if not logged in
      navigate('/');
    }
  }, [authLoading, isAuthenticated, navigate]);

  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      checkStatus();
    }
  }, [isAuthenticated, authLoading]);

  const checkStatus = async () => {
    setIsLoadingStatus(true);
    setError(null);
    try {
      const statusResponse = await formBuilderAPI.getGoogleFormsStatus();
      setStatus(statusResponse);

      if (statusResponse.success && statusResponse.is_authorized) {
        await loadForms();
      }
    } catch (err: any) {
      console.error('Error checking status:', err);
      setError(err.message || 'Failed to check Google Forms status');
      setStatus({
        success: false,
        status: 'error',
        is_authenticated: false,
        is_authorized: false,
        has_valid_token: false,
        message: 'Failed to connect to Google Forms service',
        requires_config: true
      });
    } finally {
      setIsLoadingStatus(false);
    }
  };

  const loadForms = async () => {
    setIsLoadingForms(true);
    setError(null);
    try {
      const formsResponse = await formBuilderAPI.getGoogleForms(50);
      if (formsResponse.success) {
        setForms(formsResponse.forms || []);
      } else {
        setError(formsResponse.error || 'Failed to load Google Forms');
      }
    } catch (err: any) {
      console.error('Error loading forms:', err);
      setError(err.message || 'Failed to load Google Forms');
    } finally {
      setIsLoadingForms(false);
    }
  };

  const handleGoogleAuth = async () => {
    try {
      const authResponse = await formBuilderAPI.initiateGoogleAuth();
      if (authResponse.success && authResponse.authorization_url) {
        // Listen for OAuth success message from popup
        const handleAuthMessage = (event: MessageEvent) => {
          if (event.data.type === 'google-auth-success') {
            console.log('✅ Google OAuth successful, reloading forms...');
            // Remove listener
            window.removeEventListener('message', handleAuthMessage);
            // Recheck status to load forms
            checkStatus();
          }
        };

        window.addEventListener('message', handleAuthMessage);

        // Open Google OAuth in new window
        const authWindow = window.open(
          authResponse.authorization_url,
          'Google OAuth',
          'width=600,height=700'
        );

        // Fallback: Poll for authentication completion if message not received
        const pollInterval = setInterval(() => {
          if (authWindow?.closed) {
            clearInterval(pollInterval);
            // Clean up listener
            window.removeEventListener('message', handleAuthMessage);
            // Recheck status after auth window closes
            setTimeout(checkStatus, 1000);
          }
        }, 500);
      } else {
        setError(authResponse.error || 'Failed to initiate Google authentication');
      }
    } catch (err: any) {
      console.error('Error initiating auth:', err);
      setError(err.message || 'Failed to start authentication');
    }
  };

  const handleFormSelect = (form: GoogleForm) => {
    setSelectedForm(form);
  };

  const handleExportComplete = (result: any) => {
    console.log('Export completed:', result);
    if (result.success) {
      // Reset selection after successful export
      setTimeout(() => setSelectedForm(null), 3000);
    }
  };

  // Show loading while checking auth or status
  if (authLoading || isLoadingStatus) {
    return (
      <Container maxWidth="lg" sx={{ py: 8, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 3 }}>
          {authLoading ? 'Loading...' : 'Checking Google Forms connection...'}
        </Typography>
      </Container>
    );
  }

  // If not authenticated, don't show anything (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Not configured
  if (status?.requires_config) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <ErrorIcon color="warning" sx={{ fontSize: 80, mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Google Forms Not Configured
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            The Google Forms integration requires OAuth credentials to be configured in the backend.
          </Typography>
          <Alert severity="info" sx={{ mt: 3, textAlign: 'left' }}>
            <Typography variant="subtitle2" gutterBottom>
              <strong>For Administrators:</strong>
            </Typography>
            <Typography variant="body2">
              1. Set up OAuth credentials in Google Cloud Console<br />
              2. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to .env file<br />
              3. Restart the backend server
            </Typography>
          </Alert>
        </Paper>
      </Container>
    );
  }

  // Need authentication
  if (!status?.is_authorized) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <GoogleIcon color="primary" sx={{ fontSize: 80, mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Connect to Google Forms
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Sign in with your Google account to access your Google Forms and export responses to Excel.
          </Typography>

          <Box sx={{ my: 4 }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<LoginIcon />}
              onClick={handleGoogleAuth}
              sx={{
                py: 1.5,
                px: 4,
                fontSize: '1.1rem',
                background: 'linear-gradient(45deg, #4285F4 30%, #34A853 90%)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #3367D6 30%, #2E8B47 90%)',
                }
              }}
            >
              Sign in with Google
            </Button>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Grid container spacing={2} sx={{ mt: 2 }}>
            <Grid item xs={12} sm={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    ✅ Secure
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    OAuth 2.0 authentication
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    📊 Real Data
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Access your actual forms
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    💾 Export
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Download as Excel
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {error && (
            <Alert severity="error" sx={{ mt: 3 }}>
              {error}
            </Alert>
          )}
        </Paper>
      </Container>
    );
  }

  // Authorized - show forms list
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              📊 Google Forms Export
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Select a form to export responses to Excel
            </Typography>
          </Box>
          <Box>
            <Button
              startIcon={<RefreshIcon />}
              onClick={loadForms}
              disabled={isLoadingForms}
            >
              Refresh Forms
            </Button>
          </Box>
        </Box>

        <Alert severity="success" icon={<CheckCircleIcon />}>
          Connected to Google Forms • {forms.length} forms available
        </Alert>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Forms List */}
        <Grid item xs={12} md={selectedForm ? 6 : 12}>
          <Paper sx={{ height: selectedForm ? '70vh' : 'auto', overflow: 'auto' }}>
            {isLoadingForms ? (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <CircularProgress />
                <Typography sx={{ mt: 2 }}>Loading forms...</Typography>
              </Box>
            ) : forms.length === 0 ? (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <DescriptionIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  No Forms Found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  You don't have any Google Forms yet. Create one in Google Forms to get started.
                </Typography>
              </Box>
            ) : (
              <List>
                {forms.map((form) => (
                  <React.Fragment key={form.id}>
                    <ListItem disablePadding>
                      <ListItemButton
                        selected={selectedForm?.id === form.id}
                        onClick={() => handleFormSelect(form)}
                      >
                        <ListItemIcon>
                          <DescriptionIcon color={selectedForm?.id === form.id ? 'primary' : 'inherit'} />
                        </ListItemIcon>
                        <ListItemText
                          primary={form.title}
                          secondary={
                            <React.Fragment>
                              <Box component="span" sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                                <Chip
                                  label={`${form.response_count || 0} responses`}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                                <Chip
                                  label={`${form.question_count || 0} questions`}
                                  size="small"
                                  variant="outlined"
                                />
                              </Box>
                            </React.Fragment>
                          }
                        />
                      </ListItemButton>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Export Panel */}
        {selectedForm && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '70vh', overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Export: {selectedForm.title}
              </Typography>
              <Divider sx={{ my: 2 }} />
              <FormDataExporter
                form={{
                  id: parseInt(selectedForm.id),
                  title: selectedForm.title,
                  description: selectedForm.description || '',
                  schema: { fields: [] },
                  created_at: selectedForm.created_time || new Date().toISOString(),
                  updated_at: selectedForm.modified_time || new Date().toISOString(),
                  creator_id: 1,
                  creator_name: 'User',
                  is_active: true,
                  is_public: false,
                  submission_count: selectedForm.response_count || 0,
                  view_count: 0
                }}
                formType="google"
                googleFormId={selectedForm.id}
                onExportComplete={handleExportComplete}
              />
            </Paper>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default GoogleFormsExport;
