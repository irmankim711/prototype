/**
 * Advanced Analytics Panel
 * Displays comprehensive data insights, quality metrics, and statistical analysis
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Grid,
  Card,
  CardContent,
  alpha,
  useTheme,
} from '@mui/material';
import {
  ExpandMore,
  Analytics,
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Warning,
  CheckCircle,
  Error,
  Info,
  DataUsage,
  Assessment,
  Insights,
  Timeline,
  ShowChart,
} from '@mui/icons-material';
import type { 
  DataField, 
  RawDataPoint,
  DataQualityMetrics,
  AdvancedInsights,
  DataAggregation,
  TimeSeriesAnalysis 
} from './types';
import { advancedDataService } from '../../services/advancedDataService';

interface AdvancedAnalyticsPanelProps {
  data: RawDataPoint[];
  fields: DataField[];
  onInsightsGenerated?: (insights: AdvancedInsights) => void;
}

const AdvancedAnalyticsPanel: React.FC<AdvancedAnalyticsPanelProps> = ({
  data,
  fields,
  onInsightsGenerated,
}) => {
  const theme = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [dataQuality, setDataQuality] = useState<DataQualityMetrics | null>(null);
  const [insights, setInsights] = useState<AdvancedInsights | null>(null);
  const [aggregations, setAggregations] = useState<Record<string, DataAggregation>>({});
  const [timeSeriesAnalysis, setTimeSeriesAnalysis] = useState<Record<string, TimeSeriesAnalysis>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (data.length > 0 && fields.length > 0) {
      generateAnalytics();
    }
  }, [data, fields]);

  const generateAnalytics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Generate data quality metrics
      const quality = advancedDataService.assessDataQuality(data, fields);
      setDataQuality(quality);

      // Generate advanced insights
      const advancedInsights = advancedDataService.generateAdvancedInsights(data, fields);
      setInsights(advancedInsights);
      onInsightsGenerated?.(advancedInsights);

      // Generate aggregations for numerical fields
      const numericalFields = fields.filter(f => f.dataType === 'numerical');
      const aggResults: Record<string, DataAggregation> = {};
      
      for (const field of numericalFields) {
        try {
          const agg = advancedDataService.aggregateData(data, field.id);
          if (typeof agg === 'object' && 'sum' in agg) {
            aggResults[field.id] = agg as DataAggregation;
          }
        } catch (err) {
          // Silently skip failed aggregations
          continue;
        }
      }
      setAggregations(aggResults);

      // Generate time series analysis for temporal fields
      const temporalFields = fields.filter(f => f.dataType === 'temporal');
      const numericalFieldsForTime = fields.filter(f => f.dataType === 'numerical');
      
      if (temporalFields.length > 0 && numericalFieldsForTime.length > 0) {
        const timeResults: Record<string, TimeSeriesAnalysis> = {};
        
        for (const timeField of temporalFields) {
          for (const valueField of numericalFieldsForTime) {
            try {
              const analysis = advancedDataService.analyzeTimeSeries(data, timeField.id, valueField.id);
              timeResults[`${timeField.id}_${valueField.id}`] = analysis;
            } catch (err) {
              // Silently skip failed time series analysis
              continue;
            }
          }
        }
        setTimeSeriesAnalysis(timeResults);
      }

    } catch (err: any) {
      setError(err.message || 'Failed to generate analytics');
    } finally {
      setIsLoading(false);
    }
  }, [data, fields, onInsightsGenerated]);

  const getQualityColor = (score: number) => {
    if (score >= 0.9) return theme.palette.success.main;
    if (score >= 0.7) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  const getQualityIcon = (score: number) => {
    if (score >= 0.9) return <CheckCircle color="success" />;
    if (score >= 0.7) return <Warning color="warning" />;
    return <Error color="error" />;
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return <TrendingUp color="success" />;
      case 'down':
        return <TrendingDown color="error" />;
      case 'stable':
        return <TrendingFlat color="info" />;
      default:
        return <TrendingFlat color="info" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return theme.palette.error.main;
      case 'medium':
        return theme.palette.warning.main;
      case 'low':
        return theme.palette.info.main;
      default:
        return theme.palette.info.main;
    }
  };

  if (isLoading) {
    return (
      <Box p={2}>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <Analytics color="primary" />
          <Typography variant="h6" fontWeight="semibold">
            Advanced Analytics
          </Typography>
        </Box>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" textAlign="center" mt={2}>
          Generating comprehensive analytics...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={2}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Typography variant="body2" color="text.secondary">
          Failed to generate analytics. Please check your data and try again.
        </Typography>
      </Box>
    );
  }

  if (!dataQuality || !insights) {
    return (
      <Box p={2}>
        <Typography variant="body2" color="text.secondary">
          No analytics available. Please ensure you have data loaded.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      <Box display="flex" alignItems="center" gap={1} mb={3}>
        <Analytics color="primary" />
        <Typography variant="h6" fontWeight="semibold">
          Advanced Analytics
        </Typography>
      </Box>

      {/* Data Quality Overview */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <DataUsage fontSize="small" />
            <Typography variant="subtitle1" fontWeight="medium">
              Data Quality Assessment
            </Typography>
            <Chip
              label={`${(dataQuality.overallScore * 100).toFixed(1)}%`}
              color={dataQuality.overallScore >= 0.9 ? 'success' : dataQuality.overallScore >= 0.7 ? 'warning' : 'error'}
              size="small"
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            {Object.entries({
              'Completeness': dataQuality.completeness,
              'Accuracy': dataQuality.accuracy,
              'Consistency': dataQuality.consistency,
              'Validity': dataQuality.validity,
              'Uniqueness': dataQuality.uniqueness,
            }).map(([metric, score]) => (
              <Grid item xs={12} sm={6} md={4} key={metric}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      {getQualityIcon(score)}
                      <Typography variant="body2" fontWeight="medium">
                        {metric}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={score * 100}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: alpha(getQualityColor(score), 0.2),
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: getQualityColor(score),
                        },
                      }}
                    />
                    <Typography variant="caption" color="text.secondary" mt={1} display="block">
                      {(score * 100).toFixed(1)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {dataQuality.issues.length > 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" mb={1}>
                Data Quality Issues:
              </Typography>
              <List dense>
                {dataQuality.issues.map((issue, index) => (
                  <ListItem key={index} sx={{ py: 0 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <Warning fontSize="small" color="warning" />
                    </ListItemIcon>
                    <ListItemText primary={issue} />
                  </ListItem>
                ))}
              </List>
            </Alert>
          )}

          {dataQuality.recommendations.length > 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" mb={1}>
                Recommendations:
              </Typography>
              <List dense>
                {dataQuality.recommendations.map((rec, index) => (
                  <ListItem key={index} sx={{ py: 0 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <Info fontSize="small" color="info" />
                    </ListItemIcon>
                    <ListItemText primary={rec} />
                  </ListItem>
                ))}
              </List>
            </Alert>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Statistical Aggregations */}
      {Object.keys(aggregations).length > 0 && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box display="flex" alignItems="center" gap={1}>
              <Assessment fontSize="small" />
              <Typography variant="subtitle1" fontWeight="medium">
                Statistical Aggregations
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {Object.entries(aggregations).map(([fieldId, agg]) => {
                const field = fields.find(f => f.id === fieldId);
                return (
                  <Grid item xs={12} sm={6} key={fieldId}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" fontWeight="medium" mb={2}>
                          {field?.name || fieldId}
                        </Typography>
                        <Grid container spacing={1}>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Count</Typography>
                            <Typography variant="body2" fontWeight="medium">{agg.count}</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Sum</Typography>
                            <Typography variant="body2" fontWeight="medium">{agg.sum.toLocaleString()}</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Average</Typography>
                            <Typography variant="body2" fontWeight="medium">{agg.average.toFixed(2)}</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Median</Typography>
                            <Typography variant="body2" fontWeight="medium">{agg.median.toFixed(2)}</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Min</Typography>
                            <Typography variant="body2" fontWeight="medium">{agg.min.toLocaleString()}</Typography>
                          </Grid>
                          <Grid item xs={6}>
                            <Typography variant="caption" color="text.secondary">Max</Typography>
                            <Typography variant="body2" fontWeight="medium">{agg.max.toLocaleString()}</Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Time Series Analysis */}
      {Object.keys(timeSeriesAnalysis).length > 0 && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box display="flex" alignItems="center" gap={1}>
              <Timeline fontSize="small" />
              <Typography variant="subtitle1" fontWeight="medium">
                Time Series Analysis
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {Object.entries(timeSeriesAnalysis).map(([key, analysis]) => {
                const [timeField, valueField] = key.split('_');
                const timeFieldName = fields.find(f => f.id === timeField)?.name || timeField;
                const valueFieldName = fields.find(f => f.id === valueField)?.name || valueField;
                
                return (
                  <Grid item xs={12} sm={6} key={key}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" fontWeight="medium" mb={2}>
                          {timeFieldName} vs {valueFieldName}
                        </Typography>
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          {getTrendIcon(analysis.trend)}
                          <Typography variant="body2" fontWeight="medium">
                            {analysis.trend.charAt(0).toUpperCase() + analysis.trend.slice(1)} Trend
                          </Typography>
                          <Chip
                            label={`${(analysis.trendStrength * 100).toFixed(1)}%`}
                            size="small"
                            color="primary"
                          />
                        </Box>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Seasonality: {analysis.seasonality ? 'Detected' : 'Not detected'}
                          {analysis.seasonality && ` (${(analysis.seasonalityStrength * 100).toFixed(1)}% strength)`}
                        </Typography>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="caption" color="text.secondary" display="block">
                          Next Value Forecast: {analysis.forecast.nextValue.toFixed(2)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block">
                          Confidence: {(analysis.forecast.confidence * 100).toFixed(1)}%
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Advanced Insights */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Insights fontSize="small" />
            <Typography variant="subtitle1" fontWeight="medium">
              Advanced Insights
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {/* Patterns */}
          {insights.patterns.length > 0 && (
            <Box mb={3}>
              <Typography variant="subtitle2" fontWeight="medium" mb={1}>
                Detected Patterns
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {insights.patterns.map((pattern, index) => (
                  <Chip
                    key={index}
                    label={pattern}
                    size="small"
                    color="info"
                    variant="outlined"
                    icon={<ShowChart />}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Anomalies */}
          {insights.anomalies.length > 0 && (
            <Box mb={3}>
              <Typography variant="subtitle2" fontWeight="medium" mb={1}>
                Detected Anomalies
              </Typography>
              <List dense>
                {insights.anomalies.map((anomaly, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <Warning
                        fontSize="small"
                        sx={{ color: getSeverityColor(anomaly.severity) }}
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={anomaly.description}
                      secondary={`Value: ${anomaly.value.toFixed(2)} | Expected: ${anomaly.expectedRange[0].toFixed(2)} - ${anomaly.expectedRange[1].toFixed(2)}`}
                    />
                    <Chip
                      label={anomaly.severity}
                      size="small"
                      color={anomaly.severity === 'high' ? 'error' : anomaly.severity === 'medium' ? 'warning' : 'info'}
                      variant="outlined"
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Trends */}
          {insights.trends.length > 0 && (
            <Box mb={3}>
              <Typography variant="subtitle2" fontWeight="medium" mb={1}>
                Trend Analysis
              </Typography>
              <Grid container spacing={2}>
                {insights.trends.map((trend, index) => (
                  <Grid item xs={12} sm={6} key={index}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          {getTrendIcon(trend.direction)}
                          <Typography variant="body2" fontWeight="medium">
                            {trend.field}
                          </Typography>
                        </Box>
                        <Typography variant="caption" color="text.secondary" display="block">
                          {trend.description}
                        </Typography>
                        <Box display="flex" gap={1} mt={1}>
                          <Chip
                            label={`${(trend.strength * 100).toFixed(1)}% strength`}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                          <Chip
                            label={`${(trend.confidence * 100).toFixed(1)}% confidence`}
                            size="small"
                            color="secondary"
                            variant="outlined"
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {/* Recommendations */}
          {insights.recommendations.length > 0 && (
            <Box>
              <Typography variant="subtitle2" fontWeight="medium" mb={1}>
                Recommendations
              </Typography>
              <List dense>
                {insights.recommendations.map((rec, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon sx={{ minWidth: 32 }}>
                      <Info fontSize="small" color="info" />
                    </ListItemIcon>
                    <ListItemText primary={rec} />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default AdvancedAnalyticsPanel;
