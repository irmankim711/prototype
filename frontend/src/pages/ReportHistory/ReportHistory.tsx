import { useState } from 'react';
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
} from '@mui/material';
import {
  Download as DownloadIcon,
  Visibility as ViewIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import type { Report } from '../../services/api';

// Mock function - replace with actual API call
const fetchReportHistory = async (): Promise<Report[]> => {
  const response = await fetch('/api/reports/history');
  return response.json();
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'processing':
      return 'warning';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

export default function ReportHistory() {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const { data: reports, isLoading } = useQuery({
    queryKey: ['reportHistory'],
    queryFn: fetchReportHistory,
  });

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
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

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Report History
      </Typography>

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
              {reports
                ?.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((report) => (
                  <TableRow key={report.id}>
                    <TableCell>{report.title}</TableCell>
                    <TableCell>
                      {report.templateId}
                    </TableCell>
                    <TableCell>
                      {new Date(report.createdAt).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={report.status}
                        color={getStatusColor(report.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        disabled={report.status !== 'completed'}
                        component="a"
                        href={report.outputUrl || '#'}
                        target="_blank"
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
          count={reports?.length || 0}
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
        <DialogTitle>
          {selectedReport?.title}
        </DialogTitle>
        <DialogContent dividers>
          {selectedReport?.status === 'completed' ? (
            <iframe
              src={selectedReport.outputUrl}
              style={{ width: '100%', height: '500px', border: 'none' }}
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
          {selectedReport?.status === 'completed' && (
            <Button
              variant="contained"
              component="a"
              href={selectedReport.outputUrl || '#'}
              target="_blank"
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
