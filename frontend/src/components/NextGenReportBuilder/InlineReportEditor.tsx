import React from 'react';
/**
 * Inline Report Editor Component
 * Allows editing reports directly in the same page after generation with AI integration
 */

import { useState, useRef, useCallback, useEffect } from "react";
  
import { Box, Paper, Typography, IconButton, Button, Tooltip, Chip, Divider, Menu, MenuItem, ListItemIcon, ListItemText, Dialog, DialogTitle, DialogContent, DialogActions, TextField, CircularProgress, Alert, Fade, Collapse, ButtonGroup } from "@mui/material";
  
import { Edit, Save, Cancel, FormatBold, FormatItalic, FormatUnderlined, FormatListBulleted, FormatListNumbered, SmartToy, AutoAwesome, Translate, Spellcheck, ExpandMore, ExpandLess, History, Undo, Redo } from "@mui/icons-material";

import { debounce } from "lodash-es";

interface InlineReportEditorProps {
  reportContent: string;
  
reportId?: number;
  
onSave: (content: string) => void;
  
onCancel?: () => void;
  
readOnly?: boolean;
  
showAITools?: boolean;
  
autoSave?: boolean;
  
autoSaveInterval?: number;
}

interface AIEnhancement {
  type: 'improve' | 'formal' | 'summary' | 'expand' | 'translate';
  
original: string;
  
enhanced: string;
  
confidence: number;
}

