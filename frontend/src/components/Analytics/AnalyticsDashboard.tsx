import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tab,
  Tabs,
  Container,
  Paper,
  Chip,
  Button,
  Divider,
  Alert,
  useTheme,
} from "@mui/material";
import {
  Analytics as AnalyticsIcon,
  Dashboard as DashboardIcon,
  TrendingUp,
  Assessment,
  Timeline,
  BarChart as BarChartIcon,
} from "@mui/icons-material";
import RealTimeStats from "./RealTimeStats";
import InteractiveCharts from "./InteractiveCharts";
import { analyticsService } from "../../services/analyticsService";
import type {
  TopFormData,
  PerformanceComparison,
  GeographicData,
  FieldAnalytics,
} from "../../services/analyticsService";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

export const AnalyticsDashboard: React.FC = () => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [topForms, setTopForms] = useState<TopFormData[]>([]);
  const [performanceData, setPerformanceData] =
    useState<PerformanceComparison | null>(null);
  const [geoData, setGeoData] = useState<GeographicData | null>(null);
  const [selectedFormId, setSelectedFormId] = useState<number | null>(null);
  const [fieldAnalytics, setFieldAnalytics] = useState<FieldAnalytics | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const fetchTopForms = async () => {
    try {
      const { forms } = await analyticsService.getTopPerformingForms(10);
      setTopForms(forms);
    } catch (err) {
      console.error("Error fetching top forms:", err);
    }
  };

  const fetchPerformanceData = async () => {
    try {
      const data = await analyticsService.getPerformanceComparison();
      setPerformanceData(data);
    } catch (err) {
      console.error("Error fetching performance data:", err);
    }
  };

  const fetchGeographicData = async () => {
    try {
      const data = await analyticsService.getGeographicDistribution();
      setGeoData(data);
    } catch (err) {
      console.error("Error fetching geographic data:", err);
    }
  };

  const fetchFieldAnalytics = async (formId: number) => {
    try {
      setLoading(true);
      const data = await analyticsService.getFieldAnalytics(formId);
      setFieldAnalytics(data);
      setSelectedFormId(formId);
    } catch (err) {
      console.error("Error fetching field analytics:", err);
      setError("Failed to fetch field analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopForms();
    fetchPerformanceData();
    fetchGeographicData();
  }, []);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "up":
        return <TrendingUp sx={{ color: theme.palette.success.main }} />;
      case "down":
        return (
          <TrendingUp
            sx={{
              color: theme.palette.error.main,
              transform: "rotate(180deg)",
            }}
          />
        );
      default:
        return <Timeline sx={{ color: theme.palette.grey[500] }} />;
    }
  };

  const getPerformanceColor = (score: number) => {
    if (score >= 70) return theme.palette.success.main;
    if (score >= 40) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ pb: 4 }}>
        {/* Header */}
        <Box display="flex" alignItems="center" gap={2} mb={4}>
          <AnalyticsIcon
            sx={{ fontSize: 32, color: theme.palette.primary.main }}
          />
          <Typography variant="h4" component="h1">
            Analytics Dashboard
          </Typography>
          <Chip
            label="Enhanced"
            color="primary"
            variant="outlined"
            size="small"
          />
        </Box>

        {/* Navigation Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="fullWidth"
            indicatorColor="primary"
            textColor="primary"
          >
            <Tab
              icon={<DashboardIcon />}
              label="Overview"
              iconPosition="start"
            />
            <Tab icon={<BarChartIcon />} label="Charts" iconPosition="start" />
            <Tab
              icon={<TrendingUp />}
              label="Performance"
              iconPosition="start"
            />
            <Tab
              icon={<Assessment />}
              label="Field Analysis"
              iconPosition="start"
            />
          </Tabs>
        </Paper>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Tab Panels */}
        <TabPanel value={activeTab} index={0}>
          {/* Overview Tab */}
          <Grid container spacing={3}>
            {/* Real-time Stats */}
            <Grid item xs={12}>
              <RealTimeStats refreshInterval={30000} />
            </Grid>

            {/* Top Performing Forms */}
            <Grid item xs={12} lg={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Top Performing Forms
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {topForms.length > 0 ? (
                    <Grid container spacing={2}>
                      {topForms.slice(0, 6).map((form: any) => (
                        <Grid item xs={12} sm={6} md={4} key={form.form_id}>
                          <Paper
                            sx={{
                              p: 2,
                              cursor: "pointer",
                              "&:hover": { bgcolor: "grey.50" },
                            }}
                            onClick={() => fetchFieldAnalytics(form.form_id)}
                          >
                            <Box
                              display="flex"
                              alignItems="center"
                              justifyContent="space-between"
                              mb={1}
                            >
                              <Typography variant="subtitle2" noWrap>
                                {form.form_name}
                              </Typography>
                              {getTrendIcon(form.trend)}
                            </Box>
                            <Typography variant="h6" color="primary">
                              {form.submissions}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              submissions • {form.completion_rate}% completion
                            </Typography>
                            <Box mt={1}>
                              <Chip
                                size="small"
                                label={`${form.recent_activity} recent`}
                                color={
                                  form.recent_activity > 0
                                    ? "success"
                                    : "default"
                                }
                              />
                            </Box>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  ) : (
                    <Typography color="textSecondary">
                      No form data available
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Geographic Distribution */}
            <Grid item xs={12} lg={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Geographic Distribution
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {geoData ? (
                    <Box>
                      {geoData.countries.slice(0, 5).map((country: any) => (
                        <Box
                          key={country.name}
                          display="flex"
                          justifyContent="space-between"
                          alignItems="center"
                          mb={1}
                        >
                          <Typography variant="body2">
                            {country.name}
                          </Typography>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Box
                              width={60}
                              height={6}
                              bgcolor={theme.palette.grey[200]}
                              borderRadius={3}
                              position="relative"
                            >
                              <Box
                                width={`${country.percentage}%`}
                                height="100%"
                                bgcolor={theme.palette.primary.main}
                                borderRadius={3}
                              />
                            </Box>
                            <Typography variant="caption" sx={{ minWidth: 30 }}>
                              {country.percentage}%
                            </Typography>
                          </Box>
                        </Box>
                      ))}
                      <Typography
                        variant="caption"
                        color="textSecondary"
                        mt={2}
                        display="block"
                      >
                        Total countries: {geoData.total_countries}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography color="textSecondary">
                      Loading geographic data...
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Charts Tab */}
          <InteractiveCharts />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {/* Performance Tab */}
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Form Performance Analysis
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {performanceData ? (
                    <Box>
                      {performanceData.best_performer && (
                        <Alert severity="success" sx={{ mb: 3 }}>
                          <Typography variant="h6">Best Performer</Typography>
                          <Typography>
                            {performanceData.best_performer.form_title} - Score:{" "}
                            {performanceData.best_performer.performance_score}
                            /100
                          </Typography>
                        </Alert>
                      )}

                      <Grid container spacing={2}>
                        {performanceData.forms.slice(0, 9).map((form: any) => (
                          <Grid item xs={12} sm={6} md={4} key={form.form_id}>
                            <Paper sx={{ p: 2 }}>
                              <Typography
                                variant="subtitle2"
                                gutterBottom
                                noWrap
                              >
                                {form.form_title}
                              </Typography>
                              <Box
                                display="flex"
                                alignItems="center"
                                gap={1}
                                mb={1}
                              >
                                <Typography
                                  variant="h6"
                                  sx={{
                                    color: getPerformanceColor(
                                      form.performance_score
                                    ),
                                  }}
                                >
                                  {form.performance_score}
                                </Typography>
                                <Typography
                                  variant="caption"
                                  color="textSecondary"
                                >
                                  / 100
                                </Typography>
                              </Box>
                              <Typography variant="body2" color="textSecondary">
                                {form.total_submissions} submissions
                              </Typography>
                              <Typography variant="body2" color="textSecondary">
                                {form.avg_per_day} avg/day
                              </Typography>
                              <Box mt={1}>
                                <Chip
                                  size="small"
                                  label={`${form.days_active} days active`}
                                  variant="outlined"
                                />
                              </Box>
                            </Paper>
                          </Grid>
                        ))}
                      </Grid>
                    </Box>
                  ) : (
                    <Typography color="textSecondary">
                      Loading performance data...
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {/* Field Analysis Tab */}
          <Grid container spacing={3}>
            <Grid item xs={12} lg={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Select Form for Analysis
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {topForms.map((form: any) => (
                    <Button
                      key={form.form_id}
                      fullWidth
                      variant={
                        selectedFormId === form.form_id
                          ? "contained"
                          : "outlined"
                      }
                      onClick={() => fetchFieldAnalytics(form.form_id)}
                      sx={{ mb: 1, justifyContent: "flex-start" }}
                    >
                      {form.form_name}
                    </Button>
                  ))}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} lg={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Field Completion Analysis
                  </Typography>
                  <Divider sx={{ mb: 2 }} />

                  {loading ? (
                    <Typography>Loading field analytics...</Typography>
                  ) : fieldAnalytics ? (
                    <Box>
                      <Alert severity="info" sx={{ mb: 3 }}>
                        <Typography variant="h6">
                          {fieldAnalytics.form_title}
                        </Typography>
                        <Typography>
                          Total Submissions: {fieldAnalytics.total_submissions}{" "}
                          • Overall Completion:{" "}
                          {fieldAnalytics.overall_completion}%
                        </Typography>
                      </Alert>

                      <Grid container spacing={2}>
                        {Object.entries(fieldAnalytics.field_stats).map(
                          ([fieldName, stats]) => (
                            <Grid item xs={12} sm={6} key={fieldName}>
                              <Paper sx={{ p: 2 }}>
                                <Box
                                  display="flex"
                                  justifyContent="space-between"
                                  alignItems="center"
                                  mb={1}
                                >
                                  <Typography variant="subtitle2">
                                    {fieldName}
                                  </Typography>
                                  <Chip
                                    size="small"
                                    label={
                                      stats.is_required
                                        ? "Required"
                                        : "Optional"
                                    }
                                    color={
                                      stats.is_required ? "error" : "default"
                                    }
                                    variant="outlined"
                                  />
                                </Box>

                                <Box mb={2}>
                                  <Box
                                    display="flex"
                                    justifyContent="space-between"
                                    mb={1}
                                  >
                                    <Typography variant="body2">
                                      Completion Rate
                                    </Typography>
                                    <Typography
                                      variant="body2"
                                      fontWeight="bold"
                                    >
                                      {stats.completion_rate}%
                                    </Typography>
                                  </Box>
                                  <Box
                                    height={8}
                                    bgcolor={theme.palette.grey[200]}
                                    borderRadius={4}
                                  >
                                    <Box
                                      height="100%"
                                      width={`${stats.completion_rate}%`}
                                      bgcolor={
                                        stats.completion_rate >= 80
                                          ? theme.palette.success.main
                                          : stats.completion_rate >= 50
                                          ? theme.palette.warning.main
                                          : theme.palette.error.main
                                      }
                                      borderRadius={4}
                                    />
                                  </Box>
                                </Box>

                                <Typography
                                  variant="caption"
                                  color="textSecondary"
                                >
                                  {stats.completed_count} of{" "}
                                  {stats.total_submissions} submissions
                                </Typography>
                                <br />
                                <Typography
                                  variant="caption"
                                  color="textSecondary"
                                >
                                  Type: {stats.field_type}
                                </Typography>
                              </Paper>
                            </Grid>
                          )
                        )}
                      </Grid>
                    </Box>
                  ) : (
                    <Typography color="textSecondary">
                      Select a form to view field completion analysis
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Box>
    </Container>
  );
};

export default AnalyticsDashboard;
