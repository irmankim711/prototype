import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  TextField,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
} from "@mui/material";
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Lightbulb as LightbulbIcon,
  AutoFixHigh as AutoFixHighIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Add as AddIcon,
} from "@mui/icons-material";
import { fetchTemplateContent, generateLivePreview } from "../../services/api";

interface TemplateEditorProps {
  templateName: string;
  data: Record<string, string>;
  onDataChange: (data: Record<string, string>) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export default function TemplateEditor({
  templateName,
  data,
  onDataChange,
  onGenerate,
  isGenerating,
}: TemplateEditorProps) {
  const [rightPanelTab, setRightPanelTab] = useState(0);
  const [templateContent, setTemplateContent] = useState<any>(null);
  const [livePreview, setLivePreview] = useState<string | null>(null);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [editedData, setEditedData] = useState<Record<string, string>>(data);
  const [isEditingPreview, setIsEditingPreview] = useState(false);
  const [editableContent, setEditableContent] = useState<string>("");
  const [selectedSuggestion, setSelectedSuggestion] = useState<number | null>(
    null
  );

  // Log props for debugging
  console.log("TemplateEditor props:", { templateName, data, isGenerating });
  console.log("Component state:", { editedData, livePreview, editableContent });

  const [aiSuggestions] = useState([
    {
      id: 1,
      title: "Executive Summary",
      description: "Add a comprehensive executive summary",
      suggestion: "Include key findings, recommendations, and project overview",
      type: "content",
      content:
        "Based on our comprehensive analysis, this report provides strategic insights and actionable recommendations for improving operational efficiency and stakeholder satisfaction.",
    },
    {
      id: 2,
      title: "Key Performance Indicators",
      description: "Insert relevant KPIs and metrics",
      suggestion: "Add measurable outcomes and performance data",
      type: "data",
      content:
        "Performance metrics show a 15% improvement in efficiency with 92% stakeholder satisfaction rate.",
    },
    {
      id: 3,
      title: "Risk Assessment",
      description: "Include risk analysis section",
      suggestion: "Identify potential risks and mitigation strategies",
      type: "analysis",
      content:
        "Risk factors have been identified and categorized as low to medium impact with appropriate mitigation measures in place.",
    },
    {
      id: 4,
      title: "Recommendations",
      description: "Provide actionable recommendations",
      suggestion: "List specific steps and next actions",
      type: "action",
      content:
        "We recommend implementing the proposed solutions in phases, starting with high-priority items in Q1 2025.",
    },
    {
      id: 5,
      title: "Financial Impact",
      description: "Add financial analysis and projections",
      suggestion: "Include cost-benefit analysis",
      type: "financial",
      content:
        "The proposed initiatives are projected to generate cost savings of $150,000 annually with an ROI of 240%.",
    },
  ]);

  // Load template content when component mounts
  useEffect(() => {
    const loadTemplateContent = async () => {
      if (!templateName) return;

      setIsLoadingContent(true);
      try {
        const content = await fetchTemplateContent(templateName);
        setTemplateContent(content);
      } catch (error) {
        console.error("Failed to load template content:", error);
      } finally {
        setIsLoadingContent(false);
      }
    };

    loadTemplateContent();
  }, [templateName]);

  // Sync data changes with parent
  useEffect(() => {
    onDataChange(editedData);
  }, [editedData, onDataChange]);

  // Auto-generate preview when data changes, if not in edit mode
  useEffect(() => {
    if (!editableContent && Object.keys(editedData).length > 0) {
      handleGeneratePreview();
    }
  }, [editedData, editableContent]);

  // Don't auto-initialize editable content - let user choose their mode

  const handleGeneratePreview = async () => {
    console.log("handleGeneratePreview called");
    console.log("templateName:", templateName);
    console.log("editedData:", editedData);
    console.log("editableContent:", editableContent);

    if (!templateName) {
      setPreviewError("No template selected");
      console.log("Error: No template selected");
      return;
    }

    // If we have editable content, use that for preview
    if (editableContent) {
      setLivePreview(null); // Clear iframe preview when using editable content
      console.log("Using editable content, clearing iframe preview");
      return;
    }

    // Otherwise generate preview from field data
    if (Object.keys(editedData).length === 0) {
      setPreviewError("No data available for preview");
      console.log("Error: No data available for preview");
      return;
    }

    setIsGeneratingPreview(true);
    setPreviewError(null);
    console.log("Starting preview generation...");

    try {
      const result = await generateLivePreview(templateName, editedData);
      console.log("Preview result:", result);
      // Handle both string and object responses from the API
      const previewUrl = typeof result === "string" ? result : result.preview;

      // Ensure PDF data URL is properly formatted
      const formattedPreviewUrl = previewUrl.startsWith("data:")
        ? previewUrl
        : `data:application/pdf;base64,${previewUrl}`;

      console.log(
        "Setting livePreview with URL length:",
        formattedPreviewUrl.length
      );
      setLivePreview(formattedPreviewUrl);
      setEditableContent(""); // Clear editable content when showing iframe preview
    } catch (error: unknown) {
      console.error("Preview generation error:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Failed to generate preview";
      setPreviewError(errorMessage);
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  // Handle data field changes
  const handleDataChange = (key: string, value: string) => {
    const newData = { ...editedData, [key]: value };
    setEditedData(newData);
    onDataChange(newData);
  };

  // Download original template
  const handleDownloadTemplate = () => {
    const link = document.createElement("a");
    link.href = `/mvp/templates/${templateName}/download`;
    link.download = templateName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle suggestion selection
  const handleSuggestionSelect = (suggestion: (typeof aiSuggestions)[0]) => {
    setSelectedSuggestion(suggestion.id);
    setEditableContent(suggestion.content);
  };

  // Handle adding suggestion to preview
  const handleAddToPreview = (content: string) => {
    setEditableContent((prev) => prev + "\n\n" + content);
  };

  if (isLoadingContent) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography
          variant="h5"
          component="h2"
          sx={{ fontWeight: 600, color: "#1976d2" }}
        >
          Template Editor & AI Assistant
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button
            variant={editableContent ? "contained" : "outlined"}
            startIcon={<EditIcon />}
            onClick={() => {
              if (!editableContent) {
                setEditableContent(`# ${templateName} Report

Welcome to your report template. Start editing...`);
                setLivePreview(null);
              }
            }}
            size="small"
          >
            Edit Mode
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleGeneratePreview}
            disabled={isGeneratingPreview}
          >
            {isGeneratingPreview ? "Generating..." : "API Preview"}
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={onGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? "Generating..." : "Generate Report"}
          </Button>
        </Box>
      </Box>

      {/* Main Content Area */}
      <Grid
        container
        sx={{ height: "100vh", margin: 0, width: "100%", padding: 0 }}
      >
        {/* Left Panel - AI Suggestions */}
        <Grid
          item
          xs={12}
          md={5}
          sx={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
            padding: 0,
          }}
        >
          <Box sx={{}}>
            <Typography
              variant="h6"
              sx={{ fontWeight: 600, color: "#1976d2", mb: 1 }}
            >
              <LightbulbIcon sx={{ mr: 1, verticalAlign: "middle" }} />
              AI Content Suggestions
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Choose from AI-generated content suggestions to enhance your
              report
            </Typography>
          </Box>

          <Box
            sx={{
              flex: 1,
              overflow: "auto",
            }}
          >
            <List sx={{ p: 0 }}>
              {aiSuggestions.map((suggestion) => (
                <ListItem
                  key={suggestion.id}
                  sx={{
                    flexDirection: "column",
                    alignItems: "stretch",
                    p: 0,
                    mb: 2,
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                  onClick={() => handleSuggestionSelect(suggestion)}
                >
                  <Box sx={{}}>
                    <Box
                      sx={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        mb: 1,
                      }}
                    >
                      <Typography
                        variant="subtitle1"
                        sx={{ fontWeight: 600, color: "#1976d2" }}
                      >
                        {suggestion.title}
                      </Typography>
                      <Chip
                        label={suggestion.type.toUpperCase()}
                        size="small"
                        sx={{
                          fontSize: "0.7rem",
                          height: 20,
                          backgroundColor: "rgba(25, 118, 210, 0.15)",
                          color: "#1976d2",
                          border: "none",
                        }}
                      />
                    </Box>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 1.5 }}
                    >
                      {suggestion.description}
                    </Typography>
                    <Box sx={{}}>
                      <Typography
                        variant="body2"
                        sx={{ fontStyle: "italic", lineHeight: 1.4 }}
                      >
                        "{suggestion.content}"
                      </Typography>
                    </Box>
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAddToPreview(suggestion.content);
                      }}
                      sx={{ mt: 1, textTransform: "none" }}
                    >
                      Add to Preview
                    </Button>
                  </Box>
                </ListItem>
              ))}
            </List>
          </Box>
        </Grid>

