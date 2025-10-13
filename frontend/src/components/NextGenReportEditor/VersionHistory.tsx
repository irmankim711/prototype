import React from 'react';
/**
 * Version History Component for NextGen Report Editor
 * Enhanced version with better UI and additional features
 */

import { useState, useEffect } from "react";
  
import { Box, Card, CardContent, Typography, Button, Chip, List, ListItem, ListItemText, ListItemSecondaryAction, Divider, Dialog, DialogTitle, DialogContent, DialogActions, Alert, CircularProgress, IconButton, Tooltip, Accordion, AccordionSummary, AccordionDetails, Grid, Avatar, Paper, TextField, InputAdornment } from "@mui/material";
  
import { History, Restore, Visibility, CompareArrows, ExpandMore, Schedule, Person, Edit, CheckCircle, Search, FilterList, Download, Share, Delete, MoreVert } from "@mui/icons-material";

import { formatDistanceToNow, format } from "date-fns";

import enhancedReportService from '../../services/enhancedReportService';

import type { ReportVersion, VersionComparison } from "../../services/enhancedReportService";

interface VersionHistoryProps {
  reportId: number;
  
onVersionSelect?: (version: ReportVersion) => void;
  
onVersionRestore?: (version: ReportVersion) => void;
  
showPreview?: boolean;
  
compact?: boolean;
}

interface ComparisonState {
  isOpen: boolean;
  
version1?: ReportVersion;
  
version2?: ReportVersion;
  
comparison?: VersionComparison;
  
loading: boolean;
}

