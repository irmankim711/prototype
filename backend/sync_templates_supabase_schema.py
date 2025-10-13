#!/usr/bin/env python3
"""
Template synchronization using actual Supabase schema
Matches the real table structure found in production
"""

import os
import psycopg2
import json
from pathlib import Path
from datetime import datetime
import uuid

DATABASE_URL = "postgresql://postgres.kprvqvugkggcpqwsisnz:0BQRPIQzMcqQAM43@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

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
        'template_identifier': template_stem
    })
    
    return template_info

def read_template_content(template_path: Path) -> str:
    """Read template content for storage"""
    try:
        if template_path.suffix.lower() == '.docx':
            # For DOCX, we'll store a reference/placeholder
            return f"DOCX Template: {template_path.name}"
        else:
            # For text-based templates, read the actual content
            with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Limit content size to prevent issues
                if len(content) > 10000:
                    content = content[:10000] + "\n... [Content truncated]"
                return content
    except Exception as e:
        return f"Error reading template: {str(e)}"

def sync_templates_to_supabase():
    """Sync filesystem templates to Supabase using correct schema"""
    
    print("🔄 Starting template synchronization to Supabase (correct schema)...")
    
    # Get templates directory
    backend_dir = Path(__file__).parent
    templates_dir = backend_dir / 'templates'
    
    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return False
    
    print(f"📁 Templates directory: {templates_dir}")
    
    # Find all template files
    template_extensions = ['.docx', '.jinja', '.tex', '.html']
    template_files = []
    
    for ext in template_extensions:
        template_files.extend(templates_dir.glob(f'*{ext}'))
    
    print(f"📄 Found {len(template_files)} template files")
    
    # Connect to Supabase
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        print("✅ Connected to Supabase database")
        
        synced_count = 0
        updated_count = 0
        
        for template_path in template_files:
            try:
                template_info = get_template_info(template_path)
                template_identifier = template_info['template_identifier']
                
                print(f"📝 Processing: {template_path.name}")
                
                # Check if template already exists by name
                cursor.execute("""
                    SELECT id, name FROM report_templates 
                    WHERE name = %s;
                """, (template_info['name'],))
                
                existing = cursor.fetchone()
                
                # Read template content
                content_template = read_template_content(template_path)
                
                # Prepare data matching Supabase schema
                template_data = {
                    'name': template_info['name'],
                    'description': template_info['description'],
                    'template_type': template_info['type'],
                    'content_template': content_template,
                    'parameters': {
                        'file_path': template_info['file_path'],
                        'file_size': template_info['file_size'],
                        'template_identifier': template_identifier,
                        'original_filename': template_path.name
                    },
                    'data_sources': ['excel', 'form_data'],
                    'styling': {
                        'category': template_info['category'],
                        'supports_charts': template_info['type'] in ['docx', 'html'],
                        'supports_images': template_info['type'] in ['docx', 'html']
                    },
                    'tags': [template_info['category'], template_info['type'], template_identifier],
                    'is_public': True,
                    'usage_count': 0
                }
                
                if existing:
                    # Update existing template
                    cursor.execute("""
                        UPDATE report_templates SET
                            description = %s,
                            template_type = %s,
                            content_template = %s,
                            parameters = %s,
                            data_sources = %s,
                            styling = %s,
                            tags = %s,
                            is_public = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s;
                    """, (
                        template_data['description'],
                        template_data['template_type'],
                        template_data['content_template'],
                        json.dumps(template_data['parameters']),
                        json.dumps(template_data['data_sources']),
                        json.dumps(template_data['styling']),
                        template_data['tags'],
                        template_data['is_public'],
                        existing[0]
                    ))
                    
                    print(f"   ✅ Updated existing template: {existing[1]} (ID: {existing[0]})")
                    updated_count += 1
                    
                else:
                    # Create new template
                    cursor.execute("""
                        INSERT INTO report_templates (
                            name, description, template_type, content_template,
                            parameters, data_sources, styling, tags, is_public, usage_count
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id;
                    """, (
                        template_data['name'],
                        template_data['description'],
                        template_data['template_type'],
                        template_data['content_template'],
                        json.dumps(template_data['parameters']),
                        json.dumps(template_data['data_sources']),
                        json.dumps(template_data['styling']),
                        template_data['tags'],
                        template_data['is_public'],
                        template_data['usage_count']
                    ))
                    
                    new_id = cursor.fetchone()[0]
                    print(f"   ➕ Created new template: {template_info['name']} (ID: {new_id})")
                    synced_count += 1
                    
                # Commit after each template
                conn.commit()
                
            except Exception as e:
                print(f"   ❌ Error processing {template_path.name}: {str(e)}")
                conn.rollback()
                continue
        
        # List all templates in database
        cursor.execute("""
            SELECT id, name, (parameters->>'template_identifier') as identifier, template_type
            FROM report_templates 
            ORDER BY created_at;
        """)
        
        templates = cursor.fetchall()
        
        print(f"\n✅ Successfully synced templates to Supabase!")
        print(f"   📊 New templates: {synced_count}")
        print(f"   🔄 Updated templates: {updated_count}")
        print(f"\n📋 Templates now in Supabase database ({len(templates)}):")
        
        for template in templates:
            template_id, name, identifier, template_type = template
            print(f"   • {name} ({template_type})")
            print(f"     ID: {template_id}")
            print(f"     Identifier: {identifier or 'N/A'}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Template Synchronization to Supabase (Production Schema)")
    print("=" * 65)
    
    success = sync_templates_to_supabase()
    
    if success:
        print("\n✅ Synchronization complete!")
        print("💡 Templates are now available in your Supabase database.")
        print("💡 NextGen report builder should now work with database templates.")
        print("\n🔧 Next steps:")
        print("   1. Update NextGen report builder to use Supabase schema")
        print("   2. Test report generation with 'Temp1' template")
    else:
        print("\n❌ Synchronization failed!")

if __name__ == '__main__':
    main()