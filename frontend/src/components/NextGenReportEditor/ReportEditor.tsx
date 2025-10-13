import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * NextGen Report Editor Component
 * Rich text editor with collaborative features, auto-save, and version control
 */

import { useState, useEffect, useCallback, useRef } from "react";
  
import { Box, Paper, Typography, Chip, Alert, CircularProgress, Snackbar, Fade, IconButton, Tooltip } from "@mui/material";
  
import { Save, SaveOutlined, History, People, Close } from "@mui/icons-material";

import { debounce } from "lodash-es";

import EditingToolbar from './EditingToolbar';

import CollaborativeEditor from './CollaborativeEditor';

import VersionHistory from './VersionHistory';

import AutoSaveIndicator from './AutoSaveIndicator';

import enhancedReportService from '../../services/enhancedReportService';

import collaborationService from '../../services/collaborationService';

import type { ReportVersion } from '../../services/enhancedReportService';

import type { CollaborationSession } from '../../services/collaborationService';

export interface EditorContent {
  title: string;
  
content: string;
  
sections: Array<{
    id: string;
    
type: 'text' | 'heading' | 'list' | 'quote' | 'image' | 'table';
    
content: string;
    
level?: number;
    
metadata?: Record<string, any>;
  }>;
  
metadata: {
    wordCount: number;
    
characterCount: number;
    
lastModified: Date,
    
version: number,
  };
}

interface ReportEditorProps {
  reportId: number;
  
initialContent?: EditorContent;
  
onSave?: (content: EditorContent, version?: ReportVersion) => void;
  
onClose?: () => void;
  
readOnly?: boolean;
  
enableCollaboration?: boolean;
  
autoSaveInterval?: number;
  
showVersionHistory?: boolean;
}

const ReportEditor: React.FC<ReportEditorProps> = ({
  reportId,
  initialContent,
  onSave,
  onClose,
  readOnly = false,
  enableCollaboration = true,
  autoSaveInterval = 30000,
  showVersionHistory = true,
}) => {
  // Editor state
  const [content, setContent] = useState<EditorContent>({
    title: '',
    content: '',
    sections: [],
    metadata: {
      wordCount: 0,
      characterCount: 0,
      lastModified: new Date(),
      version: 1,
    },
  });

  // UI state
  const [loading, setLoading] = useState(false);
  
const [saving, setSaving] = useState(false);
  
const [autoSaving, setAutoSaving] = useState(false);
  
const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
const [lastSaved, setLastSaved] = useState<Date | null>(null);
  
const [error, setError] = useState<string | null>(null);
  
const [showVersionPanel, setShowVersionPanel] = useState(false);
  
const [showCollaborationPanel, setShowCollaborationPanel] = useState(false);

  // Collaboration state
  const [collaborationSession, setCollaborationSession] = useState<CollaborationSession | null>(null);
  
const [activeUsers, setActiveUsers] = useState<number>(1);

  // Refs
  const editorRef = useRef<HTMLDivElement>(null);
  
const autoSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize content
  useEffect(() => {
    if (initialContent) {
      setContent(initialContent);
    } else {
      loadReportContent();
    }
  }, [reportId, initialContent]);

  // Initialize collaboration session
  useEffect(() => {
    if (enableCollaboration && !readOnly) {
      initializeCollaboration();
    }
  }, [enableCollaboration, readOnly, reportId]);

  // Auto-save setup
  const debouncedAutoSave = useCallback(
    debounce(async (contentToSave: EditorContent) => {
      if (!hasUnsavedChanges || readOnly) return;

setAutoSaving(true);
      
try {
        await enhancedReportService.autoSaveReport(reportId, contentToSave);
        
setLastSaved(new Date());
        
setError(null);
      } catch (err) {
        console.error('Auto-save failed:', err);
        
setError('Auto-save failed');
      } finally {
        setAutoSaving(false);
      }
    }, autoSaveInterval),
    [reportId, hasUnsavedChanges, readOnly, autoSaveInterval]
  );

  // Load report content
  const loadReportContent = async () => {
    setLoading(true);
    
try {
      // This would typically load from the API
      // For now, using default content
      const defaultContent: EditorContent = {
        title: 'New Report',
        content: '<p>Start writing your report here...</p>',
        sections: [],
        metadata: {
          wordCount: 0,
          characterCount: 0,
          lastModified: new Date(),
          version: 1,
        },
      };
      
setContent(defaultContent);
    } catch (err) {
      console.error('Failed to load report:', err);
      
setError('Failed to load report content');
    } finally {
      setLoading(false);
    }
  };

  // Initialize collaboration
  const initializeCollaboration = async () => {
    try {
      const session = collaborationService.createCollaborationSession(
        `report-${reportId}`,
        content.title || 'Untitled Report',
        'Collaborative report editing session'
      );
      
setCollaborationSession(session);
      
setActiveUsers(session.participants.length);
    } catch (err) {
      console.error('Failed to initialize collaboration:', err);
    }
  };

  // Handle content changes
  const handleContentChange = useCallback((newContent: Partial<EditorContent>) => {
    setContent(prev => {
      const updated = { ...prev, ...newContent };
      
      // Update metadata
      updated.metadata = {
        ...updated.metadata,
        wordCount: countWords(updated.content),
        characterCount: updated.content.length,
        lastModified: new Date(),
      };

setHasUnsavedChanges(true);
      
debouncedAutoSave(updated);

return updated;
    });
  }, [debouncedAutoSave]);

  // Manual save
  const handleSave = async () => {
    if (!hasUnsavedChanges || saving) return;

setSaving(true);
    
setError(null);

try {
      const version = await enhancedReportService.updateReportContent(
        reportId,
        content,
        'Manual save'
      );

setHasUnsavedChanges(false);
      
setLastSaved(new Date());
      
onSave?.(content, version);
    } catch (err) {
      console.error('Save failed:', err);
      
setError('Failed to save report');
    } finally {
      setSaving(false);
    }
  };

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 's':
            e.preventDefault();
            
handleSave();
            
break;
          
case 'z':
            if (e.shiftKey) {
              // Redo
              e.preventDefault();
              // Implement redo functionality
            } else {
              // Undo
              e.preventDefault();
              // Implement undo functionality
            }
            break;
        }
      }
    };

