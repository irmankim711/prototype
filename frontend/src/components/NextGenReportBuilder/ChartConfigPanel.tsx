/**
 * Chart Configuration Panel
 * Allows users to configure chart settings, data mappings, and styling
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Chip,
  Divider,
  alpha,
  useTheme,
} from '@mui/material';
import {
  ExpandMore,
  Tune,
  Palette,
  DataObject,
  Settings,
  Refresh,
} from '@mui/icons-material';
import type { ChartConfig, ChartData } from './types';

interface ChartConfigPanelProps {
  config: ChartConfig;
  availableFields: any[];
  onConfigChange: (config: ChartConfig) => void;
  onGenerateChart: () => void;
  isLoading?: boolean;
}

const ChartConfigPanel: React.FC<ChartConfigPanelProps> = ({
  config,
  availableFields,
  onConfigChange,
  onGenerateChart,
  isLoading = false,
}) => {
  const theme = useTheme();
  const [localConfig, setLocalConfig] = useState<ChartConfig>(config);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  const handleConfigChange = (updates: Partial<ChartConfig>) => {
    const newConfig = { ...localConfig, ...updates };
    setLocalConfig(newConfig);
    onConfigChange(newConfig);
  };

  const getFieldOptions = (type: 'dimension' | 'measure') => {
    return availableFields
      .filter(field => field.type === type)
      .map(field => ({
        value: field.id,
        label: field.name,
        description: field.description,
      }));
  };

  const chartTypes = [
    { value: 'bar', label: 'Bar Chart', description: 'Compare values across categories' },
    { value: 'line', label: 'Line Chart', description: 'Show trends over time' },
    { value: 'area', label: 'Area Chart', description: 'Show trends with filled areas' },
    { value: 'pie', label: 'Pie Chart', description: 'Show parts of a whole' },
    { value: 'doughnut', label: 'Doughnut Chart', description: 'Pie chart with center cutout' },
    { value: 'scatter', label: 'Scatter Plot', description: 'Show correlation between variables' },
  ];

  const colorSchemes = [
    { value: 'default', label: 'Default', description: 'Material Design colors' },
    { value: 'colorful', label: 'Colorful', description: 'Vibrant color palette' },
    { value: 'monochrome', label: 'Monochrome', description: 'Single color variations' },
    { value: 'professional', label: 'Professional', description: 'Business-appropriate colors' },
  ];

  return (
    <Box sx={{ p: 2 }}>
      <Box display="flex" alignItems="center" gap={1} mb={3}>
        <Tune color="primary" />
        <Typography variant="h6" fontWeight="semibold">
          Chart Configuration
        </Typography>
      </Box>

      {/* Basic Configuration */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Settings fontSize="small" />
            <Typography variant="subtitle1" fontWeight="medium">
              Basic Settings
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={2}>
            {/* Chart Type */}
            <FormControl fullWidth>
              <InputLabel>Chart Type</InputLabel>
              <Select
                value={localConfig.type}
                label="Chart Type"
                onChange={(e) => handleConfigChange({ type: e.target.value as ChartConfig['type'] })}
              >
                {chartTypes.map((type) => (
                  <MenuItem key={type.value} value={type.value}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {type.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {type.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Chart Title */}
            <TextField
              fullWidth
              label="Chart Title"
              value={localConfig.title}
              onChange={(e) => handleConfigChange({ title: e.target.value })}
              placeholder="Enter chart title"
            />
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Data Mapping */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <DataObject fontSize="small" />
            <Typography variant="subtitle1" fontWeight="medium">
              Data Mapping
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={2}>
            {/* X-Axis */}
            <FormControl fullWidth>
              <InputLabel>X-Axis Field</InputLabel>
              <Select
                value={localConfig.xAxis?.field || ''}
                label="X-Axis Field"
                onChange={(e) => handleConfigChange({
                  xAxis: {
                    ...localConfig.xAxis,
                    field: e.target.value,
                    label: availableFields.find(f => f.id === e.target.value)?.name || '',
                    type: availableFields.find(f => f.id === e.target.value)?.dataType === 'temporal' ? 'temporal' : 'dimension'
                  }
                })}
              >
                {getFieldOptions('dimension').map((field) => (
                  <MenuItem key={field.value} value={field.value}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {field.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {field.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Y-Axis */}
            <FormControl fullWidth>
              <InputLabel>Y-Axis Field</InputLabel>
              <Select
                value={localConfig.yAxis?.field || ''}
                label="Y-Axis Field"
                onChange={(e) => handleConfigChange({
                  yAxis: {
                    ...localConfig.yAxis,
                    field: e.target.value,
                    label: availableFields.find(f => f.id === e.target.value)?.name || '',
                    type: 'measure'
                  }
                })}
              >
                {getFieldOptions('measure').map((field) => (
                  <MenuItem key={field.value} value={field.value}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {field.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {field.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* X-Axis Label */}
            <TextField
              fullWidth
              label="X-Axis Label"
              value={localConfig.xAxis?.label || ''}
              onChange={(e) => handleConfigChange({
                xAxis: { ...localConfig.xAxis, label: e.target.value }
              })}
              placeholder="Enter X-axis label"
            />

            {/* Y-Axis Label */}
            <TextField
              fullWidth
              label="Y-Axis Label"
              value={localConfig.yAxis?.label || ''}
              onChange={(e) => handleConfigChange({
                yAxis: { ...localConfig.yAxis, label: e.target.value }
              })}
              placeholder="Enter Y-axis label"
            />
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Styling Options */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Palette fontSize="small" />
            <Typography variant="subtitle1" fontWeight="medium">
              Styling & Appearance
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box display="flex" flexDirection="column" gap={2}>
            {/* Color Scheme */}
            <FormControl fullWidth>
              <InputLabel>Color Scheme</InputLabel>
              <Select
                value={localConfig.colorScheme || 'default'}
                label="Color Scheme"
                onChange={(e) => handleConfigChange({ colorScheme: e.target.value as ChartConfig['colorScheme'] })}
              >
                {colorSchemes.map((scheme) => (
                  <MenuItem key={scheme.value} value={scheme.value}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">
                        {scheme.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {scheme.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Display Options */}
            <Box>
              <Typography variant="body2" fontWeight="medium" mb={1}>
                Display Options
              </Typography>
              <Box display="flex" flexDirection="column" gap={1}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={localConfig.showLegend !== false}
                      onChange={(e) => handleConfigChange({ showLegend: e.target.checked })}
                    />
                  }
                  label="Show Legend"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={localConfig.showGrid !== false}
                      onChange={(e) => handleConfigChange({ showGrid: e.target.checked })}
                    />
                  }
                  label="Show Grid"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={localConfig.animation !== false}
                      onChange={(e) => handleConfigChange({ animation: e.target.checked })}
                    />
                  }
                  label="Enable Animations"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={localConfig.responsive !== false}
                      onChange={(e) => handleConfigChange({ responsive: e.target.checked })}
                    />
                  }
                  label="Responsive Chart"
                />
              </Box>
            </Box>

            {/* Animation Duration */}
            {localConfig.animation !== false && (
              <Box>
                <Typography variant="body2" fontWeight="medium" mb={1}>
                  Animation Duration: {localConfig.animation ? '1000ms' : '0ms'}
                </Typography>
                <Slider
                  value={1000}
                  min={0}
                  max={2000}
                  step={100}
                  onChange={(_, value) => handleConfigChange({ animation: value as number })}
                  valueLabelDisplay="auto"
                  valueLabelFormat={(value) => `${value}ms`}
                />
              </Box>
            )}
          </Box>
        </AccordionDetails>
      </Accordion>

      <Divider sx={{ my: 2 }} />

      {/* Action Buttons */}
      <Box display="flex" gap={1}>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={onGenerateChart}
          disabled={isLoading || !localConfig.xAxis?.field || !localConfig.yAxis?.field}
          fullWidth
        >
          {isLoading ? 'Generating...' : 'Generate Chart'}
        </Button>
      </Box>

      {/* Configuration Summary */}
      <Box mt={2}>
        <Typography variant="caption" color="text.secondary" display="block" mb={1}>
          Configuration Summary
        </Typography>
        <Box display="flex" flexWrap="wrap" gap={0.5}>
          <Chip 
            label={localConfig.type} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
          {localConfig.xAxis?.field && (
            <Chip 
              label={`X: ${availableFields.find(f => f.id === localConfig.xAxis?.field)?.name || 'Unknown'}`} 
              size="small" 
              color="secondary" 
              variant="outlined"
            />
          )}
          {localConfig.yAxis?.field && (
            <Chip 
              label={`Y: ${availableFields.find(f => f.id === localConfig.yAxis?.field)?.name || 'Unknown'}`} 
              size="small" 
              color="success" 
              variant="outlined"
            />
          )}
          <Chip 
            label={localConfig.colorScheme || 'default'} 
            size="small" 
            color="info" 
            variant="outlined"
          />
        </Box>
      </Box>
    </Box>
  );
};

export default ChartConfigPanel;
