/**
 * Visual-First Chart Configuration Interface
 * Enhanced chart configurator following UX best practices
 * Focus: Visual affordances, Progressive disclosure, Smart defaults
 */

import React, { useState, useCallback, useRef } from "react";
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  IconButton,
  Chip,
  Tooltip,
  Switch,
  FormControlLabel,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  alpha,
  useTheme,
} from "@mui/material";
import {
  BarChart as BarChart3,
  TrendingUp as LineChart,
  PieChart,
  ScatterPlot as ScatterChart,
  ShowChart as AreaChart,
  DonutLarge as DonutChart,
  ArrowRight,
  KeyboardArrowUp as ArrowUp,
  Palette,
  Settings,
  ExpandMore,
  Close,
  DragIndicator,
  Tune,
  AutoAwesome,
  Visibility,
  Download,
} from "@mui/icons-material";

// Chart Type Definitions with Visual Previews
interface ChartType {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  preview: string; // Base64 or URL to mini preview
  useCases: string[];
  requiredMappings: {
    dimensions: number;
    measures: number;
  };
  optionalMappings?: string[];
}

interface DataMapping {
  id: string;
  label: string;
  type: "dimension" | "measure" | "optional";
  accepts: string[];
  icon: React.ReactNode;
  description: string;
  currentField?: any;
  required: boolean;
}

interface ChartConfiguratorProps {
  onConfigChange: (config: any) => void;
  availableFields: any[];
  initialConfig?: any;
}

// Chart Type Library with Visual Previews
const CHART_TYPES: ChartType[] = [
  {
    id: "bar",
    name: "Bar Chart",
    icon: <BarChart3 />,
    description: "Compare values across categories",
    preview: "data:image/svg+xml,%3Csvg%20viewBox%3D%220%200%2080%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Crect%20x%3D%2210%22%20y%3D%2240%22%20width%3D%2212%22%20height%3D%2215%22%20fill%3D%22%236366f1%22/%3E%3Crect%20x%3D%2225%22%20y%3D%2230%22%20width%3D%2212%22%20height%3D%2225%22%20fill%3D%22%2310b981%22/%3E%3Crect%20x%3D%2240%22%20y%3D%2235%22%20width%3D%2212%22%20height%3D%2220%22%20fill%3D%22%23f59e0b%22/%3E%3Crect%20x%3D%2255%22%20y%3D%2220%22%20width%3D%2212%22%20height%3D%2235%22%20fill%3D%22%23ef4444%22/%3E%3C/svg%3E",
    useCases: ["Category comparison", "Performance metrics", "Survey results"],
    requiredMappings: { dimensions: 1, measures: 1 },
    optionalMappings: ["color", "size"],
  },
  {
    id: "line",
    name: "Line Chart", 
    icon: <LineChart />,
    description: "Show trends over time",
    preview: "data:image/svg+xml,%3Csvg%20viewBox%3D%220%200%2080%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cpath%20d%3D%22M10%2050%20L25%2035%20L40%2040%20L55%2025%20L70%2030%22%20stroke%3D%22%236366f1%22%20stroke-width%3D%222%22%20fill%3D%22none%22/%3E%3Ccircle%20cx%3D%2210%22%20cy%3D%2250%22%20r%3D%222%22%20fill%3D%22%236366f1%22/%3E%3Ccircle%20cx%3D%2225%22%20cy%3D%2235%22%20r%3D%222%22%20fill%3D%22%236366f1%22/%3E%3Ccircle%20cx%3D%2240%22%20cy%3D%2240%22%20r%3D%222%22%20fill%3D%22%236366f1%22/%3E%3Ccircle%20cx%3D%2255%22%20cy%3D%2225%22%20r%3D%222%22%20fill%3D%22%236366f1%22/%3E%3Ccircle%20cx%3D%2270%22%20cy%3D%2230%22%20r%3D%222%22%20fill%3D%22%236366f1%22/%3E%3C/svg%3E",
    useCases: ["Time series analysis", "Trend visualization", "Performance tracking"],
    requiredMappings: { dimensions: 1, measures: 1 },
    optionalMappings: ["color", "series"],
  },
  {
    id: "pie",
    name: "Pie Chart",
    icon: <PieChart />,
    description: "Show parts of a whole",
    preview: "data:image/svg+xml,%3Csvg%20viewBox%3D%220%200%2080%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Ccircle%20cx%3D%2240%22%20cy%3D%2230%22%20r%3D%2220%22%20fill%3D%22%236366f1%22/%3E%3Cpath%20d%3D%22M40%2030%20L60%2030%20A20%2020%200%200%201%2050%2048%20Z%22%20fill%3D%22%2310b981%22/%3E%3Cpath%20d%3D%22M40%2030%20L50%2048%20A20%2020%200%200%201%2025%2040%20Z%22%20fill%3D%22%23f59e0b%22/%3E%3Cpath%20d%3D%22M40%2030%20L25%2040%20A20%2020%200%200%201%2040%2010%20Z%22%20fill%3D%22%23ef4444%22/%3E%3C/svg%3E",
    useCases: ["Market share", "Budget allocation", "Survey responses"],
    requiredMappings: { dimensions: 1, measures: 1 },
  },
  {
    id: "scatter",
    name: "Scatter Plot",
    icon: <ScatterChart />,
    description: "Explore relationships between variables",
    preview: "data:image/svg+xml,%3Csvg%20viewBox%3D%220%200%2080%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Ccircle%20cx%3D%2215%22%20cy%3D%2245%22%20r%3D%223%22%20fill%3D%22%236366f1%22/%3E%3Ccircle%20cx%3D%2225%22%20cy%3D%2235%22%20r%3D%223%22%20fill%3D%22%2310b981%22/%3E%3Ccircle%20cx%3D%2235%22%20cy%3D%2230%22%20r%3D%223%22%20fill%3D%22%23f59e0b%22/%3E%3Ccircle%20cx%3D%2245%22%20cy%3D%2225%22%20r%3D%223%22%20fill%3D%22%23ef4444%22/%3E%3Ccircle%20cx%3D%2255%22%20cy%3D%2220%22%20r%3D%223%22%20fill%3D%22%238b5cf6%22/%3E%3Ccircle%20cx%3D%2265%22%20cy%3D%2215%22%20r%3D%223%22%20fill%3D%22%2306b6d4%22/%3E%3C/svg%3E",
    useCases: ["Correlation analysis", "Performance comparison", "Risk assessment"],
    requiredMappings: { dimensions: 1, measures: 2 },
    optionalMappings: ["size", "color"],
  },
];

