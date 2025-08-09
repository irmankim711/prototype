import React from "react";
import { useState, useEffect, useCallback } from "react";
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
} from "@mui/material";
import {
  Psychology as BrainIcon,
  TrendingUp,
  Warning as AlertTriangleIcon,
  Lightbulb as LightbulbIcon,
  GpsFixed as TargetIcon,
  FlashOn as ZapIcon,
} from "@mui/icons-material";
import { AIService, AIUtils } from "../../services/aiService";
import type { AIAnalysisResult } from "../../services/aiService";

interface AIAnalysisDashboardProps {
  data: Record<string, unknown>;
  context?: string;
  onAnalysisComplete?: (result: AIAnalysisResult) => void;
  autoAnalyze?: boolean;
}

export const AIAnalysisDashboard: React.FC<AIAnalysisDashboardProps> = ({
  data,
  context = "general",
  onAnalysisComplete,
  autoAnalyze = false,
}) => {
  const [analysis, setAnalysis] = useState<AIAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performAnalysis = useCallback(async () => {
    if (!data || Object.keys(data).length === 0) {
      setError("No data provided for analysis");
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await AIService.analyzeData(data, context);
      setAnalysis(result);
      onAnalysisComplete?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  }, [data, context, onAnalysisComplete]);

  useEffect(() => {
    if (autoAnalyze && data && Object.keys(data).length > 0) {
      performAnalysis();
    }
  }, [autoAnalyze, data, performAnalysis]);

  const getQualityColor = (
    quality: string
  ): "primary" | "secondary" | "error" | "warning" | "info" | "success" => {
    switch (quality) {
      case "high":
        return "success";
      case "medium":
        return "warning";
      case "low":
        return "error";
      default:
        return "secondary";
    }
  };

  return (
    <Box sx={{ padding: 3 }}>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <BrainIcon color="primary" sx={{ fontSize: 32 }} />
          <Typography variant="h4" component="h2" fontWeight="bold">
            AI Analysis Dashboard
          </Typography>
        </Box>
        <Button
          variant="contained"
          onClick={performAnalysis}
          disabled={isAnalyzing || !data || Object.keys(data).length === 0}
          startIcon={
            isAnalyzing ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              <ZapIcon />
            )
          }
          sx={{ minWidth: 150 }}
        >
          {isAnalyzing ? "Analyzing..." : "Analyze Data"}
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Analysis Error</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Analysis Results */}
      {analysis && (
        <Grid container spacing={3}>
          {/* Summary Card */}
          <Grid item xs={12}>
            <Card elevation={2}>
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "between",
                    alignItems: "flex-start",
                    mb: 2,
                  }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 2,
                    }}
                  >
                    <BrainIcon color="primary" />
                    <Typography variant="h6" fontWeight="bold">
                      Analysis Summary
                    </Typography>
                  </Box>
                  <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                    <Chip
                      label={`${analysis.data_quality.toUpperCase()} Quality`}
                      color={getQualityColor(analysis.data_quality)}
                      size="small"
                    />
                    <Chip
                      label={
                        AIUtils.isAIPowered(analysis)
                          ? "AI-Powered"
                          : "Rule-Based"
                      }
                      color={
                        AIUtils.isAIPowered(analysis) ? "primary" : "secondary"
                      }
                      size="small"
                    />
                  </Box>
                </Box>

                <Typography
                  variant="body1"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  {analysis.summary}
                </Typography>

                <Box
                  sx={{
                    display: "flex",
                    gap: 2,
                    flexWrap: "wrap",
                    fontSize: "0.875rem",
                    color: "text.secondary",
                  }}
                >
                  <span>
                    Confidence:{" "}
                    {AIUtils.formatConfidence(analysis.confidence_score)}
                  </span>
                  <span>•</span>
                  <span>Type: {analysis.analysis_type}</span>
                  <span>•</span>
                  <span>{AIUtils.formatTimestamp(analysis.timestamp)}</span>
                </Box>

                {AIUtils.getFallbackMessage(analysis) && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    {AIUtils.getFallbackMessage(analysis)}
                  </Alert>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Insights Card */}
          <Grid item xs={12} md={6}>
            <Card elevation={2} sx={{ height: "100%" }}>
              <CardContent>
                <Box
                  sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}
                >
                  <LightbulbIcon sx={{ color: "#FFA726" }} />
                  <Typography variant="h6" fontWeight="bold">
                    Key Insights
                  </Typography>
                </Box>
                {analysis.insights.length > 0 ? (
                  <List dense>
                    {analysis.insights.map((insight: string, index: number) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <Box sx={{ fontSize: "1.2em" }}>💡</Box>
                        </ListItemIcon>
                        <ListItemText
                          primary={insight}
                          primaryTypographyProps={{ variant: "body2" }}
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No specific insights identified
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Recommendations Card */}
          <Grid item xs={12} md={6}>
            <Card elevation={2} sx={{ height: "100%" }}>
              <CardContent>
                <Box
                  sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}
                >
                  <TargetIcon sx={{ color: "#4CAF50" }} />
                  <Typography variant="h6" fontWeight="bold">
                    Recommendations
                  </Typography>
                </Box>
                {analysis.recommendations.length > 0 ? (
                  <List dense>
                    {analysis.recommendations.map(
                      (recommendation: string, index: number) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <Box sx={{ fontSize: "1.2em" }}>🎯</Box>
                          </ListItemIcon>
                          <ListItemText
                            primary={recommendation}
                            primaryTypographyProps={{ variant: "body2" }}
                          />
                        </ListItem>
                      )
                    )}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No specific recommendations at this time
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Patterns Card */}
          {analysis.patterns.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 2,
                    }}
                  >
                    <TrendingUp sx={{ color: "#2196F3" }} />
                    <Typography variant="h6" fontWeight="bold">
                      Patterns Detected
                    </Typography>
                  </Box>
                  <List dense>
                    {analysis.patterns.map((pattern: string, index: number) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <Box sx={{ fontSize: "1.2em" }}>📊</Box>
                        </ListItemIcon>
                        <ListItemText
                          primary={pattern}
                          primaryTypographyProps={{ variant: "body2" }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Anomalies Card */}
          {analysis.anomalies.length > 0 && (
            <Grid item xs={12} md={6}>
              <Card elevation={2}>
                <CardContent>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                      mb: 2,
                    }}
                  >
                    <AlertTriangleIcon sx={{ color: "#F44336" }} />
                    <Typography variant="h6" fontWeight="bold">
                      Anomalies
                    </Typography>
                  </Box>
                  <List dense>
                    {analysis.anomalies.map(
                      (anomaly: string, index: number) => (
                        <ListItem key={index} sx={{ px: 0 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <Box sx={{ fontSize: "1.2em" }}>⚠️</Box>
                          </ListItemIcon>
                          <ListItemText
                            primary={anomaly}
                            primaryTypographyProps={{ variant: "body2" }}
                          />
                        </ListItem>
                      )
                    )}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Risks and Opportunities */}
          {(analysis.risks.length > 0 || analysis.opportunities.length > 0) && (
            <Grid item xs={12}>
              <Card elevation={2}>
                <CardContent>
                  <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                    Risk Assessment & Opportunities
                  </Typography>
                  <Grid container spacing={3}>
                    {analysis.risks.length > 0 && (
                      <Grid item xs={12} md={6}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            mb: 1,
                          }}
                        >
                          <AlertTriangleIcon
                            sx={{ color: "#F44336", fontSize: 20 }}
                          />
                          <Typography
                            variant="subtitle1"
                            fontWeight="bold"
                            color="error"
                          >
                            Risks
                          </Typography>
                        </Box>
                        <List dense>
                          {analysis.risks.map((risk: string, index: number) => (
                            <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                              <ListItemText
                                primary={`• ${risk}`}
                                primaryTypographyProps={{
                                  variant: "body2",
                                  color: "text.secondary",
                                }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Grid>
                    )}
                    {analysis.opportunities.length > 0 && (
                      <Grid item xs={12} md={6}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            gap: 1,
                            mb: 1,
                          }}
                        >
                          <TrendingUp sx={{ color: "#4CAF50", fontSize: 20 }} />
                          <Typography
                            variant="subtitle1"
                            fontWeight="bold"
                            color="success.main"
                          >
                            Opportunities
                          </Typography>
                        </Box>
                        <List dense>
                          {analysis.opportunities.map(
                            (opportunity: string, index: number) => (
                              <ListItem key={index} sx={{ px: 0, py: 0.5 }}>
                                <ListItemText
                                  primary={`• ${opportunity}`}
                                  primaryTypographyProps={{
                                    variant: "body2",
                                    color: "text.secondary",
                                  }}
                                />
                              </ListItem>
                            )
                          )}
                        </List>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* Loading State */}
      {isAnalyzing && (
        <Card elevation={2}>
          <CardContent sx={{ py: 6 }}>
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 2,
              }}
            >
              <CircularProgress size={48} />
              <Box sx={{ textAlign: "center" }}>
                <Typography variant="h6" fontWeight="bold">
                  Analyzing Your Data
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Our AI is processing your data to generate insights...
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* No Data State */}
      {!data || Object.keys(data).length === 0 ? (
        <Card elevation={2}>
          <CardContent sx={{ py: 6 }}>
            <Box
              sx={{
                textAlign: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 2,
              }}
            >
              <BrainIcon sx={{ fontSize: 64, color: "text.disabled" }} />
              <Box>
                <Typography variant="h6" fontWeight="bold" color="text.primary">
                  No Data to Analyze
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Provide data to get AI-powered insights and recommendations
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      ) : null}
    </Box>
  );
};

export default AIAnalysisDashboard;
