import React from 'react';
import { Box, Typography, FormControl, InputLabel, Select, MenuItem, Paper } from '@mui/material';

interface FieldMappingProps {
  placeholders?: string[];
  dataHeaders?: string[];
  onMappingChange: (mapping: Record<string, string>) => void;
}

export default function FieldMapping(props: FieldMappingProps) {
  const placeholders = Array.isArray(props.placeholders) ? props.placeholders : [];
  const dataHeaders = Array.isArray(props.dataHeaders) ? props.dataHeaders : [];
  const [mapping, setMapping] = React.useState<Record<string, string>>({});

  React.useEffect(() => {
    props.onMappingChange(mapping);
  }, [mapping, props.onMappingChange]);

  if (!placeholders.length || !dataHeaders.length) {
    return <Typography color="error">No placeholders or data columns available for mapping.</Typography>;
  }

  return (
    <Paper sx={{ p: 3, borderRadius: 3, border: '1.5px solid #0e1c40', mt: 2 }}>
      <Typography variant="subtitle1" sx={{ color: '#0e1c40', fontWeight: 600, mb: 2 }}>
        Map Template Placeholders to Your Data
      </Typography>
      {placeholders.map(ph => (
        <Box key={ph} display="flex" alignItems="center" mb={2}>
          <Typography sx={{ minWidth: 180, fontWeight: 500, color: '#0e1c40' }}>{ph}</Typography>
          <FormControl fullWidth>
            <InputLabel>Select Data Column</InputLabel>
            <Select
              value={mapping[ph] || ''}
              onChange={e => handleChange(ph, e.target.value)}
              label="Select Data Column"
            >
              {dataHeaders.map(header => (
                <MenuItem key={header} value={header}>{header}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      ))}
    </Paper>
  );

  function handleChange(placeholder: string, value: string) {
    setMapping(prev => ({ ...prev, [placeholder]: value }));
  }
} 