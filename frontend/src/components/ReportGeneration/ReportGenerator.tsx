import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Report Generator Component
 * Main component for initiating report generation with template and data selection
 */

import { useState } from "react";
  
import { Box, Stepper, Step, StepLabel, Button, Typography, Paper, Alert, CircularProgress } from "@mui/material";
  
import { Assignment, CloudUpload, Settings, PlayArrow } from "@mui/icons-material";

import { TemplateSelector } from "../TemplateSelection";

import { ExcelUploader, DataMappingInterface } from "../ExcelUpload";

import FormatSelector from './FormatSelector';

import GenerationProgress from './GenerationProgress';

interface ReportGeneratorProps {
  onReportGenerated?: (reportId: number) => void;
  
onCancel?: () => void;
}

const steps = [
  'Select Template',
  'Upload Data',
  'Map Fields',
  'Choose Formats',
  'Generate Report',
];

const ReportGenerator: React.FC<ReportGeneratorProps> = ({
  onReportGenerated,
  onCancel,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  
const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  
const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  
const [dataMappings, setDataMappings] = useState<any[]>([]);
  
const [selectedFormats, setSelectedFormats] = useState<string[]>(['pdf']);
  
const [generationTask, setGenerationTask] = useState<any>(null);
  
const [error, setError] = useState<string | null>(null);
  
const [loading, setLoading] = useState(false);

const handleNext = async () => {
    setError(null);

if (activeStep === steps.length - 1) {
      // Start generation
      await startGeneration();
    } else {
      setActiveStep((prevActiveStep: any) => prevActiveStep + 1);
    }
  };

const handleBack = () => {
    setActiveStep((prevActiveStep: any) => prevActiveStep - 1);
  };

const handleReset = () => {
    setActiveStep(0);
    
setSelectedTemplate(null);
    
setUploadedFiles([]);
    
setDataMappings([]);
    
setSelectedFormats(['pdf']);
    
setGenerationTask(null);
    
setError(null);
  };

const startGeneration = async () => {
    if (!selectedTemplate || uploadedFiles.length === 0) {
      setError('Please complete all required steps');
      
return;
    }

    setLoading(true);

try {
      const response = await fetch('/api/v1/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token') || localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({
          template_id: selectedTemplate.id,
          data_source: {
            file_id: uploadedFiles[0].file_id,
            mappings: dataMappings,
          },
          output_formats: selectedFormats,
          report_name: `${selectedTemplate.name} - ${new Date().toLocaleDateString()}`,
        }),
      });

if (!response.ok) {
        const errorData = await response.json();
        
throw Error(errorData.error || 'Generation failed');
      }

      const result = await response.json();

if (result.success) {
        setGenerationTask({
          task_id: result.task_id,
          report_id: result.report_id,
          status: 'started',
        });
        
setActiveStep(steps.length); // Move to progress step
      } else {
        throw Error(result.error || 'Generation failed');
      }
    } catch (err: any) {
      console.error('Generation error:', err);
      
setError(err.message || 'Failed to start report generation');
    } finally {
      setLoading(false);
    }
  };

const handleGenerationComplete = (reportId: number) => {
    onReportGenerated?.(reportId);
  };

const canProceed = () => {
    switch (activeStep) {
      case 0:
        return selectedTemplate !== null;
      
case 1:
        return uploadedFiles.length > 0;
      
case 2:
        return dataMappings.length > 0;
      
case 3:
        return selectedFormats.length > 0;
      
default:
        return true;
    }
  };

const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <TemplateSelector
            onTemplateSelect={setSelectedTemplate}
            selectedTemplateId={selectedTemplate?.id}
            showPreview={true}
          />
        );

case 1:
        return (
          <ExcelUploader
            onFileUploaded={(file: any) => setUploadedFiles([file])}
            onFileRemoved={() => setUploadedFiles([])}
            uploadedFiles={uploadedFiles}
            maxFiles={1}
          />
        );

case 2:
        return uploadedFiles.length > 0 && selectedTemplate ? (
          <DataMappingInterface
            excelColumns={uploadedFiles[0].columns?.map((name: string) => ({
              name,
              type: 'string', // Would be determined from actual data
              sample_values: [],
              null_count: 0,
              unique_count: 0,
            })) || []}
            templateVariables={selectedTemplate.variables || []}
            onMappingChange={setDataMappings}
            initialMappings={dataMappings}
          />
        ) : (
          <Alert severity="info">
            Please complete the previous steps first.
          </Alert>
        );

case 3:
        return (
          <FormatSelector
            selectedFormats={selectedFormats}
            onFormatsChange={setSelectedFormats}
            template={selectedTemplate}
          />
        );

case 4:
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" gutterBottom>
              Ready to Generate Report
            </Typography>
            
            <Paper sx={{ p: 3, mt: 2, textAlign: 'left' }}>
              <Typography variant="subtitle1" gutterBottom>
                Generation Summary:
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Template:</strong> {selectedTemplate?.name}
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Data Source:</strong> {uploadedFiles[0]?.filename}
              </Typography>
              
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Mappings:</strong> {dataMappings.length} field mappings
              </Typography>
              
              <Typography variant="body2">
                <strong>Output Formats:</strong> {selectedFormats.join(', ').toUpperCase()}
              </Typography>
            </Paper>
          </Box>
        );

default:
        return null;
    }
  };

  // Show generation progress if task is running
  if (generationTask) {
    return (
      <GenerationProgress
        taskId={generationTask.task_id}
        reportId={generationTask.report_id}
        onComplete={handleGenerationComplete}
        onCancel={onCancel}
      />
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Stepper */}
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label, index) => (
          <Step key={label}>
            <StepLabel
              icon={
                index === 0 ? <Assignment /> :
                index === 1 ? <CloudUpload /> :
                index === 2 ? <Settings /> :
                index === 3 ? <Settings /> :
                <PlayArrow />
              }
            >
              {label}
            </StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Step Content */}
      <Box sx={{ mb: 4, minHeight: '400px' }}>
        {getStepContent(activeStep)}
      </Box>

      {/* Navigation Buttons */}
      <Box sx={{ display: 'flex', flexDirection: 'row', pt: 2 }}>
        <Button
          color="inherit"
          disabled={activeStep === 0 || loading}
          onClick={handleBack}
          sx={{ mr: 1 }}
        >
          Back
        </Button>
        
        <Box sx={{ flex: '1 1 auto' }} />
        
        {onCancel && (
          <Button
            onClick={onCancel}
            disabled={loading}
            sx={{ mr: 1 }}
          >
            Cancel
          </Button>
        )}
        
        <Button
          onClick={handleNext}
          disabled={!canProceed() || loading}
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : undefined}
        >
          {loading ? 'Processing...' : 
           activeStep === steps.length - 1 ? 'Generate Report' : 'Next'}
        </Button>
      </Box>
    </Box>
  );
};

export default ReportGenerator;
