/**
 * Template Card Component
 * Individual template card with thumbnail, details, and actions
 */

import React from 'react';
  
import { Card, CardContent, CardActions, CardMedia, Typography, Button, Chip, Box, IconButton, Tooltip, Avatar, LinearProgress } from "@mui/material";
  
import { Visibility, GetApp, Star, StarBorder, Schedule, Person, Assessment, CheckCircle, TableChart } from "@mui/icons-material";

import { formatDistanceToNow } from "date-fns";

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

interface TemplateCardProps {
  template: Template;
  
selected: boolean;
  
onSelect: () => void;
  
onPreview?: () => void;
  
viewMode?: 'grid' | 'list';
  
showFavorite?: boolean;
  
onFavorite?: (templateId: number) => void;
  
isFavorite?: boolean;
}

const TemplateCard: React.FC<TemplateCardProps> = ({
  template,
  selected,
  onSelect,
  onPreview,
  viewMode = 'grid',
  showFavorite = false,
  onFavorite,
  isFavorite = false,
}) => {
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple':
        return 'success';
      
case 'moderate':
        return 'warning';
      
case 'complex':
        return 'error';
      
default:
        return 'default';
    }
  };

const getComplexityProgress = (complexity: string) => {
    switch (complexity) {
      case 'simple':
        return 33;
      
case 'moderate':
        return 66;
      
case 'complex':
        return 100;
      
default:
        return 0;
    }
  };

const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'business':
        return <Assessment />;
      
case 'financial':
        return <TableChart />;
      
default:
        return <Assessment />;
    }
  };

