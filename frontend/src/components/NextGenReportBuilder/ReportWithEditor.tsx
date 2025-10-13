import React from 'react';
/**
 * Report with Inline Editor Component
 * Combines report display with inline editing capabilities and AI integration
 */

import { useState, useCallback } from "react";
  
import { Box, Paper, Typography, Button, Tabs, Tab, Divider, Alert, Chip, IconButton, Tooltip, Menu, MenuItem, ListItemIcon, ListItemText } from "@mui/material";
  
import { Visibility, Edit, Download, Share, History, SmartToy, PictureAsPdf, Description, MoreVert } from "@mui/icons-material";

import InlineReportEditor from './InlineReportEditor';

import DocumentPreview from '../DocumentPreview';

interface ReportWithEditorProps {
  reportId: number;
  
reportTitle: string;
  
reportContent: string;
  
reportStatus: 'generating' | 'completed' | 'failed';
  
onSave: (content: string) => void;
  
onExport?: (format: 'pdf' | 'docx' | 'html') => void;
  
onShare?: () => void;
  
showVersionHistory?: boolean;
  
enableAI?: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  
index: number;
  
value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`report-tabpanel-${index}`}
      aria-labelledby={`report-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const ReportWithEditor: React.FC<ReportWithEditorProps> = ({
  reportId,
  reportTitle,
  reportContent,
  reportStatus,
  onSave,
  onExport,
  onShare,
  showVersionHistory = true,
  enableAI = true,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  
const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  
const [isExporting, setIsExporting] = useState(false);

const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

const handleSave = useCallback((content: string) => {
    onSave(content);
    // Show success message or handle response
  }, [onSave]);

const handleExport = async (format: 'pdf' | 'docx' | 'html') => {
    if (!onExport) return;

setIsExporting(true);
    
try {
      await onExport(format);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
      
setMenuAnchor(null);
    }
  };

const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMenuAnchor(event.currentTarget);
  };

const handleMenuClose = () => {
    setMenuAnchor(null);
  };

if (reportStatus === 'generating') {
    return (
      <Paper elevation={2} sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom>
          Generating Report...
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Your report is being generated. This may take a few moments.
        </Typography>
      </Paper>
    );
  }

  if (reportStatus === 'failed') {
    return (
      <Alert severity="error">
        Report generation failed. Please try again or contact support.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h5" component="h1" gutterBottom>
            {reportTitle}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip 
              label="Generated" 
              color="success" 
              size="small" 
            />
            {enableAI && (
              <Chip 
                icon={<SmartToy />}
                label="AI Enhanced" 
                color="primary" 
                size="small" 
                variant="outlined"
              />
            )}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {onShare && (
            <Button
              startIcon={<Share />}
              onClick={onShare}
              variant="outlined"
            >
              Share
            </Button>
          )}

          {showVersionHistory && (
            <Button
              startIcon={<History />}
              variant="outlined"
            >
              History
            </Button>
          )}

          <Tooltip title="Export options">
            <IconButton onClick={handleMenuOpen}>
              <MoreVert />
            </IconButton>
          </Tooltip>

          <Menu
            anchorEl={menuAnchor}
            open={Boolean(menuAnchor)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={() => handleExport('pdf')} disabled={isExporting}>
              <ListItemIcon>
                <PictureAsPdf />
              </ListItemIcon>
              <ListItemText>Export as PDF</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleExport('docx')} disabled={isExporting}>
              <ListItemIcon>
                <Description />
              </ListItemIcon>
              <ListItemText>Export as Word</ListItemText>
            </MenuItem>
            <MenuItem onClick={() => handleExport('html')} disabled={isExporting}>
              <ListItemIcon>
                <Download />
              </ListItemIcon>
              <ListItemText>Export as HTML</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* Tabs */}
      <Paper elevation={1}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab 
            icon={<Edit />} 
            label="Edit" 
            id="report-tab-0"
            aria-controls="report-tabpanel-0"
          />
          <Tab 
            icon={<Visibility />} 
            label="Preview" 
            id="report-tab-1"
            aria-controls="report-tabpanel-1"
          />
        </Tabs>

        {/* Tab Panels */}
        <TabPanel value={activeTab} index={0}>
          <InlineReportEditor
            reportContent={reportContent}
            reportId={reportId}
            onSave={handleSave}
            showAITools={enableAI}
            autoSave={true}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <Box sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Report Preview
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            {/* Preview content */}
            <Box 
              sx={{ 
                minHeight: 400,
                '& h1, & h2, & h3': { 
                  color: 'primary.main',
                  marginBottom: 2 
                },
                '& p': { 
                  marginBottom: 2,
                  lineHeight: 1.6 
                },
                '& ul, & ol': { 
                  marginBottom: 2,
                  paddingLeft: 3 
                },
              }}
              dangerouslySetInnerHTML={{ __html: reportContent }}
            />
          </Box>
        </TabPanel>
      </Paper>

      {/* AI Suggestions Panel (if enabled) */}
      {enableAI && activeTab === 0 && (
        <Paper elevation={1} sx={{ mt: 2, p: 2, bgcolor: 'primary.50' }}>
          <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SmartToy color="primary" />
            AI Suggestions
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Select text in the editor above to get AI-powered suggestions for improvement, 
            translation, or formatting.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default ReportWithEditor;
