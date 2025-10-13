/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Report Generation State Management Hook
 * Manages the entire report generation lifecycle with real-time updates
 */

import { useState, useCallback, useRef } from "react";

import { nextGenReportService } from "../services/nextGenReportService";

import { reportService } from "../services/reportService";

import type { ReportGenerationState, GenerationStep } from '../components/NextGenReportBuilder/ReportGenerationTracker';

export interface ReportGenerationOptions {
  title: string;
  
templateId?: string;
  
dataSourceId?: string;
  
chartConfig?: any;
  
chartData?: any;
  
rawData?: any[];
  
metadata?: Record<string, any>;
  
onProgress?: (state: ReportGenerationState) => void;
  
onComplete?: (reportId: string, reportData: any) => void;
  
onError?: (error: string) => void;
}

const DEFAULT_STEPS: Omit<GenerationStep, 'startTime' | 'endTime'>[] = [
  {
    id: 'validation',
    label: 'Validating data and configuration',
    status: 'pending',
    message: 'Checking report parameters...',
  },
  {
    id: 'processing',
    label: 'Processing data and charts',
    status: 'pending',
    message: 'Generating visualizations...',
  },
  {
    id: 'template',
    label: 'Applying template and formatting',
    status: 'pending',
    message: 'Formatting document...',
  },
  {
    id: 'rendering',
    label: 'Rendering final report',
    status: 'pending',
    message: 'Creating final output...',
  },
  {
    id: 'finalization',
    label: 'Finalizing and preparing download',
    status: 'pending',
    message: 'Preparing report files...',
  },
];

