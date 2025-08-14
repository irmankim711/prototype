import React, { useState, useCallback, useEffect } from "react";
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Button,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  LinearProgress,
} from "@mui/material";
import {
  CloudUpload,
  Preview,
  Download,
  Refresh,
  Settings,
  AutoAwesome,
  TableChart,
  Assessment,
  Close,
  CheckCircle,
  Info,
} from "@mui/icons-material";
import { useDropzone } from "react-dropzone";
import { enhancedReportService } from "../../services/enhancedReportService";
import "./EnhancedReportBuilder.css";

interface ExcelData {
  success: boolean;
  data?: {
    primary_sheet: {
      headers: string[];
      sample_data: Record<string, string | number | null>[];
      clean_rows: number;
      total_cols: number;
      statistics: Record<string, unknown>;
      field_categories: Record<string, string>;
      quality_assessment: {
        completeness: {
          completeness_percentage: number;
        };
        uniqueness: {
          duplicate_rows: number;
        };
      };
    };
    filename: string;
  };
  ai_insights?: Record<string, unknown>;
  error?: string;
}

interface ContentVariation {
  style: string;
  title: string;
  content: string;
  tone: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function EnhancedReportBuilder() {
  // Core state
  const [currentStep, setCurrentStep] = useState(0);
  const [excelData, setExcelData] = useState<ExcelData | null>(null);
  const [contentVariations, setContentVariations] = useState<
    ContentVariation[]
  >([]);
  const [selectedContent, setSelectedContent] =
    useState<ContentVariation | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState("professional");
  const [previewHtml, setPreviewHtml] = useState("");

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [previewDialog, setPreviewDialog] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);

  // Available templates
  const templates = [
    {
      id: "professional",
      name: "Professional Report",
      description: "Clean, formal business report",
      color: "#2E86AB",
    },
    {
      id: "training",
      name: "Training Analysis",
      description: "Education and training focused",
      color: "#27AE60",
    },
    {
      id: "analytics",
      name: "Data Analytics",
      description: "Technical analysis with charts",
      color: "#8E44AD",
    },
    {
      id: "executive",
      name: "Executive Summary",
      description: "High-level executive overview",
      color: "#34495E",
    },
  ];

