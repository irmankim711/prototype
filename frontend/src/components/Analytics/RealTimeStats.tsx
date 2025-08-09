import React from "react";
import { useState, useEffect } from "react";
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
  useTheme,
} from "@mui/material";
import {
  TrendingUp,
  TrendingDown,
  Timeline,
  Assignment,
  AccessTime,
} from "@mui/icons-material";
import { analyticsService } from "../../services/analyticsService";
import type { AnalyticsStats } from "../../services/analyticsService";

interface RealTimeStatsProps {
  refreshInterval?: number; // in milliseconds
}

export const RealTimeStats: React.FC<RealTimeStatsProps> = ({
  refreshInterval = 30000, // Default 30 seconds
}) => {
  const theme = useTheme();
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchStats = async () => {
    try {
      const data = await analyticsService.getRealTimeStats();
      setStats(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error("Error fetching real-time stats:", err);
      setError("Failed to fetch real-time statistics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();

    // Set up polling for real-time updates
    const interval = setInterval(fetchStats, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

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

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height={200}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error || !stats) {
    return (
      <Paper sx={{ p: 3, textAlign: "center" }}>
        <Typography color="error">{error || "No data available"}</Typography>
      </Paper>
    );
  }

  return (
    <Box>
      {/* Header with last updated timestamp */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h6" component="h3">
          Real-Time Statistics
        </Typography>
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
      </Box>

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
