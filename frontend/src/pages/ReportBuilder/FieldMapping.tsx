import React, { useEffect, useState } from 'react';
import { Box, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Select, MenuItem, Typography } from '@mui/material';

interface FieldMappingProps {
  templateFields: { name: string; label: string }[];
  dataHeaders: string[];
  onMappingChange: (mapping: Record<string, string>) => void;
}

export default function FieldMapping({ templateFields, dataHeaders, onMappingChange }: FieldMappingProps) {
  const [mapping, setMapping] = useState<Record<string, string>>({});

  // Auto-map on mount or when fields/headers change
  useEffect(() => {
    const autoMap: Record<string, string> = {};
    templateFields.forEach(field => {
      const match = dataHeaders.find(h => h.toLowerCase() === field.name.toLowerCase() || h.toLowerCase() === field.label.toLowerCase());
      if (match) autoMap[field.name] = match;
    });
    setMapping(autoMap);
    onMappingChange(autoMap);
    // eslint-disable-next-line
  }, [JSON.stringify(templateFields), JSON.stringify(dataHeaders)]);

  const handleChange = (fieldName: string, header: string) => {
    const newMapping = { ...mapping, [fieldName]: header };
    setMapping(newMapping);
    onMappingChange(newMapping);
  };

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom>Field Mapping</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Template Field</TableCell>
              <TableCell>Mapped Column</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {templateFields.map(field => (
              <TableRow key={field.name}>
                <TableCell>{field.label}</TableCell>
                <TableCell>
                  <Select
                    value={mapping[field.name] || ''}
                    onChange={e => handleChange(field.name, e.target.value)}
                    displayEmpty
                    fullWidth
                  >
                    <MenuItem value=""><em>None</em></MenuItem>
                    {dataHeaders.map(header => (
                      <MenuItem key={header} value={header}>{header}</MenuItem>
                    ))}
                  </Select>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
} 