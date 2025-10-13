/**
 * NextGen Report Builder Component Exports
 * Centralized export file for all NextGen Report Builder components
 */

export { default as NextGenReportBuilder } from './NextGenReportBuilder';
export { default as ChartRenderer } from './ChartRenderer';
export { default as ChartConfigPanel } from './ChartConfigPanel';
export { default as DataSourceManagementPanel } from './DataSourceManagementPanel';
export { default as AdvancedAnalyticsPanel } from './AdvancedAnalyticsPanel';
export { default as AdvancedChartTypesPanel } from './AdvancedChartTypesPanel';
export { default as DataTransformationPanel } from './DataTransformationPanel';
export { default as ExcelImportComponent } from './ExcelImportComponent';
export { default as AccessibilityHelpers } from './AccessibilityHelpers';
export { default as ContextualPanels } from './ContextualPanels';
export { default as ChartConfigurator } from './ChartConfigurator';
export { default as MobileComponents } from './MobileComponents';
export { default as NextGenReportBuilderErrorBoundary } from './ErrorBoundary';
export { default as AuthGuard } from './AuthGuard';

// Export hooks
export { usePerformanceMonitor } from './usePerformanceMonitor';

// Export types
export type {
  ChartData,
  ChartConfig,
  DataField,
  RawDataPoint,
  DataAggregation,
  TimeSeriesAnalysis,
  CorrelationAnalysis,
  DataQualityMetrics,
  ChartInsights,
  ChartSuggestion
} from './types';

// Export services
export { nextGenReportService } from '../../services/nextGenReportService';
export { chartDataService } from '../../services/chartDataService';

// Export chart templates
export const ChartTemplate = {
  // Chart template configurations would be implemented here
  // This would provide predefined chart configurations for common use cases
};

// Export accessibility toolbar component
export const AccessibilityToolbar = () => {
  // Accessibility toolbar implementation would go here
  // This would provide tools for screen readers, high contrast, etc.
  return null; // Placeholder until implementation is complete
};

