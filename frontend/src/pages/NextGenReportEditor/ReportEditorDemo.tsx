import React from 'react';
/**
 * NextGen Report Editor Demo Page
 * Demonstrates the full report editing capabilities
 */

import { useState } from "react";
  
import { Box, Container, Typography, Button, Card, CardContent, Grid, Chip, Dialog, DialogTitle, DialogContent, DialogActions, List, ListItem, ListItemText, ListItemIcon, Divider } from "@mui/material";
  
import { Edit, Add, Visibility, History, People, Save, Share, Download } from "@mui/icons-material";

import { ReportEditor, type EditorContent } from "../../components/NextGenReportEditor";

import type { ReportVersion } from '../../services/enhancedReportService';

interface MockReport {
  id: number;
  
title: string;
  
description: string;
  
lastModified: Date;
  
author: string;
  
status: 'draft' | 'published' | 'archived';
  
collaborators: number;
  
versions: number;
}

const ReportEditorDemo: React.FC = () => {
  const [selectedReport, setSelectedReport] = useState<MockReport | null>(null);
  
const [editorOpen, setEditorOpen] = useState(false);
  
const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Mock reports data
  const mockReports: MockReport[] = [
    {
      id: 1,
      title: 'Q4 Sales Performance Analysis',
      description: 'Comprehensive analysis of Q4 sales data with regional breakdowns and trend analysis.',
      lastModified: new Date('2024-01-15T10:30:00'),
      author: 'John Smith',
      status: 'published',
      collaborators: 3,
      versions: 12,
    },
    {
      id: 2,
      title: 'Customer Satisfaction Survey Results',
      description: 'Analysis of customer feedback and satisfaction metrics from the latest survey.',
      lastModified: new Date('2024-01-14T15:45:00'),
      author: 'Sarah Johnson',
      status: 'draft',
      collaborators: 2,
      versions: 8,
    },
    {
      id: 3,
      title: 'Market Research Report - Tech Trends',
      description: 'Research findings on emerging technology trends and market opportunities.',
      lastModified: new Date('2024-01-13T09:15:00'),
      author: 'Mike Chen',
      status: 'published',
      collaborators: 5,
      versions: 15,
    },
  ];

const handleOpenEditor = (report: MockReport) => {
    setSelectedReport(report);
    
setEditorOpen(true);
  };

const handleCloseEditor = () => {
    setEditorOpen(false);
    
setSelectedReport(null);
  };

const handleSaveReport = (content: EditorContent, version?: ReportVersion) => {
    console.log('Report saved:', content, version);
    // In a real app, this would save to the backend
  };

const handleCreateReport = () => {
    const newReport: MockReport = {
      id: Date.now(),
      title: 'New Report',
      description: 'A new report created with the NextGen editor.',
      lastModified: new Date(),
      author: 'Current User',
      status: 'draft',
      collaborators: 1,
      versions: 1,
    };

setSelectedReport(newReport);
    
setCreateDialogOpen(false);
    
setEditorOpen(true);
  };

  const getStatusColor =  (status: string) => {
    switch (status) {
      case 'published':
        return 'success';
      case 'draft':
        return 'warning';
      case 'archived':
        return 'default';
      default:
        return 'default';
    }
  };

const mockInitialContent: EditorContent = {
    title: selectedReport?.title || 'New Report',
    content: `
      <h1>Executive Summary</h1>
      <p>This report provides a comprehensive analysis of our recent findings and recommendations for moving forward.</p>
      
      <h2>Key Findings</h2>
      <ul>
        <li>Finding 1: Significant improvement in customer satisfaction scores</li>
        <li>Finding 2: Revenue growth exceeded expectations by 15%</li>
        <li>Finding 3: Market share increased in key demographics</li>
      </ul>
      
      <h2>Recommendations</h2>
      <p>Based on our analysis, we recommend the following actions:</p>
      <ol>
        <li>Continue current marketing strategies</li>
        <li>Expand into new market segments</li>
        <li>Invest in customer service improvements</li>
      </ol>
      
      <h2>Conclusion</h2>
      <p>The data shows positive trends across all key metrics. We are well-positioned for continued growth in the coming quarters.</p>
    `,
    sections: [],
    metadata: {
      wordCount: 120,
      characterCount: 800,
      lastModified: new Date(),
      version: selectedReport?.versions || 1,
    },
  };

return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          NextGen Report Editor
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Advanced collaborative report editing with real-time features
        </Typography>
        
        <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip icon={<Edit />} label="Rich Text Editing" />
          <Chip icon={<People />} label="Real-time Collaboration" />
          <Chip icon={<History />} label="Version Control" />
          <Chip icon={<Save />} label="Auto-save" />
        </Box>
      </Box>

      {/* Action Buttons */}
      <Box sx={{ mb: 4, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setCreateDialogOpen(true)}
          size="large"
        >
          Create New Report
        </Button>
        
        <Button
          variant="outlined"
          startIcon={<Visibility />}
          onClick={() => handleOpenEditor(mockReports[0])}
          size="large"
        >
          Demo Editor
        </Button>
      </Box>

      {/* Reports Grid */}
      <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 3 }}>
        Recent Reports
      </Typography>
      
      <Grid container spacing={3}>
        {mockReports.map((report: any) => (
          <Grid item xs={12} md={6} lg={4} key={report.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  elevation: 4,
                  transform: 'translateY(-2px)',
                },
              }}
              onClick={() => handleOpenEditor(report)}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Typography variant="h6" component="h3" noWrap>
                    {report.title}
                  </Typography>
                  <Chip
                    label={report.status}
                    size="small"
                    color={getStatusColor(report.status) as any}
                  />
                </Box>
                
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                    mb: 2,
                  }}
                >
                  {report.description}
                </Typography>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 'auto' }}>
                  <Typography variant="caption" color="text.secondary">
                    by {report.author}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip
                      icon={<People />}
                      label={report.collaborators}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      icon={<History />}
                      label={`v${report.versions}`}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </Box>
                
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Modified {report.lastModified.toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Features Section */}
      <Box sx={{ mt: 6 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Editor Features
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Rich Text Editing
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><Edit /></ListItemIcon>
                    <ListItemText primary="WYSIWYG editor with formatting tools" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><Edit /></ListItemIcon>
                    <ListItemText primary="Tables, images, and multimedia support" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><Edit /></ListItemIcon>
                    <ListItemText primary="Custom styles and templates" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Collaboration
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><People /></ListItemIcon>
                    <ListItemText primary="Real-time multi-user editing" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><People /></ListItemIcon>
                    <ListItemText primary="Live cursors and selections" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><People /></ListItemIcon>
                    <ListItemText primary="Comments and suggestions" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Version Control
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><History /></ListItemIcon>
                    <ListItemText primary="Complete version history" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><History /></ListItemIcon>
                    <ListItemText primary="Compare versions side-by-side" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><History /></ListItemIcon>
                    <ListItemText primary="Rollback to any previous version" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Smart Features
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemIcon><Save /></ListItemIcon>
                    <ListItemText primary="Auto-save with visual indicators" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><Share /></ListItemIcon>
                    <ListItemText primary="Export to multiple formats" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon><Download /></ListItemIcon>
                    <ListItemText primary="Offline editing support" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Report Editor Dialog */}
      <Dialog
        open={editorOpen}
        onClose={handleCloseEditor}
        maxWidth={false}
        fullWidth
        PaperProps={{
          sx: {
            width: '100vw',
            height: '100vh',
            maxWidth: 'none',
            maxHeight: 'none',
            m: 0,
          },
        }}
      >
        {selectedReport && (
          <ReportEditor
            reportId={selectedReport.id}
            initialContent={mockInitialContent}
            onSave={handleSaveReport}
            onClose={handleCloseEditor}
            enableCollaboration={true}
            showVersionHistory={true}
          />
        )}
      </Dialog>

      {/* Create Report Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)}>
        <DialogTitle>Create New Report</DialogTitle>
        <DialogContent>
          <Typography>
            Create a new report with the NextGen editor. You'll have access to all collaborative
            features including real-time editing, version control, and auto-save.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateReport} variant="contained">
            Create Report
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default ReportEditorDemo;
