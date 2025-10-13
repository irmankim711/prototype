/**
 * Form Data Pipeline Dashboard Component
 * Manages data sources, exports, and real-time updates
 */

import React, { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  LinearProgress,
  Tooltip,
  Badge,
} from "@mui/material";
import {
  Add as AddIcon,
  Download as DownloadIcon,
  Sync as SyncIcon,
  CloudDownload as CloudDownloadIcon,
  Assessment as AssessmentIcon,
  Storage as StorageIcon,
  Schedule as ScheduleIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
} from "@mui/icons-material";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSocket } from "../hooks/useSocket";
import { formPipelineApi } from "../services/formPipelineApi";
import { formatDateTime } from "../utils/formatters";
import { CreateDataSourceDialog } from "./CreateDataSourceDialog";
import { CreateExportDialog } from "./CreateExportDialog";
import { ExportProgressCard } from "./ExportProgressCard";

interface DataSource {
  id: number;
  name: string;
  source_type: string;
  source_id: string;
  source_url?: string;
  is_active: boolean;
  auto_sync: boolean;
  sync_interval: number;
  last_sync?: string;
  created_at: string;
  submission_count: number;
}

interface ExcelExport {
  id: number;
  name: string;
  description?: string;
  export_status: string;
  export_progress: number;
  file_name?: string;
  file_size?: number;
  total_submissions: number;
  processed_submissions: number;
  error_count: number;
  started_at?: string;
  completed_at?: string;
  export_duration?: number;
  created_at: string;
  is_auto_generated: boolean;
  auto_schedule?: string;
  next_auto_export?: string;
}

interface AnalyticsSummary {
  total_data_sources: number;
  total_submissions: number;
  recent_submissions: number;
  active_exports: number;
  last_sync?: string;
  data_sources: DataSource[];
}

