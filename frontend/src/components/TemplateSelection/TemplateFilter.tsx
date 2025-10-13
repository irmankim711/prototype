import React from 'react';
/**
 * Template Filter Component
 * Advanced filtering options for template selection
 */

import { useState } from "react";
  
import { Box, Paper, Typography, FormControl, InputLabel, Select, MenuItem, Checkbox, FormControlLabel, FormGroup, Slider, Chip, Button, Divider, Accordion, AccordionSummary, AccordionDetails, Rating, Switch } from "@mui/material";
  
import { ExpandMore, FilterList, Clear } from "@mui/icons-material";

interface FilterOptions {
  categories: string[];
  
types: string[];
  
complexity: string[];
  
features: string[];
  
usageRange: [number, number];
  
rating: number;
  
recentlyUsed: boolean;
  
supportsExcel: boolean;
  
isPopular: boolean;
}

interface TemplateFilterProps {
  filters: FilterOptions;
  
onFiltersChange: (filters: FilterOptions) => void;
  
onReset: () => void;
  
availableCategories?: string[];
  
availableTypes?: string[];
}

const TemplateFilter: React.FC<TemplateFilterProps> = ({
  filters,
  onFiltersChange,
  onReset,
  availableCategories = [],
  availableTypes = [],
}) => {
  const [expanded, setExpanded] = useState<string[]>(['categories', 'features']);

const handleAccordionChange = (panel: string) => (
    event: React.SyntheticEvent,
    isExpanded: boolean
  ) => {
    setExpanded(
      isExpanded
        ? [...expanded, panel]
        : expanded.filter(p => p !== panel)
    );
  };

const handleCategoryChange = (category: string) => {
    const newCategories = filters.categories.includes(category)
      ? filters.categories.filter(c => c !== category)
      : [...filters.categories, category];

onFiltersChange({
      ...filters,
      categories: newCategories,
    });
  };

const handleTypeChange = (type: string) => {
    const newTypes = filters.types.includes(type)
      ? filters.types.filter(t => t !== type)
      : [...filters.types, type];

onFiltersChange({
      ...filters,
      types: newTypes,
    });
  };

const handleComplexityChange = (complexity: string) => {
    const newComplexity = filters.complexity.includes(complexity)
      ? filters.complexity.filter(c => c !== complexity)
      : [...filters.complexity, complexity];

onFiltersChange({
      ...filters,
      complexity: newComplexity,
    });
  };

const handleFeatureChange = (feature: string) => {
    const newFeatures = filters.features.includes(feature)
      ? filters.features.filter(f => f !== feature)
      : [...filters.features, feature];

onFiltersChange({
      ...filters,
      features: newFeatures,
    });
  };

const handleUsageRangeChange = (event: Event, newValue: number | number[]) => {
    onFiltersChange({
      ...filters,
      usageRange: newValue as [number, number],
    });
  };

const handleRatingChange = (event: React.SyntheticEvent, newValue: number | null) => {
    onFiltersChange({
      ...filters,
      rating: newValue || 0,
    });
  };

const categories = availableCategories.length > 0 ? availableCategories : [
    'Business',
    'Financial',
    'Marketing',
    'Technical',
    'Academic',
    'General',
  ];

const types = availableTypes.length > 0 ? availableTypes : [
    'Report',
    'Dashboard',
    'Presentation',
    'Document',
    'Invoice',
    'Proposal',
  ];

const complexityLevels = [
    'Simple',
    'Moderate',
    'Complex',
  ];

const features = [
    'Charts & Graphs',
    'Tables',
    'Images',
    'Headers & Footers',
    'Page Numbers',
    'Table of Contents',
    'Formulas',
    'Conditional Formatting',
  ];

const getActiveFiltersCount = () => {
    let count = 0;
    
count += filters.categories.length;
    
count += filters.types.length;
    
count += filters.complexity.length;
    
count += filters.features.length;
    
if (filters.rating > 0) count++;
    
if (filters.recentlyUsed) count++;
    
if (filters.supportsExcel) count++;
    
if (filters.isPopular) count++;
    
if (filters.usageRange[0] > 0 || filters.usageRange[1] < 100) count++;
    
return count;
  };

return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FilterList />
          <Typography variant="h6">
            Filters
          </Typography>
          {getActiveFiltersCount() > 0 && (
            <Chip
              label={getActiveFiltersCount()}
              size="small"
              color="primary"
            />
          )}
        </Box>
        
        <Button
          size="small"
          startIcon={<Clear />}
          onClick={onReset}
          disabled={getActiveFiltersCount() === 0}
        >
          Clear All
        </Button>
      </Box>

      {/* Categories */}
      <Accordion
        expanded={expanded.includes('categories')}
        onChange={handleAccordionChange('categories')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography>Categories</Typography>
          {filters.categories.length > 0 && (
            <Chip
              label={filters.categories.length}
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <FormGroup>
            {categories.map((category: any) => (
              <FormControlLabel
                key={category}
                control={
                  <Checkbox
                    checked={filters.categories.includes(category)}
                    onChange={() => handleCategoryChange(category)}
                  />
                }
                label={category}
              />
            ))}
          </FormGroup>
        </AccordionDetails>
      </Accordion>

      {/* Template Types */}
      <Accordion
        expanded={expanded.includes('types')}
        onChange={handleAccordionChange('types')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography>Template Types</Typography>
          {filters.types.length > 0 && (
            <Chip
              label={filters.types.length}
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <FormGroup>
            {types.map((type: any) => (
              <FormControlLabel
                key={type}
                control={
                  <Checkbox
                    checked={filters.types.includes(type)}
                    onChange={() => handleTypeChange(type)}
                  />
                }
                label={type}
              />
            ))}
          </FormGroup>
        </AccordionDetails>
      </Accordion>

      {/* Complexity */}
      <Accordion
        expanded={expanded.includes('complexity')}
        onChange={handleAccordionChange('complexity')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography>Complexity</Typography>
          {filters.complexity.length > 0 && (
            <Chip
              label={filters.complexity.length}
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <FormGroup>
            {complexityLevels.map((level: any) => (
              <FormControlLabel
                key={level}
                control={
                  <Checkbox
                    checked={filters.complexity.includes(level)}
                    onChange={() => handleComplexityChange(level)}
                  />
                }
                label={level}
              />
            ))}
          </FormGroup>
        </AccordionDetails>
      </Accordion>

      {/* Features */}
      <Accordion
        expanded={expanded.includes('features')}
        onChange={handleAccordionChange('features')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography>Features</Typography>
          {filters.features.length > 0 && (
            <Chip
              label={filters.features.length}
              size="small"
              sx={{ ml: 1 }}
            />
          )}
        </AccordionSummary>
        <AccordionDetails>
          <FormGroup>
            {features.map((feature: any) => (
              <FormControlLabel
                key={feature}
                control={
                  <Checkbox
                    checked={filters.features.includes(feature)}
                    onChange={() => handleFeatureChange(feature)}
                  />
                }
                label={feature}
              />
            ))}
          </FormGroup>
        </AccordionDetails>
      </Accordion>

      {/* Usage Statistics */}
      <Accordion
        expanded={expanded.includes('usage')}
        onChange={handleAccordionChange('usage')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography>Usage Range</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ px: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Number of times used: {filters.usageRange[0]} - {filters.usageRange[1]}
            </Typography>
            <Slider
              value={filters.usageRange}
              onChange={handleUsageRangeChange}
              valueLabelDisplay="auto"
              min={0}
              max={100}
              marks={[
                { value: 0, label: '0' },
                { value: 25, label: '25' },
                { value: 50, label: '50' },
                { value: 75, label: '75' },
                { value: 100, label: '100+' },
              ]}
            />
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Rating */}
      <Accordion
        expanded={expanded.includes('rating')}
        onChange={handleAccordionChange('rating')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography>Minimum Rating</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Rating
              value={filters.rating}
              onChange={handleRatingChange}
              precision={0.5}
            />
            <Typography variant="body2" color="text.secondary">
              {filters.rating > 0 ? `${filters.rating} stars & up` : 'Any rating'}
            </Typography>
          </Box>
        </AccordionDetails>
      </Accordion>

      <Divider sx={{ my: 2 }} />

      {/* Quick Filters */}
      <Typography variant="subtitle2" gutterBottom>
        Quick Filters
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <FormControlLabel
          control={
            <Switch
              checked={filters.supportsExcel}
              onChange={(e: any) =>
                onFiltersChange({
                  ...filters,
                  supportsExcel: e.target.checked,
                })
              }
            />
          }
          label="Supports Excel"
        />
        
        <FormControlLabel
          control={
            <Switch
              checked={filters.recentlyUsed}
              onChange={(e: any) =>
                onFiltersChange({
                  ...filters,
                  recentlyUsed: e.target.checked,
                })
              }
            />
          }
          label="Recently Used"
        />
        
        <FormControlLabel
          control={
            <Switch
              checked={filters.isPopular}
              onChange={(e: any) =>
                onFiltersChange({
                  ...filters,
                  isPopular: e.target.checked,
                })
              }
            />
          }
          label="Popular Templates"
        />
      </Box>
    </Paper>
  );
};

export default TemplateFilter;