document.addEventListener('keydown', handleKeyDown);
    
return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleSave]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
      debouncedAutoSave.cancel();
    };
  }, [debouncedAutoSave]);

  // Utility functions
  const countWords = (text: string): number => {
    return text.replace(/<[^>]*>/g, '').split(/\s+/).filter(word => word.length > 0).length;
  };

if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ borderRadius: 0, zIndex: 1000 }}>
        <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h6" component="h1" noWrap>
              {content.title || 'Untitled Report'}
            </Typography>
            
            {/* Status indicators */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AutoSaveIndicator
                isSaving={saving}
                isAutoSaving={autoSaving}
                hasUnsavedChanges={hasUnsavedChanges}
                lastSaved={lastSaved}
              />
              
              {enableCollaboration && (
                <Chip
                  icon={<People />}
                  label={`${activeUsers} user${activeUsers !== 1 ? 's' : ''}`}
                  size="small"
                  variant="outlined"
                  onClick={() => setShowCollaborationPanel(true)}
                  sx={{ cursor: 'pointer' }}
                />
              )}
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* Action buttons */}
            {!readOnly && (
              <Tooltip title="Save (Ctrl+S)">
                <IconButton
                  onClick={handleSave}
                  disabled={!hasUnsavedChanges || saving}
                  color={hasUnsavedChanges ? 'primary' : 'default'}
                >
                  {saving ? <CircularProgress size={20} /> : <Save />}
                </IconButton>
              </Tooltip>
            )}

            {showVersionHistory && (
              <Tooltip title="Version History">
                <IconButton onClick={() => setShowVersionPanel(true)}>
                  <History />
                </IconButton>
              </Tooltip>
            )}

            {onClose && (
              <Tooltip title="Close Editor">
                <IconButton onClick={onClose}>
                  <Close />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        {/* Editing Toolbar */}
        {!readOnly && (
          <EditingToolbar
            onFormatText={(format, value) => {
              // Handle text formatting
              document.execCommand(format, false, value);
            }}
            onInsertElement={(elementType: any) => {
              // Handle element insertion
              const newSection = {
                id: `section-${Date.now()}`,
                type: elementType as any,
                content: '',
              };
              
handleContentChange({
                sections: [...content.sections, newSection],
              });
            }}
            disabled={readOnly}
          />
        )}
      </Paper>

      {/* Main Editor Area */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Editor */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <CollaborativeEditor
            ref={editorRef}
            content={content}
            onChange={handleContentChange}
            readOnly={readOnly}
            collaborationSession={collaborationSession}
            reportId={reportId}
          />
        </Box>

        {/* Side Panels */}
        <Fade in={showVersionPanel}>
          <Box sx={{ width: showVersionPanel ? 400 : 0, overflow: 'hidden', transition: 'width 0.3s' }}>
            {showVersionPanel && (
              <Paper elevation={2} sx={{ height: '100%', borderRadius: 0 }}>
                <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Typography variant="h6">Version History</Typography>
                  <IconButton size="small" onClick={() => setShowVersionPanel(false)}>
                    <Close />
                  </IconButton>
                </Box>
                <VersionHistory
                  reportId={reportId}
                  onVersionSelect={(version: any) => {
                    // Handle version selection
                    console.log('Selected version:', version);
                  }}
                  onVersionRestore={(version: any) => {
                    // Handle version restore
                    console.log('Restored version:', version);
                    
setShowVersionPanel(false);
                  }}
                />
              </Paper>
            )}
          </Box>
        </Fade>
      </Box>

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ReportEditor;
