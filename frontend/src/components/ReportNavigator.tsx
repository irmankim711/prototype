/**
 * Report Navigator
 * Helper component to navigate to specific reports and show recent reports
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Alert,
  Divider,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Download as DownloadIcon,
  Assessment as ReportsIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { reportService } from '../services/reportService';
import { useNavigate } from 'react-router-dom';

interface ReportNavigatorProps {
  onReportSelect?: (report: any) => void;
  onViewReport?: (reportId: string) => void;
  onEditReport?: (reportId: string) => void;
  onDownloadReport?: (reportId: string) => void;
  maxRecentReports?: number;
}

const ReportNavigator: React.FC<ReportNavigatorProps> = ({
  onReportSelect,
  onViewReport,
  onEditReport,
  onDownloadReport,
  maxRecentReports = 5,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  // Fetch recent reports
  const {
    data: reports,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportService.getAllReports(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const recentReports = reports?.slice(0, maxRecentReports) || [];
  const filteredReports = recentReports.filter((report: any) =>
    report.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.id?.toString().includes(searchTerm)
  );

  const handleReportClick = (report: any) => {
    onReportSelect?.(report);
  };

  const handleViewReport = (reportId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    onViewReport?.(reportId);
  };

  const handleEditReport = (reportId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    onEditReport?.(reportId);
  };

  const handleDownloadReport = (reportId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    onDownloadReport?.(reportId);
  };

  const handleGoToReports = () => {
    navigate('/reports');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'generating':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <HistoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Recent Reports
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Loading recent reports...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom color="error">
            <HistoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Recent Reports
          </Typography>
          <Alert severity="error" sx={{ mt: 1 }}>
            Failed to load reports. Please try again later.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <HistoryIcon sx={{ mr: 1 }} />
            Recent Reports ({recentReports.length})
          </Typography>
          <Button
            size="small"
            startIcon={<ReportsIcon />}
            onClick={handleGoToReports}
            variant="outlined"
          >
            View All
          </Button>
        </Box>

        {recentReports.length > 0 && (
          <>
            {/* Search Field */}
            <TextField
              fullWidth
              size="small"
              placeholder="Search reports by name or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ mb: 2 }}
            />

            <Divider sx={{ mb: 2 }} />

            {filteredReports.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                {searchTerm ? 'No reports match your search.' : 'No reports found.'}
              </Typography>
            ) : (
              <List dense>
                {filteredReports.map((report: any) => (
                  <ListItem
                    key={report.id}
                    button
                    onClick={() => handleReportClick(report)}
                    sx={{
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1,
                      '&:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle2" noWrap>
                            {report.title || `Report ${report.id}`}
                          </Typography>
                          <Chip
                            label={report.status || 'completed'}
                            color={getStatusColor(report.status || 'completed') as any}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            ID: {report.id} • Created: {new Date(report.createdAt || report.created_at || Date.now()).toLocaleDateString()}
                          </Typography>
                          {report.formTitle && (
                            <Typography variant="caption" color="text.secondary">
                              Form: {report.formTitle}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {onViewReport && (
                          <IconButton
                            size="small"
                            onClick={(e) => handleViewReport(report.id.toString(), e)}
                            title="View Report"
                          >
                            <ViewIcon />
                          </IconButton>
                        )}
                        {onEditReport && (
                          <IconButton
                            size="small"
                            onClick={(e) => handleEditReport(report.id.toString(), e)}
                            title="Edit Report"
                          >
                            <EditIcon />
                          </IconButton>
                        )}
                        {onDownloadReport && (
                          <IconButton
                            size="small"
                            onClick={(e) => handleDownloadReport(report.id.toString(), e)}
                            title="Download Report"
                          >
                            <DownloadIcon />
                          </IconButton>
                        )}
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </>
        )}

        {recentReports.length === 0 && (
          <Alert severity="info">
            <Typography variant="body2">
              No reports available. Generate your first report by uploading an Excel file!
            </Typography>
            <Button
              size="small"
              onClick={handleGoToReports}
              sx={{ mt: 1 }}
              variant="outlined"
            >
              Go to Reports Page
            </Button>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default ReportNavigator;