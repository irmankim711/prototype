import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Grid,
  Alert,
  Chip,
  Divider,
} from '@mui/material';
import { Save as SaveIcon, Refresh as RefreshIcon } from '@mui/icons-material';

interface FieldMappingProps {
  excelHeaders: string[];
  templatePlaceholders: string[];
  currentMapping: Record<string, string>;
  onMappingChange: (mapping: Record<string, string>) => void;
}

export default function FieldMapping({
  excelHeaders,
  templatePlaceholders,
  currentMapping,
  onMappingChange,
}: FieldMappingProps) {
  const [mapping, setMapping] = useState<Record<string, string>>(currentMapping);
  const [unmappedPlaceholders, setUnmappedPlaceholders] = useState<string[]>([]);

  useEffect(() => {
    // Find placeholders that aren't mapped yet
    const mappedPlaceholders = Object.values(mapping);
    const unmapped = templatePlaceholders.filter(
      placeholder => !mappedPlaceholders.includes(placeholder)
    );
    setUnmappedPlaceholders(unmapped);
  }, [mapping, templatePlaceholders]);

  const handleMappingChange = (excelHeader: string, placeholder: string) => {
    const newMapping = { ...mapping, [excelHeader]: placeholder };
    setMapping(newMapping);
    onMappingChange(newMapping);
  };

  const handleAutoMap = () => {
    const autoMapping: Record<string, string> = {};
    
    excelHeaders.forEach(header => {
      const normalizedHeader = header.toLowerCase();
      
      // Try to find a matching placeholder
      for (const placeholder of templatePlaceholders) {
        const normalizedPlaceholder = placeholder.toLowerCase();
        
        // Check for exact matches or partial matches
        if (normalizedHeader.includes(normalizedPlaceholder) || 
            normalizedPlaceholder.includes(normalizedHeader) ||
            normalizedHeader.replace(/[^a-z0-9]/g, '') === normalizedPlaceholder.replace(/[^a-z0-9]/g, '')) {
          autoMapping[header] = placeholder;
          break;
        }
      }
    });
    
    setMapping(autoMapping);
    onMappingChange(autoMapping);
  };

  const handleClearMapping = () => {
    setMapping({});
    onMappingChange({});
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Field Mapping</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleAutoMap}
            sx={{ mr: 1 }}
          >
            Auto Map
          </Button>
          <Button
            variant="outlined"
            onClick={handleClearMapping}
            color="error"
          >
            Clear All
          </Button>
        </Box>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        Map your Excel columns to template placeholders. Unmapped placeholders will need to be filled manually.
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Excel Columns
            </Typography>
            <Box sx={{ mb: 2 }}>
              {excelHeaders.map((header, index) => (
                <Chip
                  key={index}
                  label={header}
                  variant="outlined"
                  sx={{ m: 0.5 }}
                  color={mapping[header] ? 'primary' : 'default'}
                />
              ))}
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Template Placeholders
            </Typography>
            <Box sx={{ mb: 2 }}>
              {templatePlaceholders.map((placeholder, index) => (
                <Chip
                  key={index}
                  label={placeholder}
                  variant="outlined"
                  sx={{ m: 0.5 }}
                  color={Object.values(mapping).includes(placeholder) ? 'success' : 'default'}
                />
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Divider sx={{ my: 3 }} />

      <Typography variant="h6" gutterBottom>
        Manual Mapping
      </Typography>

      <Grid container spacing={2}>
        {excelHeaders.map((header) => (
          <Grid item xs={12} sm={6} key={header}>
            <FormControl fullWidth size="small">
              <InputLabel>{header}</InputLabel>
              <Select
                value={mapping[header] || ''}
                label={header}
                onChange={(e) => handleMappingChange(header, e.target.value)}
              >
                <MenuItem value="">
                  <em>Select placeholder...</em>
                </MenuItem>
                {templatePlaceholders.map((placeholder) => (
                  <MenuItem key={placeholder} value={placeholder}>
                    {placeholder}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        ))}
      </Grid>

      {unmappedPlaceholders.length > 0 && (
        <Alert severity="warning" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Unmapped placeholders that need manual input:
          </Typography>
          <Box sx={{ mt: 1 }}>
            {unmappedPlaceholders.map((placeholder) => (
              <Chip
                key={placeholder}
                label={placeholder}
                variant="outlined"
                color="warning"
                sx={{ m: 0.5 }}
              />
            ))}
          </Box>
        </Alert>
      )}

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="body2" color="text.secondary">
          {Object.keys(mapping).length} of {excelHeaders.length} columns mapped
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {unmappedPlaceholders.length} placeholders need manual input
        </Typography>
      </Box>
    </Box>
  );
} 