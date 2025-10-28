import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  Grid,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useMutation, useQuery } from "@tanstack/react-query";
import { useAuth } from '../../context/FirebaseAuthContext';
import apiService from '../../services/apiService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

interface SettingsData {
  general: {
    companyName: string;
    timezone: string;
    enableNotifications: boolean;
    firstName: string;
    lastName: string;
    phone: string;
    jobTitle: string;
    bio: string;
    avatarUrl: string;
  };
  preferences: {
    theme: string;
    language: string;
    emailNotifications: boolean;
    pushNotifications: boolean;
  };
  profile: {
    email: string;
    username: string;
    isVerified: boolean;
    createdAt: string | null;
    lastLogin: string | null;
  };
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState(0);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [formData, setFormData] = useState<any>({});
  const { currentUser } = useAuth();

  // Fetch user settings
  const { data: settingsData, isLoading, refetch } = useQuery({
    queryKey: ['userSettings'],
    queryFn: async () => {
      const response = await apiService.get('/api/settings');
      return response.data as SettingsData;
    },
    enabled: !!currentUser,
  });

  // Initialize form data when settings are loaded
  useEffect(() => {
    if (settingsData) {
      setFormData({
        companyName: settingsData.general.companyName || '',
        timezone: settingsData.general.timezone || 'UTC',
        enableNotifications: settingsData.general.enableNotifications ?? true,
        firstName: settingsData.general.firstName || '',
        lastName: settingsData.general.lastName || '',
        phone: settingsData.general.phone || '',
        jobTitle: settingsData.general.jobTitle || '',
        bio: settingsData.general.bio || '',
        theme: settingsData.preferences.theme || 'light',
        language: settingsData.preferences.language || 'en',
        emailNotifications: settingsData.preferences.emailNotifications ?? true,
        pushNotifications: settingsData.preferences.pushNotifications ?? false,
      });
    }
  }, [settingsData]);

  const updateSettingsMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiService.post('/api/settings', data);
      return response.data;
    },
    onSuccess: () => {
      refetch();
    },
  });

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleTestConnection = async () => {
    setIsTestingConnection(true);
    try {
      // Add connection test logic here
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert('Connection successful!');
    } catch (error) {
      alert('Connection failed!');
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: value }));
  };

  const handleSaveSettings = async (event: React.FormEvent) => {
    event.preventDefault();
    await updateSettingsMutation.mutateAsync(formData);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Paper sx={{ width: '100%', mt: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="settings tabs"
        >
          <Tab label="General" />
          <Tab label="API Integration" />
          <Tab label="Email" />
          <Tab label="Automation" />
        </Tabs>

        <form onSubmit={handleSaveSettings}>
          <TabPanel value={activeTab} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  General Settings
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  name="firstName"
                  value={formData.firstName || ''}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  name="lastName"
                  value={formData.lastName || ''}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Phone"
                  name="phone"
                  value={formData.phone || ''}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Job Title"
                  name="jobTitle"
                  value={formData.jobTitle || ''}
                  onChange={(e) => handleInputChange('jobTitle', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Company Name"
                  name="companyName"
                  value={formData.companyName || ''}
                  onChange={(e) => handleInputChange('companyName', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Default Time Zone"
                  name="timezone"
                  value={formData.timezone || 'UTC'}
                  onChange={(e) => handleInputChange('timezone', e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Bio"
                  name="bio"
                  multiline
                  rows={3}
                  value={formData.bio || ''}
                  onChange={(e) => handleInputChange('bio', e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.enableNotifications ?? true}
                      onChange={(e) => handleInputChange('enableNotifications', e.target.checked)}
                      name="enableNotifications"
                    />
                  }
                  label="Enable Email Notifications"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.pushNotifications ?? false}
                      onChange={(e) => handleInputChange('pushNotifications', e.target.checked)}
                      name="pushNotifications"
                    />
                  }
                  label="Enable Push Notifications"
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={activeTab} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  API Settings
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="OpenAI API Key"
                  name="openaiApiKey"
                  type="password"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Google API Key"
                  name="googleApiKey"
                  type="password"
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  onClick={handleTestConnection}
                  disabled={isTestingConnection}
                >
                  {isTestingConnection ? (
                    <CircularProgress size={24} />
                  ) : (
                    'Test Connection'
                  )}
                </Button>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={activeTab} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Email Settings
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SMTP Server"
                  name="smtpServer"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SMTP Port"
                  name="smtpPort"
                  type="number"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Email Username"
                  name="emailUsername"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Email Password"
                  name="emailPassword"
                  type="password"
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={activeTab} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Automation Settings
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked name="enableAutoReports" />}
                  label="Enable Automated Report Generation"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked name="enableAutoEmails" />}
                  label="Enable Automated Email Sending"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Report Generation Schedule (Cron)"
                  name="reportSchedule"
                  placeholder="0 0 * * *"
                  helperText="Cron expression for report generation schedule"
                />
              </Grid>
            </Grid>
          </TabPanel>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ px: 3, pb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {updateSettingsMutation.isSuccess && (
              <Alert severity="success" sx={{ flex: 1, mr: 2 }}>
                Settings updated successfully!
              </Alert>
            )}
            {updateSettingsMutation.isError && (
              <Alert severity="error" sx={{ flex: 1, mr: 2 }}>
                Error updating settings. Please try again.
              </Alert>
            )}
            <Button
              type="submit"
              variant="contained"
              disabled={updateSettingsMutation.isPending}
              sx={{ minWidth: 150 }}
            >
              {updateSettingsMutation.isPending ? (
                <CircularProgress size={24} />
              ) : (
                'Save Settings'
              )}
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
}
