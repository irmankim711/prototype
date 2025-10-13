"""
Data Mapping Service for Template-Based Report Generation
Handles field mapping between Excel data and template variables
"""
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from difflib import SequenceMatcher

from ..models import DataMapping, TemplateModel as Template
from ..services.excel_processing_service import excel_processing_service
from .. import db

logger = logging.getLogger(__name__)

class DataMappingService:
    """Service for managing data mappings between Excel and templates"""
    
    def __init__(self):
        logger.info("Data mapping service initialized")
    
    def create_mapping(self, excel_data: Dict[str, Any], template_vars: List[Dict[str, Any]], 
                      user_id: int, mapping_name: str = None) -> Dict[str, Any]:
        """
        Create data mapping between Excel data and template variables
        
        Args:
            excel_data: Excel data information (file_path, sheet_name, columns)
            template_vars: List of template variable definitions
            user_id: User ID creating the mapping
            mapping_name: Optional name for the mapping
            
        Returns:
            Created mapping dictionary
        """
        try:
            # Auto-generate field mappings
            auto_mappings = self.auto_map_fields(
                excel_data.get('columns', []), 
                template_vars
            )
            
            # Create mapping name if not provided
            if not mapping_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                mapping_name = f"Mapping_{timestamp}"
            
            # Create data mapping record
            data_mapping = DataMapping(
                name=mapping_name,
                template_id=excel_data.get('template_id'),
                excel_file_path=excel_data.get('file_path'),
                sheet_name=excel_data.get('sheet_name'),
                field_mappings=auto_mappings,
                transformations={},  # Will be populated later
                created_by=user_id
            )
            
            db.session.add(data_mapping)
            db.session.commit()
            
            # Validate the mapping
            validation_result = self.validate_mapping(data_mapping)
            
            # Update validation status
            data_mapping.is_validated = validation_result['valid']
            data_mapping.validation_errors = validation_result.get('errors', [])
            data_mapping.last_validated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Data mapping created: {data_mapping.id} by user {user_id}")
            
            result = data_mapping.to_dict()
            result['validation'] = validation_result
            result['auto_mapped_count'] = len([m for m in auto_mappings.values() if m])
            
            return {
                'success': True,
                'mapping': result
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating data mapping: {e}")
            return {
                'success': False,
                'error': 'Failed to create mapping',
                'message': str(e)
            }
    
    def auto_map_fields(self, excel_columns: List[str], template_vars: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Automatically map Excel columns to template variables
        
        Args:
            excel_columns: List of Excel column names
            template_vars: List of template variable definitions
            
        Returns:
            Dictionary mapping template variables to Excel columns
        """
        mappings = {}
        
        try:
            for var in template_vars:
                var_name = var.get('name', '')
                if not var_name:
                    continue
                
                # Find best matching column
                best_match = self._find_best_column_match(var_name, excel_columns)
                mappings[var_name] = best_match
            
            logger.info(f"Auto-mapped {len([m for m in mappings.values() if m])} out of {len(template_vars)} variables")
            
        except Exception as e:
            logger.error(f"Error in auto-mapping: {e}")
        
        return mappings
    
    def validate_mapping(self, mapping: DataMapping) -> Dict[str, Any]:
        """
        Validate data mapping configuration
        
        Args:
            mapping: DataMapping object to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': [],
            'coverage': 0,
            'mapped_fields': 0,
            'total_fields': 0
        }
        
        try:
            # Get template information
            template = Template.query.get(mapping.template_id)
            if not template:
                validation_result['valid'] = False
                validation_result['errors'].append('Template not found')
                return validation_result
            
            template_vars = template.variables or []
            field_mappings = mapping.field_mappings or {}
            
            # Check Excel file exists and is accessible
            if not mapping.excel_file_path or not os.path.exists(mapping.excel_file_path):
                validation_result['valid'] = False
                validation_result['errors'].append('Excel file not found or inaccessible')
                return validation_result
            
            # Get Excel data preview to validate columns
            excel_preview = excel_processing_service.get_data_preview(
                mapping.excel_file_path, 
                mapping.sheet_name, 
                rows=5
            )
            
            if not excel_preview.get('success'):
                validation_result['valid'] = False
                validation_result['errors'].append('Cannot read Excel data')
                return validation_result
            
            excel_columns = excel_preview.get('columns', [])
            
            # Validate field mappings
            validation_result['total_fields'] = len(template_vars)
            mapped_count = 0
            required_missing = 0
            
            for var in template_vars:
                var_name = var.get('name', '')
                is_required = var.get('required', False)
                mapped_column = field_mappings.get(var_name)
                
                if mapped_column:
                    mapped_count += 1
                    
                    # Check if mapped column exists in Excel
                    if mapped_column not in excel_columns:
                        validation_result['errors'].append(
                            f"Mapped column '{mapped_column}' for variable '{var_name}' not found in Excel data"
                        )
                        validation_result['valid'] = False
                    
                    # Check data type compatibility
                    expected_type = var.get('type', 'string')
                    excel_data_types = excel_preview.get('data_types', {})
                    actual_type = excel_data_types.get(mapped_column, 'string')
                    
                    if not self._are_types_compatible(expected_type, actual_type):
                        validation_result['warnings'].append(
                            f"Type mismatch for '{var_name}': expected {expected_type}, got {actual_type}"
                        )
                
                elif is_required:
                    required_missing += 1
                    validation_result['errors'].append(
                        f"Required variable '{var_name}' is not mapped"
                    )
                    validation_result['valid'] = False
            
            validation_result['mapped_fields'] = mapped_count
            validation_result['coverage'] = (mapped_count / len(template_vars) * 100) if template_vars else 100
            
            # Add suggestions
            if validation_result['coverage'] < 80:
                validation_result['suggestions'].append(
                    f"Only {validation_result['coverage']:.1f}% of template variables are mapped"
                )
            
            if required_missing > 0:
                validation_result['suggestions'].append(
                    f"{required_missing} required variables need to be mapped"
                )
            
            # Check for unused Excel columns
            mapped_columns = [col for col in field_mappings.values() if col]
            unused_columns = [col for col in excel_columns if col not in mapped_columns]
            
            if unused_columns:
                validation_result['suggestions'].append(
                    f"{len(unused_columns)} Excel columns are not mapped and could be used for additional variables"
                )
            
            logger.info(f"Mapping validation completed - Valid: {validation_result['valid']}, Coverage: {validation_result['coverage']:.1f}%")
            
        except Exception as e:
            logger.error(f"Error validating mapping: {e}")
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def apply_transformations(self, data: pd.DataFrame, mapping: DataMapping) -> pd.DataFrame:
        """
        Apply data transformations based on mapping configuration
        
        Args:
            data: pandas DataFrame with Excel data
            mapping: DataMapping object with transformation rules
            
        Returns:
            Transformed DataFrame
        """
        try:
            transformed_data = data.copy()
            transformations = mapping.transformations or {}
            field_mappings = mapping.field_mappings or {}
            
            # Apply transformations for each mapped field
            for var_name, excel_column in field_mappings.items():
                if not excel_column or excel_column not in transformed_data.columns:
                    continue
                
                var_transformations = transformations.get(var_name, {})
                
                # Apply data type conversion
                target_type = var_transformations.get('type')
                if target_type:
                    transformed_data[excel_column] = self._convert_column_type(
                        transformed_data[excel_column], target_type
                    )
                
                # Apply value transformations
                value_mapping = var_transformations.get('value_mapping')
                if value_mapping:
                    transformed_data[excel_column] = transformed_data[excel_column].map(
                        value_mapping
                    ).fillna(transformed_data[excel_column])
                
                # Apply formatting
                format_rule = var_transformations.get('format')
                if format_rule:
                    transformed_data[excel_column] = self._apply_formatting(
                        transformed_data[excel_column], format_rule
                    )
                
                # Apply validation rules
                validation_rules = var_transformations.get('validation')
                if validation_rules:
                    transformed_data = self._apply_validation_rules(
                        transformed_data, excel_column, validation_rules
                    )
            
            logger.info(f"Applied transformations to {len(field_mappings)} mapped fields")
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error applying transformations: {e}")
            return data  # Return original data on error
    
    def save_mapping(self, mapping_data: Dict[str, Any], user_id: int) -> Optional[int]:
        """
        Save or update data mapping
        
        Args:
            mapping_data: Mapping data dictionary
            user_id: User ID saving the mapping
            
        Returns:
            Mapping ID if successful, None otherwise
        """
        try:
            mapping_id = mapping_data.get('id')
            
            if mapping_id:
                # Update existing mapping
                mapping = DataMapping.query.get(mapping_id)
                if not mapping:
                    logger.warning(f"Mapping {mapping_id} not found for update")
                    return None
                
                # Update fields
                mapping.name = mapping_data.get('name', mapping.name)
                mapping.field_mappings = mapping_data.get('field_mappings', mapping.field_mappings)
                mapping.transformations = mapping_data.get('transformations', mapping.transformations)
                mapping.updated_at = datetime.utcnow()
                
            else:
                # Create new mapping
                mapping = DataMapping(
                    name=mapping_data.get('name', f"Mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    template_id=mapping_data.get('template_id'),
                    excel_file_path=mapping_data.get('excel_file_path'),
                    sheet_name=mapping_data.get('sheet_name'),
                    field_mappings=mapping_data.get('field_mappings', {}),
                    transformations=mapping_data.get('transformations', {}),
                    created_by=user_id
                )
                db.session.add(mapping)
            
            # Validate mapping
            validation_result = self.validate_mapping(mapping)
            mapping.is_validated = validation_result['valid']
            mapping.validation_errors = validation_result.get('errors', [])
            mapping.last_validated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Mapping saved successfully: {mapping.id}")
            return mapping.id
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving mapping: {e}")
            return None
    
    def get_mapping_suggestions(self, excel_columns: List[str], template_vars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get mapping suggestions for better field matching
        
        Args:
            excel_columns: List of Excel column names
            template_vars: List of template variable definitions
            
        Returns:
            Suggestions dictionary
        """
        suggestions = {
            'auto_mappings': {},
            'alternative_mappings': {},
            'unmapped_variables': [],
            'unused_columns': [],
            'confidence_scores': {}
        }
        
        try:
            # Generate auto mappings with confidence scores
            for var in template_vars:
                var_name = var.get('name', '')
                if not var_name:
                    continue
                
                matches = self._get_column_matches_with_scores(var_name, excel_columns)
                
                if matches:
                    best_match = matches[0]
                    suggestions['auto_mappings'][var_name] = best_match['column']
                    suggestions['confidence_scores'][var_name] = best_match['score']
                    
                    # Add alternatives if confidence is low
                    if best_match['score'] < 0.8 and len(matches) > 1:
                        suggestions['alternative_mappings'][var_name] = [
                            {'column': m['column'], 'score': m['score']} 
                            for m in matches[1:4]  # Top 3 alternatives
                        ]
                else:
                    suggestions['unmapped_variables'].append(var_name)
            
            # Find unused columns
            mapped_columns = list(suggestions['auto_mappings'].values())
            suggestions['unused_columns'] = [
                col for col in excel_columns if col not in mapped_columns
            ]
            
            logger.info(f"Generated mapping suggestions: {len(suggestions['auto_mappings'])} auto-mapped")
            
        except Exception as e:
            logger.error(f"Error generating mapping suggestions: {e}")
        
        return suggestions
    
    def _find_best_column_match(self, var_name: str, excel_columns: List[str]) -> Optional[str]:
        """Find the best matching Excel column for a template variable"""
        if not var_name or not excel_columns:
            return None
        
        var_name_lower = var_name.lower()
        best_match = None
        best_score = 0
        
        for column in excel_columns:
            column_lower = column.lower()
            
            # Exact match
            if var_name_lower == column_lower:
                return column
            
            # Calculate similarity score
            score = SequenceMatcher(None, var_name_lower, column_lower).ratio()
            
            # Boost score for partial matches
            if var_name_lower in column_lower or column_lower in var_name_lower:
                score += 0.2
            
            # Boost score for word matches
            var_words = set(var_name_lower.replace('_', ' ').replace('-', ' ').split())
            col_words = set(column_lower.replace('_', ' ').replace('-', ' ').split())
            
            if var_words & col_words:  # Common words
                score += 0.3
            
            if score > best_score:
                best_score = score
                best_match = column
        
        # Only return match if confidence is reasonable
        return best_match if best_score > 0.5 else None
    
    def _get_column_matches_with_scores(self, var_name: str, excel_columns: List[str]) -> List[Dict[str, Any]]:
        """Get all column matches with confidence scores"""
        matches = []
        var_name_lower = var_name.lower()
        
        for column in excel_columns:
            column_lower = column.lower()
            
            # Calculate base similarity
            score = SequenceMatcher(None, var_name_lower, column_lower).ratio()
            
            # Apply scoring boosts
            if var_name_lower == column_lower:
                score = 1.0
            elif var_name_lower in column_lower or column_lower in var_name_lower:
                score += 0.2
            
            # Word-based matching
            var_words = set(var_name_lower.replace('_', ' ').replace('-', ' ').split())
            col_words = set(column_lower.replace('_', ' ').replace('-', ' ').split())
            
            common_words = var_words & col_words
            if common_words:
                score += 0.3 * (len(common_words) / max(len(var_words), len(col_words)))
            
            if score > 0.3:  # Only include reasonable matches
                matches.append({
                    'column': column,
                    'score': min(score, 1.0)  # Cap at 1.0
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches
    
    def _are_types_compatible(self, expected_type: str, actual_type: str) -> bool:
        """Check if data types are compatible"""
        type_compatibility = {
            'string': ['string', 'integer', 'float', 'boolean', 'date', 'datetime'],
            'integer': ['integer', 'float', 'string'],
            'float': ['float', 'integer', 'string'],
            'boolean': ['boolean', 'string', 'integer'],
            'date': ['date', 'datetime', 'string'],
            'datetime': ['datetime', 'date', 'string']
        }
        
        compatible_types = type_compatibility.get(expected_type, [expected_type])
        return actual_type in compatible_types
    
    def _convert_column_type(self, series: pd.Series, target_type: str) -> pd.Series:
        """Convert pandas Series to target data type"""
        try:
            if target_type == 'integer':
                return pd.to_numeric(series, errors='coerce').astype('Int64')
            elif target_type == 'float':
                return pd.to_numeric(series, errors='coerce')
            elif target_type == 'boolean':
                return series.astype(str).str.lower().isin(['true', '1', 'yes', 'y'])
            elif target_type in ['date', 'datetime']:
                return pd.to_datetime(series, errors='coerce')
            else:  # string
                return series.astype(str)
        except Exception as e:
            logger.warning(f"Type conversion failed for {target_type}: {e}")
            return series
    
    def _apply_formatting(self, series: pd.Series, format_rule: str) -> pd.Series:
        """Apply formatting rule to pandas Series"""
        try:
            if format_rule == 'uppercase':
                return series.astype(str).str.upper()
            elif format_rule == 'lowercase':
                return series.astype(str).str.lower()
            elif format_rule == 'title':
                return series.astype(str).str.title()
            elif format_rule == 'strip':
                return series.astype(str).str.strip()
            elif format_rule.startswith('date:'):
                date_format = format_rule.split(':', 1)[1]
                return pd.to_datetime(series, errors='coerce').dt.strftime(date_format)
            else:
                return series
        except Exception as e:
            logger.warning(f"Formatting failed for rule {format_rule}: {e}")
            return series
    
    def _apply_validation_rules(self, df: pd.DataFrame, column: str, 
                               validation_rules: Dict[str, Any]) -> pd.DataFrame:
        """Apply validation rules to DataFrame column"""
        try:
            # Mark invalid rows
            invalid_mask = pd.Series([False] * len(df), index=df.index)
            
            # Required field validation
            if validation_rules.get('required', False):
                invalid_mask |= df[column].isna() | (df[column].astype(str).str.strip() == '')
            
            # Range validation for numeric fields
            if 'min_value' in validation_rules:
                invalid_mask |= df[column] < validation_rules['min_value']
            
            if 'max_value' in validation_rules:
                invalid_mask |= df[column] > validation_rules['max_value']
            
            # Length validation for string fields
            if 'min_length' in validation_rules:
                invalid_mask |= df[column].astype(str).str.len() < validation_rules['min_length']
            
            if 'max_length' in validation_rules:
                invalid_mask |= df[column].astype(str).str.len() > validation_rules['max_length']
            
            # Pattern validation
            if 'pattern' in validation_rules:
                import re
                pattern = validation_rules['pattern']
                invalid_mask |= ~df[column].astype(str).str.match(pattern, na=False)
            
            # Add validation status column
            df[f'{column}_valid'] = ~invalid_mask
            
            return df
            
        except Exception as e:
            logger.warning(f"Validation rules application failed: {e}")
            return df

# Global service instance
data_mapping_service = DataMappingService()