import React from 'react';
/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Template Selector Component
 * Grid view for selecting report templates with filtering and search
 */

import { useState, useEffect } from "react";
  
import { Box, Grid, Typography, TextField, InputAdornment, CircularProgress, Alert, Pagination, Chip, FormControl, InputLabel, Select, MenuItem, Button } from "@mui/material";
  
import { Search, FilterList, ViewModule, ViewList, Refresh } from "@mui/icons-material";

import TemplateCard from './TemplateCard';

import TemplateFilter from './TemplateFilter';

import TemplatePreview from './TemplatePreview';

import { templateService } from "../../services/templateService";

interface Template {
  id: number;
  
name: string;
  
description: string;
  
category: string;
  
template_type: string;
  
supports_excel: boolean;
  
usage_count: number;
  
last_used: string | null;
  
created_at: string;
  
creator_name: string;
  
preview_url?: string;
  
complexity: 'simple' | 'moderate' | 'complex';
  
tags: string[];
}

interface TemplateSelectorProps {
  onTemplateSelect: (template: Template) => void;
  
selectedTemplateId?: number;
  
showPreview?: boolean;
  
allowMultiSelect?: boolean;
  
filterCategories?: string[];
  
maxSelection?: number;
}

const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  onTemplateSelect,
  selectedTemplateId,
  showPreview = true,
  allowMultiSelect = false,
  filterCategories,
  maxSelection = 1,
}) => {
  const [templates, setTemplates] = useState<Template[]>([]);
  
const [loading, setLoading] = useState(true);
  
const [error, setError] = useState<string | null>(null);
  
const [searchTerm, setSearchTerm] = useState('');
  
const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
const [selectedType, setSelectedType] = useState<string>('all');
  
const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
const [page, setPage] = useState(1);
  
const [totalPages, setTotalPages] = useState(1);
  
const [selectedTemplates, setSelectedTemplates] = useState<Set<number>>(new Set());
  
const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);
  
const [showFilters, setShowFilters] = useState(false);

const templatesPerPage = 12;

useEffect(() => {
    loadTemplates();
  }, [page, searchTerm, selectedCategory, selectedType]);

useEffect(() => {
    if (selectedTemplateId) {
      setSelectedTemplates(new Set([selectedTemplateId]));
    }
  }, [selectedTemplateId]);

const loadTemplates = async () => {
    try {
      setLoading(true);
      
setError(null);

const filters: any = {};

if (searchTerm) {
        filters.search = searchTerm;
      }
      
      if (selectedCategory !== 'all') {
        filters.category = selectedCategory;
      }
      
      if (selectedType !== 'all') {
        filters.template_type = selectedType;
      }

      if (filterCategories && filterCategories.length > 0) {
        filters.categories = filterCategories;
      }

      const response = await templateService.getTemplates(filters);

if (response.success) {
        // Add mock complexity and tags for demo
        const enhancedTemplates = response.templates.map((template: React.ChangeEvent<HTMLInputElement>) => ({
          ...template,
          complexity: getTemplateComplexity(template),
          tags: generateTemplateTags(template),
        }));

        // Paginate results
        const startIndex = (page - 1) * templatesPerPage;
        
const endIndex = startIndex + templatesPerPage;
        
const paginatedTemplates = enhancedTemplates.slice(startIndex, endIndex);

setTemplates(paginatedTemplates);
        
setTotalPages(Math.ceil(enhancedTemplates.length / templatesPerPage));
      } else {
        setError(response.error || 'Failed to load templates');
      }
    } catch (err) {
      console.error('Error loading templates:', err);
      
setError('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

const getTemplateComplexity = (template: any): 'simple' | 'moderate' | 'complex' => {
    const variableCount = template.variables?.length || 0;
    
if (variableCount <= 5) return 'simple';
    
if (variableCount <= 15) return 'moderate';
    
return 'complex';
  };

const generateTemplateTags = (template: any): string[] => {
    const tags = [];

if (template.supports_excel) tags.push('Excel');
    
if (template.category) tags.push(template.category);
    
if (template.template_type) tags.push(template.template_type);
    
if (template.usage_count > 10) tags.push('Popular');
    
if (template.last_used) {
      const lastUsed = new Date(template.last_used);
      
const daysSinceUsed = (Date.now() - lastUsed.getTime()) / (1000 * 60 * 60 * 24);
      
if (daysSinceUsed <= 7) tags.push('Recent');
    }
    
    return tags;
  };

const handleTemplateSelect = (template: Template) => {
    if (allowMultiSelect) {
      const newSelected = new Set(selectedTemplates);

if (newSelected.has(template.id)) {
        newSelected.delete(template.id);
      } else if (newSelected.size < maxSelection) {
        newSelected.add(template.id);
      }
      
      setSelectedTemplates(newSelected);
      
      // Call callback with array of selected templates
      const selectedTemplateObjects = templates.filter(t => newSelected.has(t.id));
      
onTemplateSelect(selectedTemplateObjects as any);
    } else {
      setSelectedTemplates(new Set([template.id]));
      
onTemplateSelect(template);
    }
  };

const handlePreview = (template: Template) => {
    setPreviewTemplate(template);
  };

const handleRefresh = () => {
    setPage(1);
    
loadTemplates();
  };

const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
    
setPage(1);
  };

const handleCategoryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedCategory(event.target.value);
    
setPage(1);
  };

const handleTypeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedType(event.target.value);
    
setPage(1);
  };

