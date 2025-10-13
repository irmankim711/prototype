#!/usr/bin/env python3
"""
Test script for Enhanced Template Optimization
Tests the new template optimization service with sample data.
"""

import os
import sys
import requests
import json
import pandas as pd
from pathlib import Path

# Add the backend path to sys.path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.services.template_optimizer import TemplateOptimizerService

def create_sample_excel_data():
    """Create sample Excel file with program data."""
    
    # Create sample data structure
    program_info_data = {
        'Field': [
            'Title', 'Date', 'Time', 'Location', 'Organizer', 'Speaker', 
            'Trainer', 'Facilitator', 'Male Participants', 'Female Participants',
            'Total Participants', 'Background', 'Objectives'
        ],
        'Value': [
            'PROGRAM PEMBANGUNAN KAPASITI ASNAF',
            '15/08/2025',
            '9:00 AM - 5:00 PM', 
            'DEWAN MUBARAK, SHAH ALAM',
            'LEMBAGA ZAKAT SELANGOR',
            'DR. AHMAD IBRAHIM',
            'USTAZ HASSAN ALI',
            'PUAN SITI FATIMAH',
            '25',
            '35', 
            '60',
            'Program ini bertujuan untuk meningkatkan kapasiti asnaf dalam bidang keusahawanan',
            'Peserta akan dapat memahami asas keusahawanan dan kemahiran asas perniagaan'
        ]
    }
    
    # Participants data
    participants_data = {
        'Bil': list(range(1, 61)),
        'Nama': [f'PESERTA {i:02d}' for i in range(1, 61)],
        'No. K/P': [f'12345678901{i:01d}' for i in range(0, 60)],
        'Alamat': [f'ALAMAT PESERTA {i}' for i in range(1, 61)],
        'No. Tel': [f'013-456789{i:02d}' for i in range(1, 61)],
        'Markah Pra': [round(50 + (i % 30), 1) for i in range(60)],
        'Markah Post': [round(60 + (i % 35), 1) for i in range(60)],
        'Hadir H1': ['✓' for _ in range(60)],
        'Hadir H2': ['✓' if i < 58 else '✗' for i in range(60)]
    }
    
    # Evaluation data
    evaluation_data = {
        'Kriteria Penilaian': [
            'Menepati objektif kursus',
            'Kandungan modul memberi impak', 
            'Jangka masa sesi',
            'Cetakkan nota',
            'Nota mudah fahami',
            'Penggunaan white board',
            'Sistem LCD',
            'Penggunaan PA sistem',
            'Persediaan yang rapi',
            'Penyampaian yang teratur',
            'Bahasa mudah difahami',
            'Pengetahuan tajuk kursus',
            'Menjawab soalan dengan baik',
            'Metodologi latihan sesuai',
            'Menarik minat peserta',
            'Maklumbalas peserta',
            'Memberi impak kepada peserta',
            'Prestasi keseluruhan'
        ],
        '1': [0, 1, 0, 0, 1, 2, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
        '2': [2, 3, 1, 2, 2, 3, 2, 1, 1, 2, 2, 1, 1, 2, 1, 2, 1, 2],  
        '3': [8, 6, 5, 7, 8, 10, 8, 6, 5, 7, 8, 6, 7, 8, 6, 8, 7, 6],
        '4': [25, 28, 30, 26, 25, 22, 24, 28, 30, 26, 25, 28, 27, 25, 28, 26, 27, 28],
        '5': [25, 22, 24, 25, 24, 23, 25, 25, 24, 25, 24, 25, 25, 24, 25, 24, 25, 23]
    }
    
    # Tentative data
    tentative_day1_data = {
        'Masa': [
            '8:30 - 9:00', '9:00 - 9:15', '9:15 - 10:30', '10:30 - 10:45',
            '10:45 - 12:00', '12:00 - 1:00', '1:00 - 2:30', '2:30 - 2:45',
            '2:45 - 4:00', '4:00 - 4:30'
        ],
        'Aktiviti': [
            'Pendaftaran', 'Pembukaan', 'Sesi 1: Pengenalan Keusahawanan', 'Rehat',
            'Sesi 2: Pelan Perniagaan', 'Solat & Makan Tengahari', 'Sesi 3: Pemasaran', 'Rehat',
            'Sesi 4: Pengurusan Kewangan', 'Penutup Hari 1'
        ],
        'Penerangan': [
            'Pendaftaran peserta dan pengagihan kit', 'Ucapan alu-aluan dan taklimat program',
            'Memahami konsep asas keusahawanan', 'Rehat dan networking',
            'Menyediakan pelan perniagaan yang berkesan', 'Solat Zohor dan makan tengahari',
            'Strategi pemasaran untuk usahawan baru', 'Rehat petang',
            'Pengurusan kewangan perniagaan', 'Rumusan dan penutup hari pertama'
        ],
        'Pengendali': [
            'Urusetia', 'Pengerusi', 'Dr. Ahmad Ibrahim', 'Urusetia',
            'Ustaz Hassan Ali', 'Urusetia', 'Puan Siti Fatimah', 'Urusetia',
            'Dr. Ahmad Ibrahim', 'Pengerusi'
        ]
    }
    
    # Create Excel file
    excel_file = 'sample_program_data.xlsx'
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        pd.DataFrame(program_info_data).to_excel(writer, sheet_name='Program Info', index=False)
        pd.DataFrame(participants_data).to_excel(writer, sheet_name='Participants', index=False)
        pd.DataFrame(evaluation_data).to_excel(writer, sheet_name='Evaluation', index=False)
        pd.DataFrame(tentative_day1_data).to_excel(writer, sheet_name='Tentative Day 1', index=False)
    
    print(f"✓ Created sample Excel file: {excel_file}")
    return excel_file

def create_sample_latex_template():
    """Create a sample LaTeX template based on the provided Temp2.tex."""
    
    template_content = """
% Enhanced LaTeX Template for Program Reports
\\documentclass[a4paper,12pt]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{geometry}
\\geometry{margin=1in}
\\usepackage{booktabs}
\\usepackage{graphicx}
\\usepackage{longtable}
\\usepackage{colortbl}
\\usepackage{xcolor}

\\definecolor{lightgray}{gray}{0.9}

\\begin{document}

% Title Page
\\begin{center}
    \\vspace*{1cm}
    \\textbf{\\huge LAPORAN {{program.title}}}\\\\
    \\vspace{0.5cm}
    \\textbf{{program.location}}\\\\
    \\vspace{0.5cm}
    \\textbf{Tarikh: {{program.date}}}\\\\
    \\vspace{0.5cm}
    \\textbf{Masa: {{program.time}}}\\\\
    \\vspace{1cm}
    \\textbf{ANJURAN: {{program.organizer}}}\\\\
\\end{center}

\\newpage

% Section 1: Program Information
\\section{Maklumat Program}
\\begin{tabular}{|l|l|}
    \\hline
    \\textbf{Latar Belakang Kursus} & {{program.background}} \\\\
    \\hline
    \\textbf{Tarikh} & {{program.date}} \\\\
    \\hline
    \\textbf{Tempat} & {{program.location}} \\\\
    \\hline
    \\textbf{Penceramah} & {{program.speaker}} \\\\
    \\hline
    \\textbf{Jurulatih} & {{program.trainer}} \\\\
    \\hline
    \\textbf{Fasilitator} & {{program.facilitator}} \\\\
    \\hline
    \\textbf{Jumlah Peserta (Lelaki)} & {{program.male_participants}} \\\\
    \\hline
    \\textbf{Jumlah Peserta (Perempuan)} & {{program.female_participants}} \\\\
    \\hline
    \\textbf{Jumlah Keseluruhan Hadir} & {{program.total_participants}} \\\\
    \\hline
\\end{tabular}

% Section 2: Course Objectives
\\section{Objektif Kursus}
{{program.objectives}}

% Section 3: Program Tentative
\\section{Tentatif Program}
\\subsection{Hari Pertama}
\\begin{longtable}{|p{2cm}|p{4cm}|p{6cm}|p{3cm}|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Masa} & \\textbf{Aktiviti} & \\textbf{Penerangan} & \\textbf{Pengendali} \\\\
    \\hline
    \\endhead
    {{#tentative.day1}}
    {{time}} & {{activity}} & {{description}} & {{handler}} \\\\
    \\hline
    {{/tentative.day1}}
\\end{longtable}

% Section 4: Attendance Report
\\section{Laporan Kehadiran Peserta}
\\begin{longtable}{|c|p{4cm}|p{3cm}|c|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Bil} & \\textbf{Nama} & \\textbf{No. K/P} & \\textbf{Hadir H1} & \\textbf{Hadir H2} \\\\
    \\hline
    \\endhead
    {{#participants}}
    {{bil}} & {{name}} & {{ic}} & {{attendance_day1}} & {{attendance_day2}} \\\\
    \\hline
    {{/participants}}
\\end{longtable}

\\textbf{Jumlah Kehadiran:} {{attendance.total_attended}} \\\\
\\textbf{Jumlah Tidak Hadir:} {{attendance.total_absent}}

% Section 5: Pre-Post Analysis
\\section{Analisa Pra dan Post}
\\begin{longtable}{|c|p{4cm}|c|c|c|}
    \\hline
    \\rowcolor{lightgray}
    \\textbf{Bil} & \\textbf{Nama} & \\textbf{Markah Pra} & \\textbf{Markah Post} & \\textbf{Perubahan} \\\\
    \\hline
    \\endhead
    {{#participants}}
    {{bil}} & {{name}} & {{pre_mark}} & {{post_mark}} & {{change}} \\\\
    \\hline
    {{/participants}}
\\end{longtable}

\\end{document}
"""
    
    template_file = 'sample_template.tex'
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"✓ Created sample LaTeX template: {template_file}")
    return template_file