export const FormPipelineDashboard: React.FC = () => {
  const [createDataSourceOpen, setCreateDataSourceOpen] = useState(false);
  const [createExportOpen, setCreateExportOpen] = useState(false);

  const queryClient = useQueryClient();
  const socket = useSocket();

  // Fetch analytics summary
  const { data: analytics, isLoading: analyticsLoading } =
    useQuery<AnalyticsSummary>({
      queryKey: ["form-pipeline-analytics"],
      queryFn: formPipelineApi.getAnalyticsSummary,
      refetchInterval: 30000, // Refresh every 30 seconds
    });

  // Fetch data sources
  const { data: dataSourcesData, isLoading: dataSourcesLoading } = useQuery({
    queryKey: ["form-data-sources"],
    queryFn: () => formPipelineApi.getDataSources(),
    refetchInterval: 30000,
  });

  // Fetch exports
  const { data: exportsData, isLoading: exportsLoading } = useQuery({
    queryKey: ["excel-exports"],
    queryFn: () => formPipelineApi.getExcelExports(),
    refetchInterval: 10000, // More frequent for export status updates
  });

  // Manual sync mutation
  const syncMutation = useMutation({
    mutationFn: (dataSourceId: number) =>
      formPipelineApi.manualSync(dataSourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["form-data-sources"] });
      queryClient.invalidateQueries({ queryKey: ["form-pipeline-analytics"] });
    },
  });

  // Download export mutation
  const downloadMutation = useMutation({
    mutationFn: (exportId: number) => formPipelineApi.downloadExport(exportId),
    onSuccess: (blob: Blob, exportId: number) => {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `export_${exportId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    },
  });

  // Socket event handlers
  useEffect(() => {
    if (!socket.socket) return;

    // Subscribe to dashboard updates
    socket.socket.emit("subscribe_dashboard", { user_id: "current_user" });

    // Handle sync updates
    socket.socket.on(
      "sync_update",
      (data: { source_id: number; status: string; message?: string }) => {
        console.log("Sync update received:", data);
        queryClient.invalidateQueries({ queryKey: ["form-data-sources"] });
        queryClient.invalidateQueries({
          queryKey: ["form-pipeline-analytics"],
        });
      }
    );

    // Handle export updates
    socket.socket.on(
      "export_update",
      (data: { export_id: number; status: string; progress?: number }) => {
        console.log("Export update received:", data);
        queryClient.invalidateQueries({ queryKey: ["excel-exports"] });
      }
    );

    // Handle new submissions
    socket.socket.on(
      "new_submission",
      (data: { source_id: number; submission_count: number }) => {
        console.log("New submission received:", data);
        queryClient.invalidateQueries({
          queryKey: ["form-pipeline-analytics"],
        });
      }
    );

    return () => {
      if (socket.socket) {
        socket.socket.off("sync_update");
        socket.socket.off("export_update");
        socket.socket.off("new_submission");
      }
    };
  }, [socket.socket, queryClient]);

  const handleManualSync = (dataSourceId: number) => {
    syncMutation.mutate(dataSourceId);
  };

  const handleDownloadExport = (exportId: number) => {
    downloadMutation.mutate(exportId);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "processing":
        return "warning";
      case "error":
        return "error";
      case "pending":
        return "info";
      default:
        return "default";
    }
  };

  const getSourceTypeIcon = (sourceType: string) => {
    switch (sourceType) {
      case "google_forms":
        return "📋";
      case "microsoft_forms":
        return "📊";
      case "zoho_forms":
        return "📄";
      case "typeform":
        return "📝";
      case "custom":
        return "⚙️";
      default:
        return "📁";
    }
  };

  if (analyticsLoading) {
    return <LinearProgress />;
  }

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Form Data Pipeline
      </Typography>

      {/* Analytics Summary Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Data Sources
                  </Typography>
                  <Typography variant="h4">
                    {analytics?.total_data_sources || 0}
                  </Typography>
                </Box>
                <StorageIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Submissions
                  </Typography>
                  <Typography variant="h4">
                    {analytics?.total_submissions || 0}
                  </Typography>
                </Box>
                <AssessmentIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Recent (24h)
                  </Typography>
                  <Typography variant="h4">
                    <Badge
                      badgeContent="new"
                      color="error"
                      invisible={!analytics?.recent_submissions}
                    >
                      {analytics?.recent_submissions || 0}
                    </Badge>
                  </Typography>
                </Box>
                <ScheduleIcon color="secondary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                alignItems="center"
                justifyContent="space-between"
              >
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Exports
                  </Typography>
                  <Typography variant="h4">
                    {analytics?.active_exports || 0}
                  </Typography>
                </Box>
                <CloudDownloadIcon color="info" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Last Sync Info */}
      {analytics?.last_sync && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Last synchronization: {formatDateTime(analytics.last_sync)}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Data Sources Section */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                mb={2}
              >
                <Typography variant="h6">Data Sources</Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => setCreateDataSourceOpen(true)}
                >
                  Add Source
                </Button>
              </Box>

              {dataSourcesLoading ? (
                <LinearProgress />
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Submissions</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {dataSourcesData?.data_sources?.map(
                        (source: DataSource) => (
                          <TableRow key={source.id}>
                            <TableCell>
                              <Box display="flex" alignItems="center">
                                <Box sx={{ mr: 1 }}>
                                  {getSourceTypeIcon(source.source_type)}
                                </Box>
                                <Box>
                                  <Typography variant="body2" fontWeight="bold">
                                    {source.name}
                                  </Typography>
                                  <Typography
                                    variant="caption"
                                    color="textSecondary"
                                  >
                                    {source.source_id}
                                  </Typography>
                                </Box>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={source.source_type.replace("_", " ")}
                                size="small"
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <Box display="flex" alignItems="center">
                                {source.is_active ? (
                                  <CheckCircleIcon
                                    color="success"
                                    fontSize="small"
                                  />
                                ) : (
                                  <ErrorIcon color="error" fontSize="small" />
                                )}
                                <Typography variant="caption" ml={1}>
                                  {source.auto_sync ? "Auto" : "Manual"}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {source.submission_count}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Tooltip title="Manual Sync">
                                <IconButton
                                  size="small"
                                  onClick={() => handleManualSync(source.id)}
                                  disabled={syncMutation.isPending}
                                >
                                  <SyncIcon />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        )
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Excel Exports Section */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                mb={2}
              >
                <Typography variant="h6">Excel Exports</Typography>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={() => setCreateExportOpen(true)}
                  disabled={!dataSourcesData?.data_sources?.length}
                >
                  Create Export
                </Button>
              </Box>

              {exportsLoading ? (
                <LinearProgress />
              ) : (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Progress</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {exportsData?.exports?.map((exportItem: ExcelExport) => (
                        <TableRow key={exportItem.id}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="bold">
                                {exportItem.name}
                              </Typography>
                              <Typography
                                variant="caption"
                                color="textSecondary"
                              >
                                {exportItem.total_submissions} submissions
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={exportItem.export_status}
                              size="small"
                              color={getStatusColor(exportItem.export_status)}
                            />
                          </TableCell>
                          <TableCell>
                            <Box display="flex" alignItems="center">
                              <LinearProgress
                                variant="determinate"
                                value={exportItem.export_progress}
                                sx={{ width: 60, mr: 1 }}
                              />
                              <Typography variant="caption">
                                {exportItem.export_progress}%
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            {exportItem.export_status === "completed" && (
                              <Tooltip title="Download Excel File">
                                <IconButton
                                  size="small"
                                  onClick={() =>
                                    handleDownloadExport(exportItem.id)
                                  }
                                  disabled={downloadMutation.isPending}
                                >
                                  <DownloadIcon />
                                </IconButton>
                              </Tooltip>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Active Export Progress Cards */}
      {exportsData?.exports?.filter(
        (exp: ExcelExport) => exp.export_status === "processing"
      ).length > 0 && (
        <Box mt={3}>
          <Typography variant="h6" gutterBottom>
            Active Exports
          </Typography>
          <Grid container spacing={2}>
            {exportsData.exports
              .filter((exp: ExcelExport) => exp.export_status === "processing")
              .map((exportItem: ExcelExport) => (
                <Grid item xs={12} md={6} key={exportItem.id}>
                  <ExportProgressCard export={exportItem} />
                </Grid>
              ))}
          </Grid>
        </Box>
      )}

      {/* Dialogs */}
      <CreateDataSourceDialog
        open={createDataSourceOpen}
        onClose={() => setCreateDataSourceOpen(false)}
        onSuccess={() => {
          setCreateDataSourceOpen(false);
          queryClient.invalidateQueries({ queryKey: ["form-data-sources"] });
          queryClient.invalidateQueries({
            queryKey: ["form-pipeline-analytics"],
          });
        }}
      />

      <CreateExportDialog
        open={createExportOpen}
        onClose={() => setCreateExportOpen(false)}
        dataSources={dataSourcesData?.data_sources || []}
        onSuccess={() => {
          setCreateExportOpen(false);
          queryClient.invalidateQueries({ queryKey: ["excel-exports"] });
        }}
      />
    </Box>
  );
};
