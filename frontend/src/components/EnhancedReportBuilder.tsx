import React, { useState, useCallback, useEffect } from "react";
import {
  Box,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  Chip,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fade,
} from "@mui/material";
import {
  CloudUpload,
  Analytics,
  Download,
  AutoAwesome,
  Refresh,
  Preview,
  GetApp,
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import { useDropzone } from "react-dropzone";
import { enhancedReportService } from "../services/enhancedReportService";

// Styled components
const UploadBox = styled(Box)<{ isDragActive: boolean }>(
  ({ theme, isDragActive }) => ({
    border: `2px dashed ${
      isDragActive ? theme.palette.primary.main : theme.palette.grey[400]
    }`,
    borderRadius: theme.spacing(2),
    padding: theme.spacing(6),
    textAlign: "center",
    cursor: "pointer",
    transition: "all 0.3s ease",
    backgroundColor: isDragActive
      ? theme.palette.primary.light + "20"
      : theme.palette.grey[50],
    "&:hover": {
      borderColor: theme.palette.primary.main,
      backgroundColor: theme.palette.primary.light + "10",
    },
  })
);

const PreviewContainer = styled(Box)(({ theme }) => ({
  border: `1px solid ${theme.palette.grey[300]}`,
  borderRadius: theme.spacing(1),
  height: "600px",
  overflow: "auto",
  backgroundColor: "#fff",
  position: "relative",
}));

const ContentVariationCard = styled(Card)<{ isSelected: boolean }>(
  ({ theme, isSelected }) => ({
    cursor: "pointer",
    transition: "all 0.3s ease",
    border: isSelected
      ? `2px solid ${theme.palette.primary.main}`
      : `1px solid ${theme.palette.grey[300]}`,
    transform: isSelected ? "scale(1.02)" : "scale(1)",
    "&:hover": {
      transform: "scale(1.02)",
      boxShadow: theme.shadows[4],
    },
  })
);

const TemplateCard = styled(Card)<{ isSelected: boolean }>(
  ({ theme, isSelected }) => ({
    cursor: "pointer",
    transition: "all 0.3s ease",
    border: isSelected
      ? `2px solid ${theme.palette.primary.main}`
      : `1px solid ${theme.palette.grey[300]}`,
    "&:hover": {
      boxShadow: theme.shadows[4],
    },
  })
);

// Types
interface ExcelData {
  success: boolean;
  primary_sheet: {
    headers: string[];
    sample_data: Array<Record<string, unknown>>;
    total_rows: number;
    total_cols: number;
    statistics: Record<string, unknown>;
    field_categories: Record<string, string>;
  };
  sheets: Record<string, unknown>;
}

interface ContentVariation {
  style: string;
  title: string;
  content: string;
  tone: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  style: string;
  color_scheme: string[];
}

const steps = [
  "Upload Data",
  "Choose Template",
  "Customize Content",
  "Preview & Export",
];

const EnhancedReportBuilder: React.FC = () => {
  // State management
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [excelData, setExcelData] = useState<ExcelData | null>(null);
  const [selectedTemplate, setSelectedTemplate] =
    useState<string>("professional");
  const [contentVariations, setContentVariations] = useState<
    ContentVariation[]
  >([]);
  const [selectedContent, setSelectedContent] =
    useState<ContentVariation | null>(null);
  const [previewHtml, setPreviewHtml] = useState<string>("");
  const [templates, setTemplates] = useState<Template[]>([]);

  // UI states
  const [previewTab, setPreviewTab] = useState(0);
  const [exportDialog, setExportDialog] = useState(false);

  // File upload handler
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setUploadedFile(file);
    setLoading(true);
    setError(null);

    try {
      const result = await enhancedReportService.uploadExcelFile(file);

      if (result.success && result.data) {
        // Transform the service response to match our component's ExcelData interface
        const transformedData: ExcelData = {
          success: true,
          primary_sheet: {
            headers: result.data.primary_sheet.headers,
            sample_data: result.data.primary_sheet.sample_data.map((row) =>
              Object.fromEntries(
                Object.entries(row).map(([k, v]) => [k, v as unknown])
              )
            ),
            total_rows: result.data.primary_sheet.clean_rows,
            total_cols: result.data.primary_sheet.total_cols,
            statistics: result.data.primary_sheet.statistics,
            field_categories: result.data.primary_sheet.field_categories,
          },
          sheets: { filename: result.data.filename },
        };
        setExcelData(transformedData);
        setActiveStep(1); // Move to template selection
      } else {
        setError(result.error || "Failed to upload file");
      }
    } catch (err: unknown) {
      console.error("Upload error:", err);
      setError("Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [
        ".xlsx",
      ],
      "application/vnd.ms-excel": [".xls"],
      "text/csv": [".csv"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  // Load templates
  useEffect(() => {
    const loadTemplates = async () => {
      try {
        const response = await fetch("/api/enhanced-report/templates", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });
        const result = await response.json();
        if (result.success) {
          setTemplates(result.templates);
        }
      } catch (err: unknown) {
        console.error("Failed to load templates:", err);
      }
    };

    loadTemplates();
  }, []);

  // Generate content variations
  const generateContentVariations = async () => {
    if (!excelData) return;

    setLoading(true);
    try {
      const result = await enhancedReportService.generateContentVariations({
        excel_data: excelData,
        section_type: "executive_summary",
      });

      if (result.success && result.content_variations) {
        setContentVariations(result.content_variations.variations || []);
        if (result.content_variations.variations?.length > 0) {
          setSelectedContent(result.content_variations.variations[0]);
        }
        setActiveStep(2); // Move to content customization
      } else {
        setError(result.error || "Failed to generate content variations");
      }
    } catch (err: unknown) {
      console.error("Content generation error:", err);
      setError("Content generation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Generate live preview
  const generatePreview = async () => {
    if (!excelData || !selectedContent) return;

    setLoading(true);
    try {
      const result = await enhancedReportService.generateLivePreview({
        excel_data: excelData,
        template_type: selectedTemplate,
        selected_content: selectedContent,
      });

      if (result.success && result.preview_html) {
        setPreviewHtml(result.preview_html);
        setActiveStep(3); // Move to preview & export
      } else {
        setError(result.error || "Failed to generate preview");
      }
    } catch (err: unknown) {
      console.error("Preview generation error:", err);
      setError("Preview generation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Export report
  const exportReport = async (format: string) => {
    if (!excelData || !selectedContent) return;

    setLoading(true);
    try {
      const result = await enhancedReportService.exportReport({
        excel_data: excelData,
        selected_content: selectedContent,
        format: format,
        template_type: selectedTemplate,
      });

      if (result.success) {
        // Handle download
        if (result.download_url) {
          window.open(result.download_url, "_blank");
        }
        setExportDialog(false);
      } else {
        setError(result.error || "Export failed");
      }
    } catch (err: unknown) {
      console.error("Export error:", err);
      setError("Export failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Render step content
  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="h5" gutterBottom align="center">
              Upload Your Excel Data
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              align="center"
              sx={{ mb: 4 }}
            >
              Drag and drop your Excel file or click to browse. Supported
              formats: .xlsx, .xls, .csv
            </Typography>

            <UploadBox {...getRootProps()} isDragActive={isDragActive}>
              <input {...getInputProps()} />
              <CloudUpload
                sx={{ fontSize: 48, color: "primary.main", mb: 2 }}
              />
              {isDragActive ? (
                <Typography variant="h6">Drop the file here...</Typography>
              ) : (
                <>
                  <Typography variant="h6" gutterBottom>
                    Drag & drop your Excel file here
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    or click to select file
                  </Typography>
                </>
              )}
              {uploadedFile && (
                <Chip
                  label={uploadedFile.name}
                  color="primary"
                  sx={{ mt: 2 }}
                  onDelete={() => setUploadedFile(null)}
                />
              )}
            </UploadBox>

            {excelData && (
              <Alert severity="success" sx={{ mt: 2 }}>
                File uploaded successfully! Found{" "}
                {excelData.primary_sheet.total_rows} rows and{" "}
                {excelData.primary_sheet.total_cols} columns.
              </Alert>
            )}
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="h5" gutterBottom align="center">
              Choose Report Template
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              align="center"
              sx={{ mb: 4 }}
            >
              Select a template that best fits your report style and audience
            </Typography>

            <Grid container spacing={3}>
              {templates.map((template) => (
                <Grid item xs={12} md={6} key={template.id}>
                  <TemplateCard
                    isSelected={selectedTemplate === template.id}
                    onClick={() => setSelectedTemplate(template.id)}
                  >
                    <CardContent>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 2 }}
                      >
                        <Analytics sx={{ mr: 1, color: "primary.main" }} />
                        <Typography variant="h6">{template.name}</Typography>
                      </Box>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mb: 2 }}
                      >
                        {template.description}
                      </Typography>
                      <Box sx={{ display: "flex", gap: 1 }}>
                        {template.color_scheme
                          .slice(0, 4)
                          .map((color, index) => (
                            <Box
                              key={index}
                              sx={{
                                width: 20,
                                height: 20,
                                backgroundColor: color,
                                borderRadius: "50%",
                                border: "1px solid #ccc",
                              }}
                            />
                          ))}
                      </Box>
                    </CardContent>
                  </TemplateCard>
                </Grid>
              ))}
            </Grid>

            <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
              <Button
                variant="contained"
                size="large"
                onClick={generateContentVariations}
                startIcon={<AutoAwesome />}
                disabled={loading}
              >
                Generate AI Content
              </Button>
            </Box>
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h5" gutterBottom align="center">
              Customize Content with AI
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              align="center"
              sx={{ mb: 4 }}
            >
              Choose from AI-generated content variations or create your own
            </Typography>

            <Grid container spacing={3}>
              {contentVariations.map((variation, index) => (
                <Grid item xs={12} md={6} key={index}>
                  <ContentVariationCard
                    isSelected={selectedContent?.style === variation.style}
                    onClick={() => setSelectedContent(variation)}
                  >
                    <CardContent>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 2 }}
                      >
                        <AutoAwesome sx={{ mr: 1, color: "primary.main" }} />
                        <Typography variant="h6">{variation.title}</Typography>
                        <Chip
                          label={variation.style}
                          size="small"
                          sx={{ ml: "auto" }}
                          color={
                            variation.style === "professional"
                              ? "primary"
                              : "default"
                          }
                        />
                      </Box>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {variation.content}
                      </Typography>
                      <Chip
                        label={variation.tone}
                        size="small"
                        variant="outlined"
                      />
                    </CardContent>
                  </ContentVariationCard>
                </Grid>
              ))}
            </Grid>

            <Box
              sx={{ display: "flex", justifyContent: "center", gap: 2, mt: 4 }}
            >
              <Button
                variant="outlined"
                onClick={() => generateContentVariations()}
                startIcon={<Refresh />}
                disabled={loading}
              >
                Regenerate Content
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={generatePreview}
                startIcon={<Preview />}
                disabled={loading || !selectedContent}
              >
                Generate Preview
              </Button>
            </Box>
          </Box>
        );

      case 3:
        return (
          <Box>
            <Typography variant="h5" gutterBottom align="center">
              Preview & Export
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              align="center"
              sx={{ mb: 4 }}
            >
              Review your report and export in your preferred format
            </Typography>

            <Box sx={{ mb: 3 }}>
              <Tabs
                value={previewTab}
                onChange={(_, newValue) => setPreviewTab(newValue)}
              >
                <Tab label="Live Preview" />
                <Tab label="Data Summary" />
              </Tabs>
            </Box>

            {previewTab === 0 && (
              <PreviewContainer>
                {previewHtml ? (
                  <Box
                    component="iframe"
                    srcDoc={previewHtml}
                    sx={{
                      width: "100%",
                      height: "100%",
                      border: "none",
                    }}
                  />
                ) : (
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      height: "100%",
                    }}
                  >
                    <Typography color="text.secondary">
                      Click "Generate Preview" to see your report
                    </Typography>
                  </Box>
                )}
              </PreviewContainer>
            )}

            {previewTab === 1 && excelData && (
              <Box sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Data Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: "center" }}>
                      <Typography variant="h4" color="primary">
                        {excelData.primary_sheet.total_rows}
                      </Typography>
                      <Typography variant="body2">Total Records</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: "center" }}>
                      <Typography variant="h4" color="primary">
                        {excelData.primary_sheet.total_cols}
                      </Typography>
                      <Typography variant="body2">Data Fields</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: "center" }}>
                      <Typography variant="h4" color="primary">
                        {Object.keys(excelData.sheets).length}
                      </Typography>
                      <Typography variant="body2">Sheets</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6} md={3}>
                    <Paper sx={{ p: 2, textAlign: "center" }}>
                      <Typography variant="h4" color="primary">
                        {selectedTemplate}
                      </Typography>
                      <Typography variant="body2">Template</Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            )}

            <Box
              sx={{ display: "flex", justifyContent: "center", gap: 2, mt: 4 }}
            >
              <Button
                variant="outlined"
                onClick={generatePreview}
                startIcon={<Refresh />}
                disabled={loading}
              >
                Refresh Preview
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={() => setExportDialog(true)}
                startIcon={<Download />}
                disabled={loading || !previewHtml}
              >
                Export Report
              </Button>
            </Box>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: "auto", p: 3 }}>
      {/* Header */}
      <Paper
        sx={{
          p: 3,
          mb: 3,
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          color: "white",
        }}
      >
        <Typography variant="h4" align="center" gutterBottom>
          🤖 AI-Powered Report Builder
        </Typography>
        <Typography variant="subtitle1" align="center">
          Upload Excel → Choose Style → AI Content → Live Preview → Export
        </Typography>
      </Paper>

      {/* Stepper */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper activeStep={activeStep} alternativeLabel>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Progress bar */}
      {loading && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress />
        </Box>
      )}

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Main content */}
      <Paper sx={{ p: 4, minHeight: 600 }}>
        <Fade in={true} key={activeStep}>
          <Box>{renderStepContent()}</Box>
        </Fade>
      </Paper>

      {/* Navigation */}
      <Box sx={{ display: "flex", justifyContent: "space-between", mt: 3 }}>
        <Button
          disabled={activeStep === 0}
          onClick={() => setActiveStep(activeStep - 1)}
        >
          Back
        </Button>

        <Button
          variant="contained"
          disabled={
            (activeStep === 0 && !excelData) ||
            (activeStep === 1 && !selectedTemplate) ||
            (activeStep === 2 && !selectedContent) ||
            activeStep === 3
          }
          onClick={() => {
            if (activeStep === 0 && excelData) setActiveStep(1);
            else if (activeStep === 1) generateContentVariations();
            else if (activeStep === 2) generatePreview();
          }}
        >
          {activeStep === 3 ? "Completed" : "Next"}
        </Button>
      </Box>

      {/* Export Dialog */}
      <Dialog open={exportDialog} onClose={() => setExportDialog(false)}>
        <DialogTitle>Export Report</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>Choose your export format:</Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => exportReport("html")}
                startIcon={<GetApp />}
              >
                HTML
              </Button>
            </Grid>
            <Grid item xs={6}>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => exportReport("pdf")}
                startIcon={<GetApp />}
                disabled
              >
                PDF (Coming Soon)
              </Button>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EnhancedReportBuilder;
