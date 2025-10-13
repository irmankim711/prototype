import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Immediate Report Preview Component
 * Shows generated report content immediately after generation with download options
 */

import { useState, useEffect, useRef } from "react";

import { Dialog, DialogTitle, DialogContent, DialogActions, Box, Typography, Button, IconButton, Alert, CircularProgress, Menu, MenuItem, ListItemIcon, ListItemText, Chip, Tooltip, Paper, Divider, Slide, Zoom } from "@mui/material";

import { Close, Fullscreen, FullscreenExit, Download, Share, Print, Refresh, Save, Edit, PictureAsPdf, Description, TableView, ZoomIn, ZoomOut, FitScreen } from "@mui/icons-material";

export const Transition = React.forwardRef(function Transition(
  props: React.ComponentProps<typeof Slide> & {
    children: React.ReactElement<any, any>;
  },
  ref: React.Ref<any>,
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

interface ImmediateReportPreviewProps {
  open: boolean;
  onClose: () => void;
  reportContent: {
    type: 'pdf' | 'docx' | 'excel';
    data: Blob;
    filename: string;
  } | null;
  isLoading?: boolean;
  error?: string | null;
}

export default function ImmediateReportPreview({
  open,
  onClose,
  reportContent,
  isLoading = false,
  error = null,
}: ImmediateReportPreviewProps) {
  const [fullscreen, setFullscreen] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const previewRef = useRef<HTMLDivElement>(null);

  const handleDownload = () => {
    if (reportContent) {
      const url = URL.createObjectURL(reportContent.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = reportContent.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  };

  const handlePrint = () => {
    if (reportContent?.type === 'pdf') {
      const url = URL.createObjectURL(reportContent.data);
      const iframe = document.createElement('iframe');
      iframe.src = url;
      iframe.style.display = 'none';
      document.body.appendChild(iframe);
      iframe.onload = () => {
        iframe.contentWindow?.print();
      };
    }
  };

  const handleShare = async () => {
    if (navigator.share && reportContent) {
      try {
        const file = new File([reportContent.data], reportContent.filename, {
          type: reportContent.data.type,
        });

        await navigator.share({
          title: 'Generated Report',
          text: 'Generated report from Automated Report Platform',
          files: [file],
        });
      } catch (err) {
        console.error('Error sharing:', err);
      }
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 25, 200));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 25, 50));
  };

  const handleFitScreen = () => {
    setZoomLevel(100);
  };

  const getFileIcon = () => {
    if (!reportContent) return null;

    switch (reportContent.type) {
      case 'pdf':
        return <PictureAsPdf color="error" />;
      case 'docx':
        return <Description color="primary" />;
      case 'excel':
        return <TableView color="success" />;
      default:
        return <Description />;
    }
  };

  const getFileTypeChip = () => {
    if (!reportContent) return null;

    const chipProps = {
      pdf: { label: 'PDF', color: 'error' as const },
      docx: { label: 'DOCX', color: 'primary' as const },
      excel: { label: 'XLSX', color: 'success' as const },
    };

    const props = chipProps[reportContent.type];
    return <Chip size="small" variant="outlined" {...props} />;
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth={fullscreen ? false : 'lg'}
      fullWidth={!fullscreen}
      fullScreen={fullscreen}
      TransitionComponent={Transition}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            {getFileIcon()}
            <Typography variant="h6" component="div">
              Report Preview
            </Typography>
            {getFileTypeChip()}
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <Tooltip title="Zoom Out">
              <IconButton
                onClick={handleZoomOut}
                disabled={zoomLevel <= 50}
                size="small"
              >
                <ZoomOut />
              </IconButton>
            </Tooltip>
            <Typography variant="body2" sx={{ minWidth: 60, textAlign: 'center' }}>
              {zoomLevel}%
            </Typography>
            <Tooltip title="Zoom In">
              <IconButton
                onClick={handleZoomIn}
                disabled={zoomLevel >= 200}
                size="small"
              >
                <ZoomIn />
              </IconButton>
            </Tooltip>
            <Tooltip title="Fit Screen">
              <IconButton onClick={handleFitScreen} size="small">
                <FitScreen />
              </IconButton>
            </Tooltip>
            <Tooltip title={fullscreen ? "Exit Fullscreen" : "Fullscreen"}>
              <IconButton
                onClick={() => setFullscreen(!fullscreen)}
                size="small"
              >
                {fullscreen ? <FullscreenExit /> : <Fullscreen />}
              </IconButton>
            </Tooltip>
            <IconButton onClick={onClose} size="small">
              <Close />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0, minHeight: 400 }}>
        {isLoading ? (
          <Box
            display="flex"
            flexDirection="column"
            alignItems="center"
            justifyContent="center"
            minHeight={400}
            gap={2}
          >
            <CircularProgress size={60} />
            <Typography variant="h6">Generating Report...</Typography>
            <Typography variant="body2" color="textSecondary">
              This may take a few moments
            </Typography>
          </Box>
        ) : error ? (
          <Box p={3}>
            <Alert severity="error">
              <Typography variant="h6">Error Loading Report</Typography>
              <Typography variant="body2">{error}</Typography>
            </Alert>
          </Box>
        ) : reportContent ? (
          <Box
            ref={previewRef}
            sx={{
              height: fullscreen ? 'calc(100vh - 140px)' : 500,
              overflow: 'auto',
              backgroundColor: '#f5f5f5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 2,
            }}
          >
            <Paper
              elevation={3}
              sx={{
                transform: `scale(${zoomLevel / 100})`,
                transformOrigin: 'center center',
                transition: 'transform 0.2s ease',
                maxWidth: '100%',
                maxHeight: '100%',
              }}
            >
              {reportContent.type === 'pdf' ? (
                <embed
                  src={URL.createObjectURL(reportContent.data)}
                  type="application/pdf"
                  width="800"
                  height="600"
                  style={{ border: 'none' }}
                />
              ) : (
                <Box
                  sx={{
                    width: 800,
                    height: 600,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'white',
                    border: '1px solid #ddd',
                    gap: 2,
                  }}
                >
                  {getFileIcon()}
                  <Typography variant="h6">
                    {reportContent.filename}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    {reportContent.type.toUpperCase()} files cannot be previewed directly.
                    Please download to view the content.
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Download />}
                    onClick={handleDownload}
                  >
                    Download File
                  </Button>
                </Box>
              )}
            </Paper>
          </Box>
        ) : (
          <Box
            display="flex"
            alignItems="center"
            justifyContent="center"
            minHeight={400}
          >
            <Typography variant="h6" color="textSecondary">
              No report content available
            </Typography>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Box display="flex" alignItems="center" gap={1} flexGrow={1}>
          {reportContent && (
            <Typography variant="body2" color="textSecondary">
              File: {reportContent.filename} ({(reportContent.data.size / 1024).toFixed(1)} KB)
            </Typography>
          )}
        </Box>
        <Button
          onClick={handleMenuOpen}
          disabled={!reportContent}
          startIcon={<Share />}
        >
          Actions
        </Button>
        <Button
          onClick={handleDownload}
          disabled={!reportContent}
          variant="contained"
          startIcon={<Download />}
        >
          Download
        </Button>
      </DialogActions>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleDownload} disabled={!reportContent}>
          <ListItemIcon>
            <Download fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download</ListItemText>
        </MenuItem>
        <MenuItem onClick={handlePrint} disabled={!reportContent || reportContent.type !== 'pdf'}>
          <ListItemIcon>
            <Print fontSize="small" />
          </ListItemIcon>
          <ListItemText>Print</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleShare} disabled={!reportContent || !navigator.share}>
          <ListItemIcon>
            <Share fontSize="small" />
          </ListItemIcon>
          <ListItemText>Share</ListItemText>
        </MenuItem>
      </Menu>
    </Dialog>
  );
}