        {/* Right Panel - Editable Preview */}
        <Grid
          item
          xs={12}
          md={7}
          sx={{
            display: "flex",
            flexDirection: "column",
            height: "100%",
          }}
        >
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Box>
              <Typography
                variant="h6"
                sx={{ fontWeight: 600, color: "#1976d2", mb: 0.5 }}
              >
                <EditIcon sx={{ mr: 1, verticalAlign: "middle" }} />
                Editable Preview
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Click to edit content directly or add AI suggestions
              </Typography>
            </Box>
            <Box sx={{ display: "flex", gap: 1 }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<SaveIcon />}
                onClick={() => {
                  // Save edited content
                  console.log("Save content:", editableContent);
                }}
              >
                Save Changes
              </Button>
            </Box>
          </Box>

          <Box
            sx={{
              flex: 1,
              overflow: "auto",
              p: 3,
              backgroundColor: "white",
            }}
          >
            {previewError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {previewError}
              </Alert>
            )}

            <Box
              sx={{
                minHeight: "500px",
                position: "relative",
              }}
            >
              <Typography
                variant="h6"
                sx={{
                  color: "#1976d2",
                }}
              >
                {templateName || "Report Preview"}
              </Typography>

              {editableContent ? (
                <TextField
                  fullWidth
                  multiline
                  rows={20}
                  value={editableContent}
                  onChange={(e) => setEditableContent(e.target.value)}
                  variant="outlined"
                  placeholder="Start typing or add AI suggestions..."
                  sx={{
                    "& .MuiOutlinedInput-root": {
                      fontSize: "0.95rem",
                      lineHeight: 1.6,
                      "& fieldset": {
                        border: "none",
                      },
                      "&:hover fieldset": {
                        border: "none",
                      },
                      "&.Mui-focused fieldset": {
                        border: "none",
                      },
                    },
                  }}
                />
              ) : livePreview ? (
                <Box
                  component="iframe"
                  src={livePreview}
                  sx={{
                    width: "100%",
                    height: "500px",
                    border: "none",
                    backgroundColor: "white",
                  }}
                  title="Template Preview"
                />
              ) : !isGeneratingPreview ? (
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    height: "400px",
                    textAlign: "center",
                    color: "text.secondary",
                  }}
                >
                  <AutoFixHighIcon
                    sx={{ fontSize: 64, mb: 2, color: "#e0e0e0" }}
                  />
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    Choose Your Editing Mode
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 3, maxWidth: 400 }}>
                    Click "Edit Mode" to write content directly, or "API
                    Preview" to generate a preview from your uploaded data. You
                    can also select AI suggestions from the left panel.
                  </Typography>
                  <Box sx={{ display: "flex", gap: 1 }}>
                    <Button
                      variant="contained"
                      startIcon={<EditIcon />}
                      onClick={() =>
                        setEditableContent(
                          `# ${templateName} Report\n\nStart writing your report content here...`
                        )
                      }
                    >
                      Start Editing
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      onClick={handleGeneratePreview}
                      disabled={Object.keys(editedData).length === 0}
                    >
                      API Preview
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    height: "400px",
                  }}
                >
                  <CircularProgress />
                  <Typography variant="body2" sx={{ ml: 2 }}>
                    Generating preview...
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>
        </Grid>
      </Grid>
    </>
  );
}
