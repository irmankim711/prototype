#!/usr/bin/env python3
"""
Direct template synchronization to Supabase
Bypasses Flask app initialization to avoid complex config issues
"""

import os
import psycopg2
from pathlib import Path
from datetime import datetime

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
        'template_identifier': template_stem,
        'supports_charts': template_info.get('type') in ['docx', 'html'],
        'supports_images': template_info.get('type') in ['docx', 'html'],
        'is_active': True
    })
    
    return template_info

def sync_templates_to_supabase():
    """Sync filesystem templates directly to Supabase"""
    
    print("🔄 Starting direct template synchronization to Supabase...")
    
    # Get templates directory
    backend_dir = Path(__file__).parent
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
                
                # Check if template already exists
                cursor.execute("""
                    SELECT id, name FROM report_templates 
                    WHERE name = %s OR (placeholder_schema->>'template_identifier') = %s;
                """, (template_info['name'], template_identifier))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing template
                    cursor.execute("""
                        UPDATE report_templates SET
                            description = %s,
                            template_type = %s,
                            file_path = %s,
                            category = %s,
                            supports_charts = %s,
                            supports_images = %s,
                            placeholder_schema = %s,
                            is_active = %s,
                            updated_at = %s
                        WHERE id = %s;
                    """, (
                        template_info['description'],
                        template_info['type'],
                        template_info['file_path'],
                        template_info['category'],
                        template_info['supports_charts'],
                        template_info['supports_images'],
                        {
                            'file_size': template_info['file_size'],
                            'template_identifier': template_identifier,
                            'original_filename': template_path.name
                        },
                        template_info['is_active'],
                        datetime.utcnow(),
                        existing[0]
                    ))
                    
                    print(f"   ✅ Updated existing template: {existing[1]} (ID: {existing[0]})")
                    updated_count += 1
                    
                else:
                    # Create new template
                    cursor.execute("""
                        INSERT INTO report_templates (
                            name, description, template_type, file_path, category,
                            supports_charts, supports_images, placeholder_schema, 
                            is_active, created_at, created_by, version
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id;
                    """, (
                        template_info['name'],
                        template_info['description'],
                        template_info['type'],
                        template_info['file_path'],
                        template_info['category'],
                        template_info['supports_charts'],
                        template_info['supports_images'],
                        {
                            'file_size': template_info['file_size'],
                            'template_identifier': template_identifier,
                            'original_filename': template_path.name
                        },
                        template_info['is_active'],
                        datetime.utcnow(),
                        'system',
                        '1.0'
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
            SELECT id, name, (placeholder_schema->>'template_identifier') as identifier
            FROM report_templates 
            ORDER BY id;
        """)
        
        templates = cursor.fetchall()
        
        print(f"\n✅ Successfully synced templates!")
        print(f"   📊 New templates: {synced_count}")
        print(f"   🔄 Updated templates: {updated_count}")
        print(f"\n📋 Templates now in Supabase database:")
        
        for template in templates:
            print(f"   • ID {template[0]}: {template[1]} (identifier: {template[2] or 'N/A'})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False
        
    return True

def main():
    """Main function"""
    print("🚀 Direct Template Database Synchronization to Supabase")
    print("=" * 60)
    
    success = sync_templates_to_supabase()
    
    if success:
        print("\n✅ Synchronization complete!")
        print("💡 Templates are now available in your Supabase database.")
        print("💡 NextGen report builder will now use database templates.")
    else:
        print("\n❌ Synchronization failed!")

if __name__ == '__main__':
    main()