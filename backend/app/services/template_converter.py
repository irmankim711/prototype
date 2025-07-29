"""
Template conversion utilities for handling different templating syntaxes
"""
import re
import logging

logger = logging.getLogger(__name__)

class TemplateConverter:
    """
    Converts between different template syntaxes
    """
    
    @staticmethod
    def mustache_to_jinja2(template_content):
        """
        Convert Mustache-style syntax to Jinja2 syntax
        
        Converts:
        - {{#section}} ... {{/section}} to {% for item in section %} ... {% endfor %}
        - {{variable}} to {{ variable }} (already compatible)
        - {{#if condition}} ... {{/if}} to {% if condition %} ... {% endif %}
        """
        logger.info("Converting Mustache template to Jinja2")
        
        converted = template_content
        
        # Pattern for section loops: {{#section}} ... {{/section}}
        section_pattern = r'\{\{#([^}]+)\}\}(.*?)\{\{/\1\}\}'
        
        def replace_section(match):
            section_name = match.group(1).strip()
            content = match.group(2)
            
            # Handle nested sections like tentative.day1
            if '.' in section_name:
                parts = section_name.split('.')
                base_name = parts[0]
                nested_key = parts[1]
                # For nested sections, iterate over the nested array
                return f'{{% for item in {base_name}.{nested_key} %}}{content}{{% endfor %}}'
            else:
                # For simple sections, iterate over the array
                return f'{{% for item in {section_name} %}}{content}{{% endfor %}}'
        
        # Replace all section patterns (handle nested patterns)
        while re.search(section_pattern, converted, re.DOTALL):
            converted = re.sub(section_pattern, replace_section, converted, flags=re.DOTALL)
        
        # Pattern for conditional sections: {{#if condition}} ... {{/if}}
        if_pattern = r'\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}'
        
        def replace_if(match):
            condition = match.group(1).strip()
            content = match.group(2)
            return f'{{% if {condition} %}}{content}{{% endif %}}'
        
        converted = re.sub(if_pattern, replace_if, converted, flags=re.DOTALL)
        
        # Handle variable references within loops
        # Convert {{item.property}} to {{ item.property }}
        # This is already compatible with Jinja2, but ensure proper spacing
        var_pattern = r'\{\{([^#/][^}]*)\}\}'
        
        def replace_var(match):
            var_name = match.group(1).strip()
            # Check if it's a loop variable reference
            if var_name.startswith('item.') or var_name in ['item']:
                return f'{{{{ {var_name} }}}}'
            else:
                # Handle nested object access
                return f'{{{{ {var_name} }}}}'
        
        converted = re.sub(var_pattern, replace_var, converted)
        
        logger.info("Template conversion completed")
        return converted
    
    @staticmethod
    def prepare_context_for_mustache_conversion(context):
        """
        Prepare context data structure for converted Mustache templates
        """
        if not isinstance(context, dict):
            return context
        
        prepared = {}
        
        for key, value in context.items():
            if isinstance(value, list) and len(value) > 0:
                # For arrays, ensure each item has access to its properties
                prepared[key] = value
            elif isinstance(value, dict):
                # For nested objects, preserve structure
                prepared[key] = value
            else:
                # For simple values, keep as is
                prepared[key] = value
        
        return prepared
    
    @staticmethod
    def generate_safe_context_from_template(template_content):
        """
        Generate a comprehensive safe context based on placeholders found in template
        """
        placeholders = set()
        
        # Extract all placeholder patterns
        patterns = [
            r'\{\{([^#/][^}]*)\}\}',  # Simple variables
            r'\{%\s*for\s+\w+\s+in\s+([^%}]+)\s*%\}',  # Jinja2 for loops
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, template_content)
            for match in matches:
                placeholders.add(match.strip())
        
        safe_context = {}
        
        for placeholder in placeholders:
            parts = placeholder.split('.')
            current = safe_context
            
            for i, part in enumerate(parts):
                if part not in current:
                    # If this is the last part and it's a number, create a dict with numbered keys
                    if i == len(parts) - 1 and part.isdigit():
                        # This is a numbered field like evaluation.tools.lcd.1
                        # The parent should be a dict with numbered keys
                        parent_key = parts[i-1] if i > 0 else part
                        if parent_key not in current:
                            current[parent_key] = {}
                        if not isinstance(current[parent_key], dict):
                            current[parent_key] = {}
                        current[parent_key][part] = '0'
                    elif i == len(parts) - 1:
                        # This is a final value
                        current[part] = ''
                    else:
                        # This is an intermediate object
                        current[part] = {}
                
                if i < len(parts) - 1:
                    current = current[part]
        
        # Add common base structures that templates often need
        base_context = {
            'program': {
                'title': 'SAMPLE PROGRAM',
                'date': '01/01/2025',
                'time': '9:00 AM - 5:00 PM',
                'location': 'SAMPLE LOCATION',
                'organizer': 'SAMPLE ORGANIZER',
                'speaker': 'SAMPLE SPEAKER',
                'trainer': 'SAMPLE TRAINER',
                'facilitator': 'SAMPLE FACILITATOR',
                'male_participants': '0',
                'female_participants': '0',
                'total_participants': '0',
                'background': 'SAMPLE BACKGROUND',
                'objectives': 'SAMPLE OBJECTIVES'
            },
            'participants': [],
            'tentative': {'day1': [], 'day2': []},
            'attendance': {'total_attended': '0', 'total_absent': '0'},
            'suggestions': {'consultant': [], 'participants': []},
            'signature': {
                'consultant': {'name': 'CONSULTANT NAME'},
                'executive': {'name': 'EXECUTIVE NAME'},
                'head': {'name': 'HEAD NAME'}
            },
            'images': []
        }
        
        # Merge generated context with base context
        def deep_merge(base, generated):
            for key, value in generated.items():
                if key in base:
                    if isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    # If base has a value and generated has a different type, keep base
                else:
                    base[key] = value
            return base
        
        return deep_merge(base_context, safe_context)
    
    @staticmethod
    def analyze_template_syntax(template_content):
        """
        Analyze template to determine its syntax type
        """
        mustache_patterns = [
            r'\{\{#[^}]+\}\}',  # {{#section}}
            r'\{\{/[^}]+\}\}',  # {{/section}}
            r'\{\{#if\s+[^}]+\}\}',  # {{#if condition}}
        ]
        
        jinja2_patterns = [
            r'\{%\s*for\s+',  # {% for
            r'\{%\s*if\s+',   # {% if
            r'\{%\s*endif\s*%\}',  # {% endif %}
            r'\{%\s*endfor\s*%\}',  # {% endfor %}
        ]
        
        mustache_count = sum(len(re.findall(pattern, template_content)) for pattern in mustache_patterns)
        jinja2_count = sum(len(re.findall(pattern, template_content)) for pattern in jinja2_patterns)
        
        if mustache_count > 0 and jinja2_count == 0:
            return 'mustache'
        elif jinja2_count > 0 and mustache_count == 0:
            return 'jinja2'
        elif mustache_count > 0 and jinja2_count > 0:
            return 'mixed'
        else:
            return 'simple'  # Just variable substitution
        """
        Analyze template to determine its syntax type
        """
        mustache_patterns = [
            r'\{\{#[^}]+\}\}',  # {{#section}}
            r'\{\{/[^}]+\}\}',  # {{/section}}
            r'\{\{#if\s+[^}]+\}\}',  # {{#if condition}}
        ]
        
        jinja2_patterns = [
            r'\{%\s*for\s+',  # {% for
            r'\{%\s*if\s+',   # {% if
            r'\{%\s*endif\s*%\}',  # {% endif %}
            r'\{%\s*endfor\s*%\}',  # {% endfor %}
        ]
        
        mustache_count = sum(len(re.findall(pattern, template_content)) for pattern in mustache_patterns)
        jinja2_count = sum(len(re.findall(pattern, template_content)) for pattern in jinja2_patterns)
        
        if mustache_count > 0 and jinja2_count == 0:
            return 'mustache'
        elif jinja2_count > 0 and mustache_count == 0:
            return 'jinja2'
        elif mustache_count > 0 and jinja2_count > 0:
            return 'mixed'
        else:
            return 'simple'  # Just variable substitution