// Enhanced Drop Zone Component
const DataMappingZone: React.FC<{
  mapping: DataMapping;
  onDrop: (field: any) => void;
  onRemove: () => void;
  isHovering: boolean;
  isValidDrop: boolean;
}> = ({ mapping, onDrop, onRemove, isHovering, isValidDrop }) => {
  const theme = useTheme();
  
  const getBorderColor = () => {
    if (!isValidDrop && isHovering) return theme.palette.error.main;
    if (isValidDrop && isHovering) return theme.palette.success.main;
    if (mapping.currentField) return theme.palette.primary.main;
    return alpha(theme.palette.grey[300], 0.7);
  };

  const getBackgroundColor = () => {
    if (!isValidDrop && isHovering) return alpha(theme.palette.error.main, 0.1);
    if (isValidDrop && isHovering) return alpha(theme.palette.success.main, 0.1);
    if (mapping.currentField) return alpha(theme.palette.primary.main, 0.05);
    return "transparent";
  };

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        minHeight: 100,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        borderStyle: mapping.required ? "solid" : "dashed",
        borderWidth: 2,
        borderColor: getBorderColor(),
        backgroundColor: getBackgroundColor(),
        borderRadius: 2,
        position: "relative",
        transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        animation: isHovering ? "pulse 1.5s infinite" : "none",
        cursor: "pointer",
        "&:hover": {
          borderColor: mapping.currentField
            ? theme.palette.primary.dark
            : theme.palette.primary.light,
        },
      }}
      role="button"
      tabIndex={0}
      aria-label={`Drop ${mapping.accepts.join(" or ")} field here for ${mapping.label}`}
    >
      {/* Required Badge */}
      {mapping.required && !mapping.currentField && (
        <Chip
          label="Required"
          size="small"
          color="error"
          sx={{
            position: "absolute",
            top: -8,
            right: -8,
            fontSize: "0.6rem",
            height: 16,
          }}
        />
      )}

      {mapping.currentField ? (
        <Box display="flex" flexDirection="column" alignItems="center" gap={1} width="100%">
          <Box display="flex" alignItems="center" gap={1} width="100%">
            <DragIndicator sx={{ fontSize: 16, color: "text.secondary" }} />
            {mapping.icon}
            <Typography variant="body2" fontWeight="medium" flex={1} noWrap>
              {mapping.currentField.name}
            </Typography>
            <IconButton size="small" onClick={onRemove}>
              <Close fontSize="small" />
            </IconButton>
          </Box>
          <Chip
            label={mapping.currentField.type}
            size="small"
            variant="outlined"
            sx={{ fontSize: "0.7rem", height: 18 }}
          />
        </Box>
      ) : (
        <Box display="flex" flexDirection="column" alignItems="center" gap={1}>
          {mapping.icon}
          <Typography variant="body2" fontWeight="semibold" textAlign="center">
            {mapping.label}
          </Typography>
          <Typography variant="caption" color="text.secondary" textAlign="center">
            {mapping.description}
          </Typography>
          <Chip
            label={mapping.accepts.join(" | ")}
            size="small"
            variant="outlined"
            sx={{ fontSize: "0.65rem", height: 16 }}
          />
        </Box>
      )}
    </Paper>
  );
};

