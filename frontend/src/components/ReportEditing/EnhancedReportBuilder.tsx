/**
 * Enhanced Report Builder with Advanced Editing Features
 * Integrates rich text editing, version control, and template management
 */

import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  Button,
  Alert,
  Divider,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import {
  Edit,
  History,
  Palette,
  Preview,
  Save,
  Download,
  Share,
} from "@mui/icons-material";
import { useParams, useNavigate } from "react-router-dom";
import ReportEditor from "./ReportEditor";
import VersionHistory from "./VersionHistory";
import TemplateManager from "./TemplateManager";
import enhancedReportService from "../../services/enhancedReportService";
import type {
  ReportVersion,
  ReportTemplate,
} from "../../services/enhancedReportService";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`report-editing-tabpanel-${index}`}
      aria-labelledby={`report-editing-tab-${index}`}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

interface ReportData {
  id: number;
  title: string;
  content?: any;
  current_version?: ReportVersion;
  created_at: string;
  updated_at: string;
}

const EnhancedReportBuilder: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState(0);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Preview and export states
  const [previewMode, setPreviewMode] = useState(false);
  const [previewVersion, setPreviewVersion] = useState<ReportVersion | null>(
    null
  );
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (reportId) {
      fetchReportData();
    }
  }, [reportId]);

  const fetchReportData = async () => {
    if (!reportId) return;

    try {
      setLoading(true);
      setError(null);

      // For now, we'll simulate report data since the API integration would need the existing report service
      // In a real implementation, this would fetch from the existing report API
      const simulatedData: ReportData = {
        id: parseInt(reportId),
        title: `Report ${reportId}`,
        content: {
          title: `Report ${reportId}`,
          content:
            "<p>This is the main content of your report. You can edit this using the rich text editor.</p>",
          sections: [],
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setReportData(simulatedData);
    } catch (err) {
      console.error("Failed to fetch report:", err);
      setError("Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    if (hasUnsavedChanges && newValue !== activeTab) {
      const confirmSwitch = window.confirm(
        "You have unsaved changes. Are you sure you want to switch tabs? Your changes will be auto-saved."
      );
      if (!confirmSwitch) return;
    }
    setActiveTab(newValue);
  };

  const handleContentSave = (content: any, version?: ReportVersion) => {
    setHasUnsavedChanges(false);
    if (version) {
      setReportData((prev: any) =>
        prev ? { ...prev, current_version: version } : null
      );
    }
  };

  const handleAutoSave = (content: any) => {
    // Auto-save doesn't change the unsaved state since it's automatic
    console.log("Auto-saved content:", content);
  };

  const handleVersionSelect = async (version: ReportVersion) => {
    try {
      const versionData = await enhancedReportService.getSpecificVersion(
        parseInt(reportId!),
        version.id
      );
      setPreviewVersion(versionData);
      setPreviewMode(true);
    } catch (err) {
      console.error("Failed to load version:", err);
      setError("Failed to load version for preview");
    }
  };

  const handleVersionRestore = (newVersion: ReportVersion) => {
    setReportData((prev: any) =>
      prev ? { ...prev, current_version: newVersion } : null
    );
    setActiveTab(0); // Switch back to editor
    setError(null);
  };

  const handleTemplateApply = (template: ReportTemplate) => {
    // Template applied, refresh the data
    fetchReportData();
    setActiveTab(0); // Switch back to editor
  };

  const handleExportReport = async () => {
    if (!reportData) return;

    setExporting(true);
    try {
      // This would integrate with your existing export functionality
      // For now, we'll simulate the export
      await new Promise((resolve: any) => setTimeout(resolve, 2000));

      // Simulate download
      const blob = new Blob(["Exported report content"], {
        type: "text/plain",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${reportData.title}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed:", err);
      setError("Failed to export report");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl">
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="400px"
        >
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error && !reportData) {
    return (
      <Container maxWidth="xl">
        <Alert severity="error" sx={{ mt: 4 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  if (!reportData) {
    return (
      <Container maxWidth="xl">
        <Alert severity="warning" sx={{ mt: 4 }}>
          Report not found
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            mb: 2,
          }}
        >
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              {reportData.title}
            </Typography>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 2,
                flexWrap: "wrap",
              }}
            >
              <Typography variant="body2" color="text.secondary">
                Last updated: {new Date(reportData.updated_at).toLocaleString()}
              </Typography>

              {reportData.current_version && (
                <Chip
                  label={`Version ${reportData.current_version.version_number}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              )}

              {hasUnsavedChanges && (
                <Chip label="Unsaved changes" size="small" color="warning" />
              )}
            </Box>
          </Box>

          {/* Action Buttons */}
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
            <Button
              variant="outlined"
              startIcon={<Preview />}
              onClick={() => setPreviewMode(true)}
            >
              Preview
            </Button>

            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={handleExportReport}
              disabled={exporting}
            >
              {exporting ? "Exporting..." : "Export"}
            </Button>

            <Button variant="outlined" startIcon={<Share />}>
              Share
            </Button>
          </Box>
        </Box>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
      </Box>

      {/* Main Content */}
      <Paper elevation={1}>
        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="report editing tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab
              icon={<Edit />}
              label="Editor"
              id="report-editing-tab-0"
              aria-controls="report-editing-tabpanel-0"
            />
            <Tab
              icon={<History />}
              label="Version History"
              id="report-editing-tab-1"
              aria-controls="report-editing-tabpanel-1"
            />
            <Tab
              icon={<Palette />}
              label="Templates"
              id="report-editing-tab-2"
              aria-controls="report-editing-tabpanel-2"
            />
          </Tabs>
        </Box>

        {/* Tab Content */}
        <TabPanel value={activeTab} index={0}>
          <ReportEditor
            reportId={reportData.id}
            initialContent={reportData.content}
            onSave={handleContentSave}
            onAutoSave={handleAutoSave}
            showVersionControls={true}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <VersionHistory
            reportId={reportData.id}
            onVersionSelect={handleVersionSelect}
            onVersionRestore={handleVersionRestore}
            showPreview={true}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <TemplateManager
            reportId={reportData.id}
            onTemplateApply={handleTemplateApply}
            showCreateTemplate={true}
          />
        </TabPanel>
      </Paper>

      {/* Preview Dialog */}
      <Dialog
        open={previewMode}
        onClose={() => {
          setPreviewMode(false);
          setPreviewVersion(null);
        }}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: "90vh" },
        }}
      >
        <DialogTitle>
          Report Preview
          {previewVersion && (
            <Typography variant="subtitle2" color="text.secondary">
              Version {previewVersion.version_number}
            </Typography>
          )}
        </DialogTitle>

        <DialogContent sx={{ p: 0 }}>
          <Box sx={{ height: "100%", overflow: "auto" }}>
            <ReportEditor
              reportId={reportData.id}
              initialContent={previewVersion?.content || reportData.content}
              readOnly={true}
              showVersionControls={false}
            />
          </Box>
        </DialogContent>

        <DialogActions>
          <Button
            onClick={() => {
              setPreviewMode(false);
              setPreviewVersion(null);
            }}
          >
            Close
          </Button>

          {previewVersion && (
            <Button
              variant="contained"
              onClick={async () => {
                try {
                  await enhancedReportService.rollbackToVersion(
                    reportData.id,
                    previewVersion.id
                  );
                  handleVersionRestore(previewVersion);
                  setPreviewMode(false);
                  setPreviewVersion(null);
                } catch (err) {
                  setError("Failed to restore version");
                }
              }}
            >
              Restore This Version
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Navigation Helper */}
      <Box sx={{ mt: 4, textAlign: "center" }}>
        <Button variant="text" onClick={() => navigate("/reports")}>
          ← Back to Reports
        </Button>
      </Box>
    </Container>
  );
};

export default EnhancedReportBuilder;
