/**
 * Auto-Save Indicator Component
 * Visual indicator for save status with animations and user feedback
 */

import React from 'react';
  
import { Box, Chip, CircularProgress, Fade, Tooltip, Typography, Zoom } from "@mui/material";
  
import { Save, SaveOutlined, CheckCircle, Warning, Error, Schedule } from "@mui/icons-material";

import { formatDistanceToNow } from "date-fns";

interface AutoSaveIndicatorProps {
  isSaving: boolean;
  
isAutoSaving: boolean;
  
hasUnsavedChanges: boolean;
  
lastSaved: Date | null;
  
error?: string | null;
  
className?: string;
}

const AutoSaveIndicator: React.FC<AutoSaveIndicatorProps> = ({
  isSaving,
  isAutoSaving,
  hasUnsavedChanges,
  lastSaved,
  error,
  className,
}) => {
  const getSaveStatus = () => {
    if (error) {
      return {
        icon: <Error />,
        label: 'Save failed',
        color: 'error' as const,
        tooltip: error,
      };
    }

    if (isSaving) {
      return {
        icon: <CircularProgress size={16} />,
        label: 'Saving...',
        color: 'primary' as const,
        tooltip: 'Saving your changes',
      };
    }

    if (isAutoSaving) {
      return {
        icon: <CircularProgress size={16} />,
        label: 'Auto-saving...',
        color: 'secondary' as const,
        tooltip: 'Automatically saving your changes',
      };
    }

    if (hasUnsavedChanges) {
      return {
        icon: <SaveOutlined />,
        label: 'Unsaved changes',
        color: 'warning' as const,
        tooltip: 'You have unsaved changes. Press Ctrl+S to save manually.',
      };
    }

    if (lastSaved) {
      return {
        icon: <CheckCircle />,
        label: 'Saved',
        color: 'success' as const,
        tooltip: `Last saved ${formatDistanceToNow(lastSaved, { addSuffix: true })}`,
      };
    }

    return {
      icon: <Schedule />,
      label: 'Not saved',
      color: 'default' as const,
      tooltip: 'Document has not been saved yet',
    };
  };

const status = getSaveStatus();

return (
    <Box className={className} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Fade in={true} timeout={300}>
        <Tooltip title={status.tooltip} arrow>
          <Chip
            icon={status.icon}
            label={status.label}
            size="small"
            color={status.color}
            variant={hasUnsavedChanges || error ? 'filled' : 'outlined'}
            sx={{
              transition: 'all 0.3s ease',
              '& .MuiChip-icon': {
                transition: 'all 0.3s ease',
              },
            }}
          />
        </Tooltip>
      </Fade>

      {lastSaved && !hasUnsavedChanges && !isSaving && !isAutoSaving && !error && (
        <Zoom in={true} timeout={500}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              opacity: 0.7,
              transition: 'opacity 0.3s ease',
              '&:hover': {
                opacity: 1,
              },
            }}
          >
            {formatDistanceToNow(lastSaved, { addSuffix: true })}
          </Typography>
        </Zoom>
      )}
    </Box>
  );
};

export default AutoSaveIndicator;
