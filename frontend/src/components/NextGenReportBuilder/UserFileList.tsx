import React, { useState, useEffect } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Typography,
  Button,
  TextField,
  InputAdornment,
  Chip,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  TableChart,
  CheckCircle,
  Search,
  Refresh,
  Info
} from '@mui/icons-material';
import { nextGenReportService } from '../../services/nextGenReportService';

interface UploadedFile {
  id: string;
  fileId: string;
  name: string;
  originalFilename: string;
  filePath: string;
  fileSize: number;
  status: string;
  uploadedAt: string;
  tablesCount: number;
  totalRows: number;
  totalColumns: number;
  sheetsProcessed: number;
}

interface UserFileListProps {
  onFileSelect: (fileIds: string[]) => void;
  multiSelect?: boolean;
  maxSelection?: number;
}

const UserFileList: React.FC<UserFileListProps> = ({
  onFileSelect,
  multiSelect = false,
  maxSelection = 10
}) => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [totalFiles, setTotalFiles] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    loadUserFiles();
  }, [page, searchQuery]);

  const loadUserFiles = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await nextGenReportService.getUserExcelFiles(page, 20, searchQuery);

      if (response.success) {
        setFiles(response.files);
        setTotalFiles(response.pagination.totalFiles);
        setHasMore(response.pagination.hasNext);
      } else {
        setError('Failed to load files');
      }
    } catch (err: any) {
      console.error('Failed to load files:', err);
      setError(err.message || 'Failed to load Excel files');
    } finally {
      setLoading(false);
    }
  };

  const toggleFileSelection = (fileId: string) => {
    if (multiSelect) {
      setSelectedFileIds(prev => {
        if (prev.includes(fileId)) {
          // Deselect
          return prev.filter(id => id !== fileId);
        } else {
          // Select (check max limit)
          if (prev.length >= maxSelection) {
            setError(`Maximum ${maxSelection} files can be selected`);
            return prev;
          }
          return [...prev, fileId];
        }
      });
    } else {
      // Single select mode
      setSelectedFileIds([fileId]);
    }
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setPage(1); // Reset to first page on search
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString();
  };

  const handleGenerateReport = () => {
    if (selectedFileIds.length > 0) {
      onFileSelect(selectedFileIds);
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6">
          Your Excel Files
          {totalFiles > 0 && (
            <Chip
              label={`${totalFiles} file${totalFiles !== 1 ? 's' : ''}`}
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </Typography>
        <Tooltip title="Refresh file list">
          <IconButton onClick={loadUserFiles} size="small">
            <Refresh />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Search Bar */}
      <TextField
        fullWidth
        placeholder="Search files by name..."
        value={searchQuery}
        onChange={(e) => handleSearch(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 2 }}
      />

      {/* Multi-select info */}
      {multiSelect && (
        <Alert severity="info" icon={<Info />} sx={{ mb: 2 }}>
          {selectedFileIds.length === 0
            ? `Select up to ${maxSelection} files to generate a combined report`
            : `${selectedFileIds.length} of ${maxSelection} files selected`}
        </Alert>
      )}

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && files.length === 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Empty State */}
      {!loading && files.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <TableChart sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="body1" color="text.secondary">
            {searchQuery ? 'No files found matching your search' : 'No Excel files uploaded yet'}
          </Typography>
          {searchQuery && (
            <Button onClick={() => setSearchQuery('')} sx={{ mt: 2 }}>
              Clear Search
            </Button>
          )}
        </Paper>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Paper sx={{ maxHeight: 400, overflow: 'auto' }}>
          <List>
            {files.map((file) => {
              const isSelected = selectedFileIds.includes(file.id);

              return (
                <ListItem
                  key={file.id}
                  button
                  selected={isSelected}
                  onClick={() => toggleFileSelection(file.id)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'primary.light',
                      '&:hover': {
                        backgroundColor: 'primary.light',
                      },
                    },
                  }}
                >
                  {multiSelect && (
                    <ListItemIcon>
                      <Checkbox
                        edge="start"
                        checked={isSelected}
                        tabIndex={-1}
                        disableRipple
                      />
                    </ListItemIcon>
                  )}

                  <ListItemIcon>
                    <TableChart color={isSelected ? 'primary' : 'action'} />
                  </ListItemIcon>

                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1">{file.name}</Typography>
                        {isSelected && <CheckCircle color="primary" fontSize="small" />}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          {file.totalRows} rows • {file.totalColumns} columns • {formatFileSize(file.fileSize)}
                        </Typography>
                        <br />
                        <Typography variant="caption" color="text.secondary">
                          Uploaded {formatDate(file.uploadedAt)}
                        </Typography>
                        {file.status !== 'completed' && (
                          <Chip
                            label={file.status}
                            size="small"
                            color="warning"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              );
            })}
          </List>
        </Paper>
      )}

      {/* Pagination */}
      {hasMore && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Button onClick={() => setPage(p => p + 1)} disabled={loading}>
            Load More
          </Button>
        </Box>
      )}

      {/* Generate Report Button */}
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          {selectedFileIds.length > 0 &&
            `${selectedFileIds.length} file${selectedFileIds.length !== 1 ? 's' : ''} selected`}
        </Typography>
        <Button
          variant="contained"
          size="large"
          onClick={handleGenerateReport}
          disabled={selectedFileIds.length === 0 || loading}
          startIcon={<TableChart />}
        >
          Generate Report from {selectedFileIds.length} File{selectedFileIds.length !== 1 ? 's' : ''}
        </Button>
      </Box>
    </Box>
  );
};

export default UserFileList;
