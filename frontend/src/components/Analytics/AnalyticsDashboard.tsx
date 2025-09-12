import React from "react";
import { useState, useEffect, useCallback, useRef } from "react";
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
  AlertTitle,
  Collapse,
  IconButton,
  Tooltip,
  Skeleton,
  useTheme,
} from "@mui/material";
import {
  Analytics as AnalyticsIcon,
  Dashboard as DashboardIcon,
  TrendingUp,
  Assessment,
  Timeline,
  BarChart as BarChartIcon,
  Refresh,
  Error,
  Warning,
  Info,
  ExpandMore,
  ExpandLess,
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
  
  // Enhanced state management for loading and errors
  const [loading, setLoading] = useState({
    topForms: false,
    performance: false,
    geographic: false,
    fieldAnalytics: false,
    overall: true,
  });
  
  const [errors, setErrors] = useState({
    topForms: null as string | null,
    performance: null as string | null,
    geographic: null as string | null,
    fieldAnalytics: null as string | null,
    overall: null as string | null,
  });
  
  const [retryCounts, setRetryCounts] = useState({
    topForms: 0,
    performance: 0,
    geographic: 0,
    fieldAnalytics: 0,
  });
  
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Refs to track timeouts for cleanup
  const timeoutRefs = useRef<{ [key: string]: NodeJS.Timeout }>({});
  const isMountedRef = useRef(true);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Enhanced fetch functions with retry logic and better error handling
  const fetchTopForms = useCallback(async (isRetry: boolean = false) => {
    if (isRetry) {
      setIsRetrying(true);
    } else {
      setLoading(prev => ({ ...prev, topForms: true }));
    }
    
    try {
      const { forms } = await analyticsService.getTopPerformingForms(10);
      if (!isMountedRef.current) return;
      setTopForms(forms);
      setErrors(prev => ({ ...prev, topForms: null }));
      setRetryCounts(prev => ({ ...prev, topForms: 0 }));
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      console.error("Error fetching top forms:", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch top performing forms";
      setErrors(prev => ({ ...prev, topForms: errorMessage }));
      
      // Auto-retry logic with cleanup tracking
      if (retryCounts.topForms < 2 && !isRetry) {
        setRetryCounts(prev => ({ ...prev, topForms: prev.topForms + 1 }));
        const timeoutId = setTimeout(() => {
          if (isMountedRef.current) {
            fetchTopForms(true);
          }
        }, 2000);
        timeoutRefs.current.topForms = timeoutId;
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(prev => ({ ...prev, topForms: false }));
        setIsRetrying(false);
      }
    }
  }, [retryCounts.topForms]);

  const fetchPerformanceData = useCallback(async (isRetry: boolean = false) => {
    if (isRetry) {
      setIsRetrying(true);
    } else {
      setLoading(prev => ({ ...prev, performance: true }));
    }
    
    try {
      const data = await analyticsService.getPerformanceComparison();
      if (!isMountedRef.current) return;
      setPerformanceData(data);
      setErrors(prev => ({ ...prev, performance: null }));
      setRetryCounts(prev => ({ ...prev, performance: 0 }));
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      console.error("Error fetching performance data:", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch performance data";
      setErrors(prev => ({ ...prev, performance: errorMessage }));
      
      // Auto-retry logic with cleanup tracking
      if (retryCounts.performance < 2 && !isRetry) {
        setRetryCounts(prev => ({ ...prev, performance: prev.performance + 1 }));
        const timeoutId = setTimeout(() => {
          if (isMountedRef.current) {
            fetchPerformanceData(true);
          }
        }, 2000);
        timeoutRefs.current.performance = timeoutId;
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(prev => ({ ...prev, performance: false }));
        setIsRetrying(false);
      }
    }
  }, [retryCounts.performance]);

  const fetchGeographicData = useCallback(async (isRetry: boolean = false) => {
    if (isRetry) {
      setIsRetrying(true);
    } else {
      setLoading(prev => ({ ...prev, geographic: true }));
    }
    
    try {
      const data = await analyticsService.getGeographicDistribution();
      if (!isMountedRef.current) return;
      setGeoData(data);
      setErrors(prev => ({ ...prev, geographic: null }));
      setRetryCounts(prev => ({ ...prev, geographic: 0 }));
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      console.error("Error fetching geographic data:", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch geographic data";
      setErrors(prev => ({ ...prev, geographic: errorMessage }));
      
      // Auto-retry logic with cleanup tracking
      if (retryCounts.geographic < 2 && !isRetry) {
        setRetryCounts(prev => ({ ...prev, geographic: prev.geographic + 1 }));
        const timeoutId = setTimeout(() => {
          if (isMountedRef.current) {
            fetchGeographicData(true);
          }
        }, 2000);
        timeoutRefs.current.geographic = timeoutId;
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(prev => ({ ...prev, geographic: false }));
        setIsRetrying(false);
      }
    }
  }, [retryCounts.geographic]);

  const fetchFieldAnalytics = useCallback(async (formId: number, isRetry: boolean = false) => {
    if (isRetry) {
      setIsRetrying(true);
    } else {
      setLoading(prev => ({ ...prev, fieldAnalytics: true }));
    }
    
    try {
      const data = await analyticsService.getFieldAnalytics(formId);
      if (!isMountedRef.current) return;
      setFieldAnalytics(data);
      setSelectedFormId(formId);
      setErrors(prev => ({ ...prev, fieldAnalytics: null }));
      setRetryCounts(prev => ({ ...prev, fieldAnalytics: 0 }));
    } catch (err: unknown) {
      if (!isMountedRef.current) return;
      console.error("Error fetching field analytics:", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch field analytics";
      setErrors(prev => ({ ...prev, fieldAnalytics: errorMessage }));
      
      // Auto-retry logic with cleanup tracking
      if (retryCounts.fieldAnalytics < 2 && !isRetry) {
        setRetryCounts(prev => ({ ...prev, fieldAnalytics: prev.fieldAnalytics + 1 }));
        const timeoutId = setTimeout(() => {
          if (isMountedRef.current) {
            fetchFieldAnalytics(formId, true);
          }
        }, 2000);
        timeoutRefs.current.fieldAnalytics = timeoutId;
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(prev => ({ ...prev, fieldAnalytics: false }));
        setIsRetrying(false);
      }
    }
  }, [retryCounts.fieldAnalytics]);

  // Retry handlers for each data type
  const handleRetryTopForms = () => {
    setRetryCounts(prev => ({ ...prev, topForms: 0 }));
    fetchTopForms();
  };

  const handleRetryPerformance = () => {
    setRetryCounts(prev => ({ ...prev, performance: 0 }));
    fetchPerformanceData();
  };

  const handleRetryGeographic = () => {
    setRetryCounts(prev => ({ ...prev, geographic: 0 }));
    fetchGeographicData();
  };

  const handleRetryFieldAnalytics = () => {
    if (selectedFormId) {
      setRetryCounts(prev => ({ ...prev, fieldAnalytics: 0 }));
      fetchFieldAnalytics(selectedFormId);
    }
  };

  // Overall retry function
  const handleRetryAll = () => {
    setRetryCounts({
      topForms: 0,
      performance: 0,
      geographic: 0,
      fieldAnalytics: 0,
    });
    setErrors({
      topForms: null,
      performance: null,
      geographic: null,
      fieldAnalytics: null,
      overall: null,
    });
    fetchTopForms();
    fetchPerformanceData();
    fetchGeographicData();
  };

  useEffect(() => {
    isMountedRef.current = true;

    const initializeDashboard = async () => {
      if (!isMountedRef.current) return;
      
      setLoading(prev => ({ ...prev, overall: true }));
      try {
        await Promise.all([
          fetchTopForms(),
          fetchPerformanceData(),
          fetchGeographicData(),
        ]);
        if (!isMountedRef.current) return;
        setErrors(prev => ({ ...prev, overall: null }));
      } catch (err: unknown) {
        if (!isMountedRef.current) return;
        console.error("Error initializing dashboard:", err);
        setErrors(prev => ({ 
          ...prev, 
          overall: err.message || "Failed to initialize dashboard" 
        }));
      } finally {
        if (isMountedRef.current) {
          setLoading(prev => ({ ...prev, overall: false }));
        }
      }
    };

    initializeDashboard();

    return () => {
      isMountedRef.current = false;
      // Clear any pending retry timeouts
      Object.values(timeoutRefs.current).forEach(timeout => {
        if (timeout) clearTimeout(timeout);
      });
      timeoutRefs.current = {};
    };
  }, [fetchTopForms, fetchPerformanceData, fetchGeographicData]);

  // Additional cleanup effect for component unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      // Clear all timeouts on unmount
      Object.values(timeoutRefs.current).forEach(timeout => {
        if (timeout) clearTimeout(timeout);
      });
      timeoutRefs.current = {};
    };
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

  // Check if there are any overall errors
  const hasOverallError = Object.values(errors).some(error => error !== null);
  const hasData = topForms.length > 0 || performanceData || geoData;

  // Loading skeleton component
  const LoadingSkeleton = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Skeleton variant="rectangular" height={200} />
      </Grid>
      <Grid item xs={12} lg={8}>
        <Skeleton variant="rectangular" height={300} />
      </Grid>
      <Grid item xs={12} lg={4}>
        <Skeleton variant="rectangular" height={300} />
      </Grid>
    </Grid>
  );

  // Error fallback component
  const ErrorFallback = ({ error, onRetry, title }: { 
    error: string; 
    onRetry: () => void; 
    title: string;
  }) => (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardContent sx={{ textAlign: 'center', py: 4 }}>
        <Error sx={{ fontSize: 48, color: theme.palette.error.main, mb: 2 }} />
        <Typography variant="h6" color="error" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          {error}
        </Typography>
        <Button
          variant="outlined"
          onClick={onRetry}
          startIcon={<Refresh />}
          disabled={isRetrying}
        >
          Retry
        </Button>
      </CardContent>
    </Card>
  );

  // Overall error state
  if (loading.overall) {
    return (
      <Container maxWidth="xl">
        <Box sx={{ pb: 4 }}>
          <Box display="flex" alignItems="center" gap={2} mb={4}>
            <AnalyticsIcon sx={{ fontSize: 32, color: theme.palette.primary.main }} />
            <Typography variant="h4" component="h1">
              Analytics Dashboard
            </Typography>
            <Chip label="Enhanced" color="primary" variant="outlined" size="small" />
          </Box>
          <LoadingSkeleton />
        </Box>
      </Container>
    );
  }

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

        {/* Overall Error Alert */}
        {hasOverallError && (
          <Alert 
            severity="error" 
            sx={{ mb: 3 }}
            action={
              <Box display="flex" gap={1}>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={handleRetryAll}
                  disabled={isRetrying}
                  startIcon={<Refresh />}
                >
                  Retry All
                </Button>
                <IconButton
                  size="small"
                  onClick={() => setShowErrorDetails(!showErrorDetails)}
                >
                  {showErrorDetails ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Box>
            }
          >
            <AlertTitle>Dashboard Data Issues</AlertTitle>
            Some analytics data could not be loaded. Click "Retry All" to attempt to reload all data.
            
            <Collapse in={showErrorDetails}>
              <Box mt={2}>
                {errors.topForms && (
                  <Typography variant="body2" color="textSecondary">
                    <strong>Top Forms:</strong> {errors.topForms}
                  </Typography>
                )}
                {errors.performance && (
                  <Typography variant="body2" color="textSecondary">
                    <strong>Performance Data:</strong> {errors.performance}
                  </Typography>
                )}
                {errors.geographic && (
                  <Typography variant="body2" color="textSecondary">
                    <strong>Geographic Data:</strong> {errors.geographic}
                  </Typography>
                )}
              </Box>
            </Collapse>
          </Alert>
        )}

        {/* Success Alert when data is loaded */}
        {!hasOverallError && hasData && (
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body2">
              Analytics dashboard loaded successfully. All data sources are operational.
            </Typography>
          </Alert>
        )}

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
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      Top Performing Forms
                    </Typography>
                    <Tooltip title="Refresh top forms">
                      <IconButton
                        size="small"
                        onClick={handleRetryTopForms}
                        disabled={loading.topForms || isRetrying}
                      >
                        <Refresh />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  
                  {loading.topForms ? (
                    <Box display="flex" flexDirection="column" gap={2}>
                      {[1, 2, 3, 4, 5, 6].map((i) => (
                        <Skeleton key={i} variant="rectangular" height={80} />
                      ))}
                    </Box>
                  ) : errors.topForms ? (
                    <ErrorFallback
                      error={errors.topForms}
                      onRetry={handleRetryTopForms}
                      title="Failed to Load Top Forms"
                    />
                  ) : topForms.length > 0 ? (
                    <Grid container spacing={2}>
                      {topForms.slice(0, 6).map((form: TopFormData) => (
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
                    <Box textAlign="center" py={4}>
                      <Info sx={{ fontSize: 48, color: theme.palette.info.main, mb: 2 }} />
                      <Typography variant="h6" color="textSecondary">
                        No Form Data Available
                      </Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        There are no forms to display at the moment.
                      </Typography>
                      <Button
                        variant="outlined"
                        onClick={handleRetryTopForms}
                        startIcon={<Refresh />}
                      >
                        Refresh
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Geographic Distribution */}
            <Grid item xs={12} lg={4}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      Geographic Distribution
                    </Typography>
                    <Tooltip title="Refresh geographic data">
                      <IconButton
                        size="small"
                        onClick={handleRetryGeographic}
                        disabled={loading.geographic || isRetrying}
                      >
                        <Refresh />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  
                  {loading.geographic ? (
                    <Box display="flex" flexDirection="column" gap={2}>
                      {[1, 2, 3, 4, 5].map((i) => (
                        <Skeleton key={i} variant="rectangular" height={30} />
                      ))}
                    </Box>
                  ) : errors.geographic ? (
                    <ErrorFallback
                      error={errors.geographic}
                      onRetry={handleRetryGeographic}
                      title="Failed to Load Geographic Data"
                    />
                  ) : geoData ? (
                    <Box>
                      {geoData.countries.slice(0, 5).map((country: { name: string; count: number; percentage: number }) => (
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
                    <Box textAlign="center" py={4}>
                      <Warning sx={{ fontSize: 48, color: theme.palette.warning.main, mb: 2 }} />
                      <Typography variant="h6" color="textSecondary">
                        No Geographic Data
                      </Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        Geographic distribution data is not available.
                      </Typography>
                      <Button
                        variant="outlined"
                        onClick={handleRetryGeographic}
                        startIcon={<Refresh />}
                      >
                        Refresh
                      </Button>
                    </Box>
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
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      Form Performance Analysis
                    </Typography>
                    <Tooltip title="Refresh performance data">
                      <IconButton
                        size="small"
                        onClick={handleRetryPerformance}
                        disabled={loading.performance || isRetrying}
                      >
                        <Refresh />
                      </IconButton>
                    </Tooltip>
                  </Box>
                  <Divider sx={{ mb: 2 }} />
                  
                  {loading.performance ? (
                    <Box display="flex" flexDirection="column" gap={2}>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((i) => (
                        <Skeleton key={i} variant="rectangular" height={120} />
                      ))}
                    </Box>
                  ) : errors.performance ? (
                    <ErrorFallback
                      error={errors.performance}
                      onRetry={handleRetryPerformance}
                      title="Failed to Load Performance Data"
                    />
                  ) : performanceData ? (
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
                        {performanceData.forms.slice(0, 9).map((form: { name: string; current: number; previous: number }) => (
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
                    <Box textAlign="center" py={4}>
                      <Info sx={{ fontSize: 48, color: theme.palette.info.main, mb: 2 }} />
                      <Typography variant="h6" color="textSecondary">
                        No Performance Data
                      </Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        Performance comparison data is not available.
                      </Typography>
                      <Button
                        variant="outlined"
                        onClick={handleRetryPerformance}
                        startIcon={<Refresh />}
                      >
                        Refresh
                      </Button>
                    </Box>
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
                  {topForms.length > 0 ? (
                    topForms.map((form: TopFormData) => (
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
                        disabled={loading.fieldAnalytics}
                      >
                        {form.form_name}
                      </Button>
                    ))
                  ) : (
                    <Box textAlign="center" py={4}>
                      <Info sx={{ fontSize: 48, color: theme.palette.info.main, mb: 2 }} />
                      <Typography variant="h6" color="textSecondary">
                        No Forms Available
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Please load forms first to analyze field completion.
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} lg={8}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      Field Completion Analysis
                    </Typography>
                    {selectedFormId && (
                      <Tooltip title="Refresh field analytics">
                        <IconButton
                          size="small"
                          onClick={handleRetryFieldAnalytics}
                          disabled={loading.fieldAnalytics || isRetrying}
                        >
                          <Refresh />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                  <Divider sx={{ mb: 2 }} />

                  {loading.fieldAnalytics ? (
                    <Box display="flex" flexDirection="column" gap={2}>
                      {[1, 2, 3, 4].map((i) => (
                        <Skeleton key={i} variant="rectangular" height={150} />
                      ))}
                    </Box>
                  ) : errors.fieldAnalytics ? (
                    <ErrorFallback
                      error={errors.fieldAnalytics}
                      onRetry={handleRetryFieldAnalytics}
                      title="Failed to Load Field Analytics"
                    />
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
                    <Box textAlign="center" py={4}>
                      <Info sx={{ fontSize: 48, color: theme.palette.info.main, mb: 2 }} />
                      <Typography variant="h6" color="textSecondary">
                        Select a Form
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        Choose a form from the left panel to view field completion analysis.
                      </Typography>
                    </Box>
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
