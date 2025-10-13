import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
} from "@mui/material";
import {
  Edit,
  Download,
  Share,
  AutoAwesome,
  Visibility,
  Save,
  Cancel,
  PictureAsPdf,
  Description,
  TableChart,
  Analytics,
  Lightbulb,
  SmartToy,
  ExpandMore,
  ContentCopy,
  Print,
  Email,
} from "@mui/icons-material";

interface AutomatedReport {
  id: number;
  title: string;
  description: string;
  content: string;
  status: "draft" | "generating" | "completed" | "error";
  type: "summary" | "detailed" | "analytics" | "custom";
  data_source: "google_forms" | "internal_forms" | "mixed";
  source_id: string;
  created_at: string;
  updated_at: string;
  generated_by_ai: boolean;
  ai_suggestions?: string[];
  download_formats: string[];
  metrics?: {
    total_responses: number;
    completion_rate: number;
    avg_response_time: number;
  };
}

interface AIReportSuggestion {
  type: "content" | "structure" | "visualization" | "insight";
  suggestion: string;
  confidence: number;
  reasoning: string;
}

interface ReportViewerProps {
  reportId: number;
  onClose: () => void;
}

const EnhancedReportViewer: React.FC<ReportViewerProps> = ({
  reportId,
  onClose,
}) => {
  const [report, setReport] = useState<AutomatedReport | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [editedTitle, setEditedTitle] = useState("");
  const [editedDescription, setEditedDescription] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [aiSuggestions, setAiSuggestions] = useState<AIReportSuggestion[]>([]);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);

  const loadReport = React.useCallback(async () => {
    setIsLoading(true);
    try {
      // Simulate API call - replace with actual API
      const response = await fetch(`/api/reports/${reportId}`);
      const data = await response.json();
      setReport(data);
      setEditedContent(data.content);
      setEditedTitle(data.title);
      setEditedDescription(data.description);
    } catch (error) {
      console.error("Error loading report:", error);
    } finally {
      setIsLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await fetch(`/api/reports/${reportId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: editedTitle,
          description: editedDescription,
          content: editedContent,
        }),
      });

      if (response.ok) {
        setReport((prev: any) =>
          prev
            ? {
                ...prev,
                title: editedTitle,
                description: editedDescription,
                content: editedContent,
                updated_at: new Date().toISOString(),
              }
            : null
        );
        setIsEditing(false);
      }
    } catch (error) {
      console.error("Error saving report:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const generateAISuggestions = async () => {
    setIsGeneratingAI(true);
    try {
      const response = await fetch(`/api/reports/${reportId}/ai-suggestions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: editedContent,
          type: report?.type,
          data_source: report?.data_source,
        }),
      });

      const suggestions = await response.json();
      setAiSuggestions(suggestions);
    } catch (error) {
      console.error("Error generating AI suggestions:", error);
    } finally {
      setIsGeneratingAI(false);
    }
  };

  const applyAISuggestion = (suggestion: AIReportSuggestion) => {
    if (suggestion.type === "content") {
      setEditedContent((prev: any) => prev + "\n\n" + suggestion.suggestion);
    }
    // Add more logic for different suggestion types
  };

  const handleDownload = async (format: string) => {
    setIsDownloading(true);
    try {
      const response = await fetch(`/api/reports/${reportId}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ format }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = `${report?.title || "report"}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error("Error downloading report:", error);
    } finally {
      setIsDownloading(false);
    }
  };

  interface TabPanelProps {
    children?: React.ReactNode;
    value: number;
    index: number;
  }

  const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  if (isLoading) {
    return (
      <Dialog open maxWidth="lg" fullWidth>
        <DialogContent>
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            minHeight={400}
          >
            <CircularProgress />
          </Box>
        </DialogContent>
      </Dialog>
    );
  }

  if (!report) {
    return (
      <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
        <DialogContent>
          <Alert severity="error">Report not found</Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  }

  return (
    <Dialog open onClose={onClose} maxWidth="xl" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            {isEditing ? (
              <TextField
                value={editedTitle}
                onChange={(e: any) => setEditedTitle(e.target.value)}
                variant="outlined"
                size="small"
                fullWidth
              />
            ) : (
              <Typography variant="h5">{report.title}</Typography>
            )}
            <Box display="flex" gap={1} mt={1}>
              <Chip
                label={report.status}
                color={report.status === "completed" ? "success" : "default"}
                size="small"
              />
              <Chip label={report.type} variant="outlined" size="small" />
              {report.generated_by_ai && (
                <Chip
                  label="AI Enhanced"
                  color="secondary"
                  size="small"
                  icon={<SmartToy />}
                />
              )}
            </Box>
          </Box>
          <Box display="flex" gap={1}>
            {!isEditing ? (
              <>
                <Tooltip title="Edit Report">
                  <IconButton onClick={() => setIsEditing(true)}>
                    <Edit />
                  </IconButton>
                </Tooltip>
                <Tooltip title="AI Suggestions">
                  <IconButton
                    onClick={generateAISuggestions}
                    disabled={isGeneratingAI}
                    color="secondary"
                  >
                    {isGeneratingAI ? (
                      <CircularProgress size={24} />
                    ) : (
                      <AutoAwesome />
                    )}
                  </IconButton>
                </Tooltip>
              </>
            ) : (
              <>
                <Button
                  onClick={handleSave}
                  disabled={isSaving}
                  startIcon={
                    isSaving ? <CircularProgress size={16} /> : <Save />
                  }
                  variant="contained"
                  size="small"
                >
                  Save
                </Button>
                <Button
                  onClick={() => setIsEditing(false)}
                  startIcon={<Cancel />}
                  size="small"
                >
                  Cancel
                </Button>
              </>
            )}
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 2 }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
          >
            <Tab label="Content" icon={<Description />} />
            <Tab label="Analytics" icon={<Analytics />} />
            <Tab label="AI Insights" icon={<Lightbulb />} />
            <Tab label="Export" icon={<Download />} />
          </Tabs>
        </Box>

        {/* Content Tab */}
        <TabPanel value={activeTab} index={0}>
          {isEditing ? (
            <Box>
              <TextField
                label="Description"
                value={editedDescription}
                onChange={(e: any) => setEditedDescription(e.target.value)}
                multiline
                rows={2}
                fullWidth
                margin="normal"
              />
              <TextField
                label="Content (Markdown supported)"
                value={editedContent}
                onChange={(e: any) => setEditedContent(e.target.value)}
                multiline
                rows={20}
                fullWidth
                margin="normal"
                variant="outlined"
              />
            </Box>
          ) : (
            <Box>
              <Typography variant="body2" color="textSecondary" paragraph>
                {report.description}
              </Typography>
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography
                  variant="body1"
                  component="div"
                  sx={{
                    whiteSpace: "pre-wrap",
                    fontFamily: "monospace",
                    fontSize: "0.9rem",
                    lineHeight: 1.6,
                  }}
                >
                  {report.content}
                </Typography>
              </Paper>
            </Box>
          )}
        </TabPanel>

        {/* Analytics Tab */}
        <TabPanel value={activeTab} index={1}>
          {report.metrics && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h4" color="primary">
                      {report.metrics.total_responses}
                    </Typography>
                    <Typography variant="body2">Total Responses</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h4" color="success.main">
                      {(report.metrics.completion_rate * 100).toFixed(1)}%
                    </Typography>
                    <Typography variant="body2">Completion Rate</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card>
                  <CardContent>
                    <Typography variant="h4" color="info.main">
                      {Math.round(report.metrics.avg_response_time)}s
                    </Typography>
                    <Typography variant="body2">Avg Response Time</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        {/* AI Insights Tab */}
        <TabPanel value={activeTab} index={2}>
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
            mb={2}
          >
            <Typography variant="h6">AI-Powered Insights</Typography>
            <Button
              startIcon={<AutoAwesome />}
              onClick={generateAISuggestions}
              disabled={isGeneratingAI}
              variant="outlined"
            >
              {isGeneratingAI ? "Generating..." : "Generate New Insights"}
            </Button>
          </Box>

          {aiSuggestions.length > 0 ? (
            <List>
              {aiSuggestions.map((suggestion, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={suggestion.type}
                        size="small"
                        color="secondary"
                      />
                      <Typography variant="body2">
                        {suggestion.suggestion.substring(0, 80)}...
                      </Typography>
                      <Chip
                        label={`${Math.round(suggestion.confidence * 100)}%`}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography paragraph>{suggestion.suggestion}</Typography>
                      <Typography
                        variant="body2"
                        color="textSecondary"
                        paragraph
                      >
                        <strong>Reasoning:</strong> {suggestion.reasoning}
                      </Typography>
                      <Button
                        size="small"
                        onClick={() => applyAISuggestion(suggestion)}
                        startIcon={<ContentCopy />}
                      >
                        Apply Suggestion
                      </Button>
                    </Box>
                  </AccordionDetails>
                </Accordion>
              ))}
            </List>
          ) : (
            <Alert severity="info">
              No AI insights available yet. Click "Generate New Insights" to get
              AI-powered suggestions for improving your report.
            </Alert>
          )}
        </TabPanel>

        {/* Export Tab */}
        <TabPanel value={activeTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Download Formats
              </Typography>
              <List>
                {[
                  {
                    format: "pdf",
                    label: "PDF Document",
                    icon: <PictureAsPdf />,
                  },
                  {
                    format: "word",
                    label: "Word Document",
                    icon: <Description />,
                  },
                  {
                    format: "excel",
                    label: "Excel Spreadsheet",
                    icon: <TableChart />,
                  },
                  { format: "html", label: "HTML Page", icon: <Visibility /> },
                ].map((item: any) => (
                  <ListItem key={item.format}>
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.label} />
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleDownload(item.format)}
                      disabled={isDownloading}
                      startIcon={<Download />}
                    >
                      Download
                    </Button>
                  </ListItem>
                ))}
              </List>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Share Options
              </Typography>
              <List>
                <ListItem>
                  <ListItemIcon>
                    <Email />
                  </ListItemIcon>
                  <ListItemText primary="Email Report" />
                  <Button variant="outlined" size="small">
                    Share
                  </Button>
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Share />
                  </ListItemIcon>
                  <ListItemText primary="Generate Share Link" />
                  <Button variant="outlined" size="small">
                    Create Link
                  </Button>
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Print />
                  </ListItemIcon>
                  <ListItemText primary="Print Report" />
                  <Button variant="outlined" size="small">
                    Print
                  </Button>
                </ListItem>
              </List>
            </Grid>
          </Grid>
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Typography variant="caption" color="textSecondary" sx={{ mr: "auto" }}>
          Last updated: {new Date(report.updated_at).toLocaleString()}
        </Typography>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>

      {/* Floating Action Button for Quick Actions */}
      <SpeedDial
        ariaLabel="Quick Actions"
        sx={{ position: "absolute", bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
      >
        <SpeedDialAction
          icon={<Download />}
          tooltipTitle="Quick Download (PDF)"
          onClick={() => handleDownload("pdf")}
        />
        <SpeedDialAction
          icon={<Share />}
          tooltipTitle="Share Report"
          onClick={() => {
            /* Add share logic */
          }}
        />
        <SpeedDialAction
          icon={<AutoAwesome />}
          tooltipTitle="AI Enhance"
          onClick={generateAISuggestions}
        />
      </SpeedDial>
    </Dialog>
  );
};

export default EnhancedReportViewer;
