/**
 * Context-Aware Property Panels for Next-Gen Report Builder
 * Adaptive interfaces that change based on selected elements
 * Focus: Context sensitivity, Progressive disclosure, Smart defaults
 */

import React, { useState, useCallback, useMemo } from "react";
import {
  Box,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Slider,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Button,
  Divider,
  Grid,
  Card,
  CardContent,
  Tooltip,
  alpha,
  useTheme,
} from "@mui/material";
import {
  ExpandMore,
  Palette,
  Tune,
  Visibility,
  Code,
  Settings,
  AutoAwesome,
  ContentCopy,
  Refresh,
  Help,
  BarChart as BarChart3,
  TrendingUp as LineChart,
  PieChart,
  TableChart,
  TextFields,
  Image as ImageIcon,
} from "@mui/icons-material";

// Context-aware panel configurations
interface PanelConfig {
  primary: string[];
  secondary: string[];
  advanced: string[];
  smartDefaults: Record<string, any>;
}

interface ElementContext {
  type: "chart" | "table" | "text" | "image" | "heading";
  subtype?: string;
  properties: Record<string, any>;
  dataFields: any[];
  suggestions: any[];
}

// Smart panel configuration based on element type
const getPanelConfig = (context: ElementContext): PanelConfig => {
  const configs: Record<string, PanelConfig> = {
    chart: {
      primary: ["Chart Type", "Data Mapping", "Colors"],
      secondary: ["Legend", "Labels", "Interactions"],
      advanced: ["Custom Calculations", "Animation", "Export Options"],
      smartDefaults: {
        showLegend: true,
        showLabels: false,
        colorScheme: "professional",
        animation: true,
      },
    },
    table: {
      primary: ["Columns", "Sorting", "Filtering"],
      secondary: ["Styling", "Pagination", "Export"],
      advanced: ["Custom Formatting", "Conditional Logic", "Calculations"],
      smartDefaults: {
        sortable: true,
        filterable: true,
        pagination: true,
        alternateRows: true,
      },
    },
    text: {
      primary: ["Content", "Typography", "Alignment"],
      secondary: ["Spacing", "Background", "Border"],
      advanced: ["Custom CSS", "Responsive Behavior"],
      smartDefaults: {
        fontSize: 14,
        fontWeight: "normal",
        textAlign: "left",
        lineHeight: 1.5,
      },
    },
    image: {
      primary: ["Source", "Size", "Position"],
      secondary: ["Caption", "Border", "Effects"],
      advanced: ["Responsive Behavior", "Accessibility"],
      smartDefaults: {
        altText: "",
        responsive: true,
        aspectRatio: "auto",
      },
    },
    heading: {
      primary: ["Text", "Level", "Style"],
      secondary: ["Color", "Spacing", "Alignment"],
      advanced: ["Custom CSS", "Anchor Links"],
      smartDefaults: {
        level: 2,
        fontWeight: "bold",
        color: "inherit",
      },
    },
  };

  return configs[context.type] || configs.text;
};