const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'business', label: 'Business' },
    { value: 'financial', label: 'Financial' },
    { value: 'marketing', label: 'Marketing' },
    { value: 'technical', label: 'Technical' },
    { value: 'academic', label: 'Academic' },
    { value: 'general', label: 'General' },
  ];

const types = [
    { value: 'all', label: 'All Types' },
    { value: 'report', label: 'Report' },
    { value: 'dashboard', label: 'Dashboard' },
    { value: 'presentation', label: 'Presentation' },
    { value: 'document', label: 'Document' },
  ];

if (loading && templates.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h5" component="h2">
          Select Template
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<FilterList />}
            onClick={() => setShowFilters(!showFilters)}
          >
            Filters
          </Button>
          
          <Button
            variant="outlined"
            startIcon={viewMode === 'grid' ? <ViewList /> : <ViewModule />}
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            {viewMode === 'grid' ? 'List' : 'Grid'}
          </Button>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search templates..."
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        {showFilters && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={selectedCategory}
                onChange={handleCategoryChange}
                label="Category"
              >
                {categories.map((category: any) => (
                  <MenuItem key={category.value} value={category.value}>
                    {category.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Type</InputLabel>
              <Select
                value={selectedType}
                onChange={handleTypeChange}
                label="Type"
              >
                {types.map((type: any) => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        )}
      </Box>

      {/* Selection Summary */}
      {allowMultiSelect && selectedTemplates.size > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {selectedTemplates.size} of {maxSelection} templates selected
          </Typography>
        </Box>
      )}

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Templates Grid/List */}
      {templates.length === 0 && !loading ? (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" gutterBottom>
            No templates found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Try adjusting your search criteria or filters
          </Typography>
        </Box>
      ) : (
        <>
          <Grid container spacing={viewMode === 'grid' ? 3 : 1}>
            {templates.map((template: any) => (
              <Grid 
                item 
                xs={12} 
                sm={viewMode === 'grid' ? 6 : 12} 
                md={viewMode === 'grid' ? 4 : 12} 
                lg={viewMode === 'grid' ? 3 : 12}
                key={template.id}
              >
                <TemplateCard
                  template={template}
                  selected={selectedTemplates.has(template.id)}
                  onSelect={() => handleTemplateSelect(template)}
                  onPreview={showPreview ? () => handlePreview(template) : undefined}
                  viewMode={viewMode}
                />
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(event, value) => setPage(value)}
                color="primary"
                size="large"
              />
            </Box>
          )}
        </>
      )}

      {/* Loading Overlay */}
      {loading && templates.length > 0 && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            bgcolor: 'rgba(255, 255, 255, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <CircularProgress />
        </Box>
      )}

      {/* Template Preview Dialog */}
      {previewTemplate && (
        <TemplatePreview
          template={previewTemplate}
          open={!!previewTemplate}
          onClose={() => setPreviewTemplate(null)}
          onSelect={() => {
            handleTemplateSelect(previewTemplate);
            
setPreviewTemplate(null);
          }}
        />
      )}
    </Box>
  );
};

export default TemplateSelector;
