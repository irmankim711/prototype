import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
  Chip,
  Divider,
  Alert
} from '@mui/material';
import { Close, Edit, Download, ContentCopy, CheckCircle } from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Template {
  id: string;
  name: string;
  type: 'latex' | 'jinja2' | 'docx';
  description: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

interface TemplateViewerProps {
  template: Template;
  onClose: () => void;
  onEdit: (template: Template) => void;
}

const TemplateViewer: React.FC<TemplateViewerProps> = ({
  template,
  onClose,
  onEdit
}) => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [copied, setCopied] = useState(false);

  const getLanguage = (type: string) => {
    switch (type) {
      case 'latex':
        return 'latex';
      case 'jinja2':
        return 'jinja2';
      case 'docx':
        return 'xml';
      default:
        return 'text';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'latex':
        return theme.palette.primary.main;
      case 'jinja2':
        return theme.palette.secondary.main;
      case 'docx':
        return theme.palette.success.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const handleCopyContent = async () => {
    try {
      await navigator.clipboard.writeText(template.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy content:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([template.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${template.name}.${template.type}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const renderContent = () => {
    if (activeTab === 0) {
      // Formatted view
      return (
        <Box sx={{ mt: 2 }}>
          <SyntaxHighlighter
            language={getLanguage(template.type)}
            style={materialLight}
            customStyle={{
              margin: 0,
              borderRadius: theme.shape.borderRadius,
              fontSize: '0.875rem'
            }}
            showLineNumbers
            wrapLines
          >
            {template.content}
          </SyntaxHighlighter>
        </Box>
      );
    } else {
      // Raw view
      return (
        <Box sx={{ mt: 2 }}>
          <Paper
            sx={{
              p: 2,
              backgroundColor: theme.palette.grey[50],
              border: `1px solid ${theme.palette.grey[300]}`,
              borderRadius: theme.shape.borderRadius
            }}
          >
            <pre
              style={{
                margin: 0,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
              }}
            >
              {template.content}
            </pre>
          </Paper>
        </Box>
      );
    }
  };

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        zIndex: 1300,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2
      }}
      onClick={onClose}
    >
      <Paper
        sx={{
          width: '100%',
          maxWidth: '90vw',
          height: '90vh',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: `1px solid ${theme.palette.divider}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h5" component="h2">
              {template.name}
            </Typography>
            <Chip
              label={template.type.toUpperCase()}
              size="small"
              sx={{
                backgroundColor: getTypeColor(template.type),
                color: 'white',
                fontWeight: 'bold'
              }}
            />
          </Box>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Copy Content">
              <IconButton
                onClick={handleCopyContent}
                color={copied ? 'success' : 'primary'}
              >
                {copied ? <CheckCircle /> : <ContentCopy />}
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Download Template">
              <IconButton onClick={handleDownload} color="success">
                <Download />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Edit Template">
              <IconButton onClick={() => onEdit(template)} color="secondary">
                <Edit />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Close">
              <IconButton onClick={onClose} color="default">
                <Close />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Description */}
        <Box sx={{ p: 2, backgroundColor: theme.palette.grey[50] }}>
          <Typography variant="body2" color="text.secondary">
            {template.description}
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
            <Typography variant="caption" color="text.secondary">
              Created: {new Date(template.createdAt).toLocaleDateString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Updated: {new Date(template.updatedAt).toLocaleDateString()}
            </Typography>
          </Box>
        </Box>

        <Divider />

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            sx={{ px: 2 }}
          >
            <Tab label="Formatted View" />
            <Tab label="Raw View" />
          </Tabs>
        </Box>

        {/* Content */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
          {renderContent()}
        </Box>

        {/* Copy Success Alert */}
        {copied && (
          <Alert
            severity="success"
            sx={{
              position: 'absolute',
              bottom: 16,
              right: 16,
              zIndex: 1
            }}
          >
            Content copied to clipboard!
          </Alert>
        )}
      </Paper>
    </Box>
  );
};

export default TemplateViewer;
