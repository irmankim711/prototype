/**
 * Next-Generation Report Builder Interface
 * Senior UX Designer Implementation following Progressive Disclosure Principles
 * Focus: User-Centered Design, Visual Hierarchy, Interaction Affordances
 */

import React, { useState, useRef, useCallback, useEffect } from "react";
import {
  Box,
  Typography,
  Button,
  Paper,
  Drawer,
  AppBar,
  Toolbar,
  IconButton,
  Chip,
  Badge,
  Tooltip,
  Zoom,
  Fab,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  alpha,
  Menu as MuiMenu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Alert,
} from "@mui/material";
import {
  DragIndicator,
  BarChart as BarChart3,
  TrendingUp as LineChart,
  PieChart,
  TableChart as TableIcon,
  TextFields,
  Image as ImageIcon,
  Save,
  Download,
  Share,
  Preview,
  MenuOpen,
  Menu,
  Add,
  AutoAwesome,
  Palette,
  Tune,
  ExpandMore,
  Visibility,
  VisibilityOff,
  ZoomIn,
  ZoomOut,
  Fullscreen,
  Close,
  ArrowRight,
  KeyboardArrowUp as ArrowUp,
  SmartToy,
  PictureAsPdf,
  TableView,
  Slideshow,
  Code,
  MoreVert,
  Refresh,
  Error as ErrorIcon,
  FileUpload,
} from "@mui/icons-material";
import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";
import type { DropResult } from "@hello-pangea/dnd";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";
import ExcelImportComponent from "./ExcelImportComponent";
import { nextGenReportService } from "../../services/nextGenReportService";
import ChartRenderer from "./ChartRenderer";
import type { ChartData, ChartConfig } from "./types";
import ChartConfigPanel from "./ChartConfigPanel";
import { chartDataService } from "../../services/chartDataService";
import DataSourceManagementPanel from "./DataSourceManagementPanel";
import AdvancedChartTypesPanel from "./AdvancedChartTypesPanel";

// Design System Constants
const DESIGN_TOKENS = {
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
};

// Component Types & Interfaces
interface DataField {
  id: string;
  name: string;
  type: "dimension" | "measure";
  dataType: "categorical" | "numerical" | "temporal";
  icon: React.ReactNode;
  sampleValues: string[];
  usageCount: number;
  description?: string;
}

