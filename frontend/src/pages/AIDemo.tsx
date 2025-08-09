import React from "react";
import { useState } from "react";
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
} from "@mui/material";
import { BrainIcon } from "@mui/icons-material";
import {
  AIHub,
  AIAnalysisDashboard,
  AIReportSuggestions,
  AISmartPlaceholders,
} from "../components/ai";
import type {
  AIAnalysisResult,
  AIReportSuggestion,
  AIPlaceholder,
} from "../components/ai";

/**
 * Demo page showing how to use the AI components
 * This demonstrates the complete AI functionality integration
 */
export const AIDemo: React.FC = () => {
  const [analysisResult, setAnalysisResult] = useState<AIAnalysisResult | null>(
    null
  );
  const [selectedSuggestion, setSelectedSuggestion] =
    useState<AIReportSuggestion | null>(null);
  const [selectedPlaceholder, setSelectedPlaceholder] =
    useState<AIPlaceholder | null>(null);

  // Sample data for demonstration
  const sampleData = {
    sales: [
      { month: "Jan", revenue: 45000, customers: 120 },
      { month: "Feb", revenue: 52000, customers: 135 },
      { month: "Mar", revenue: 48000, customers: 128 },
      { month: "Apr", revenue: 61000, customers: 158 },
      { month: "May", revenue: 67000, customers: 171 },
    ],
    expenses: {
      marketing: 15000,
      operations: 25000,
      salaries: 45000,
      utilities: 3500,
    },
    kpis: {
      conversion_rate: 3.2,
      customer_satisfaction: 4.1,
      average_order_value: 287.5,
    },
  };

  const sampleReports = [
    {
      title: "Q1 Sales Report",
      type: "sales",
      data: { revenue: 145000, growth: 0.12 },
      created_at: "2024-01-15",
    },
    {
      title: "Marketing Performance",
      type: "marketing",
      data: { campaigns: 5, conversion: 3.2, spend: 15000 },
      created_at: "2024-01-20",
    },
  ];

  const handleAnalysisComplete = (result: AIAnalysisResult) => {
    setAnalysisResult(result);
    console.log("Analysis completed:", result);
  };

  const handleSuggestionApply = (suggestion: AIReportSuggestion) => {
    setSelectedSuggestion(suggestion);
    console.log("Suggestion applied:", suggestion);
  };

  const handlePlaceholderSelect = (placeholder: AIPlaceholder) => {
    setSelectedPlaceholder(placeholder);
    console.log("Placeholder selected:", placeholder);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ textAlign: "center", mb: 4 }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: 2,
            mb: 2,
          }}
        >
          <BrainIcon color="primary" sx={{ fontSize: 48 }} />
          <Typography variant="h2" component="h1" fontWeight="bold">
            AI Components Demo
          </Typography>
        </Box>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Explore the AI-powered features for data analysis, report suggestions,
          and smart placeholders
        </Typography>
      </Box>

      {/* Quick Demo Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                🧠 AI Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Get intelligent insights from your data with AI-powered analysis
              </Typography>
              <AIAnalysisDashboard
                data={sampleData}
                context="sales_dashboard"
                onAnalysisComplete={handleAnalysisComplete}
                autoAnalyze={false}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                💡 Report Suggestions
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Generate smart report suggestions based on your data
              </Typography>
              <AIReportSuggestions
                reports={sampleReports}
                context="business_analytics"
                onSuggestionApply={handleSuggestionApply}
                autoGenerate={false}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
                ✨ Smart Placeholders
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Generate contextual placeholders for dynamic reports
              </Typography>
              <AISmartPlaceholders
                context="financial_report"
                industry="technology"
                onPlaceholderSelect={handlePlaceholderSelect}
                autoGenerate={false}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Results Display */}
      {(analysisResult || selectedSuggestion || selectedPlaceholder) && (
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
              Demo Results
            </Typography>
            <Grid container spacing={2}>
              {analysisResult && (
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography
                        variant="subtitle1"
                        fontWeight="bold"
                        color="primary"
                      >
                        Latest Analysis
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Summary: {analysisResult.summary}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Quality: {analysisResult.data_quality} | Confidence:{" "}
                        {Math.round(analysisResult.confidence_score * 100)}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {selectedSuggestion && (
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography
                        variant="subtitle1"
                        fontWeight="bold"
                        color="secondary"
                      >
                        Applied Suggestion
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Key Metrics: {selectedSuggestion.key_metrics.length}{" "}
                        found
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Quality Score:{" "}
                        {Math.round(
                          selectedSuggestion.report_quality_score * 100
                        )}
                        %
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {selectedPlaceholder && (
                <Grid item xs={12} md={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography
                        variant="subtitle1"
                        fontWeight="bold"
                        color="info.main"
                      >
                        Selected Placeholder
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{ mt: 1, fontFamily: "monospace" }}
                      >
                        {`{{${selectedPlaceholder.name}}}`}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {selectedPlaceholder.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Full AI Hub */}
      <Card elevation={3}>
        <CardContent>
          <Typography variant="h4" fontWeight="bold" sx={{ mb: 3 }}>
            Complete AI Hub
          </Typography>
          <AIHub
            data={sampleData}
            reports={sampleReports}
            context="business_intelligence"
            onAnalysisComplete={handleAnalysisComplete}
            onSuggestionApply={handleSuggestionApply}
            onPlaceholderSelect={handlePlaceholderSelect}
          />
        </CardContent>
      </Card>

      {/* Usage Instructions */}
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
            Usage Instructions
          </Typography>
          <Typography variant="body1" sx={{ mb: 2 }}>
            This demo shows how to integrate AI components into your React
            application:
          </Typography>
          <Box component="ul" sx={{ pl: 2 }}>
            <li>
              <Typography variant="body2">
                <strong>AIAnalysisDashboard:</strong> Analyzes data and provides
                insights, patterns, and recommendations
              </Typography>
            </li>
            <li>
              <Typography variant="body2">
                <strong>AIReportSuggestions:</strong> Generates intelligent
                report structure and content suggestions
              </Typography>
            </li>
            <li>
              <Typography variant="body2">
                <strong>AISmartPlaceholders:</strong> Creates contextual
                placeholders for dynamic content
              </Typography>
            </li>
            <li>
              <Typography variant="body2">
                <strong>AIHub:</strong> Complete interface combining all AI
                features with tabs
              </Typography>
            </li>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            All components include fallback mechanisms and work even when AI
            services are unavailable.
          </Typography>
        </CardContent>
      </Card>
    </Container>
  );
};

export default AIDemo;
