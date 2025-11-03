"""
Template Service for Template-Based Report Generation
Extends existing template functionality with CRUD operations and validation
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy import and_, or_
from flask import current_app

from ..models import TemplateModel as Template
from ..models.template_models import ReportStatus
from .. import db

logger = logging.getLogger(__name__)

class TemplateService:
    """Service for managing report templates with CRUD operations"""
    
    def __init__(self):
        self._templates_path = None
        logger.info("Template service initialized")
    
    @property
    def templates_path(self):
        """Lazy initialization of templates path within app context"""
        if self._templates_path is None:
            from flask import current_app
            self._templates_path = Path(current_app.root_path).parent / 'templates'
        return self._templates_path
    
    def get_templates(self, user_id: int = None, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get all active templates with optional filtering

        Args:
            user_id: User ID for permission filtering
            filters: Dictionary of filters (category, template_type, search)

        Returns:
            List of template dictionaries
        """
        try:
            query = Template.query.filter_by(is_active=True)

            # Apply filters
            if filters:
                if filters.get('category'):
                    query = query.filter(Template.category == filters['category'])

                if filters.get('template_type'):
                    query = query.filter(Template.template_type == filters['template_type'])

                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            Template.name.ilike(search_term),
                            Template.description.ilike(search_term)
                        )
                    )

                if filters.get('supports_excel') is not None:
                    query = query.filter(Template.supports_excel == filters['supports_excel'])

            # Order by name
            templates = query.order_by(Template.name).all()

            # Convert to dictionaries and add metadata
            result = []
            for template in templates:
                template_dict = template.to_dict()

                # Add usage statistics
                template_dict['usage_count'] = self._get_template_usage_count(template.id)
                template_dict['last_used'] = self._get_template_last_used(template.id)

                # Add file information if file-based
                if template.file_path and os.path.exists(template.file_path):
                    file_stat = os.stat(template.file_path)
                    template_dict['file_size'] = file_stat.st_size
                    template_dict['file_modified'] = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

                result.append(template_dict)

            # If no templates in database, scan file system
            if not result:
                logger.info("No templates in database, scanning file system")
                result = self._scan_file_based_templates()

            logger.info(f"Retrieved {len(result)} templates with filters: {filters}")
            return result

        except Exception as e:
            logger.error(f"Error retrieving templates: {e}")
            return []
    
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by ID
        
        Args:
            template_id: Template ID
            
        Returns:
            Template dictionary or None if not found
        """
        try:
            template = Template.query.filter_by(id=template_id, is_active=True).first()
            
            if not template:
                logger.warning(f"Template {template_id} not found")
                return None
            
            template_dict = template.to_dict()
            
            # Add detailed metadata
            template_dict['usage_count'] = self._get_template_usage_count(template.id)
            template_dict['last_used'] = self._get_template_last_used(template.id)
            template_dict['variables_count'] = len(template.variables or [])
            template_dict['required_fields_count'] = len(template.required_fields or [])
            
            # Add template content preview (first 500 chars)
            if template.template_content:
                template_dict['content_preview'] = template.template_content[:500]
            
            logger.info(f"Retrieved template {template_id}")
            return template_dict
            
        except Exception as e:
            logger.error(f"Error retrieving template {template_id}: {e}")
            return None
    
    def create_template(self, template_data: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
        """
        Create a new template
        
        Args:
            template_data: Template data dictionary
            user_id: User ID creating the template
            
        Returns:
            Created template dictionary or None if failed
        """
        try:
            # Validate required fields
            required_fields = ['name', 'template_content']
            for field in required_fields:
                if not template_data.get(field):
                    raise ValueError(f"Missing required field: {field}")
            
            # Create new template
            template = Template(
                name=template_data['name'],
                description=template_data.get('description', ''),
                category=template_data.get('category', 'general'),
                template_content=template_data['template_content'],
                variables=template_data.get('variables', []),
                template_type=template_data.get('template_type', 'report'),
                supports_excel=template_data.get('supports_excel', True),
                required_fields=template_data.get('required_fields', []),
                created_by=user_id
            )
            
            # Extract variables from template content if not provided
            if not template.variables:
                template.variables = self._extract_template_variables(template.template_content)
            
            db.session.add(template)
            db.session.commit()
            
            logger.info(f"Created template {template.id} by user {user_id}")
            return template.to_dict()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating template: {e}")
            return None
    
    def update_template(self, template_id: int, updates: Dict[str, Any], user_id: int) -> Optional[Dict[str, Any]]:
        """
        Update an existing template
        
        Args:
            template_id: Template ID to update
            updates: Dictionary of fields to update
            user_id: User ID making the update
            
        Returns:
            Updated template dictionary or None if failed
        """
        try:
            template = Template.query.filter_by(id=template_id, is_active=True).first()
            
            if not template:
                logger.warning(f"Template {template_id} not found for update")
                return None
            
            # Update allowed fields
            allowed_fields = [
                'name', 'description', 'category', 'template_content', 
                'variables', 'template_type', 'supports_excel', 'required_fields'
            ]
            
            for field in allowed_fields:
                if field in updates:
                    setattr(template, field, updates[field])
            
            # Re-extract variables if template content changed
            if 'template_content' in updates and not updates.get('variables'):
                template.variables = self._extract_template_variables(template.template_content)
            
            template.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Updated template {template_id} by user {user_id}")
            return template.to_dict()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating template {template_id}: {e}")
            return None
    
    def delete_template(self, template_id: int, user_id: int) -> bool:
        """
        Soft delete a template (mark as inactive)
        
        Args:
            template_id: Template ID to delete
            user_id: User ID making the deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template = Template.query.filter_by(id=template_id, is_active=True).first()
            
            if not template:
                logger.warning(f"Template {template_id} not found for deletion")
                return False
            
            # Check if template is in use
            from .report_generation_service import ReportGenerationService
            if ReportGenerationService.is_template_in_use(template_id):
                logger.warning(f"Cannot delete template {template_id} - it is in use")
                return False
            
            # Soft delete
            template.is_active = False
            template.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Deleted template {template_id} by user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting template {template_id}: {e}")
            return False
    
    def validate_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate template structure and content
        
        Args:
            template_data: Template data to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            # Check required fields
            required_fields = ['name', 'template_content']
            for field in required_fields:
                if not template_data.get(field):
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['valid'] = False
            
            # Validate template content
            template_content = template_data.get('template_content', '')
            if template_content:
                content_validation = self._validate_template_content(template_content)
                validation_result['errors'].extend(content_validation.get('errors', []))
                validation_result['warnings'].extend(content_validation.get('warnings', []))
                validation_result['suggestions'].extend(content_validation.get('suggestions', []))
                
                if content_validation.get('errors'):
                    validation_result['valid'] = False
            
            # Validate variables
            variables = template_data.get('variables', [])
            if variables:
                var_validation = self._validate_template_variables(variables)
                validation_result['warnings'].extend(var_validation.get('warnings', []))
                validation_result['suggestions'].extend(var_validation.get('suggestions', []))
            
            logger.info(f"Template validation completed - Valid: {validation_result['valid']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating template: {e}")
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def get_template_variables(self, template_id: int) -> List[Dict[str, Any]]:
        """
        Get template variables with metadata
        
        Args:
            template_id: Template ID
            
        Returns:
            List of template variables
        """
        try:
            template = Template.query.filter_by(id=template_id, is_active=True).first()
            
            if not template:
                logger.warning(f"Template {template_id} not found")
                return []
            
            variables = template.variables or []
            
            # Enhance variables with metadata
            enhanced_variables = []
            for var in variables:
                if isinstance(var, dict):
                    enhanced_variables.append(var)
                else:
                    # Convert string variables to dict format
                    enhanced_variables.append({
                        'name': var,
                        'type': 'string',
                        'required': False,
                        'description': f'Variable: {var}'
                    })
            
            logger.info(f"Retrieved {len(enhanced_variables)} variables for template {template_id}")
            return enhanced_variables
            
        except Exception as e:
            logger.error(f"Error retrieving template variables: {e}")
            return []
    
    def generate_template_preview(self, template_id: int, sample_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a preview of the template with sample data
        
        Args:
            template_id: Template ID
            sample_data: Sample data for preview
            
        Returns:
            Preview result dictionary
        """
        try:
            template = Template.query.filter_by(id=template_id, is_active=True).first()
            
            if not template:
                return {'error': 'Template not found'}
            
            # Use provided sample data or generate default
            if not sample_data:
                sample_data = self._generate_sample_data(template.variables or [])
            
            # Render template with sample data
            from jinja2 import Template as Jinja2Template
            jinja_template = Jinja2Template(template.template_content)
            rendered_content = jinja_template.render(**sample_data)
            
            return {
                'success': True,
                'template_id': template_id,
                'rendered_content': rendered_content,
                'sample_data': sample_data
            }
            
        except Exception as e:
            logger.error(f"Error generating template preview: {e}")
            return {'error': str(e)}
    
    def _get_template_usage_count(self, template_id: int) -> int:
        """Get usage count for a template"""
        try:
            from ..models.template_models import GeneratedReport
            return GeneratedReport.query.filter_by(template_id=template_id).count()
        except:
            return 0
    
    def _get_template_last_used(self, template_id: int) -> Optional[str]:
        """Get last used date for a template"""
        try:
            from ..models.template_models import GeneratedReport
            last_report = GeneratedReport.query.filter_by(template_id=template_id)\
                .order_by(GeneratedReport.created_at.desc()).first()
            return last_report.created_at.isoformat() if last_report else None
        except:
            return None
    
    def _extract_template_variables(self, template_content: str) -> List[Dict[str, Any]]:
        """Extract variables from template content"""
        import re
        
        # Find Jinja2 variables
        variable_pattern = r'\{\{\s*([^}]+)\s*\}\}'
        matches = re.findall(variable_pattern, template_content)
        
        variables = []
        seen_vars = set()
        
        for match in matches:
            # Clean up variable name
            var_name = match.strip().split('|')[0].split('.')[0]  # Remove filters and attributes
            
            if var_name not in seen_vars and not var_name.startswith('_'):
                variables.append({
                    'name': var_name,
                    'type': 'string',
                    'required': False,
                    'description': f'Template variable: {var_name}'
                })
                seen_vars.add(var_name)
        
        return variables
    
    def _validate_template_content(self, template_content: str) -> Dict[str, List[str]]:
        """Validate template content syntax"""
        result = {'errors': [], 'warnings': [], 'suggestions': []}
        
        try:
            from jinja2 import Template as Jinja2Template, TemplateSyntaxError
            
            # Try to parse template
            Jinja2Template(template_content)
            
            # Check for common issues
            if '{{' not in template_content:
                result['warnings'].append('Template contains no variables')
            
            # Check for unescaped HTML if it looks like HTML
            if '<' in template_content and '>' in template_content:
                if '|safe' not in template_content and '|e' not in template_content:
                    result['suggestions'].append('Consider using |safe filter for HTML content')
            
        except TemplateSyntaxError as e:
            result['errors'].append(f'Template syntax error: {str(e)}')
        except Exception as e:
            result['errors'].append(f'Template validation error: {str(e)}')
        
        return result
    
    def _validate_template_variables(self, variables: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Validate template variables"""
        result = {'warnings': [], 'suggestions': []}
        
        if not variables:
            result['warnings'].append('No variables defined for template')
            return result
        
        # Check for required variables without defaults
        required_vars = [v for v in variables if v.get('required', False)]
        if not required_vars:
            result['suggestions'].append('Consider marking some variables as required')
        
        return result
    
    def _generate_sample_data(self, variables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate sample data for template preview"""
        sample_data = {}
        
        for var in variables:
            var_name = var.get('name', '')
            var_type = var.get('type', 'string')
            
            if var_type == 'string':
                sample_data[var_name] = f'Sample {var_name}'
            elif var_type == 'number':
                sample_data[var_name] = 42
            elif var_type == 'date':
                sample_data[var_name] = datetime.now().strftime('%Y-%m-%d')
            elif var_type == 'boolean':
                sample_data[var_name] = True
            elif var_type == 'list':
                sample_data[var_name] = [f'Item 1', f'Item 2', f'Item 3']
            else:
                sample_data[var_name] = f'Sample {var_name}'
        
        # Add common template variables
        sample_data.update({
            'title': 'Sample Report Title',
            'date': datetime.now().strftime('%Y-%m-%d'),
            'author': 'Sample Author',
            'company': 'Sample Company'
        })

        return sample_data

    def _scan_file_based_templates(self) -> List[Dict[str, Any]]:
        """
        Scan the templates directory for file-based templates
        Returns a list of template dictionaries
        """
        templates = []

        try:
            # Check both main templates directory and report_templates subdirectory
            template_dirs = [
                self.templates_path,
                self.templates_path / 'report_templates'
            ]

            for templates_dir in template_dirs:
                if not templates_dir.exists():
                    continue

                logger.info(f"Scanning template directory: {templates_dir}")

                # Scan for .docx files
                for template_file in templates_dir.rglob('*.docx'):
                    # Skip temporary files
                    if template_file.name.startswith('~'):
                        continue

                    try:
                        template_info = {
                            'id': template_file.stem,
                            'name': template_file.stem.replace('_', ' ').title(),
                            'description': f'Word document template: {template_file.name}',
                            'template_type': 'docx',
                            'category': 'general',
                            'created_at': datetime.fromtimestamp(template_file.stat().st_ctime).isoformat(),
                            'updated_at': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat(),
                            'file_path': str(template_file),
                            'file_size': template_file.stat().st_size,
                            'is_active': True,
                            'supports_excel': True
                        }
                        templates.append(template_info)
                        logger.info(f"Found template: {template_info['name']}")
                    except Exception as e:
                        logger.error(f"Error processing template file {template_file}: {e}")

                # Scan for .tex files
                for template_file in templates_dir.rglob('*.tex'):
                    if template_file.name.startswith('~'):
                        continue

                    try:
                        with open(template_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except (IOError, UnicodeDecodeError) as e:
                        logger.warning(f"Could not read template file {template_file}: {str(e)}")
                        content = ''

                    template_info = {
                        'id': template_file.stem,
                        'name': template_file.stem.replace('_', ' ').title(),
                        'description': f'LaTeX template: {template_file.name}',
                        'template_type': 'latex',
                        'category': 'general',
                        'template_content': content,
                        'created_at': datetime.fromtimestamp(template_file.stat().st_ctime).isoformat(),
                        'updated_at': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat(),
                        'file_path': str(template_file),
                        'file_size': template_file.stat().st_size,
                        'is_active': True,
                        'supports_excel': True
                    }
                    templates.append(template_info)

                # Scan for .jinja files
                for template_file in templates_dir.rglob('*.jinja*'):
                    if template_file.name.startswith('~'):
                        continue

                    try:
                        with open(template_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except (IOError, UnicodeDecodeError) as e:
                        logger.warning(f"Could not read template file {template_file}: {str(e)}")
                        content = ''

                    template_info = {
                        'id': template_file.stem,
                        'name': template_file.stem.replace('_', ' ').title(),
                        'description': f'Jinja2 template: {template_file.name}',
                        'template_type': 'jinja2',
                        'category': 'general',
                        'template_content': content,
                        'created_at': datetime.fromtimestamp(template_file.stat().st_ctime).isoformat(),
                        'updated_at': datetime.fromtimestamp(template_file.stat().st_mtime).isoformat(),
                        'file_path': str(template_file),
                        'file_size': template_file.stat().st_size,
                        'is_active': True,
                        'supports_excel': True
                    }
                    templates.append(template_info)

            logger.info(f"Found {len(templates)} file-based templates")
            return templates

        except Exception as e:
            logger.error(f"Error scanning file-based templates: {e}")
            return []

# Global service instance
template_service = TemplateService()