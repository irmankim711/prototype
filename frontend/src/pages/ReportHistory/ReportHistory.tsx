import React from "react";
import { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  Grid,
  Card,
  CardContent,
  Tooltip,
  Badge,
} from "@mui/material";
import {
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
  PictureAsPdf as PdfIcon,
  Description as DocxIcon,
  TableChart as ExcelIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
} from "@mui/icons-material";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reportService } from "../../services/reportService";
import type { Report } from "../../types/reports";
import DocumentPreview from "../../components/DocumentPreview";

const getStatusColor = (
  status: string
): "success" | "warning" | "error" | "default" => {
  switch (status) {
    case "completed":
      return "success";
    case "generating":
      return "warning";
    case "pending":
      return "warning";
    case "failed":
      return "error";
    default:
      return "default";
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case "completed":
      return "✅";
    case "generating":
      return "🔄";
    case "pending":
      return "⏳";
    case "failed":
      return "❌";
    default:
      return "❓";
  }
};

export default function ReportHistory() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [storageDialogOpen, setStorageDialogOpen] = useState(false);
  const [storageUsage, setStorageUsage] = useState<any>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewReportId, setPreviewReportId] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch reports using the new reportService
  const {
    data: reportData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["reports", page, rowsPerPage],
    queryFn: async () => {
      try {
        const reports = await reportService.getAllReports();
        return {
          reports: reports.slice(page * rowsPerPage, (page + 1) * rowsPerPage),
          pagination: {
            page: page + 1,
            pages: Math.ceil(reports.length / rowsPerPage),
            per_page: rowsPerPage,
            total: reports.length,
            has_next: (page + 1) * rowsPerPage < reports.length,
            has_prev: page > 0,
          },
        };
      } catch (error) {
        console.error("Error fetching reports:", error);
        throw error;
      }
    },
    retry: 3,
  });

  // Fetch storage usage
  const {
    data: storageData,
    isLoading: storageLoading,
  } = useQuery({
    queryKey: ["storageUsage"],
    queryFn: () => reportService.getStorageUsage(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Delete report mutation
  const deleteMutation = useMutation({
    mutationFn: (reportId: string) => reportService.deleteReport(reportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      setSuccess("Report deleted successfully");
    },
    onError: (error: any) => {
      setError(`Failed to delete report: ${error.message}`);
    },
  });

  // Cleanup reports mutation
  const cleanupMutation = useMutation({
    mutationFn: (force: boolean) => reportService.cleanupReports(force),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      queryClient.invalidateQueries({ queryKey: ["storageUsage"] });
      setSuccess(`Cleanup completed: ${result.reports_processed} reports processed`);
    },
    onError: (error: any) => {
      setError(`Failed to cleanup reports: ${error.message}`);
    },
  });

  const reports = reportData?.reports || [];
  const totalReports = reportData?.pagination?.total || 0;

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handlePreviewReport = (report: Report) => {
    setSelectedReport(report);
    setIsPreviewOpen(true);
  };

  const handleClosePreview = () => {
    setSelectedReport(null);
    setIsPreviewOpen(false);
  };

  const handleDownloadReport = async (report: Report, fileType: 'pdf' | 'docx' | 'excel') => {
    try {
      const blob = await reportService.downloadReport(report.id.toString(), fileType);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = `${report.title}_${fileType}.${fileType === 'excel' ? 'xlsx' : fileType}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setSuccess(`Report downloaded as ${fileType.toUpperCase()}`);
    } catch (err: any) {
      setError(`Failed to download ${fileType.toUpperCase()}: ${err.message}`);
      console.error("Download error:", err);
    }
  };

  const handleDeleteReport = async (report: Report) => {
    if (window.confirm(`Are you sure you want to delete "${report.title}"?`)) {
      await deleteMutation.mutateAsync(report.id.toString());
    }
  };

  const handleCleanupReports = async () => {
    if (window.confirm("This will delete old reports. Continue?")) {
      await cleanupMutation.mutateAsync(false);
    }
  };

  const handleForceCleanup = async () => {
    if (window.confirm("This will force cleanup all old reports. Are you sure?")) {
      await cleanupMutation.mutateAsync(true);
    }
  };

  const handleRefresh = () => {
    refetch();
  };

  const handleViewStorage = () => {
    setStorageUsage(storageData);
    setStorageDialogOpen(true);
  };

  if (isError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load reports. Please check your connection and try again.
        </Alert>
        <Button onClick={handleRefresh} variant="contained">
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 3 }}>
        <Typography variant="h4" component="h1">
          Report History
        </Typography>
        <Box>
          <Button
            startIcon={<StorageIcon />}
            onClick={handleViewStorage}
            variant="outlined"
            sx={{ mr: 1 }}
          >
            Storage Usage
          </Button>
          <Button
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            variant="outlined"
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            onClick={handleCleanupReports}
            variant="outlined"
            color="warning"
            sx={{ mr: 1 }}
          >
            Cleanup Old Reports
          </Button>
        </Box>
      </Box>

      {/* Storage Summary Card */}
      {storageData && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Typography variant="h6" color="primary">
                  {storageData.total_reports || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Reports
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="h6" color="success.main">
                  {storageData.completed_reports || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Completed
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="h6" color="warning.main">
                  {storageData.pending_reports || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Pending
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="h6" color="error.main">
                  {storageData.failed_reports || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Failed
                </Typography>
              </Grid>
            </Grid>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Total Storage: {storageData.total_storage_mb || 0} MB
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Reports Table */}
      <Paper sx={{ width: "100%", overflow: "hidden" }}>
        <TableContainer sx={{ maxHeight: 600 }}>
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Files</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : reports.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No reports found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                reports.map((report) => (
                  <TableRow key={report.id} hover>
                    <TableCell>
                      <Chip
                        label={`${getStatusIcon(report.status)} ${report.status}`}
                        color={getStatusColor(report.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {report.title}
                      </Typography>
                      {report.description && (
                        <Typography variant="caption" color="text.secondary">
                          {report.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={report.report_type || 'custom'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(report.created_at || '').toLocaleDateString()}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(report.created_at || '').toLocaleTimeString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", gap: 0.5 }}>
                        {report.pdf_file_path && (
                          <Tooltip title="Download PDF">
                            <IconButton
                              size="small"
                              onClick={() => handleDownloadReport(report, 'pdf')}
                              color="error"
                            >
                              <PdfIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {report.docx_file_path && (
                          <Tooltip title="Download DOCX">
                            <IconButton
                              size="small"
                              onClick={() => handleDownloadReport(report, 'docx')}
                              color="primary"
                            >
                              <DocxIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                        {report.excel_file_path && (
                          <Tooltip title="Download Excel">
                            <IconButton
                              size="small"
                              onClick={() => handleDownloadReport(report, 'excel')}
                              color="success"
                            >
                              <ExcelIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: "flex", gap: 0.5 }}>
                        <Tooltip title="Preview Report">
                          <IconButton
                            size="small"
                            onClick={() => {
                              setPreviewReportId(report.id.toString());
                              setPreviewOpen(true);
                            }}
                            disabled={report.status !== 'completed'}
                          >
                            <ViewIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Report">
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteReport(report)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={totalReports}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>

      {/* Preview Dialog */}
      <Dialog
        open={isPreviewOpen}
        onClose={handleClosePreview}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Report Preview: {selectedReport?.title}
        </DialogTitle>
        <DialogContent>
          {selectedReport && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Report Details
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>Status:</strong> {selectedReport.status}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Type:</strong> {selectedReport.report_type}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Created:</strong> {new Date(selectedReport.created_at || '').toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    <strong>PDF Size:</strong> {selectedReport.pdf_file_size ? `${Math.round(selectedReport.pdf_file_size / 1024)} KB` : 'N/A'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>DOCX Size:</strong> {selectedReport.docx_file_size ? `${Math.round(selectedReport.docx_file_size / 1024)} KB` : 'N/A'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Excel Size:</strong> {selectedReport.excel_file_size ? `${Math.round(selectedReport.excel_file_size / 1024)} KB` : 'N/A'}
                  </Typography>
                </Grid>
              </Grid>
              
              {selectedReport.description && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body2">
                    {selectedReport.description}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Download Options
                </Typography>
                <Box sx={{ display: "flex", gap: 1 }}>
                  {selectedReport.pdf_file_path && (
                    <Button
                      startIcon={<PdfIcon />}
                      onClick={() => handleDownloadReport(selectedReport, 'pdf')}
                      variant="outlined"
                      color="error"
                    >
                      Download PDF
                    </Button>
                  )}
                  {selectedReport.docx_file_path && (
                    <Button
                      startIcon={<DocxIcon />}
                      onClick={() => handleDownloadReport(selectedReport, 'docx')}
                      variant="outlined"
                      color="primary"
                    >
                      Download DOCX
                    </Button>
                  )}
                  {selectedReport.excel_file_path && (
                    <Button
                      startIcon={<ExcelIcon />}
                      onClick={() => handleDownloadReport(selectedReport, 'excel')}
                      variant="outlined"
                      color="success"
                    >
                      Download Excel
                    </Button>
                  )}
                </Box>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePreview}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Storage Usage Dialog */}
      <Dialog
        open={storageDialogOpen}
        onClose={() => setStorageDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Storage Usage Details</DialogTitle>
        <DialogContent>
          {storageUsage && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    Report Statistics
                  </Typography>
                  <Typography variant="body2">
                    Total Reports: {storageUsage.total_reports}
                  </Typography>
                  <Typography variant="body2">
                    Completed: {storageUsage.completed_reports}
                  </Typography>
                  <Typography variant="body2">
                    Pending: {storageUsage.pending_reports}
                  </Typography>
                  <Typography variant="body2">
                    Failed: {storageUsage.failed_reports}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>
                    Storage Information
                  </Typography>
                  <Typography variant="body2">
                    Total Storage: {storageUsage.total_storage_mb} MB
                  </Typography>
                  <Typography variant="body2">
                    Average per Report: {storageUsage.average_storage_per_report} bytes
                  </Typography>
                  <Typography variant="body2">
                    Static Directory: {storageUsage.static_directory_size_mb} MB
                  </Typography>
                  <Typography variant="body2">
                    Temp Directory: {storageUsage.temp_directory_size_mb} MB
                  </Typography>
                </Grid>
              </Grid>
              
              {storageUsage.last_cleanup && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Cleanup Information
                  </Typography>
                  <Typography variant="body2">
                    Last Cleanup: {new Date(storageUsage.last_cleanup).toLocaleString()}
                  </Typography>
                  <Typography variant="body2">
                    Retention Policy: {storageUsage.retention_days} days
                  </Typography>
                  {storageUsage.next_cleanup_due && (
                    <Typography variant="body2">
                      Next Cleanup: {new Date(storageUsage.next_cleanup_due).toLocaleString()}
                    </Typography>
                  )}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setStorageDialogOpen(false)}>Close</Button>
          <Button onClick={handleForceCleanup} color="warning">
            Force Cleanup
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Alerts */}
      {success && (
        <Alert severity="success" sx={{ mt: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Document Preview Dialog */}
      {previewReportId && (
        <DocumentPreview
          open={previewOpen}
          onClose={() => {
            setPreviewOpen(false);
            setPreviewReportId(null);
          }}
          reportId={previewReportId}
          title="Report Preview"
          onDownload={() => {
            // Handle download if needed
          }}
        />
      )}
    </Box>
  );
}