export const useReportGeneration = () => {
  const [generationState, setGenerationState] = useState<ReportGenerationState>({
    status: 'idle',
    currentStep: 0,
    steps: DEFAULT_STEPS.map(step => ({ ...step })),
    progress: 0,
  });

const [isGenerating, setIsGenerating] = useState(false);
  
const [generatedReport, setGeneratedReport] = useState<any>(null);
  
const [showProgressTracker, setShowProgressTracker] = useState(false);
  
const [showImmediatePreview, setShowImmediatePreview] = useState(false);

  // Refs to track generation process
  const generationStartTime = useRef<Date | null>(null);
  
const progressTimer = useRef<NodeJS.Timeout | null>(null);
  
const abortController = useRef<AbortController | null>(null);

  // Update a specific step
  const updateStep = useCallback((stepId: string, updates: Partial<GenerationStep>) => {
    setGenerationState(prev => ({
      ...prev,
      steps: prev.steps.map(step =>
        step.id === stepId ? { ...step, ...updates } : step
      ),
    }));
  }, []);

  // Update overall progress
  const updateProgress = useCallback((progress: number, estimatedTimeRemaining?: number) => {
    setGenerationState(prev => ({
      ...prev,
      progress,
      estimatedTimeRemaining,
    }));
  }, []);

  // Simulate realistic progress updates
  const simulateProgress = useCallback((stepIndex: number, stepDuration: number) => {
    const startTime = Date.now();
    
const interval = 200; // Update every 200ms

    if (progressTimer.current) {
      clearInterval(progressTimer.current);
    }

    progressTimer.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      
const stepProgress = Math.min((elapsed / stepDuration) * 100, 100);
      
const overallProgress = ((stepIndex * 100) + stepProgress) / DEFAULT_STEPS.length;

const remaining = Math.max(0, stepDuration - elapsed);
      
const estimatedTotal = remaining + ((DEFAULT_STEPS.length - stepIndex - 1) * 3000);

updateProgress(overallProgress, estimatedTotal);

if (stepProgress >= 100) {
        if (progressTimer.current) {
          clearInterval(progressTimer.current);
          
progressTimer.current = null;
        }
      }
    }, interval);
  }, [updateProgress]);

  // Start generation process
  const startGeneration = useCallback(async (options: ReportGenerationOptions) => {
    try {
      console.log('🚀 Starting report generation:', options.title);

      // Reset state
      setIsGenerating(true);
      
setGeneratedReport(null);
      
setShowProgressTracker(true);
      
generationStartTime.current = new Date();
      
abortController.current = new AbortController();

const initialState: ReportGenerationState = {
        status: 'generating',
        currentStep: 0,
        steps: DEFAULT_STEPS.map(step => ({ ...step })),
        progress: 0,
        startTime: generationStartTime.current,
      };

setGenerationState(initialState);

if (options.onProgress) {
        options.onProgress(initialState);
      }

      // Step 1: Validation
      updateStep('validation', {
        status: 'in_progress',
        startTime: new Date(),
        message: 'Validating report configuration...',
      });
      
simulateProgress(0, 2000);

await new Promise(resolve => setTimeout(resolve, 2000));

updateStep('validation', {
        status: 'completed',
        endTime: new Date(),
        progress: 100,
        message: 'Configuration validated successfully',
      });

      // Step 2: Processing
      setGenerationState(prev => ({ ...prev, currentStep: 1 }));
      
updateStep('processing', {
        status: 'in_progress',
        startTime: new Date(),
        message: 'Processing data and generating charts...',
      });
      
simulateProgress(1, 4000);

      // Prepare report data
      const reportData = {
        title: options.title,
        templateId: options.templateId || '04- LAPORAN FU _ PUNCAK ALAM_final.docx',
        description: `Generated report: ${options.title}`,
        formId: options.dataSourceId || 'default-form',
        data: {
          chartData: options.chartData,
          chartConfig: options.chartConfig,
          rawData: options.rawData || [],
          dataSourceId: options.dataSourceId,
        },
        config: {
          template_used: options.templateId || '04- LAPORAN FU _ PUNCAK ALAM_final.docx',
          chart_type: options.chartConfig?.type || 'bar',
          title: options.title,
          theme: 'professional',
          include_chart: true,
          include_data_table: true,
          include_insights: true,
        },
        metadata: {
          ...options.metadata,
          generatedAt: new Date().toISOString(),
        },
      };

      // Generate actual report
      const response = await reportService.generateReport(reportData);

await new Promise(resolve => setTimeout(resolve, 2000));

updateStep('processing', {
        status: 'completed',
        endTime: new Date(),
        progress: 100,
        message: 'Data processed and charts generated',
      });

      // Step 3: Template Application
      setGenerationState(prev => ({ ...prev, currentStep: 2 }));
      
updateStep('template', {
        status: 'in_progress',
        startTime: new Date(),
        message: 'Applying template and formatting...',
      });
      
simulateProgress(2, 2500);

await new Promise(resolve => setTimeout(resolve, 2500));

updateStep('template', {
        status: 'completed',
        endTime: new Date(),
        progress: 100,
        message: 'Template applied successfully',
      });

      // Step 4: Rendering
      setGenerationState(prev => ({ ...prev, currentStep: 3 }));
      
updateStep('rendering', {
        status: 'in_progress',
        startTime: new Date(),
        message: 'Rendering final report...',
      });
      
simulateProgress(3, 3000);

await new Promise(resolve => setTimeout(resolve, 3000));

updateStep('rendering', {
        status: 'completed',
        endTime: new Date(),
        progress: 100,
        message: 'Report rendered successfully',
      });

      // Step 5: Finalization
      setGenerationState(prev => ({ ...prev, currentStep: 4 }));
      
updateStep('finalization', {
        status: 'in_progress',
        startTime: new Date(),
        message: 'Preparing final files...',
      });
      
simulateProgress(4, 1500);

await new Promise(resolve => setTimeout(resolve, 1500));

updateStep('finalization', {
        status: 'completed',
        endTime: new Date(),
        progress: 100,
        message: 'Report ready for preview',
      });

      // Complete generation
      const endTime = new Date();
      
const finalState: ReportGenerationState = {
        status: 'completed',
        currentStep: 4,
        steps: generationState.steps.map(step => 
          step.id === 'finalization' 
            ? { ...step, status: 'completed' as const, endTime, progress: 100 }
            : step
        ),
        progress: 100,
        startTime: generationStartTime.current,
        endTime,
        reportId: response.reportId || response.report_id || response.id,
        previewUrl: response.previewUrl || response.preview_url,
        downloadUrls: {
          pdf: response.pdfUrl || response.pdf_url,
          docx: response.docxUrl || response.docx_url,
          excel: response.excelUrl || response.excel_url,
        },
      };

setGenerationState(finalState);
      
setGeneratedReport(response);

if (progressTimer.current) {
        clearInterval(progressTimer.current);
        
progressTimer.current = null;
      }

      console.log('✅ Report generation completed:', response);

      // Notify completion
      if (options.onComplete) {
        options.onComplete(finalState.reportId!, response);
      }

      if (options.onProgress) {
        options.onProgress(finalState);
      }

      // Trigger immediate preview after brief delay
      setTimeout(() => {
        setShowImmediatePreview(true);
      }, 1000);

    } catch (error: any) {
      console.error('❌ Report generation failed:', error);

      // Update current step with error
      const currentStepId = DEFAULT_STEPS[generationState.currentStep]?.id;
      
if (currentStepId) {
        updateStep(currentStepId, {
          status: 'error',
          endTime: new Date(),
          error: error.message || 'Unknown error occurred',
        });
      }

      // Update overall state
      const errorState: ReportGenerationState = {
        ...generationState,
        status: 'error',
        error: error.message || 'Report generation failed',
        endTime: new Date(),
      };

setGenerationState(errorState);

if (progressTimer.current) {
        clearInterval(progressTimer.current);
        
progressTimer.current = null;
      }

      if (options.onError) {
        options.onError(error.message || 'Report generation failed');
      }

      if (options.onProgress) {
        options.onProgress(errorState);
      }
    } finally {
      setIsGenerating(false);
    }
  }, [generationState.currentStep, generationState.steps, simulateProgress, updateProgress, updateStep]);

  // Cancel generation
  const cancelGeneration = useCallback(() => {
    if (abortController.current) {
      abortController.current.abort();
    }

    if (progressTimer.current) {
      clearInterval(progressTimer.current);
      
progressTimer.current = null;
    }

    setGenerationState(prev => ({
      ...prev,
      status: 'idle',
      currentStep: 0,
      progress: 0,
      error: 'Generation cancelled by user',
    }));

setIsGenerating(false);
    
setShowProgressTracker(false);

console.log('🚫 Report generation cancelled');
  }, []);

  // Retry generation
  const retryGeneration = useCallback((options: ReportGenerationOptions) => {
    console.log('🔄 Retrying report generation');
    
    // Reset error state
    setGenerationState(prev => ({
      ...prev,
      status: 'idle',
      error: undefined,
      steps: DEFAULT_STEPS.map(step => ({ ...step, status: 'pending' as const })),
    }));

    // Start generation again
    startGeneration(options);
  }, [startGeneration]);

  // Close progress tracker
  const closeProgressTracker = useCallback(() => {
    setShowProgressTracker(false);
  }, []);

  // Close immediate preview
  const closeImmediatePreview = useCallback(() => {
    setShowImmediatePreview(false);
  }, []);

  // Set generated report manually (for external updates)
  const setGeneratedReportManually = useCallback((report: any) => {
    setGeneratedReport(report);
  }, []);

  // Reset all state
  const resetGeneration = useCallback(() => {
    if (progressTimer.current) {
      clearInterval(progressTimer.current);
      
progressTimer.current = null;
    }

    setGenerationState({
      status: 'idle',
      currentStep: 0,
      steps: DEFAULT_STEPS.map(step => ({ ...step })),
      progress: 0,
    });

setIsGenerating(false);
    
setGeneratedReport(null);
    
setShowProgressTracker(false);
    
setShowImmediatePreview(false);
    
generationStartTime.current = null;
    
abortController.current = null;
  }, []);

return {
    // State
    generationState,
    isGenerating,
    generatedReport,
    showProgressTracker,
    showImmediatePreview,
    
    // Actions
    startGeneration,
    cancelGeneration,
    retryGeneration,
    closeProgressTracker,
    closeImmediatePreview,
    resetGeneration,
    setGeneratedReport: setGeneratedReportManually,
    
    // Utils
    updateStep,
    updateProgress,
  };
};
