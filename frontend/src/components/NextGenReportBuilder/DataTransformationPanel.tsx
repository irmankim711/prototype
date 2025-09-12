/**
 * Data Transformation Panel
 * Allows users to filter, transform, and manipulate data with advanced operations
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Grid,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Alert,
  IconButton,
  Tooltip,
  alpha,
  useTheme,
} from '@mui/material';
import {
  ExpandMore,
  Transform,
  FilterList,
  Add,
  Delete,
  Refresh,
  DataObject,
  Functions,
  Clear,
} from '@mui/icons-material';
import type { RawDataPoint, DataField } from './types';
import { advancedDataService } from '../../services/advancedDataService';

interface DataTransformationPanelProps {
  data: RawDataPoint[];
  fields: DataField[];
  onDataTransformed: (transformedData: RawDataPoint[]) => void;
  onFiltersApplied: (filteredData: RawDataPoint[]) => void;
}

interface FilterRule {
  id: string;
  field: string;
  operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'not_contains' | 'between' | 'in';
  value: any;
  value2?: any;
  enabled: boolean;
}

interface TransformationRule {
  id: string;
  field: string;
  operation: 'normalize' | 'standardize' | 'log' | 'sqrt' | 'square' | 'round' | 'floor' | 'ceil';
  newField?: string;
  enabled: boolean;
}

const DataTransformationPanel: React.FC<DataTransformationPanelProps> = ({
  data,
  fields,
  onDataTransformed,
  onFiltersApplied,
}) => {
  const theme = useTheme();
  const [filters, setFilters] = useState<FilterRule[]>([]);
  const [transformations, setTransformations] = useState<TransformationRule[]>([]);
  const [filteredData, setFilteredData] = useState<RawDataPoint[]>(data);
  const [transformedData, setTransformedData] = useState<RawDataPoint[]>(data);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setFilteredData(data);
    setTransformedData(data);
  }, [data]);

  const addFilter = () => {
    const newFilter: FilterRule = {
      id: `filter_${Date.now()}`,
      field: fields[0]?.id || '',
      operator: 'equals',
      value: '',
      enabled: true,
    };
    setFilters([...filters, newFilter]);
  };

  const removeFilter = (id: string) => {
    setFilters(filters.filter(f => f.id !== id));
  };

  const updateFilter = (id: string, updates: Partial<FilterRule>) => {
    setFilters(filters.map(f => f.id === id ? { ...f, ...updates } : f));
  };

  const addTransformation = () => {
    const newTransformation: TransformationRule = {
      id: `transform_${Date.now()}`,
      field: fields.filter(f => f.dataType === 'numerical')[0]?.id || '',
      operation: 'normalize',
      enabled: true,
    };
    setTransformations([...transformations, newTransformation]);
  };

  const removeTransformation = (id: string) => {
    setTransformations(transformations.filter(t => t.id !== id));
  };

  const updateTransformation = (id: string, updates: Partial<TransformationRule>) => {
    setTransformations(transformations.map(t => t.id === id ? { ...t, ...updates } : t));
  };

  const applyFilters = async () => {
    try {
      setIsProcessing(true);
      setError(null);

      const enabledFilters = filters.filter(f => f.enabled);
      if (enabledFilters.length === 0) {
        setFilteredData(data);
        onFiltersApplied(data);
        return;
      }

      const filtered = advancedDataService.advancedFilter(data, enabledFilters);
      setFilteredData(filtered);
      onFiltersApplied(filtered);
    } catch (err: any) {
      setError(err.message || 'Failed to apply filters');
    } finally {
      setIsProcessing(false);
    }
  };

  const applyTransformations = async () => {
    try {
      setIsProcessing(true);
      setError(null);

      const enabledTransformations = transformations.filter(t => t.enabled);
      if (enabledTransformations.length === 0) {
        setTransformedData(filteredData);
        onDataTransformed(filteredData);
        return;
      }

      const transformed = advancedDataService.transformData(filteredData, enabledTransformations);
      setTransformedData(transformed);
      onDataTransformed(transformed);
    } catch (err: any) {
      setError(err.message || 'Failed to apply transformations');
    } finally {
      setIsProcessing(false);
    }
  };

  const clearAll = () => {
    setFilters([]);
    setTransformations([]);
    setFilteredData(data);
    setTransformedData(data);
    onFiltersApplied(data);
    onDataTransformed(data);
  };

  const getValidOperators = (fieldType: string) => {
    const allOperators = [
      { value: 'equals', label: 'Equals' },
      { value: 'not_equals', label: 'Not Equals' },
      { value: 'greater_than', label: 'Greater Than' },
      { value: 'less_than', label: 'Less Than' },
      { value: 'contains', label: 'Contains' },
      { value: 'not_contains', label: 'Not Contains' },
      { value: 'between', label: 'Between' },
      { value: 'in', label: 'In List' },
    ];

    if (fieldType === 'numerical') {
      return allOperators.filter(op => ['equals', 'not_equals', 'greater_than', 'less_than', 'between', 'in'].includes(op.value));
    }
    if (fieldType === 'temporal') {
      return allOperators.filter(op => ['equals', 'not_equals', 'greater_than', 'less_than', 'between'].includes(op.value));
    }
    return allOperators.filter(op => ['equals', 'not_equals', 'contains', 'not_contains', 'in'].includes(op.value));
  };

  const getValidOperations = (fieldType: string) => {
    if (fieldType !== 'numerical') return [];
    
    return [
      { value: 'normalize', label: 'Normalize' },
      { value: 'standardize', label: 'Standardize' },
      { value: 'log', label: 'Log' },
      { value: 'sqrt', label: 'Square Root' },
      { value: 'square', label: 'Square' },
      { value: 'round', label: 'Round' },
      { value: 'floor', label: 'Floor' },
      { value: 'ceil', label: 'Ceiling' },
    ];
  };

  const renderFilterValueInput = (filter: FilterRule) => {
    const fieldType = fields.find(f => f.id === filter.field)?.dataType || 'categorical';
    
    if (filter.operator === 'between') {
      return (
        <Box display="flex" gap={1} alignItems="center">
          <TextField
            size="small"
            placeholder="Min value"
            value={filter.value || ''}
            onChange={(e) => updateFilter(filter.id, { value: e.target.value })}
            sx={{ minWidth: 120 }}
          />
          <Typography variant="body2" color="text.secondary">to</Typography>
          <TextField
            size="small"
            placeholder="Max value"
            value={filter.value2 || ''}
            onChange={(e) => updateFilter(filter.id, { value2: e.target.value })}
            sx={{ minWidth: 120 }}
          />
        </Box>
      );
    }

    if (filter.operator === 'in') {
      return (
        <TextField
          size="small"
          placeholder="Value1, Value2, Value3"
          value={filter.value || ''}
          onChange={(e) => updateFilter(filter.id, { value: e.target.value })}
          helperText="Separate values with commas"
          fullWidth
        />
      );
    }

    if (fieldType === 'temporal') {
      return (
        <TextField
          size="small"
          type="date"
          value={filter.value || ''}
          onChange={(e) => updateFilter(filter.id, { value: e.target.value })}
          fullWidth
        />
      );
    }

    return (
      <TextField
        size="small"
        placeholder="Enter value"
        value={filter.value || ''}
        onChange={(e) => updateFilter(filter.id, { value: e.target.value })}
        fullWidth
      />
    );
  };

  return (
    <Box sx={{ p: 2 }}>
      <Box display="flex" alignItems="center" gap={1} mb={3}>
        <Transform color="primary" />
        <Typography variant="h6" fontWeight="semibold">
          Data Transformation & Filtering
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Data Filters */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <FilterList fontSize="small" />
            <Typography variant="subtitle1" fontWeight="medium">
              Data Filters
            </Typography>
            {filters.length > 0 && (
              <Chip
                label={`${filters.filter(f => f.enabled).length} active`}
                size="small"
                color="primary"
                variant="outlined"
              />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box mb={2}>
            <Button
              variant="outlined"
              startIcon={<Add />}
              onClick={addFilter}
              size="small"
            >
              Add Filter
            </Button>
          </Box>

          {filters.length === 0 ? (
            <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
              No filters configured. Add a filter to start filtering your data.
            </Typography>
          ) : (
            <List>
              {filters.map((filter) => (
                <ListItem
                  key={filter.id}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    backgroundColor: alpha(theme.palette.background.paper, 0.5),
                  }}
                >
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={3}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Field</InputLabel>
                        <Select
                          value={filter.field}
                          label="Field"
                          onChange={(e) => updateFilter(filter.id, { field: e.target.value })}
                        >
                          {fields.map((field) => (
                            <MenuItem key={field.id} value={field.id}>
                              {field.name} ({field.dataType})
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={2}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Operator</InputLabel>
                        <Select
                          value={filter.operator}
                          label="Operator"
                          onChange={(e) => updateFilter(filter.id, { operator: e.target.value as FilterRule['operator'] })}
                        >
                          {getValidOperators(fields.find(f => f.id === filter.field)?.dataType || 'categorical').map((op) => (
                            <MenuItem key={op.value} value={op.value}>
                              {op.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={4}>
                      {renderFilterValueInput(filter)}
                    </Grid>

                    <Grid item xs={12} sm={2}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={filter.enabled}
                            onChange={(e) => updateFilter(filter.id, { enabled: e.target.checked })}
                          />
                        }
                        label="Active"
                      />
                    </Grid>

                    <Grid item xs={12} sm={1}>
                      <Tooltip title="Remove filter">
                        <IconButton
                          size="small"
                          onClick={() => removeFilter(filter.id)}
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </Grid>
                  </Grid>
                </ListItem>
              ))}
            </List>
          )}

          {filters.length > 0 && (
            <Box display="flex" gap={1} mt={2}>
              <Button
                variant="contained"
                startIcon={<FilterList />}
                onClick={applyFilters}
                disabled={isProcessing}
              >
                {isProcessing ? 'Applying...' : 'Apply Filters'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<Clear />}
                onClick={() => {
                  setFilters([]);
                  setFilteredData(data);
                  onFiltersApplied(data);
                }}
              >
                Clear All
              </Button>
            </Box>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Data Transformations */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <Functions fontSize="small" />
            <Typography variant="subtitle1" fontWeight="medium">
              Data Transformations
            </Typography>
            {transformations.length > 0 && (
              <Chip
                label={`${transformations.filter(t => t.enabled).length} active`}
                size="small"
                color="secondary"
                variant="outlined"
              />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box mb={2}>
            <Button
              variant="outlined"
              startIcon={<Add />}
              onClick={addTransformation}
              size="small"
            >
              Add Transformation
            </Button>
          </Box>

          {transformations.length === 0 ? (
            <Typography variant="body2" color="text.secondary" textAlign="center" py={2}>
              No transformations configured. Add a transformation to start manipulating your data.
            </Typography>
          ) : (
            <List>
              {transformations.map((transformation) => (
                <ListItem
                  key={transformation.id}
                  sx={{
                    border: 1,
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    backgroundColor: alpha(theme.palette.background.paper, 0.5),
                  }}
                >
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={3}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Source Field</InputLabel>
                        <Select
                          value={transformation.field}
                          label="Source Field"
                          onChange={(e) => updateTransformation(transformation.id, { field: e.target.value })}
                        >
                          {fields.filter(f => f.dataType === 'numerical').map((field) => (
                            <MenuItem key={field.id} value={field.id}>
                              {field.name} ({field.dataType})
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={2}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Operation</InputLabel>
                        <Select
                          value={transformation.operation}
                          label="Operation"
                          onChange={(e) => updateTransformation(transformation.id, { operation: e.target.value as TransformationRule['operation'] })}
                        >
                          {getValidOperations(fields.find(f => f.id === transformation.field)?.dataType || 'categorical').map((op) => (
                            <MenuItem key={op.value} value={op.value}>
                              {op.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>

                    <Grid item xs={12} sm={3}>
                      <TextField
                        size="small"
                        label="New Field Name (optional)"
                        placeholder="Leave empty to overwrite"
                        value={transformation.newField || ''}
                        onChange={(e) => updateTransformation(transformation.id, { newField: e.target.value })}
                        fullWidth
                      />
                    </Grid>

                    <Grid item xs={12} sm={2}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={transformation.enabled}
                            onChange={(e) => updateTransformation(transformation.id, { enabled: e.target.checked })}
                          />
                        }
                        label="Active"
                      />
                    </Grid>

                    <Grid item xs={12} sm={2}>
                      <Box display="flex" gap={1}>
                        <Tooltip title="Remove transformation">
                          <IconButton
                            size="small"
                            onClick={() => removeTransformation(transformation.id)}
                            color="error"
                          >
                            <Delete />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Grid>
                  </Grid>
                </ListItem>
              ))}
            </List>
          )}

          {transformations.length > 0 && (
            <Box display="flex" gap={1} mt={2}>
              <Button
                variant="contained"
                startIcon={<Functions />}
                onClick={applyTransformations}
                disabled={isProcessing}
                color="secondary"
              >
                {isProcessing ? 'Applying...' : 'Apply Transformations'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<Clear />}
                onClick={() => {
                  setTransformations([]);
                  setTransformedData(filteredData);
                  onDataTransformed(filteredData);
                }}
              >
                Clear All
              </Button>
            </Box>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Data Summary */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box display="flex" alignItems="center" gap={1}>
            <DataObject fontSize="small" />
            <Typography variant="subtitle1" fontWeight="medium">
              Data Summary
            </Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Original Data
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {data.length.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    records
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    After Filtering
                  </Typography>
                  <Typography variant="h6" color="info">
                    {filteredData.length.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    records ({((filteredData.length / data.length) * 100).toFixed(1)}%)
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={4}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    After Transformation
                  </Typography>
                  <Typography variant="h6" color="secondary">
                    {transformedData.length.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    records
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Box display="flex" gap={1} mt={2}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => {
                setFilteredData(data);
                setTransformedData(data);
                onFiltersApplied(data);
                onDataTransformed(data);
              }}
            >
              Reset to Original
            </Button>
            <Button
              variant="outlined"
              startIcon={<Clear />}
              onClick={clearAll}
            >
              Clear All Operations
            </Button>
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default DataTransformationPanel;