// Chart-specific property panel
const ChartPropertyPanel: React.FC<{
  context: ElementContext;
  onChange: (properties: Record<string, any>) => void;
}> = ({ context, onChange }) => {
  const theme = useTheme();
  const [properties, setProperties] = useState(context.properties);

  const handlePropertyChange = useCallback((key: string, value: any) => {
    const newProperties = { ...properties, [key]: value };
    setProperties(newProperties);
    onChange(newProperties);
  }, [properties, onChange]);

  const chartTypes = [
    { value: "bar", label: "Bar Chart", icon: <BarChart3 /> },
    { value: "line", label: "Line Chart", icon: <LineChart /> },
    { value: "pie", label: "Pie Chart", icon: <PieChart /> },
  ];

  const colorSchemes = [
    { value: "professional", label: "Professional", colors: ["#2563eb", "#10b981", "#f59e0b"] },
    { value: "vibrant", label: "Vibrant", colors: ["#ef4444", "#8b5cf6", "#06b6d4"] },
    { value: "monochrome", label: "Monochrome", colors: ["#374151", "#6b7280", "#9ca3af"] },
  ];

  return (
    <Box>
      {/* Primary Controls */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <BarChart3 color="primary" />
            <Typography variant="h6">Chart Type</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <FormControl fullWidth>
            <InputLabel>Chart Type</InputLabel>
            <Select
              value={properties.chartType || "bar"}
              label="Chart Type"
              onChange={(e) => handlePropertyChange("chartType", e.target.value)}
            >
              {chartTypes.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  <Box display="flex" alignItems="center" gap={1}>
                    {type.icon}
                    {type.label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </AccordionDetails>
      </Accordion>

      {/* Color Scheme */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Palette color="primary" />
            <Typography variant="h6">Colors</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Color Scheme
            </Typography>
            <Grid container spacing={1} mb={2}>
              {colorSchemes.map((scheme) => (
                <Grid item xs={12} key={scheme.value}>
                  <Card
                    variant={properties.colorScheme === scheme.value ? "outlined" : "elevation"}
                    sx={{
                      cursor: "pointer",
                      borderColor: properties.colorScheme === scheme.value 
                        ? "primary.main" 
                        : "transparent",
                      borderWidth: 2,
                      "&:hover": {
                        backgroundColor: alpha(theme.palette.primary.main, 0.04),
                      },
                    }}
                    onClick={() => handlePropertyChange("colorScheme", scheme.value)}
                  >
                    <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Typography variant="body2" fontWeight="medium">
                          {scheme.label}
                        </Typography>
                        <Box display="flex" gap={0.5}>
                          {scheme.colors.map((color, index) => (
                            <Box
                              key={index}
                              sx={{
                                width: 16,
                                height: 16,
                                backgroundColor: color,
                                borderRadius: "50%",
                                border: "1px solid",
                                borderColor: "divider",
                              }}
                            />
                          ))}
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Display Options */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Visibility color="primary" />
            <Typography variant="h6">Display</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={properties.showLegend ?? true}
                  onChange={(e) => handlePropertyChange("showLegend", e.target.checked)}
                />
              }
              label="Show Legend"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={properties.showLabels ?? false}
                  onChange={(e) => handlePropertyChange("showLabels", e.target.checked)}
                />
              }
              label="Show Data Labels"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={properties.showGrid ?? true}
                  onChange={(e) => handlePropertyChange("showGrid", e.target.checked)}
                />
              }
              label="Show Grid Lines"
            />
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Advanced Options */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Settings color="primary" />
            <Typography variant="h6">Advanced</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={3}>
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Animation Duration (seconds)
              </Typography>
              <Slider
                value={properties.animationDuration ?? 1}
                onChange={(_, value) => handlePropertyChange("animationDuration", value)}
                min={0}
                max={3}
                step={0.1}
                marks={[
                  { value: 0, label: "0s" },
                  { value: 1, label: "1s" },
                  { value: 2, label: "2s" },
                  { value: 3, label: "3s" },
                ]}
                valueLabelDisplay="auto"
              />
            </Box>
            
            <TextField
              label="Custom CSS Classes"
              value={properties.customClasses || ""}
              onChange={(e) => handlePropertyChange("customClasses", e.target.value)}
              placeholder="custom-chart-style"
              helperText="Space-separated CSS class names"
              fullWidth
              size="small"
            />
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

// Table-specific property panel
const TablePropertyPanel: React.FC<{
  context: ElementContext;
  onChange: (properties: Record<string, any>) => void;
}> = ({ context, onChange }) => {
  const [properties, setProperties] = useState(context.properties);

  const handlePropertyChange = useCallback((key: string, value: any) => {
    const newProperties = { ...properties, [key]: value };
    setProperties(newProperties);
    onChange(newProperties);
  }, [properties, onChange]);

  return (
    <Box>
      {/* Column Configuration */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <TableChart color="primary" />
            <Typography variant="h6">Columns</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={2}>
            {context.dataFields.map((field, index) => (
              <Box key={field.id} display="flex" alignItems="center" gap={2}>
                <TextField
                  label="Column Header"
                  value={field.displayName || field.name}
                  onChange={(e) => {
                    // Update field display name
                  }}
                  size="small"
                  sx={{ flex: 1 }}
                />
                <FormControl size="small" sx={{ minWidth: 100 }}>
                  <InputLabel>Type</InputLabel>
                  <Select value={field.dataType} label="Type">
                    <MenuItem value="text">Text</MenuItem>
                    <MenuItem value="number">Number</MenuItem>
                    <MenuItem value="date">Date</MenuItem>
                    <MenuItem value="currency">Currency</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            ))}
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Table Features */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Tune color="primary" />
            <Typography variant="h6">Features</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={2}>
            <FormControlLabel
              control={
                <Switch
                  checked={properties.sortable ?? true}
                  onChange={(e) => handlePropertyChange("sortable", e.target.checked)}
                />
              }
              label="Sortable Columns"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={properties.filterable ?? false}
                  onChange={(e) => handlePropertyChange("filterable", e.target.checked)}
                />
              }
              label="Column Filters"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={properties.pagination ?? true}
                  onChange={(e) => handlePropertyChange("pagination", e.target.checked)}
                />
              }
              label="Pagination"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={properties.alternateRows ?? true}
                  onChange={(e) => handlePropertyChange("alternateRows", e.target.checked)}
                />
              }
              label="Alternate Row Colors"
            />
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

// Text/Heading property panel
const TextPropertyPanel: React.FC<{
  context: ElementContext;
  onChange: (properties: Record<string, any>) => void;
}> = ({ context, onChange }) => {
  const [properties, setProperties] = useState(context.properties);

  const handlePropertyChange = useCallback((key: string, value: any) => {
    const newProperties = { ...properties, [key]: value };
    setProperties(newProperties);
    onChange(newProperties);
  }, [properties, onChange]);

  const fontSizes = [12, 14, 16, 18, 20, 24, 28, 32, 36, 42, 48];
  const fontWeights = [
    { value: "normal", label: "Normal" },
    { value: "medium", label: "Medium" },
    { value: "semibold", label: "Semi Bold" },
    { value: "bold", label: "Bold" },
  ];

  return (
    <Box>
      {/* Content */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <TextFields color="primary" />
            <Typography variant="h6">Content</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <TextField
            label={context.type === "heading" ? "Heading Text" : "Text Content"}
            value={properties.content || ""}
            onChange={(e) => handlePropertyChange("content", e.target.value)}
            multiline={context.type !== "heading"}
            rows={context.type === "heading" ? 1 : 4}
            fullWidth
            placeholder={context.type === "heading" ? "Enter heading..." : "Enter text content..."}
          />
        </AccordionDetails>
      </Accordion>

      {/* Typography */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Palette color="primary" />
            <Typography variant="h6">Typography</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={2}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Font Size</InputLabel>
                  <Select
                    value={properties.fontSize || 14}
                    label="Font Size"
                    onChange={(e) => handlePropertyChange("fontSize", e.target.value)}
                  >
                    {fontSizes.map((size) => (
                      <MenuItem key={size} value={size}>
                        {size}px
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Font Weight</InputLabel>
                  <Select
                    value={properties.fontWeight || "normal"}
                    label="Font Weight"
                    onChange={(e) => handlePropertyChange("fontWeight", e.target.value)}
                  >
                    {fontWeights.map((weight) => (
                      <MenuItem key={weight.value} value={weight.value}>
                        {weight.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            <FormControl fullWidth size="small">
              <InputLabel>Text Alignment</InputLabel>
              <Select
                value={properties.textAlign || "left"}
                label="Text Alignment"
                onChange={(e) => handlePropertyChange("textAlign", e.target.value)}
              >
                <MenuItem value="left">Left</MenuItem>
                <MenuItem value="center">Center</MenuItem>
                <MenuItem value="right">Right</MenuItem>
                <MenuItem value="justify">Justify</MenuItem>
              </Select>
            </FormControl>

            {context.type === "heading" && (
              <FormControl fullWidth size="small">
                <InputLabel>Heading Level</InputLabel>
                <Select
                  value={properties.level || 2}
                  label="Heading Level"
                  onChange={(e) => handlePropertyChange("level", e.target.value)}
                >
                  {[1, 2, 3, 4, 5, 6].map((level) => (
                    <MenuItem key={level} value={level}>
                      H{level}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

// Smart suggestions panel
const SmartSuggestionsPanel: React.FC<{
  context: ElementContext;
  onApplySuggestion: (suggestion: any) => void;
}> = ({ context, onApplySuggestion }) => {
  const suggestions = useMemo(() => {
    // Generate context-aware suggestions
    const baseSuggestions = [
      {
        id: "optimize-colors",
        title: "Optimize Color Scheme",
        description: "Apply professional color palette for better readability",
        confidence: 0.9,
        icon: <Palette />,
      },
      {
        id: "improve-typography",
        title: "Improve Typography",
        description: "Adjust font sizes and spacing for better hierarchy",
        confidence: 0.85,
        icon: <TextFields />,
      },
      {
        id: "add-interactivity",
        title: "Add Interactivity",
        description: "Enable hover effects and tooltips for better UX",
        confidence: 0.75,
        icon: <Settings />,
      },
    ];

    return baseSuggestions;
  }, [context]);

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={1} mb={2}>
        <AutoAwesome color="primary" />
        <Typography variant="h6">Smart Suggestions</Typography>
      </Box>
      
      <Box display="flex" flexDirection="column" gap={1}>
        {suggestions.map((suggestion) => (
          <Card
            key={suggestion.id}
            variant="outlined"
            sx={{
              cursor: "pointer",
              transition: "all 0.2s ease",
              "&:hover": {
                backgroundColor: alpha("#6366f1", 0.04),
                borderColor: "#6366f1",
              },
            }}
            onClick={() => onApplySuggestion(suggestion)}
          >
            <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
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
                  <Typography variant="caption" color="text.secondary">
                    {suggestion.description}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
};

// Main contextual panel component
const ContextualPropertyPanel: React.FC<{
  selectedElement: any;
  onPropertyChange: (elementId: string, properties: Record<string, any>) => void;
}> = ({ selectedElement, onPropertyChange }) => {
  if (!selectedElement) {
    return (
      <Box p={2}>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          Select an element to view its properties
        </Typography>
      </Box>
    );
  }

  const context: ElementContext = {
    type: selectedElement.type,
    subtype: selectedElement.subtype,
    properties: selectedElement.properties || {},
    dataFields: selectedElement.dataFields || [],
    suggestions: [],
  };

  const handlePropertyChange = useCallback((properties: Record<string, any>) => {
    onPropertyChange(selectedElement.id, properties);
  }, [selectedElement.id, onPropertyChange]);

  const handleApplySuggestion = useCallback((suggestion: any) => {
    // Implementation for applying suggestions
  }, []);

  const renderPropertyPanel = () => {
    switch (context.type) {
      case "chart":
        return (
          <ChartPropertyPanel
            context={context}
            onChange={handlePropertyChange}
          />
        );
      case "table":
        return (
          <TablePropertyPanel
            context={context}
            onChange={handlePropertyChange}
          />
        );
      case "text":
      case "heading":
        return (
          <TextPropertyPanel
            context={context}
            onChange={handlePropertyChange}
          />
        );
      default:
        return (
          <Typography variant="body2" color="text.secondary">
            Properties panel for {context.type} coming soon...
          </Typography>
        );
    }
  };

  return (
    <Box>
      {/* Element Info Header */}
      <Box p={2} borderBottom={1} borderColor="divider">
        <Typography variant="h6" fontWeight="semibold">
          {selectedElement.title || `${context.type} Element`}
        </Typography>
        <Chip
          label={context.type}
          size="small"
          sx={{ mt: 1, textTransform: "capitalize" }}
        />
      </Box>

      {/* Properties */}
      <Box p={2}>
        {renderPropertyPanel()}
      </Box>

      <Divider />

      {/* Smart Suggestions */}
      <Box p={2}>
        <SmartSuggestionsPanel
          context={context}
          onApplySuggestion={handleApplySuggestion}
        />
      </Box>
    </Box>
  );
};

export default ContextualPropertyPanel;
export {
  ChartPropertyPanel,
  TablePropertyPanel,
  TextPropertyPanel,
  SmartSuggestionsPanel,
};
