import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  Menu,
  MenuItem,
} from "@mui/material";
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Lightbulb as LightbulbIcon,
  AutoFixHigh as AutoFixHighIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Add as AddIcon,
  MoreVert as MoreVertIcon,
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

  const handleGeneratePreview = async () => {
    if (!templateName || Object.keys(editedData).length === 0) return;

    setIsGeneratingPreview(true);
    setPreviewError(null);

    try {
      const preview = await generateLivePreview(templateName, editedData);
      setLivePreview(preview);
    } catch (error: any) {
      setPreviewError(error.message || "Failed to generate preview");
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
  const handleSuggestionSelect = (suggestion: any) => {
    setSelectedSuggestion(suggestion.id);
    setEditableContent(suggestion.content);
  };

  // Handle adding suggestion to preview
  const handleAddToPreview = (content: string) => {
    setEditableContent((prev: any) => prev + "\n\n" + content);
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
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: "1px solid #e0e0e0",
          backgroundColor: "#fafafa",
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
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleGeneratePreview}
            disabled={isGeneratingPreview}
          >
            {isGeneratingPreview ? "Generating..." : "Refresh Preview"}
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
      <Grid container sx={{ flex: 1, height: "calc(100vh - 80px)" }}>
        {/* Left Panel - AI Suggestions */}
        <Grid
          item
          xs={12}
          md={5}
          sx={{
            borderRight: "1px solid #e0e0e0",
            display: "flex",
            flexDirection: "column",
            height: "100%",
          }}
        >
          <Box
            sx={{
              p: 3,
              borderBottom: "1px solid #e0e0e0",
              backgroundColor: "#f8f9fa",
            }}
          >
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
              p: 2,
            }}
          >
            <List sx={{ p: 0 }}>
              {aiSuggestions.map((suggestion: any) => (
                <ListItem
                  key={suggestion.id}
                  sx={{
                    flexDirection: "column",
                    alignItems: "stretch",
                    p: 0,
                    mb: 2,
                    cursor: "pointer",
                    border:
                      selectedSuggestion === suggestion.id
                        ? "2px solid #1976d2"
                        : "1px solid #e0e0e0",
                    borderRadius: 2,
                    backgroundColor:
                      selectedSuggestion === suggestion.id
                        ? "#f3f7ff"
                        : "white",
                    transition: "all 0.2s ease",
                    "&:hover": {
                      backgroundColor: "#f8f9fa",
                      transform: "translateY(-1px)",
                      boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                    },
                  }}
                  onClick={() => handleSuggestionSelect(suggestion)}
                >
                  <Box sx={{ p: 2 }}>
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
                        variant="outlined"
                        sx={{
                          fontSize: "0.7rem",
                          height: 20,
                          borderColor: "#1976d2",
                          color: "#1976d2",
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
                    <Box
                      sx={{
                        p: 1.5,
                        backgroundColor: "rgba(25, 118, 210, 0.08)",
                        borderRadius: 1,
                        borderLeft: "3px solid #1976d2",
                      }}
                    >
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
                      onClick={(e: any) => {
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
              p: 3,
              borderBottom: "1px solid #e0e0e0",
              backgroundColor: "#f8f9fa",
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

            <Paper
              elevation={0}
              sx={{
                p: 3,
                border: "1px solid #e0e0e0",
                borderRadius: 2,
                minHeight: "500px",
                backgroundColor: "#fafafa",
                position: "relative",
              }}
            >
              <Typography
                variant="h6"
                sx={{
                  mb: 3,
                  color: "#1976d2",
                  borderBottom: "2px solid #e0e0e0",
                  pb: 1,
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
                  onChange={(e: any) => setEditableContent(e.target.value)}
                  variant="outlined"
                  placeholder="Start typing or add AI suggestions..."
                  sx={{
                    backgroundColor: "white",
                    "& .MuiOutlinedInput-root": {
                      fontSize: "0.95rem",
                      lineHeight: 1.6,
                      "& fieldset": {
                        borderColor: "#e0e0e0",
                      },
                      "&:hover fieldset": {
                        borderColor: "#1976d2",
                      },
                      "&.Mui-focused fieldset": {
                        borderColor: "#1976d2",
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
                    borderRadius: 1,
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
                    Start Building Your Report
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 3, maxWidth: 400 }}>
                    Select AI suggestions from the left panel to add content, or
                    click "Refresh Preview" to see your template with current
                    data.
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<LightbulbIcon />}
                    onClick={() =>
                      setEditableContent(
                        "Click to start editing your report content..."
                      )
                    }
                  >
                    Start Editing
                  </Button>
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
            </Paper>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
