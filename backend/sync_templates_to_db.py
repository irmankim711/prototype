#!/usr/bin/env python3
"""
Template Database Synchronization Script

This script syncs filesystem templates to the database, ensuring proper integration
between template files and the ReportTemplate model.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import Flask app and models
from app import create_app, db
from app.models import ReportTemplate

def get_template_info(template_path: Path) -> dict:
    """Extract template information from file"""
    
    # Map template names to proper display info
    template_mappings = {
        'Temp1': {
            'name': 'Standard Business Report',
            'description': 'Professional business report template with clean formatting and data visualization support.',
            'category': 'business',
            'type': 'docx'
        },
        'Temp1_jinja2': {
            'name': 'Dynamic Business Report',
            'description': 'Business report template with Jinja2 templating for dynamic content generation.',
            'category': 'business', 
            'type': 'docx'
        },
        'Temp1_jinja2_excelheaders': {
            'name': 'Excel-Optimized Business Report',
            'description': 'Business report template optimized for Excel data integration with automatic header mapping.',
            'category': 'business',
            'type': 'docx'
        },
        'TestTemplate': {
            'name': 'Test Report Template',
            'description': 'Template for testing report generation functionality with sample data structures.',
            'category': 'testing',
            'type': 'docx'
        },
        'Temp2': {
            'name': 'Scientific/Academic Report',
            'description': 'LaTeX-based template for scientific and academic reports with advanced formatting.',
            'category': 'academic',
            'type': 'tex'
        }
    }
    
    template_stem = template_path.stem
    template_info = template_mappings.get(template_stem, {
        'name': template_stem.replace('_', ' ').title(),
        'description': f'Template file: {template_path.name}',
        'category': 'general',
        'type': template_path.suffix[1:] if template_path.suffix else 'unknown'
    })
    
    # Add file-specific info
    template_info.update({
        'file_path': str(template_path),
        'file_size': template_path.stat().st_size if template_path.exists() else 0,
        'template_identifier': template_stem,  # This will be used for lookups
        'supports_charts': template_info.get('type') in ['docx', 'html'],
        'supports_images': template_info.get('type') in ['docx', 'html'],
        'is_active': True,
        'is_public': True
    })
    
    return template_info

def sync_templates_to_database():
    """Sync filesystem templates to database"""
    
    print("🔄 Starting template synchronization...")
    
    # Get templates directory
    templates_dir = backend_dir / 'templates'
    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return
    
    print(f"📁 Templates directory: {templates_dir}")
    
    # Find all template files
    template_extensions = ['.docx', '.jinja', '.tex', '.html']
    template_files = []
    
    for ext in template_extensions:
        template_files.extend(templates_dir.glob(f'*{ext}'))
    
    print(f"📄 Found {len(template_files)} template files")
    
    synced_count = 0
    updated_count = 0
    
    for template_path in template_files:
        try:
            template_info = get_template_info(template_path)
            template_identifier = template_info['template_identifier']
            
            print(f"📝 Processing: {template_path.name}")
            
            # Check if template already exists in database
            existing_template = ReportTemplate.query.filter_by(name=template_info['name']).first()
            
            if existing_template:
                # Update existing template
                existing_template.description = template_info['description']
                existing_template.file_path = template_info['file_path']
                existing_template.template_type = template_info['type']
                existing_template.category = template_info['category']
                existing_template.supports_charts = template_info['supports_charts']
                existing_template.supports_images = template_info['supports_images']
                existing_template.placeholder_schema = {
                    'file_size': template_info['file_size'],
                    'template_identifier': template_identifier,
                    'original_filename': Path(template_info['file_path']).name
                }
                existing_template.is_active = template_info['is_active']
                existing_template.updated_at = datetime.utcnow()
                
                print(f"   ✅ Updated existing template: {existing_template.name} (ID: {existing_template.id})")
                updated_count += 1
                
            else:
                # Create new template
                new_template = ReportTemplate(
                    name=template_info['name'],
                    description=template_info['description'],
                    template_type=template_info['type'],  # Required field
                    file_path=template_info['file_path'],
                    category=template_info['category'],
                    supports_charts=template_info['supports_charts'],
                    supports_images=template_info['supports_images'],
                    placeholder_schema={
                        'file_size': template_info['file_size'],
                        'template_identifier': template_identifier,
                        'original_filename': Path(template_info['file_path']).name
                    },
                    is_active=template_info['is_active'],
                    created_at=datetime.utcnow(),
                    created_by='system'  # Add required field
                )
                
                db.session.add(new_template)
                db.session.flush()  # Get ID without committing
                
                print(f"   ➕ Created new template: {new_template.name} (ID: {new_template.id})")
                synced_count += 1
                
        except Exception as e:
            print(f"   ❌ Error processing {template_path.name}: {str(e)}")
            continue
    
    # Commit all changes
    try:
        db.session.commit()
        print(f"✅ Successfully synced templates!")
        print(f"   📊 New templates: {synced_count}")
        print(f"   🔄 Updated templates: {updated_count}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving to database: {str(e)}")
    
    # List all templates in database
    print("\n📋 Templates now in database:")
    templates = ReportTemplate.query.all()
    for template in templates:
        placeholder_schema = template.placeholder_schema or {}
        template_id = placeholder_schema.get('template_identifier', 'N/A')
        print(f"   • ID {template.id}: {template.name} (identifier: {template_id})")

def main():
    """Main function"""
    print("🚀 Template Database Synchronization")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Sync templates
        sync_templates_to_database()
    
    print("\n✅ Synchronization complete!")

if __name__ == '__main__':
    main()