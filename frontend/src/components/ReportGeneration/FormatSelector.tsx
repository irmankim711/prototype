/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Format Selector Component
 * Choose output formats for report generation
 */

import React from 'react';
  
import { Box, Paper, Typography, FormGroup, FormControlLabel, Checkbox, Card, CardContent, Grid, Chip, Alert } from "@mui/material";
  
import { PictureAsPdf, Description, Language } from "@mui/icons-material";

interface FormatSelectorProps {
  selectedFormats: string[];
  
onFormatsChange: (formats: string[]) => void;
  
template?: any;
  
maxFormats?: number;
}

const FormatSelector: React.FC<FormatSelectorProps> = ({
  selectedFormats,
  onFormatsChange,
  template,
  maxFormats = 3,
}) => {
  const formats = [
    {
      id: 'pdf',
      name: 'PDF',
      description: 'Portable Document Format - Best for sharing and printing',
      icon: <PictureAsPdf />,
      features: ['Print-ready', 'Consistent layout', 'Widely supported'],
      recommended: true,
    },
    {
      id: 'docx',
      name: 'Word Document',
      description: 'Microsoft Word format - Best for editing and collaboration',
      icon: <Description />,
      features: ['Editable', 'Track changes', 'Comments'],
      recommended: false,
    },
    {
      id: 'html',
      name: 'HTML',
      description: 'Web format - Best for online viewing and embedding',
      icon: <Language />,
      features: ['Interactive', 'Responsive', 'Web-friendly'],
      recommended: false,
    },
  ];

const handleFormatChange = (formatId: string, checked: boolean) => {
    if (checked) {
      if (selectedFormats.length < maxFormats) {
        onFormatsChange([...selectedFormats, formatId]);
      }
    } else {
      onFormatsChange(selectedFormats.filter(f => f !== formatId));
    }
  };

const isFormatDisabled = (formatId: string) => {
    return !selectedFormats.includes(formatId) && selectedFormats.length >= maxFormats;
  };

return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Select Output Formats
      </Typography>
      
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Choose up to {maxFormats} formats for your report. You can always generate additional formats later.
      </Typography>

      {selectedFormats.length === 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Please select at least one output format.
        </Alert>
      )}

      <Grid container spacing={3}>
        {formats.map((format: any) => {
          const isSelected = selectedFormats.includes(format.id);
          
const isDisabled = isFormatDisabled(format.id);

return (
            <Grid item xs={12} md={4} key={format.id}>
              <Card
                sx={{
                  height: '100%',
                  border: isSelected ? 2 : 1,
                  borderColor: isSelected ? 'primary.main' : 'grey.300',
                  cursor: isDisabled ? 'not-allowed' : 'pointer',
                  opacity: isDisabled ? 0.6 : 1,
                  transition: 'all 0.2s',
                  '&:hover': {
                    borderColor: isDisabled ? 'grey.300' : 'primary.main',
                    elevation: isDisabled ? 1 : 4,
                  },
                }}
                onClick={() => {
                  if (!isDisabled) {
                    handleFormatChange(format.id, !isSelected);
                  }
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ color: 'primary.main', mr: 2 }}>
                      {format.icon}
                    </Box>
                    
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" component="h3">
                        {format.name}
                      </Typography>
                      
                      {format.recommended && (
                        <Chip
                          label="Recommended"
                          size="small"
                          color="primary"
                          sx={{ mt: 0.5 }}
                        />
                      )}
                    </Box>
                    
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={isSelected}
                          onChange={(e: any) => handleFormatChange(format.id, e.target.checked)}
                          disabled={isDisabled}
                        />
                      }
                      label=""
                      sx={{ m: 0 }}
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {format.description}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {format.features.map((feature, index) => (
                      <Chip
                        key={index}
                        label={feature}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Selection Summary */}
      {selectedFormats.length > 0 && (
        <Paper sx={{ p: 2, mt: 3, bgcolor: 'grey.50' }}>
          <Typography variant="subtitle2" gutterBottom>
            Selected Formats ({selectedFormats.length}/{maxFormats})
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {selectedFormats.map((formatId: any) => {
              const format = formats.find(f => f.id === formatId);
              
return (
                <Chip
                  key={formatId}
                  label={format?.name}
                  color="primary"
                  onDelete={() => handleFormatChange(formatId, false)}
                />
              );
            })}
          </Box>
        </Paper>
      )}

      {/* Template Compatibility */}
      {template && (
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Template Compatibility
          </Typography>
          <Typography variant="body2">
            The selected template "{template.name}" supports all output formats. 
            {template.supports_excel && ' Excel data integration is enabled for this template.'}
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default FormatSelector;
