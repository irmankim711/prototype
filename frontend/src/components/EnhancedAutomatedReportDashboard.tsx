import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Tooltip,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
} from "@mui/material";
import {
  Add,
  Visibility,
  Edit,
  Download,
  Share,
  AutoAwesome,
  Search,
  Refresh,
  SmartToy,
  Analytics,
  Save,
  Cancel,
  PictureAsPdf,
  Description,
  TableChart,
  Print,
  Email,
  ContentCopy,
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

interface EditableReportViewerProps {
  report: AutomatedReport;
  onClose: () => void;
  onSave: (updatedReport: Partial<AutomatedReport>) => Promise<void>;
  onDownload: (reportId: number, format: string) => Promise<void>;
  onGenerateAI: (reportId: number) => Promise<void>;
}

const EditableReportViewer: React.FC<EditableReportViewerProps> = ({
  report,
  onClose,
  onSave,
  onDownload,
  onGenerateAI,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(report.title);
  const [editedDescription, setEditedDescription] = useState(
    report.description
  );
  const [editedContent, setEditedContent] = useState(report.content);
  const [isSaving, setIsSaving] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Track changes
  useEffect(() => {
    const hasChanges =
      editedTitle !== report.title ||
      editedDescription !== report.description ||
      editedContent !== report.content;
    setHasUnsavedChanges(hasChanges);
  }, [editedTitle, editedDescription, editedContent, report]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave({
        title: editedTitle,
        description: editedDescription,
        content: editedContent,
      });
      setIsEditing(false);
      setHasUnsavedChanges(false);
    } catch (error) {
      console.error("Error saving report:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditedTitle(report.title);
    setEditedDescription(report.description);
    setEditedContent(report.content);
    setIsEditing(false);
    setHasUnsavedChanges(false);
  };

  const handleDownload = async (format: string) => {
    setIsDownloading(true);
    try {
      await onDownload(report.id, format);
    } catch (error) {
      console.error("Error downloading report:", error);
    } finally {
      setIsDownloading(false);
    }
  };

  const handleGenerateAI = async () => {
    setIsGeneratingAI(true);
    try {
      await onGenerateAI(report.id);
    } catch (error) {
      console.error("Error generating AI insights:", error);
    } finally {
      setIsGeneratingAI(false);
    }
  };

  const TabPanel = ({
    children,
    value,
    index,
  }: {
    children: React.ReactNode;
    value: number;
    index: number;
  }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Dialog open onClose={onClose} maxWidth="xl" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box flex={1}>
            {isEditing ? (
              <TextField
                value={editedTitle}
                onChange={(e: any) => setEditedTitle(e.target.value)}
                variant="outlined"
                size="small"
                fullWidth
                label="Report Title"
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
              {hasUnsavedChanges && (
                <Chip label="Unsaved Changes" color="warning" size="small" />
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
                <Tooltip title="AI Enhancement">
                  <IconButton
                    onClick={handleGenerateAI}
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
                  disabled={isSaving || !hasUnsavedChanges}
                  startIcon={
                    isSaving ? <CircularProgress size={16} /> : <Save />
                  }
                  variant="contained"
                  size="small"
                >
                  Save
                </Button>
                <Button
                  onClick={handleCancel}
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
                label="Content"
                value={editedContent}
                onChange={(e: any) => setEditedContent(e.target.value)}
                multiline
                rows={20}
                fullWidth
                margin="normal"
                variant="outlined"
                helperText="You can use markdown formatting"
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
          {report.metrics ? (
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
          ) : (
            <Alert severity="info">
              No analytics data available for this report.
            </Alert>
          )}
        </TabPanel>

        {/* Export Tab */}
        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Download Formats
              </Typography>
              <Grid container spacing={2}>
                {[
                  {
                    format: "pdf",
                    label: "PDF Document",
                    icon: <PictureAsPdf />,
                    color: "error",
                  },
                  {
                    format: "word",
                    label: "Word Document",
                    icon: <Description />,
                    color: "primary",
                  },
                  {
                    format: "excel",
                    label: "Excel Spreadsheet",
                    icon: <TableChart />,
                    color: "success",
                  },
                  {
                    format: "html",
                    label: "HTML Page",
                    icon: <Visibility />,
                    color: "info",
                  },
                ].map((item: any) => (
                  <Grid item xs={12} sm={6} key={item.format}>
                    <Card>
                      <CardContent sx={{ textAlign: "center" }}>
                        <Box color={`${item.color}.main`} mb={1}>
                          {item.icon}
                        </Box>
                        <Typography variant="body2" gutterBottom>
                          {item.label}
                        </Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => handleDownload(item.format)}
                          disabled={isDownloading}
                          startIcon={
                            isDownloading ? (
                              <CircularProgress size={16} />
                            ) : (
                              <Download />
                            )
                          }
                          fullWidth
                        >
                          Download
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Share Options
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Button
                  variant="outlined"
                  startIcon={<Email />}
                  onClick={() => {
                    /* Add email functionality */
                  }}
                >
                  Email Report
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Share />}
                  onClick={() => {
                    /* Add share link functionality */
                  }}
                >
                  Generate Share Link
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Print />}
                  onClick={() => window.print()}
                >
                  Print Report
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<ContentCopy />}
                  onClick={() => navigator.clipboard.writeText(report.content)}
                >
                  Copy Content
                </Button>
              </Box>
            </Grid>
          </Grid>
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Typography variant="caption" color="textSecondary" sx={{ mr: "auto" }}>
          Last updated: {new Date(report.updated_at).toLocaleDateString()}{" "}
          {new Date(report.updated_at).toLocaleTimeString()}
        </Typography>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>

      {/* Quick Actions Speed Dial */}
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
          icon={<Edit />}
          tooltipTitle="Edit Report"
          onClick={() => setIsEditing(true)}
        />
        <SpeedDialAction
          icon={<AutoAwesome />}
          tooltipTitle="AI Enhancement"
          onClick={handleGenerateAI}
        />
        <SpeedDialAction
          icon={<Share />}
          tooltipTitle="Share Report"
          onClick={() => {
            /* Add share functionality */
          }}
        />
      </SpeedDial>
    </Dialog>
  );
};

// Enhanced AutomatedReportDashboard with editing and download capabilities
const EnhancedAutomatedReportDashboard: React.FC = () => {
  const [reports, setReports] = useState<AutomatedReport[]>([]);
  const [filteredReports, setFilteredReports] = useState<AutomatedReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<AutomatedReport | null>(
    null
  );
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterType, setFilterType] = useState<string>("all");

  useEffect(() => {
    loadReports();
  }, []);

  const filterReports = React.useCallback(() => {
    let filtered = reports;

    if (searchTerm) {
      filtered = filtered.filter(
        (report: any) =>
          report.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          report.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
          report.content.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterStatus !== "all") {
      filtered = filtered.filter((report: any) => report.status === filterStatus);
    }

    if (filterType !== "all") {
      filtered = filtered.filter((report: any) => report.type === filterType);
    }

    setFilteredReports(filtered);
  }, [reports, searchTerm, filterStatus, filterType]);

  useEffect(() => {
    filterReports();
  }, [filterReports]);

  const loadReports = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/automated-reports");
      const data = await response.json();
      setReports(data);
    } catch (error) {
      console.error("Error loading reports:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveReport = async (
    reportId: number,
    updatedData: Partial<AutomatedReport>
  ) => {
    try {
      const response = await fetch(`/api/reports/${reportId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedData),
      });

      if (response.ok) {
        // Update local state
        setReports((prev: any) =>
          prev.map((report: any) =>
            report.id === reportId
              ? {
                  ...report,
                  ...updatedData,
                  updated_at: new Date().toISOString(),
                }
              : report
          )
        );

        // Update selected report if it's the one being edited
        if (selectedReport && selectedReport.id === reportId) {
          setSelectedReport((prev: any) =>
            prev ? { ...prev, ...updatedData } : null
          );
        }
      }
    } catch (error) {
      console.error("Error saving report:", error);
      throw error;
    }
  };

  const handleDownloadReport = async (reportId: number, format: string) => {
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
        a.download = `report.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error("Error downloading report:", error);
      throw error;
    }
  };

  const handleGenerateAI = async (reportId: number) => {
    try {
      const response = await fetch(`/api/reports/${reportId}/enhance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "general" }),
      });

      if (response.ok) {
        await loadReports(); // Reload to get updated content
      }
    } catch (error) {
      console.error("Error generating AI insights:", error);
      throw error;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Box>
          <Typography variant="h4" gutterBottom>
            Enhanced Automated Reports
          </Typography>
          <Typography variant="body2" color="textSecondary">
            View, edit, and download AI-powered reports with advanced features
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => {
            /* Add create report functionality */
          }}
          size="large"
        >
          Create Report
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search reports..."
              value={searchTerm}
              onChange={(e: any) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <Search sx={{ mr: 1, color: "text.secondary" }} />
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={filterStatus}
                onChange={(e: any) => setFilterStatus(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="generating">Generating</MenuItem>
                <MenuItem value="draft">Draft</MenuItem>
                <MenuItem value="error">Error</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={filterType}
                onChange={(e: any) => setFilterType(e.target.value)}
                label="Type"
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="summary">Summary</MenuItem>
                <MenuItem value="detailed">Detailed</MenuItem>
                <MenuItem value="analytics">Analytics</MenuItem>
                <MenuItem value="custom">Custom</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadReports}
            >
              Refresh
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Reports Grid */}
      {isLoading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : filteredReports.length === 0 ? (
        <Alert severity="info">
          No reports found. Create your first automated report to get started.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {filteredReports.map((report: any) => (
            <Grid item xs={12} md={6} lg={4} key={report.id}>
              <Card
                sx={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box
                    display="flex"
                    justifyContent="space-between"
                    alignItems="flex-start"
                    mb={2}
                  >
                    <Box flexGrow={1}>
                      <Typography variant="h6" gutterBottom>
                        {report.title}
                      </Typography>
                      <Typography
                        variant="body2"
                        color="textSecondary"
                        paragraph
                      >
                        {report.description}
                      </Typography>
                    </Box>
                  </Box>

                  <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                    <Chip
                      label={report.status}
                      color={
                        report.status === "completed" ? "success" : "default"
                      }
                      size="small"
                    />
                    <Chip label={report.type} variant="outlined" size="small" />
                    {report.generated_by_ai && (
                      <Chip
                        icon={<SmartToy />}
                        label="AI Enhanced"
                        color="secondary"
                        size="small"
                      />
                    )}
                  </Box>

                  <Typography variant="caption" color="textSecondary">
                    Updated: {new Date(report.updated_at).toLocaleDateString()}
                  </Typography>
                </CardContent>

                <Box sx={{ p: 2, pt: 0 }}>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<Visibility />}
                        onClick={() => setSelectedReport(report)}
                        disabled={report.status === "generating"}
                      >
                        View & Edit
                      </Button>
                    </Grid>
                    <Grid item xs={6}>
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<Download />}
                        onClick={() => handleDownloadReport(report.id, "pdf")}
                        disabled={report.status === "generating"}
                      >
                        Download
                      </Button>
                    </Grid>
                  </Grid>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Enhanced Report Viewer */}
      {selectedReport && (
        <EditableReportViewer
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
          onSave={(updatedData: any) =>
            handleSaveReport(selectedReport.id, updatedData)
          }
          onDownload={handleDownloadReport}
          onGenerateAI={handleGenerateAI}
        />
      )}
    </Box>
  );
};

export default EnhancedAutomatedReportDashboard;
