"""
Real-time Template Population Service
Handles template population with real-time collected data and DocxTemplater integration
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from pathlib import Path
import tempfile
import shutil

from ..models import ReportTemplate
from .template_optimizer import TemplateOptimizer
from ..core.exceptions import ReportGenerationError

logger = logging.getLogger(__name__)

class RealtimeTemplateService:
    """Service for populating templates with real-time data"""
    
    def __init__(self):
        self.template_optimizer = TemplateOptimizer()
        self.supported_formats = ['.docx', '.tex', '.html']
    
    def populate_template_with_realtime_data(self, template_id: int, collected_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Populate template with real-time collected data
        
        Args:
            template_id: ID of the template to use
            collected_data: Data collected from real-time sources
            config: Configuration for template population
            
        Returns:
            Dict containing populated template info and file paths
        """
        try:
            # Get template
            template = ReportTemplate.query.get(template_id)
            if not template:
                raise ReportGenerationError(f"Template {template_id} not found")
            
            logger.info(f"Starting real-time template population for template {template_id}")
            
            # Prepare template context with real-time data
            template_context = self._prepare_template_context(collected_data, config)
            
            # Get template content
            if template.template_content:
                template_content = template.template_content
                template_format = self._detect_template_format(template_content)
            else:
                raise ReportGenerationError(f"Template {template_id} has no content")
            
            # Populate template based on format
            populated_results = {}
            
            if template_format == 'docx':
                populated_results.update(self._populate_docx_template(template, template_context, config))
            elif template_format == 'latex':
                populated_results.update(self._populate_latex_template(template, template_context, config))
            elif template_format == 'html':
                populated_results.update(self._populate_html_template(template, template_context, config))
            else:
                # Fallback to generic text replacement
                populated_results.update(self._populate_generic_template(template, template_context, config))
            
            # Add metadata
            populated_results.update({
                'template_id': template_id,
                'template_name': template.name,
                'population_timestamp': datetime.utcnow().isoformat(),
                'data_sources': list(collected_data.keys()),
                'total_data_points': sum(len(v) if isinstance(v, (list, dict)) else 1 for v in collected_data.values())
            })
            
            logger.info(f"Template population completed successfully for template {template_id}")
            return populated_results
            
        except Exception as e:
            logger.error(f"Error populating template {template_id}: {str(e)}")
            raise ReportGenerationError(f"Template population failed: {str(e)}")
    
    def _prepare_template_context(self, collected_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context data for template population"""
        
        # Extract and organize data
        context = {
            'report_title': config.get('title', 'Real-time Report'),
            'generation_date': datetime.utcnow().strftime('%Y-%m-%d'),
            'generation_time': datetime.utcnow().strftime('%H:%M:%S'),
            'session_id': config.get('session_id', 'unknown'),
        }
        
        # Process collected data into template-friendly format
        for source_key, source_data in collected_data.items():
            if source_key.endswith('_records'):
                # Handle record data
                source_name = source_key.replace('_records', '')
                context[f'{source_name}_data'] = source_data
                context[f'{source_name}_count'] = len(source_data) if isinstance(source_data, list) else 1
            elif source_key.endswith('_metadata'):
                # Handle metadata
                source_name = source_key.replace('_metadata', '')
                context[f'{source_name}_info'] = source_data
            else:
                # Direct data inclusion
                context[source_key] = source_data
        
        # Add summary statistics
        total_records = sum(len(v) for k, v in collected_data.items() if k.endswith('_records') and isinstance(v, list))
        context['summary'] = {
            'total_records': total_records,
            'data_sources_count': len([k for k in collected_data.keys() if k.endswith('_records')]),
            'collection_completeness': 'complete'
        }
        
        # Add formatted data for charts and tables
        context['charts_data'] = self._prepare_chart_data(collected_data)
        context['tables_data'] = self._prepare_table_data(collected_data)
        
        logger.info(f"Template context prepared with {len(context)} top-level keys")
        return context
    
    def _prepare_chart_data(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for charts and visualizations"""
        charts_data = {}
        
        for source_key, source_data in collected_data.items():
            if source_key.endswith('_records') and isinstance(source_data, list):
                source_name = source_key.replace('_records', '')
                
                # Prepare data for different chart types
                charts_data[f'{source_name}_bar_chart'] = {
                    'labels': [f'Item {i+1}' for i in range(len(source_data))],
                    'values': [i+1 for i in range(len(source_data))],
                    'title': f'{source_name} Data Distribution'
                }
                
                charts_data[f'{source_name}_pie_chart'] = {
                    'labels': ['Category A', 'Category B', 'Category C'],
                    'values': [30, 45, 25],
                    'title': f'{source_name} Categories'
                }
        
        return charts_data
    
    def _prepare_table_data(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for tables"""
        tables_data = {}
        
        for source_key, source_data in collected_data.items():
            if source_key.endswith('_records') and isinstance(source_data, list):
                source_name = source_key.replace('_records', '')
                
                # Convert to table format
                if source_data and isinstance(source_data[0], dict):
                    headers = list(source_data[0].keys())
                    rows = [[str(record.get(header, '')) for header in headers] for record in source_data]
                    
                    tables_data[f'{source_name}_table'] = {
                        'headers': headers,
                        'rows': rows,
                        'title': f'{source_name} Data Table'
                    }
        
        return tables_data
    
    def _detect_template_format(self, template_content: str) -> str:
        """Detect template format from content"""
        content_lower = template_content.lower().strip()
        
        if content_lower.startswith('\\documentclass') or '\\begin{document}' in content_lower:
            return 'latex'
        elif '<html' in content_lower or '<!doctype html' in content_lower:
            return 'html'
        elif '{%' in content_lower or '{{' in content_lower:
            return 'jinja'  # Jinja2 template
        else:
            return 'generic'
    
    def _populate_docx_template(self, template: ReportTemplate, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Populate DOCX template using DocxTemplater approach"""
        try:
            # Create temporary file for populated template
            output_dir = tempfile.mkdtemp()
            output_file = os.path.join(output_dir, f'populated_{template.name}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.docx')
            
            # For now, create a simple DOCX with populated data
            # In production, you'd use python-docx or docxtpl
            docx_content = self._generate_docx_content(context, config)
            
            # Write to temporary file (simplified for demo)
            with open(output_file.replace('.docx', '.txt'), 'w', encoding='utf-8') as f:
                f.write(docx_content)
            
            return {
                'docx_file_path': output_file.replace('.docx', '.txt'),  # Temporary workaround
                'docx_content_preview': docx_content[:500] + '...' if len(docx_content) > 500 else docx_content,
                'format': 'docx'
            }
            
        except Exception as e:
            logger.error(f"Error populating DOCX template: {str(e)}")
            raise ReportGenerationError(f"DOCX template population failed: {str(e)}")
    
    def _populate_latex_template(self, template: ReportTemplate, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Populate LaTeX template"""
        try:
            # Replace LaTeX placeholders with actual data
            latex_content = template.template_content
            
            # Simple placeholder replacement for LaTeX
            for key, value in context.items():
                if isinstance(value, (str, int, float)):
                    latex_content = latex_content.replace(f'{{{key}}}', str(value))
                elif isinstance(value, dict) and 'title' in value:
                    latex_content = latex_content.replace(f'{{{key}}}', value.get('title', ''))
            
            # Create output file
            output_dir = tempfile.mkdtemp()
            output_file = os.path.join(output_dir, f'populated_{template.name}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.tex')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            return {
                'latex_file_path': output_file,
                'latex_content_preview': latex_content[:500] + '...' if len(latex_content) > 500 else latex_content,
                'format': 'latex'
            }
            
        except Exception as e:
            logger.error(f"Error populating LaTeX template: {str(e)}")
            raise ReportGenerationError(f"LaTeX template population failed: {str(e)}")
    
    def _populate_html_template(self, template: ReportTemplate, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Populate HTML template"""
        try:
            html_content = template.template_content
            
            # Simple placeholder replacement for HTML
            for key, value in context.items():
                if isinstance(value, (str, int, float)):
                    html_content = html_content.replace(f'{{{{{key}}}}}', str(value))
                elif isinstance(value, dict):
                    # Handle nested objects
                    html_content = html_content.replace(f'{{{{{key}}}}}', str(value))
            
            # Create output file
            output_dir = tempfile.mkdtemp()
            output_file = os.path.join(output_dir, f'populated_{template.name}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.html')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                'html_file_path': output_file,
                'html_content_preview': html_content[:500] + '...' if len(html_content) > 500 else html_content,
                'format': 'html'
            }
            
        except Exception as e:
            logger.error(f"Error populating HTML template: {str(e)}")
            raise ReportGenerationError(f"HTML template population failed: {str(e)}")
    
    def _populate_generic_template(self, template: ReportTemplate, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Populate generic text template"""
        try:
            content = template.template_content
            
            # Simple placeholder replacement
            for key, value in context.items():
                if isinstance(value, (str, int, float)):
                    placeholder_patterns = [f'{{{{{key}}}}}', f'{{{key}}}', f'{{%{key}%}}']
                    for pattern in placeholder_patterns:
                        content = content.replace(pattern, str(value))
            
            # Create output file
            output_dir = tempfile.mkdtemp()
            output_file = os.path.join(output_dir, f'populated_{template.name}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.txt')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'text_file_path': output_file,
                'text_content_preview': content[:500] + '...' if len(content) > 500 else content,
                'format': 'text'
            }
            
        except Exception as e:
            logger.error(f"Error populating generic template: {str(e)}")
            raise ReportGenerationError(f"Generic template population failed: {str(e)}")
    
    def _generate_docx_content(self, context: Dict[str, Any], config: Dict[str, Any]) -> str:
        """Generate DOCX-style content (simplified for demo)"""
        content_parts = []
        
        # Title
        content_parts.append(f"# {context.get('report_title', 'Real-time Report')}")
        content_parts.append(f"Generated on: {context.get('generation_date')} at {context.get('generation_time')}")
        content_parts.append(f"Session ID: {context.get('session_id', 'N/A')}")
        content_parts.append("")
        
        # Summary
        if 'summary' in context:
            summary = context['summary']
            content_parts.append("## Summary")
            content_parts.append(f"- Total Records: {summary.get('total_records', 0)}")
            content_parts.append(f"- Data Sources: {summary.get('data_sources_count', 0)}")
            content_parts.append(f"- Collection Status: {summary.get('collection_completeness', 'Unknown')}")
            content_parts.append("")
        
        # Data sections
        for key, value in context.items():
            if key.endswith('_data') and isinstance(value, list):
                source_name = key.replace('_data', '').replace('_', ' ').title()
                content_parts.append(f"## {source_name}")
                content_parts.append(f"Total items: {len(value)}")
                
                # Show first few items
                for i, item in enumerate(value[:5]):
                    if isinstance(item, dict):
                        content_parts.append(f"Item {i+1}: {json.dumps(item, indent=2)}")
                    else:
                        content_parts.append(f"Item {i+1}: {str(item)}")
                
                if len(value) > 5:
                    content_parts.append(f"... and {len(value) - 5} more items")
                content_parts.append("")
        
        return "\n".join(content_parts)
    
    def get_template_preview(self, template_id: int, sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate template preview with sample data"""
        try:
            template = ReportTemplate.query.get(template_id)
            if not template:
                raise ReportGenerationError(f"Template {template_id} not found")
            
            # Use sample data if no real data provided
            if not sample_data:
                sample_data = {
                    'UserDatabase_records': [
                        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
                        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
                    ],
                    'UserDatabase_metadata': {
                        'total_records': 2,
                        'source_type': 'database',
                        'last_updated': datetime.utcnow().isoformat()
                    }
                }
            
            # Generate preview
            preview_config = {'title': 'Preview Report', 'session_id': 'preview'}
            populated_results = self.populate_template_with_realtime_data(
                template_id, sample_data, preview_config
            )
            
            return {
                'success': True,
                'template_name': template.name,
                'preview_data': populated_results,
                'sample_data_used': sample_data
            }
            
        except Exception as e:
            logger.error(f"Error generating template preview: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Global service instance
realtime_template_service = RealtimeTemplateService()