if (viewMode === 'list') {
    return (
      <Card
        sx={{
          display: 'flex',
          mb: 1,
          border: selected ? 2 : 1,
          borderColor: selected ? 'primary.main' : 'grey.300',
          cursor: 'pointer',
          transition: 'all 0.2s',
          '&:hover': {
            elevation: 4,
            transform: 'translateY(-1px)',
          },
        }}
        onClick={onSelect}
      >
        {/* Thumbnail */}
        <Box sx={{ width: 120, flexShrink: 0 }}>
          <CardMedia
            component="div"
            sx={{
              height: 80,
              background: `linear-gradient(135deg, ${
                selected ? '#1976d2' : '#f5f5f5'
              } 0%, ${selected ? '#42a5f5' : '#e0e0e0'} 100%)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: selected ? 'white' : 'text.secondary',
            }}
          >
            {getCategoryIcon(template.category)}
          </CardMedia>
        </Box>

        {/* Content */}
        <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
          <CardContent sx={{ flex: 1, pb: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
              <Typography variant="h6" component="h3" noWrap>
                {template.name}
              </Typography>
              
              {selected && (
                <CheckCircle color="primary" sx={{ ml: 1 }} />
              )}
            </Box>

            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
                mb: 1,
              }}
            >
              {template.description}
            </Typography>

            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
              <Chip
                label={template.category}
                size="small"
                variant="outlined"
              />
              <Chip
                label={template.complexity}
                size="small"
                color={getComplexityColor(template.complexity) as any}
                variant="outlined"
              />
              {template.supports_excel && (
                <Chip
                  label="Excel"
                  size="small"
                  color="info"
                  variant="outlined"
                />
              )}
            </Box>
          </CardContent>

          <CardActions sx={{ pt: 0 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Used {template.usage_count} times
              </Typography>
              
              {template.last_used && (
                <Typography variant="caption" color="text.secondary">
                  • Last used {formatDistanceToNow(new Date(template.last_used), { addSuffix: true })}
                </Typography>
              )}
            </Box>

            {onPreview && (
              <Button size="small" startIcon={<Visibility />} onClick={(e: any) => {
                e.stopPropagation();
                
onPreview();
              }}>
                Preview
              </Button>
            )}
          </CardActions>
        </Box>
      </Card>
    );
  }

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        border: selected ? 2 : 1,
        borderColor: selected ? 'primary.main' : 'grey.300',
        cursor: 'pointer',
        transition: 'all 0.2s',
        position: 'relative',
        '&:hover': {
          elevation: 4,
          transform: 'translateY(-2px)',
        },
      }}
      onClick={onSelect}
    >
      {/* Selection Indicator */}
      {selected && (
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            zIndex: 1,
          }}
        >
          <CheckCircle color="primary" />
        </Box>
      )}

      {/* Favorite Button */}
      {showFavorite && (
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            left: 8,
            zIndex: 1,
          }}
        >
          <IconButton
            size="small"
            onClick={(e: any) => {
              e.stopPropagation();
              
onFavorite?.(template.id);
            }}
            sx={{
              bgcolor: 'rgba(255, 255, 255, 0.9)',
              '&:hover': {
                bgcolor: 'rgba(255, 255, 255, 1)',
              },
            }}
          >
            {isFavorite ? <Star color="warning" /> : <StarBorder />}
          </IconButton>
        </Box>
      )}

      {/* Thumbnail */}
      <CardMedia
        component="div"
        sx={{
          height: 140,
          background: `linear-gradient(135deg, ${
            selected ? '#1976d2' : '#f5f5f5'
          } 0%, ${selected ? '#42a5f5' : '#e0e0e0'} 100%)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: selected ? 'white' : 'text.secondary',
          position: 'relative',
        }}
      >
        {getCategoryIcon(template.category)}
        
        {/* Template Type Badge */}
        <Chip
          label={template.template_type}
          size="small"
          sx={{
            position: 'absolute',
            bottom: 8,
            left: 8,
            bgcolor: 'rgba(255, 255, 255, 0.9)',
          }}
        />
      </CardMedia>

      <CardContent sx={{ flexGrow: 1 }}>
        {/* Title */}
        <Typography variant="h6" component="h3" gutterBottom noWrap>
          {template.name}
        </Typography>

        {/* Description */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            mb: 2,
            minHeight: '3.6em',
          }}
        >
          {template.description}
        </Typography>

        {/* Complexity Indicator */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              Complexity
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {template.complexity}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={getComplexityProgress(template.complexity)}
            color={getComplexityColor(template.complexity) as any}
            sx={{ height: 4, borderRadius: 2 }}
          />
        </Box>

        {/* Tags */}
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 2 }}>
          {template.tags.slice(0, 3).map((tag, index) => (
            <Chip
              key={index}
              label={tag}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.7rem', height: 20 }}
            />
          ))}
          {template.tags.length > 3 && (
            <Chip
              label={`+${template.tags.length - 3}`}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.7rem', height: 20 }}
            />
          )}
        </Box>

        {/* Metadata */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <Avatar sx={{ width: 20, height: 20, fontSize: '0.75rem' }}>
            {template.creator_name[0]}
          </Avatar>
          <Typography variant="caption" color="text.secondary" noWrap>
            {template.creator_name}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Schedule sx={{ fontSize: 16 }} color="action" />
          <Typography variant="caption" color="text.secondary">
            Used {template.usage_count} times
          </Typography>
        </Box>

        {template.last_used && (
          <Typography variant="caption" color="text.secondary" display="block">
            Last used {formatDistanceToNow(new Date(template.last_used), { addSuffix: true })}
          </Typography>
        )}
      </CardContent>

      <CardActions>
        {onPreview && (
          <Button
            size="small"
            startIcon={<Visibility />}
            onClick={(e: any) => {
              e.stopPropagation();
              
onPreview();
            }}
          >
            Preview
          </Button>
        )}
        
        <Button
          size="small"
          variant={selected ? 'contained' : 'outlined'}
          onClick={(e: any) => {
            e.stopPropagation();
            
onSelect();
          }}
        >
          {selected ? 'Selected' : 'Select'}
        </Button>
      </CardActions>
    </Card>
  );
};

export default TemplateCard;
