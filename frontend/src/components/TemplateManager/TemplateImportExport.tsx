import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Chip,
  Divider
} from '@mui/material';
import { Upload, Download, Delete, CheckCircle, Error } from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import TemplateService from '../../services/templateService';
import { Template } from './TemplateManager';

interface TemplateImportExportProps {
  onTemplatesImported: (templates: Template[]) => void;
}

const TemplateImportExport: React.FC<TemplateImportExportProps> = ({
  onTemplatesImported
}) => {
  const theme = useTheme();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importedFiles, setImportedFiles] = useState<File[]>([]);
  const [importStatus, setImportStatus] = useState<{
    success: string[];
    errors: string[];
  }>({ success: [], errors: [] });
  const [isImporting, setIsImporting] = useState(false);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setImportedFiles(files);
    setImportStatus({ success: [], errors: [] });
  };

  const handleImport = async () => {
    if (importedFiles.length === 0) return;

    setIsImporting(true);
    try {
      const templates = await TemplateService.importTemplatesFromFiles(importedFiles);
      
      const successFiles = importedFiles.map(f => f.name);
      setImportStatus({
        success: successFiles,
        errors: []
      });

      onTemplatesImported(templates);
      setImportedFiles([]);
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      setImportStatus({
        success: [],
        errors: ['Failed to import templates. Please try again.']
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleExportAll = async () => {
    try {
      await TemplateService.exportAllTemplates();
    } catch (error) {
      console.error('Error exporting templates:', error);
    }
  };

  const removeFile = (fileName: string) => {
    setImportedFiles(importedFiles.filter(f => f.name !== fileName));
  };

  const getFileTypeColor = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'tex':
        return theme.palette.primary.main;
      case 'jinja':
      case 'jinja2':
        return theme.palette.secondary.main;
      case 'docx':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getFileTypeLabel = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'tex':
        return 'LaTeX';
      case 'jinja':
      case 'jinja2':
        return 'Jinja2';
      case 'docx':
        return 'DOCX';
      default:
        return 'Unknown';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Template Import/Export
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Import Templates
        </Typography>
        
        <Box sx={{ mb: 2 }}>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".tex,.jinja,.jinja2,.docx,.txt"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          
          <Button
            variant="outlined"
            startIcon={<Upload />}
            onClick={() => fileInputRef.current?.click()}
            sx={{ mr: 2 }}
          >
            Select Files
          </Button>
          
          {importedFiles.length > 0 && (
            <Button
              variant="contained"
              onClick={handleImport}
              disabled={isImporting}
              startIcon={<Upload />}
            >
              {isImporting ? 'Importing...' : `Import ${importedFiles.length} Template(s)`}
            </Button>
          )}
        </Box>

        {importedFiles.length > 0 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Selected Files ({importedFiles.length}):
            </Typography>
            <List dense>
              {importedFiles.map((file, index) => (
                <ListItem key={index} sx={{ border: `1px solid ${theme.palette.divider}`, mb: 1, borderRadius: 1 }}>
                  <ListItemText
                    primary={file.name}
                    secondary={`Size: ${(file.size / 1024).toFixed(1)} KB`}
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={getFileTypeLabel(file.name)}
                      size="small"
                      sx={{
                        backgroundColor: getFileTypeColor(file.name),
                        color: 'white',
                        mr: 1
                      }}
                    />
                    <Tooltip title="Remove File">
                      <IconButton
                        edge="end"
                        onClick={() => removeFile(file.name)}
                        size="small"
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {importStatus.success.length > 0 && (
          <Alert severity="success" sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CheckCircle />
              <Typography variant="body2">
                Successfully imported {importStatus.success.length} template(s):
              </Typography>
            </Box>
            <List dense sx={{ mt: 1 }}>
              {importStatus.success.map((fileName, index) => (
                <ListItem key={index} sx={{ py: 0 }}>
                  <ListItemText
                    primary={fileName}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>
          </Alert>
        )}

        {importStatus.errors.length > 0 && (
          <Alert severity="error" sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Error />
              <Typography variant="body2">
                Import errors:
              </Typography>
            </Box>
            <List dense sx={{ mt: 1 }}>
              {importStatus.errors.map((error, index) => (
                <ListItem key={index} sx={{ py: 0 }}>
                  <ListItemText
                    primary={error}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>
          </Alert>
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Export Templates
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<Download />}
            onClick={handleExportAll}
            color="primary"
          >
            Export All Templates
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={() => {
              // This would open a dialog to select specific templates
              alert('Select specific templates feature coming soon!');
            }}
          >
            Export Selected Templates
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Templates will be exported as individual files in their native format.
        </Typography>
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Supported File Types
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            label="LaTeX (.tex)"
            color="primary"
            variant="outlined"
          />
          <Chip
            label="Jinja2 (.jinja, .jinja2)"
            color="secondary"
            variant="outlined"
          />
          <Chip
            label="DOCX (.docx)"
            color="success"
            variant="outlined"
          />
          <Chip
            label="Text (.txt)"
            color="default"
            variant="outlined"
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default TemplateImportExport;
