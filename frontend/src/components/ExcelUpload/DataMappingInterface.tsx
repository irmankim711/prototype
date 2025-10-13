import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Data Mapping Interface Component
 * Visual interface for mapping Excel columns to template variables
 */

import { useState, useEffect } from "react";
  
import { Box, Paper, Typography, Grid, Card, CardContent, Button, Alert, Chip, IconButton, Tooltip, FormControl, InputLabel, Select, MenuItem, Switch, FormControlLabel, Divider } from "@mui/material";
  
import { DragIndicator, Link, LinkOff, Visibility, Settings, CheckCircle, Warning, Error } from "@mui/icons-material";

import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

interface ExcelColumn {
  name: string;
  
type: string;
  
sample_values: any[];
  
null_count: number;
  
unique_count: number;
}

interface TemplateVariable {
  name: string;
  
type: string;
  
required: boolean;
  
description?: string;
}

interface DataMapping {
  template_variable: string;
  
excel_column: string;
  
transformation?: string;
  
validation_rules?: any[];
}

interface DataMappingInterfaceProps {
  excelColumns: ExcelColumn[];
  
templateVariables: TemplateVariable[];
  
onMappingChange: (mappings: DataMapping[]) => void;
  
initialMappings?: DataMapping[];
  
showPreview?: boolean;
}

