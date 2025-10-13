/**
 * Rich Text Editor Component for Report Content
 * Provides WYSIWYG editing with auto-save and version control integration
 */

import React from "react";
import { useState, useEffect, useCallback, useRef } from "react";
import {
  Box,
  Paper,
  Toolbar,
  IconButton,
  Divider,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tooltip,
} from "@mui/material";
import {
  FormatBold,
  FormatItalic,
  FormatUnderlined,
  FormatListBulleted,
  FormatListNumbered,
  FormatQuote,
  Image,
  Link,
  Save,
  History,
} from "@mui/icons-material";
import debounce from "lodash-es/debounce";
import enhancedReportService from "../../services/enhancedReportService";
import type { ReportVersion } from "../../services/enhancedReportService";

interface ReportEditorProps {
  reportId: number;
  initialContent?: any;
  onSave?: (content: any, version?: ReportVersion) => void;
  onAutoSave?: (content: any) => void;
  readOnly?: boolean;
  showVersionControls?: boolean;
  autoSaveInterval?: number; // milliseconds
}

interface EditorState {
  content: string;
  title: string;
  sections: Array<{
    id: string;
    type: "text" | "heading" | "list" | "quote" | "image";
    content: string;
    level?: number; // for headings
  }>;
}

const ReportEditor: React.FC<ReportEditorProps> = ({
  reportId,
  initialContent,
  onSave,
  onAutoSave,
  readOnly = false,
  showVersionControls = true,
  autoSaveInterval = 30000, // 30 seconds
}) => {
  const [editorState, setEditorState] = useState<EditorState>({
    content: "",
    title: "",
    sections: [],
  });

  const [isSaving, setIsSaving] = useState(false);
  const [isAutoSaving, setIsAutoSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Save dialog state
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [changeSummary, setChangeSummary] = useState("");

  // Editor refs
  const editorRef = useRef<HTMLDivElement>(null);
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize content
  useEffect(() => {
    if (initialContent) {
      setEditorState({
        content: initialContent.content || "",
        title: initialContent.title || "",
        sections: initialContent.sections || [],
      });
    }
  }, [initialContent]);

  // Auto-save functionality
  const debouncedAutoSave = useCallback(
    debounce(async (content: EditorState) => {
      if (!hasUnsavedChanges || readOnly) return;

      setIsAutoSaving(true);
      try {
        await enhancedReportService.autoSaveReport(reportId, content);
        onAutoSave?.(content);
        setLastSaved(new Date());
        setSaveError(null);
      } catch (error) {
        console.error("Auto-save failed:", error);
        setSaveError("Auto-save failed");
      } finally {
        setIsAutoSaving(false);
      }
    }, autoSaveInterval),
    [reportId, hasUnsavedChanges, readOnly, autoSaveInterval, onAutoSave]
  );

  // Handle content changes
  const handleContentChange = useCallback(
    (newContent: Partial<EditorState>) => {
      setEditorState((prev: any) => {
        const updated = { ...prev, ...newContent };
        setHasUnsavedChanges(true);
        debouncedAutoSave(updated);
        return updated;
      });
    },
    [debouncedAutoSave]
  );

  // Manual save with version creation
  const handleManualSave = async () => {
    if (!hasUnsavedChanges) return;

    setShowSaveDialog(true);
  };

  const performSave = async () => {
    setIsSaving(true);
    setSaveError(null);

    try {
      const version = await enhancedReportService.updateReportContent(
        reportId,
        editorState,
        changeSummary || "Manual save"
      );

      setHasUnsavedChanges(false);
      setLastSaved(new Date());
      setShowSaveDialog(false);
      setChangeSummary("");
      onSave?.(editorState, version);
    } catch (error) {
      console.error("Save failed:", error);
      setSaveError("Failed to save report");
    } finally {
      setIsSaving(false);
    }
  };

  // Formatting functions
  const formatText = (command: string, value?: string) => {
    document.execCommand(command, false, value);
    const selection = window.getSelection();
    if (selection && editorRef.current) {
      handleContentChange({
        content: editorRef.current.innerHTML,
      });
    }
  };

  // Insert section
  const insertSection = (
    type: "heading" | "text" | "list" | "quote" | "image"
  ) => {
    const newSection = {
      id: `section-${Date.now()}`,
      type,
      content: "",
      level: type === "heading" ? 1 : undefined,
    };

    handleContentChange({
      sections: [...editorState.sections, newSection],
    });
  };

  // Section management
  const updateSection = (
    sectionId: string,
    updates: Partial<(typeof editorState.sections)[0]>
  ) => {
    const updatedSections = editorState.sections.map((section: any) =>
      section.id === sectionId ? { ...section, ...updates } : section
    );
    handleContentChange({ sections: updatedSections });
  };

  const removeSection = (sectionId: string) => {
    const updatedSections = editorState.sections.filter(
      (section: any) => section.id !== sectionId
    );
    handleContentChange({ sections: updatedSections });
  };

  // Cleanup auto-save on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
      debouncedAutoSave.cancel();
    };
  }, [debouncedAutoSave]);

  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      {/* Editor Toolbar */}
      <Paper elevation={1} sx={{ borderRadius: 0 }}>
        <Toolbar>
          {/* Formatting Controls */}
          <Box
            sx={{
              display: "flex",
              gap: 1,
              flexWrap: "wrap",
              alignItems: "center",
            }}
          >
            {!readOnly && (
              <>
                <Tooltip title="Bold">
                  <IconButton size="small" onClick={() => formatText("bold")}>
                    <FormatBold />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Italic">
                  <IconButton size="small" onClick={() => formatText("italic")}>
                    <FormatItalic />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Underline">
                  <IconButton
                    size="small"
                    onClick={() => formatText("underline")}
                  >
                    <FormatUnderlined />
                  </IconButton>
                </Tooltip>

                <Divider orientation="vertical" flexItem />

                <Tooltip title="Heading">
                  <IconButton
                    size="small"
                    onClick={() => insertSection("heading")}
                  >
                    <Title />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Bullet List">
                  <IconButton
                    size="small"
                    onClick={() => formatText("insertUnorderedList")}
                  >
                    <FormatListBulleted />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Numbered List">
                  <IconButton
                    size="small"
                    onClick={() => formatText("insertOrderedList")}
                  >
                    <FormatListNumbered />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Quote">
                  <IconButton
                    size="small"
                    onClick={() => insertSection("quote")}
                  >
                    <FormatQuote />
                  </IconButton>
                </Tooltip>

                <Divider orientation="vertical" flexItem />

                <Tooltip title="Insert Image">
                  <IconButton
                    size="small"
                    onClick={() => insertSection("image")}
                  >
                    <Image />
                  </IconButton>
                </Tooltip>

                <Tooltip title="Insert Link">
                  <IconButton
                    size="small"
                    onClick={() =>
                      formatText("createLink", prompt("Enter URL:") || "")
                    }
                  >
                    <Link />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          {/* Status and Controls */}
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            {/* Save Status */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              {isAutoSaving && (
                <Chip
                  icon={<CircularProgress size={16} />}
                  label="Auto-saving..."
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              )}

              {isSaving && (
                <Chip
                  icon={<CircularProgress size={16} />}
                  label="Saving..."
                  size="small"
                  color="primary"
                />
              )}

              {lastSaved && !isSaving && !isAutoSaving && (
                <Typography variant="caption" color="text.secondary">
                  Saved {lastSaved.toLocaleTimeString()}
                </Typography>
              )}

              {hasUnsavedChanges && !isSaving && !isAutoSaving && (
                <Chip
                  label="Unsaved changes"
                  size="small"
                  color="warning"
                  variant="outlined"
                />
              )}
            </Box>

            {/* Action Buttons */}
            {!readOnly && (
              <>
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={handleManualSave}
                  disabled={!hasUnsavedChanges || isSaving}
                  size="small"
                >
                  Save
                </Button>

                {showVersionControls && (
                  <Button
                    variant="outlined"
                    startIcon={<History />}
                    size="small"
                  >
                    Versions
                  </Button>
                )}
              </>
            )}
          </Box>
        </Toolbar>
      </Paper>

      {/* Error Alert */}
      {saveError && (
        <Alert
          severity="error"
          onClose={() => setSaveError(null)}
          sx={{ borderRadius: 0 }}
        >
          {saveError}
        </Alert>
      )}

      {/* Editor Content */}
      <Box sx={{ flex: 1, overflow: "auto", p: 3 }}>
        <Paper elevation={0} sx={{ minHeight: "100%", p: 3 }}>
          {/* Title */}
          <TextField
            fullWidth
            variant="standard"
            placeholder="Report Title"
            value={editorState.title}
            onChange={(e: any) =>
              handleContentChange({ title: e.target.value })
            }
            disabled={readOnly}
            sx={{
              mb: 3,
              "& .MuiInput-input": {
                fontSize: "2rem",
                fontWeight: "bold",
              },
            }}
          />

          {/* Main Content */}
          <Box
            ref={editorRef}
            contentEditable={!readOnly}
            suppressContentEditableWarning
            onInput={(e: any) => {
              handleContentChange({ content: e.currentTarget.innerHTML });
            }}
            sx={{
              minHeight: "300px",
              border: readOnly ? "none" : "1px solid #e0e0e0",
              borderRadius: 1,
              p: 2,
              "&:focus": {
                outline: "none",
                borderColor: "primary.main",
              },
              "& p": { margin: "8px 0" },
              "& h1, & h2, & h3": { margin: "16px 0 8px 0" },
              "& ul, & ol": { margin: "8px 0", paddingLeft: "24px" },
              "& blockquote": {
                borderLeft: "4px solid #e0e0e0",
                margin: "16px 0",
                paddingLeft: "16px",
                fontStyle: "italic",
              },
            }}
            dangerouslySetInnerHTML={{ __html: editorState.content }}
          />

          {/* Sections */}
          {editorState.sections.map((section: any) => (
            <Box key={section.id} sx={{ mt: 2, position: "relative" }}>
              {!readOnly && (
                <IconButton
                  size="small"
                  onClick={() => removeSection(section.id)}
                  sx={{ position: "absolute", right: -40, top: 0 }}
                >
                  ×
                </IconButton>
              )}

              {section.type === "heading" && (
                <TextField
                  fullWidth
                  variant="standard"
                  placeholder="Heading"
                  value={section.content}
                  onChange={(e: any) =>
                    updateSection(section.id, { content: e.target.value })
                  }
                  disabled={readOnly}
                  sx={{
                    "& .MuiInput-input": {
                      fontSize: `${2 - (section.level || 1) * 0.2}rem`,
                      fontWeight: "bold",
                    },
                  }}
                />
              )}

              {section.type === "text" && (
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  placeholder="Text content"
                  value={section.content}
                  onChange={(e: any) =>
                    updateSection(section.id, { content: e.target.value })
                  }
                  disabled={readOnly}
                />
              )}

              {section.type === "quote" && (
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  placeholder="Quote text"
                  value={section.content}
                  onChange={(e: any) =>
                    updateSection(section.id, { content: e.target.value })
                  }
                  disabled={readOnly}
                  sx={{
                    "& .MuiInputBase-root": {
                      fontStyle: "italic",
                      borderLeft: "4px solid",
                      borderColor: "primary.main",
                      paddingLeft: 2,
                    },
                  }}
                />
              )}
            </Box>
          ))}
        </Paper>
      </Box>

      {/* Save Dialog */}
      <Dialog
        open={showSaveDialog}
        onClose={() => setShowSaveDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Save Report</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Change Summary (Optional)"
            fullWidth
            variant="outlined"
            value={changeSummary}
            onChange={(e: any) => setChangeSummary(e.target.value)}
            placeholder="Describe your changes..."
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSaveDialog(false)}>Cancel</Button>
          <Button
            onClick={performSave}
            variant="contained"
            disabled={isSaving}
            startIcon={isSaving ? <CircularProgress size={16} /> : <Save />}
          >
            Save Version
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ReportEditor;
