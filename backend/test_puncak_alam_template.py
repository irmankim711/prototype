"""
Test the converted Puncak Alam template with sample data
"""
from docxtpl import DocxTemplate
import os

def test_template():
    """Test the template with sample data"""

    template_path = "templates/04- LAPORAN FU _ PUNCAK ALAM_final.docx"
    output_path = "static/generated/test_puncak_alam_output.docx"

    # Ensure output directory exists
    os.makedirs("static/generated", exist_ok=True)

    print(f"Testing template: {template_path}")
    print(f"Output will be: {output_path}\n")

    # Sample data matching the 8 tags in the template
    sample_data = {
        'NAMA_PESERTA_HADIR': 'Ahmad bin Abdullah',
        'MARKAH_PRE': '85',
        'KAD_PENGENALAN': '990101-01-1234',
        'ALAMAT': 'No. 123, Jalan Puncak Alam, 42300 Selangor',
        'NO_TELEFON': '012-3456789',
        'KEHADIRAH_SABTU': 'Hadir',
        'KEHADIRAN_AHAD': 'Hadir',
        'ALASAN': 'Tiada'
    }

    try:
        # Load template
        print("Loading template...")
        doc = DocxTemplate(template_path)

        # Render with data
        print("Rendering template with sample data...")
        doc.render(sample_data)

        # Save output
        print("Saving output...")
        doc.save(output_path)

        print(f"\n✅ SUCCESS! Report generated successfully!")
        print(f"   Output: {output_path}")
        print(f"\nSample data used:")
        for key, value in sample_data.items():
            print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR during template rendering:")
        print(f"   {type(e).__name__}: {str(e)}")
        print(f"\nThis usually means:")
        print(f"  1. Template tags don't match data keys")
        print(f"  2. Template has syntax errors")
        print(f"  3. Template file is corrupted")

        # Show what tags the template expects
        print(f"\n📋 Template expects these tags:")
        print(f"  {{ NAMA_PESERTA_HADIR }}")
        print(f"  {{ MARKAH_PRE }}")
        print(f"  {{ KAD_PENGENALAN }}")
        print(f"  {{ ALAMAT }}")
        print(f"  {{ NO_TELEFON }}")
        print(f"  {{ KEHADIRAH_SABTU }}")
        print(f"  {{ KEHADIRAN_AHAD }}")
        print(f"  {{ ALASAN }}")

        return False

if __name__ == "__main__":
    success = test_template()
    exit(0 if success else 1)
