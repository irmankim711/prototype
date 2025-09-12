/**
 * Document Preview Component
 * In-browser preview for DOCX, PDF, and other document formats
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  Typography,
  CircularProgress,
  Alert,
  Toolbar,
  Tooltip,
  Paper,
  Zoom,
  LinearProgress,
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  Print as PrintIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Fullscreen as FullscreenIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { reportService } from '../services/reportService';

interface DocumentPreviewProps {
  open: boolean;
  onClose: () => void;
  reportId: string | number;
  title?: string;
  onEdit?: () => void;
  onDownload?: () => void;
}

interface PreviewResponse {
  success: boolean;
  preview_url?: string;
  preview_type?: 'html' | 'pdf' | 'image' | 'data';
  preview_data?: any;
  error?: string;
}

const DocumentPreview: React.FC<DocumentPreviewProps> = ({
  open,
  onClose,
  reportId,
  title = 'Document Preview',
  onEdit,
  onDownload,
}) => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewType, setPreviewType] = useState<'html' | 'pdf' | 'image' | 'data'>('html');
  const [previewData, setPreviewData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Generate preview mutation - try both NextGen and legacy endpoints
  const previewMutation = useMutation({
    mutationFn: async (id: string | number): Promise<PreviewResponse> => {
      try {
        // First try the NextGen reports preview endpoint
        const nextgenResponse = await reportService.previewReport(String(id));
        if (nextgenResponse && nextgenResponse.success) {
          return {
            success: true,
            preview_url: `/api/v1/nextgen/reports/${id}/preview`,
            preview_type: 'html' as const,
            preview_data: nextgenResponse.preview
          };
        }
      } catch (nextgenError) {
        console.log('NextGen preview failed, trying legacy endpoint');
      }
      
      try {
        // Fallback to legacy Excel-to-DOCX preview endpoint
        const response = await axios.get(`/api/excel-to-docx/${id}/preview`);
        return response.data;
      } catch (legacyError) {
        throw new Error('Both NextGen and legacy preview endpoints failed');
      }
    },
    onSuccess: (data) => {
      if (data.success) {
        if (data.preview_data) {
          // Handle NextGen preview data
          setPreviewData(data.preview_data);
          setPreviewType('data');
        } else if (data.preview_url) {
          // Handle legacy preview URL
          setPreviewUrl(data.preview_url);
          setPreviewType(data.preview_type || 'html');
        }
        setError(null);
      } else {
        setError(data.error || 'Failed to generate preview');
      }
    },
    onError: (error: any) => {
      setError(`Preview failed: ${error.response?.data?.error || error.message}`);
    },
  });

  // Load preview when dialog opens
  useEffect(() => {
    if (open && reportId) {
      setPreviewUrl(null);
      setPreviewData(null);
      setError(null);
      setZoom(100);
      previewMutation.mutate(reportId);
    }
  }, [open, reportId]);

  const handleZoomIn = () => {
    const newZoom = Math.min(zoom + 25, 200);
    setZoom(newZoom);
    updateIframeZoom(newZoom);
  };

  const handleZoomOut = () => {
    const newZoom = Math.max(zoom - 25, 50);
    setZoom(newZoom);
    updateIframeZoom(newZoom);
  };

  const updateIframeZoom = (zoomLevel: number) => {
    if (iframeRef.current && previewType === 'html') {
      const iframeDoc = iframeRef.current.contentDocument;
      if (iframeDoc && iframeDoc.body) {
        iframeDoc.body.style.zoom = `${zoomLevel}%`;
      }
    }
  };

  const handlePrint = () => {
    if (iframeRef.current && previewType === 'html') {
      iframeRef.current.contentWindow?.print();
    } else {
      window.print();
    }
  };

  const handleFullscreen = () => {
    if (!isFullscreen && containerRef.current) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
    setIsFullscreen(!isFullscreen);
  };

  const handleRefresh = () => {
    if (reportId) {
      previewMutation.mutate(reportId);
    }
  };

  const renderPreviewContent = () => {
    if (previewMutation.isPending) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '400px',
          }}
        >
          <CircularProgress size={48} />
          <Typography variant="body2" sx={{ mt: 2 }}>
            Generating preview...
          </Typography>
          <LinearProgress sx={{ width: '100%', mt: 2 }} />
        </Box>
      );
    }

    if (error) {
      return (
        <Alert 
          severity="error" 
          sx={{ m: 2 }}
          action={
            <Button size="small" onClick={handleRefresh}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      );
    }

    if (!previewUrl && !previewData) {
      return (
        <Alert severity="info" sx={{ m: 2 }}>
          No preview available
        </Alert>
      );
    }

    // Render based on preview type
    switch (previewType) {
      case 'data':
        return (
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              {previewData?.title || 'Report Preview'}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {previewData?.description || 'Generated report details'}
            </Typography>
            
            {previewData?.files && Object.keys(previewData.files).length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Available Files:
                </Typography>
                {Object.entries(previewData.files).map(([type, fileInfo]: [string, any]) => (
                  <Paper key={type} variant="outlined" sx={{ p: 2, mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {type.toUpperCase()} File
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Size: {fileInfo.size ? `${Math.round(fileInfo.size / 1024)} KB` : 'Unknown'}
                        </Typography>
                        <Typography variant="caption" color={fileInfo.exists ? 'success.main' : 'error.main'} sx={{ ml: 1 }}>
                          {fileInfo.exists ? '✓ Available' : '✗ Missing'}
                        </Typography>
                      </Box>
                      {fileInfo.exists && onDownload && (
                        <Button 
                          size="small" 
                          startIcon={<DownloadIcon />}
                          onClick={() => onDownload()}
                        >
                          Download
                        </Button>
                      )}
                    </Box>
                  </Paper>
                ))}
              </Box>
            )}
            
            {previewData?.metadata && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Report Metadata:
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                  <pre style={{ margin: 0, fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(previewData.metadata, null, 2)}
                  </pre>
                </Paper>
              </Box>
            )}
          </Box>
        );
      case 'html':
        return (
          <Box
            sx={{
              width: '100%',
              height: '100%',
              border: '1px solid #e0e0e0',
              borderRadius: 1,
              overflow: 'hidden',
            }}
          >
            <iframe
              ref={iframeRef}
              src={`/api/excel-to-docx/preview-content/${reportId}`}
              style={{
                width: '100%',
                height: '100%',
                border: 'none',
                background: 'white',
              }}
              title="Document Preview"
              onLoad={() => updateIframeZoom(zoom)}
            />
          </Box>
        );

      case 'pdf':
        return (
          <Box
            sx={{
              width: '100%',
              height: '100%',
              border: '1px solid #e0e0e0',
              borderRadius: 1,
            }}
          >
            <embed
              src={previewUrl}
              type="application/pdf"
              width="100%"
              height="100%"
              style={{ borderRadius: 4 }}
            />
          </Box>
        );

      case 'image':
        return (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              p: 2,
            }}
          >
            <img
              src={previewUrl}
              alt="Document Preview"
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                objectFit: 'contain',
                transform: `scale(${zoom / 100})`,
              }}
            />
          </Box>
        );

      default:
        return (
          <Alert severity="warning" sx={{ m: 2 }}>
            Unsupported preview type: {previewType}
          </Alert>
        );
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          height: '90vh',
          maxHeight: '90vh',
        },
      }}
      // Fix ARIA accessibility issues
      aria-labelledby="document-preview-title"
      aria-describedby="document-preview-content"
      // Remove conflicting aria-hidden attributes
      BackdropProps={{
        sx: { backgroundColor: 'rgba(0, 0, 0, 0.5)' },
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
        <Typography 
          variant="h6" 
          component="h2" 
          sx={{ flexGrow: 1 }}
          id="document-preview-title"
        >
          {title}
        </Typography>
        <IconButton 
          onClick={onClose} 
          size="small"
          aria-label="Close document preview"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      {/* Toolbar */}
      <Paper sx={{ borderRadius: 0, borderBottom: 1, borderColor: 'divider' }}>
        <Toolbar variant="dense">
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexGrow: 1 }}>
            {previewType === 'html' && (
              <>
                <Tooltip title="Zoom Out">
                  <IconButton size="small" onClick={handleZoomOut} disabled={zoom <= 50}>
                    <ZoomOutIcon />
                  </IconButton>
                </Tooltip>
                <Typography variant="body2" sx={{ minWidth: 60, textAlign: 'center' }}>
                  {zoom}%
                </Typography>
                <Tooltip title="Zoom In">
                  <IconButton size="small" onClick={handleZoomIn} disabled={zoom >= 200}>
                    <ZoomInIcon />
                  </IconButton>
                </Tooltip>
              </>
            )}
            
            <Tooltip title="Print">
              <IconButton size="small" onClick={handlePrint}>
                <PrintIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Refresh">
              <IconButton size="small" onClick={handleRefresh}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Fullscreen">
              <IconButton size="small" onClick={handleFullscreen}>
                <FullscreenIcon />
              </IconButton>
            </Tooltip>
          </Box>

          <Box sx={{ display: 'flex', gap: 1 }}>
            {onEdit && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<EditIcon />}
                onClick={onEdit}
              >
                Edit
              </Button>
            )}
            
            {onDownload && (
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={onDownload}
              >
                Download
              </Button>
            )}
          </Box>
        </Toolbar>
      </Paper>

      {/* Preview Content */}
      <DialogContent
        ref={containerRef}
        sx={{
          p: 0,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          flexGrow: 1,
        }}
        id="document-preview-content"
        aria-describedby="document-preview-content"
      >
        {renderPreviewContent()}
      </DialogContent>
    </Dialog>
  );
};

export default DocumentPreview;