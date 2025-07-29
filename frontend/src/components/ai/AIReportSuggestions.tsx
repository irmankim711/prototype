import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  AlertTitle,
  Chip,
  Box,
  CircularProgress,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Description as DocumentIcon,
  Lightbulb as LightbulbIcon,
  ExpandMore as ExpandMoreIcon,
  Psychology as BrainIcon,
  TrendingUp,
  Analytics
} from '@mui/icons-material';
import { AIService } from '../../services/aiService';
import type { AIReportSuggestion, AIReportSuggestionsResult } from '../../services/aiService';

interface AIReportSuggestionsProps {
  reports: Record<string, unknown>[];
  context?: string;
  onSuggestionApply?: (suggestion: AIReportSuggestion) => void;
  autoGenerate?: boolean;
}

export const AIReportSuggestions: React.FC<AIReportSuggestionsProps> = ({
  reports,
  context = 'general',
  onSuggestionApply,
  autoGenerate = false
}) => {
  const [result, setResult] = useState<AIReportSuggestionsResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateSuggestions = React.useCallback(async () => {
    if (!reports || reports.length === 0) {
      setError('No reports provided for analysis');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const reportData = reports.reduce((acc, report, index) => ({
        ...acc,
        [`report_${index}`]: report
      }), {});
      
      const suggestionsResult = await AIService.getReportSuggestions(reportData, context);
      setResult(suggestionsResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate suggestions');
    } finally {
      setIsGenerating(false);
    }
  }, [reports, context]);

  useEffect(() => {
    if (autoGenerate && reports && reports.length > 0) {
      generateSuggestions();
    }
  }, [autoGenerate, reports, generateSuggestions]);

  const handleApplySuggestion = () => {
    if (result?.suggestions && onSuggestionApply) {
      onSuggestionApply(result.suggestions);
    }
  };

  return (
    <Box sx={{ padding: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <LightbulbIcon color="primary" sx={{ fontSize: 32 }} />
          <Typography variant="h4" component="h2" fontWeight="bold">
            AI Report Suggestions
          </Typography>
        </Box>
        <Button
          variant="contained"
          onClick={generateSuggestions}
          disabled={isGenerating || !reports || reports.length === 0}
          startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <BrainIcon />}
          sx={{ minWidth: 180 }}
        >
          {isGenerating ? 'Generating...' : 'Generate Suggestions'}
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Generation Error</AlertTitle>
          {error}
        </Alert>
      )}

      {/* AI Status */}
      {result && (
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              label={result.ai_powered ? 'AI-Powered' : 'Rule-Based'}
              color={result.ai_powered ? 'primary' : 'secondary'}
              size="small"
            />
            <Chip
              label={result.report_type.toUpperCase()}
              variant="outlined"
              size="small"
            />
          </Box>
          {result.fallback_reason && (
            <Alert severity="info" sx={{ mt: 2 }}>
              {result.fallback_reason}
            </Alert>
          )}
        </Box>
      )}

      {/* Suggestions Content */}
      {result?.suggestions && (
        <Grid container spacing={3}>
          {/* Key Metrics */}
          <Grid item xs={12} md={6}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Analytics color="primary" />
                  <Typography variant="h6" fontWeight="bold">
                    Key Metrics ({result.suggestions.key_metrics.length})
                  </Typography>
                </Box>
                <List dense>
                  {result.suggestions.key_metrics.map((metric, index) => (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <Chip
                          label={metric.importance.charAt(0).toUpperCase()}
                          color={
                            metric.importance === 'high' ? 'error' :
                            metric.importance === 'medium' ? 'warning' : 'info'
                          }
                          size="small"
                          sx={{ minWidth: 32, height: 24 }}
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={`${metric.metric}: ${metric.value}`}
                        secondary={metric.description}
                        primaryTypographyProps={{ variant: 'body2', fontWeight: 'bold' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Visualizations */}
          <Grid item xs={12} md={6}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <TrendingUp color="secondary" />
                  <Typography variant="h6" fontWeight="bold">
                    Recommended Charts ({result.suggestions.visualizations.length})
                  </Typography>
                </Box>
                <List dense>
                  {result.suggestions.visualizations.map((viz, index) => (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 32 }}>
                        <DocumentIcon color="action" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText
                        primary={viz.type}
                        secondary={`${viz.data_fields.join(', ')} - ${viz.purpose}`}
                        primaryTypographyProps={{ variant: 'body2', fontWeight: 'bold' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Report Sections */}
          <Grid item xs={12}>
            <Card elevation={2}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" fontWeight="bold">
                    Report Structure & Content
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      label={`Quality: ${Math.round(result.suggestions.report_quality_score * 100)}%`}
                      color="success"
                      variant="outlined"
                      size="small"
                    />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={handleApplySuggestion}
                      disabled={!onSuggestionApply}
                    >
                      Apply Suggestions
                    </Button>
                  </Box>
                </Box>

                <Grid container spacing={2}>
                  {/* Trends */}
                  <Grid item xs={12} md={6}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          Trends ({result.suggestions.trends.length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {result.suggestions.trends.map((trend, index) => (
                            <ListItem key={index} sx={{ px: 0 }}>
                              <ListItemText
                                primary={`• ${trend}`}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>

                  {/* Critical Areas */}
                  <Grid item xs={12} md={6}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          Critical Areas ({result.suggestions.critical_areas.length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {result.suggestions.critical_areas.map((area, index) => (
                            <ListItem key={index} sx={{ px: 0 }}>
                              <ListItemText
                                primary={`• ${area}`}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>

                  {/* Executive Points */}
                  <Grid item xs={12} md={6}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          Executive Summary ({result.suggestions.executive_points.length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {result.suggestions.executive_points.map((point, index) => (
                            <ListItem key={index} sx={{ px: 0 }}>
                              <ListItemText
                                primary={`• ${point}`}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>

                  {/* Next Steps */}
                  <Grid item xs={12} md={6}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="subtitle1" fontWeight="bold">
                          Next Steps ({result.suggestions.next_steps.length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List dense>
                          {result.suggestions.next_steps.map((step, index) => (
                            <ListItem key={index} sx={{ px: 0 }}>
                              <ListItemText
                                primary={`${index + 1}. ${step}`}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Loading State */}
      {isGenerating && (
        <Card elevation={2}>
          <CardContent sx={{ py: 6 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <CircularProgress size={48} />
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" fontWeight="bold">Generating Report Suggestions</Typography>
                <Typography variant="body2" color="text.secondary">
                  AI is analyzing your reports to suggest new insights...
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* No Reports State */}
      {!reports || reports.length === 0 ? (
        <Card elevation={2}>
          <CardContent sx={{ py: 6 }}>
            <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <DocumentIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
              <Box>
                <Typography variant="h6" fontWeight="bold" color="text.primary">
                  No Reports Available
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Create some reports first to get AI-powered suggestions
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      ) : null}

      {/* No Suggestions State */}
      {!isGenerating && !result && reports && reports.length > 0 && (
        <Card elevation={2}>
          <CardContent sx={{ py: 6 }}>
            <Box sx={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <LightbulbIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
              <Box>
                <Typography variant="h6" fontWeight="bold" color="text.primary">
                  No Suggestions Yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Click "Generate Suggestions" to get AI-powered report ideas
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default AIReportSuggestions;
