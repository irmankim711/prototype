/**
 * Report Access Guide
 * Step-by-step visual guide to help users access report features
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Alert,
  Chip,
  Divider,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  CloudUpload,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Download as DownloadIcon,
  Assessment as ReportsIcon,
  PlayArrow as PlayIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Login as LoginIcon,
  CheckCircle,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { setupTestAuth, isAuthenticated, getCurrentUser } from '../utils/authHelper';

const ReportAccessGuide: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [expanded, setExpanded] = useState(true);
  const [authStatus, setAuthStatus] = useState<{
    authenticated: boolean;
    user: any;
    loading: boolean;
  }>({
    authenticated: isAuthenticated(),
    user: getCurrentUser(),
    loading: false,
  });

  const navigate = useNavigate();

  const steps = [
    {
      label: 'Make sure you are logged in',
      icon: <LoginIcon />,
      description: 'Authentication is required to access report features',
      action: 'Login or use quick auth',
    },
    {
      label: 'Go to Reports page',
      icon: <ReportsIcon />,
      description: 'Navigate to the main reports interface',
      action: 'Click "Go to Reports"',
    },
    {
      label: 'Upload Excel file',
      icon: <CloudUpload />,
      description: 'Use the "DOCX Generator" tab to upload your Excel file',
      action: 'Drag & drop or browse for .xlsx file',
    },
    {
      label: 'Wait for generation',
      icon: <PlayIcon />,
      description: 'The system will convert your Excel to a DOCX report',
      action: 'Processing happens automatically',
    },
    {
      label: 'Access your report',
      icon: <CheckCircle />,
      description: 'After generation, you\'ll see options to View, Edit, and Download',
      action: 'Choose from the success modal or reports list',
    },
  ];

  const handleQuickAuth = async () => {
    setAuthStatus(prev => ({ ...prev, loading: true }));
    
    try {
      const result = await setupTestAuth();
      if (result.success) {
        setAuthStatus({
          authenticated: true,
          user: result.user,
          loading: false,
        });
        setActiveStep(1); // Move to next step
      } else {
        console.error('Quick auth failed:', result.error);
        setAuthStatus(prev => ({ ...prev, loading: false }));
      }
    } catch (error) {
      console.error('Quick auth error:', error);
      setAuthStatus(prev => ({ ...prev, loading: false }));
    }
  };

  const handleGoToReports = () => {
    navigate('/reports');
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ReportsIcon color="primary" />
            How to Access Report Features
          </Typography>
          <IconButton 
            onClick={() => setExpanded(!expanded)}
            size="small"
          >
            {expanded ? <CollapseIcon /> : <ExpandIcon />}
          </IconButton>
        </Box>

        <Collapse in={expanded}>
          {/* Authentication Status */}
          <Alert 
            severity={authStatus.authenticated ? 'success' : 'warning'}
            sx={{ mb: 3 }}
            action={
              !authStatus.authenticated && (
                <Button 
                  size="small" 
                  onClick={handleQuickAuth}
                  disabled={authStatus.loading}
                  startIcon={<LoginIcon />}
                >
                  {authStatus.loading ? 'Logging in...' : 'Quick Login'}
                </Button>
              )
            }
          >
            <Typography variant="body2">
              {authStatus.authenticated 
                ? `✅ Logged in as: ${authStatus.user?.email || 'User'}` 
                : '⚠️ You need to be logged in to access report features'
              }
            </Typography>
          </Alert>

          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((step, index) => (
              <Step key={step.label}>
                <StepLabel 
                  icon={step.icon}
                  sx={{
                    '& .MuiStepLabel-iconContainer': {
                      color: activeStep >= index ? 'primary.main' : 'text.secondary',
                    },
                  }}
                >
                  <Typography variant="h6">{step.label}</Typography>
                </StepLabel>
                <StepContent>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {step.description}
                  </Typography>
                  
                  <Chip 
                    label={step.action} 
                    size="small" 
                    variant="outlined"
                    sx={{ mb: 2 }}
                  />

                  {/* Step-specific actions */}
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    {index === 0 && !authStatus.authenticated && (
                      <Button
                        size="small"
                        onClick={handleQuickAuth}
                        disabled={authStatus.loading}
                        startIcon={<LoginIcon />}
                        variant="contained"
                      >
                        {authStatus.loading ? 'Logging in...' : 'Quick Login'}
                      </Button>
                    )}
                    
                    {index === 1 && (
                      <Button
                        size="small"
                        onClick={handleGoToReports}
                        startIcon={<ReportsIcon />}
                        variant="contained"
                      >
                        Go to Reports
                      </Button>
                    )}
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      disabled={index === 0}
                      onClick={handleBack}
                      size="small"
                    >
                      Back
                    </Button>
                    <Button
                      variant="contained"
                      onClick={handleNext}
                      size="small"
                      disabled={
                        (index === 0 && !authStatus.authenticated) ||
                        index === steps.length - 1
                      }
                    >
                      {index === steps.length - 1 ? 'Finish' : 'Continue'}
                    </Button>
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>

          {activeStep === steps.length && (
            <Paper square elevation={0} sx={{ p: 3, mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                🎉 Ready to Go!
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                You're all set to generate and access reports. After uploading an Excel file, 
                you'll see a success modal with these options:
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                <Chip icon={<ViewIcon />} label="View Report" color="primary" />
                <Chip icon={<EditIcon />} label="Edit AI Insights" color="secondary" />
                <Chip icon={<DownloadIcon />} label="Download DOCX" color="success" />
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button onClick={handleGoToReports} variant="contained">
                  Start Using Reports
                </Button>
                <Button onClick={handleReset}>Reset Guide</Button>
              </Box>
            </Paper>
          )}
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default ReportAccessGuide;