def test_template_optimization():
    """Test the template optimization service."""
    
    print("🚀 Testing Enhanced Template Optimization System")
    print("=" * 60)
    
    # Create sample files
    excel_file = create_sample_excel_data()
    template_file = create_sample_latex_template()
    
    # Initialize optimizer
    optimizer = TemplateOptimizerService()
    
    # Read template content
    with open(template_file, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    print("\\n📋 Analyzing template and Excel data...")
    
    try:
        # Optimize template with Excel data
        result = optimizer.optimize_template_with_excel(template_content, excel_file)
        
        if result['success']:
            print("✅ Template optimization successful!")
            
            # Display results
            print("\\n📊 Analysis Results:")
            print("-" * 40)
            
            placeholders = result.get('placeholders', {})
            print(f"Simple placeholders: {len(placeholders.get('simple', []))}")
            print(f"Nested placeholders: {len(placeholders.get('nested', []))}")
            print(f"Loop blocks: {len(placeholders.get('loops', []))}")
            print(f"Tables detected: {len(placeholders.get('tables', []))}")
            
            data_analysis = result.get('data_analysis', {})
            print(f"\\nParticipants extracted: {len(data_analysis.get('participants', []))}")
            print(f"Program fields extracted: {len(data_analysis.get('program_info', {}))}")
            
            missing_fields = result.get('missing_fields', [])
            print(f"Missing fields: {len(missing_fields)}")
            if missing_fields:
                print("Missing fields:", missing_fields[:5], "..." if len(missing_fields) > 5 else "")
            
            # Show sample context data
            context = result.get('enhanced_context', {})
            if 'program' in context:
                print("\\n📝 Sample extracted data:")
                program = context['program']
                print(f"  Title: {program.get('title', 'N/A')}")
                print(f"  Date: {program.get('date', 'N/A')}")
                print(f"  Total Participants: {program.get('total_participants', 'N/A')}")
            
            optimizations = result.get('optimizations', {})
            if optimizations:
                print("\\n🔧 Optimization suggestions:")
                for suggestion_type, suggestions in optimizations.items():
                    if suggestions:
                        print(f"  {suggestion_type}: {len(suggestions)} items")
            
            print("\\n✨ Template is ready for report generation!")
            
            # Save the enhanced context for inspection
            with open('sample_context.json', 'w', encoding='utf-8') as f:
                json.dump(context, f, indent=2, ensure_ascii=False)
            print("💾 Context data saved to: sample_context.json")
            
        else:
            print(f"❌ Template optimization failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Error during optimization: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up sample files
        for file in [excel_file, template_file]:
            if os.path.exists(file):
                os.remove(file)
                print(f"🗑️  Cleaned up: {file}")

def demo_api_endpoints():
    """Demonstrate the API endpoints with sample data."""
    
    print("\\n🌐 API Endpoint Demonstration")
    print("=" * 60)
    
    base_url = "http://localhost:5000/api/mvp"
    
    # Test analyze endpoint
    print("\\n🔍 Testing template analysis endpoint...")
    
    # You would typically send files here, but for demo purposes:
    print(f"POST {base_url}/ai/optimize-template-with-excel")
    print("📤 Would send: template_file + excel_file")
    print("📥 Expected response: analysis results with placeholders and data mapping")
    
    # Test generation endpoint
    print("\\n🏗️  Testing report generation endpoint...")
    print(f"POST {base_url}/templates/generate-with-excel")
    print("📤 Would send: template_file + excel_file")
    print("📥 Expected response: generated report with download URL")
    
    print("\\n💡 To test the API endpoints:")
    print("1. Start the Flask backend server")
    print("2. Use the frontend demo or tools like Postman")
    print("3. Upload template and Excel files to the endpoints")

if __name__ == "__main__":
    test_template_optimization()
    demo_api_endpoints()
    
    print("\\n🎉 Enhanced Template System Demo Complete!")
    print("\\nKey improvements made:")
    print("✓ Comprehensive Excel data extraction")
    print("✓ Intelligent template placeholder analysis")
    print("✓ Automatic data mapping and validation")
    print("✓ Missing field identification")
    print("✓ Quality optimization suggestions")
    print("✓ Support for complex LaTeX templates")
    print("✓ Multi-sheet Excel processing")
    print("✓ Nested data structure handling")