const DataMappingInterface: React.FC<DataMappingInterfaceProps> = ({
  excelColumns,
  templateVariables,
  onMappingChange,
  initialMappings = [],
  showPreview = true,
}) => {
  const [mappings, setMappings] = useState<DataMapping[]>(initialMappings);
  
const [selectedSheet, setSelectedSheet] = useState<string>('Sheet1');
  
const [autoMapping, setAutoMapping] = useState(true);
  
const [validationResults, setValidationResults] = useState<any[]>([]);
  
const [showAdvanced, setShowAdvanced] = useState(false);

useEffect(() => {
    if (autoMapping && excelColumns.length > 0 && templateVariables.length > 0) {
      performAutoMapping();
    }
  }, [excelColumns, templateVariables, autoMapping]);

useEffect(() => {
    onMappingChange(mappings);
    
validateMappings();
  }, [mappings]);

const performAutoMapping = () => {
    const autoMappings: DataMapping[] = [];

templateVariables.forEach(variable => {
      // Try to find exact match first
      let matchedColumn = excelColumns.find(col => 
        col.name.toLowerCase() === variable.name.toLowerCase()
      );
      
      // Try partial match if no exact match
      if (!matchedColumn) {
        matchedColumn = excelColumns.find(col =>
          col.name.toLowerCase().includes(variable.name.toLowerCase()) ||
          variable.name.toLowerCase().includes(col.name.toLowerCase())
        );
      }
      
      // Try type-based matching for common patterns
      if (!matchedColumn && variable.type === 'date') {
        matchedColumn = excelColumns.find(col =>
          col.name.toLowerCase().includes('date') ||
          col.name.toLowerCase().includes('time') ||
          col.type === 'date'
        );
      }
      
      if (!matchedColumn && variable.type === 'number') {
        matchedColumn = excelColumns.find(col =>
          col.type === 'number' && !autoMappings.some(m => m.excel_column === col.name)
        );
      }
      
      if (matchedColumn) {
        autoMappings.push({
          template_variable: variable.name,
          excel_column: matchedColumn.name,
          transformation: getDefaultTransformation(variable.type, matchedColumn.type),
        });
      }
    });

setMappings(autoMappings);
  };

const getDefaultTransformation = (templateType: string, excelType: string): string | undefined => {
    if (templateType === 'number' && excelType === 'string') {
      return 'parse_number';
    }
    if (templateType === 'date' && excelType === 'string') {
      return 'parse_date';
    }
    if (templateType === 'string' && excelType === 'number') {
      return 'to_string';
    }
    return undefined;
  };

const validateMappings = () => {
    const results: any[] = [];
    
    // Check required variables
    templateVariables.forEach(variable => {
      if (variable.required) {
        const mapping = mappings.find(m => m.template_variable === variable.name);
        
if (!mapping) {
          results.push({
            type: 'error',
            variable: variable.name,
            message: `Required variable "${variable.name}" is not mapped`,
          });
        }
      }
    });
    
    // Check type compatibility
    mappings.forEach(mapping => {
      const variable = templateVariables.find(v => v.name === mapping.template_variable);
      
const column = excelColumns.find(c => c.name === mapping.excel_column);

if (variable && column) {
        if (variable.type !== column.type && !mapping.transformation) {
          results.push({
            type: 'warning',
            variable: mapping.template_variable,
            message: `Type mismatch: ${variable.type} expected, ${column.type} provided`,
          });
        }
      }
    });

setValidationResults(results);
  };

const handleDragEnd = (result: React.ChangeEvent<HTMLInputElement>) => {
    if (!result.destination) return;

const { source, destination } = result;

if (source.droppableId === 'excel-columns' && destination.droppableId.startsWith('variable-')) {
      const variableName = destination.droppableId.replace('variable-', '');
      
const columnName = excelColumns[source.index].name;

addMapping(variableName, columnName);
    }
  };

const addMapping = (variableName: string, columnName: string) => {
    const variable = templateVariables.find(v => v.name === variableName);
    
const column = excelColumns.find(c => c.name === columnName);

if (!variable || !column) return;

const newMapping: DataMapping = {
      template_variable: variableName,
      excel_column: columnName,
      transformation: getDefaultTransformation(variable.type, column.type),
    };

setMappings(prev => {
      const filtered = prev.filter(m => m.template_variable !== variableName);
      
return [...filtered, newMapping];
    });
  };

const removeMapping = (variableName: string) => {
    setMappings(prev => prev.filter(m => m.template_variable !== variableName));
  };

const updateMapping = (variableName: string, updates: Partial<DataMapping>) => {
    setMappings(prev => prev.map(m => 
      m.template_variable === variableName ? { ...m, ...updates } : m
    ));
  };

const getMappingForVariable = (variableName: string) => {
    return mappings.find(m => m.template_variable === variableName);
  };

const getValidationForVariable = (variableName: string) => {
    return validationResults.filter(r => r.variable === variableName);
  };

const getTypeColor = (type: string) => {
    switch (type) {
      case 'string': return 'primary';
      
case 'number': return 'success';
      
case 'date': return 'warning';
      
case 'boolean': return 'info';
      
default: return 'default';
    }
  };

const getValidationIcon = (validations: any[]) => {
    if (validations.some(v => v.type === 'error')) return <Error color="error" />;
    
if (validations.some(v => v.type === 'warning')) return <Warning color="warning" />;
    
return <CheckCircle color="success" />;
  };

return (
    <Box>
      {/* Header Controls */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">
          Data Mapping
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControlLabel
            control={
              <Switch
                checked={autoMapping}
                onChange={(e: any) => setAutoMapping(e.target.checked)}
              />
            }
            label="Auto-mapping"
          />
          
          <Button
            variant="outlined"
            startIcon={<Settings />}
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            Advanced
          </Button>
          
          <Button
            variant="contained"
            onClick={performAutoMapping}
            disabled={!autoMapping}
          >
            Re-map
          </Button>
        </Box>
      </Box>

      {/* Validation Summary */}
      {validationResults.length > 0 && (
        <Alert 
          severity={validationResults.some(r => r.type === 'error') ? 'error' : 'warning'}
          sx={{ mb: 3 }}
        >
          <Typography variant="subtitle2" gutterBottom>
            Mapping Issues ({validationResults.length})
          </Typography>
          {validationResults.slice(0, 3).map((result, index) => (
            <Typography key={index} variant="body2">
              • {result.message}
            </Typography>
          ))}
          {validationResults.length > 3 && (
            <Typography variant="body2">
              ... and {validationResults.length - 3} more
            </Typography>
          )}
        </Alert>
      )}

      <DragDropContext onDragEnd={handleDragEnd}>
        <Grid container spacing={3}>
          {/* Excel Columns */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, height: '600px', overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Excel Columns ({excelColumns.length})
              </Typography>
              
              <Droppable droppableId="excel-columns">
                {(provided: any) => (
                  <Box
                    {...provided.droppableProps}
                    ref={provided.innerRef}
                  >
                    {excelColumns.map((column, index) => (
                      <Draggable
                        key={column.name}
                        draggableId={`column-${column.name}`}
                        index={index}
                      >
                        {(provided, snapshot) => (
                          <Card
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            sx={{
                              mb: 1,
                              cursor: 'grab',
                              opacity: snapshot.isDragging ? 0.8 : 1,
                              transform: snapshot.isDragging ? 'rotate(5deg)' : 'none',
                            }}
                          >
                            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <DragIndicator color="action" />
                                <Box sx={{ flex: 1 }}>
                                  <Typography variant="subtitle2" noWrap>
                                    {column.name}
                                  </Typography>
                                  <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                                    <Chip
                                      label={column.type}
                                      size="small"
                                      color={getTypeColor(column.type) as any}
                                    />
                                    <Chip
                                      label={`${column.unique_count} unique`}
                                      size="small"
                                      variant="outlined"
                                    />
                                  </Box>
                                </Box>
                              </Box>
                              
                              {column.sample_values.length > 0 && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                  Sample: {column.sample_values.slice(0, 2).join(', ')}
                                  {column.sample_values.length > 2 && '...'}
                                </Typography>
                              )}
                            </CardContent>
                          </Card>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </Box>
                )}
              </Droppable>
            </Paper>
          </Grid>

          {/* Mapping Area */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2, height: '600px', overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom>
                Template Variables ({templateVariables.length})
              </Typography>
              
              {templateVariables.map((variable: any) => {
                const mapping = getMappingForVariable(variable.name);
                
const validations = getValidationForVariable(variable.name);

return (
                  <Droppable key={variable.name} droppableId={`variable-${variable.name}`}>
                    {(provided, snapshot) => (
                      <Card
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                        sx={{
                          mb: 2,
                          border: snapshot.isDraggingOver ? 2 : 1,
                          borderColor: snapshot.isDraggingOver ? 'primary.main' : 'grey.300',
                          bgcolor: snapshot.isDraggingOver ? 'action.hover' : 'background.paper',
                        }}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                            <Box sx={{ flex: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Typography variant="subtitle1">
                                  {variable.name}
                                </Typography>
                                
                                {variable.required && (
                                  <Chip label="Required" size="small" color="error" />
                                )}
                                
                                <Chip
                                  label={variable.type}
                                  size="small"
                                  color={getTypeColor(variable.type) as any}
                                />
                                
                                {validations.length > 0 && getValidationIcon(validations)}
                              </Box>
                              
                              {variable.description && (
                                <Typography variant="body2" color="text.secondary">
                                  {variable.description}
                                </Typography>
                              )}
                            </Box>
                            
                            {mapping && (
                              <IconButton
                                size="small"
                                onClick={() => removeMapping(variable.name)}
                                color="error"
                              >
                                <LinkOff />
                              </IconButton>
                            )}
                          </Box>
                          
                          {mapping ? (
                            <Box>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                <Link color="success" />
                                <Typography variant="body2">
                                  Mapped to: <strong>{mapping.excel_column}</strong>
                                </Typography>
                              </Box>
                              
                              {mapping.transformation && (
                                <Chip
                                  label={`Transform: ${mapping.transformation}`}
                                  size="small"
                                  variant="outlined"
                                  color="info"
                                />
                              )}
                              
                              {showAdvanced && (
                                <Box sx={{ mt: 2 }}>
                                  <FormControl size="small" sx={{ minWidth: 150 }}>
                                    <InputLabel>Transformation</InputLabel>
                                    <Select
                                      value={mapping.transformation || ''}
                                      onChange={(e: any) => updateMapping(variable.name, {
                                        transformation: e.target.value || undefined
                                      })}
                                      label="Transformation"
                                    >
                                      <MenuItem value="">None</MenuItem>
                                      <MenuItem value="parse_number">Parse Number</MenuItem>
                                      <MenuItem value="parse_date">Parse Date</MenuItem>
                                      <MenuItem value="to_string">To String</MenuItem>
                                      <MenuItem value="to_uppercase">To Uppercase</MenuItem>
                                      <MenuItem value="to_lowercase">To Lowercase</MenuItem>
                                      <MenuItem value="trim">Trim Whitespace</MenuItem>
                                    </Select>
                                  </FormControl>
                                </Box>
                              )}
                            </Box>
                          ) : (
                            <Box
                              sx={{
                                p: 2,
                                border: '2px dashed',
                                borderColor: 'grey.300',
                                borderRadius: 1,
                                textAlign: 'center',
                                bgcolor: 'grey.50',
                              }}
                            >
                              <Typography variant="body2" color="text.secondary">
                                Drag an Excel column here to map
                              </Typography>
                            </Box>
                          )}
                          
                          {validations.length > 0 && (
                            <Box sx={{ mt: 2 }}>
                              {validations.map((validation, index) => (
                                <Alert
                                  key={index}
                                  severity={validation.type}
                                  sx={{ mt: 1 }}
                                >
                                  {validation.message}
                                </Alert>
                              ))}
                            </Box>
                          )}
                          
                          {provided.placeholder}
                        </CardContent>
                      </Card>
                    )}
                  </Droppable>
                );
              })}
            </Paper>
          </Grid>
        </Grid>
      </DragDropContext>

      {/* Mapping Summary */}
      <Box sx={{ mt: 3 }}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Mapping Summary
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {mappings.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Variables Mapped
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {templateVariables.filter(v => v.required && !getMappingForVariable(v.name)).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Required Missing
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} sm={4}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">
                  {validationResults.filter(r => r.type === 'error').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Errors
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Box>
    </Box>
  );
};

export default DataMappingInterface;
