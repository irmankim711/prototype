"""
Script to register existing DOCX templates in the database
This ensures templates are visible in the frontend and can be used for report generation
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app import create_app, db
from app.models import TemplateModel as Template
from datetime import datetime

def register_template(name, description, file_path, category='business', template_type='report'):
    """Register a template in the database"""

    # Check if template already exists
    existing = Template.query.filter_by(name=name).first()
    if existing:
        print(f"Template '{name}' already exists (ID: {existing.id})")
        # Update file path if changed
        if existing.file_path != file_path:
            existing.file_path = file_path
            existing.updated_at = datetime.utcnow()
            db.session.commit()
            print(f"  Updated file path to: {file_path}")
        return existing

    # Create new template
    template = Template(
        name=name,
        description=description,
        category=category,
        template_type=template_type,
        file_path=file_path,
        template_content='',  # Empty for file-based templates
        is_active=True,
        supports_excel=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.session.add(template)
    db.session.commit()
    print(f"Registered template '{name}' (ID: {template.id})")
    return template

def main():
    import os

    # Set the database URL to match the running server
    os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/IRMAN/OneDrive/Desktop/prototype/backend/app.db'

    app = create_app()

    with app.app_context():
        print(f"\nUsing database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print("Registering templates from backend/templates directory...")
        print("-" * 60)

        templates_dir = Path(backend_dir) / 'templates'

        # Register the main Puncak Alam template
        puncak_alam_template = templates_dir / '04- LAPORAN FU _ PUNCAK ALAM_final.docx'
        if puncak_alam_template.exists():
            register_template(
                name='Laporan Follow-up Puncak Alam',
                description='Official follow-up report template for Puncak Alam. Includes all standard sections with professional formatting.',
                file_path=str(puncak_alam_template.absolute()),
                category='business',
                template_type='report'
            )
        else:
            print(f"Warning: Template file not found: {puncak_alam_template}")

        # Find and register all DOCX templates recursively
        for docx_file in templates_dir.rglob('*.docx'):
            # Skip temporary files
            if docx_file.name.startswith('~') or docx_file.name.startswith('._'):
                continue

            # Skip if already registered
            if docx_file.name == '04- LAPORAN FU _ PUNCAK ALAM_final.docx':
                continue

            # Create a friendly name from filename
            friendly_name = docx_file.stem.replace('_', ' ').replace('-', ' ').title()

            register_template(
                name=friendly_name,
                description=f'Report template: {friendly_name}',
                file_path=str(docx_file.absolute()),
                category='general',
                template_type='report'
            )

        print("-" * 60)
        print("\nAll templates registered successfully!")

        # List all registered templates
        print("\nRegistered Templates:")
        all_templates = Template.query.filter_by(is_active=True).all()
        for t in all_templates:
            print(f"  - ID: {t.id} | Name: {t.name}")
            print(f"    File: {t.file_path}")
            print(f"    Exists: {os.path.exists(t.file_path) if t.file_path else False}")

if __name__ == '__main__':
    main()
