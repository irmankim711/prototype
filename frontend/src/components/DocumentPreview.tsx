/**
 * Document Preview Component
 * In-browser preview for DOCX, PDF, and other document formats
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Dialog,
  Button,
  IconButton,
  Typography,
  CircularProgress,
  Alert,
  Toolbar,
  Tooltip,
  Paper,
  LinearProgress,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
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
  PictureAsPdf as PdfIcon,
  Description as DocxIcon,
  TableChart as ExcelIcon,
} from '@mui/icons-material';
import InlineReportEditor from './NextGenReportBuilder/InlineReportEditor';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import axiosInstance from '../services/axiosInstance';

interface DocumentPreviewProps {
  open: boolean;
  onClose: () => void;
  reportId: string | number;
  title?: string;
  onEdit?: () => void;
  onDownload?: (fileType: 'pdf' | 'docx' | 'excel') => void;
  // Used when preview endpoint returns 404 but we still have a file URL
  fallbackDownloadUrl?: string | null;
  // Report object to check available file types
  // Report object to check available file types
  report?: any;
  // Display variant
  variant?: 'dialog' | 'pane';
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
  fallbackDownloadUrl = null,
  report = null,
  variant = 'dialog',
}) => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewType, setPreviewType] = useState<'html' | 'pdf' | 'image' | 'data'>('html');
  const [previewData, setPreviewData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [editableContent, setEditableContent] = useState<any>(null);
  const [downloadMenuAnchor, setDownloadMenuAnchor] = useState<null | HTMLElement>(null);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Helper to make absolute URL for embedding in Office viewer
  const toAbsoluteUrl = (url: string): string => {
    try {
      const u = new URL(url, window.location.origin);
      return u.toString();
    } catch {
      return `${window.location.origin}${url.startsWith('/') ? '' : '/'}${url}`;
    }
  };

  // Helper to build Office Web Viewer URL for DOCX
  const buildOfficeViewerUrl = (fileUrl: string): string =>
    `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(toAbsoluteUrl(fileUrl))}`;

  // Generate preview mutation - try both NextGen and legacy endpoints
  const previewMutation = useMutation({
    mutationFn: async (id: string | number): Promise<PreviewResponse> => {
      console.log('🔍 Loading preview for report ID:', id);
      
      try {
        // First try the NextGen reports preview endpoint
        console.log('📡 Trying NextGen preview endpoint...');
        const nextgenResponse = await axiosInstance.get(`/api/v1/nextgen/reports/${id}/preview`);
        console.log('✅ NextGen preview response:', nextgenResponse.data);
        
        if (nextgenResponse.data && nextgenResponse.data.success) {
          // Check if we have actual file paths for PDF/DOCX
          const preview = nextgenResponse.data.preview || nextgenResponse.data;
          
          console.log('📄 Preview data:', preview);
          console.log('📄 Preview files:', preview?.files);
          
          // Check for existing files
          if (preview?.files) {
            if (preview.files.pdf?.exists) {
              const pdfUrl = `/api/v1/nextgen/reports/${id}/download/pdf`;
              console.log('✅ PDF file exists, using URL:', pdfUrl);
              return {
                success: true,
                preview_url: pdfUrl,
                preview_type: 'pdf' as const,
                preview_data: preview
              };
            }
            
            if (preview.files.docx?.exists) {
              // For DOCX, use Office Web Viewer for embedding
              console.log('✅ DOCX file exists - using Office Web Viewer');
              const docxUrl = `/api/v1/nextgen/reports/${id}/download/docx`;
              return {
                success: true,
                preview_url: buildOfficeViewerUrl(docxUrl),
                preview_type: 'html' as const,
                preview_data: preview
              };
            }
          }
          
          // Fallback to data preview with report information
          console.log('📊 Using data preview mode');
          return {
            success: true,
            preview_type: 'data' as const,
            preview_data: preview
          };
        }
      } catch (nextgenError: any) {
        console.warn('⚠️ NextGen preview failed:', nextgenError.response?.status, nextgenError.message);
        console.log('🔄 Trying legacy endpoint...');
      }

      try {
        // Fallback to reports API preview endpoint
        console.log('📡 Trying reports API preview endpoint...');
        const response = await axiosInstance.get(`/api/reports/${id}/preview`);
        console.log('✅ Reports API preview response:', response.data);
        
        if (response.data && response.data.success) {
          const preview = response.data.preview_data || response.data.preview || response.data;

          console.log('📄 Legacy preview data:', preview);
          console.log('📄 Legacy preview files:', preview?.files);

          // Check if we have actual file paths for PDF/DOCX (same logic as NextGen)
          if (preview?.files) {
            // Prioritize PDF over DOCX since Office Web Viewer has accessibility issues
            if (preview.files.pdf?.exists) {
              const pdfUrl = preview.files.pdf.download_url || `/api/reports/${id}/download/pdf`;
              console.log('✅ PDF file exists, using URL:', pdfUrl);
              return {
                success: true,
                preview_url: pdfUrl,
                preview_type: 'pdf' as const,
                preview_data: preview
              };
            }

            if (preview.files.docx?.exists) {
              // DOCX preview has issues with Office Web Viewer requiring public URLs
              // For now, show data preview with download option
              console.log('⚠️ DOCX file exists but Office Web Viewer requires publicly accessible URLs');
              console.log('📊 Showing data preview instead with download option');
              // Don't set preview_url, let it fall through to data preview
            }
          }

          // Fallback to data preview if no files or explicit preview_url provided
          const result: PreviewResponse = {
            success: true,
            preview_type: (response.data.preview_type || 'data') as 'html' | 'pdf' | 'image' | 'data',
            preview_data: preview
          };
          if (response.data.preview_url) {
            result.preview_url = response.data.preview_url;
          }
          return result;
        }
      } catch (legacyError: any) {
        console.warn('⚠️ Reports API preview failed:', legacyError.response?.status, legacyError.message);
      }

      try {
        // Final fallback to Excel-to-PDF preview endpoint
        console.log('📡 Trying Excel-to-PDF preview endpoint...');
        const response = await axios.get(`/api/excel-to-pdf/preview/${id}`);
        console.log('✅ Excel-to-PDF preview response:', response.data);

        // Check if response is HTML instead of JSON (routing issue)
        if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
          console.error('❌ Excel-to-PDF endpoint returned HTML instead of JSON - route not found');
          throw new Error('Preview endpoint not available');
        }

        return response.data;
      } catch (finalError: any) {
        console.error('❌ All preview endpoints failed');
        console.error('❌ Final error:', finalError.response?.status, finalError.message);
        throw new Error(`Preview failed: ${finalError.response?.data?.error || finalError.message || 'All preview endpoints failed'}`);
      }
    },
    onSuccess: (data) => {
      console.log('✅ Preview mutation succeeded:', data);

      // Validate that data is an object and not HTML string
      if (typeof data !== 'object' || data === null) {
        console.error('❌ Invalid preview response - expected object, got:', typeof data);
        setError('Invalid preview response from server');
        return;
      }

      if (data.success) {
        if (data.preview_url) {
          // Handle preview URL first (PDF/DOCX files)
          console.log('📄 Setting preview URL:', data.preview_url);
          setPreviewUrl(data.preview_url);
          setPreviewType(data.preview_type || 'html');
          setPreviewData(data.preview_data); // Still store data for metadata
        } else if (data.preview_data) {
          // Fallback: Handle NextGen preview data without URL
          console.log('📊 Setting preview data (no URL)');
          console.log('📊 Preview data content:', data.preview_data);
          console.log('📊 Preview data files:', data.preview_data?.files);
          console.log('📊 Preview data metadata:', data.preview_data?.metadata);
          setPreviewData(data.preview_data);
          setPreviewType('data');

          // AUTO-ENABLE EDIT MODE for data previews
          console.log('📝 Auto-enabling edit mode for data preview');
          setIsEditMode(true);
          
          // Populate editable content immediately
          let contentToEdit: any = {};
          const pData = data.preview_data;
          
          if (pData) {
            if (pData.metadata) {
              contentToEdit = { ...pData.metadata };
            } else if (pData.data_source) {
              contentToEdit = typeof pData.data_source === 'string' 
                ? JSON.parse(pData.data_source) 
                : pData.data_source;
            } else if (pData.generated_data) {
              contentToEdit = pData.generated_data;
            }
          }
          
          // If no content found, use sample structure (same as handleEditToggle)
          if (Object.keys(contentToEdit).length === 0) {
            console.log('⚠️ No editable content found, using sample structure');
            contentToEdit = {
              title: pData?.title || "LAPORAN PROGRAM TITLE",
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
          }
          
          console.log('📝 Auto-loaded editable content:', contentToEdit);
          setEditableContent(contentToEdit);
        }
        setError(null);
      } else {
        const errorMsg = data.error || 'Failed to generate preview';
        console.error('❌ Preview failed:', errorMsg);
        setError(errorMsg);
      }
    },
    onError: (error: any) => {
      const errorMsg = error.response?.data?.error || error.message || 'Failed to load preview';
      console.error('❌ Preview mutation error:', errorMsg);
      console.error('❌ Error details:', error);
      // If the report is not found by ID but we have a fallback file URL, use that
      const status = error?.response?.status || error?.response?.data?.code;
      if ((status === 404 || error?.response?.data?.code === 'NOT_FOUND') && fallbackDownloadUrl) {
        console.warn('⚠️ Preview 404; falling back to provided download URL:', fallbackDownloadUrl);
        setError(null);
        setPreviewData({ fallback: true, url: fallbackDownloadUrl });
        // Infer preview type from extension; DOCX cannot be embedded reliably, show as data
        if (/\.(pdf)(\?|$)/i.test(fallbackDownloadUrl)) {
          setPreviewType('pdf');
          setPreviewUrl(fallbackDownloadUrl);
        } else if (/\.(docx)(\?|$)/i.test(fallbackDownloadUrl)) {
          // Use Office viewer for DOCX
          setPreviewType('html');
          setPreviewUrl(buildOfficeViewerUrl(fallbackDownloadUrl));
        } else {
          setPreviewType('data');
          setPreviewUrl(fallbackDownloadUrl);
        }
        return;
      }
      setError(errorMsg);
    },
  });

  // Load preview when dialog opens
  useEffect(() => {
    if (open && (reportId !== null && reportId !== undefined)) {
      console.log('🔄 DocumentPreview: Dialog opened, loading preview for report ID:', reportId);
      setPreviewUrl(null);
      setPreviewData(null);
      setError(null);
      setZoom(100);
      setIsEditMode(false);
      setEditableContent(null);
      
      // If ID is 0 or synthetic 'file:' and we have fallback URL, bypass API and render directly
      const idString = String(reportId);
      if ((reportId === 0 || idString.startsWith('file:')) && fallbackDownloadUrl) {
        console.log('⚡ Bypassing preview API, using fallback file URL directly:', fallbackDownloadUrl);
        const url = fallbackDownloadUrl;
        setError(null);
        setPreviewData({ fallback: true, url });
        if (/\.(pdf)(\?|$)/i.test(url)) {
          setPreviewType('pdf');
          setPreviewUrl(url);
        } else if (/\.(docx)(\?|$)/i.test(url)) {
          setPreviewType('html');
          setPreviewUrl(buildOfficeViewerUrl(url));
        } else {
          setPreviewType('data');
          setPreviewUrl(url);
        }
        return;
      }

      // If reportId is 0 but no fallback URL, show error
      if (reportId === 0 && !fallbackDownloadUrl) {
        console.warn('⚠️ Report ID is 0 but no fallback URL provided');
        setError('Report not saved yet. Please save the report first before previewing.');
        return;
      }

      // Small delay to ensure dialog is fully rendered
      const loadPreview = () => {
        console.log('📡 Triggering preview mutation for report ID:', reportId);
        previewMutation.mutate(reportId);
      };
      
      // Use setTimeout to ensure state is ready
      const timer = setTimeout(loadPreview, 100);
      return () => clearTimeout(timer);
    } else if (!open) {
      // Reset state when dialog closes
      setPreviewUrl(null);
      setPreviewData(null);
      setError(null);
      setIsEditMode(false);
      setEditableContent(null);
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
      // Entering edit mode - load editable content from report data
      console.log('📝 Entering edit mode for report ID:', reportId);
      console.log('📝 Current preview data:', previewData);
      
      // Try to extract editable content from preview data
      let contentToEdit: any = {};
      
      if (previewData) {
        // Try to get data from metadata or data_source
        if (previewData.metadata) {
          contentToEdit = { ...previewData.metadata };
        } else if (previewData.data_source) {
          contentToEdit = typeof previewData.data_source === 'string' 
            ? JSON.parse(previewData.data_source) 
            : previewData.data_source;
        } else if (previewData.generated_data) {
          contentToEdit = previewData.generated_data;
        }
      }
      
      // If no content found, use sample structure
      if (Object.keys(contentToEdit).length === 0) {
        console.log('⚠️ No editable content found, using sample structure');
        contentToEdit = {
          title: previewData?.title || "LAPORAN PROGRAM TITLE",
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
      }
      
      console.log('📝 Editable content loaded:', contentToEdit);
      setEditableContent(contentToEdit);
    }
    setIsEditMode(!isEditMode);
  };

  const handleSaveChanges = async (contentToSave?: string) => {
    if (!editableContent || !reportId) {
      console.error('❌ Cannot save: missing content or report ID');
      return;
    }

    try {
      console.log('💾 Saving changes for report ID:', reportId);
      console.log('💾 Changes to save:', editableContent);
      
      setIsEditMode(false);
      
      // Use passed content or fallback to state
      const finalContent = contentToSave || (typeof editableContent === 'string' ? editableContent : editableContent?.content);
      
      // Try to update report via NextGen API first
      try {
        const updateResponse = await axiosInstance.put(`/api/v1/nextgen/reports/${reportId}`, {
          title: previewData?.title || 'Untitled Report',
          description: previewData?.description,
          generated_data: {
            ...((typeof editableContent === 'object' ? editableContent : {})),
            content: finalContent // Ensure content is updated
          },
          data_source: {
            ...((typeof editableContent === 'object' ? editableContent : {})),
            content: finalContent
          }
        });
        
        console.log('✅ Report updated successfully:', updateResponse.data);
        
        // Refresh preview after update
        if (open && reportId) {
          setTimeout(() => {
            previewMutation.mutate(reportId);
          }, 500);
        }
        
        if (onEdit) {
          onEdit(); // Notify parent component
        }
      } catch (nextgenError: any) {
        console.warn('⚠️ NextGen update failed, trying reports API:', nextgenError);
        
        // Fallback to reports API
        try {
          const updateResponse = await axiosInstance.put(`/api/reports/${reportId}/edit`, {
            title: editableContent.title || previewData?.title,
            description: editableContent.description || previewData?.description,
            data_source: editableContent,
            generation_config: previewData?.generation_config || {}
          });
          
          console.log('✅ Report updated via reports API:', updateResponse.data);
          
          // Refresh preview after update
          if (open && reportId) {
            setTimeout(() => {
              previewMutation.mutate(reportId);
            }, 500);
          }
          
          if (onEdit) {
            onEdit();
          }
        } catch (reportsError: any) {
          console.error('❌ Both update endpoints failed:', reportsError);
          setError(`Failed to save changes: ${reportsError.response?.data?.error || reportsError.message}`);
          setIsEditMode(true); // Stay in edit mode on error
        }
      }
    } catch (error: any) {
      console.error('❌ Error saving changes:', error);
      setError(`Failed to save changes: ${error.message}`);
      setIsEditMode(true); // Stay in edit mode on error
    }
  };

  const handleCancelEdit = () => {
    setIsEditMode(false);
    setEditableContent(null);
  };



  const handleDownloadMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setDownloadMenuAnchor(event.currentTarget);
  };

  const handleDownloadMenuClose = () => {
    setDownloadMenuAnchor(null);
  };

  const handleDownloadFile = (fileType: 'pdf' | 'docx' | 'excel') => {
    if (onDownload) {
      onDownload(fileType);
    }
    handleDownloadMenuClose();
  };

  // Check which file types are available
  const getAvailableFileTypes = () => {
    const available: Array<'pdf' | 'docx' | 'excel'> = [];

    // Check from report prop first
    if (report) {
      if (report.pdf_file_path) available.push('pdf');
      if (report.docx_file_path) available.push('docx');
      if (report.excel_file_path) available.push('excel');
    }

    // Fallback to preview data
    if (previewData?.files) {
      if (previewData.files.pdf?.exists && !available.includes('pdf')) available.push('pdf');
      if (previewData.files.docx?.exists && !available.includes('docx')) available.push('docx');
      if (previewData.files.excel?.exists && !available.includes('excel')) available.push('excel');
    }

    return available;
  };

  // Transform flat data to editor content
  const transformDataToEditorContent = (data: any) => {
    let htmlContent = '';
    
    // Helper to add section
    const addSection = (title: string, content: string) => {
      if (content) {
        htmlContent += `<h2>${title}</h2><p>${content}</p>`;
      }
    };

    // Known fields mapping for specific order/formatting
    const knownFields = ['title', 'location', 'tarikh', 'time', 'organizer', 'anjuran', 'objectives', 'course', 'content', 'evaluation', 'improvements', 'discussions', 'records', 'fields'];

    // Build HTML content from known fields first
    if (data.location) htmlContent += `<p><strong>Location:</strong> ${data.location}</p>`;
    if (data.tarikh) htmlContent += `<p><strong>Tarikh:</strong> ${data.tarikh}</p>`;
    if (data.time) htmlContent += `<p><strong>Masa:</strong> ${data.time}</p>`;
    if (data.organizer || data.anjuran) htmlContent += `<p><strong>Anjuran:</strong> ${data.organizer || data.anjuran}</p>`;
    
    if (htmlContent) htmlContent += '<hr/>';
    
    addSection('Objektif Kursus', data.objectives);
    addSection('Kandungan Kursus', data.course || data.content);
    addSection('Penilaian Program', data.evaluation);
    addSection('Cadangan Penambahbaikan', data.improvements);
    addSection('Cadangan Perunding', data.discussions);

    // Handle Data Records (e.g. from Excel)
    if (data.records && Array.isArray(data.records) && data.records.length > 0) {
      htmlContent += '<h2>Data Records</h2>';
      htmlContent += '<div style="overflow-x: auto;">';
      htmlContent += '<table border="1" style="width:100%; border-collapse: collapse; margin-top: 10px;">';
      
      // Header
      const headers = Object.keys(data.records[0] || {});
      htmlContent += '<thead><tr>';
      headers.forEach(h => htmlContent += `<th style="padding: 8px; background: #f0f0f0; text-align: left;">${h}</th>`);
      htmlContent += '</tr></thead>';
      
      // Body
      htmlContent += '<tbody>';
      data.records.slice(0, 50).forEach((row: any) => { // Limit to 50 rows for performance
        htmlContent += '<tr>';
        headers.forEach(h => htmlContent += `<td style="padding: 8px;">${row[h]}</td>`);
        htmlContent += '</tr>';
      });
      htmlContent += '</tbody></table>';
      htmlContent += '</div>';
      
      if (data.records.length > 50) {
        htmlContent += `<p><em>...and ${data.records.length - 50} more records</em></p>`;
      }
    }

    // Handle any other generic fields not explicitly mapped
    const otherKeys = Object.keys(data).filter(key => 
      !knownFields.includes(key) && 
      key !== 'id' && 
      key !== 'metadata' &&
      key !== 'generated_data' && // Avoid duplication if flattened
      key !== 'data_source'
    );
    
    if (otherKeys.length > 0) {
      htmlContent += '<hr/><h3>Other Details</h3>';
      otherKeys.forEach(key => {
        const value = data[key];
        // Format key to Title Case
        const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        
        if (Array.isArray(value)) {
          // Handle Arrays
          htmlContent += `<p><strong>${label}:</strong> (${value.length} items)</p>`;
          if (value.length > 0) {
            // Check if it's an array of objects (table) or primitives (list)
            if (typeof value[0] === 'object' && value[0] !== null) {
              // Render as table
              htmlContent += '<div style="overflow-x: auto; margin-bottom: 10px;">';
              htmlContent += '<table border="1" style="width:100%; border-collapse: collapse;">';
              const headers = Object.keys(value[0]);
              htmlContent += '<thead><tr>';
              headers.forEach(h => htmlContent += `<th style="padding: 5px; background: #f0f0f0;">${h}</th>`);
              htmlContent += '</tr></thead><tbody>';
              value.slice(0, 20).forEach((row: any) => {
                htmlContent += '<tr>';
                headers.forEach(h => {
                  const cellVal = typeof row[h] === 'object' ? JSON.stringify(row[h]) : row[h];
                  htmlContent += `<td style="padding: 5px;">${cellVal}</td>`;
                });
                htmlContent += '</tr>';
              });
              htmlContent += '</tbody></table>';
              if (value.length > 20) htmlContent += `<p><em>...and ${value.length - 20} more items</em></p>`;
              htmlContent += '</div>';
            } else {
              // Render as list
              htmlContent += '<ul>';
              value.forEach((item: any) => htmlContent += `<li>${item}</li>`);
              htmlContent += '</ul>';
            }
          }
        } else if (typeof value === 'object' && value !== null) {
          // Handle Objects
          htmlContent += `<p><strong>${label}:</strong></p>`;
          htmlContent += `<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">${JSON.stringify(value, null, 2)}</pre>`;
        } else {
          // Handle Primitives
          htmlContent += `<p><strong>${label}:</strong> ${value}</p>`;
        }
      });
    }

    // If htmlContent is still empty, just dump the JSON
    if (!htmlContent) {
       htmlContent = `<h3>Raw Data</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
    }

    return {
      title: data.title || 'Untitled Report',
      content: htmlContent,
      sections: []
    };
  };

  // Render inline editable content using InlineReportEditor
  const renderEditableContent = () => {
    if (!editableContent) return null;

    // Prepare content string for the editor
    let editorContentString = '';
    
    if (typeof editableContent === 'string') {
      editorContentString = editableContent;
    } else if (editableContent.content && typeof editableContent.content === 'string') {
      // If it's already an object with content property (from transformDataToEditorContent)
      editorContentString = editableContent.content;
    } else {
      // Transform data object to HTML string
      const transformed = transformDataToEditorContent(editableContent);
      editorContentString = transformed.content;
    }

    return (
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
        <InlineReportEditor
          reportId={typeof reportId === 'number' ? reportId : Number(reportId) || 0}
          reportContent={editorContentString}
          onSave={(content) => {
            console.log('💾 Inline Editor saved:', content);
            // Update local state
            setEditableContent((prev: any) => {
              if (typeof prev === 'object') {
                return { ...prev, content: content };
              }
              return { content: content };
            });
            
            // Trigger save to backend
            handleSaveChanges(content);
          }}
          onCancel={() => setIsEditMode(false)}
          readOnly={false}
          showAITools={true}
          autoSave={true}
        />
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
      console.log('❌ No preview available - previewUrl:', previewUrl, 'previewData:', previewData, 'previewType:', previewType);
      return (
        <Alert severity="info" sx={{ m: 2 }}>
          No preview available
        </Alert>
      );
    }

    console.log('🎨 Rendering preview - Type:', previewType, 'URL:', previewUrl, 'HasData:', !!previewData);

    // Render based on preview type
    switch (previewType) {
      case 'data':
        console.log('📝 Rendering data preview for:', previewData);
        console.log('📝 Title:', previewData?.title);
        console.log('📝 Description:', previewData?.description);
        console.log('📝 Files:', previewData?.files);
        console.log('📝 Has files:', previewData?.files && Object.keys(previewData.files).length > 0);

        return (
          <Box sx={{ p: 3, width: '100%', height: '100%', overflow: 'auto', bgcolor: 'background.paper' }}>
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
                {Object.entries(previewData.files).map(([type, fileInfo]: [string, any]) => {
                  const fileType = type.toLowerCase() as 'pdf' | 'docx' | 'excel';
                  const FileIcon = fileType === 'pdf' ? PdfIcon : fileType === 'docx' ? DocxIcon : ExcelIcon;
                  const iconColor = fileType === 'pdf' ? 'error' : fileType === 'docx' ? 'primary' : 'success';

                  return (
                    <Paper key={type} variant="outlined" sx={{ p: 2, mb: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <FileIcon fontSize="medium" color={iconColor} />
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
                        </Box>
                        {fileInfo.exists && onDownload && (
                          <Button
                            size="small"
                            variant="contained"
                            color={iconColor}
                            startIcon={<DownloadIcon />}
                            onClick={() => onDownload(fileType)}
                          >
                            Download
                          </Button>
                        )}
                      </Box>
                    </Paper>
                  );
                })}
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
              src={previewUrl || `/api/excel-to-pdf/preview-content/${reportId}`}
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

  const content = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: 'background.paper' }}>
      {/* Toolbar */}
      <Toolbar
        variant="dense"
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'grey.50',
          justifyContent: 'space-between',
        }}
      >
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="subtitle1" component="div" noWrap sx={{ maxWidth: 300 }}>
            {title}
          </Typography>
          {previewType === 'html' && (
            <Box display="flex" alignItems="center" bgcolor="white" borderRadius={1} border={1} borderColor="divider" ml={2}>
              <IconButton size="small" onClick={handleZoomOut} disabled={zoom <= 50}>
                <ZoomOutIcon fontSize="small" />
              </IconButton>
              <Typography variant="caption" sx={{ minWidth: 40, textAlign: 'center' }}>
                {zoom}%
              </Typography>
              <IconButton size="small" onClick={handleZoomIn} disabled={zoom >= 200}>
                <ZoomInIcon fontSize="small" />
              </IconButton>
            </Box>
          )}
        </Box>

        <Box display="flex" alignItems="center" gap={1}>
          {/* Edit Toggle */}
          <Tooltip title={isEditMode ? "Cancel Editing" : "Edit Report"}>
            <IconButton 
              size="small" 
              onClick={isEditMode ? handleCancelEdit : handleEditToggle}
              color={isEditMode ? "primary" : "default"}
            >
              {isEditMode ? <CancelIcon /> : <EditIcon />}
            </IconButton>
          </Tooltip>

          {/* Save Changes (only in edit mode) */}
          {isEditMode && (
            <Tooltip title="Save Changes">
              <IconButton 
                size="small" 
                onClick={() => handleSaveChanges()}
                color="primary"
              >
                <SaveIcon />
              </IconButton>
            </Tooltip>
          )}

          <Tooltip title="Refresh">
            <IconButton size="small" onClick={handleRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Toggle Fullscreen">
            <IconButton size="small" onClick={handleFullscreen}>
              <FullscreenIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Download">
            <IconButton size="small" onClick={handleDownloadMenuOpen}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Print">
            <IconButton size="small" onClick={handlePrint}>
              <PrintIcon />
            </IconButton>
          </Tooltip>

          {variant === 'dialog' && (
            <IconButton edge="end" color="inherit" onClick={onClose} aria-label="close">
              <CloseIcon />
            </IconButton>
          )}
        </Box>
      </Toolbar>

      {/* Main Content */}
      <Box sx={{ flex: 1, overflow: 'hidden', position: 'relative' }} ref={containerRef}>
        {renderPreviewContent()}
      </Box>

      {/* Download Menu */}
      <Menu
        anchorEl={downloadMenuAnchor}
        open={Boolean(downloadMenuAnchor)}
        onClose={handleDownloadMenuClose}
      >
        {getAvailableFileTypes().map((type) => (
          <MenuItem key={type} onClick={() => handleDownloadFile(type)}>
            <ListItemIcon>
              {type === 'pdf' ? <PdfIcon fontSize="small" /> : 
               type === 'docx' ? <DocxIcon fontSize="small" /> : 
               <ExcelIcon fontSize="small" />}
            </ListItemIcon>
            <ListItemText>Download as {type.toUpperCase()}</ListItemText>
          </MenuItem>
        ))}
        {getAvailableFileTypes().length === 0 && (
          <MenuItem disabled>
            <ListItemText>No files available</ListItemText>
          </MenuItem>
        )}
      </Menu>
    </Box>
  );

  if (variant === 'pane') {
    return (
      <Paper elevation={3} sx={{ height: '100%', overflow: 'hidden' }}>
        {content}
      </Paper>
    );
  }

  return (
    <Dialog
      fullScreen={isFullscreen}
      maxWidth="lg"
      fullWidth
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: { height: isFullscreen ? '100%' : '90vh' }
      }}
    >
      {content}
    </Dialog>
  );
};

export default DocumentPreview;