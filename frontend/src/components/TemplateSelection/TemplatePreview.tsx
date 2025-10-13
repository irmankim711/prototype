import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Template Preview Component
 * Modal dialog for previewing template details and content
 */

import { useState, useEffect } from "react";
  
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box, Chip, Divider, Tab, Tabs, Paper, List, ListItem, ListItemText, ListItemIcon, CircularProgress, Alert, IconButton, Tooltip } from "@mui/material";
  
import { Close, Visibility, Code, Assignment, GetApp, Share, Star, StarBorder, CheckCircle, TableChart, Assessment } from "@mui/icons-material";

import { templateService } from "../../services/templateService";

interface Template {
  id: number;
  
name: string;
  
description: string;
  
category: string;
  
template_type: string;
  
supports_excel: boolean;
  
usage_count: number;
  
last_used: string | null;
  
created_at: string;
  
creator_name: string;
  
preview_url?: string;
  
complexity: 'simple' | 'moderate' | 'complex';
  
tags: string[];
}

interface TemplatePreviewProps {
  template: Template;
  
open: boolean;
  
onClose: () => void;
  
onSelect: () => void;
  
showActions?: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  
index: number;
  
value: number;
}

export default function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`template-tabpanel-${index}`}
      aria-labelledby={`template-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const TemplatePreview: React.FC<TemplatePreviewProps> = ({
  template,
  open,
  onClose,
  onSelect,
  showActions = true,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  
const [templateDetails, setTemplateDetails] = useState<any>(null);
  
const [templateVariables, setTemplateVariables] = useState<any[]>([]);
  
const [previewContent, setPreviewContent] = useState<string>('');
  
const [loading, setLoading] = useState(false);
  
const [error, setError] = useState<string | null>(null);
  
const [isFavorite, setIsFavorite] = useState(false);

useEffect(() => {
    if (open && template) {
      loadTemplateDetails();
    }
  }, [open, template]);

const loadTemplateDetails = async () => {
    try {
      setLoading(true);
      
setError(null);

      // Load template details
      const detailsResponse = await templateService.getTemplate(template.id);
      
if (detailsResponse.success) {
        setTemplateDetails(detailsResponse.template);
      }

      // Load template variables
      const variablesResponse = await templateService.getTemplateVariables(template.id);
      
if (variablesResponse.success) {
        setTemplateVariables(variablesResponse.variables);
      }

      // Generate preview
      const previewResponse = await templateService.generatePreview(template.id);
      
if (previewResponse.success) {
        setPreviewContent(previewResponse.rendered_content);
      }

    } catch (err) {
      console.error('Error loading template details:', err);
      
setError('Failed to load template details');
    } finally {
      setLoading(false);
    }
  };

const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

const handleFavoriteToggle = () => {
    setIsFavorite(!isFavorite);
    // In a real app, this would call an API to update favorites
  };

const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'business':
        return <Assessment />;
      
case 'financial':
        return <TableChart />;
      
default:
        return <Assessment />;
    }
  };

const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple':
        return 'success';
      
case 'moderate':
        return 'warning';
      
case 'complex':
        return 'error';
      
default:
        return 'default';
    }
  };

return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 1,
                background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
              }}
            >
              {getCategoryIcon(template.category)}
            </Box>
            
            <Box>
              <Typography variant="h6" component="h2">
                {template.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {template.category} • {template.template_type}
              </Typography>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {showActions && (
              <>
                <Tooltip title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}>
                  <IconButton onClick={handleFavoriteToggle}>
                    {isFavorite ? <Star color="warning" /> : <StarBorder />}
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Share template">
                  <IconButton>
                    <Share />
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Download template">
                  <IconButton>
                    <GetApp />
                  </IconButton>
                </Tooltip>
              </>
            )}
            
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress />
          </Box>
        ) : error ? (
          <Box sx={{ p: 3 }}>
            <Alert severity="error">{error}</Alert>
          </Box>
        ) : (
          <>
            {/* Tabs */}
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab icon={<Visibility />} label="Overview" />
                <Tab icon={<Assignment />} label="Variables" />
                <Tab icon={<Code />} label="Preview" />
              </Tabs>
            </Box>

            {/* Overview Tab */}
            <TabPanel value={activeTab} index={0}>
              <Box sx={{ display: 'flex', gap: 3 }}>
                {/* Left Column - Details */}
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {template.description}
                  </Typography>

                  <Typography variant="h6" gutterBottom>
                    Features
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText primary="Professional formatting" />
                    </ListItem>
                    
                    {template.supports_excel && (
                      <ListItem>
                        <ListItemIcon>
                          <CheckCircle color="success" />
                        </ListItemIcon>
                        <ListItemText primary="Excel data integration" />
                      </ListItem>
                    )}
                    
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText primary="Customizable variables" />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircle color="success" />
                      </ListItemIcon>
                      <ListItemText primary="Multiple export formats" />
                    </ListItem>
                  </List>

                  <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                    Tags
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {template.tags.map((tag, index) => (
                      <Chip
                        key={index}
                        label={tag}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>

                {/* Right Column - Metadata */}
                <Box sx={{ width: 300 }}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Template Info
                    </Typography>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Complexity
                      </Typography>
                      <Chip
                        label={template.complexity}
                        size="small"
                        color={getComplexityColor(template.complexity) as any}
                        sx={{ mt: 0.5 }}
                      />
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Usage Statistics
                      </Typography>
                      <Typography variant="body1">
                        Used {template.usage_count} times
                      </Typography>
                      {template.last_used && (
                        <Typography variant="body2" color="text.secondary">
                          Last used: {new Date(template.last_used).toLocaleDateString()}
                        </Typography>
                      )}
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Created By
                      </Typography>
                      <Typography variant="body1">
                        {template.creator_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(template.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Variables
                      </Typography>
                      <Typography variant="body1">
                        {templateVariables.length} variables
                      </Typography>
                    </Box>

                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Supported Formats
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
                        <Chip label="PDF" size="small" />
                        <Chip label="DOCX" size="small" />
                        <Chip label="HTML" size="small" />
                      </Box>
                    </Box>
                  </Paper>
                </Box>
              </Box>
            </TabPanel>

            {/* Variables Tab */}
            <TabPanel value={activeTab} index={1}>
              <Typography variant="h6" gutterBottom>
                Template Variables ({templateVariables.length})
              </Typography>
              
              {templateVariables.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  This template has no configurable variables.
                </Typography>
              ) : (
                <List>
                  {templateVariables.map((variable, index) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemText
                          primary={variable.name}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                Type: {variable.type} {variable.required && '(Required)'}
                              </Typography>
                              {variable.description && (
                                <Typography variant="body2" color="text.secondary">
                                  {variable.description}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                        <Chip
                          label={variable.type}
                          size="small"
                          variant="outlined"
                          color={variable.required ? 'error' : 'default'}
                        />
                      </ListItem>
                      {index < templateVariables.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </TabPanel>

            {/* Preview Tab */}
            <TabPanel value={activeTab} index={2}>
              <Typography variant="h6" gutterBottom>
                Template Preview
              </Typography>
              
              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  maxHeight: '400px',
                  overflow: 'auto',
                  bgcolor: 'grey.50',
                }}
              >
                {previewContent ? (
                  <Box
                    dangerouslySetInnerHTML={{ __html: previewContent }}
                    sx={{
                      '& h1, & h2, & h3': { mt: 2, mb: 1 },
                      '& p': { mb: 1 },
                      '& ul, & ol': { pl: 2 },
                    }}
                  />
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Preview not available
                  </Typography>
                )}
              </Paper>
            </TabPanel>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={onSelect}
          startIcon={<CheckCircle />}
        >
          Select Template
        </Button>
      </DialogActions>
    </Dialog>
  );
};

