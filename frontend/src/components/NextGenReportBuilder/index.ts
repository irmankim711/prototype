/**
 * Next-Generation Report Builder - Component Index
 * Complete UX redesign following enterprise best practices
 * 
 * This index exports all components for the redesigned Report Builder interface
 * following Senior UX Designer specifications for progressive disclosure,
 * accessibility, and mobile-first responsive design.
 */

// Main Components
export { default as NextGenReportBuilder } from './NextGenReportBuilder';
export { default as ExcelImportComponent } from './ExcelImportComponent';
export { default as ChartRenderer } from './ChartRenderer';
export { default as ChartConfigPanel } from './ChartConfigPanel';
export { default as AdvancedAnalyticsPanel } from './AdvancedAnalyticsPanel';
export { default as DataTransformationPanel } from './DataTransformationPanel';
export { default as AccessibilityHelpers } from './AccessibilityHelpers';
export { default as ContextualPanels } from './ContextualPanels';
export { default as ChartConfigurator } from './ChartConfigurator';
export { default as MobileComponents } from './MobileComponents';

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
  AdvancedInsights
} from './types';

// Accessibility Components
export {
  AccessibilityToolbar,
  useScreenReader,
  useKeyboardNavigation,
  useMotionPreferences,
  AccessibleDragDrop,
  AccessibleDropZone,
  HighContrastToggle,
  FontSizeControl,
  KeyboardShortcutsHelp,
} from "./AccessibilityHelpers";

// Mobile Components
export {
  useTouchGestures,
  MobileDataField,
  MobileBottomPanel,
  MobileChartTypeSelector,
  MobileDropZone,
  MobileNavigationTabs,
  MobileFloatingActionMenu,
  MobileReportCanvas,
} from "./MobileComponents";

// Contextual Panels
export {
  ChartPropertyPanel,
  TablePropertyPanel,
  TextPropertyPanel,
  SmartSuggestionsPanel,
} from "./ContextualPanels";

// Type Definitions
export interface ReportElement {
  id: string;
  type: "chart" | "table" | "text" | "image" | "heading" | "divider";
  title: string;
  config: any;
  position: { x: number; y: number };
  size: { width: number; height: number };
  metadata: {
    created: Date;
    modified: Date;
    version: number;
  };
}

export interface ReportElement {
  id: string;
  type: "chart" | "table" | "text" | "image" | "heading" | "divider";
  title: string;
  config: any;
  position: { x: number; y: number };
  size: { width: number; height: number };
  metadata: {
    created: Date;
    modified: Date;
    version: number;
  };
}

export interface SmartSuggestion {
  id: string;
  title: string;
  confidence: number;
  preview: string;
  reasoning: string;
  icon: React.ReactNode;
  quickApply: () => void;
}

export interface ChartType {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  preview: string;
  useCases: string[];
  requiredMappings: {
    dimensions: number;
    measures: number;
  };
  optionalMappings?: string[];
}

// Design System Constants
export const DESIGN_TOKENS = {
  colors: {
    primary: "#2563eb",
    primaryLight: "#3b82f6", 
    primaryBg: "#dbeafe",
    success: "#10b981",
    warning: "#f59e0b",
    error: "#ef4444",
    gray: {
      900: "#111827",
      600: "#4b5563", 
      300: "#d1d5db",
      50: "#f9fafb",
    },
    white: "#ffffff",
  },
  typography: {
    sizes: {
      "3xl": "1.875rem",
      xl: "1.25rem", 
      lg: "1.125rem",
      base: "1rem",
      sm: "0.875rem",
      xs: "0.75rem",
    },
    weights: {
      semibold: 600,
      medium: 500,
      normal: 400,
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  layout: {
    headerHeight: 64,
    leftPanelWidth: 280,
    rightPanelWidth: 320,
    bottomBarHeight: 48,
  },
} as const;

// Utility Functions
export const generateSmartSuggestions = (dataFields: any[]): SmartSuggestion[] => {
  const dimensions = dataFields.filter(f => f.type === "dimension").length;
  const measures = dataFields.filter(f => f.type === "measure").length;
  
  // Generate contextual suggestions based on available data
  const suggestions: SmartSuggestion[] = [];
  
  if (dimensions >= 1 && measures >= 1) {
    suggestions.push({
      id: "trend_analysis",
      title: "Trend Analysis",
      confidence: 0.9,
      preview: "Line chart showing trends over time",
      reasoning: "Time-series data detected",
      icon: null, // Would be populated with actual icon
      quickApply: () => console.log("Creating trend analysis"),
    });
  }
  
  return suggestions;
};

export const validateChartConfiguration = (chartType: ChartType, mappings: Record<string, any>): boolean => {
  const requiredMappings = chartType.requiredMappings;
  const mappedDimensions = Object.values(mappings).filter(field => field?.type === "dimension").length;
  const mappedMeasures = Object.values(mappings).filter(field => field?.type === "measure").length;
  
  return mappedDimensions >= requiredMappings.dimensions && 
         mappedMeasures >= requiredMappings.measures;
};

// Component Usage Examples
/**
 * Basic Usage:
 * 
 * import { NextGenReportBuilder } from './components/NextGenReportBuilder';
 * 
 * function App() {
 *   return <NextGenReportBuilder />;
 * }
 * 
 * With Custom Configuration:
 * 
 * import { 
 *   NextGenReportBuilder, 
 *   AccessibilityToolbar,
 *   DESIGN_TOKENS 
 * } from './components/NextGenReportBuilder';
 * 
 * function CustomReportBuilder() {
 *   return (
 *     <ThemeProvider theme={createTheme({ palette: { primary: { main: DESIGN_TOKENS.colors.primary } } })}>
 *       <NextGenReportBuilder />
 *       <AccessibilityToolbar />
 *     </ThemeProvider>
 *   );
 * }
 * 
 * Mobile-Only Implementation:
 * 
 * import { 
 *   MobileNavigationTabs,
 *   MobileReportCanvas,
 *   MobileBottomPanel 
 * } from './components/NextGenReportBuilder';
 * 
 * function MobileReportBuilder() {
 *   const [activeTab, setActiveTab] = useState(0);
 *   
 *   return (
 *     <Box>
 *       <MobileReportCanvas elements={[]} onElementSelect={() => {}} selectedElementId={null} />
 *       <MobileNavigationTabs activeTab={activeTab} onTabChange={setActiveTab} />
 *     </Box>
 *   );
 * }
 */