const VersionHistory: React.FC<VersionHistoryProps> = ({
  reportId,
  onVersionSelect,
  onVersionRestore,
  showPreview = true,
  compact = false,
}) => {
  const [versions, setVersions] = useState<ReportVersion[]>([]);
  
const [loading, setLoading] = useState(true);
  
const [error, setError] = useState<string | null>(null);
  
const [selectedVersions, setSelectedVersions] = useState<Set<number>>(new Set());
  
const [searchTerm, setSearchTerm] = useState('');
  
const [viewMode, setViewMode] = useState<'list' | 'timeline'>('list');

const [comparison, setComparison] = useState<ComparisonState>({
    isOpen: false,
    loading: false,
  });

const [rollbackDialog, setRollbackDialog] = useState<{
    isOpen: boolean;
    
version?: ReportVersion;
  }>({ isOpen: false });

const [previewDialog, setPreviewDialog] = useState<{
    isOpen: boolean;
    
version?: ReportVersion;
  }>({ isOpen: false });

useEffect(() => {
    fetchVersions();
  }, [reportId]);

const fetchVersions = async () => {
    try {
      setLoading(true);
      
setError(null);
      
const data = await enhancedReportService.getReportVersions(reportId);
      
setVersions(data.versions);
    } catch (err) {
      console.error('Failed to fetch versions:', err);
      
setError('Failed to load version history');
    } finally {
      setLoading(false);
    }
  };

const handleVersionSelect = (version: ReportVersion) => {
    if (selectedVersions.size < 2) {
      const newSelected = new Set(selectedVersions);
      
if (newSelected.has(version.id)) {
        newSelected.delete(version.id);
      } else {
        newSelected.add(version.id);
      }
      setSelectedVersions(newSelected);
    }
  };

const handleCompareVersions = async () => {
    const versionIds = Array.from(selectedVersions);
    
if (versionIds.length !== 2) return;

setComparison({ isOpen: true, loading: true });

try {
      const [version1, version2] = await Promise.all([
        enhancedReportService.getSpecificVersion(reportId, versionIds[0]),
        enhancedReportService.getSpecificVersion(reportId, versionIds[1]),
      ]);

const comparisonResult = await enhancedReportService.compareVersions(
        reportId,
        versionIds[0],
        versionIds[1]
      );

setComparison({
        isOpen: true,
        version1,
        version2,
        comparison: comparisonResult,
        loading: false,
      });
    } catch (err) {
      console.error('Failed to compare versions:', err);
      
setComparison({ isOpen: false, loading: false });
      
setError('Failed to compare versions');
    }
  };

const handleRollback = async (version: ReportVersion) => {
    try {
      const newVersion = await enhancedReportService.rollbackToVersion(
        reportId,
        version.id
      );
      
await fetchVersions();
      
setRollbackDialog({ isOpen: false });
      
onVersionRestore?.(newVersion);
    } catch (err) {
      console.error('Failed to rollback:', err);
      
setError('Failed to rollback to selected version');
    }
  };

const handlePreview = async (version: ReportVersion) => {
    setPreviewDialog({ isOpen: true, version });
    
onVersionSelect?.(version);
  };

const filteredVersions = versions.filter(version =>
    version.change_summary?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    version.creator_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'any';
    
const kb = bytes / 1024;
    
return kb < 1024 ? `${kb.toFixed(1)} KB` : `${(kb / 1024).toFixed(1)} MB`;
  };

const getChangeTypeColor = (changeType: string) => {
    switch (changeType) {
      case 'added':
        return 'success';
      
case 'removed':
        return 'error';
      
case 'modified':
        return 'warning';
      
default:
        return 'default';
    }
  };

const getVersionIcon = (version: ReportVersion, index: number) => {
    if (version.is_current) return <CheckCircle color="primary" />;
    
if (index === 0 && !version.is_current) return <History color="secondary" />;
    
return <Edit color="action" />;
  };

if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" onClose={() => setError(null)}>
        {error}
      </Alert>
    );
  }

  const renderListView = () => (
    <List>
      {filteredVersions.map((version, index) => (
        <React.Fragment key={version.id}>
          <ListItem
            sx={{
              border: 1,
              borderColor: selectedVersions.has(version.id) ? 'primary.main' : 'grey.300',
              borderRadius: 1,
              mb: 1,
              backgroundColor: version.is_current ? 'action.selected' : 'background.paper',
              cursor: 'pointer',
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
            onClick={() => handleVersionSelect(version)}
          >
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                  <Typography variant="subtitle1" component="span">
                    Version {version.version_number}
                  </Typography>

                  {version.is_current && (
                    <Chip label="Current" size="small" color="primary" icon={<CheckCircle />} />
                  )}

                  {index === 0 && !version.is_current && (
                    <Chip label="Latest" size="small" color="secondary" variant="outlined" />
                  )}

                  <Chip
                    label={format(new Date(version.created_at), 'MMM dd, yyyy HH:mm')}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              }
              secondary={
                <Box sx={{ mt: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Avatar sx={{ width: 20, height: 20, fontSize: '0.75rem' }}>
                        {(version.creator_name || 'U')[0]}
                      </Avatar>
                      <Typography variant="body2">
                        {version.creator_name || 'any'}
                      </Typography>
                    </Box>

                    <Typography variant="body2" color="text.secondary">
                      {formatDistanceToNow(new Date(version.created_at), { addSuffix: true })}
                    </Typography>

                    <Typography variant="body2" color="text.secondary">
                      {formatFileSize(version.file_size)}
                    </Typography>
                  </Box>

                  {version.change_summary && (
                    <Typography variant="body2" color="text.secondary">
                      {version.change_summary}
                    </Typography>
                  )}
                </Box>
              }
            />

            <ListItemSecondaryAction>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {showPreview && (
                  <Tooltip title="Preview this version">
                    <IconButton
                      size="small"
                      onClick={(e: any) => {
                        e.stopPropagation();
                        
handlePreview(version);
                      }}
                    >
                      <Visibility />
                    </IconButton>
                  </Tooltip>
                )}

                {!version.is_current && (
                  <Tooltip title="Rollback to this version">
                    <IconButton
                      size="small"
                      onClick={(e: any) => {
                        e.stopPropagation();
                        
setRollbackDialog({ isOpen: true, version });
                      }}
                    >
                      <Restore />
                    </IconButton>
                  </Tooltip>
                )}

                <Tooltip title="More options">
                  <IconButton size="small">
                    <MoreVert />
                  </IconButton>
                </Tooltip>
              </Box>
            </ListItemSecondaryAction>
          </ListItem>
        </React.Fragment>
      ))}
    </List>
  );

const renderTimelineView = () => (
    <Box sx={{ position: 'relative', pl: 4 }}>
      {/* Timeline line */}
      <Box
        sx={{
          position: 'absolute',
          left: 16,
          top: 24,
          bottom: 0,
          width: 2,
          bgcolor: 'divider',
        }}
      />
      
      {filteredVersions.map((version, index) => (
        <Box key={version.id} sx={{ position: 'relative', mb: 3 }}>
          {/* Timeline dot */}
          <Box
            sx={{
              position: 'absolute',
              left: -20,
              top: 16,
              width: 40,
              height: 40,
              borderRadius: '50%',
              bgcolor: version.is_current ? 'primary.main' : 'grey.400',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              zIndex: 1,
            }}
          >
            {getVersionIcon(version, index)}
          </Box>
          
          {/* Timeline content */}
          <Paper
            elevation={1}
            sx={{
              p: 2,
              ml: 2,
              border: selectedVersions.has(version.id) ? 2 : 0,
              borderColor: 'primary.main',
              cursor: 'pointer',
              transition: 'all 0.2s',
              '&:hover': { 
                elevation: 2,
                transform: 'translateX(4px)',
              },
            }}
            onClick={() => handleVersionSelect(version)}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
              <Typography variant="h6" component="h3">
                Version {version.version_number}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {format(new Date(version.created_at), 'MMM dd, HH:mm')}
              </Typography>
            </Box>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              by {version.creator_name || 'any'} • {formatFileSize(version.file_size)}
            </Typography>
            
            {version.change_summary && (
              <Typography variant="body2" sx={{ mb: 2 }}>
                {version.change_summary}
              </Typography>
            )}
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              {version.is_current && (
                <Chip label="Current" size="small" color="primary" />
              )}
              {index === 0 && !version.is_current && (
                <Chip label="Latest" size="small" color="secondary" variant="outlined" />
              )}
            </Box>
          </Paper>
        </Box>
      ))}
    </Box>
  );

return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography
          variant={compact ? "subtitle1" : "h6"}
          component="h2"
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
        >
          <History />
          Version History ({filteredVersions.length})
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {selectedVersions.size === 2 && (
            <Button
              variant="contained"
              startIcon={<CompareArrows />}
              onClick={handleCompareVersions}
              size="small"
            >
              Compare
            </Button>
          )}
          
          <Button
            variant="outlined"
            startIcon={viewMode === 'list' ? <Schedule /> : <FilterList />}
            onClick={() => setViewMode(viewMode === 'list' ? 'timeline' : 'list')}
            size="small"
          >
            {viewMode === 'list' ? 'Timeline' : 'List'}
          </Button>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ mb: 2 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search versions by description or author..."
          value={searchTerm}
          onChange={(e: any) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Instructions */}
      {selectedVersions.size === 0 && !compact && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Select up to 2 versions to compare them, or click on a version to view details.
        </Alert>
      )}

      {/* Version List/Timeline */}
      {viewMode === 'list' ? renderListView() : renderTimelineView()}

      {/* Empty State */}
      {filteredVersions.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <History sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No versions found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {searchTerm ? 'Try adjusting your search terms.' : 'No version history available yet.'}
          </Typography>
        </Box>
      )}

      {/* Comparison Dialog */}
      <Dialog
        open={comparison.isOpen}
        onClose={() => setComparison({ isOpen: false, loading: false })}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Version Comparison
          {comparison.version1 && comparison.version2 && (
            <Typography variant="subtitle2" color="text.secondary">
              Version {comparison.version1.version_number} vs Version{' '}
              {comparison.version2.version_number}
            </Typography>
          )}
        </DialogTitle>

        <DialogContent>
          {comparison.loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : comparison.comparison ? (
            <Box>
              {/* Comparison Stats */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={3}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="success.main">
                        {comparison.comparison.stats.added}
                      </Typography>
                      <Typography variant="body2">Added</Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={3}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="error.main">
                        {comparison.comparison.stats.removed}
                      </Typography>
                      <Typography variant="body2">Removed</Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={3}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h6" color="warning.main">
                        {comparison.comparison.stats.modified}
                      </Typography>
                      <Typography variant="body2">Modified</Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={3}>
                  <Card>
                    <CardContent sx={{ textAlign: 'center' }}>
                      <Typography variant="h6">
                        {comparison.comparison.stats.total_changes}
                      </Typography>
                      <Typography variant="body2">Total Changes</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Detailed Changes */}
              {comparison.comparison.changes.length > 0 ? (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Detailed Changes
                  </Typography>

                  {comparison.comparison.changes.map((change, index) => (
                    <Accordion key={index}>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={change.type}
                            size="small"
                            color={getChangeTypeColor(change.type) as any}
                          />
                          <Typography variant="body2">{change.path}</Typography>
                        </Box>
                      </AccordionSummary>

                      <AccordionDetails>
                        {change.type === 'modified' && (
                          <Grid container spacing={2}>
                            <Grid item xs={6}>
                              <Typography variant="subtitle2" color="error">
                                Old Value:
                              </Typography>
                              <Typography
                                variant="body2"
                                component="pre"
                                sx={{ whiteSpace: 'pre-wrap', bgcolor: 'grey.100', p: 1, borderRadius: 1 }}
                              >
                                {JSON.stringify(change.old_value, null, 2)}
                              </Typography>
                            </Grid>
                            <Grid item xs={6}>
                              <Typography variant="subtitle2" color="success">
                                New Value:
                              </Typography>
                              <Typography
                                variant="body2"
                                component="pre"
                                sx={{ whiteSpace: 'pre-wrap', bgcolor: 'grey.100', p: 1, borderRadius: 1 }}
                              >
                                {JSON.stringify(change.new_value, null, 2)}
                              </Typography>
                            </Grid>
                          </Grid>
                        )}

                        {(change.type === 'added' || change.type === 'removed') && (
                          <Box>
                            <Typography variant="subtitle2">Value:</Typography>
                            <Typography
                              variant="body2"
                              component="pre"
                              sx={{ whiteSpace: 'pre-wrap', bgcolor: 'grey.100', p: 1, borderRadius: 1 }}
                            >
                              {JSON.stringify(change.value, null, 2)}
                            </Typography>
                          </Box>
                        )}
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </Box>
              ) : (
                <Alert severity="info">
                  No differences found between selected versions.
                </Alert>
              )}
            </Box>
          ) : null}
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setComparison({ isOpen: false, loading: false })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Rollback Confirmation Dialog */}
      <Dialog
        open={rollbackDialog.isOpen}
        onClose={() => setRollbackDialog({ isOpen: false })}
      >
        <DialogTitle>Confirm Rollback</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to rollback to Version{' '}
            {rollbackDialog.version?.version_number}?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will create a new version with the content from the selected version. The
            current version will be preserved in the history.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRollbackDialog({ isOpen: false })}>Cancel</Button>
          <Button
            onClick={() =>
              rollbackDialog.version && handleRollback(rollbackDialog.version)
            }
            variant="contained"
            color="primary"
          >
            Rollback
          </Button>
        </DialogActions>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog
        open={previewDialog.isOpen}
        onClose={() => setPreviewDialog({ isOpen: false })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Version {previewDialog.version?.version_number} Preview
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Created by {previewDialog.version?.creator_name} on{' '}
            {previewDialog.version && format(new Date(previewDialog.version.created_at), 'PPpp')}
          </Typography>
          
          {previewDialog.version?.change_summary && (
            <Alert severity="info" sx={{ mb: 2 }}>
              {previewDialog.version.change_summary}
            </Alert>
          )}
          
          <Box
            sx={{
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
              p: 2,
              maxHeight: '400px',
              overflow: 'auto',
            }}
          >
            <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
              {JSON.stringify(previewDialog.version?.content, null, 2)}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialog({ isOpen: false })}>Close</Button>
          {previewDialog.version && !previewDialog.version.is_current && (
            <Button
              onClick={() => {
                setPreviewDialog({ isOpen: false });
                
setRollbackDialog({ isOpen: true, version: previewDialog.version });
              }}
              variant="contained"
              startIcon={<Restore />}
            >
              Rollback to This Version
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default VersionHistory;
