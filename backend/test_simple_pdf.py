"""
Simple PDF Generation Test
Tests ReportLab directly without importing the full app
"""

import os
import tempfile
from datetime import datetime

def test_reportlab_installation():
    """Test if ReportLab is properly installed"""
    print("Testing ReportLab installation...")
    
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        print("✅ ReportLab imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ ReportLab import failed: {e}")
        return False

def test_simple_pdf():
    """Create a simple PDF to test functionality"""
    print("Testing simple PDF creation...")
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Add title
        title = Paragraph("Test PDF Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Add description
        description = Paragraph("This is a test PDF generated using ReportLab.", styles['Normal'])
        story.append(description)
        story.append(Spacer(1, 20))
        
        # Add table
        data = [
            ['Name', 'Age', 'City'],
            ['John Doe', '30', 'New York'],
            ['Jane Smith', '25', 'Los Angeles'],
            ['Bob Johnson', '35', 'Chicago']
        ]
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        
        # Check if file was created
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ Simple PDF created successfully!")
            print(f"   File: {pdf_path}")
            print(f"   Size: {file_size} bytes")
            
            # Clean up
            os.remove(pdf_path)
            return True
        else:
            print("❌ PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error creating simple PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_pdf():
    """Test advanced PDF features"""
    print("Testing advanced PDF features...")
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.lib.enums import TA_CENTER
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E4057')
        )
        
        title = Paragraph("Advanced PDF Report", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Statistics table
        stats_data = [
            ['Metric', 'Value'],
            ['Total Records', '150'],
            ['Success Rate', '95.5%'],
            ['Average Time', '2.3 minutes'],
            ['Satisfaction', '4.8/5']
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A90A4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(stats_table)
        
        doc.build(story)
        
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✅ Advanced PDF created successfully!")
            print(f"   File: {pdf_path}")
            print(f"   Size: {file_size} bytes")
            
            os.remove(pdf_path)
            return True
        else:
            print("❌ Advanced PDF file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Error creating advanced PDF: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Simple PDF Test Suite")
    print("=" * 40)
    
    success_count = 0
    total_tests = 3
    
    # Test ReportLab installation
    if test_reportlab_installation():
        success_count += 1
    
    # Test simple PDF creation
    if test_simple_pdf():
        success_count += 1
    
    # Test advanced features
    if test_advanced_pdf():
        success_count += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 ReportLab is working correctly!")
        print("✅ PDF generation functionality is ready to use.")
    else:
        print("⚠️  Some tests failed.")
        if success_count == 0:
            print("   Please install ReportLab: pip install reportlab")
        else:
            print("   Basic functionality works, check errors above.")
