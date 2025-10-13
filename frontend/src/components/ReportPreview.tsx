import React from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
} from "@mui/material";
import {
  TrendingUp,
  Assessment,
  Insights,
  Recommend,
  BarChart,
} from "@mui/icons-material";
import type { Report } from "../types/reports";

interface ReportPreviewProps {
  report: Report;
}

const ReportPreview: React.FC<ReportPreviewProps> = ({ report }) => {
  const formatMetricValue = (value: number | string): string => {
    if (typeof value === "number") {
      return value.toLocaleString();
    }
    return value.toString();
  };

  const getMetricIcon = (key: string) => {
    const lowerKey = key.toLowerCase();
    if (lowerKey.includes("trend") || lowerKey.includes("growth")) {
      return <TrendingUp color="primary" />;
    }
    if (lowerKey.includes("chart") || lowerKey.includes("graph")) {
      return <BarChart color="secondary" />;
    }
    if (lowerKey.includes("insight") || lowerKey.includes("analysis")) {
      return <Insights color="info" />;
    }
    return <Assessment color="action" />;
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Report Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {report.title}
        </Typography>
        <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
          <Chip
            label={`Status: ${report.status}`}
            color={report.status === "completed" ? "success" : "warning"}
          />
          <Chip label={`Form: ${report.formTitle}`} variant="outlined" />
          <Chip
            label={`${report.submissionCount} submissions`}
            variant="outlined"
          />
        </Box>
        <Typography variant="body2" color="text.secondary">
          Generated on:{" "}
          {new Date(report.createdAt).toLocaleDateString("en-US", {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </Typography>
      </Box>

      {/* AI Insights Section */}
      {report.aiInsights && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography
              variant="h5"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              <Insights color="primary" />
              AI Analysis Summary
            </Typography>

            <Typography variant="body1" paragraph>
              {report.aiInsights.summary}
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Grid container spacing={3}>
              {/* Key Metrics */}
              {Object.keys(report.aiInsights.keyMetrics).length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography
                    variant="h6"
                    gutterBottom
                    sx={{ display: "flex", alignItems: "center", gap: 1 }}
                  >
                    <Assessment color="secondary" />
                    Key Metrics
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Grid container spacing={2}>
                      {Object.entries(report.aiInsights.keyMetrics).map(
                        ([key, value]) => (
                          <Grid item xs={12} sm={6} key={key}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                                mb: 1,
                              }}
                            >
                              {getMetricIcon(key)}
                              <Box>
                                <Typography
                                  variant="body2"
                                  color="text.secondary"
                                >
                                  {key
                                    .replace(/([A-Z])/g, " $1")
                                    .replace(/^./, (str: any) => str.toUpperCase())}
                                </Typography>
                                <Typography variant="h6" color="primary">
                                  {formatMetricValue(value)}
                                </Typography>
                              </Box>
                            </Box>
                          </Grid>
                        )
                      )}
                    </Grid>
                  </Paper>
                </Grid>
              )}

              {/* Trends */}
              {report.aiInsights.trends.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography
                    variant="h6"
                    gutterBottom
                    sx={{ display: "flex", alignItems: "center", gap: 1 }}
                  >
                    <TrendingUp color="success" />
                    Identified Trends
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 1 }}>
                    <List dense>
                      {report.aiInsights.trends.map((trend, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <TrendingUp fontSize="small" color="success" />
                          </ListItemIcon>
                          <ListItemText
                            primary={trend}
                            primaryTypographyProps={{ variant: "body2" }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Grid>
              )}

              {/* Recommendations */}
              {report.aiInsights.recommendations.length > 0 && (
                <Grid item xs={12}>
                  <Typography
                    variant="h6"
                    gutterBottom
                    sx={{ display: "flex", alignItems: "center", gap: 1 }}
                  >
                    <Recommend color="info" />
                    Recommendations
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 1 }}>
                    <List dense>
                      {report.aiInsights.recommendations.map(
                        (recommendation, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <Recommend fontSize="small" color="info" />
                            </ListItemIcon>
                            <ListItemText
                              primary={recommendation}
                              primaryTypographyProps={{ variant: "body2" }}
                            />
                          </ListItem>
                        )
                      )}
                    </List>
                  </Paper>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Report Statistics */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Report Statistics
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="h4" color="primary">
                  {report.submissionCount}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Submissions
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="h4" color="secondary">
                  {report.status === "completed" ? "100%" : "0%"}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Completion Rate
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="h4" color="success.main">
                  {report.aiInsights?.trends.length || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Trends Identified
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="h4" color="info.main">
                  {report.aiInsights?.recommendations.length || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Recommendations
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Error Information */}
      {report.status === "failed" && report.errorMessage && (
        <Card sx={{ mt: 2, bgcolor: "error.light" }}>
          <CardContent>
            <Typography variant="h6" color="error.contrastText" gutterBottom>
              Generation Failed
            </Typography>
            <Typography variant="body2" color="error.contrastText">
              {report.errorMessage}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ReportPreview;
