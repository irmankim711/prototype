"""
Clean up database - keep ONLY the Puncak Alam template
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models.report_models import ReportTemplate

def cleanup_templates():
    """Keep only Puncak Alam template, deactivate all others"""
    app = create_app()

    with app.app_context():
        # Get all templates
        all_templates = ReportTemplate.query.all()

        print(f"Found {len(all_templates)} templates in database")
        print("=" * 60)

        puncak_alam_template = None

        for template in all_templates:
            # Check if this is the Puncak Alam template
            if 'PUNCAK ALAM' in template.name.upper() or 'LAPORAN FU' in template.name.upper():
                print(f"✓ KEEPING: {template.name} (ID: {template.id})")
                template.is_active = True
                puncak_alam_template = template
            else:
                print(f"✗ DEACTIVATING: {template.name} (ID: {template.id})")
                template.is_active = False

        # If no Puncak Alam template, create one
        if not puncak_alam_template:
            print("\n⚠ No Puncak Alam template found. Creating one...")

            template_path = os.path.join(
                os.path.dirname(__file__),
                'templates',
                'report_templates',
                '04- LAPORAN FU _ PUNCAK ALAM (1).docx'
            )

            puncak_alam_template = ReportTemplate(
                name='04- Laporan Fu Puncak Alam Final',
                description='Report template: 04- LAPORAN FU _ PUNCAK ALAM_final',
                category='report',
                template_type='report',
                file_path=template_path,
                supports_excel=True,
                is_active=True,
                created_by=1  # Admin user
            )
            db.session.add(puncak_alam_template)
            print(f"✓ CREATED: {puncak_alam_template.name}")

        # Commit changes
        db.session.commit()

        print("\n" + "=" * 60)
        print("✅ Database cleanup complete!")
        print(f"✅ Active templates: 1 (Puncak Alam)")
        print(f"✅ Template ID: {puncak_alam_template.id}")
        print(f"✅ Template path: {puncak_alam_template.file_path}")

if __name__ == '__main__':
    cleanup_templates()
