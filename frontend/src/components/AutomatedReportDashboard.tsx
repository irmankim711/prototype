import React, { useState, useEffect } from "react";
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
  CircularProgress,
  Alert,
  Fab,
  Menu,
  MenuItem,
  Divider,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Badge,
  ListItemIcon,
  ListItemText,
} from "@mui/material";
import {
  Add,
  Visibility,
  Edit,
  Delete,
  Download,
  Share,
  AutoAwesome,
  Search,
  Refresh,
  MoreVert,
  SmartToy,
  Analytics,
  CheckCircle,
  Error,
  Warning,
  Pending,
} from "@mui/icons-material";
import EnhancedReportViewer from "./EnhancedReportViewer";

interface AutomatedReport {
  id: number;
  title: string;
  description: string;
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

const AutomatedReportDashboard: React.FC = () => {
  const [reports, setReports] = useState<AutomatedReport[]>([]);
  const [filteredReports, setFilteredReports] = useState<AutomatedReport[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedReport, setSelectedReport] = useState<number | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterType, setFilterType] = useState<string>("all");
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [isGeneratingAI, setIsGeneratingAI] = useState<number | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const filterReports = React.useCallback(() => {
    let filtered = reports;

    if (searchTerm) {
      filtered = filtered.filter(
        (report) =>
          report.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          report.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (filterStatus !== "all") {
      filtered = filtered.filter((report) => report.status === filterStatus);
    }

    if (filterType !== "all") {
      filtered = filtered.filter((report) => report.type === filterType);
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

  const handleMenuClick = (
    event: React.MouseEvent<HTMLElement>,
    reportId: number
  ) => {
    setAnchorEl(event.currentTarget);
    setSelectedReportId(reportId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedReportId(null);
  };

  const enhanceWithAI = async (reportId: number) => {
    setIsGeneratingAI(reportId);
    try {
      const response = await fetch(`/api/reports/${reportId}/enhance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "general" }),
      });

      if (response.ok) {
        await loadReports(); // Reload to get updated report
      }
    } catch (error) {
      console.error("Error enhancing report:", error);
    } finally {
      setIsGeneratingAI(null);
    }
  };

  const deleteReport = async (reportId: number) => {
    if (window.confirm("Are you sure you want to delete this report?")) {
      try {
        const response = await fetch(`/api/reports/${reportId}`, {
          method: "DELETE",
        });

        if (response.ok) {
          setReports((prev) => prev.filter((r) => r.id !== reportId));
        }
      } catch (error) {
        console.error("Error deleting report:", error);
      }
    }
  };

  const quickDownload = async (reportId: number, format: string) => {
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
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle color="success" />;
      case "generating":
        return <Pending color="info" />;
      case "error":
        return <Error color="error" />;
      case "draft":
        return <Warning color="warning" />;
      default:
        return <Pending />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "generating":
        return "info";
      case "error":
        return "error";
      case "draft":
        return "warning";
      default:
        return "default";
    }
  };

  const CreateReportDialog = () => (
    <Dialog
      open={showCreateDialog}
      onClose={() => setShowCreateDialog(false)}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>Create New Automated Report</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2 }}>
          <TextField label="Report Title" fullWidth margin="normal" />
          <TextField
            label="Description"
            fullWidth
            multiline
            rows={3}
            margin="normal"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Report Type</InputLabel>
            <Select label="Report Type">
              <MenuItem value="summary">Summary Report</MenuItem>
              <MenuItem value="detailed">Detailed Analysis</MenuItem>
              <MenuItem value="analytics">Analytics Report</MenuItem>
              <MenuItem value="custom">Custom Report</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Data Source</InputLabel>
            <Select label="Data Source">
              <MenuItem value="google_forms">Google Forms</MenuItem>
              <MenuItem value="internal_forms">Internal Forms</MenuItem>
              <MenuItem value="mixed">Mixed Sources</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowCreateDialog(false)}>Cancel</Button>
        <Button variant="contained" startIcon={<AutoAwesome />}>
          Generate with AI
        </Button>
      </DialogActions>
    </Dialog>
  );

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
            Automated Reports
          </Typography>
          <Typography variant="body2" color="textSecondary">
            AI-powered report generation and management
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setShowCreateDialog(true)}
          size="large"
        >
          Create Report
        </Button>
      </Box>

      {/* Filters and Search */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search reports..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
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
                onChange={(e) => setFilterStatus(e.target.value)}
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
                onChange={(e) => setFilterType(e.target.value)}
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
          {filteredReports.map((report) => (
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
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuClick(e, report.id)}
                    >
                      <MoreVert />
                    </IconButton>
                  </Box>

                  <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                    <Chip
                      icon={getStatusIcon(report.status)}
                      label={report.status}
                      color={
                        getStatusColor(report.status) as
                          | "success"
                          | "info"
                          | "error"
                          | "warning"
                          | "default"
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

                  {report.metrics && (
                    <Box mb={2}>
                      <Typography
                        variant="body2"
                        color="textSecondary"
                        gutterBottom
                      >
                        Quick Stats:
                      </Typography>
                      <Grid container spacing={1}>
                        <Grid item xs={4}>
                          <Typography variant="caption" display="block">
                            Responses
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {report.metrics.total_responses}
                          </Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="caption" display="block">
                            Completion
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {(report.metrics.completion_rate * 100).toFixed(1)}%
                          </Typography>
                        </Grid>
                        <Grid item xs={4}>
                          <Typography variant="caption" display="block">
                            Avg Time
                          </Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {Math.round(report.metrics.avg_response_time)}s
                          </Typography>
                        </Grid>
                      </Grid>
                    </Box>
                  )}

                  <Typography variant="caption" color="textSecondary">
                    Updated: {new Date(report.updated_at).toLocaleDateString()}{" "}
                    {new Date(report.updated_at).toLocaleTimeString()}
                  </Typography>
                </CardContent>

                <Box sx={{ p: 2, pt: 0 }}>
                  <Grid container spacing={1}>
                    <Grid item xs={6}>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<Visibility />}
                        onClick={() => setSelectedReport(report.id)}
                        disabled={report.status === "generating"}
                      >
                        View
                      </Button>
                    </Grid>
                    <Grid item xs={6}>
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={
                          isGeneratingAI === report.id ? (
                            <CircularProgress size={16} />
                          ) : (
                            <AutoAwesome />
                          )
                        }
                        onClick={() => enhanceWithAI(report.id)}
                        disabled={
                          isGeneratingAI === report.id ||
                          report.status === "generating"
                        }
                      >
                        {isGeneratingAI === report.id
                          ? "Enhancing..."
                          : "AI Enhance"}
                      </Button>
                    </Grid>
                  </Grid>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem
          onClick={() => {
            setSelectedReport(selectedReportId);
            handleMenuClose();
          }}
        >
          <ListItemIcon>
            <Visibility />
          </ListItemIcon>
          <ListItemText>View Report</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            /* Edit logic */ handleMenuClose();
          }}
        >
          <ListItemIcon>
            <Edit />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            quickDownload(selectedReportId!, "pdf");
            handleMenuClose();
          }}
        >
          <ListItemIcon>
            <Download />
          </ListItemIcon>
          <ListItemText>Download PDF</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            quickDownload(selectedReportId!, "word");
            handleMenuClose();
          }}
        >
          <ListItemIcon>
            <Download />
          </ListItemIcon>
          <ListItemText>Download Word</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            quickDownload(selectedReportId!, "excel");
            handleMenuClose();
          }}
        >
          <ListItemIcon>
            <Download />
          </ListItemIcon>
          <ListItemText>Download Excel</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            /* Share logic */ handleMenuClose();
          }}
        >
          <ListItemIcon>
            <Share />
          </ListItemIcon>
          <ListItemText>Share</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            deleteReport(selectedReportId!);
            handleMenuClose();
          }}
          sx={{ color: "error.main" }}
        >
          <ListItemIcon>
            <Delete color="error" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Report Viewer Dialog */}
      {selectedReport && (
        <EnhancedReportViewer
          reportId={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}

      {/* Create Report Dialog */}
      <CreateReportDialog />

      {/* Floating Action Button for Quick AI Analysis */}
      <Fab
        color="secondary"
        aria-label="AI Analysis"
        sx={{ position: "fixed", bottom: 16, right: 16 }}
        onClick={() => {
          // Quick AI analysis of all reports
          console.log("Running AI analysis on all reports...");
        }}
      >
        <Badge
          badgeContent={reports.filter((r) => !r.generated_by_ai).length}
          color="error"
        >
          <Analytics />
        </Badge>
      </Fab>
    </Box>
  );
};

export default AutomatedReportDashboard;
