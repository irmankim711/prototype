/**
 * Report Success Modal
 * Shows after successful report generation with clear next steps
 */

import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Divider,
  Alert,
  IconButton,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  Edit as EditIcon,
  Download as DownloadIcon,
  Assessment as ReportsIcon,
  Close as CloseIcon,
  CheckCircle,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface ReportSuccessModalProps {
  open: boolean;
  onClose: () => void;
  report: {
    report_id: number | string;
    title: string;
    file_size?: number;
    metadata?: any;
  } | null;
  onView?: () => void;
  onEdit?: () => void;
  onDownload?: () => void;
}

const ReportSuccessModal: React.FC<ReportSuccessModalProps> = ({
  open,
  onClose,
  report,
  onView,
  onEdit,
  onDownload,
}) => {
  const navigate = useNavigate();

  if (!report) return null;

  const handleGoToReports = () => {
    onClose();
    navigate('/reports');
  };

  const handleViewReport = () => {
    onView?.();
    onClose();
  };

  const handleEditReport = () => {
    onEdit?.();
    onClose();
  };

  const handleDownloadReport = () => {
    onDownload?.();
    // Don't close modal for download - user might want to do more actions
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          p: 1,
        },
      }}
      // Fix ARIA issue - remove aria-hidden when dialog is open
      BackdropProps={{
        sx: { backgroundColor: 'rgba(0, 0, 0, 0.5)' },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircle color="success" sx={{ fontSize: 28 }} />
          <Typography variant="h5" component="h2" fontWeight="bold">
            Report Generated Successfully!
          </Typography>
        </Box>
        <IconButton
          onClick={onClose}
          size="small"
          sx={{ color: 'text.secondary' }}
          aria-label="Close dialog"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ pb: 2 }}>
        <Alert severity="success" sx={{ mb: 3 }}>
          <Typography variant="body1" fontWeight="medium">
            Your report "{report.title}" has been successfully generated and is ready for use.
          </Typography>
        </Alert>

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Report Details
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <Chip
              icon={<CheckCircle />}
              label="Ready"
              color="success"
              size="small"
            />
            <Chip
              label={`ID: ${report.report_id}`}
              variant="outlined"
              size="small"
            />
            {report.file_size && (
              <Chip
                label={`Size: ${(report.file_size / 1024).toFixed(1)} KB`}
                variant="outlined"
                size="small"
              />
            )}
          </Box>

          <Typography variant="body2" color="text.secondary">
            You can now view, edit, or download your report using the actions below.
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Typography variant="h6" gutterBottom>
          What would you like to do next?
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
          <Button
            variant="contained"
            startIcon={<ViewIcon />}
            onClick={handleViewReport}
            disabled={!onView}
            size="large"
            sx={{ minWidth: 140 }}
          >
            View Report
          </Button>

          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={handleEditReport}
            disabled={!onEdit}
            size="large"
            sx={{ minWidth: 140 }}
          >
            Edit Report
          </Button>

          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadReport}
            disabled={!onDownload}
            size="large"
            sx={{ minWidth: 140 }}
          >
            Download
          </Button>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3, pt: 1 }}>
        <Button
          onClick={handleGoToReports}
          startIcon={<ReportsIcon />}
          variant="text"
          color="primary"
        >
          View All Reports
        </Button>
        
        <Box sx={{ flexGrow: 1 }} />
        
        <Button
          onClick={onClose}
          variant="text"
          color="inherit"
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ReportSuccessModal;