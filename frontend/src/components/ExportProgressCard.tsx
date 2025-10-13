/**
 * Export Progress Card Component
 * Shows real-time progress for Excel export generation
 */

import React from "react";
import {
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Box,
  Chip,
  IconButton,
  Collapse,
  Alert,
} from "@mui/material";
import {
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
} from "@mui/icons-material";
import { formatDateTime } from "../utils/formatters";
import type { ExcelExport } from "../services/formPipelineApi";

interface ExportProgressCardProps {
  export: ExcelExport;
  onDownload?: (exportId: number) => void;
  showExpanded?: boolean;
  onToggleExpanded?: () => void;
}

export const ExportProgressCard: React.FC<ExportProgressCardProps> = ({
  export: exportData,
  onDownload,
  showExpanded = false,
  onToggleExpanded,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "error";
      case "processing":
        return "warning";
      case "pending":
        return "info";
      default:
        return "default";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircleIcon />;
      case "failed":
        return <ErrorIcon />;
      case "processing":
      case "pending":
        return <ScheduleIcon />;
      default:
        return <ScheduleIcon />;
    }
  };

  const handleDownload = () => {
    if (onDownload && exportData.export_status === "completed") {
      onDownload(exportData.id);
    }
  };

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            mb: 2,
          }}
        >
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" component="div" gutterBottom>
              {exportData.name}
            </Typography>

            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
              <Chip
                size="small"
                label={exportData.export_status}
                color={
                  getStatusColor(exportData.export_status) as
                    | "success"
                    | "error"
                    | "warning"
                    | "info"
                    | "default"
                }
                icon={getStatusIcon(exportData.export_status)}
              />

              {exportData.is_auto_generated && (
                <Chip
                  size="small"
                  label="Auto-Generated"
                  variant="outlined"
                  color="info"
                />
              )}
            </Box>

            <Typography variant="body2" color="text.secondary">
              Created: {formatDateTime(exportData.created_at)}
            </Typography>

            {exportData.completed_at && (
              <Typography variant="body2" color="text.secondary">
                Completed: {formatDateTime(exportData.completed_at)}
              </Typography>
            )}
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {exportData.export_status === "completed" &&
              exportData.file_name && (
                <IconButton
                  color="primary"
                  onClick={handleDownload}
                  title="Download Excel file"
                >
                  <DownloadIcon />
                </IconButton>
              )}

            {onToggleExpanded && (
              <IconButton
                onClick={onToggleExpanded}
                sx={{
                  transform: showExpanded ? "rotate(180deg)" : "rotate(0deg)",
                  transition: "transform 0.2s",
                }}
              >
                <ExpandMoreIcon />
              </IconButton>
            )}
          </Box>
        </Box>

        {/* Progress Bar for Processing */}
        {exportData.export_status === "processing" && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress
              variant={
                exportData.export_progress ? "determinate" : "indeterminate"
              }
              value={exportData.export_progress || 0}
            />
            {exportData.export_progress && (
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 0.5 }}
              >
                {exportData.export_progress}% complete
              </Typography>
            )}
          </Box>
        )}

        {/* Error Message */}
        {exportData.export_status === "failed" && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Export Failed:</strong> Check logs for details
            </Typography>
          </Alert>
        )}

        {/* Expanded Details */}
        <Collapse in={showExpanded}>
          <Box sx={{ pt: 2, borderTop: "1px solid", borderColor: "divider" }}>
            {exportData.description && (
              <Typography variant="body2" color="text.secondary" paragraph>
                {exportData.description}
              </Typography>
            )}

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: 2,
              }}
            >
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Submissions
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {exportData.processed_submissions} of{" "}
                  {exportData.total_submissions} processed
                </Typography>
              </Box>

              {exportData.started_at && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Started
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {formatDateTime(exportData.started_at)}
                  </Typography>
                </Box>
              )}

              {exportData.file_size && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    File Size
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {(exportData.file_size / 1024 / 1024).toFixed(2)} MB
                  </Typography>
                </Box>
              )}

              {exportData.export_duration && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Duration
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {exportData.export_duration} seconds
                  </Typography>
                </Box>
              )}
            </Box>

            {exportData.error_count > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Processing Errors
                </Typography>
                <Alert severity="warning">
                  {exportData.error_count} submission
                  {exportData.error_count !== 1 ? "s" : ""} had processing
                  errors
                </Alert>
              </Box>
            )}
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};
