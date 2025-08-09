import React from "react";
import { useState } from "react";
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
import { useMutation } from "@tanstack/react-query";

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

  const updateSettingsMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      return response.json();
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

  const handleSaveSettings = async (event: React.FormEvent) => {
    event.preventDefault();
    const formData = new FormData(event.target as HTMLFormElement);
    const data = Object.fromEntries(formData.entries());
    await updateSettingsMutation.mutateAsync(data);
  };

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
                  label="Company Name"
                  name="companyName"
                  defaultValue=""
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Default Time Zone"
                  name="timezone"
                  defaultValue="UTC"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={<Switch defaultChecked name="enableNotifications" />}
                  label="Enable Email Notifications"
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

          <Box sx={{ px: 3, pb: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              type="submit"
              variant="contained"
              disabled={updateSettingsMutation.isLoading}
            >
              {updateSettingsMutation.isLoading ? (
                <CircularProgress size={24} />
              ) : (
                'Save Settings'
              )}
            </Button>
          </Box>
        </form>

        {updateSettingsMutation.isSuccess && (
          <Alert severity="success" sx={{ m: 3 }}>
            Settings updated successfully!
          </Alert>
        )}

        {updateSettingsMutation.isError && (
          <Alert severity="error" sx={{ m: 3 }}>
            Error updating settings. Please try again.
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
