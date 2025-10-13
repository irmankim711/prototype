import React from "react";
import { useState, useEffect } from "react";
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
  TextField,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Snackbar,
} from "@mui/material";
import {
  AutoAwesome as SmartIcon,
  ExpandMore as ExpandMoreIcon,
  ContentCopy as CopyIcon,
  Psychology as BrainIcon,
  Info as InfoIcon,
} from "@mui/icons-material";
import { AIService } from "../../services/aiService";
import type {
  AIPlaceholder,
  AIPlaceholdersResult,
} from "../../services/aiService";

interface AISmartPlaceholdersProps {
  context?: string;
  industry?: string;
  onPlaceholderSelect?: (placeholder: AIPlaceholder) => void;
  autoGenerate?: boolean;
}

export const AISmartPlaceholders: React.FC<AISmartPlaceholdersProps> = ({
  context = "general",
  industry = "general",
  onPlaceholderSelect,
  autoGenerate = false,
}) => {
  const [result, setResult] = useState<AIPlaceholdersResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contextInput, setContextInput] = useState(context);
  const [industryInput, setIndustryInput] = useState(industry);
  const [copyFeedback, setCopyFeedback] = useState("");
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const generatePlaceholders = React.useCallback(async () => {
    if (!contextInput.trim()) {
      setError("Please provide a context for placeholder generation");
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const placeholdersResult = await AIService.getSmartPlaceholders(
        contextInput,
        industryInput
      );
      setResult(placeholdersResult);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate placeholders"
      );
    } finally {
      setIsGenerating(false);
    }
  }, [contextInput, industryInput]);

  useEffect(() => {
    if (autoGenerate && contextInput.trim()) {
      generatePlaceholders();
    }
  }, [autoGenerate, contextInput, generatePlaceholders]);

  const handleCopyPlaceholder = async (placeholder: AIPlaceholder) => {
    try {
      await navigator.clipboard.writeText(`{{${placeholder.name}}}`);
      setCopyFeedback(`Copied: {{${placeholder.name}}}`);
      setSnackbarOpen(true);
    } catch {
      setCopyFeedback("Failed to copy to clipboard");
      setSnackbarOpen(true);
    }
  };

  const handlePlaceholderClick = (placeholder: AIPlaceholder) => {
    if (onPlaceholderSelect) {
      onPlaceholderSelect(placeholder);
    } else {
      handleCopyPlaceholder(placeholder);
    }
  };

  const renderPlaceholderGroup = (
    title: string,
    placeholders: AIPlaceholder[],
    color: string
  ) => (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            {title}
          </Typography>
          <Chip
            label={placeholders.length}
            size="small"
            sx={{ backgroundColor: color, color: "white", minWidth: 32 }}
          />
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          {placeholders.map((placeholder, index) => (
            <Grid item xs={12} sm={6} key={index}>
              <Card
                variant="outlined"
                sx={{
                  cursor: "pointer",
                  "&:hover": {
                    backgroundColor: "action.hover",
                    borderColor: "primary.main",
                  },
                  transition: "all 0.2s ease-in-out",
                }}
                onClick={() => handlePlaceholderClick(placeholder)}
              >
                <CardContent sx={{ p: 2 }}>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      mb: 1,
                    }}
                  >
                    <Typography
                      variant="subtitle2"
                      fontWeight="bold"
                      color="primary"
                      sx={{ fontFamily: "monospace" }}
                    >
                      {`{{${placeholder.name}}}`}
                    </Typography>
                    <Box sx={{ display: "flex", gap: 0.5 }}>
                      {placeholder.required && (
                        <Chip label="Required" color="error" size="small" />
                      )}
                      {placeholder.dynamic && (
                        <Chip label="Dynamic" color="info" size="small" />
                      )}
                      <IconButton
                        size="small"
                        onClick={(e: any) => {
                          e.stopPropagation();
                          handleCopyPlaceholder(placeholder);
                        }}
                      >
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>

                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mb: 1 }}
                  >
                    {placeholder.description}
                  </Typography>

                  {placeholder.example && (
                    <Box
                      sx={{
                        mt: 1,
                        p: 1,
                        backgroundColor: "grey.100",
                        borderRadius: 1,
                      }}
                    >
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ fontStyle: "italic" }}
                      >
                        Example: {placeholder.example}
                      </Typography>
                    </Box>
                  )}

                  {placeholder.format && (
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="primary">
                        Format: {placeholder.format}
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </AccordionDetails>
    </Accordion>
  );

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
          <SmartIcon color="primary" sx={{ fontSize: 32 }} />
          <Typography variant="h4" component="h2" fontWeight="bold">
            AI Smart Placeholders
          </Typography>
        </Box>
      </Box>

      {/* Input Controls */}
      <Card elevation={1} sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Context"
                placeholder="e.g., financial report, marketing dashboard"
                value={contextInput}
                onChange={(e: any) => setContextInput(e.target.value)}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Industry"
                placeholder="e.g., healthcare, finance, retail"
                value={industryInput}
                onChange={(e: any) => setIndustryInput(e.target.value)}
                variant="outlined"
                size="small"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Button
                fullWidth
                variant="contained"
                onClick={generatePlaceholders}
                disabled={isGenerating || !contextInput.trim()}
                startIcon={
                  isGenerating ? (
                    <CircularProgress size={20} color="inherit" />
                  ) : (
                    <BrainIcon />
                  )
                }
              >
                {isGenerating ? "Generating..." : "Generate"}
              </Button>
            </Grid>
            <Grid item xs={12} md={2}>
              <Tooltip title="Placeholders are dynamic variables you can use in templates. Click on any placeholder to copy it.">
                <IconButton color="info">
                  <InfoIcon />
                </IconButton>
              </Tooltip>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

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
          <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
            <Chip
              label={result.ai_powered ? "AI-Powered" : "Rule-Based"}
              color={result.ai_powered ? "primary" : "secondary"}
              size="small"
            />
            <Chip label="GENERATED" variant="outlined" size="small" />
          </Box>
          {result.fallback_reason && (
            <Alert severity="info" sx={{ mt: 2 }}>
              {result.fallback_reason}
            </Alert>
          )}
        </Box>
      )}

      {/* Placeholders Content */}
      {result?.placeholders && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Available Placeholders (
            {result.placeholders.basic_placeholders.length +
              result.placeholders.financial_metrics.length +
              result.placeholders.operational_details.length +
              result.placeholders.analytical_insights.length +
              result.placeholders.industry_specific.length +
              result.placeholders.compliance_regulatory.length}{" "}
            total)
          </Typography>

          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {/* Basic Placeholders */}
            {result.placeholders.basic_placeholders.length > 0 &&
              renderPlaceholderGroup(
                "Basic Placeholders",
                result.placeholders.basic_placeholders,
                "#2196F3"
              )}

            {/* Financial Metrics */}
            {result.placeholders.financial_metrics.length > 0 &&
              renderPlaceholderGroup(
                "Financial Metrics",
                result.placeholders.financial_metrics,
                "#4CAF50"
              )}

            {/* Operational Details */}
            {result.placeholders.operational_details.length > 0 &&
              renderPlaceholderGroup(
                "Operational Details",
                result.placeholders.operational_details,
                "#FF9800"
              )}

            {/* Industry Specific */}
            {result.placeholders.industry_specific.length > 0 &&
              renderPlaceholderGroup(
                "Industry Specific",
                result.placeholders.industry_specific,
                "#9C27B0"
              )}

            {/* Compliance & Regulatory */}
            {result.placeholders.compliance_regulatory.length > 0 &&
              renderPlaceholderGroup(
                "Compliance & Regulatory",
                result.placeholders.compliance_regulatory,
                "#795548"
              )}
          </Box>
        </Box>
      )}

      {/* Loading State */}
      {isGenerating && (
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
                  Generating Smart Placeholders
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  AI is creating contextual placeholders for your use case...
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* No Context State */}
      {!contextInput.trim() && !isGenerating && !result && (
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
              <SmartIcon sx={{ fontSize: 64, color: "text.disabled" }} />
              <Box>
                <Typography variant="h6" fontWeight="bold" color="text.primary">
                  Provide Context
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Enter a context above to generate smart placeholders
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* No Placeholders State */}
      {!isGenerating && !result && contextInput.trim() && (
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
              <SmartIcon sx={{ fontSize: 64, color: "text.disabled" }} />
              <Box>
                <Typography variant="h6" fontWeight="bold" color="text.primary">
                  No Placeholders Yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Click "Generate" to get AI-powered placeholder suggestions
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Copy Feedback Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        message={copyFeedback}
      />
    </Box>
  );
};

export default AISmartPlaceholders;
