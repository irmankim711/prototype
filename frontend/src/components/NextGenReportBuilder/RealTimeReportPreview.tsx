import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Real-Time Report Preview Component
 * Shows live preview of generated reports with automatic updates
 */

import { useState, useEffect } from "react";
  
import { Dialog, DialogTitle, DialogContent, DialogActions, Box, Typography, Button, IconButton, Alert, CircularProgress, Chip, Menu, MenuItem, ListItemIcon, ListItemText, Tooltip } from "@mui/material";
  
import { Close, Fullscreen, Download, Share, Refresh, Visibility, Print, PictureAsPdf, TableView, Description, MoreVert } from "@mui/icons-material";

import { nextGenReportService } from "../../services/nextGenReportService";

import { reportService } from "../../services/reportService";

import ReportErrorBoundary from './ReportErrorBoundary';

interface RealTimeReportPreviewProps {
  open: boolean;
  
onClose: () => void;
  
reportId?: string;
  
report?: any;
  
title?: string;
  
onEdit?: () => void;
  
onDownload?: (format: 'pdf' | 'docx' | 'excel') => void;
  
onShare?: () => void;
  
autoRefresh?: boolean;
  
refreshInterval?: number;
}

const RealTimeReportPreview: React.FC<RealTimeReportPreviewProps> = ({
  open,
  onClose,
  reportId,
  report,
  title = 'Report Preview',
  onEdit,
  onDownload,
  onShare,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}) => {
  // State
  const [loading, setLoading] = useState(false);
  
const [error, setError] = useState<string | null>(null);
  
const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  
const [reportData, setReportData] = useState(report);
  
const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
const [fullscreen, setFullscreen] = useState(false);
  
const [downloadMenuAnchor, setDownloadMenuAnchor] = useState<HTMLElement | null>(null);

  // Get the actual report ID from various sources
  const actualReportId = reportId || report?.id || report?.reportId || report?.report_id;

  // Load report preview
  const loadPreview = React.useCallback(async () => {
    if (!actualReportId) return;

try {
      setLoading(true);
      
setError(null);

console.log('🔄 Loading preview for report:', actualReportId);

      // Try to get preview URL from backend
      const previewResponse = await nextGenReportService.getReportPreview(actualReportId);

if (previewResponse?.previewUrl || previewResponse?.preview_url) {
        setPreviewUrl(previewResponse.previewUrl || previewResponse.preview_url);
      } else {
        // Fallback: try to construct preview URL
        setPreviewUrl(`/api/reports/${actualReportId}/preview`);
      }

      // Update report data if available
      if (previewResponse?.report) {
        setReportData(previewResponse.report);
      }

      setLastUpdated(new Date());
      
console.log('✅ Preview loaded successfully');

    } catch (error: any) {
      console.error('❌ Failed to load preview:', error);
      
setError(error.message || 'Failed to load report preview');
    } finally {
      setLoading(false);
    }
  }, [actualReportId]);

  // Auto-refresh effect
  useEffect(() => {
    if (open && actualReportId) {
      loadPreview();

if (autoRefresh && refreshInterval > 0) {
        const interval = setInterval(() => {
          loadPreview();
        }, refreshInterval);

return () => clearInterval(interval);
      }
    }
  }, [open, actualReportId, autoRefresh, refreshInterval, loadPreview]);

  // Subscribe to real-time updates
  useEffect(() => {
    const handleReportUpdate = (updatedReport: React.ChangeEvent<HTMLInputElement>) => {
      if (updatedReport.id === actualReportId || 
          updatedReport.reportId === actualReportId || 
          updatedReport.report_id === actualReportId) {
        console.log('📈 Real-time report update received:', updatedReport);
        
setReportData(updatedReport);
        
loadPreview();
      }
    };

nextGenReportService.onReportGenerated(handleReportUpdate);

return () => {
      nextGenReportService.offReportGenerated(handleReportUpdate);
    };
  }, [actualReportId, loadPreview]);

  // Handle download
  const handleDownload = async (format: 'pdf' | 'docx' | 'excel') => {
    try {
      if (onDownload) {
        onDownload(format);
      } else if (actualReportId) {
        setLoading(true);
        
const blob = await reportService.downloadReport(actualReportId, format);
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        
const a = document.createElement('a');
        
a.style.display = 'none';
        
a.href = url;
        
a.download = `${reportData?.title || 'report'}.${format === 'excel' ? 'xlsx' : format}`;
        
document.body.appendChild(a);
        
a.click();
        
window.URL.revokeObjectURL(url);
        
document.body.removeChild(a);

console.log(`✅ Downloaded report as ${format.toUpperCase()}`);
      }
    } catch (error: any) {
      console.error(`❌ Download failed:`, error);
      
setError(`Download failed: ${error.message}`);
    } finally {
      setLoading(false);
      
setDownloadMenuAnchor(null);
    }
  };

if (!actualReportId && !report) {
    return null;
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullscreen}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          height: fullscreen ? '100vh' : '90vh',
          maxHeight: fullscreen ? '100vh' : '90vh',
        },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 1,
        }}
      >
        <Box>
          <Typography variant="h6">{title}</Typography>
          {lastUpdated && (
            <Typography variant="caption" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
        </Box>

        <Box display="flex" alignItems="center" gap={1}>
          {/* Report Status */}
          {reportData?.status && (
            <Chip
              label={reportData.status}
              size="small"
              color={
                reportData.status === 'completed' ? 'success' :
                reportData.status === 'processing' ? 'warning' : 'default'
              }
            />
          )}

          {/* Auto-refresh indicator */}
          {autoRefresh && (
            <Tooltip title="Auto-refreshing every 30 seconds">
              <CircularProgress size={16} />
            </Tooltip>
          )}

          {/* Action buttons */}
          <Tooltip title="Refresh">
            <IconButton size="small" onClick={loadPreview} disabled={loading}>
              <Refresh />
            </IconButton>
          </Tooltip>

          <Tooltip title="Fullscreen">
            <IconButton size="small" onClick={() => setFullscreen(!fullscreen)}>
              <Fullscreen />
            </IconButton>
          </Tooltip>

          <Tooltip title="Download">
            <IconButton
              size="small"
              onClick={(e: any) => setDownloadMenuAnchor(e.currentTarget)}
            >
              <Download />
            </IconButton>
          </Tooltip>

          {onShare && (
            <Tooltip title="Share">
              <IconButton size="small" onClick={onShare}>
                <Share />
              </IconButton>
            </Tooltip>
          )}

          <IconButton size="small" onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0, overflow: 'hidden' }}>
        <ReportErrorBoundary
          onRetry={loadPreview}
          onError={(error: any) => setError(error.message)}
        >
          {loading && !previewUrl && (
            <Box
              display="flex"
              alignItems="center"
              justifyContent="center"
              height="100%"
              flexDirection="column"
              gap={2}
            >
              <CircularProgress size={48} />
              <Typography variant="h6" color="text.secondary">
                Loading Report Preview...
              </Typography>
            </Box>
          )}

          {error && (
            <Box p={3}>
              <Alert 
                severity="error" 
                action={
                  <Button size="small" onClick={loadPreview}>
                    Retry
                  </Button>
                }
              >
                {error}
              </Alert>
            </Box>
          )}

          {previewUrl && !error && (
            <Box sx={{ width: '100%', height: '100%', position: 'relative' }}>
              {loading && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    zIndex: 1000,
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: 2,
                  }}
                >
                  <Alert severity="info" sx={{ alignItems: 'center' }}>
                    <CircularProgress size={16} sx={{ mr: 1 }} />
                    Refreshing preview...
                  </Alert>
                </Box>
              )}
              
              <iframe
                src={previewUrl}
                title="Report Preview"
                width="100%"
                height="100%"
                frameBorder={0}
                style={{ border: 0 }}
                onLoad={() => setLoading(false)}
                onError={() => setError('Failed to load preview')}
              />
            </Box>
          )}
        </ReportErrorBoundary>
      </DialogContent>

      {(onEdit || reportData) && (
        <DialogActions>
          {onEdit && (
            <Button onClick={onEdit} startIcon={<Visibility />}>
              Edit Report
            </Button>
          )}
          
          <Button onClick={onClose}>
            Close
          </Button>
        </DialogActions>
      )}

      {/* Download Menu */}
      <Menu
        anchorEl={downloadMenuAnchor}
        open={Boolean(downloadMenuAnchor)}
        onClose={() => setDownloadMenuAnchor(null)}
      >
        <MenuItem onClick={() => handleDownload('pdf')}>
          <ListItemIcon>
            <PictureAsPdf />
          </ListItemIcon>
          <ListItemText primary="Download as PDF" />
        </MenuItem>
        
        <MenuItem onClick={() => handleDownload('docx')}>
          <ListItemIcon>
            <Description />
          </ListItemIcon>
          <ListItemText primary="Download as DOCX" />
        </MenuItem>
        
        <MenuItem onClick={() => handleDownload('excel')}>
          <ListItemIcon>
            <TableView />
          </ListItemIcon>
          <ListItemText primary="Download as Excel" />
        </MenuItem>
      </Menu>
    </Dialog>
  );
};

export default RealTimeReportPreview;
