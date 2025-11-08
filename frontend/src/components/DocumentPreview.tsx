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
  Button,
  IconButton,
  Typography,
  CircularProgress,
  Alert,
  Toolbar,
  Tooltip,
  Paper,
  LinearProgress,
  TextField,
  Stack,
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
  Save as SaveIcon,
  Cancel as CancelIcon,
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
  const [isEditMode, setIsEditMode] = useState(false);
  const [editableContent, setEditableContent] = useState<any>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Generate preview mutation - try both NextGen and legacy endpoints
  const previewMutation = useMutation({
    mutationFn: async (id: string | number): Promise<PreviewResponse> => {
      try {
        // First try the NextGen reports preview endpoint
        const nextgenResponse = await reportService.previewReport(String(id));
        if (nextgenResponse && nextgenResponse.success) {
          // Check if we have actual file paths for PDF/DOCX
          const preview = nextgenResponse.preview;
          if (preview?.files?.pdf?.exists || preview?.files?.docx?.exists) {
            // We have actual files - return PDF preview type with download URL
            const pdfUrl = preview.files.pdf?.exists
              ? `/api/v1/nextgen/reports/${id}/download/pdf`
              : preview.files.docx?.exists
              ? `/api/v1/nextgen/reports/${id}/download/docx`
              : null;

            return {
              success: true,
              preview_url: pdfUrl || '',
              preview_type: 'pdf' as const,
              preview_data: preview
            };
          }

          // Fallback to data preview
          return {
            success: true,
            preview_url: `/api/v1/nextgen/reports/${id}/preview`,
            preview_type: 'data' as const,
            preview_data: preview
          };
        }
      } catch (nextgenError) {
        console.log('NextGen preview failed, trying legacy endpoint');
      }

      try {
        // Fallback to Excel-to-PDF preview endpoint
        const response = await axios.get(`/api/excel-to-pdf/preview/${id}`);
        return response.data;
      } catch (legacyError) {
        throw new Error('Both NextGen and legacy preview endpoints failed');
      }
    },
    onSuccess: (data) => {
      if (data.success) {
        if (data.preview_url) {
          // Handle preview URL first (PDF/DOCX files)
          setPreviewUrl(data.preview_url);
          setPreviewType(data.preview_type || 'html');
          setPreviewData(data.preview_data); // Still store data for metadata
        } else if (data.preview_data) {
          // Fallback: Handle NextGen preview data without URL
          setPreviewData(data.preview_data);
          setPreviewType('data');
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

  const handleEditToggle = () => {
    if (!isEditMode) {
      // Entering edit mode - load editable content
      const sampleEditableContent = {
        title: "LAPORAN PROGRAM TITLE",
        location: "LOCATION",
        tarikh: "TARIKH",
        time: "9:00 AM - 5:00 PM",
        resources: "PERUNDING MUBARAK RESOURCES",
        lokasi: "LOKASI",
        location2: "LOCATION",
        anjuran: "ANJURAN",
        organizer: "ORGANIZER",
        content: "ISI KANDUNGAN",
        course: "LAPORAN KURSUS FIQH USRAH DAERAH KUALA SELANGOR",
        objectives: "Setelah mengikuti modul,peserta akan:",
        evaluation: "*Rujuk lampiran A: Borang Penilaian Peserta (BPK-11/JPIE)",
        improvements: "CADANGAN UNTUK PENAMBAHBAIKAN KESELURUHAN PROGRAM",
        discussions: "CADANGAN PERUNDING"
      };
      setEditableContent(sampleEditableContent);
    }
    setIsEditMode(!isEditMode);
  };

  const handleSaveChanges = () => {
    // Save the changes and exit edit mode
    console.log('Saving changes:', editableContent);
    setIsEditMode(false);
    // TODO: Send changes to backend
    if (onEdit) {
      onEdit(); // Notify parent component
    }
  };

  const handleCancelEdit = () => {
    setIsEditMode(false);
    setEditableContent(null);
  };

  const handleContentChange = (field: string, value: string) => {
    setEditableContent((prev: any) => ({
      ...prev,
      [field]: value
    }));
  };

  // Render inline editable content based on the report structure
  const renderEditableContent = () => {
    if (!editableContent) return null;

    return (
      <Box sx={{ p: 3, maxWidth: '800px', margin: '0 auto' }}>
        <Stack spacing={3}>
          {/* Main Title */}
          <TextField
            label="Program Title"
            value={editableContent.title || ''}
            onChange={(e) => handleContentChange('title', e.target.value)}
            fullWidth
            variant="outlined"
            sx={{
              '& .MuiInputBase-input': {
                fontSize: '1.5rem',
                fontWeight: 'bold',
                textAlign: 'center'
              }
            }}
          />

          {/* Location */}
          <TextField
            label="Location"
            value={editableContent.location || ''}
            onChange={(e) => handleContentChange('location', e.target.value)}
            fullWidth
            variant="outlined"
          />

          {/* Date */}
          <TextField
            label="Tarikh (Date)"
            value={editableContent.tarikh || ''}
            onChange={(e) => handleContentChange('tarikh', e.target.value)}
            fullWidth
            variant="outlined"
          />

          {/* Time */}
          <TextField
            label="Time"
            value={editableContent.time || ''}
            onChange={(e) => handleContentChange('time', e.target.value)}
            fullWidth
            variant="outlined"
            sx={{
              '& .MuiInputBase-root': {
                backgroundColor: '#f57c00',
                color: 'white'
              }
            }}
          />

          {/* Resources */}
          <TextField
            label="Resources"
            value={editableContent.resources || ''}
            onChange={(e) => handleContentChange('resources', e.target.value)}
            fullWidth
            variant="outlined"
          />

          {/* Lokasi */}
          <TextField
            label="Lokasi"
            value={editableContent.lokasi || ''}
            onChange={(e) => handleContentChange('lokasi', e.target.value)}
            fullWidth
            variant="outlined"
          />

          {/* Anjuran */}
          <TextField
            label="Anjuran"
            value={editableContent.anjuran || ''}
            onChange={(e) => handleContentChange('anjuran', e.target.value)}
            fullWidth
            variant="outlined"
          />

          {/* Organizer */}
          <TextField
            label="Organizer"
            value={editableContent.organizer || ''}
            onChange={(e) => handleContentChange('organizer', e.target.value)}
            fullWidth
            variant="outlined"
          />

          {/* Course Content */}
          <TextField
            label="Course Content"
            value={editableContent.course || ''}
            onChange={(e) => handleContentChange('course', e.target.value)}
            fullWidth
            variant="outlined"
            multiline
            rows={2}
          />

          {/* Objectives */}
          <TextField
            label="Objektif Kursus"
            value={editableContent.objectives || ''}
            onChange={(e) => handleContentChange('objectives', e.target.value)}
            fullWidth
            variant="outlined"
            multiline
            rows={3}
          />

          {/* Evaluation */}
          <TextField
            label="Penilaian Program"
            value={editableContent.evaluation || ''}
            onChange={(e) => handleContentChange('evaluation', e.target.value)}
            fullWidth
            variant="outlined"
            multiline
            rows={2}
          />

          {/* Improvements */}
          <TextField
            label="Cadangan Penambahbaikan"
            value={editableContent.improvements || ''}
            onChange={(e) => handleContentChange('improvements', e.target.value)}
            fullWidth
            variant="outlined"
            multiline
            rows={3}
          />

          {/* Discussions */}
          <TextField
            label="Cadangan Perunding"
            value={editableContent.discussions || ''}
            onChange={(e) => handleContentChange('discussions', e.target.value)}
            fullWidth
            variant="outlined"
            multiline
            rows={3}
          />
        </Stack>
      </Box>
    );
  };

  const renderPreviewContent = () => {
    // If in edit mode, show editable content
    if (isEditMode) {
      return renderEditableContent();
    }

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
              src={`/api/excel-to-pdf/preview-content/${reportId}`}
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
              src={previewUrl || undefined}
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
              src={previewUrl || ''}
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
          flexGrow: 1
        }}
        id="document-preview-title"
      >
        {title}
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
            {isEditMode ? (
              <>
                <Button
                  variant="contained"
                  size="small"
                  color="primary"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveChanges}
                >
                  Save
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<CancelIcon />}
                  onClick={handleCancelEdit}
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                {onEdit && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<EditIcon />}
                    onClick={handleEditToggle}
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
              </>
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