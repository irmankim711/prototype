/**
 * Next-Gen Report Builder Page
 * Integration wrapper that connects the UI with backend services
 */

import React, { useState, useEffect, useCallback } from "react";
import { Box, Alert, Snackbar, CircularProgress, Typography, Button } from "@mui/material";
import NextGenReportBuilder from "../../components/NextGenReportBuilder/NextGenReportBuilder";
import AccessibilityToolbar from "../../components/NextGenReportBuilder/AccessibilityHelpers";
import AuthGuard from "../../components/NextGenReportBuilder/AuthGuard";
import NextGenReportBuilderErrorBoundary from "../../components/NextGenReportBuilder/ErrorBoundary";
import { 
  nextGenReportService,
  type DataSource,
  type DataField,
  type ReportConfig,
  type ReportElement 
} from "../../services/nextGenReportService";
import { robustReportService } from "../../services/robustReportService";
import { Description } from "@mui/icons-material";

const NextGenReportBuilderPage: React.FC = () => {
  console.log('🎯 NextGenReportBuilderPage: Component initializing...');
  
  // State Management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Data State - Use types from the service
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedDataSource, setSelectedDataSource] = useState<DataSource | null>(null);
  const [dataFields, setDataFields] = useState<DataField[]>([]);
  
  // Report State - Use types from the service
  const [currentReport, setCurrentReport] = useState<ReportConfig | null>(null);
  const [reportElements, setReportElements] = useState<ReportElement[]>([]);
  
  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    console.log('🎯 NextGenReportBuilderPage: loadInitialData starting...');
    try {
      setLoading(true);
      setError(null);
      
      console.log('🎯 NextGenReportBuilderPage: About to call robustReportService.getDataSources()');
      // Load available data sources
      const sources = await robustReportService.getDataSources();
      console.log('✅ NextGenReportBuilderPage: Data sources received:', sources.length, 'items');
      setDataSources(sources);
      
      // Auto-select first available data source
      if (sources.length > 0) {
        const firstSource = sources[0];
        setSelectedDataSource(firstSource);
        
              // Load fields for the selected data source
      const fields = await nextGenReportService.getDataFields(firstSource.id);
      setDataFields(fields);
      }
      
      setLoading(false);
    } catch (error: any) {
      console.error('Error loading data sources:', error);
      
      // Provide more specific error messages
      let errorMessage = 'Failed to load data sources. ';
      
      if (error.message?.includes('Authentication required')) {
        errorMessage += 'Please log in to access this feature.';
      } else if (error.response?.status === 500) {
        errorMessage += 'Server error occurred. Please try again later.';
      } else if (error.response?.status === 401 || error.response?.status === 403) {
        errorMessage += 'Authentication failed. Please log in again.';
      } else {
        errorMessage += 'Using mock data for demonstration.';
      }
      
      setError(errorMessage);
      setLoading(false);
      
              // No fallback to mock data in production
        setError('Unable to load data sources. Please check your connection and try again.');
    }
  };

  // Handle data source selection
  const handleDataSourceChange = async (dataSourceId: string) => {
    try {
      const source = dataSources.find(ds => ds.id === dataSourceId);
      if (!source) return;
      
      setSelectedDataSource(source);
      setLoading(true);
      setError(null);
      
      const fields = await nextGenReportService.getDataFields(dataSourceId);
      setDataFields(fields);
      
      setLoading(false);
    } catch (error: any) {
      console.error('Error loading data source fields:', error);
      
      let errorMessage = 'Failed to load data source fields. ';
      
      if (error.message?.includes('Authentication required')) {
        errorMessage += 'Please log in to access this feature.';
      } else if (error.response?.status === 500) {
        errorMessage += 'Server error occurred. Please try again later.';
      } else if (error.response?.status === 401 || error.response?.status === 403) {
        errorMessage += 'Authentication failed. Please log in again.';
      } else {
        errorMessage += 'Please try again.';
      }
      
      setError(errorMessage);
      setLoading(false);
    }
  };

  // Handle report saving
  const handleSaveReport = async (reportConfig: Partial<ReportConfig>) => {
    try {
      if (!selectedDataSource) {
        setError('Please select a data source first');
        return;
      }

      setLoading(true);
      setError(null);

      const reportToSave: ReportConfig = {
        ...reportConfig,
        dataSourceId: selectedDataSource.id,
        metadata: {
          created: new Date(),
          modified: new Date(),
          createdBy: 'current-user', // This should come from user context
          version: 1,
        },
      } as ReportConfig;

      const savedReport = await nextGenReportService.saveTemplate(reportToSave);
      setCurrentReport(savedReport);
      setSuccess('Report saved successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
      
      setLoading(false);
    } catch (error: any) {
      console.error('Error saving report:', error);
      
      let errorMessage = 'Failed to save report. ';
      
      if (error.message?.includes('Authentication required')) {
        errorMessage += 'Please log in to save reports.';
      } else if (error.response?.status === 500) {
        errorMessage += 'Server error occurred. Please try again later.';
      } else if (error.response?.status === 401 || error.response?.status === 403) {
        errorMessage += 'Authentication failed. Please log in again.';
      } else {
        errorMessage += 'Please try again.';
      }
      
      setError(errorMessage);
      setLoading(false);
    }
  };

  // Retry loading data
  const handleRetry = () => {
    loadInitialData();
  };

  // Clear error
  const handleClearError = () => {
    setError(null);
  };

  // Clear success
  const handleClearSuccess = () => {
    setSuccess(null);
  };

  // Handle element updates
  const handleElementUpdate = useCallback((elementId: string, updates: Partial<ReportElement>) => {
    setReportElements(prev => 
      prev.map(element => 
        element.id === elementId 
          ? { ...element, ...updates }
          : element
      )
    );
  }, []);

  // Handle adding new elements
  const handleAddElement = useCallback((elementType: ReportElement['type']) => {
    const newElement: ReportElement = {
      id: `element_${Date.now()}`,
      type: elementType,
      title: `New ${elementType}`,
      config: {},
      position: { x: 0, y: reportElements.length * 100 },
      size: { width: 400, height: 300 },
      metadata: {
        created: new Date(),
        modified: new Date(),
        version: 1,
      },
    };

    setReportElements(prev => [...prev, newElement]);
  }, [reportElements.length]);

  // Handle chart data generation
  const handleGenerateChartData = async (elementId: string, chartConfig: Record<string, unknown>) => {
    try {
      if (!selectedDataSource) {
        setError('No data source selected');
        return;
      }

      setLoading(true);
      const chartData = await nextGenReportService.generateChartData(
        selectedDataSource.id,
        chartConfig
      );

      // Update the element with the generated data
      handleElementUpdate(elementId, {
        config: { ...chartConfig, data: chartData }
      });

      setLoading(false);
    } catch (error) {
      console.error('Error generating chart data:', error);
      setError('Failed to generate chart data');
      setLoading(false);
    }
  };

  // Handle AI suggestions
  const handleGetAISuggestions = async () => {
    try {
      if (!selectedDataSource) return [];

      const suggestions = await nextGenReportService.getSmartSuggestions(
        selectedDataSource.id,
        { existingElements: reportElements }
      );

      return suggestions;
    } catch (err) {
      console.error('Failed to get AI suggestions:', err);
      return [];
    }
  };

  // Handle report export
  const handleExportReport = async (format: 'pdf' | 'excel' | 'powerpoint' | 'html') => {
    try {
      if (!currentReport?.id) {
        setError('Please save the report first');
        return;
      }

      const blob = await nextGenReportService.exportReport(currentReport.id, format);
      
      // Download the file
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${currentReport.title}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      setSuccess(`Report exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Error exporting report:', error);
      setError(`Failed to export report as ${format}`);
    }
  };

  // Handle navigation to DOCX Generator
  const handleGoToDocxGenerator = () => {
    // This would typically navigate to a different page or component
    // For now, we'll just show a success message
    setSuccess('Navigating to DOCX Generator...');
    setTimeout(() => setSuccess(null), 3000);
  };

  if (loading && dataSources.length === 0) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        height="100vh"
        flexDirection="column"
        gap={2}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="text.secondary">
          Loading Next-Gen Report Builder...
        </Typography>
      </Box>
    );
  }

  return (
    <NextGenReportBuilderErrorBoundary>
      <AuthGuard>
        <Box sx={{ height: "100vh", overflow: "hidden" }}>
          {/* DOCX Generator Navigation Button */}
          <Box sx={{ p: 2, bgcolor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
            <Button
              variant="contained"
              startIcon={<Description />}
              onClick={handleGoToDocxGenerator}
              sx={{ 
                background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5855eb 0%, #7c3aed 50%, #0891b2 100%)',
                }
              }}
            >
              Generate DOCX Report
            </Button>
          </Box>

          {/* Next-Gen Report Builder Component */}
          <NextGenReportBuilder
            // Data Props
            dataSources={dataSources}
            selectedDataSource={selectedDataSource}
            dataFields={dataFields}
            onDataSourceChange={handleDataSourceChange}
            
            // Report Props
            reportElements={reportElements}
            onElementUpdate={handleElementUpdate}
            onAddElement={handleAddElement}
            
            // Chart Props
            onGenerateChartData={handleGenerateChartData}
            
            // AI Props
            onGetAISuggestions={handleGetAISuggestions}
            
            // Save/Export Props
            onSaveReport={handleSaveReport}
            onExportReport={handleExportReport}
            
            // Current Report
            currentReport={currentReport}
            
            // Loading State
            isLoading={loading}
          />

          {/* Accessibility Toolbar */}
          <AccessibilityToolbar />

          {/* Success/Error Notifications */}
          <Snackbar
            open={!!success}
            autoHideDuration={4000}
            onClose={() => setSuccess(null)}
          >
            <Alert severity="success" onClose={() => setSuccess(null)}>
              {success}
            </Alert>
          </Snackbar>

          <Snackbar
            open={!!error}
            autoHideDuration={6000}
            onClose={() => setError(null)}
          >
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          </Snackbar>
        </Box>
      </AuthGuard>
    </NextGenReportBuilderErrorBoundary>
  );
};

export default NextGenReportBuilderPage;
