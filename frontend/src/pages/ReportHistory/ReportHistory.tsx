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
} from "@mui/material";
import {
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";
import { useQuery } from "@tanstack/react-query";
import {
  fetchReportsHistory,
  downloadReport,
  type Report,
} from "../../services/api";

const getStatusColor = (
  status: string
): "success" | "warning" | "error" | "default" => {
  switch (status) {
    case "completed":
      return "success";
    case "processing":
      return "warning";
    case "failed":
      return "error";
    default:
      return "default";
  }
};

export default function ReportHistory() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    data: reportData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["reportHistory", page + 1, rowsPerPage],
    queryFn: () => fetchReportsHistory(page + 1, rowsPerPage),
    retry: 3,
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

  const handleDownloadReport = async (report: Report) => {
    if (report.outputUrl) {
      try {
        await downloadReport(report.outputUrl, `${report.title}.docx`);
      } catch (err) {
        setError("Failed to download report");
        console.error("Download error:", err);
      }
    }
  };

  if (isLoading) {
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

  if (isError) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load report history. Please try again later.
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Report History
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Report Name</TableCell>
                <TableCell>Template</TableCell>
                <TableCell>Created Date</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell>{report.title}</TableCell>
                  <TableCell>{report.templateId}</TableCell>
                  <TableCell>
                    {new Date(report.createdAt).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={report.status}
                      color={getStatusColor(report.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      disabled={
                        report.status !== "completed" || !report.outputUrl
                      }
                      onClick={() => handleDownloadReport(report)}
                    >
                      <DownloadIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handlePreviewReport(report)}
                    >
                      <ViewIcon />
                    </IconButton>
                    <IconButton size="small" color="error">
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
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

      <Dialog
        open={isPreviewOpen}
        onClose={handleClosePreview}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{selectedReport?.title}</DialogTitle>
        <DialogContent dividers>
          {selectedReport?.status === "completed" ? (
            <Box
              component="iframe"
              src={selectedReport.outputUrl}
              sx={{
                width: "100%",
                height: "500px",
                border: "none",
              }}
              title="Report Preview"
            />
          ) : (
            <Box p={3} textAlign="center">
              <Typography color="textSecondary">
                Preview not available. Report status: {selectedReport?.status}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePreview}>Close</Button>
          {selectedReport?.status === "completed" && (
            <Button
              variant="contained"
              onClick={() =>
                selectedReport && handleDownloadReport(selectedReport)
              }
              startIcon={<DownloadIcon />}
            >
              Download
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}