  // File upload handler
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setLoading(true);
    setError(null);
    setUploadProgress(0);

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const result = await enhancedReportService.uploadExcelFile(file);

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (result.success) {
        setExcelData(result);
        setSuccess(`Successfully analyzed ${file.name}!`);
        setCurrentStep(1);

        // Auto-generate content variations
        await generateContentVariations(result);
      } else {
        setError(result.error || "Failed to upload file");
      }
    } catch (err) {
      setError("Upload failed. Please try again.");
      console.error("Upload error:", err);
    } finally {
      setLoading(false);
      setTimeout(() => setUploadProgress(0), 2000);
    }
  }, []);

  // Generate AI content variations
  const generateContentVariations = async (data: ExcelData) => {
    if (!data.success || !data.data) return;

    try {
      const variations = await enhancedReportService.generateContentVariations({
        excel_data: data.data,
        section_type: "executive_summary",
      });

      if (variations.success && variations.content_variations?.variations) {
        setContentVariations(variations.content_variations.variations);
        setSelectedContent(variations.content_variations.variations[0]);
      }
    } catch (err) {
      console.error("Failed to generate content variations:", err);
    }
  };

  // Generate live preview
  const generatePreview = useCallback(async () => {
    if (!excelData?.data) return;

    setPreviewLoading(true);
    try {
      const preview = await enhancedReportService.generateLivePreview({
        excel_data: excelData.data,
        template_type: selectedTemplate,
        selected_content: selectedContent,
      });

      if (preview.success) {
        setPreviewHtml(preview.preview_html);
        setCurrentStep(2);
      } else {
        setError(preview.error || "Failed to generate preview");
      }
    } catch (err) {
      setError("Preview generation failed");
      console.error("Preview error:", err);
    } finally {
      setPreviewLoading(false);
    }
  }, [excelData?.data, selectedTemplate, selectedContent]);

  // Export report
  const exportReport = async (format: string = "html") => {
    if (!excelData?.data) return;

    setLoading(true);
    try {
      const result = await enhancedReportService.exportReport({
        excel_data: excelData.data,
        selected_content: selectedContent,
        format: format,
        template_type: selectedTemplate,
      });

      if (result.success) {
        setSuccess(`Report exported successfully as ${format.toUpperCase()}!`);
        if (result.download_url) {
          window.open(result.download_url, "_blank");
        }
      } else {
        setError(result.error || "Export failed");
      }
    } catch (err) {
      setError("Export failed");
      console.error("Export error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Dropzone configuration
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
      "application/vnd.ms-excel": [".xls"],
      "text/csv": [".csv"],
    },
    multiple: false,
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  // Auto-generate preview when template or content changes
  useEffect(() => {
    if (excelData?.data && selectedContent && currentStep >= 1) {
      generatePreview();
    }
  }, [
    selectedTemplate,
    selectedContent,
    currentStep,
    excelData?.data,
    generatePreview,
  ]);

  // Clear notifications
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 8000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: "center" }}>
        <Typography
          variant="h3"
          component="h1"
          sx={{ mb: 2, fontWeight: 700, color: "#1976d2" }}
        >
          🤖 AI-Powered Report Builder
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Upload Excel → Choose AI Content → Live Preview → Export
        </Typography>

        {/* Progress Steps */}
        <Box sx={{ display: "flex", justifyContent: "center", gap: 2, mb: 3 }}>
          {["Upload Data", "Customize Content", "Preview & Export"].map(
            (step, index) => (
              <Chip
                key={step}
                label={step}
                color={currentStep >= index ? "primary" : "default"}
                variant={currentStep === index ? "filled" : "outlined"}
                icon={currentStep > index ? <CheckCircle /> : undefined}
              />
            )
          )}
        </Box>
      </Box>

      {/* Notifications */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert
          severity="success"
          sx={{ mb: 3 }}
          onClose={() => setSuccess(null)}
        >
          {success}
        </Alert>
      )}

      {/* Upload Progress */}
      {uploadProgress > 0 && uploadProgress < 100 && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            Analyzing file... {uploadProgress}%
          </Typography>
        </Box>
      )}

      <Grid container spacing={4}>
        {/* Left Panel - Controls */}
        <Grid item xs={12} md={4}>
          <Box sx={{ position: "sticky", top: 20 }}>
            {/* Step 1: File Upload */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography
                  variant="h6"
                  sx={{ mb: 2, display: "flex", alignItems: "center", gap: 1 }}
                >
                  <CloudUpload color="primary" />
                  Step 1: Upload Excel File
                </Typography>

                <Paper
                  {...getRootProps()}
                  sx={{
                    p: 3,
                    border: "2px dashed",
                    borderColor: isDragActive ? "primary.main" : "grey.300",
                    backgroundColor: isDragActive
                      ? "action.hover"
                      : "background.paper",
                    cursor: "pointer",
                    textAlign: "center",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: "primary.main",
                      backgroundColor: "action.hover",
                    },
                  }}
                >
                  <input {...getInputProps()} />
                  <CloudUpload
                    sx={{ fontSize: 48, color: "primary.main", mb: 2 }}
                  />
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {isDragActive ? "Drop file here" : "Drag & drop Excel file"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    or click to browse (.xlsx, .xls, .csv)
                  </Typography>
                </Paper>

                {excelData?.data && (
                  <Box sx={{ mt: 2 }}>
                    <Alert severity="success" sx={{ mb: 2 }}>
                      <Typography variant="subtitle2">
                        File analyzed successfully!
                      </Typography>
                    </Alert>
                    <Grid container spacing={1}>
                      <Grid item xs={6}>
                        <Chip
                          label={`${excelData.data.primary_sheet.clean_rows} rows`}
                          size="small"
                          color="primary"
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <Chip
                          label={`${excelData.data.primary_sheet.total_cols} columns`}
                          size="small"
                          color="secondary"
                        />
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Step 2: Template Selection */}
            {excelData?.data && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography
                    variant="h6"
                    sx={{
                      mb: 2,
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                    }}
                  >
                    <Settings color="primary" />
                    Step 2: Choose Template
                  </Typography>

                  <Grid container spacing={1}>
                    {templates.map((template) => (
                      <Grid item xs={12} key={template.id}>
                        <Paper
                          onClick={() => setSelectedTemplate(template.id)}
                          sx={{
                            p: 2,
                            cursor: "pointer",
                            border: "2px solid",
                            borderColor:
                              selectedTemplate === template.id
                                ? template.color
                                : "transparent",
                            backgroundColor:
                              selectedTemplate === template.id
                                ? `${template.color}10`
                                : "background.paper",
                            transition: "all 0.3s ease",
                            "&:hover": {
                              borderColor: template.color,
                              backgroundColor: `${template.color}05`,
                            },
                          }}
                        >
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            <Box
                              sx={{
                                width: 16,
                                height: 16,
                                borderRadius: "50%",
                                backgroundColor: template.color,
                              }}
                            />
                            <Box sx={{ flex: 1 }}>
                              <Typography
                                variant="subtitle2"
                                sx={{ fontWeight: 600 }}
                              >
                                {template.name}
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                              >
                                {template.description}
                              </Typography>
                            </Box>
                            {selectedTemplate === template.id && (
                              <CheckCircle sx={{ color: template.color }} />
                            )}
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            )}

            {/* Step 3: AI Content Variations */}
            {contentVariations.length > 0 && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography
                    variant="h6"
                    sx={{
                      mb: 2,
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                    }}
                  >
                    <AutoAwesome color="primary" />
                    Step 3: AI Content Style
                  </Typography>

                  <Box sx={{ maxHeight: 300, overflowY: "auto" }}>
                    {contentVariations.map((variation, index) => (
                      <Paper
                        key={index}
                        onClick={() => setSelectedContent(variation)}
                        sx={{
                          p: 2,
                          mb: 1,
                          cursor: "pointer",
                          border: "1px solid",
                          borderColor:
                            selectedContent?.style === variation.style
                              ? "primary.main"
                              : "grey.300",
                          backgroundColor:
                            selectedContent?.style === variation.style
                              ? "primary.50"
                              : "background.paper",
                          transition: "all 0.3s ease",
                        }}
                      >
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
                            sx={{
                              fontWeight: 600,
                              textTransform: "capitalize",
                            }}
                          >
                            {variation.style}
                          </Typography>
                          <Chip label={variation.tone} size="small" />
                        </Box>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                            overflow: "hidden",
                          }}
                        >
                          {variation.content}
                        </Typography>
                      </Paper>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            )}

            {/* Export Actions */}
            {previewHtml && (
              <Card>
                <CardContent>
                  <Typography
                    variant="h6"
                    sx={{
                      mb: 2,
                      display: "flex",
                      alignItems: "center",
                      gap: 1,
                    }}
                  >
                    <Download color="primary" />
                    Export Report
                  </Typography>

                  <Grid container spacing={1}>
                    <Grid item xs={12}>
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<Download />}
                        onClick={() => exportReport("html")}
                        disabled={loading}
                        sx={{ mb: 1 }}
                      >
                        Export as HTML
                      </Button>
                    </Grid>
                    <Grid item xs={6}>
                      <Button
                        fullWidth
                        variant="outlined"
                        size="small"
                        onClick={() => exportReport("pdf")}
                        disabled={loading}
                      >
                        PDF
                      </Button>
                    </Grid>
                    <Grid item xs={6}>
                      <Button
                        fullWidth
                        variant="outlined"
                        size="small"
                        onClick={() => exportReport("word")}
                        disabled={loading}
                      >
                        Word
                      </Button>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}
          </Box>
        </Grid>

        {/* Right Panel - Preview */}
        <Grid item xs={12} md={8}>
          <Card sx={{ minHeight: 600 }}>
            <CardContent sx={{ p: 0 }}>
              {/* Preview Header */}
              <Box
                sx={{
                  p: 3,
                  borderBottom: "1px solid",
                  borderColor: "divider",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Typography
                  variant="h6"
                  sx={{ display: "flex", alignItems: "center", gap: 1 }}
                >
                  <Preview color="primary" />
                  Live Preview
                  {previewLoading && <CircularProgress size={20} />}
                </Typography>

                <Box sx={{ display: "flex", gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Refresh />}
                    onClick={generatePreview}
                    disabled={!excelData?.data || previewLoading}
                  >
                    Refresh
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Preview />}
                    onClick={() => setPreviewDialog(true)}
                    disabled={!previewHtml}
                  >
                    Full Screen
                  </Button>
                </Box>
              </Box>

              {/* Preview Content */}
              <Box sx={{ p: 3 }}>
                {!excelData?.data ? (
                  <Box sx={{ textAlign: "center", py: 8 }}>
                    <TableChart
                      sx={{ fontSize: 80, color: "grey.300", mb: 2 }}
                    />
                    <Typography variant="h6" color="text.secondary">
                      Upload an Excel file to see live preview
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Your report will appear here in real-time as you make
                      changes
                    </Typography>
                  </Box>
                ) : previewLoading ? (
                  <Box sx={{ textAlign: "center", py: 8 }}>
                    <CircularProgress size={60} sx={{ mb: 2 }} />
                    <Typography variant="h6" color="text.secondary">
                      Generating AI-powered preview...
                    </Typography>
                  </Box>
                ) : previewHtml ? (
                  <Box
                    sx={{
                      border: "1px solid",
                      borderColor: "grey.300",
                      borderRadius: 1,
                      minHeight: 400,
                      overflow: "hidden",
                    }}
                  >
                    <iframe
                      srcDoc={previewHtml}
                      className="report-preview-iframe"
                      title="Report Preview"
                    />
                  </Box>
                ) : (
                  <Box sx={{ textAlign: "center", py: 8 }}>
                    <Assessment
                      sx={{ fontSize: 80, color: "grey.300", mb: 2 }}
                    />
                    <Typography variant="h6" color="text.secondary">
                      Configure your report settings
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Choose a template and content style to generate preview
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>

          {/* Data Overview */}
          {excelData?.data && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Tabs
                  value={currentTab}
                  onChange={(_, newValue) => setCurrentTab(newValue)}
                >
                  <Tab label="Data Summary" />
                  <Tab label="Sample Data" />
                  <Tab label="AI Insights" />
                </Tabs>

                <TabPanel value={currentTab} index={0}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: "center" }}>
                        <Typography variant="h4" color="primary.main">
                          {excelData.data.primary_sheet.clean_rows.toLocaleString()}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Total Records
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: "center" }}>
                        <Typography variant="h4" color="secondary.main">
                          {excelData.data.primary_sheet.total_cols}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Data Fields
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: "center" }}>
                        <Typography variant="h4" color="success.main">
                          {excelData.data.primary_sheet.quality_assessment?.completeness?.completeness_percentage?.toFixed(
                            1
                          ) || 100}
                          %
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Data Quality
                        </Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Paper sx={{ p: 2, textAlign: "center" }}>
                        <Typography variant="h4" color="warning.main">
                          {excelData.data.primary_sheet.quality_assessment
                            ?.uniqueness?.duplicate_rows || 0}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Duplicates
                        </Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </TabPanel>

                <TabPanel value={currentTab} index={1}>
                  <Box sx={{ overflowX: "auto" }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          {excelData.data.primary_sheet.headers.map(
                            (header, index) => (
                              <th key={index}>{header}</th>
                            )
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {excelData.data.primary_sheet.sample_data
                          .slice(0, 5)
                          .map((row, index) => (
                            <tr key={index}>
                              {excelData.data!.primary_sheet.headers.map(
                                (header, cellIndex) => (
                                  <td key={cellIndex}>
                                    {row[header] !== null &&
                                    row[header] !== undefined
                                      ? String(row[header])
                                      : "-"}
                                  </td>
                                )
                              )}
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </Box>
                </TabPanel>

                <TabPanel value={currentTab} index={2}>
                  {excelData.ai_insights ? (
                    <Box>
                      <Typography variant="body1" sx={{ mb: 2 }}>
                        AI-generated insights from your data:
                      </Typography>
                      <Alert severity="info">
                        <Typography variant="body2">
                          {JSON.stringify(excelData.ai_insights, null, 2)}
                        </Typography>
                      </Alert>
                    </Box>
                  ) : (
                    <Box sx={{ textAlign: "center", py: 4 }}>
                      <Info sx={{ fontSize: 60, color: "grey.300", mb: 2 }} />
                      <Typography variant="body1" color="text.secondary">
                        AI insights will appear here when available
                      </Typography>
                    </Box>
                  )}
                </TabPanel>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Full Screen Preview Dialog */}
      <Dialog
        open={previewDialog}
        onClose={() => setPreviewDialog(false)}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: "90vh" },
        }}
      >
        <DialogTitle
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6">Full Report Preview</Typography>
          <IconButton onClick={() => setPreviewDialog(false)}>
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {previewHtml && (
            <iframe
              srcDoc={previewHtml}
              className="fullscreen-preview-iframe"
              title="Full Report Preview"
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialog(false)}>Close</Button>
          <Button variant="contained" onClick={() => exportReport("html")}>
            Export Report
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