// Chart Type Selector with Visual Previews
const ChartTypeSelector: React.FC<{
  selectedType: string;
  onTypeChange: (type: ChartType) => void;
  availableFields: any[];
}> = ({ selectedType, onTypeChange, availableFields }) => {
  const theme = useTheme();
  
  // Smart filtering based on available data
  const getAvailableChartTypes = () => {
    const dimensions = availableFields.filter(f => f.type === "dimension").length;
    const measures = availableFields.filter(f => f.type === "measure").length;
    
    return CHART_TYPES.filter(chartType => {
      return dimensions >= chartType.requiredMappings.dimensions &&
             measures >= chartType.requiredMappings.measures;
    });
  };

  const availableChartTypes = getAvailableChartTypes();

  return (
    <Box>
      <Typography variant="h6" fontWeight="semibold" mb={2}>
        Chart Type
      </Typography>
      <Grid container spacing={2}>
        {availableChartTypes.map((chartType) => (
          <Grid item xs={6} sm={4} md={3} key={chartType.id}>
            <Card
              variant="outlined"
              sx={{
                cursor: "pointer",
                border: selectedType === chartType.id
                  ? `2px solid ${theme.palette.primary.main}`
                  : `1px solid ${alpha(theme.palette.grey[300], 0.7)}`,
                backgroundColor: selectedType === chartType.id
                  ? alpha(theme.palette.primary.main, 0.05)
                  : "transparent",
                transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                "&:hover": {
                  borderColor: theme.palette.primary.main,
                  transform: "translateY(-2px)",
                  boxShadow: theme.shadows[4],
                },
              }}
              onClick={() => onTypeChange(chartType)}
            >
              <CardContent sx={{ p: 2, textAlign: "center" }}>
                {/* Visual Preview */}
                <Box
                  sx={{
                    width: 60,
                    height: 40,
                    mx: "auto",
                    mb: 1,
                    borderRadius: 1,
                    backgroundColor: alpha(theme.palette.grey[100], 0.5),
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                  }}
                >
                  <img
                    src={chartType.preview}
                    alt={`${chartType.name} preview`}
                    style={{ width: "100%", height: "100%" }}
                  />
                </Box>
                
                {/* Icon */}
                <Box sx={{ color: selectedType === chartType.id ? "primary.main" : "text.secondary", mb: 1 }}>
                  {chartType.icon}
                </Box>
                
                {/* Name */}
                <Typography variant="body2" fontWeight="medium" mb={0.5}>
                  {chartType.name}
                </Typography>
                
                {/* Description */}
                <Typography variant="caption" color="text.secondary" display="block">
                  {chartType.description}
                </Typography>
                
                {/* Use Cases */}
                <Box mt={1}>
                  <Typography variant="caption" color="text.secondary" fontSize="0.6rem">
                    Best for: {chartType.useCases[0]}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

// Main Chart Configurator Component
const ChartConfigurator: React.FC<ChartConfiguratorProps> = ({
  onConfigChange,
  availableFields,
  initialConfig = {},
}) => {
  const theme = useTheme();
  const [selectedChartType, setSelectedChartType] = useState<ChartType>(
    CHART_TYPES.find(t => t.id === initialConfig.type) || CHART_TYPES[0]
  );
  const [mappings, setMappings] = useState<Record<string, any>>({});
  const [styleConfig, setStyleConfig] = useState({
    showLegend: true,
    showLabels: true,
    colorScheme: "default",
    gridLines: true,
    animations: true,
  });

  // Generate data mappings based on selected chart type
  const getDataMappings = (): DataMapping[] => {
    const baseMappings: DataMapping[] = [
      {
        id: "x-axis",
        label: "X-Axis",
        type: "dimension",
        accepts: ["dimension"],
        icon: <ArrowRight />,
        description: "Categories or time periods",
        required: true,
      },
      {
        id: "y-axis", 
        label: "Y-Axis",
        type: "measure",
        accepts: ["measure"],
        icon: <ArrowUp />,
        description: "Values to visualize",
        required: true,
      },
    ];

    // Add optional mappings based on chart type
    if (selectedChartType.optionalMappings?.includes("color")) {
      baseMappings.push({
        id: "color",
        label: "Color",
        type: "optional",
        accepts: ["dimension", "measure"],
        icon: <Palette />,
        description: "Group by color",
        required: false,
      });
    }

    if (selectedChartType.id === "scatter" && selectedChartType.optionalMappings?.includes("size")) {
      baseMappings.push({
        id: "size",
        label: "Size",
        type: "optional",
        accepts: ["measure"],
        icon: <Settings />,
        description: "Bubble size",
        required: false,
      });
    }

    return baseMappings.map(mapping => ({
      ...mapping,
      currentField: mappings[mapping.id],
    }));
  };

  const handleFieldDrop = (mappingId: string, field: any) => {
    const newMappings = { ...mappings, [mappingId]: field };
    setMappings(newMappings);
    
    // Update configuration
    onConfigChange({
      type: selectedChartType.id,
      mappings: newMappings,
      style: styleConfig,
    });
  };

  const handleFieldRemove = (mappingId: string) => {
    const newMappings = { ...mappings };
    delete newMappings[mappingId];
    setMappings(newMappings);
    
    onConfigChange({
      type: selectedChartType.id,
      mappings: newMappings,
      style: styleConfig,
    });
  };

  const handleChartTypeChange = (chartType: ChartType) => {
    setSelectedChartType(chartType);
    // Clear incompatible mappings
    const newMappings = { ...mappings };
    // Implementation for clearing incompatible mappings
    setMappings(newMappings);
    
    onConfigChange({
      type: chartType.id,
      mappings: newMappings,
      style: styleConfig,
    });
  };

  const dataMappings = getDataMappings();

  return (
    <Box sx={{ maxWidth: 1200, mx: "auto", p: 3 }}>
      {/* Chart Type Selection */}
      <Paper elevation={1} sx={{ p: 3, mb: 3, borderRadius: 3 }}>
        <ChartTypeSelector
          selectedType={selectedChartType.id}
          onTypeChange={handleChartTypeChange}
          availableFields={availableFields}
        />
      </Paper>

      {/* Data Mapping Configuration */}
      <Paper elevation={1} sx={{ p: 3, mb: 3, borderRadius: 3 }}>
        <Box display="flex" alignItems="center" gap={1} mb={3}>
          <AutoAwesome color="primary" />
          <Typography variant="h6" fontWeight="semibold">
            Data Mapping
          </Typography>
          <Chip label="Drag & Drop" size="small" variant="outlined" />
        </Box>
        
        <Grid container spacing={2}>
          {dataMappings.map((mapping) => (
            <Grid item xs={12} sm={6} md={4} key={mapping.id}>
              <DataMappingZone
                mapping={mapping}
                onDrop={(field) => handleFieldDrop(mapping.id, field)}
                onRemove={() => handleFieldRemove(mapping.id)}
                isHovering={false} // This would be connected to drag state
                isValidDrop={true} // This would be validation logic
              />
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Style Configuration - Progressive Disclosure */}
      <Paper elevation={1} sx={{ borderRadius: 3 }}>
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box display="flex" alignItems="center" gap={1}>
              <Tune />
              <Typography variant="h6" fontWeight="semibold">
                Style & Options
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" fontWeight="medium" mb={2}>
                  Display Options
                </Typography>
                <Box display="flex" flexDirection="column" gap={2}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={styleConfig.showLegend}
                        onChange={(e) => setStyleConfig(prev => ({ ...prev, showLegend: e.target.checked }))}
                      />
                    }
                    label="Show Legend"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={styleConfig.showLabels}
                        onChange={(e) => setStyleConfig(prev => ({ ...prev, showLabels: e.target.checked }))}
                      />
                    }
                    label="Show Data Labels"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={styleConfig.gridLines}
                        onChange={(e) => setStyleConfig(prev => ({ ...prev, gridLines: e.target.checked }))}
                      />
                    }
                    label="Grid Lines"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={styleConfig.animations}
                        onChange={(e) => setStyleConfig(prev => ({ ...prev, animations: e.target.checked }))}
                      />
                    }
                    label="Animations"
                  />
                </Box>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" fontWeight="medium" mb={2}>
                  Color Scheme
                </Typography>
                <FormControl fullWidth>
                  <InputLabel>Color Palette</InputLabel>
                  <Select
                    value={styleConfig.colorScheme}
                    label="Color Palette"
                    onChange={(e) => setStyleConfig(prev => ({ ...prev, colorScheme: e.target.value }))}
                  >
                    <MenuItem value="default">Default</MenuItem>
                    <MenuItem value="colorful">Colorful</MenuItem>
                    <MenuItem value="monochrome">Monochrome</MenuItem>
                    <MenuItem value="corporate">Corporate</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Paper>

      {/* Quick Actions */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mt={3}>
        <Box display="flex" gap={1}>
          <Chip label="Ready to generate" color="success" variant="outlined" />
          <Chip label={`${Object.keys(mappings).length} fields mapped`} variant="outlined" />
        </Box>
        
        <Box display="flex" gap={1}>
          <IconButton>
            <Visibility />
          </IconButton>
          <IconButton>
            <Download />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

export default ChartConfigurator;
