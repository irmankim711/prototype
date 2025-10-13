import React from 'react';
/**
 * Real-Time Report Generation Progress Tracker
 * Provides live updates during report generation with progress indicators
 */

import { useState, useEffect } from "react";
  
import { Dialog, DialogTitle, DialogContent, DialogActions, Box, Typography, LinearProgress, CircularProgress, Button, Alert, Stepper, Step, StepLabel, StepContent, Card, CardContent, Chip, IconButton, Collapse } from "@mui/material";
  
import { Close, CheckCircle, Error, Refresh, Visibility, Download, ExpandMore, ExpandLess } from "@mui/icons-material";

export interface GenerationStep {
  id: string;
  
label: string;
  
status: 'pending' | 'in_progress' | 'completed' | 'error';
  
startTime?: Date;
  
endTime?: Date;
  
progress?: number;
  
message?: string;
  
error?: string;
}

export interface ReportGenerationState {
  status: 'idle' | 'generating' | 'completed' | 'error';
  
currentStep: number;
  
steps: GenerationStep[];
  
progress: number;
  
estimatedTimeRemaining?: number;
  
startTime?: Date;
  
endTime?: Date;
  
reportId?: string;
  
previewUrl?: string;
  
downloadUrls?: {
    pdf?: string;
    
docx?: string;
    
excel?: string,
  };
  
error?: string;
}

interface ReportGenerationTrackerProps {
  open: boolean;
  
onClose: () => void;
  
generationState: ReportGenerationState;
  
onPreview?: (reportId: string) => void;
  
onDownload?: (reportId: string, format: 'pdf' | 'docx' | 'excel') => void;
  
onSaveToHistory?: (reportId: string) => void;
  
onRetry?: () => void;
  
allowClose?: boolean;
  
autoPreviewOnComplete?: boolean;
}

const ReportGenerationTracker: React.FC<ReportGenerationTrackerProps> = ({
  open,
  onClose,
  generationState,
  onPreview,
  onDownload,
  onSaveToHistory,
  onRetry,
  allowClose = true,
  autoPreviewOnComplete = true,
}) => {
  const [showDetails, setShowDetails] = useState(false);
  
const [timeElapsed, setTimeElapsed] = useState(0);

  // Update elapsed time
  useEffect(() => {
    if (generationState.status === 'generating' && generationState.startTime) {
      const interval = setInterval(() => {
        const elapsed = Date.now() - generationState.startTime!.getTime();
        
setTimeElapsed(elapsed);
      }, 1000);

return () => clearInterval(interval);
    }
  }, [generationState.status, generationState.startTime]);

  // Auto-trigger preview when generation completes
  useEffect(() => {
    if (
      autoPreviewOnComplete &&
      generationState.status === 'completed' &&
      generationState.reportId &&
      onPreview
    ) {
      // Small delay to ensure UI updates are visible
      setTimeout(() => {
        onPreview(generationState.reportId!);
      }, 1000);
    }
  }, [
    generationState.status,
    generationState.reportId,
    onPreview,
    autoPreviewOnComplete,
  ]);

const formatTime = (milliseconds: number): string => {
    const seconds = Math.floor(milliseconds / 1000);
    
const minutes = Math.floor(seconds / 60);
    
const remainingSeconds = seconds % 60;

if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

const getStatusIcon = (step: GenerationStep) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle color="success" />;
      
case 'error':
        return <Error color="error" />;
      
case 'in_progress':
        return <CircularProgress size={20} />;
      
default:
        return null;
    }
  };

  const getStatusColor =  (status: ReportGenerationState['status']) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      case 'generating':
        return 'info';
      case 'idle':
      default:
        return 'default';
    }
  };

const canClose = allowClose || generationState.status !== 'generating';