interface ReportElement {
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

interface SmartSuggestion {
  id: string;
  title: string;
  confidence: number;
  preview: string;
  reasoning: string;
  icon: React.ReactNode;
  quickApply: () => void;
}

// Enhanced Data Field Component with metadata display
const DataFieldComponent: React.FC<{
  field: DataField;
  isDragging: boolean;
  onDragStart: () => void;
}> = ({ field, isDragging, onDragStart }) => {
  const theme = useTheme();
  
  return (
    <Paper
      elevation={isDragging ? 8 : 1}
      sx={{
        p: 1.5,
        cursor: "grab",
        borderRadius: 2,
        border: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
        backgroundColor: isDragging
          ? alpha(theme.palette.primary.main, 0.1)
          : theme.palette.background.paper,
        transform: isDragging ? "scale(1.05) rotate(2deg)" : "scale(1)",
        transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        "&:hover": {
          backgroundColor: alpha(theme.palette.primary.main, 0.04),
          borderColor: theme.palette.primary.main,
          transform: "translateY(-1px)",
        },
        "&:active": {
          cursor: "grabbing",
        },
      }}
      onMouseDown={onDragStart}
    >
      <Box display="flex" alignItems="center" gap={1}>
        <DragIndicator sx={{ fontSize: 16, color: "text.secondary" }} />
        {field.icon}
        <Box flex={1} minWidth={0}>
          <Typography
            variant="body2"
            fontWeight="medium"
            noWrap
            title={field.name}
          >
            {field.name}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            display="block"
          >
            {field.dataType} • {field.usageCount} uses
          </Typography>
        </Box>
        <Chip
          label={field.type}
          size="small"
          variant="outlined"
          sx={{
            height: 20,
            fontSize: "0.7rem",
            color: field.type === "dimension" ? "primary.main" : "secondary.main",
            borderColor: field.type === "dimension" ? "primary.main" : "secondary.main",
          }}
        />
      </Box>
    </Paper>
  );
};

// Smart Drop Zone Component with visual affordances
const DropZone: React.FC<{
  label: string;
  accepts: string[];
  icon: React.ReactNode;
  currentField?: DataField;
  placeholder: string;
  isValidDrop: boolean;
  isHovering: boolean;
  onDrop: (field: DataField) => void;
}> = ({ label, accepts, icon, currentField, placeholder, isValidDrop, isHovering, onDrop }) => {
  const theme = useTheme();
  
  const getBorderColor = () => {
    if (!isValidDrop && isHovering) return theme.palette.error.main;
    if (isValidDrop && isHovering) return theme.palette.success.main;
    if (currentField) return theme.palette.primary.main;
    return alpha(theme.palette.grey[300], 0.7);
  };

  const getBackgroundColor = () => {
    if (!isValidDrop && isHovering) return alpha(theme.palette.error.main, 0.1);
    if (isValidDrop && isHovering) return alpha(theme.palette.success.main, 0.1);
    if (currentField) return alpha(theme.palette.primary.main, 0.05);
    return "transparent";
  };

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        minHeight: 80,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        borderStyle: "dashed",
        borderWidth: 2,
        borderColor: getBorderColor(),
        backgroundColor: getBackgroundColor(),
        borderRadius: 2,
        transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        animation: isHovering ? "pulse 1.5s infinite" : "none",
        "@keyframes pulse": {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.8 },
        },
      }}
      role="button"
      tabIndex={0}
      aria-label={`Drop ${accepts.join(" or ")} field here for ${label}`}
    >
      {currentField ? (
        <Box display="flex" alignItems="center" gap={1}>
          {icon}
          <Typography variant="body2" fontWeight="medium">
            {currentField.name}
          </Typography>
          <IconButton size="small" onClick={() => onDrop(undefined as any)}>
            <Close fontSize="small" />
          </IconButton>
        </Box>
      ) : (
        <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
          {icon}
          <Typography variant="caption" color="text.secondary" textAlign="center">
            {placeholder}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

// AI Suggestions Panel
const AISuggestionsPanel: React.FC<{
  suggestions: SmartSuggestion[];
  onApplySuggestion: (suggestion: SmartSuggestion) => void;
  isLoading?: boolean;
  error?: string | null;
}> = ({ suggestions, onApplySuggestion, isLoading = false, error = null }) => {
  if (isLoading) {
    return (
      <Box>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <SmartToy color="primary" />
          <Typography variant="h6" fontWeight="semibold">
            AI Suggestions
          </Typography>
        </Box>
        <Box display="flex" flexDirection="column" gap={2}>
          <LinearProgress />
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Analyzing your data for smart suggestions...
          </Typography>
        </Box>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <SmartToy color="primary" />
          <Typography variant="h6" fontWeight="semibold">
            AI Suggestions
          </Typography>
        </Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      </Box>
    );
  }

  if (suggestions.length === 0) {
    return (
      <Box>
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <SmartToy color="primary" />
          <Typography variant="h6" fontWeight="semibold">
            AI Suggestions
          </Typography>
        </Box>
        <Box textAlign="center" py={3}>
          <Typography variant="body2" color="text.secondary" mb={2}>
            No AI suggestions available
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Upload data or connect data sources to get AI-powered insights
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={1} mb={2}>
        <SmartToy color="primary" />
        <Typography variant="h6" fontWeight="semibold">
          AI Suggestions
        </Typography>
      </Box>
      <Box display="flex" flexDirection="column" gap={1}>
        {suggestions.map((suggestion) => (
          <Paper
            key={suggestion.id}
            variant="outlined"
            sx={{
              p: 2,
              cursor: "pointer",
              borderRadius: 2,
              transition: "all 0.2s ease",
              "&:hover": {
                backgroundColor: alpha("#6366f1", 0.04),
                borderColor: "#6366f1",
                transform: "translateY(-1px)",
              },
            }}
            onClick={() => onApplySuggestion(suggestion)}
          >
            <Box display="flex" alignItems="start" gap={2}>
              {suggestion.icon}
              <Box flex={1}>
                <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                  <Typography variant="body2" fontWeight="medium">
                    {suggestion.title}
                  </Typography>
                  <Chip
                    label={`${Math.round(suggestion.confidence * 100)}%`}
                    size="small"
                    color="primary"
                    sx={{ height: 16, fontSize: "0.6rem" }}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                  {suggestion.reasoning}
                </Typography>
                <Typography variant="body2" color="text.primary">
                  {suggestion.preview}
                </Typography>
              </Box>
            </Box>
          </Paper>
        ))}
      </Box>
    </Box>
  );
};

// Props interface for the main component
interface NextGenReportBuilderProps {
  dataSources?: any[];
  selectedDataSource?: any;
  dataFields?: DataField[];
  onDataSourceChange?: (dataSourceId: string) => void;
  reportElements?: ReportElement[];
  onElementUpdate?: (elementId: string, updates: Partial<ReportElement>) => void;
  onAddElement?: (elementType: ReportElement['type']) => void;
  onGenerateChartData?: (elementId: string, chartConfig: any) => void;
  onGetAISuggestions?: () => Promise<SmartSuggestion[]>;
  onSaveReport?: (reportConfig: any) => void;
  onExportReport?: (format: 'pdf' | 'excel' | 'powerpoint' | 'html') => void;
  currentReport?: any;
  isLoading?: boolean;
}

// Main Next-Gen Report Builder Component
const NextGenReportBuilder: React.FC<NextGenReportBuilderProps> = ({
  dataSources = [],
  selectedDataSource,
  dataFields = [],
  onDataSourceChange,
  reportElements = [],
  onElementUpdate,
  onAddElement,
  onGenerateChartData,
  onGetAISuggestions,
  onSaveReport,
  onExportReport,
  currentReport,
  isLoading = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  
  // Core State Management
  const [reportTitle, setReportTitle] = useState("Quarterly Performance Analysis");
  const [elements, setElements] = useState<ReportElement[]>([]);
  const [selectedElementId, setSelectedElementId] = useState<string | null>(null);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  
  // Data Loading States
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [dataError, setDataError] = useState<string | null>(null);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);
  const [templatesError, setTemplatesError] = useState<string | null>(null);
  
  // Panel States - Progressive Disclosure
  const [leftPanelOpen, setLeftPanelOpen] = useState(!isMobile);
  const [rightPanelOpen, setRightPanelOpen] = useState(!isMobile);
  const [activeLeftTab, setActiveLeftTab] = useState(0); // 0: Data, 1: Components, 2: Templates, 3: Excel Import, 4: Real-time, 5: Data Sources, 6: Advanced
  const [activeRightTab, setActiveRightTab] = useState(0); // 0: Properties, 1: Styling, 2: Advanced
  
  // UI State
  const [zoomLevel, setZoomLevel] = useState(100);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [draggedField, setDraggedField] = useState<DataField | null>(null);
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);
  const [availableTemplates, setAvailableTemplates] = useState<any[]>([]);
  
  // Use provided data fields or fallback to empty array
  const displayDataFields = dataFields.length > 0 ? dataFields.map(field => ({
    ...field,
    icon: field.type === "dimension" 
      ? <BarChart3 sx={{ fontSize: 16, color: "#6366f1" }} />
      : <LineChart sx={{ fontSize: 16, color: "#06b6d4" }} />
  })) : [];

  // Smart AI Suggestions - Based on available data
  const generateAISuggestions = useCallback((): SmartSuggestion[] => {
    // Return empty array, let backend provide real suggestions
    return [];
  }, []);

  // AI Suggestions State
  const [aiSuggestions, setAiSuggestions] = useState<SmartSuggestion[]>([]);
  const [isLoadingAISuggestions, setIsLoadingAISuggestions] = useState(false);
  const [aiSuggestionsError, setAiSuggestionsError] = useState<string | null>(null);

  // Chart State Management
  const [currentChartConfig, setCurrentChartConfig] = useState<ChartConfig>({
    type: 'bar',
    title: 'New Chart',
    xAxis: undefined,
    yAxis: undefined,
    colorScheme: 'default',
    showLegend: true,
    showGrid: true,
    animation: true,
    responsive: true,
  });
  const [currentChartData, setCurrentChartData] = useState<ChartData | null>(null);
  const [isGeneratingChart, setIsGeneratingChart] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);
  const [rawData, setRawData] = useState<any[]>([]);

  // Load data on component mount
  useEffect(() => {
    loadData();
    loadSampleData();
  }, []);

  const loadSampleData = () => {
    // Generate sample data for demonstration
    const sampleData = [
      { quarter: 'Q1', revenue: 85000, region: 'North' },
      { quarter: 'Q2', revenue: 92000, region: 'North' },
      { quarter: 'Q3', revenue: 78000, region: 'North' },
      { quarter: 'Q4', revenue: 96000, region: 'North' },
      { quarter: 'Q1', revenue: 75000, region: 'South' },
      { quarter: 'Q2', revenue: 88000, region: 'South' },
      { quarter: 'Q3', revenue: 82000, region: 'South' },
      { quarter: 'Q4', revenue: 90000, region: 'South' },
      { quarter: 'Q1', revenue: 90000, region: 'East' },
      { quarter: 'Q2', revenue: 95000, region: 'East' },
      { quarter: 'Q3', revenue: 85000, region: 'East' },
      { quarter: 'Q4', revenue: 98000, region: 'East' },
      { quarter: 'Q1', revenue: 70000, region: 'West' },
      { quarter: 'Q2', revenue: 85000, region: 'West' },
      { quarter: 'Q3', revenue: 75000, region: 'West' },
      { quarter: 'Q4', revenue: 88000, region: 'West' },
    ];
    setRawData(sampleData);
  };

  // Load AI suggestions when data fields change
  useEffect(() => {
    if (displayDataFields.length > 0 && selectedDataSource) {
      loadAISuggestions();
    }
  }, [displayDataFields, selectedDataSource]);

  const loadData = async () => {
    try {
      setIsLoadingData(true);
      setDataError(null);
      
      // Load data sources and fields if not provided via props
      if (dataSources.length === 0) {
        const sources = await nextGenReportService.getDataSources();
        // Update data sources if needed
      }
      
              if (dataFields.length === 0 && selectedDataSource) {
          const fields = await nextGenReportService.getDataFields(selectedDataSource.id);
          // Update data fields if needed
        }
      
    } catch (error: any) {
      setDataError(error.message || 'Failed to load data. Please check your connection and try again.');
    } finally {
      setIsLoadingData(false);
    }
  };

  const loadAISuggestions = async () => {
    try {
      setIsLoadingAISuggestions(true);
      setAiSuggestionsError(null);
      
      if (selectedDataSource && displayDataFields.length > 0) {
        const suggestions = await nextGenReportService.getSmartSuggestions(selectedDataSource.id);
        setAiSuggestions(suggestions);
      } else {
        setAiSuggestions([]);
      }
    } catch (error: any) {
      setAiSuggestionsError(error.message || 'Failed to load AI suggestions. Please try again.');
      setAiSuggestions([]);
    } finally {
      setIsLoadingAISuggestions(false);
    }
  };

  // Generate chart from configuration
  const generateChart = async () => {
    try {
      setIsGeneratingChart(true);
      setChartError(null);

      // Validate chart configuration
      const validationErrors = chartDataService.validateChartConfig(currentChartConfig, displayDataFields);
      if (validationErrors.length > 0) {
        throw new Error(`Chart configuration errors: ${validationErrors.join(', ')}`);
      }

      // Check if we have raw data
      if (rawData.length === 0) {
        throw new Error('No data available for chart generation');
      }

      // Process raw data into chart format
      const processedData = chartDataService.processDataForChart(
        rawData,
        currentChartConfig,
        displayDataFields
      );

      setCurrentChartData(processedData);
      
      // Get data insights
      const insights = chartDataService.getDataInsights(rawData, currentChartConfig, displayDataFields);
      if (insights) {
      }

    } catch (error: any) {
      setChartError(error.message || 'Failed to generate chart');
      setCurrentChartData(null);
    } finally {
      setIsGeneratingChart(false);
    }
  };

  // Handle chart configuration changes
  const handleChartConfigChange = (newConfig: ChartConfig) => {
    setCurrentChartConfig(newConfig);
    // Clear previous chart data when configuration changes
    setCurrentChartData(null);
    setChartError(null);
  };

  // Load templates on component mount
  useEffect(() => {
    loadAvailableTemplates();
  }, []);

  const loadAvailableTemplates = async () => {
    try {
      setIsLoadingTemplates(true);
      setTemplatesError(null);
      
      const templates = await nextGenReportService.getReportTemplates();
      setAvailableTemplates(templates);
    } catch (error: any) {
      setTemplatesError(error.message || 'Failed to load templates. Please try again later.');
      setAvailableTemplates([]);
    } finally {
      setIsLoadingTemplates(false);
    }
  };

  // Handle report saving
  const handleSaveReport = async () => {
    try {
      if (!onSaveReport) {
        throw new Error('Save functionality not available');
      }

      const reportConfig = {
        title: reportTitle,
        description: `Report with ${elements.length} elements`,
        elements: elements,
        layout: {
          theme: 'professional',
          colorScheme: 'default',
          responsive: true,
          zoomLevel: zoomLevel,
        },
      };

      await onSaveReport(reportConfig);
    } catch (error: any) {
      setDataError(error.message || 'Error saving report:');
    }
  };

  // Handle adding new elements
  const handleAddElement = (elementType: ReportElement['type']) => {
    const newElement: ReportElement = {
      id: `element_${Date.now()}`,
      type: elementType,
      title: `New ${elementType}`,
      config: {},
      position: { x: 0, y: elements.length * 100 },
      size: { width: 400, height: 300 },
      metadata: {
        created: new Date(),
        modified: new Date(),
        version: 1,
      },
    };

    setElements(prev => [...prev, newElement]);
    if (onAddElement) {
      onAddElement(elementType);
    }
  };

  // Handle AI suggestions
  const handleApplySuggestion = async (suggestion: SmartSuggestion) => {
    try {
      suggestion.quickApply();
      
      // Create chart element based on suggestion
      const newElement: ReportElement = {
        id: `ai_element_${Date.now()}`,
        type: 'chart',
        title: suggestion.title,
        config: {
          chartType: suggestion.id.includes('trend') ? 'line' : suggestion.id.includes('comparison') ? 'bar' : 'table',
          aiGenerated: true,
          confidence: suggestion.confidence,
        },
        position: { x: 20, y: elements.length * 120 + 20 },
        size: { width: 500, height: 350 },
        metadata: {
          created: new Date(),
          modified: new Date(),
          version: 1,
        },
      };
      
      setElements(prev => [...prev, newElement]);
      
      if (onGetAISuggestions) {
        const updatedSuggestions = await onGetAISuggestions();
        // Update suggestions if needed
      }
    } catch (error: any) {
      setDataError(error.message || 'Error applying AI suggestion:');
    }
  };

  // Drag and Drop Handlers
  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;
    
    // Handle field to chart area drag and drop
  };

  const handleFieldDrop = (field: DataField, dropZoneType: string) => {
    if (!currentChartConfig) return;
    
    const updatedConfig = { ...currentChartConfig };
    
    if (dropZoneType === 'x-axis') {
      updatedConfig.xAxis = {
        field: field.id,
        label: field.name,
        type: field.dataType === 'temporal' ? 'temporal' : 'dimension'
      };
    } else if (dropZoneType === 'y-axis') {
      updatedConfig.yAxis = {
        field: field.id,
        label: field.name,
        type: 'measure'
      };
    }
    
    setCurrentChartConfig(updatedConfig);
  };

  // Export Menu Handlers
  const handleExportMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenuAnchor(event.currentTarget);
  };

  const handleExportMenuClose = () => {
    setExportMenuAnchor(null);
  };

  const handleExport = async (format: 'pdf' | 'excel' | 'powerpoint' | 'html') => {
    try {
      if (onExportReport) {
        await onExportReport(format);
      } else {
        // Fallback export logic
        console.log(`Exporting as ${format}`);
        // Could implement client-side export here
      }
    } catch (error: any) {
      setDataError(`Export failed: ${error.message}`);
    } finally {
      handleExportMenuClose();
    }
  };

  // Component Library Items
  const componentLibrary = [
    {
      type: "chart",
      icon: <BarChart3 />,
      label: "Bar Chart",
      description: "Compare values across categories",
    },
    {
      type: "line_chart",
      icon: <LineChart />,
      label: "Line Chart", 
      description: "Show trends over time",
    },
    {
      type: "pie_chart",
      icon: <PieChart />,
      label: "Pie Chart",
      description: "Show parts of a whole",
    },
    {
      type: "table",
      icon: <TableIcon />,
      label: "Data Table",
      description: "Display detailed tabular data",
    },
    {
      type: "heading",
      icon: <TextFields />,
      label: "Heading",
      description: "Add section titles",
    },
    {
      type: "image",
      icon: <ImageIcon />,
      label: "Image",
      description: "Insert charts or graphics",
    },
  ];

  // Left Panel Content based on Progressive Disclosure
  const renderLeftPanelContent = () => {
    switch (activeLeftTab) {
      case 0: // Data Sources
        return (
          <Box p={2}>
            <Typography variant="h6" fontWeight="semibold" mb={2}>
              Data Fields
            </Typography>
            
            {isLoadingData ? (
              <Box display="flex" flexDirection="column" gap={2}>
                <LinearProgress />
                <Typography variant="body2" color="text.secondary" textAlign="center">
                  Loading data sources...
                </Typography>
              </Box>
            ) : dataError ? (
              <Box display="flex" flexDirection="column" gap={2}>
                <Alert severity="error" sx={{ mb: 2 }}>
                  {dataError}
                </Alert>
                <Button 
                  variant="outlined" 
                  size="small" 
                  onClick={loadData}
                  startIcon={<Refresh />}
                >
                  Retry
                </Button>
              </Box>
            ) : displayDataFields.length === 0 ? (
              <Box textAlign="center" py={3}>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  No data sources available
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Upload an Excel file or connect a data source to get started
                </Typography>
              </Box>
            ) : (
              <>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Drag fields to chart areas to create visualizations
                </Typography>
                <Box display="flex" flexDirection="column" gap={1}>
                  {displayDataFields.map((field) => (
                    <DataFieldComponent
                      key={field.id}
                      field={field}
                      isDragging={draggedField?.id === field.id}
                      onDragStart={() => setDraggedField(field)}
                    />
                  ))}
                </Box>
              </>
            )}
          </Box>
        );
      
      case 1: // Component Library
        return (
          <Box p={2}>
            <Typography variant="h6" fontWeight="semibold" mb={2}>
              Components
            </Typography>
            <Box display="grid" gridTemplateColumns="1fr 1fr" gap={1}>
              {componentLibrary.map((component) => (
                <Paper
                  key={component.type}
                  variant="outlined"
                  sx={{
                    p: 2,
                    cursor: "pointer",
                    borderRadius: 2,
                    textAlign: "center",
                    transition: "all 0.2s ease",
                    "&:hover": {
                      backgroundColor: alpha(theme.palette.primary.main, 0.04),
                      borderColor: theme.palette.primary.main,
                      transform: "translateY(-2px)",
                    },
                  }}
                  onClick={() => handleAddElement(component.type as ReportElement['type'])}
                >
                  <Box mb={1}>{component.icon}</Box>
                  <Typography variant="caption" fontWeight="medium" display="block">
                    {component.label}
                  </Typography>
                </Paper>
              ))}
            </Box>
          </Box>
        );
      
      case 2: // Template Gallery
        return (
          <Box p={2}>
            <Typography variant="h6" fontWeight="semibold" mb={2}>
              Templates
            </Typography>
            
            {isLoadingTemplates ? (
              <Box display="flex" flexDirection="column" gap={2}>
                <LinearProgress />
                <Typography variant="body2" color="text.secondary" textAlign="center">
                  Loading templates...
                </Typography>
              </Box>
            ) : templatesError ? (
              <Box display="flex" flexDirection="column" gap={2}>
                <Alert severity="error" sx={{ mb: 2 }}>
                  {templatesError}
                </Alert>
                <Button 
                  variant="outlined" 
                  size="small" 
                  onClick={loadAvailableTemplates}
                  startIcon={<Refresh />}
                >
                  Retry
                </Button>
              </Box>
            ) : availableTemplates.length === 0 ? (
              <Box textAlign="center" py={3}>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  No templates available
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Templates will appear here once they're configured
                </Typography>
              </Box>
            ) : (
              <>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Quick-start templates for common report types
                </Typography>
                <Box display="flex" flexDirection="column" gap={1}>
                  {availableTemplates.map((template) => (
                    <Paper
                      key={template.id}
                      variant="outlined"
                      sx={{
                        p: 2,
                        mb: 1,
                        cursor: "pointer",
                        borderRadius: 2,
                        transition: "all 0.2s ease",
                        "&:hover": {
                          backgroundColor: alpha("#2563eb", 0.04),
                          borderColor: "#2563eb",
                        },
                      }}
                      onClick={() => console.log(`Loading template: ${template.id}`)}
                    >
                      <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                        <Typography variant="body2" fontWeight="medium">
                          {template.name}
                        </Typography>
                        {template.type === 'docx' && (
                          <Chip 
                            label="DOCX" 
                            size="small" 
                            color="primary" 
                            sx={{ height: 16, fontSize: '0.6rem' }}
                          />
                        )}
                        {template.isDefault && (
                          <Chip 
                            label="★" 
                            size="small" 
                            color="warning" 
                            sx={{ height: 16, fontSize: '0.6rem', minWidth: 20 }}
                          />
                        )}
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        {template.description || 'Click to apply template'}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              </>
            )}
          </Box>
        );
      
      case 3: // Excel Import
        return (
          <Box p={2}>
            <ExcelImportComponent
              onDataSourceCreated={(dataSource) => {
                // Add the new data source to the list
                console.log('New data source created:', dataSource);
                // Could refresh data sources here
              }}
              onReportGenerated={(report) => {
                console.log('Report generated:', report);
                // Could add the report to the elements or show a success message
              }}
            />
          </Box>
        );
      
      case 4: // Data Source Management
             return (
               <Box p={2}>
                 <DataSourceManagementPanel
                   onDataSourceChange={(sourceId) => {
                     console.log('Data source changed:', sourceId);
                     // Handle data source changes
                   }}
                 />
               </Box>
             );

           case 5: // Advanced Chart Types & Export
             return (
               <Box p={2}>
                 <AdvancedChartTypesPanel
                   chartData={currentChartData || undefined}
                   chartConfig={currentChartConfig}
                   onChartConfigChange={(config) => {
                     console.log('Advanced chart config changed:', config);
                     // Handle advanced chart configuration changes
                   }}
                   onExport={(result) => {
                     console.log('Export result:', result);
                     // Handle export results
                   }}
                 />
               </Box>
             );

           default:
             return null;
    }
  };

  // Right Panel Content - Context-sensitive
  const renderRightPanelContent = () => {
    if (displayDataFields.length === 0) {
      return (
        <Box p={2}>
          <AISuggestionsPanel
            suggestions={aiSuggestions}
            onApplySuggestion={handleApplySuggestion}
            isLoading={isLoadingData || isLoadingTemplates || isLoadingAISuggestions}
            error={dataError || templatesError || aiSuggestionsError}
          />
        </Box>
      );
    }

    // Show chart configuration panel when data fields are available
    return (
      <Box p={2}>
        <ChartConfigPanel
          config={currentChartConfig}
          availableFields={displayDataFields}
          onConfigChange={handleChartConfigChange}
          onGenerateChart={generateChart}
          isLoading={isGeneratingChart}
        />
      </Box>
    );
  };

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Global Loading Indicator */}
      {(isLoadingData || isLoadingTemplates || isLoadingAISuggestions) && (
        <Box
          sx={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9999,
          }}
        >
          <LinearProgress />
        </Box>
      )}
      
      {/* Header Bar - Fixed 64px */}
      <AppBar 
        position="static" 
        elevation={1}
        sx={{ 
          backgroundColor: "background.paper",
          color: "text.primary",
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
        }}
      >
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Box display="flex" alignItems="center" gap={2}>
            <IconButton
              onClick={() => setLeftPanelOpen(!leftPanelOpen)}
              size="small"
            >
              {leftPanelOpen ? <MenuOpen /> : <Menu />}
            </IconButton>
            <Typography
              variant="h6"
              component="div"
              sx={{
                fontWeight: "semibold",
                cursor: "text",
                "&:hover": { backgroundColor: alpha(theme.palette.action.hover, 0.04) },
                px: 1,
                py: 0.5,
                borderRadius: 1,
              }}
              contentEditable
              suppressContentEditableWarning
            >
              {reportTitle}
            </Typography>
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            {/* Zoom Controls */}
            <Box display="flex" alignItems="center" gap={0.5}>
              <IconButton size="small" onClick={() => setZoomLevel(Math.max(50, zoomLevel - 10))}>
                <ZoomOut fontSize="small" />
              </IconButton>
              <Typography variant="caption" sx={{ minWidth: 40, textAlign: "center" }}>
                {zoomLevel}%
              </Typography>
              <IconButton size="small" onClick={() => setZoomLevel(Math.min(200, zoomLevel + 10))}>
                <ZoomIn fontSize="small" />
              </IconButton>
            </Box>

            <Divider orientation="vertical" flexItem />

            {/* Action Buttons */}
            <Button
              variant={isPreviewMode ? "contained" : "outlined"}
              startIcon={isPreviewMode ? <VisibilityOff /> : <Visibility />}
              onClick={() => setIsPreviewMode(!isPreviewMode)}
              size="small"
            >
              {isPreviewMode ? "Edit" : "Preview"}
            </Button>
            
            <Button 
              variant="outlined" 
              startIcon={<Refresh />} 
              size="small"
              onClick={loadData}
              disabled={isLoadingData}
            >
              Refresh
            </Button>
            
            <Button 
              variant="outlined" 
              startIcon={<Save />} 
              size="small"
              onClick={handleSaveReport}
              disabled={isLoadingData}
            >
              Save
            </Button>
            
            <Button 
              variant="outlined" 
              startIcon={<Download />} 
              size="small"
              onClick={handleExportMenuClick}
              disabled={isLoadingData}
            >
              Export
            </Button>
            
            <Button variant="contained" startIcon={<Share />} size="small">
              Share
            </Button>

            <IconButton
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              size="small"
            >
              <Tune />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main Content Area */}
      <Box sx={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {/* Left Panel - Data Sources & Components */}
        <Drawer
          variant={isMobile ? "temporary" : "persistent"}
          open={leftPanelOpen}
          onClose={() => setLeftPanelOpen(false)}
          sx={{
            width: DESIGN_TOKENS.layout.leftPanelWidth,
            flexShrink: 0,
            "& .MuiDrawer-paper": {
              width: DESIGN_TOKENS.layout.leftPanelWidth,
              borderRight: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              top: DESIGN_TOKENS.layout.headerHeight,
              height: `calc(100vh - ${DESIGN_TOKENS.layout.headerHeight}px)`,
            },
          }}
        >
          {/* Left Panel Tabs */}
          <Box sx={{ borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
            <Box display="flex">
              {["Data", "Components", "Templates", "Excel", "Data Sources", "Advanced"].map((tab, index) => (
                <Button
                  key={tab}
                  variant={activeLeftTab === index ? "contained" : "text"}
                  size="small"
                  sx={{ 
                    flex: 1, 
                    borderRadius: 0,
                    textTransform: "none",
                    fontWeight: activeLeftTab === index ? "semibold" : "medium",
                    fontSize: "0.75rem",
                  }}
                  onClick={() => setActiveLeftTab(index)}
                >
                  {tab}
                </Button>
              ))}
            </Box>
          </Box>
          
          {renderLeftPanelContent()}
        </Drawer>

        {/* Center Canvas - Primary Focus Area */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            backgroundColor: "#f8fafc",
            position: "relative",
          }}
        >
          <DragDropContext onDragEnd={handleDragEnd}>
            {/* Chart Configuration Area */}
            <Box sx={{ p: 3, flex: 1 }}>
              {isLoadingData ? (
                <Paper
                  elevation={2}
                  sx={{
                    p: 3,
                    borderRadius: 3,
                    minHeight: 200,
                    backgroundColor: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mb: 3,
                  }}
                >
                  <Box textAlign="center">
                    <LinearProgress sx={{ width: 200, mb: 2 }} />
                    <Typography variant="h6" fontWeight="semibold" mb={1}>
                      Loading Report Builder
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      Preparing your workspace...
                    </Typography>
                  </Box>
                </Paper>
              ) : dataError ? (
                <Paper
                  elevation={2}
                  sx={{
                    p: 3,
                    borderRadius: 3,
                    minHeight: 200,
                    backgroundColor: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    mb: 3,
                  }}
                >
                  <Box textAlign="center">
                    <ErrorIcon sx={{ fontSize: 48, color: "error.main", mb: 2 }} />
                    <Typography variant="h6" fontWeight="semibold" mb={1}>
                      Unable to Load Data
                    </Typography>
                    <Typography variant="body1" color="text.secondary" mb={3}>
                      {dataError}
                    </Typography>
                    <Button 
                      variant="contained" 
                      onClick={loadData}
                      startIcon={<Refresh />}
                    >
                      Retry
                    </Button>
                  </Box>
                </Paper>
              ) : displayDataFields.length === 0 ? (
                  <Paper
                    elevation={2}
                    sx={{
                      p: 3,
                      borderRadius: 3,
                      minHeight: 200,
                      backgroundColor: "white",
                      border: `2px dashed ${alpha(theme.palette.primary.main, 0.2)}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      mb: 3,
                    }}
                  >
                    <Box textAlign="center">
                      <AutoAwesome sx={{ fontSize: 48, color: "text.secondary", mb: 2 }} />
                      <Typography variant="h5" fontWeight="semibold" mb={1}>
                        Get Started with Your First Report
                      </Typography>
                      <Typography variant="body1" color="text.secondary" mb={3}>
                        Upload an Excel file or connect a data source to begin building reports
                      </Typography>
                      <Button 
                        variant="contained" 
                        onClick={() => setActiveLeftTab(3)} // Switch to Excel tab
                        startIcon={<FileUpload />}
                      >
                        Upload Excel File
                      </Button>
                    </Box>
                  </Paper>
                ) : (
                  <>
                    {/* Chart Display Area */}
                    {currentChartData ? (
                      <Box mb={3}>
                        <ChartRenderer
                          chartData={currentChartData}
                          config={currentChartConfig}
                          height={400}
                          width="100%"
                          onChartClick={(event, elements) => {
                            // Chart click handling would be implemented here
                          }}
                          onChartHover={(event, elements) => {
                            // Chart hover handling would be implemented here
                          }}
                        />
                      </Box>
                    ) : chartError ? (
                      <Paper
                        elevation={2}
                        sx={{
                          p: 3,
                          borderRadius: 3,
                          minHeight: 200,
                          backgroundColor: "white",
                          border: `2px dashed ${theme.palette.error.main}`,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          mb: 3,
                        }}
                      >
                        <Box textAlign="center">
                          <ErrorIcon sx={{ fontSize: 48, color: "error.main", mb: 2 }} />
                          <Typography variant="h6" fontWeight="semibold" mb={1}>
                            Chart Generation Failed
                          </Typography>
                          <Typography variant="body1" color="text.secondary" mb={3}>
                            {chartError}
                          </Typography>
                          <Button 
                            variant="contained" 
                            onClick={generateChart}
                            startIcon={<Refresh />}
                            disabled={isGeneratingChart}
                          >
                            {isGeneratingChart ? 'Generating...' : 'Retry'}
                          </Button>
                        </Box>
                      </Paper>
                    ) : (
                      /* Current Chart Configuration */
                      <Paper
                        elevation={2}
                        sx={{
                          p: 3,
                          borderRadius: 3,
                          minHeight: 200,
                          backgroundColor: "white",
                          border: `2px dashed ${alpha(theme.palette.primary.main, 0.2)}`,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          mb: 3,
                        }}
                      >
                        <Box textAlign="center">
                          <AutoAwesome sx={{ fontSize: 48, color: "text.secondary", mb: 2 }} />
                          <Typography variant="h5" fontWeight="semibold" mb={1}>
                            Configure Your Chart
                          </Typography>
                          <Typography variant="body1" color="text.secondary" mb={3}>
                            Use the configuration panel on the right to set up your chart
                          </Typography>
                          <Button 
                            variant="contained" 
                            onClick={generateChart}
                            startIcon={<SmartToy />}
                            disabled={!currentChartConfig.xAxis?.field || !currentChartConfig.yAxis?.field}
                          >
                            Generate Chart
                          </Button>
                        </Box>
                      </Paper>
                    )}

                    {/* Drop Zones for Chart Configuration */}
                    <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
                      <DropZone
                        label="X-Axis"
                        accepts={["dimension"]}
                        icon={<ArrowRight />}
                        placeholder="Drag dimension here"
                        isValidDrop={true}
                        isHovering={false}
                        onDrop={(field) => handleFieldDrop(field, "x-axis")}
                      />
                      <DropZone
                        label="Y-Axis"
                        accepts={["measure"]}
                        icon={<ArrowUp />}
                        placeholder="Drag measure here"
                        isValidDrop={true}
                        isHovering={false}
                        onDrop={(field) => handleFieldDrop(field, "y-axis")}
                      />
                    </Box>
                  </>
                )}
            </Box>
          </DragDropContext>
        </Box>

        {/* Right Panel - Context-Aware Properties */}
        <Drawer
          variant={isMobile ? "temporary" : "persistent"}
          anchor="right"
          open={rightPanelOpen}
          onClose={() => setRightPanelOpen(false)}
          sx={{
            width: DESIGN_TOKENS.layout.rightPanelWidth,
            flexShrink: 0,
            "& .MuiDrawer-paper": {
              width: DESIGN_TOKENS.layout.rightPanelWidth,
              borderLeft: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
              top: DESIGN_TOKENS.layout.headerHeight,
              height: `calc(100vh - ${DESIGN_TOKENS.layout.headerHeight}px)`,
            },
          }}
        >
          {renderRightPanelContent()}
        </Drawer>
      </Box>

      {/* Export Menu */}
      <MuiMenu
        anchorEl={exportMenuAnchor}
        open={Boolean(exportMenuAnchor)}
        onClose={handleExportMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={() => handleExport('pdf')}>
          <ListItemIcon>
            <PictureAsPdf fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            <Typography variant="body2">Export as PDF</Typography>
            <Typography variant="caption" color="text.secondary">
              Portable document format
            </Typography>
          </ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleExport('excel')}>
          <ListItemIcon>
            <TableView fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            <Typography variant="body2">Export as Excel</Typography>
            <Typography variant="caption" color="text.secondary">
              Excel spreadsheet format
            </Typography>
          </ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleExport('powerpoint')}>
          <ListItemIcon>
            <Slideshow fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            <Typography variant="body2">Export as PowerPoint</Typography>
            <Typography variant="caption" color="text.secondary">
              Presentation format
            </Typography>
          </ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleExport('html')}>
          <ListItemIcon>
            <Code fontSize="small" />
          </ListItemIcon>
          <ListItemText>
            <Typography variant="body2">Export as HTML</Typography>
            <Typography variant="caption" color="text.secondary">
              Web page format
            </Typography>
          </ListItemText>
        </MenuItem>
      </MuiMenu>

      {/* Floating Action Button for Mobile */}
      {isMobile && (
        <Fab
          color="primary"
          sx={{
            position: "fixed",
            bottom: 16,
            right: 16,
            zIndex: 1000,
          }}
          onClick={() => setRightPanelOpen(true)}
        >
          <Add />
        </Fab>
      )}
    </Box>
  );
};

export default NextGenReportBuilder;
