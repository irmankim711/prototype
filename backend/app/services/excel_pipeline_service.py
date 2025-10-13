"""
Excel Pipeline Service - Complete Excel Generation Workflow
Orchestrates the entire Excel generation process from form data to validated output

Features:
- Complete pipeline orchestration
- Progress tracking and monitoring
- Error handling and recovery
- Integration with enhanced Excel service
- Support for different export configurations
- Real-time status updates
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import uuid
from pathlib import Path

from .enhanced_excel_service import EnhancedExcelService, ExcelValidationError, DataProcessingError
from ..config.excel_config import get_excel_config, customize_excel_config

logger = logging.getLogger(__name__)

class ExcelPipelineService:
    """
    Complete Excel generation pipeline service
    Handles the entire workflow from data preparation to final validation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.base_config = self.config.get('base_config', 'production')
        self.excel_config = customize_excel_config(
            base_config=self.base_config,
            customizations=self.config.get('excel_customizations', {})
        )
        
        # Pipeline configuration
        self.enable_progress_tracking = self.config.get('enable_progress_tracking', True)
        self.enable_validation = self.config.get('enable_validation', True)
        self.enable_compression = self.config.get('enable_compression', True)
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 5)  # seconds
        
        # Output configuration
        self.output_directory = self.config.get('output_directory', 'reports/excel')
        self.filename_template = self.config.get('filename_template', 'form_export_{timestamp}_{uuid}.xlsx')
        
        # Initialize enhanced Excel service
        self.excel_service = EnhancedExcelService(config=self.excel_config)
        
        # Pipeline state
        self.current_pipeline_id = None
        self.pipeline_status = 'idle'
        self.start_time = None
        self.progress = 0
        self.current_step = None
        self.errors = []
        self.warnings = []
        
        logger.info(f"ExcelPipelineService initialized with config: {self.excel_config}")
    
    def generate_excel_pipeline(
        self,
        data: List[Dict[str, Any]],
        pipeline_config: Dict[str, Any] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute complete Excel generation pipeline
        
        Args:
            data: Form submission data
            pipeline_config: Pipeline-specific configuration
            progress_callback: Optional progress callback function
            
        Returns:
            Complete pipeline results
        """
        pipeline_id = str(uuid.uuid4())
        self.current_pipeline_id = pipeline_id
        self.pipeline_status = 'running'
        self.start_time = datetime.now()
        self.progress = 0
        self.current_step = 'initializing'
        self.errors = []
        self.warnings = []
        
        # Merge configurations
        final_config = self._merge_configurations(pipeline_config)
        
        # Setup progress tracking
        if self.enable_progress_tracking and progress_callback:
            self.excel_service.progress_callback = progress_callback
        
        pipeline_result = {
            'pipeline_id': pipeline_id,
            'success': False,
            'status': 'failed',
            'start_time': self.start_time.isoformat(),
            'end_time': None,
            'duration_seconds': 0,
            'progress': 0,
            'current_step': None,
            'excel_file_path': None,
            'excel_file_size': 0,
            'data_quality_score': 0.0,
            'validation_passed': False,
            'errors': [],
            'warnings': [],
            'pipeline_metrics': {}
        }
        
        try:
            # Step 1: Pipeline initialization and validation
            self._update_pipeline_progress(5, 'initializing', "Initializing Excel generation pipeline...")
            self._validate_pipeline_inputs(data, final_config)
            
            # Step 2: Data preparation and analysis
            self._update_pipeline_progress(15, 'data_preparation', "Preparing and analyzing form data...")
            prepared_data = self._prepare_data_for_excel(data, final_config)
            
            # Step 3: Excel generation
            self._update_pipeline_progress(40, 'excel_generation', "Generating Excel file...")
            excel_result = self._generate_excel_file(prepared_data, final_config)
            
            # Step 4: Validation and quality checks
            if self.enable_validation:
                self._update_pipeline_progress(80, 'validation', "Validating Excel output...")
                validation_result = self._validate_excel_output(excel_result, prepared_data)
                pipeline_result['validation_passed'] = validation_result['valid']
                pipeline_result['data_quality_score'] = validation_result.get('validation_score', 0.0)
            
            # Step 5: Finalization
            self._update_pipeline_progress(95, 'finalizing', "Finalizing Excel generation...")
            final_result = self._finalize_pipeline(excel_result, validation_result if self.enable_validation else None)
            
            # Update pipeline result
            pipeline_result.update({
                'success': True,
                'status': 'completed',
                'end_time': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
                'progress': 100,
                'current_step': 'completed',
                'excel_file_path': final_result['file_path'],
                'excel_file_size': final_result['file_size'],
                'pipeline_metrics': self._get_pipeline_metrics()
            })
            
            self.pipeline_status = 'completed'
            self._update_pipeline_progress(100, 'completed', "Excel generation pipeline completed successfully!")
            
            logger.info(f"Excel pipeline {pipeline_id} completed successfully")
            return pipeline_result
            
        except Exception as e:
            error_msg = f"Excel pipeline failed: {str(e)}"
            logger.error(error_msg)
            
            # Update pipeline result with error
            pipeline_result.update({
                'status': 'failed',
                'end_time': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                'current_step': self.current_step,
                'errors': self.errors + [error_msg],
                'warnings': self.warnings,
                'pipeline_metrics': self._get_pipeline_metrics()
            })
            
            self.pipeline_status = 'failed'
            self.errors.append(error_msg)
            
            return pipeline_result
        
        finally:
            # Cleanup
            self._cleanup_pipeline()
    
    def _merge_configurations(self, pipeline_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge pipeline configuration with base Excel configuration"""
        if not pipeline_config:
            pipeline_config = {}
        
        # Start with base Excel config
        merged_config = self.excel_config.copy()
        
        # Override with pipeline-specific config
        merged_config.update(pipeline_config)
        
        # Ensure critical settings are preserved
        merged_config['validation_enabled'] = self.enable_validation
        merged_config['compression_enabled'] = self.enable_compression
        
        return merged_config
    
    def _validate_pipeline_inputs(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
        """Validate pipeline inputs and configuration"""
        if not data:
            raise DataProcessingError("No data provided for Excel generation")
        
        if not isinstance(data, list):
            raise DataProcessingError("Data must be a list of dictionaries")
        
        # Validate configuration
        required_config_keys = ['max_chunk_size', 'max_memory_mb']
        for key in required_config_keys:
            if key not in config:
                raise DataProcessingError(f"Missing required configuration: {key}")
        
        # Check data size limits
        if len(data) > 100000:
            raise DataProcessingError("Dataset too large (max 100,000 records)")
        
        logger.info(f"Pipeline inputs validated. Dataset size: {len(data)} records")
    
    def _prepare_data_for_excel(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare and preprocess data for Excel generation"""
        try:
            # Apply data preprocessing if configured
            if config.get('preprocess_data', True):
                data = self._preprocess_form_data(data)
            
            # Apply data filtering if configured
            if config.get('filters'):
                data = self._apply_data_filters(data, config['filters'])
            
            # Apply data sorting if configured
            if config.get('sort_by'):
                data = self._sort_data(data, config['sort_by'], config.get('sort_order', 'asc'))
            
            logger.info(f"Data preparation completed. Final dataset size: {len(data)} records")
            return data
            
        except Exception as e:
            logger.error(f"Data preparation failed: {str(e)}")
            raise DataProcessingError(f"Data preparation failed: {str(e)}")
    
    def _preprocess_form_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Preprocess form data for better Excel compatibility"""
        processed_data = []
        
        for record in data:
            processed_record = {}
            
            for key, value in record.items():
                # Clean field names
                clean_key = self._clean_field_name(key)
                
                # Clean field values
                clean_value = self._clean_field_value(value)
                
                processed_record[clean_key] = clean_value
            
            processed_data.append(processed_record)
        
        return processed_data
    
    def _clean_field_name(self, field_name: str) -> str:
        """Clean field names for Excel compatibility"""
        if not isinstance(field_name, str):
            field_name = str(field_name)
        
        # Remove problematic characters
        clean_name = field_name.replace('\n', ' ').replace('\r', ' ')
        clean_name = clean_name.replace('/', '_').replace('\\', '_')
        clean_name = clean_name.replace('?', '').replace('*', '')
        clean_name = clean_name.replace('[', '(').replace(']', ')')
        
        # Limit length
        if len(clean_name) > 50:
            clean_name = clean_name[:47] + '...'
        
        return clean_name.strip()
    
    def _clean_field_value(self, value: Any) -> Any:
        """Clean field values for Excel compatibility"""
        if value is None:
            return ''
        
        if isinstance(value, (str, int, float, bool)):
            return value
        
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        
        if isinstance(value, list):
            return ', '.join(str(item) for item in value if item is not None)
        
        if isinstance(value, dict):
            try:
                return json.dumps(value, ensure_ascii=False, default=str)
            except:
                return str(value)
        
        return str(value)
    
    def _apply_data_filters(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply data filters to the dataset"""
        filtered_data = data
        
        for filter_key, filter_value in filters.items():
            if filter_key == 'date_range':
                filtered_data = self._filter_by_date_range(filtered_data, filter_value)
            elif filter_key == 'field_value':
                filtered_data = self._filter_by_field_value(filtered_data, filter_value)
            elif filter_key == 'exclude_empty':
                if filter_value:
                    filtered_data = self._filter_empty_fields(filtered_data)
        
        return filtered_data
    
    def _filter_by_date_range(self, data: List[Dict[str, Any]], date_range: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter data by date range"""
        start_date = date_range.get('start')
        end_date = date_range.get('end')
        
        if not start_date and not end_date:
            return data
        
        filtered_data = []
        
        for record in data:
            # Look for date fields
            record_date = None
            for key, value in record.items():
                if 'date' in key.lower() or 'at' in key.lower():
                    try:
                        if isinstance(value, str):
                            record_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        elif isinstance(value, datetime):
                            record_date = value
                        break
                    except:
                        continue
            
            if record_date:
                include_record = True
                
                if start_date and record_date < start_date:
                    include_record = False
                
                if end_date and record_date > end_date:
                    include_record = False
                
                if include_record:
                    filtered_data.append(record)
            else:
                # If no date field found, include record
                filtered_data.append(record)
        
        return filtered_data
    
    def _filter_by_field_value(self, data: List[Dict[str, Any]], field_filter: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter data by specific field values"""
        field_name = field_filter.get('field')
        field_value = field_filter.get('value')
        operator = field_filter.get('operator', 'equals')
        
        if not field_name or field_value is None:
            return data
        
        filtered_data = []
        
        for record in data:
            if field_name in record:
                record_value = record[field_name]
                include_record = False
                
                if operator == 'equals':
                    include_record = record_value == field_value
                elif operator == 'contains':
                    include_record = str(field_value) in str(record_value)
                elif operator == 'starts_with':
                    include_record = str(record_value).startswith(str(field_value))
                elif operator == 'ends_with':
                    include_record = str(record_value).endswith(str(field_value))
                elif operator == 'greater_than':
                    include_record = record_value > field_value
                elif operator == 'less_than':
                    include_record = record_value < field_value
                
                if include_record:
                    filtered_data.append(record)
            else:
                # Field not found, include record
                filtered_data.append(record)
        
        return filtered_data
    
    def _filter_empty_fields(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out records with empty required fields"""
        filtered_data = []
        
        for record in data:
            # Check if record has any non-empty values
            has_data = False
            for value in record.values():
                if value is not None and value != '':
                    has_data = True
                    break
            
            if has_data:
                filtered_data.append(record)
        
        return filtered_data
    
    def _sort_data(self, data: List[Dict[str, Any]], sort_by: str, sort_order: str = 'asc') -> List[Dict[str, Any]]:
        """Sort data by specified field"""
        if not data or sort_by not in data[0]:
            return data
        
        reverse = sort_order.lower() == 'desc'
        
        try:
            sorted_data = sorted(data, key=lambda x: x.get(sort_by, ''), reverse=reverse)
            return sorted_data
        except Exception as e:
            logger.warning(f"Data sorting failed: {str(e)}")
            return data
    
    def _generate_excel_file(self, data: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Excel file using the enhanced Excel service"""
        try:
            # Generate output file path
            output_path = self._generate_output_path()
            
            # Generate Excel file
            excel_result = self.excel_service.generate_excel(
                data=data,
                output_path=output_path,
                template_config=config.get('template_config', {})
            )
            
            if not excel_result['success']:
                raise DataProcessingError(f"Excel generation failed: {excel_result['errors']}")
            
            logger.info(f"Excel file generated successfully: {output_path}")
            return excel_result
            
        except Exception as e:
            logger.error(f"Excel file generation failed: {str(e)}")
            raise DataProcessingError(f"Excel file generation failed: {str(e)}")
    
    def _validate_excel_output(self, excel_result: Dict[str, Any], original_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate the generated Excel output"""
        try:
            # Use the enhanced Excel service validation
            validation_result = self.excel_service._validate_excel_output(
                excel_result['file_path'], 
                original_data
            )
            
            if not validation_result['valid']:
                logger.warning(f"Excel validation failed: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Excel validation failed: {str(e)}")
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': [],
                'validation_score': 0.0
            }
    
    def _finalize_pipeline(self, excel_result: Dict[str, Any], validation_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Finalize the pipeline and prepare results"""
        try:
            # Verify file exists and has content
            file_path = excel_result['file_path']
            if not os.path.exists(file_path):
                raise DataProcessingError("Generated Excel file not found")
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise DataProcessingError("Generated Excel file is empty")
            
            # Add metadata to Excel file if configured
            if self.config.get('add_pipeline_metadata', True):
                self._add_pipeline_metadata(file_path)
            
            logger.info(f"Pipeline finalized successfully. File: {file_path}, Size: {file_size} bytes")
            
            return {
                'file_path': file_path,
                'file_size': file_size,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Pipeline finalization failed: {str(e)}")
            raise DataProcessingError(f"Pipeline finalization failed: {str(e)}")
    
    def _add_pipeline_metadata(self, file_path: str) -> None:
        """Add pipeline metadata to the Excel file"""
        try:
            # This would add pipeline metadata to the Excel file
            # For now, just log the action
            logger.info(f"Pipeline metadata would be added to: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to add pipeline metadata: {str(e)}")
    
    def _generate_output_path(self) -> str:
        """Generate output file path for Excel file"""
        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        
        filename = self.filename_template.format(
            timestamp=timestamp,
            uuid=unique_id
        )
        
        return os.path.join(self.output_directory, filename)
    
    def _update_pipeline_progress(self, progress: int, step: str, message: str) -> None:
        """Update pipeline progress and status"""
        self.progress = progress
        self.current_step = step
        
        if self.enable_progress_tracking:
            logger.info(f"Pipeline Progress [{progress}%] - {step}: {message}")
    
    def _get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get pipeline performance metrics"""
        return {
            'pipeline_id': self.current_pipeline_id,
            'status': self.pipeline_status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'duration_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'progress': self.progress,
            'current_step': self.current_step,
            'errors_count': len(self.errors),
            'warnings_count': len(self.warnings),
            'memory_usage_mb': self.excel_service._get_memory_usage()
        }
    
    def _cleanup_pipeline(self) -> None:
        """Clean up pipeline resources"""
        try:
            # Cleanup Excel service
            self.excel_service.cleanup()
            
            # Reset pipeline state
            self.pipeline_status = 'idle'
            self.progress = 0
            self.current_step = None
            
            logger.info("Pipeline cleanup completed")
            
        except Exception as e:
            logger.warning(f"Pipeline cleanup failed: {str(e)}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            'service_name': 'ExcelPipelineService',
            'pipeline_id': self.current_pipeline_id,
            'status': self.pipeline_status,
            'progress': self.progress,
            'current_step': self.current_step,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'errors_count': len(self.errors),
            'warnings_count': len(self.warnings),
            'excel_service_status': self.excel_service.get_service_status()
        }
    
    def cancel_pipeline(self) -> bool:
        """Cancel the current pipeline if running"""
        if self.pipeline_status == 'running':
            self.pipeline_status = 'cancelled'
            self.current_step = 'cancelled'
            logger.info("Pipeline cancelled by user")
            return True
        return False