return (
    <Dialog
      open={open}
      onClose={canClose ? onClose : undefined}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown={!canClose}
      PaperProps={{
        sx: { minHeight: 400, maxHeight: '80vh' },
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          pb: 1,
        }}
      >
        <Box>
          <Typography variant="h6">
            {generationState.status === 'generating' ? 'Generating Report...' :
             generationState.status === 'completed' ? 'Report Generated Successfully!' :
             generationState.status === 'error' ? 'Report Generation Failed' :
             'Report Generation'}
          </Typography>
          
          {generationState.status === 'generating' && (
            <Box display="flex" alignItems="center" gap={1} mt={0.5}>
              <Typography variant="caption" color="text.secondary">
                Elapsed: {formatTime(timeElapsed)}
              </Typography>
              {generationState.estimatedTimeRemaining && (
                <>
                  <Typography variant="caption" color="text.secondary">•</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Est. remaining: {formatTime(generationState.estimatedTimeRemaining)}
                  </Typography>
                </>
              )}
            </Box>
          )}
        </Box>

        <Box display="flex" alignItems="center" gap={1}>
          <Chip
            label={generationState.status}
            size="small"
            color={getStatusColor(generationState.status) as any}
            variant={generationState.status === 'generating' ? 'filled' : 'outlined'}
          />
          
          {canClose && (
            <IconButton size="small" onClick={onClose}>
              <Close />
            </IconButton>
          )}
        </Box>
      </DialogTitle>

      <DialogContent>
        {/* Overall Progress */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="between" mb={2}>
              <Typography variant="subtitle1" fontWeight="semibold">
                Overall Progress
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {Math.round(generationState.progress)}%
              </Typography>
            </Box>
            
            <LinearProgress
              variant="determinate"
              value={generationState.progress}
              sx={{ height: 8, borderRadius: 4, mb: 2 }}
              color={
                generationState.status === 'error' ? 'error' :
                generationState.status === 'completed' ? 'success' : 'primary'
              }
            />

            {generationState.status === 'generating' && (
              <Typography variant="body2" color="text.secondary">
                Step {generationState.currentStep + 1} of {generationState.steps.length}
              </Typography>
            )}
          </CardContent>
        </Card>

        {/* Generation Steps */}
        <Box mb={3}>
          <Box display="flex" alignItems="center" justifyContent="between" mb={2}>
            <Typography variant="subtitle1" fontWeight="semibold">
              Generation Steps
            </Typography>
            <IconButton
              size="small"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? <ExpandLess /> : <ExpandMore />}
            </IconButton>
          </Box>

          <Stepper 
            activeStep={generationState.currentStep} 
            orientation="vertical"
            sx={{ pl: 0 }}
          >
            {generationState.steps.map((step, index) => (
              <Step key={step.id}>
                <StepLabel
                  icon={getStatusIcon(step)}
                  error={step.status === 'error'}
                >
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body2" fontWeight="medium">
                      {step.label}
                    </Typography>
                    {step.progress !== undefined && step.status === 'in_progress' && (
                      <Typography variant="caption" color="text.secondary">
                        ({Math.round(step.progress)}%)
                      </Typography>
                    )}
                  </Box>
                </StepLabel>
                
                <Collapse in={showDetails}>
                  <StepContent>
                    <Box pl={2}>
                      {step.message && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {step.message}
                        </Typography>
                      )}
                      
                      {step.error && (
                        <Alert severity="error" sx={{ mt: 1 }}>
                          {step.error}
                        </Alert>
                      )}
                      
                      {step.startTime && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          Started: {step.startTime.toLocaleTimeString()}
                          {step.endTime && ` • Completed: ${step.endTime.toLocaleTimeString()}`}
                        </Typography>
                      )}
                    </Box>
                  </StepContent>
                </Collapse>
              </Step>
            ))}
          </Stepper>
        </Box>

        {/* Error Display */}
        {generationState.status === 'error' && generationState.error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2" fontWeight="medium" gutterBottom>
              Generation Failed
            </Typography>
            <Typography variant="body2">
              {generationState.error}
            </Typography>
          </Alert>
        )}

        {/* Success State with Actions */}
        {generationState.status === 'completed' && (
          <Card sx={{ bgcolor: 'success.50', border: 1, borderColor: 'success.200' }}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <CheckCircle color="success" />
                <Typography variant="subtitle1" fontWeight="semibold" color="success.main">
                  Report Generated Successfully!
                </Typography>
              </Box>
              
              <Typography variant="body2" color="text.secondary" mb={2}>
                Your report has been generated and is ready for preview or download.
                Generated in {generationState.endTime && generationState.startTime ? 
                  formatTime(generationState.endTime.getTime() - generationState.startTime.getTime()) : 
                  'unknown time'}.
              </Typography>

              <Box display="flex" gap={1} flexWrap="wrap">
                {onPreview && generationState.reportId && (
                  <Button
                    variant="contained"
                    startIcon={<Visibility />}
                    onClick={() => onPreview(generationState.reportId!)}
                    color="success"
                  >
                    Preview Report
                  </Button>
                )}
                
                {onDownload && generationState.reportId && (
                  <Button
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={() => onDownload(generationState.reportId!, 'pdf')}
                  >
                    Download PDF
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        {generationState.status === 'error' && onRetry && (
          <Button
            startIcon={<Refresh />}
            onClick={onRetry}
            color="primary"
          >
            Retry Generation
          </Button>
        )}
        
        {generationState.status === 'completed' && onSaveToHistory && generationState.reportId && (
          <Button
            onClick={() => onSaveToHistory(generationState.reportId!)}
            color="primary"
          >
            Save to History
          </Button>
        )}
        
        <Button onClick={onClose} disabled={!canClose}>
          {generationState.status === 'completed' ? 'Close' : 'Cancel'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ReportGenerationTracker;