const InlineReportEditor: React.FC<InlineReportEditorProps> = ({
  reportContent,
  reportId,
  onSave,
  onCancel,
  readOnly = false,
  showAITools = true,
  autoSave = true,
  autoSaveInterval = 30000,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  
const [content, setContent] = useState(reportContent);
  
const [selectedText, setSelectedText] = useState('');
  
const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
const [isSaving, setIsSaving] = useState(false);
  
const [isAutoSaving, setIsAutoSaving] = useState(false);
  
const [lastSaved, setLastSaved] = useState<Date | null>(null);
  
const [showAIPanel, setShowAIPanel] = useState(false);
  
const [aiEnhancements, setAIEnhancements] = useState<AIEnhancement[]>([]);
  
const [isProcessingAI, setIsProcessingAI] = useState(false);
  
const [aiError, setAIError] = useState<string | null>(null);

  // Refs
  const editorRef = useRef<HTMLDivElement>(null);
  
const selectionRef = useRef<{ start: number; 
end: number }>({ start: 0, end: 0 });

  // Auto-save functionality
  const debouncedAutoSave = useCallback(
    debounce(async (contentToSave: string) => {
      if (!autoSave || !hasUnsavedChanges || readOnly) return;

setIsAutoSaving(true);
      
try {
        // In a real implementation, this would call the API
        await new Promise(resolve => setTimeout(resolve, 1000));
        
setLastSaved(new Date());
        
setHasUnsavedChanges(false);
      } catch (error) {
        console.error('Auto-save failed:', error);
      } finally {
        setIsAutoSaving(false);
      }
    }, autoSaveInterval),
    [autoSave, hasUnsavedChanges, readOnly, autoSaveInterval]
  );

  // Handle content changes
  const handleContentChange = useCallback((newContent: string) => {
    setContent(newContent);
    
setHasUnsavedChanges(true);
    
debouncedAutoSave(newContent);
  }, [debouncedAutoSave]);

  // Handle text selection
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    
if (selection && selection.toString().trim()) {
      setSelectedText(selection.toString().trim());
      
selectionRef.current = {
        start: selection.anchorOffset,
        end: selection.focusOffset,
      };
    } else {
      setSelectedText('');
    }
  }, []);

  // AI Enhancement functions
  const enhanceTextWithAI = async (type: AIEnhancement['type']) => {
    if (!selectedText.trim()) {
      setAIError('Please select text to enhance');
      
return;
    }

    setIsProcessingAI(true);
    
setAIError(null);

try {
      // Mock AI enhancement - in real implementation, call your AI service
      const mockEnhancement: AIEnhancement = {
        type,
        original: selectedText,
        enhanced: await mockAIEnhancement(selectedText, type),
        confidence: 0.85 + Math.random() * 0.15,
      };

setAIEnhancements(prev => [mockEnhancement, ...prev.slice(0, 4)]);
    } catch (error) {
      setAIError('AI enhancement failed. Please try again.');
      
console.error('AI enhancement error:', error);
    } finally {
      setIsProcessingAI(false);
    }
  };

  // Mock AI enhancement function
  const mockAIEnhancement = async (text: string, type: AIEnhancement['type']): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate API call

    switch (type) {
      case 'improve':
        return `Enhanced: ${text} with improved clarity and flow.`;
      
case 'formal':
        return `Formal version: ${text.replace(/\b(good|bad|big|small)\b/g, match => {
          const formal = { good: 'excellent', bad: 'inadequate', big: 'substantial', small: 'minimal' };
          
return formal[match as keyof typeof formal] || match;
        })}`;
      
case 'summary':
        return `Summary: ${text.split(' ').slice(0, Math.max(3, Math.floor(text.split(' ').length / 3))).join(' ')}...`;
      
case 'expand':
        return `${text} This provides additional context and detailed explanation to enhance understanding.`;
      
case 'translate':
        return `Translated: ${text} (simulated translation)`;
      
default:
        return text;
    }
  };

  // Apply AI enhancement
  const applyEnhancement = (enhancement: AIEnhancement) => {
    const newContent = content.replace(enhancement.original, enhancement.enhanced);
    
handleContentChange(newContent);
    
setSelectedText('');
    
setAIEnhancements(prev => prev.filter(e => e !== enhancement));
  };

  // Format text
  const formatText = (command: string) => {
    document.execCommand(command, false);
    
if (editorRef.current) {
      handleContentChange(editorRef.current.innerHTML);
    }
  };

  // Save content
  const handleSave = async () => {
    setIsSaving(true);
    
try {
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate save
      onSave(content);
      
setHasUnsavedChanges(false);
      
setLastSaved(new Date());
      
setIsEditing(false);
    } catch (error) {
      console.error('Save failed:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Cancel editing
  const handleCancel = () => {
    setContent(reportContent);
    
setHasUnsavedChanges(false);
    
setIsEditing(false);
    
setSelectedText('');
    
setAIEnhancements([]);
    
onCancel?.();
  };

  // Cleanup
  useEffect(() => {
    return () => {
      debouncedAutoSave.cancel();
    };
  }, [debouncedAutoSave]);

return (
    <Box sx={{ position: 'relative' }}>
      {/* Header with controls */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6">Report Content</Typography>
          
          {/* Status indicators */}
          {isEditing && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              {isAutoSaving && (
                <Chip
                  icon={<CircularProgress size={16} />}
                  label="Auto-saving..."
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              )}
              
              {hasUnsavedChanges && !isAutoSaving && (
                <Chip
                  label="Unsaved changes"
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              )}
              
              {lastSaved && !hasUnsavedChanges && (
                <Chip
                  label={`Saved ${lastSaved.toLocaleTimeString()}`}
                  size="small"
                  color="success"
                  variant="outlined"
                />
              )}
            </Box>
          )}
        </Box>

        {/* Action buttons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          {!isEditing && !readOnly && (
            <Button
              startIcon={<Edit />}
              onClick={() => setIsEditing(true)}
              variant="outlined"
            >
              Edit
            </Button>
          )}
          
          {isEditing && (
            <>
              <Button
                startIcon={<Save />}
                onClick={handleSave}
                disabled={isSaving}
                variant="contained"
              >
                {isSaving ? 'Saving...' : 'Save'}
              </Button>
              
              <Button
                startIcon={<Cancel />}
                onClick={handleCancel}
                variant="outlined"
              >
                Cancel
              </Button>
            </>
          )}
        </Box>
      </Box>

      {/* Editing toolbar */}
      {isEditing && (
        <Paper elevation={1} sx={{ p: 1, mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            {/* Text formatting */}
            <ButtonGroup size="small">
              <Tooltip title="Bold">
                <IconButton onClick={() => formatText('bold')}>
                  <FormatBold />
                </IconButton>
              </Tooltip>
              <Tooltip title="Italic">
                <IconButton onClick={() => formatText('italic')}>
                  <FormatItalic />
                </IconButton>
              </Tooltip>
              <Tooltip title="Underline">
                <IconButton onClick={() => formatText('underline')}>
                  <FormatUnderlined />
                </IconButton>
              </Tooltip>
            </ButtonGroup>

            <Divider orientation="vertical" flexItem />

            {/* Lists */}
            <ButtonGroup size="small">
              <Tooltip title="Bullet List">
                <IconButton onClick={() => formatText('insertUnorderedList')}>
                  <FormatListBulleted />
                </IconButton>
              </Tooltip>
              <Tooltip title="Numbered List">
                <IconButton onClick={() => formatText('insertOrderedList')}>
                  <FormatListNumbered />
                </IconButton>
              </Tooltip>
            </ButtonGroup>

            <Divider orientation="vertical" flexItem />

            {/* AI Tools */}
            {showAITools && (
              <>
                <Button
                  startIcon={<SmartToy />}
                  onClick={() => setShowAIPanel(!showAIPanel)}
                  size="small"
                  variant={showAIPanel ? 'contained' : 'outlined'}
                  endIcon={showAIPanel ? <ExpandLess /> : <ExpandMore />}
                >
                  AI Tools
                </Button>
                
                {selectedText && (
                  <ButtonGroup size="small">
                    <Tooltip title="Improve Text">
                      <IconButton 
                        onClick={() => enhanceTextWithAI('improve')}
                        disabled={isProcessingAI}
                      >
                        <AutoAwesome />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Make Formal">
                      <IconButton 
                        onClick={() => enhanceTextWithAI('formal')}
                        disabled={isProcessingAI}
                      >
                        <Spellcheck />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Translate">
                      <IconButton 
                        onClick={() => enhanceTextWithAI('translate')}
                        disabled={isProcessingAI}
                      >
                        <Translate />
                      </IconButton>
                    </Tooltip>
                  </ButtonGroup>
                )}
              </>
            )}
          </Box>
        </Paper>
      )}

      {/* AI Panel */}
      <Collapse in={showAIPanel && isEditing}>
        <Paper elevation={2} sx={{ p: 2, mb: 2, bgcolor: 'primary.50' }}>
          <Typography variant="subtitle2" gutterBottom>
            AI Assistant
          </Typography>
          
          {aiError && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setAIError(null)}>
              {aiError}
            </Alert>
          )}
          
          {selectedText && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Selected: "{selectedText.substring(0, 50)}..."
              </Typography>
            </Box>
          )}
          
          {isProcessingAI && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <CircularProgress size={16} />
              <Typography variant="body2">Processing with AI...</Typography>
            </Box>
          )}
          
          {/* AI Enhancements */}
          {aiEnhancements.length > 0 && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                AI Suggestions
              </Typography>
              {aiEnhancements.map((enhancement, index) => (
                <Paper key={index} elevation={1} sx={{ p: 2, mb: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Chip label={enhancement.type} size="small" />
                    <Chip 
                      label={`${Math.round(enhancement.confidence * 100)}% confidence`} 
                      size="small" 
                      variant="outlined" 
                    />
                  </Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    <strong>Original:</strong> {enhancement.original}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    <strong>Enhanced:</strong> {enhancement.enhanced}
                  </Typography>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={() => applyEnhancement(enhancement)}
                  >
                    Apply
                  </Button>
                </Paper>
              ))}
            </Box>
          )}
        </Paper>
      </Collapse>

      {/* Content editor */}
      <Paper elevation={1} sx={{ minHeight: 400 }}>
        {isEditing ? (
          <Box
            ref={editorRef}
            contentEditable
            suppressContentEditableWarning
            onInput={(e: any) => handleContentChange(e.currentTarget.innerHTML)}
            onMouseUp={handleTextSelection}
            onKeyUp={handleTextSelection}
            sx={{
              p: 3,
              minHeight: 400,
              outline: 'none',
              '&:focus': {
                bgcolor: 'action.hover',
              },
              '& p': { margin: '8px 0' },
              '& h1, & h2, & h3': { margin: '16px 0 8px 0' },
              '& ul, & ol': { margin: '8px 0', paddingLeft: '24px' },
            }}
            dangerouslySetInnerHTML={{ __html: content }}
          />
        ) : (
          <Box sx={{ p: 3 }}>
            <div dangerouslySetInnerHTML={{ __html: content }} />
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default InlineReportEditor;
