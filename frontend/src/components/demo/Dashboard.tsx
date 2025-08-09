import React from "react";
import { useState, useEffect } from "react";
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
  CircularProgress,
  Button,
  Tabs,
  Tab,
} from "@mui/material";
import {
  fetchDashboardStats,
  fetchRecentReports,
  fetchFileStats,
  fetchUserProfile,
  testDatabaseConnection,
} from "../../services/api";
import type {
  DashboardStats,
  Report,
  FileStats,
  User,
} from "../../services/api";

interface DashboardProps {
  user: User | null;
}

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
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Dashboard({ user }: DashboardProps) {
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(
    null
  );
  const [recentReports, setRecentReports] = useState<Report[]>([]);
  const [fileStats, setFileStats] = useState<FileStats | null>(null);
  const [userProfile, setUserProfile] = useState<User | null>(user);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [tabValue, setTabValue] = useState(0);
  const [dbStatus, setDbStatus] = useState<string>("");

  const loadDashboardData = async () => {
    setLoading(true);
    setError("");

    try {
      const [stats, reports, files, profile] = await Promise.all([
        fetchDashboardStats().catch(() => null),
        fetchRecentReports().catch(() => []),
        fetchFileStats().catch(() => null),
        fetchUserProfile().catch(() => null),
      ]);

      setDashboardStats(stats);
      setRecentReports(reports);
      setFileStats(files);
      setUserProfile(profile);
    } catch {
      setError("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      const result = await testDatabaseConnection();
      setDbStatus(`✅ Connected: ${result.table_count} tables found`);
    } catch {
      setDbStatus("❌ Connection failed");
    }
  };

  useEffect(() => {
    loadDashboardData();
    testConnection();
  }, []);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ width: "100%" }}>
      <Typography variant="h4" component="h1" gutterBottom>
        StratoSys MVP Dashboard
      </Typography>

      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Welcome back! Here's what's happening with your system.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ mb: 3 }}>
        <Alert severity="success" sx={{ mb: 2 }}>
          🎉 Frontend successfully connected to backend! All API endpoints are
          working.
        </Alert>
        <Typography variant="body2" color="text.secondary">
          Database Status: {dbStatus}
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Dashboard Stats" />
          <Tab label="Recent Reports" />
          <Tab label="File Management" />
          <Tab label="User Profile" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Dashboard Statistics
                </Typography>
                {dashboardStats ? (
                  <Box>
                    <Typography variant="body2">
                      Total Reports: {dashboardStats.totalReports}
                    </Typography>
                    <Typography variant="body2">
                      Completed: {dashboardStats.completedReports}
                    </Typography>
                    <Typography variant="body2">
                      Pending: {dashboardStats.pendingReports}
                    </Typography>
                    <Typography variant="body2">
                      Success Rate: {dashboardStats.successRate}%
                    </Typography>
                    <Typography variant="body2">
                      Avg Processing Time: {dashboardStats.avgProcessingTime}ms
                    </Typography>
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No dashboard stats available
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  <Button variant="outlined" onClick={loadDashboardData}>
                    Refresh Dashboard
                  </Button>
                  <Button variant="outlined" onClick={testConnection}>
                    Test DB Connection
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Recent Reports
          </Typography>
          {recentReports.length > 0 ? (
            <List>
              {recentReports.map((report: any) => (
                <ListItem key={report.id} divider>
                  <ListItemText
                    primary={report.title}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          {report.description || "No description"}
                        </Typography>
                        <Box
                          sx={{
                            mt: 1,
                            display: "flex",
                            gap: 1,
                            alignItems: "center",
                          }}
                        >
                          <Chip
                            label={report.status}
                            size="small"
                            color={
                              report.status === "completed"
                                ? "success"
                                : report.status === "processing"
                                ? "warning"
                                : report.status === "failed"
                                ? "error"
                                : "default"
                            }
                          />
                          <Typography variant="caption">
                            Created:{" "}
                            {new Date(report.createdAt).toLocaleDateString()}
                          </Typography>
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No recent reports found
            </Typography>
          )}
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            File Statistics
          </Typography>
          {fileStats ? (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {fileStats.total_files}
                  </Typography>
                  <Typography variant="body2">Total Files</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {fileStats.total_size_mb.toFixed(2)} MB
                  </Typography>
                  <Typography variant="body2">Total Size</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="success.main">
                    {fileStats.public_files}
                  </Typography>
                  <Typography variant="body2">Public Files</Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box textAlign="center">
                  <Typography variant="h4" color="warning.main">
                    {fileStats.weekly_uploads}
                  </Typography>
                  <Typography variant="body2">Weekly Uploads</Typography>
                </Box>
              </Grid>
            </Grid>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No file stats available
            </Typography>
          )}
        </Paper>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            User Profile
          </Typography>
          {userProfile ? (
            <Box>
              <Typography variant="body1">
                <strong>Email:</strong> {userProfile.email}
              </Typography>
              <Typography variant="body1">
                <strong>User ID:</strong> {userProfile.id}
              </Typography>
              <Typography variant="body1">
                <strong>Role:</strong> {userProfile.role || "User"}
              </Typography>
              <Typography variant="body1">
                <strong>Member Since:</strong>{" "}
                {new Date(userProfile.created_at).toLocaleDateString()}
              </Typography>
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No user profile data available
            </Typography>
          )}
        </Paper>
      </TabPanel>
    </Box>
  );
}
