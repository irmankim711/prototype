import React from "react";
import { useState, useEffect, useCallback, useRef } from "react";
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Paper,
  CircularProgress,
  Button,
  Alert,
  AlertTitle,
  Collapse,
  IconButton,
  Tooltip,
  useTheme,
} from "@mui/material";
import {
  TrendingUp,
  TrendingDown,
  Timeline,
  Assignment,
  AccessTime,
  Refresh,
  Error,
  Warning,
  Info,
  ExpandMore,
  ExpandLess,
} from "@mui/icons-material";
import { analyticsService } from "../../services/analyticsService";
import type { AnalyticsStats } from "../../services/analyticsService";

interface RealTimeStatsProps {
  refreshInterval?: number; // in milliseconds
  maxRetries?: number;
  retryDelay?: number;
}

export const RealTimeStats: React.FC<RealTimeStatsProps> = ({
  refreshInterval = 30000, // Default 30 seconds
  maxRetries = 3,
  retryDelay = 2000,
}) => {
  const theme = useTheme();
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  const [isPolling, setIsPolling] = useState(true);

  // Ref to track retry timeout for cleanup
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const fetchStats = useCallback(async (isRetry: boolean = false) => {
    if (isRetry) {
      setIsRetrying(true);
    } else {
      setLoading(true);
    }
    
    try {
      const data = await analyticsService.getRealTimeStats();
      setStats(data);
      setLastUpdated(new Date());
      setError(null);
      setRetryCount(0); // Reset retry count on success
    } catch (err: any) {
      console.error("Error fetching real-time stats:", err);
      
      const errorMessage = err.message || "Failed to fetch real-time statistics";
      setError(errorMessage);
      
      // Handle retry logic
      if (retryCount < maxRetries && !isRetry) {
        setRetryCount(prev => prev + 1);
        setTimeout(() => {
          fetchStats(true);
        }, retryDelay);
      }
    } finally {
      setLoading(false);
      setIsRetrying(false);
    }
  }, [retryCount, maxRetries, retryDelay]);

  const handleRetry = () => {
    setRetryCount(0);
    fetchStats();
  };

  const handleRefresh = () => {
    fetchStats();
  };

  const togglePolling = () => {
    setIsPolling(!isPolling);
  };

  useEffect(() => {
    let isMounted = true;
    let interval: NodeJS.Timeout | null = null;

    const fetchStatsSafely = async (isRetry: boolean = false) => {
      if (!isMounted) return;
      
      if (isRetry) {
        setIsRetrying(true);
      } else {
        setLoading(true);
      }
      
      try {
        const data = await analyticsService.getRealTimeStats();
        if (!isMounted) return;
        
        setStats(data);
        setLastUpdated(new Date());
        setError(null);
        setRetryCount(0); // Reset retry count on success
      } catch (err: any) {
        if (!isMounted) return;
        
        console.error("Error fetching real-time stats:", err);
        
        const errorMessage = err.message || "Failed to fetch real-time statistics";
        setError(errorMessage);
        
        // Handle retry logic
        if (retryCount < maxRetries && !isRetry) {
          setRetryCount(prev => prev + 1);
          retryTimeoutRef.current = setTimeout(() => {
            if (isMounted) {
              fetchStatsSafely(true);
            }
          }, retryDelay);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
          setIsRetrying(false);
        }
      }
    };

    fetchStatsSafely();

    // Set up polling for real-time updates only when polling is enabled
    if (isPolling) {
      interval = setInterval(() => {
        if (isMounted && !loading && !isRetrying) {
          fetchStatsSafely();
        }
      }, refreshInterval);
    }

    return () => {
      isMounted = false;
      if (interval) {
        clearInterval(interval);
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    };
  }, [refreshInterval, isPolling, loading, isRetrying, retryCount, maxRetries, retryDelay]);

  // Additional cleanup effect for component unmount
  useEffect(() => {
    return () => {
      // Clear any remaining timeouts on unmount
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    };
  }, []);

  const formatTimeAgo = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);

    if (diffMinutes < 1) return "Just now";
    if (diffMinutes === 1) return "1 minute ago";
    if (diffMinutes < 60) return `${diffMinutes} minutes ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours === 1) return "1 hour ago";
    if (diffHours < 24) return `${diffHours} hours ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return "1 day ago";
    return `${diffDays} days ago`;
  };

  const getActivityColor = (isActive: boolean) => {
    return isActive ? theme.palette.success.main : theme.palette.grey[500];
  };

  // Enhanced loading state with retry information
  if (loading && !isRetrying) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        height={200}
        gap={2}
      >
        <CircularProgress />
        <Typography variant="body2" color="textSecondary">
          Loading real-time statistics...
        </Typography>
      </Box>
    );
  }

  // Retry loading state
  if (isRetrying) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        height={200}
        gap={2}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="textSecondary">
          Retrying... (Attempt {retryCount + 1} of {maxRetries})
        </Typography>
      </Box>
    );
  }

  // Enhanced error state with retry options and details
  if (error || !stats) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert 
          severity="error" 
          action={
            <Box display="flex" gap={1}>
              <Button
                size="small"
                variant="outlined"
                onClick={handleRetry}
                disabled={isRetrying}
                startIcon={<Refresh />}
              >
                Retry
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
          <AlertTitle>Unable to Load Real-Time Statistics</AlertTitle>
          {error || "No data available"}
          
          <Collapse in={showErrorDetails}>
            <Box mt={2}>
              <Typography variant="body2" color="textSecondary">
                <strong>Error Details:</strong> {error || "Data source unavailable"}
              </Typography>
              <Typography variant="body2" color="textSecondary" mt={1}>
                <strong>Retry Count:</strong> {retryCount} of {maxRetries}
              </Typography>
              <Typography variant="body2" color="textSecondary" mt={1}>
                <strong>Last Attempt:</strong> {lastUpdated ? formatTimeAgo(lastUpdated) : "Never"}
              </Typography>
            </Box>
          </Collapse>
        </Alert>

        {/* Fallback UI when analytics data is unavailable */}
        <Box mt={3}>
          <Typography variant="h6" gutterBottom>
            Fallback Statistics
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center' }}>
                  <Info sx={{ fontSize: 40, color: theme.palette.info.main, mb: 1 }} />
                  <Typography variant="h6" color="textSecondary">
                    Data Unavailable
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Real-time statistics are currently unavailable
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center' }}>
                  <Warning sx={{ fontSize: 40, color: theme.palette.warning.main, mb: 1 }} />
                  <Typography variant="h6" color="textSecondary">
                    Connection Issue
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Check your internet connection
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center' }}>
                  <Error sx={{ fontSize: 40, color: theme.palette.error.main, mb: 1 }} />
                  <Typography variant="h6" color="textSecondary">
                    Service Unavailable
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Analytics service may be down
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card variant="outlined">
                <CardContent sx={{ textAlign: 'center' }}>
                  <Refresh sx={{ fontSize: 40, color: theme.palette.primary.main, mb: 1 }} />
                  <Typography variant="h6" color="textSecondary">
                    Manual Refresh
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Click retry to attempt reconnection
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header with last updated timestamp and controls */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h6" component="h3">
          Real-Time Statistics
        </Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Box
              width={8}
              height={8}
              borderRadius="50%"
              bgcolor={getActivityColor(stats.is_active)}
            />
            <Typography variant="caption" color="textSecondary">
              {lastUpdated
                ? `Updated ${formatTimeAgo(lastUpdated)}`
                : "Loading..."}
            </Typography>
          </Box>
          
          {/* Control buttons */}
          <Box display="flex" gap={1}>
            <Tooltip title={isPolling ? "Pause auto-refresh" : "Resume auto-refresh"}>
              <IconButton
                size="small"
                onClick={togglePolling}
                color={isPolling ? "primary" : "default"}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="Manual refresh">
              <IconButton
                size="small"
                onClick={handleRefresh}
                disabled={loading}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Box>

      {/* Success alert when data is loaded */}
      <Collapse in={!!stats && !error}>
        <Alert severity="success" sx={{ mb: 2 }}>
          <Typography variant="body2">
            Real-time data loaded successfully. Auto-refresh is {isPolling ? "enabled" : "paused"}.
          </Typography>
        </Alert>
      </Collapse>

      <Grid container spacing={3}>
        {/* Key Metrics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Last 24 Hours
                  </Typography>
                  <Typography variant="h4">{stats.submissions_24h}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Submissions
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                  <Timeline />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Last Hour
                  </Typography>
                  <Typography variant="h4">{stats.submissions_1h}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    Submissions
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: theme.palette.secondary.main }}>
                  <AccessTime />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Active Forms
                  </Typography>
                  <Typography variant="h4">{stats.active_forms}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    of {stats.total_forms} total
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: theme.palette.success.main }}>
                  <Assignment />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box>
                  <Typography color="textSecondary" gutterBottom variant="h6">
                    Status
                  </Typography>
                  <Chip
                    label={stats.is_active ? "Active" : "Quiet"}
                    color={stats.is_active ? "success" : "default"}
                    variant="filled"
                  />
                  <Typography variant="body2" color="textSecondary" mt={1}>
                    System activity
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: getActivityColor(stats.is_active) }}>
                  {stats.is_active ? <TrendingUp /> : <TrendingDown />}
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Activity Feed */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              {stats.activity_feed.length > 0 ? (
                <List dense>
                  {stats.activity_feed.map((activity: any) => (
                    <ListItem key={activity.id} divider>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: theme.palette.primary.light }}>
                          <Assignment />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={activity.form_title}
                        secondary={`New submission • ${activity.time_ago}`}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary" textAlign="center" py={3}>
                  No recent activity
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Indicator */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Overview
              </Typography>
              <Box mt={2}>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">Form Utilization</Typography>
                  <Typography variant="body2">
                    {stats.total_forms > 0
                      ? Math.round(
                          (stats.active_forms / stats.total_forms) * 100
                        )
                      : 0}
                    %
                  </Typography>
                </Box>
                <Box
                  height={8}
                  bgcolor={theme.palette.grey[200]}
                  borderRadius={4}
                  overflow="hidden"
                >
                  <Box
                    height="100%"
                    width={`${
                      stats.total_forms > 0
                        ? (stats.active_forms / stats.total_forms) * 100
                        : 0
                    }%`}
                    bgcolor={theme.palette.primary.main}
                  />
                </Box>
              </Box>

              <Box mt={3}>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">Recent Activity Level</Typography>
                  <Typography variant="body2">
                    {stats.submissions_1h > 0
                      ? "High"
                      : stats.submissions_24h > 0
                      ? "Medium"
                      : "Low"}
                  </Typography>
                </Box>
                <Box
                  height={8}
                  bgcolor={theme.palette.grey[200]}
                  borderRadius={4}
                  overflow="hidden"
                >
                  <Box
                    height="100%"
                    width={`${
                      stats.submissions_1h > 0
                        ? 100
                        : stats.submissions_24h > 5
                        ? 60
                        : stats.submissions_24h > 0
                        ? 30
                        : 10
                    }%`}
                    bgcolor={
                      stats.submissions_1h > 0
                        ? theme.palette.success.main
                        : stats.submissions_24h > 0
                        ? theme.palette.warning.main
                        : theme.palette.grey[400]
                    }
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default RealTimeStats;
